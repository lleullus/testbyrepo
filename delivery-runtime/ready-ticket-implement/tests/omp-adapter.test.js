import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

import { installReadyRuntime } from "../src/omp-adapter.js";
import { checkAuthorityCurrentness } from "../src/authority-binding.js";
import { MAX_OBSERVATION_OUTPUT_BYTES } from "../src/observation-ledger.js";

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

async function armVerify(pi, sid, cwd) {
  await pi.emit("tool_call", {
    toolCallId: `verify-skill-${sid}`,
    toolName: "read",
    input: { path: "skill://ready-ticket-verify" },
  }, context(sid, cwd));
}

function hashFile(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function initGit(project) {
  for (const args of [
    ["init", "-q"],
    ["add", "."],
    ["-c", "user.name=Ready Test", "-c", "user.email=ready@example.invalid", "commit", "-qm", "fixture"],
  ]) {
    const result = spawnSync("git", ["-C", project, ...args], { encoding: "utf8" });
    assert.equal(result.status, 0, result.stderr);
  }
}

async function canonicalVerificationFixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-ready-canonical-revalidation-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const project = path.join(root, "project");
  const canonical = path.join(root, "canonical");
  fs.mkdirSync(project);
  fs.mkdirSync(canonical);
  const ticket = path.join(project, "TICKET.md");
  const spec = path.join(project, "SPEC.md");
  const product = path.join(project, "product.js");
  const workflow = path.join(canonical, "workflow.md");
  const toTickets = path.join(canonical, "SKILL.md");
  const validator = path.join(canonical, "validate_ticket.py");
  fs.writeFileSync(ticket, "Status: ready\n\n## Verification\n\n- Parent outcome ordinal: 1\n");
  fs.writeFileSync(spec, "Status: approved\n");
  fs.writeFileSync(product, "console.log('adjusted');\n");
  fs.writeFileSync(workflow, `### To Tickets\n\n${toTickets}\n`);
  fs.writeFileSync(toTickets, "# To Tickets\n");
  fs.writeFileSync(validator, "import pathlib, sys\ntext = pathlib.Path(sys.argv[1]).read_text()\nprint('VALID' if text.startswith(('Status: ready\\n', 'Status: done\\n')) else 'INVALID')\n");
  initGit(project);
  const pi = mockPi();
  const runtime = installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => ({
      ...binding(projectRoot, ticketPath),
      ticket_sha256: hashFile(ticketPath),
      validator_path: validator,
      validator_sha256: hashFile(validator),
      protected_artifacts: [[ticket, "ticket"], [spec, "parent_spec"], [validator, "validator"], [workflow, "workflow"], [toTickets, "to_tickets"]]
        .map(([file, kind]) => ({ path: file, kind, sha256: hashFile(file) })),
    }),
    checkAuthorityCurrentness,
  });
  const ctx = context("verify", project);
  await armVerify(pi, "verify", project);
  const probe = parseToolResult(await pi.tools.get("ready_probe_binding").execute("probe", {
    ticket_path: ticket, project_root: project, output_path: path.join(root, "probe.json"), target_paths: [product], lanes: [],
  }));
  const guard = pi.tools.get("ready_guard");
  const begun = parseToolResult(await guard.execute("begin", {
    action: "begin_verify", ticket_path: ticket, project_root: project, target_paths: [product], probe_binding_path: probe.probe_binding_path,
  }, null, null, ctx));
  const argv = pi.tools.get("ready_argv");
  const inspect = () => argv.execute("revalidate", { action: "inspect", version: 1, commands: [["python3", validator, ticket]] }, null, null, ctx);
  return { root, project, ticket, spec, product, workflow, toTickets, validator, pi, runtime, ctx, guard, begun, argv, inspect };
}

test("bound canonical revalidation refreshes exact authority and closes VERIFIED", async t => {
  const f = await canonicalVerificationFixture(t);
  const observed = parseToolResult(await f.argv.execute("product", {
    action: "execute", version: 1, argv: [process.execPath, f.product],
  }, null, null, f.ctx));
  assert.equal(observed.stdout, "adjusted\n");
  for (const inputPath of ["skill://iis-workflow:1-3", `${f.workflow}:raw`, f.toTickets, f.validator, f.ticket, f.ticket, f.spec]) {
    const gate = await f.pi.emit("tool_call", { toolName: "read", toolCallId: "authority", input: { path: inputPath } }, f.ctx);
    assert.notEqual(gate?.block, true, gate?.reason);
    const canonicalPath = gate?.input?.path ?? inputPath;
    const content = fs.readFileSync(canonicalPath.replace(/:(?:raw|\d+-\d+)$/, ""), "utf8");
    await f.pi.emit("tool_result", { toolName: "read", toolCallId: "authority", content: [{ type: "text", text: content }], isError: false }, f.ctx);
  }
  assert.equal(parseToolResult(await f.inspect()).results[0].stdout, "VALID\n");
  assert.equal(parseToolResult(await f.inspect()).results[0].stdout, "VALID\n");
  const finalized = parseToolResult(await f.guard.execute("finalize", {
    action: "finalize_verification", execution_id: f.begun.execution_id, verdict: "VERIFIED",
  }, null, null, f.ctx));
  assert.equal(finalized.ticket_progression, "COMPLETED");
  assert.match(fs.readFileSync(f.ticket, "utf8"), /^Status: done$/m);
});

test("rejected overlapping verification readback remains executable after release", async t => {
  const f = await canonicalVerificationFixture(t);
  const input = { path: f.product };
  const gate = await f.pi.emit("tool_call", { toolName: "read", toolCallId: "held-read", input }, f.ctx);
  assert.notEqual(gate?.block, true);
  const command = { action: "execute", version: 1, argv: [process.execPath, f.product] };
  await assert.rejects(f.argv.execute("overlapping-execute", command, null, null, f.ctx));
  await f.pi.emit("tool_result", {
    toolName: "read", toolCallId: "held-read", input,
    content: [{ type: "text", text: fs.readFileSync(f.product, "utf8") }], isError: false,
  }, f.ctx);
  const observed = parseToolResult(await f.argv.execute("released-execute", command, null, null, f.ctx));
  assert.equal(observed.stdout, "adjusted\n");
});

