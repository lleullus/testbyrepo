import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { installReadyRuntime } from "../src/omp-adapter.js";

function schema() {
  return {
    optional() { return this; },
    min() { return this; },
    max() { return this; },
  };
}

function mockPi() {
  const handlers = new Map();
  const tools = new Map();
  const builtin = ["read", "grep", "glob", "edit", "write", "bash"].map(name => ({
    name,
    sourceInfo: { source: "builtin", path: `<builtin:${name}>`, scope: "core", origin: "builtin" },
  }));
  return {
    handlers,
    tools,
    zod: {
      object: () => schema(),
      enum: () => schema(),
      string: () => schema(),
      array: () => schema(),
      literal: () => schema(),
    },
    on(name, handler) {
      const list = handlers.get(name) || [];
      list.push(handler);
      handlers.set(name, list);
    },
    registerTool(definition) {
      tools.set(definition.name, definition);
    },
    getAllTools() {
      return builtin;
    },
    async emit(name, event, ctx) {
      let result;
      for (const handler of handlers.get(name) || []) result = await handler(event, ctx);
      return result;
    },
  };
}

function context(session, cwd) {
  return { cwd, sessionManager: { getSessionId: () => session } };
}

function parseToolResult(result) {
  return JSON.parse(result.content[0].text);
}

function binding(projectRoot, ticketPath) {
  const root = fs.realpathSync(projectRoot);
  const ticket = fs.realpathSync(ticketPath);
  const spec = fs.realpathSync(path.join(root, "SPEC.md"));
  return {
    project_root: root,
    ticket_path: ticket,
    ticket_sha256: "ticket-sha",
    ticket_status_at_start: "ready",
    parent_spec_path: spec,
    parent_spec_sha256: "spec-sha",
    behavior_authorities: [],
    ui_authority: null,
    validator_path: "/tmp/ready-validator.py",
    validator_sha256: "validator-sha",
    git_head: "head",
    baseline_worktree_fingerprint: { status_digest: "status", tracked_changed_paths: [], preexisting_untracked_paths: [] },
    protected_artifacts: [
      { path: ticket, sha256: "ticket-sha", kind: "ticket" },
      { path: spec, sha256: "spec-sha", kind: "parent_spec" },
    ],
  };
}

async function arm(pi, sid, cwd) {
  await pi.emit("tool_call", {
    toolCallId: `skill-${sid}`,
    toolName: "read",
    input: { path: "skill://ready-ticket-implement" },
  }, context(sid, cwd));
}

test("extension registration defers action methods until the runtime is initialized", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-ready-omp-load-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  let initialized = false;
  let actionCalls = 0;
  const pi = mockPi();
  pi.getAllTools = () => {
    actionCalls += 1;
    if (!initialized) throw new Error("Extension runtime not initialized. Action methods cannot be called during extension loading.");
    return [];
  };

  assert.doesNotThrow(() => installReadyRuntime(pi, { dataRoot: path.join(root, "state") }));
  assert.equal(actionCalls, 0);

  initialized = true;
  await assert.doesNotReject(() => pi.emit("resources_discover", {}, context("load", root)));
  assert.equal(actionCalls, 1);
  await pi.emit("session_start", {}, context("load", root));
  assert.equal(actionCalls, 2);
});