test("implementation command output permits closure only after a complete successful observation", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-ready-command-observation-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const ticket = path.join(root, "TICKET.md");
  const product = path.join(root, "product.js");
  fs.writeFileSync(ticket, "Status: ready\n");
  fs.writeFileSync(path.join(root, "SPEC.md"), "Status: approved\n");
  fs.writeFileSync(product, `if (process.argv[2] === 'fail') process.exit(1);\nprocess.stdout.write(process.argv[2] === 'large' ? 'x'.repeat(${MAX_OBSERVATION_OUTPUT_BYTES + 1}) : 'observed\\n');\n`);
  const pi = mockPi();
  installReadyRuntime(pi, {
    dataRoot: path.join(root, "runtime"),
    bindAuthority: async ({ projectRoot, ticketPath }) => binding(projectRoot, ticketPath),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  const ctx = context("command-observation", root);
  await arm(pi, "command-observation", root);
  const guard = pi.tools.get("ready_guard");
  const begun = parseToolResult(await guard.execute("begin", {
    action: "begin_direct", ticket_path: ticket, project_root: root,
  }, null, null, ctx));
  const execute = mode => pi.tools.get("ready_argv").execute(mode, {
    action: "mutate", version: 1, argv: [process.execPath, product, mode], target_paths: [product],
  }, null, null, ctx);
  const complete = () => guard.execute("complete", { action: "complete", execution_id: begun.execution_id }, null, null, ctx);
  assert.equal(parseToolResult(await execute("fail")).exit_code, 1);
  await assert.rejects(complete());
  await execute("large");
  await assert.rejects(complete());
  assert.equal(parseToolResult(await execute("normal")).stdout, "observed\n");
  assert.equal(parseToolResult(await complete()).phase, "COMPLETE");
});

test("cancelling an applied mutation preserves uncertainty and blocks a different mutation", { timeout: 10_000 }, async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-ready-aborted-mutation-"));
  const ticket = path.join(root, "TICKET.md");
  const effects = path.join(root, "effects.txt");
  const product = path.join(root, "mutation.cjs");
  const controller = new AbortController();
  let watcher;
  let outcome;
  t.after(async () => {
    controller.abort();
    watcher?.close();
    await outcome;
    fs.rmSync(root, { recursive: true, force: true });
  });
  fs.writeFileSync(ticket, "Status: ready\n");
  fs.writeFileSync(path.join(root, "SPEC.md"), "Status: approved\n");
  fs.writeFileSync(effects, "");
  fs.writeFileSync(product, `require('node:fs').appendFileSync(${JSON.stringify(effects)}, 'applied\\n');\nif (process.argv[2] !== 'again') setTimeout(() => {}, 60_000);\n`);
  const pi = mockPi();
  installReadyRuntime(pi, {
    dataRoot: path.join(root, "runtime"),
    bindAuthority: async ({ projectRoot, ticketPath }) => binding(projectRoot, ticketPath),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  const ctx = context("aborted-mutation", root);
  await arm(pi, "aborted-mutation", root);
  const guard = pi.tools.get("ready_guard");
  const begun = parseToolResult(await guard.execute("begin", {
    action: "begin_direct", ticket_path: ticket, project_root: root,
  }, null, null, ctx));
  const applied = new Promise(resolve => {
    watcher = fs.watch(root, (_event, name) => {
      if (String(name) === "effects.txt" && fs.readFileSync(effects, "utf8") === "applied\n") resolve();
    });
  });
  outcome = pi.tools.get("ready_argv").execute("interrupted", {
    action: "mutate", version: 1, argv: [process.execPath, product, "first"], target_paths: [effects],
  }, controller.signal, null, ctx).then(value => ({ value }), error => ({ error }));
  await Promise.race([applied, outcome.then(result => { throw result.error ?? new Error("mutation ended before the visible effect"); })]);
  controller.abort();
  assert.equal((await outcome).error?.name, "AbortError");
  const status = parseToolResult(await guard.execute("status", { action: "status", execution_id: begun.execution_id }, null, null, ctx));
  assert.equal(status.execution.phase, "MUTATION_UNCERTAIN");
  assert.equal(status.execution.mutation_revision, 0);
  await assert.rejects(() => pi.tools.get("ready_argv").execute("different-mutation", {
    action: "mutate", version: 1, argv: [process.execPath, product, "again"], target_paths: [effects],
  }, null, null, ctx));
  assert.equal(fs.readFileSync(effects, "utf8"), "applied\n");
});

test("bound canonical access does not authorize foreign paths, commands, or source refresh", async t => {
  const f = await canonicalVerificationFixture(t);
  const foreign = path.join(f.root, "foreign");
  fs.mkdirSync(foreign);
  const wrongTicket = path.join(foreign, "OTHER.md");
  fs.writeFileSync(wrongTicket, "Status: ready\n");
  const wrongValidator = path.join(foreign, "validate_ticket.py");
  const sentinel = path.join(f.root, "unauthorized-effect");
  fs.writeFileSync(wrongValidator, `from pathlib import Path\nPath(${JSON.stringify(sentinel)}).write_text('effect')\n`);
  for (const command of [["python3", f.validator, wrongTicket], ["python3", wrongValidator, f.ticket], ["python3", f.validator, f.ticket, "--extra"]]) {
    await assert.rejects(() => f.argv.execute("foreign", { action: "inspect", version: 1, commands: [command] }, null, null, f.ctx), /outside the read-only allowlist/);
  }
  assert.equal(fs.existsSync(sentinel), false);
  await assert.rejects(() => f.argv.execute("external-execute", { action: "execute", version: 1, argv: ["python3", f.validator, f.ticket] }, null, null, f.ctx), /outside Project Root/);
  for (const inputPath of [foreign, `${f.workflow}/../foreign`, `${f.workflow}:raw/../foreign`, "skill://iis-workflow/../../foreign", "skill://unknown"]) {
    const gate = await f.pi.emit("tool_call", { toolName: "read", toolCallId: "foreign-read", input: { path: inputPath } }, f.ctx);
    assert.equal(gate?.block, true);
  }
  const mutation = await f.pi.emit("tool_call", { toolName: "write", toolCallId: "write-authority", input: { path: f.workflow, content: "changed" } }, f.ctx);
  assert.equal(mutation.block, true);
  await f.pi.emit("tool_call", { toolName: "read", toolCallId: "source", input: { path: f.product } }, f.ctx);
  await f.pi.emit("tool_result", { toolName: "read", toolCallId: "source", content: [{ type: "text", text: fs.readFileSync(f.product, "utf8") }], isError: false }, f.ctx);
  const duplicate = await f.pi.emit("tool_call", { toolName: "read", toolCallId: "source-again", input: { path: f.product } }, f.ctx);
  assert.equal(duplicate.block, true);
});

test("bound canonical revalidation preserves operation and drift gates", async t => {
  await t.test("active operation", async st => {
    const f = await canonicalVerificationFixture(st);
    await f.pi.emit("tool_call", { toolName: "read", toolCallId: "pending", input: { path: f.product } }, f.ctx);
    await assert.rejects(f.inspect, /active guarded operation/);
  });
  await t.test("target drift", async st => {
    const f = await canonicalVerificationFixture(st);
    fs.appendFileSync(f.product, "// drift\n");
    await assert.rejects(f.inspect, /target drift/);
    await assert.rejects(() => f.guard.execute("finalize", { action: "finalize_verification", execution_id: f.begun.execution_id, verdict: "VERIFIED" }, null, null, f.ctx));
    assert.match(fs.readFileSync(f.ticket, "utf8"), /^Status: ready$/m);
  });
  await t.test("canonical route drift", async st => {
    const f = await canonicalVerificationFixture(st);
    fs.appendFileSync(f.workflow, "changed route\n");
    await assert.rejects(f.inspect, /authority changed/);
    await assert.rejects(() => f.guard.execute("finalize", { action: "finalize_verification", execution_id: f.begun.execution_id, verdict: "VERIFIED" }, null, null, f.ctx));
    assert.match(fs.readFileSync(f.ticket, "utf8"), /^Status: ready$/m);
  });
});

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

test("plain filesystem inspection of Ready skill files does not arm execution", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-ready-omp-review-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const pi = mockPi();
  installReadyRuntime(pi, { dataRoot: path.join(root, "state") });

  for (const [sid, skillName] of [
    ["review-implement", "ready-ticket-implement"],
    ["review-verify", "ready-ticket-verify"],
  ]) {
    await pi.emit("tool_call", {
      toolCallId: `inspect-${sid}`,
      toolName: "read",
      input: { path: path.join(root, "review", skillName, "SKILL.md") },
    }, context(sid, root));
    const unrelatedMutation = await pi.emit("tool_call", {
      toolCallId: `write-${sid}`,
      toolName: "write",
      input: { path: path.join(root, `${sid}.txt`), content: "review only\n" },
    }, context(sid, root));
    assert.equal(unrelatedMutation, undefined);
  }

  await armVerify(pi, "verify-execution", root);
  const preBeginMutation = await pi.emit("tool_call", {
    toolCallId: "verify-pre-begin-write",
    toolName: "write",
    input: { path: path.join(root, "verification-target.txt"), content: "blocked\n" },
  }, context("verify-execution", root));
  assert.equal(preBeginMutation.block, true);
  assert.match(preBeginMutation.reason, /begin has not bound/);
});

test("cancel_admission restores same-session planning and a fresh Ready admission remains guarded", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-ready-cancel-admission-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const project = path.join(root, "project");
  const source = path.join(project, "src", "product.txt");
  const ticket = path.join(project, "TICKET.md");
  fs.mkdirSync(path.dirname(source), { recursive: true });
  fs.writeFileSync(source, "current\n");
  fs.writeFileSync(ticket, "Status: ready\n");
  fs.writeFileSync(path.join(project, "SPEC.md"), "Status: approved\n");
  const pi = mockPi();
  installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => binding(projectRoot, ticketPath),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  const ctx = context("planning-recovery", project);
  const mutation = toolCallId => pi.emit("tool_call", {
    toolCallId,
    toolName: "write",
    input: { path: source, content: "next\n" },
  }, ctx);
  const guard = pi.tools.get("ready_guard");

  await arm(pi, "planning-recovery", project);
  assert.equal((await mutation("premature-write")).block, true);
  await assert.rejects(
    guard.execute("foreign-cancel", { action: "cancel_admission", execution_id: "foreign-execution" }, null, null, ctx),
    /targets only the current session/,
  );
  assert.equal((await mutation("still-armed-write")).block, true);

  const cancelled = parseToolResult(await guard.execute("cancel", {
    action: "cancel_admission", ticket_path: "", project_root: undefined,
    execution_id: "", assignment_id: "", probe_binding_path: "",
    target_paths: [], allowed_output_paths: [], verdict: "INCONCLUSIVE", decision: "STOP",
  }, null, null, ctx));
  assert.equal(cancelled.session.armed, false);
  assert.equal(await mutation("planning-write"), undefined);

  await arm(pi, "planning-recovery", project);
  assert.equal((await mutation("fresh-pre-begin-write")).block, true);
  const begun = parseToolResult(await guard.execute("begin", {
    action: "begin_direct",
    ticket_path: ticket,
    project_root: project,
  }, null, null, ctx));
  assert.equal(begun.phase, "ACTIVE");
  await assert.rejects(
    guard.execute("active-cancel", { action: "cancel_admission" }, null, null, ctx),
    /unavailable after execution, assignment, parent, or worker binding/,
  );
  const status = parseToolResult(await guard.execute("status", { action: "status" }, null, null, ctx));
  assert.equal(status.session.execution_id, begun.execution_id);
  assert.equal(status.execution.phase, "ACTIVE");
});