test("OMP adapter enforces DIRECT runtime gates, exact result attribution, path rewrite, stale evidence, and idle cleanup", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-ready-omp-direct-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const project = path.join(root, "project");
  fs.mkdirSync(path.join(project, "src"), { recursive: true });
  const ticket = path.join(project, "TICKET.md");
  const spec = path.join(project, "SPEC.md");
  const source = path.join(project, "src", "a.txt");
  fs.writeFileSync(ticket, "Status: ready\n");
  fs.writeFileSync(spec, "Status: approved\n");
  fs.writeFileSync(source, "old\n");

  const pi = mockPi();
  const runtime = installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    readySkillDir: "/fixture/ready-ticket-implement",
    bindAuthority: async ({ projectRoot, ticketPath }) => binding(projectRoot, ticketPath),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });

  const discovered = await pi.emit("resources_discover", { type: "resources_discover", cwd: project, reason: "startup" }, context("main", project));
  assert.deepEqual(discovered.skillPaths, ["/fixture/ready-ticket-implement"]);
  assert.deepEqual(Object.keys(runtime.getToolMap().mapped).sort(), ["bash", "edit", "glob", "grep", "read", "write"]);

  await arm(pi, "pre", project);
  const preBeginMutation = await pi.emit("tool_call", {
    toolCallId: "pre-write",
    toolName: "write",
    input: { path: "src/a.txt", content: "x\n" },
  }, context("pre", project));
  assert.equal(preBeginMutation.block, true);
  assert.match(preBeginMutation.reason, /begin has not bound/);

  await arm(pi, "main", project);
  const guard = pi.tools.get("ready_guard");
  const begun = parseToolResult(await guard.execute("g1", {
    action: "begin_direct",
    ticket_path: ticket,
    project_root: project,
  }, null, null, context("main", project)));
  const executionId = begun.execution_id;
  assert.equal(begun.phase, "ACTIVE");

  const firstRead = {
    toolCallId: "read-1",
    toolName: "read",
    input: { path: "src/a.txt" },
  };
  const readGate = await pi.emit("tool_call", firstRead, context("main", project));
  assert.equal(readGate.input.path, fs.realpathSync(source));

  await pi.emit("tool_result", {
    toolCallId: "read-1",
    toolName: "read",
    input: readGate.input,
    content: [{ type: "text", text: "old" }],
    isError: false,
  }, context("other-session", project));
  assert.equal(runtime.lifecycle.status(executionId).active_operation.tool_call_id, "read-1");

  await pi.emit("tool_result", {
    toolCallId: "read-1",
    toolName: "read",
    input: readGate.input,
    content: [{ type: "text", text: "old" }],
    isError: false,
  }, context("main", project));
  assert.equal(runtime.lifecycle.status(executionId).active_operation, null);

  const duplicate = await pi.emit("tool_call", { ...firstRead, toolCallId: "read-duplicate" }, context("main", project));
  assert.equal(duplicate.block, true);
  assert.match(duplicate.reason, /already succeeded/);

  const broad = await pi.emit("tool_call", {
    toolCallId: "broad",
    toolName: "bash",
    input: { command: "rg --files" },
  }, context("main", project));
  assert.equal(broad.block, true);
  assert.match(broad.reason, /inventory rescans/);

  const protectedWrite = await pi.emit("tool_call", {
    toolCallId: "ticket-write",
    toolName: "write",
    input: { path: ticket, content: "changed" },
  }, context("main", project));
  assert.equal(protectedWrite.block, true);
  assert.match(protectedWrite.reason, /protected ticket authority/);

  const outsideRead = await pi.emit("tool_call", {
    toolCallId: "outside-read",
    toolName: "read",
    input: { path: "../outside.txt" },
  }, context("main", project));
  assert.equal(outsideRead.block, true);
  assert.match(outsideRead.reason, /outside Project Root/);

  const failedWrite = {
    toolCallId: "write-failed",
    toolName: "write",
    input: { path: "src/a.txt", content: "bad\n" },
  };
  const failedWriteGate = await pi.emit("tool_call", failedWrite, context("main", project));
  await pi.emit("tool_result", {
    toolCallId: "write-failed",
    toolName: "write",
    input: failedWriteGate.input,
    content: [{ type: "text", text: "deterministic write failure" }],
    isError: true,
  }, context("main", project));
  const repeatedFailedWrite = await pi.emit("tool_call", {
    ...failedWrite,
    toolCallId: "write-failed-repeat",
  }, context("main", project));
  assert.equal(repeatedFailedWrite.block, true);
  assert.match(repeatedFailedWrite.reason, /unchanged repeat/);

  const writeEvent = {
    toolCallId: "write-1",
    toolName: "write",
    input: { path: "src/a.txt", content: "new\n" },
  };
  const writeGate = await pi.emit("tool_call", writeEvent, context("main", project));
  assert.equal(writeGate.input.path, fs.realpathSync(source));
  fs.writeFileSync(writeGate.input.path, writeEvent.input.content);
  await pi.emit("tool_result", {
    toolCallId: "write-1",
    toolName: "write",
    input: writeGate.input,
    content: [{ type: "text", text: "Wrote file" }],
    isError: false,
  }, context("main", project));
  assert.equal(runtime.lifecycle.status(executionId).mutation_revision, 1);

  await assert.rejects(
    guard.execute("g-complete-stale", { action: "complete", execution_id: executionId }, null, null, context("main", project)),
    /current-revision self-check evidence/,
  );

  const currentRead = await pi.emit("tool_call", {
    toolCallId: "read-current",
    toolName: "read",
    input: { path: "src/a.txt" },
  }, context("main", project));
  await pi.emit("tool_result", {
    toolCallId: "read-current",
    toolName: "read",
    input: currentRead.input,
    content: [{ type: "text", text: "new" }],
    isError: false,
  }, context("main", project));

  const completed = parseToolResult(await guard.execute("g-complete", {
    action: "complete",
    execution_id: executionId,
  }, null, null, context("main", project)));
  assert.equal(completed.phase, "COMPLETE");
  assert.equal(runtime.lifecycle.sessionState("main").armed, false);

  const afterTerminal = await pi.emit("tool_call", {
    toolCallId: "post-write",
    toolName: "write",
    input: { path: "src/a.txt", content: "outside runtime\n" },
  }, context("main", project));
  assert.equal(afterTerminal, undefined);
});

test("OMP adapter keeps SUBAGENT one-worker PRE_ACTION gating and blocks parent mutation", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-ready-omp-subagent-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const project = path.join(root, "project");
  fs.mkdirSync(path.join(project, "src"), { recursive: true });
  const ticket = path.join(project, "TICKET.md");
  const spec = path.join(project, "SPEC.md");
  const source = path.join(project, "src", "a.txt");
  fs.writeFileSync(ticket, "Status: ready\n");
  fs.writeFileSync(spec, "Status: approved\n");
  fs.writeFileSync(source, "old\n");

  const pi = mockPi();
  const runtime = installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => binding(projectRoot, ticketPath),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  const guard = pi.tools.get("ready_guard");

  await arm(pi, "parent", project);
  const assignment = parseToolResult(await guard.execute("assign", {
    action: "assign_subagent",
    ticket_path: ticket,
    project_root: project,
  }, null, null, context("parent", project)));

  await arm(pi, "child", project);
  const delegated = parseToolResult(await guard.execute("delegate", {
    action: "begin_delegated",
    assignment_id: assignment.assignment_id,
  }, null, null, context("child", project)));
  assert.equal(delegated.phase, "PRE_ACTION_PENDING");

  const beforeRelease = await pi.emit("tool_call", {
    toolCallId: "child-before-release",
    toolName: "write",
    input: { path: "src/a.txt", content: "new\n" },
  }, context("child", project));
  assert.equal(beforeRelease.block, true);
  assert.match(beforeRelease.reason, /PRE_ACTION_PENDING/);

  await guard.execute("pre-action", {
    action: "checkpoint_pre_action",
    execution_id: delegated.execution_id,
    summary: "authority and implementation target ready",
  }, null, null, context("child", project));

  const parentMutation = await pi.emit("tool_call", {
    toolCallId: "parent-write",
    toolName: "write",
    input: { path: "src/a.txt", content: "parent\n" },
  }, context("parent", project));
  assert.equal(parentMutation.block, true);
  assert.match(parentMutation.reason, /parent session may not mutate/);

  await guard.execute("release", {
    action: "release_checkpoint",
    execution_id: delegated.execution_id,
    decision: "CONTINUE",
  }, null, null, context("parent", project));
  assert.equal(runtime.lifecycle.status(delegated.execution_id).phase, "ACTIVE");

  const childWrite = await pi.emit("tool_call", {
    toolCallId: "child-write",
    toolName: "write",
    input: { path: "src/a.txt", content: "child\n" },
  }, context("child", project));
  assert.equal(childWrite.input.path, fs.realpathSync(source));
  fs.writeFileSync(childWrite.input.path, "child\n");
  await pi.emit("tool_result", {
    toolCallId: "child-write",
    toolName: "write",
    input: childWrite.input,
    content: [{ type: "text", text: "Wrote file" }],
    isError: false,
  }, context("child", project));

  const readGate = await pi.emit("tool_call", {
    toolCallId: "child-read",
    toolName: "read",
    input: { path: "src/a.txt" },
  }, context("child", project));
  await pi.emit("tool_result", {
    toolCallId: "child-read",
    toolName: "read",
    input: readGate.input,
    content: [{ type: "text", text: "child" }],
    isError: false,
  }, context("child", project));

  const complete = parseToolResult(await guard.execute("child-complete", {
    action: "complete",
    execution_id: delegated.execution_id,
  }, null, null, context("child", project)));
  assert.equal(complete.phase, "COMPLETE");
  assert.equal(runtime.lifecycle.sessionState("child").armed, false);
  assert.equal(runtime.lifecycle.sessionState("parent").armed, false);
});