test("cancel and rearm reject a stale begin_verify commit after asynchronous preflight", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-ready-cancel-verify-race-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const project = path.join(root, "project");
  const ticket = path.join(project, "TICKET.md");
  const product = path.join(project, "product.txt");
  fs.mkdirSync(project, { recursive: true });
  fs.writeFileSync(ticket, "Status: done\n");
  fs.writeFileSync(path.join(project, "SPEC.md"), "Status: approved\n");
  fs.writeFileSync(product, "stable\n");
  initGit(project);
  let signalEntered;
  let releaseBinding;
  const bindingEntered = new Promise(resolve => { signalEntered = resolve; });
  const bindingRelease = new Promise(resolve => { releaseBinding = resolve; });
  let bindingCalls = 0;
  const pi = mockPi();
  installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => {
      bindingCalls += 1;
      if (bindingCalls === 1) {
        signalEntered();
        await bindingRelease;
      }
      return { ...binding(projectRoot, ticketPath), ticket_status_at_start: "done" };
    },
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  const ctx = context("verify-race", project);
  const guard = pi.tools.get("ready_guard");
  await armVerify(pi, "verify-race", project);
  const pending = guard.execute("stale-begin", {
    action: "begin_verify",
    ticket_path: ticket,
    project_root: project,
    target_paths: [product],
  }, null, null, ctx);
  await bindingEntered;
  await guard.execute("cancel", { action: "cancel_admission" }, null, null, ctx);
  await armVerify(pi, "verify-race", project);
  releaseBinding();
  await assert.rejects(pending, /admission is no longer current/);
  const afterStale = parseToolResult(await guard.execute("after-stale", { action: "status" }, null, null, ctx));
  assert.equal(afterStale.session.armed, true);
  assert.equal(afterStale.execution, null);

  const fresh = parseToolResult(await guard.execute("fresh-begin", {
    action: "begin_verify",
    ticket_path: ticket,
    project_root: project,
    target_paths: [product],
  }, null, null, ctx));
  assert.equal(fresh.purpose, "verify");
  assert.equal(fresh.phase, "ACTIVE");
});

test("armed admission executes only the discovered canonical validator before binding", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-ready-admission-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const workflow = path.join(root, "workflow", "SKILL.md");
  const toTickets = path.join(root, "to-tickets", "SKILL.md");
  const validator = path.join(root, "to-tickets", "validate_ticket.py");
  const ticket = path.join(root, "TICKET-001.md");
  const malicious = path.join(root, "validate_ticket.py");
  const sentinel = path.join(root, "unauthorized-effect");
  fs.mkdirSync(path.dirname(workflow), { recursive: true });
  fs.mkdirSync(path.dirname(toTickets), { recursive: true });
  fs.writeFileSync(workflow, `### To Tickets\n\n\`${toTickets}\`\n`);
  fs.writeFileSync(toTickets, "# To Tickets\n");
  fs.writeFileSync(validator, "import pathlib, sys\nprint('VALID' if pathlib.Path(sys.argv[1]).read_text() == 'valid input' else 'INVALID')\n");
  fs.writeFileSync(ticket, "valid input");
  fs.writeFileSync(malicious, `from pathlib import Path\nPath(${JSON.stringify(sentinel)}).write_text('effect')\n`);
  const previous = process.env.IIS_READY_IIS_WORKFLOW_SKILL;
  process.env.IIS_READY_IIS_WORKFLOW_SKILL = workflow;
  t.after(() => {
    if (previous === undefined) delete process.env.IIS_READY_IIS_WORKFLOW_SKILL;
    else process.env.IIS_READY_IIS_WORKFLOW_SKILL = previous;
  });
  const pi = mockPi();
  installReadyRuntime(pi, { dataRoot: path.join(root, "state") });
  const ctx = context("admission", root);
  await armVerify(pi, "admission", root);
  const tool = pi.tools.get("ready_argv");
  const result = parseToolResult(await tool.execute("validate", {
    action: "inspect", version: 1, commands: [["python3", validator, ticket]],
  }, undefined, undefined, ctx));
  assert.equal(result.results[0].exit_code, 0);
  assert.equal(result.results[0].stdout, "VALID\n");
  fs.writeFileSync(ticket, "invalid input");
  fs.writeFileSync(workflow, `### To Tickets\n\n${toTickets}\n`);
  const invalid = parseToolResult(await tool.execute("invalid", {
    action: "inspect", version: 1, commands: [["python3", "-B", validator, ticket]],
  }, undefined, undefined, ctx));
  assert.equal(invalid.results[0].stdout, "INVALID\n");
  await assert.rejects(() => tool.execute("wrong-script", {
    action: "inspect", version: 1, commands: [["python3", malicious, ticket]],
  }, undefined, undefined, ctx), /no bound Ready execution/);
  await assert.rejects(() => tool.execute("product-execute", {
    action: "execute", version: 1, argv: ["python3", malicious],
  }, undefined, undefined, ctx), /no bound Ready execution/);
  assert.equal(fs.existsSync(sentinel), false);
  const status = parseToolResult(await pi.tools.get("ready_guard").execute("status", { action: "status" }, undefined, undefined, ctx));
  assert.equal(status.session.armed, true);
  assert.equal(status.execution, null);
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

  const preflightBroad = await pi.emit("tool_call", {
    toolCallId: "broad-preflight",
    toolName: "bash",
    input: { command: "rg --files" },
  }, context("main", project));
  assert.equal(preflightBroad, undefined);
  await pi.emit("tool_result", {
    toolCallId: "broad-preflight",
    toolName: "bash",
    input: { command: "rg --files" },
    content: [{ type: "text", text: "src/a.txt" }],
    isError: false,
  }, context("main", project));

  const secondPreflightBroad = await pi.emit("tool_call", {
    toolCallId: "broad-preflight-repeat",
    toolName: "bash",
    input: { command: "git ls-files" },
  }, context("main", project));
  assert.equal(secondPreflightBroad.block, true);
  assert.match(secondPreflightBroad.reason, /at most one/);

  const firstRead = {
    toolCallId: "read-1",
    toolName: "read",
    input: { path: "src/a.txt" },
  };
  const readGate = await pi.emit("tool_call", firstRead, context("main", project));
  assert.equal(readGate.input.path, fs.realpathSync(source));

  const inspectTool = pi.tools.get("ready_argv");
  const inspectSource = { action: "inspect", version: 1, commands: [["cat", "src/a.txt"]] };
  await assert.rejects(inspectTool.execute("overlapping-inspect", inspectSource, null, null, context("main", project)));

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

  const inspected = parseToolResult(await inspectTool.execute("released-inspect", inspectSource, null, null, context("main", project)));
  assert.equal(inspected.results[0].stdout, "old\n");

  const duplicate = await pi.emit("tool_call", { ...firstRead, toolCallId: "read-duplicate" }, context("main", project));
  assert.equal(duplicate.block, true);
  assert.match(duplicate.reason, /already succeeded/);

  fs.writeFileSync(source, "externally-changed\n");
  const refreshedRead = await pi.emit("tool_call", { ...firstRead, toolCallId: "read-refreshed" }, context("main", project));
  assert.equal(refreshedRead.input.path, fs.realpathSync(source));
  await pi.emit("tool_result", {
    toolCallId: "read-refreshed",
    toolName: "read",
    input: refreshedRead.input,
    content: [{ type: "text", text: "externally-changed" }],
    isError: false,
  }, context("main", project));

  const refreshedDuplicate = await pi.emit("tool_call", { ...firstRead, toolCallId: "read-refreshed-duplicate" }, context("main", project));
  assert.equal(refreshedDuplicate.block, true);
  assert.match(refreshedDuplicate.reason, /already succeeded/);

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

  const broadAfterMutation = await pi.emit("tool_call", {
    toolCallId: "broad-after-mutation",
    toolName: "bash",
    input: { command: "find ." },
  }, context("main", project));
  assert.equal(broadAfterMutation.block, true);
  assert.match(broadAfterMutation.reason, /mutation begins/);

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

test("verification runtime preserves a stable target and owns the guarded ready to done progression", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-ready-verify-stable-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const project = path.join(root, "project");
  fs.mkdirSync(project, { recursive: true });
  const ticket = path.join(project, "TICKET.md");
  const spec = path.join(project, "SPEC.md");
  const product = path.join(project, "product.js");
  const validator = path.join(root, "validator.py");
  fs.writeFileSync(ticket, "Status: ready\n\n## Verification\n\n- Parent outcome ordinal: 1\n");
  fs.writeFileSync(spec, "Status: approved\n");
  fs.writeFileSync(product, "console.log(process.argv[2] === 'target' ? 'adjusted' : 'original');\n");
  fs.writeFileSync(validator, "print('VALID')\n");
  initGit(project);

  const bindAuthorityFn = async ({ projectRoot, ticketPath }) => ({
    ...binding(projectRoot, ticketPath),
    ticket_sha256: hashFile(ticketPath),
    validator_path: validator,
  });
  const pi = mockPi();
  installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: bindAuthorityFn,
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  await pi.emit("session_start", {}, context("verify", project));
  await armVerify(pi, "verify", project);
  const probeTool = pi.tools.get("ready_probe_binding");
  const probeBindingPath = parseToolResult(await probeTool.execute("probe-binding", {
    ticket_path: ticket,
    project_root: project,
    output_path: path.join(root, "probe-binding.json"),
    target_paths: [product],
    lanes: [],
  })).probe_binding_path;
  const guard = pi.tools.get("ready_guard");
  const argv = pi.tools.get("ready_argv");
  const begun = parseToolResult(await guard.execute("verify-begin", {
    action: "begin_verify",
    ticket_path: ticket,
    project_root: project,
    probe_binding_path: probeBindingPath,
    target_paths: [product],
  }, null, null, context("verify", project)));
  assert.equal(begun.purpose, "verify");
  assert.ok(begun.verification_target.digest);

  const observed = parseToolResult(await argv.execute("verify-exec", {
    action: "execute",
    version: 1,
    argv: [process.execPath, product, "target"],
  }, null, null, context("verify", project)));
  assert.equal(observed.stdout.trim(), "adjusted");
  assert.equal(observed.target_current, true);
  await assert.rejects(
    guard.execute("verify-invalid-complete", {
      action: "complete",
      execution_id: begun.execution_id,
    }, null, null, context("verify", project)),
    /must close through finalize_verification/,
  );

  const finalized = parseToolResult(await guard.execute("verify-finalize", {
    action: "finalize_verification",
    execution_id: begun.execution_id,
    verdict: "VERIFIED",
  }, null, null, context("verify", project)));
  assert.equal(finalized.verification_verdict, "VERIFIED");
  assert.equal(finalized.ticket_progression, "COMPLETED");
  assert.match(fs.readFileSync(ticket, "utf8"), /^Status: done$/m);
});

test("verification runtime fails closed when verifier execution mutates the protected target", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-ready-verify-drift-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const project = path.join(root, "project");
  fs.mkdirSync(project, { recursive: true });
  const ticket = path.join(project, "TICKET.md");
  const spec = path.join(project, "SPEC.md");
  const product = path.join(project, "product.js");
  const validator = path.join(root, "validator.py");
  fs.writeFileSync(ticket, "Status: ready\n\n## Verification\n\n- Parent outcome ordinal: 1\n");
  fs.writeFileSync(spec, "Status: approved\n");
  fs.writeFileSync(product, "console.log(process.argv[2] === 'target' ? 'wrong' : 'original');\n");
  fs.writeFileSync(validator, "print('VALID')\n");
  initGit(project);

  const bindAuthorityFn = async ({ projectRoot, ticketPath }) => ({
    ...binding(projectRoot, ticketPath),
    ticket_sha256: hashFile(ticketPath),
    validator_path: validator,
  });
  const pi = mockPi();
  const runtime = installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: bindAuthorityFn,
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  await pi.emit("session_start", {}, context("verify", project));
  await armVerify(pi, "verify", project);
  const probeTool = pi.tools.get("ready_probe_binding");
  const probeBindingPath = parseToolResult(await probeTool.execute("probe-binding", {
    ticket_path: ticket,
    project_root: project,
    output_path: path.join(root, "probe-binding.json"),
    target_paths: [product],
    lanes: [],
  })).probe_binding_path;
  const guard = pi.tools.get("ready_guard");
  const argv = pi.tools.get("ready_argv");
  const begun = parseToolResult(await guard.execute("verify-begin", {
    action: "begin_verify",
    ticket_path: ticket,
    project_root: project,
    probe_binding_path: probeBindingPath,
    target_paths: [product],
  }, null, null, context("verify", project)));

  const directWrite = await pi.emit("tool_call", {
    toolCallId: "verify-write",
    toolName: "write",
    input: { path: product, content: "console.log('adjusted');\n" },
  }, context("verify", project));
  assert.equal(directWrite.block, true);
  assert.match(directWrite.reason, /immutable/);

  const beforeMutation = parseToolResult(await argv.execute("verify-observe-wrong", {
    action: "execute",
    version: 1,
    argv: [process.execPath, product, "target"],
  }, null, null, context("verify", project)));
  assert.equal(beforeMutation.stdout.trim(), "wrong");
  assert.equal(beforeMutation.target_current, true);

  const mutationScript = `require('node:fs').writeFileSync(${JSON.stringify(product)}, "console.log('adjusted');\\n")`;
  const mutated = parseToolResult(await argv.execute("verify-mutating-exec", {
    action: "execute",
    version: 1,
    argv: [process.execPath, "-e", mutationScript],
  }, null, null, context("verify", project)));
  assert.equal(mutated.target_current, false);
  assert.ok(mutated.target_drift.includes("product.js"));
  assert.equal(runtime.lifecycle.status(begun.execution_id).phase, "TARGET_DRIFT");

  await assert.rejects(
    guard.execute("verify-false-pass", {
      action: "finalize_verification",
      execution_id: begun.execution_id,
      verdict: "VERIFIED",
    }, null, null, context("verify", project)),
    /target drift|VERIFIED blocked/,
  );
  assert.match(fs.readFileSync(ticket, "utf8"), /^Status: ready$/m);

  const closed = parseToolResult(await guard.execute("verify-inconclusive", {
    action: "finalize_verification",
    execution_id: begun.execution_id,
    verdict: "INCONCLUSIVE",
  }, null, null, context("verify", project)));
  assert.equal(closed.verification_verdict, "INCONCLUSIVE");
  assert.equal(closed.ticket_progression, "NOT APPLICABLE");
  assert.match(fs.readFileSync(ticket, "utf8"), /^Status: ready$/m);
});

test("normal ready verification rejects a missing Probe binding before creating an execution", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-ready-verify-missing-probe-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const project = path.join(root, "project");
  fs.mkdirSync(project, { recursive: true });
  const ticket = path.join(project, "TICKET.md");
  const spec = path.join(project, "SPEC.md");
  const product = path.join(project, "product.js");
  const validator = path.join(root, "validator.py");
  fs.writeFileSync(ticket, "Status: ready\n\n## Verification\n\n- Parent outcome ordinal: 1\n");
  fs.writeFileSync(spec, "Status: approved\n");
  fs.writeFileSync(product, "console.log('adjusted');\n");
  fs.writeFileSync(validator, "print('VALID')\n");
  initGit(project);

  const pi = mockPi();
  const runtime = installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => ({
      ...binding(projectRoot, ticketPath),
      ticket_sha256: hashFile(ticketPath),
      validator_path: validator,
    }),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  await pi.emit("session_start", {}, context("verify", project));
  await armVerify(pi, "verify", project);
  const guard = pi.tools.get("ready_guard");
  await assert.rejects(
    guard.execute("verify-begin-missing-probe", {
      action: "begin_verify",
      ticket_path: ticket,
      project_root: project,
      target_paths: [product],
    }, null, null, context("verify", project)),
    /requires one current canonical Probe machine binding/,
  );
  assert.equal(runtime.lifecycle.sessionState("verify").execution_id ?? null, null);
  assert.match(fs.readFileSync(ticket, "utf8"), /^Status: ready$/m);
});

test("diagnostic verification of done requires no Probe and never rewrites status", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-ready-verify-done-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const project = path.join(root, "project");
  fs.mkdirSync(project, { recursive: true });
  const ticket = path.join(project, "TICKET.md");
  const spec = path.join(project, "SPEC.md");
  const product = path.join(project, "product.js");
  const validator = path.join(root, "validator.py");
  fs.writeFileSync(ticket, "Status: done\n\n## Verification\n\n- Parent outcome ordinal: 1\n");
  fs.writeFileSync(spec, "Status: approved\n");
  fs.writeFileSync(product, "console.log('adjusted');\n");
  fs.writeFileSync(validator, "print('VALID')\n");
  initGit(project);
  const initialTicket = fs.readFileSync(ticket, "utf8");

  const pi = mockPi();
  installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => ({
      ...binding(projectRoot, ticketPath),
      ticket_sha256: hashFile(ticketPath),
      ticket_status_at_start: "done",
      validator_path: validator,
    }),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  await pi.emit("session_start", {}, context("verify", project));
  await armVerify(pi, "verify", project);
  const guard = pi.tools.get("ready_guard");
  const argv = pi.tools.get("ready_argv");
  const begun = parseToolResult(await guard.execute("verify-done-begin", {
    action: "begin_verify",
    ticket_path: ticket,
    project_root: project,
    target_paths: [product],
  }, null, null, context("verify", project)));
  assert.equal(begun.purpose, "verify");

  const observed = parseToolResult(await argv.execute("verify-done-exec", {
    action: "execute",
    version: 1,
    argv: [process.execPath, product],
  }, null, null, context("verify", project)));
  assert.equal(observed.stdout.trim(), "adjusted");
  assert.equal(observed.target_current, true);

  const finalized = parseToolResult(await guard.execute("verify-done-finalize", {
    action: "finalize_verification",
    execution_id: begun.execution_id,
    verdict: "VERIFIED",
  }, null, null, context("verify", project)));
  assert.equal(finalized.verification_verdict, "VERIFIED");
  assert.equal(finalized.ticket_progression, "NOT APPLICABLE");
  assert.equal(finalized.ticket_status_after, "done");
  assert.equal(fs.readFileSync(ticket, "utf8"), initialTicket);
});

test("verification finalization rejects a foreign session before mutating Ticket status", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-ready-verify-finalize-owner-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const project = path.join(root, "project");
  fs.mkdirSync(project, { recursive: true });
  const ticket = path.join(project, "TICKET.md");
  const spec = path.join(project, "SPEC.md");
  const product = path.join(project, "product.js");
  const validator = path.join(root, "validator.py");
  fs.writeFileSync(ticket, "Status: ready\n\n## Verification\n\n- Parent outcome ordinal: 1\n");
  fs.writeFileSync(spec, "Status: approved\n");
  fs.writeFileSync(product, "console.log('adjusted');\n");
  fs.writeFileSync(validator, "print('VALID')\n");
  initGit(project);
  const initialTicket = fs.readFileSync(ticket, "utf8");

  const pi = mockPi();
  const runtime = installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => ({
      ...binding(projectRoot, ticketPath),
      ticket_sha256: hashFile(ticketPath),
      validator_path: validator,
    }),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  await armVerify(pi, "owner", project);
  const probeBindingPath = parseToolResult(await pi.tools.get("ready_probe_binding").execute("probe-binding", {
    ticket_path: ticket,
    project_root: project,
    output_path: path.join(root, "probe-binding.json"),
    target_paths: [product],
    lanes: [],
  })).probe_binding_path;
  const guard = pi.tools.get("ready_guard");
  const begun = parseToolResult(await guard.execute("verify-begin", {
    action: "begin_verify",
    ticket_path: ticket,
    project_root: project,
    probe_binding_path: probeBindingPath,
    target_paths: [product],
  }, null, null, context("owner", project)));

  await assert.rejects(
    guard.execute("verify-foreign-finalize", {
      action: "finalize_verification",
      execution_id: begun.execution_id,
      verdict: "VERIFIED",
    }, null, null, context("foreign", project)),
    /does not own Ready execution/,
  );
  assert.equal(fs.readFileSync(ticket, "utf8"), initialTicket);
  assert.equal(runtime.lifecycle.status(begun.execution_id).phase, "ACTIVE");
});

test("verification finalization rejects an active guarded operation before mutating Ticket status", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-ready-verify-finalize-operation-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const project = path.join(root, "project");
  fs.mkdirSync(project, { recursive: true });
  const ticket = path.join(project, "TICKET.md");
  const spec = path.join(project, "SPEC.md");
  const product = path.join(project, "product.js");
  const validator = path.join(root, "validator.py");
  fs.writeFileSync(ticket, "Status: ready\n\n## Verification\n\n- Parent outcome ordinal: 1\n");
  fs.writeFileSync(spec, "Status: approved\n");
  fs.writeFileSync(product, "console.log('adjusted');\n");
  fs.writeFileSync(validator, "print('VALID')\n");
  initGit(project);
  const initialTicket = fs.readFileSync(ticket, "utf8");

  const pi = mockPi();
  const runtime = installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => ({
      ...binding(projectRoot, ticketPath),
      ticket_sha256: hashFile(ticketPath),
      validator_path: validator,
    }),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  await armVerify(pi, "owner", project);
  const probeBindingPath = parseToolResult(await pi.tools.get("ready_probe_binding").execute("probe-binding", {
    ticket_path: ticket,
    project_root: project,
    output_path: path.join(root, "probe-binding.json"),
    target_paths: [product],
    lanes: [],
  })).probe_binding_path;
  const guard = pi.tools.get("ready_guard");
  const begun = parseToolResult(await guard.execute("verify-begin", {
    action: "begin_verify",
    ticket_path: ticket,
    project_root: project,
    probe_binding_path: probeBindingPath,
    target_paths: [product],
  }, null, null, context("owner", project)));
  runtime.lifecycle.beginOperation(begun.execution_id, {
    toolCallId: "still-running-observation",
    kind: "observation",
  });

  await assert.rejects(
    guard.execute("verify-active-operation-finalize", {
      action: "finalize_verification",
      execution_id: begun.execution_id,
      verdict: "VERIFIED",
    }, null, null, context("owner", project)),
    /operation is active/,
  );
  assert.equal(fs.readFileSync(ticket, "utf8"), initialTicket);
  assert.equal(runtime.lifecycle.status(begun.execution_id).phase, "ACTIVE");
});

test("delegated verification binds its target before PRE_ACTION and waits for Parent CONTINUE before runtime execution", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-ready-verify-subagent-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const project = path.join(root, "project");
  fs.mkdirSync(project, { recursive: true });
  const ticket = path.join(project, "TICKET.md");
  const spec = path.join(project, "SPEC.md");
  const product = path.join(project, "product.js");
  const validator = path.join(root, "validator.py");
  fs.writeFileSync(ticket, "Status: ready\n\n## Verification\n\n- Parent outcome ordinal: 1\n");
  fs.writeFileSync(spec, "Status: approved\n");
  fs.writeFileSync(product, "console.log('adjusted');\n");
  fs.writeFileSync(validator, "print('VALID')\n");
  initGit(project);

  const pi = mockPi();
  installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => ({
      ...binding(projectRoot, ticketPath),
      ticket_sha256: hashFile(ticketPath),
      validator_path: validator,
    }),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  await armVerify(pi, "parent", project);
  await armVerify(pi, "child", project);
  const probeBindingPath = parseToolResult(await pi.tools.get("ready_probe_binding").execute("probe-binding", {
    ticket_path: ticket,
    project_root: project,
    output_path: path.join(root, "probe-binding.json"),
    target_paths: [product],
    lanes: [],
  })).probe_binding_path;
  const guard = pi.tools.get("ready_guard");
  const argv = pi.tools.get("ready_argv");
  const assignment = parseToolResult(await guard.execute("verify-assign", {
    action: "assign_subagent",
    ticket_path: ticket,
    project_root: project,
  }, null, null, context("parent", project)));
  const begun = parseToolResult(await guard.execute("verify-child-begin", {
    action: "begin_delegated",
    assignment_id: assignment.assignment_id,
    probe_binding_path: probeBindingPath,
    target_paths: [product],
  }, null, null, context("child", project)));
  assert.equal(begun.purpose, "verify");
  assert.equal(begun.phase, "PRE_ACTION_PENDING");
  assert.ok(begun.verification_target.digest);

  await assert.rejects(
    guard.execute("verify-child-finalize-too-early", {
      action: "finalize_verification",
      execution_id: begun.execution_id,
      verdict: "VERIFIED",
    }, null, null, context("child", project)),
    /cannot finalize from phase PRE_ACTION_PENDING/,
  );
  assert.match(fs.readFileSync(ticket, "utf8"), /^Status: ready$/m);

  await assert.rejects(
    argv.execute("verify-child-too-early", {
      action: "execute",
      version: 1,
      argv: [process.execPath, product],
    }, null, null, context("child", project)),
    /requires ACTIVE verification/,
  );
  const externalBeforeContinue = await pi.emit("tool_call", {
    toolCallId: "verify-external-too-early",
    toolName: "browser",
    input: { action: "inspect" },
  }, context("child", project));
  assert.equal(externalBeforeContinue.block, true);
  assert.match(externalBeforeContinue.reason, /Parent CONTINUE|ACTIVE/);

  const checkpoint = parseToolResult(await guard.execute("verify-pre-action", {
    action: "checkpoint_pre_action",
    execution_id: begun.execution_id,
    summary: "scenario ready",
  }, null, null, context("child", project)));
  assert.equal(checkpoint.phase, "PRE_ACTION_PENDING");
  const released = parseToolResult(await guard.execute("verify-pre-action-continue", {
    action: "release_checkpoint",
    execution_id: begun.execution_id,
    decision: "CONTINUE",
  }, null, null, context("parent", project)));
  assert.equal(released.phase, "ACTIVE");

  const observed = parseToolResult(await argv.execute("verify-child-active", {
    action: "execute",
    version: 1,
    argv: [process.execPath, product],
  }, null, null, context("child", project)));
  assert.equal(observed.stdout.trim(), "adjusted");
});

test("verification runtime refreshes the same runtime readback after an allowed runtime-state change", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-ready-verify-runtime-refresh-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const project = path.join(root, "project");
  fs.mkdirSync(project, { recursive: true });
  const ticket = path.join(project, "TICKET.md");
  const spec = path.join(project, "SPEC.md");
  const product = path.join(project, "product.js");
  const runtimeState = path.join(project, "runtime-state.txt");
  const validator = path.join(root, "validator.py");
  fs.writeFileSync(ticket, "Status: ready\n\n## Verification\n\n- Parent outcome ordinal: 1\n");
  fs.writeFileSync(spec, "Status: approved\n");
  fs.writeFileSync(runtimeState, "0\n");
  fs.writeFileSync(product, [
    "const fs = require('node:fs');",
    "const statePath = process.argv[2];",
    "if (process.argv[3] === 'set') fs.writeFileSync(statePath, '1\\n');",
    "process.stdout.write(fs.readFileSync(statePath, 'utf8'));",
    "",
  ].join("\n"));
  fs.writeFileSync(validator, "print('VALID')\n");
  initGit(project);

  const pi = mockPi();
  installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => ({
      ...binding(projectRoot, ticketPath),
      ticket_sha256: hashFile(ticketPath),
      validator_path: validator,
    }),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  await armVerify(pi, "verify", project);
  const probeBindingPath = parseToolResult(await pi.tools.get("ready_probe_binding").execute("probe-binding", {
    ticket_path: ticket,
    project_root: project,
    output_path: path.join(root, "probe-binding.json"),
    target_paths: [product],
    allowed_output_paths: [runtimeState],
    lanes: [],
  })).probe_binding_path;
  const guard = pi.tools.get("ready_guard");
  const argv = pi.tools.get("ready_argv");
  parseToolResult(await guard.execute("verify-begin", {
    action: "begin_verify",
    ticket_path: ticket,
    project_root: project,
    probe_binding_path: probeBindingPath,
    target_paths: [product],
    allowed_output_paths: [runtimeState],
  }, null, null, context("verify", project)));

  const before = parseToolResult(await argv.execute("runtime-state-before", {
    action: "execute",
    version: 1,
    argv: [process.execPath, product, runtimeState, "status"],
  }, null, null, context("verify", project)));
  assert.equal(before.stdout.trim(), "0");

  const changed = parseToolResult(await argv.execute("runtime-state-change", {
    action: "execute",
    version: 1,
    argv: [process.execPath, product, runtimeState, "set"],
  }, null, null, context("verify", project)));
  assert.equal(changed.stdout.trim(), "1");
  assert.equal(changed.target_current, true);

  const after = parseToolResult(await argv.execute("runtime-state-after", {
    action: "execute",
    version: 1,
    argv: [process.execPath, product, runtimeState, "status"],
  }, null, null, context("verify", project)));
  assert.equal(after.stdout.trim(), "1");
  assert.equal(after.target_current, true);
});

async function finalizationRaceFixture(t, {
  validatorSource = "print('VALID')\n",
  checkAuthorityCurrentnessFn = async () => ({ current: true, changed: [] }),
} = {}) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-ready-verify-finalization-race-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const project = path.join(root, "project");
  fs.mkdirSync(project, { recursive: true });
  const ticket = path.join(project, "TICKET.md");
  const spec = path.join(project, "SPEC.md");
  const product = path.join(project, "product.js");
  const validator = path.join(root, "validator.py");
  fs.writeFileSync(ticket, "Status: ready\n\n## Verification\n\n- Parent outcome ordinal: 1\n");
  fs.writeFileSync(spec, "Status: approved\n");
  fs.writeFileSync(product, "console.log('adjusted');\n");
  fs.writeFileSync(validator, validatorSource);
  initGit(project);

  const pi = mockPi();
  const runtime = installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => ({
      ...binding(projectRoot, ticketPath),
      ticket_sha256: hashFile(ticketPath),
      validator_path: validator,
    }),
    checkAuthorityCurrentness: checkAuthorityCurrentnessFn,
  });
  const ctx = context("verify", project);
  await armVerify(pi, "verify", project);
  const probeBindingPath = parseToolResult(await pi.tools.get("ready_probe_binding").execute("probe-binding", {
    ticket_path: ticket,
    project_root: project,
    output_path: path.join(root, "probe-binding.json"),
    target_paths: [product],
    lanes: [],
  })).probe_binding_path;
  const guard = pi.tools.get("ready_guard");
  const begun = parseToolResult(await guard.execute("verify-begin", {
    action: "begin_verify",
    ticket_path: ticket,
    project_root: project,
    probe_binding_path: probeBindingPath,
    target_paths: [product],
  }, null, null, ctx));
  return { pi, runtime, ctx, guard, begun, ticket };
}

test("verification finalization cancels before Ticket progression when session recovery clears the reservation during authority wait", async t => {
  for (const eventName of ["session_shutdown", "session_switch", "session_branch", "session_start"]) {
    await t.test(eventName, async st => {
      let enteredAuthority;
      let releaseAuthority;
      const authorityEntered = new Promise(resolve => { enteredAuthority = resolve; });
      const authorityRelease = new Promise(resolve => { releaseAuthority = resolve; });
      const fixture = await finalizationRaceFixture(st, {
        checkAuthorityCurrentnessFn: async () => {
          enteredAuthority();
          await authorityRelease;
          return { current: true, changed: [] };
        },
      });
      const finalizing = fixture.guard.execute("verify-finalize", {
        action: "finalize_verification",
        execution_id: fixture.begun.execution_id,
        verdict: "VERIFIED",
      }, null, null, fixture.ctx).then(
        value => ({ ok: true, value }),
        error => ({ ok: false, error: error.message }),
      );

      await authorityEntered;
      await fixture.pi.emit(eventName, {}, fixture.ctx);
      releaseAuthority();
      const result = await finalizing;

      assert.equal(result.ok, false);
      assert.match(result.error, /finalization reservation is not active/);
      assert.match(fs.readFileSync(fixture.ticket, "utf8"), /^Status: ready$/m);
      assert.equal(fixture.runtime.lifecycle.status(fixture.begun.execution_id).phase, "ACTIVE");
    });
  }
});

test("verification finalization closes before session shutdown can interleave after Ticket progression begins", async t => {
  const fixture = await finalizationRaceFixture(t, {
    validatorSource: "import time\ntime.sleep(0.15)\nprint('VALID')\n",
  });
  const order = [];
  const shutdown = new Promise((resolve, reject) => {
    setTimeout(() => {
      fixture.pi.emit("session_shutdown", {}, fixture.ctx).then(() => {
        order.push("shutdown");
        resolve();
      }, reject);
    }, 25);
  });

  const finalized = parseToolResult(await fixture.guard.execute("verify-finalize", {
    action: "finalize_verification",
    execution_id: fixture.begun.execution_id,
    verdict: "VERIFIED",
  }, null, null, fixture.ctx));
  order.push("finalized");
  await shutdown;

  assert.equal(order[0], "finalized");
  assert.equal(finalized.verification_verdict, "VERIFIED");
  assert.equal(finalized.ticket_progression, "COMPLETED");
  assert.equal(finalized.ticket_status_after, "done");
  assert.match(fs.readFileSync(fixture.ticket, "utf8"), /^Status: done$/m);
  assert.equal(fixture.runtime.lifecycle.status(fixture.begun.execution_id).phase, "COMPLETE");
});
