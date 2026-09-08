import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import http from "node:http";
import test from "node:test";
import { fixture, executeArgv } from "./helpers.js";
import { installReadyRuntime } from "../src/omp-adapter.js";

// Schema is supplied by the real OMP loader; these tests exercise policy, not Zod forwarding.
const schema = { optional() { return this; } };
const zod = { object: () => schema, enum: () => schema, string: () => schema, array: () => schema, literal: () => schema };
function host(f, options = {}) {
  const handlers = {}, tools = {};
  let initialized = false;
  const pi = { on(name, fn) { handlers[name] = fn; }, registerTool(tool) { tools[tool.name] = tool; }, getAllTools() { if (!initialized) throw new Error("Extension runtime not initialized"); return ["read", "write", "edit", "grep", "glob", "hub", "todo", "bash"].map(name => ({ name, sourceInfo: { source: "builtin" } })); }, async exec(command, args, request) { const result = await executeArgv([command, ...args], request); return { code: result.exitCode, killed: result.interrupted, stdout: result.stdout, stderr: result.stderr }; } };
  pi.zod = zod;
  const runtime = installReadyRuntime(pi, { store: f.store, validatorPath: f.validatorPath, ...options });
  initialized = true;
  handlers.resources_discover();
  const context = actor => ({ cwd: f.root, sessionManager: { getSessionId: () => actor } });
  const guard = (actor, input) => tools.ready_guard.execute("guard", input, undefined, undefined, context(actor));
  return { handlers, tools, runtime, context, guard };
}

test("resource reads and authority inspection never arm; reviewed begin allows actual file mutation", async t => {
  const f = await fixture(t), h = host(f);
  await h.handlers.resources_discover();
  assert.equal(await h.handlers.tool_call({ toolName: "read", toolCallId: "read", input: { path: "skill://ready-ticket-implement" } }, h.context("worker")), undefined);
  await h.guard("worker", { action: "inspect_authority", project_root: f.root, ticket_path: f.ticket });
  assert.equal(f.store.readSession("worker"), null);
  const result = await h.guard("worker", { action: "begin_direct", project_root: f.root, ticket_path: f.ticket, plan_review_path: f.review });
  const state = result.details;
  assert.equal((await h.handlers.tool_call({ toolName: "write", toolCallId: "protected", input: { path: f.plan, content: "bad" } }, h.context("worker"))).block, true);
  const cli = path.join(f.root, "cli.js");
  assert.equal(await h.handlers.tool_call({ toolName: "write", toolCallId: "write", input: { path: cli, content: "console.log('changed')" } }, h.context("worker")), undefined);
  fs.writeFileSync(cli, "console.log('changed')");
  await h.handlers.tool_result({ toolName: "write", toolCallId: "write", isError: false });
  assert.equal((await executeArgv([process.execPath, cli], { cwd: f.root })).stdout.trim(), "changed");
  assert.equal(await h.handlers.tool_call({ toolName: "todo", toolCallId: "progress", input: { op: "done", task: "actual CLI check" } }, h.context("worker")), undefined);
  await h.guard("worker", { action: "complete", execution_id: state.execution_id });
  assert.equal((await h.handlers.tool_call({ toolName: "unknown", toolCallId: "late", input: {} }, h.context("worker"))).block, true);
  assert.equal(await h.handlers.tool_call({ toolName: "todo", toolCallId: "close-checklist", input: { op: "done", task: "implementation complete" } }, h.context("worker")), undefined);
  assert.equal((await h.handlers.tool_call({ toolName: "write", toolCallId: "late-file", input: { path: cli, content: "bad" } }, h.context("worker"))).block, true);
});

test("blocked owner can close its checklist without reopening product dispatch", async t => {
  const f = await fixture(t), h = host(f);
  const state = (await h.guard("worker", { action: "begin_direct", project_root: f.root, ticket_path: f.ticket, plan_review_path: f.review })).details;
  await h.guard("worker", { action: "block", execution_id: state.execution_id, reason: "required external condition contradicted" });
  assert.equal(await h.handlers.tool_call({ toolName: "todo", toolCallId: "close", input: { op: "block", task: "dependent implementation" } }, h.context("worker")), undefined);
  assert.equal(await h.handlers.tool_call({ toolName: "write", toolCallId: "device-close", input: { path: "xd://todo", content: JSON.stringify({ op: "done", task: "report blocker" }) } }, h.context("worker")), undefined);
  assert.equal((await h.handlers.tool_call({ toolName: "write", toolCallId: "late-file", input: { path: path.join(f.root, "cli.js"), content: "bad" } }, h.context("worker"))).block, true);
  assert.equal(f.store.readExecution(state.execution_id).phase, "BLOCKED");
  assert.equal(f.store.readActiveTicket(f.root, f.ticket), null);
});

test("checklist transport remains fenced for a suspended worker", async t => {
  const f = await fixture(t), h = host(f);
  const assignment = (await h.guard("parent", { action: "assign_subagent", project_root: f.root, ticket_path: f.ticket, plan_review_path: f.review })).details;
  const state = (await h.guard("child", { action: "begin_delegated", assignment_id: assignment.assignment_id })).details;
  const todo = { toolName: "write", toolCallId: "checklist", input: { path: "xd://todo", content: JSON.stringify({ op: "done", task: "bounded work" }) } };
  assert.equal(await h.handlers.tool_call(todo, h.context("child")), undefined);
  await h.guard("child", { action: "suspend_worker", execution_id: state.execution_id });
  assert.equal((await h.handlers.tool_call(todo, h.context("child"))).block, true);
  assert.equal(await h.handlers.tool_call({ toolName: "todo", toolCallId: "parent-checklist", input: { op: "done", task: "worker settled" } }, h.context("parent")), undefined);
  await h.guard("parent", { action: "replace_worker", execution_id: state.execution_id, plan_review_path: f.review });
  assert.equal((await h.handlers.tool_call(todo, h.context("child"))).block, true);
});

test("native/device unknown effects and paused file writes cannot bypass owner fence", async t => {
  const f = await fixture(t), h = host(f);
  const state = (await h.guard("worker", { action: "begin_direct", project_root: f.root, ticket_path: f.ticket, plan_review_path: f.review })).details;
  const unknown = await h.handlers.tool_call({ toolName: "write", toolCallId: "device", input: { path: "xd://arbitrary-command", content: "{}" } }, h.context("worker"));
  assert.equal(unknown.block, true);
  await h.guard("worker", { action: "checkpoint", execution_id: state.execution_id, kind: "MATERIAL_TURN" });
  assert.equal((await h.handlers.tool_call({ toolName: "write", toolCallId: "paused", input: { path: path.join(f.root, "cli.js"), content: "bad" } }, h.context("worker"))).block, true);
  assert.equal(await h.handlers.tool_call({ toolName: "read", toolCallId: "read", input: { path: f.ticket } }, h.context("worker")), undefined);
});

test("loopback effect survives command response timeout and cannot be replayed from unchanged source hashes", async t => {
  const f = await fixture(t);
  let counter = 0;
  const server = http.createServer((_request, response) => { counter += 1; response.end("applied"); });
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  t.after(() => new Promise(resolve => server.close(resolve)));
  const h = host(f, { executeArgv: async (argv, request) => executeArgv(argv, { ...request, timeout: argv[0] === process.execPath ? 700 : request.timeout }) });
  const evidence = path.join(f.base, "effect-resolution.json");
  const state = (await h.guard("worker", { action: "begin_direct", project_root: f.root, ticket_path: f.ticket, plan_review_path: f.review, allowed_output_paths: [evidence] })).details;
  const argv = [process.execPath, "-e", `require('http').get('http://127.0.0.1:${server.address().port}',r=>r.resume());setInterval(()=>{},1000)`];
  const result = await h.tools.ready_argv.execute("run", { action: "execute", version: 1, argv }, undefined, undefined, h.context("worker"));
  assert.equal(counter, 1);
  assert.equal(result.details.execution.phase, "EFFECT_UNCERTAIN");
  assert.equal(fs.existsSync(result.details.output_ref), true);
  await assert.rejects(h.tools.ready_argv.execute("replay", { action: "execute", version: 1, argv }, undefined, undefined, h.context("worker")), /ACTIVE/);
  await h.guard("worker", { action: "block", execution_id: state.execution_id, reason: "awaiting authoritative readback" });
  assert.ok(f.store.readActiveTicket(f.root, f.ticket));
  const record = { execution_id: state.execution_id, operation_id: result.details.operation_id, effect_surface: result.details.effect_surface, owner: "worker", outcome: "applied", readback_reference: "loopback server counter observed as 1" };
  assert.equal(await h.handlers.tool_call({ toolName: "write", toolCallId: "report", input: { path: evidence, content: JSON.stringify(record) } }, h.context("worker")), undefined);
  fs.writeFileSync(evidence, JSON.stringify(record));
  assert.equal(h.runtime.lifecycle.status(state.execution_id).phase, "EFFECT_UNCERTAIN");
  assert.equal((await h.handlers.tool_call({ toolName: "write", toolCallId: "product-during-recovery", input: { path: path.join(f.root, "cli.js"), content: "bad" } }, h.context("worker"))).block, true);
  await assert.rejects(h.tools.ready_argv.execute("still-no-replay", { action: "execute", version: 1, argv }, undefined, undefined, h.context("worker")), /ACTIVE/);
  await h.guard("worker", { action: "resolve_mutation", execution_id: state.execution_id, operation_id: record.operation_id, effect_surface: record.effect_surface, outcome: "applied", evidence_reference: evidence });
  await h.guard("worker", { action: "release_checkpoint", execution_id: state.execution_id, decision: "CONTINUE" });
  await h.guard("worker", { action: "complete", execution_id: state.execution_id });
  assert.equal(f.store.readActiveTicket(f.root, f.ticket), null);
  assert.equal(counter, 1);
});

test("readiness timeout retains owned service and wrong generation result cannot settle it", async t => {
  const f = await fixture(t), h = host(f);
  const state = (await h.guard("worker", { action: "begin_direct", project_root: f.root, ticket_path: f.ticket, plan_review_path: f.review })).details;
  const name = `ready-${state.execution_id}`;
  await h.handlers.tool_call({ toolName: "hub", toolCallId: "start", input: { op: "start", name, application: process.execPath, ready: { port: 34567 }, cwd: f.root } }, h.context("worker"));
  const daemon = { id: "native-resource", name, owner: "native-owner-not-session-id", startedAt: 100, restartCount: 0, state: "starting", persist: false, detached: false };
  await h.handlers.tool_result({ toolName: "hub", toolCallId: "start", isError: false, details: { daemon, timedOut: true } });
  await assert.rejects(h.runtime.lifecycle.complete(state.execution_id, "worker"), /service/);
  await h.handlers.tool_call({ toolName: "hub", toolCallId: "stop", input: { op: "stop", name } }, h.context("worker"));
  await h.handlers.tool_result({ toolName: "hub", toolCallId: "stop", isError: false, details: { daemon: { ...daemon, id: "replacement-resource", startedAt: 200, state: "exited" } } });
  assert.equal(h.runtime.lifecycle.status(state.execution_id).phase, "EFFECT_UNCERTAIN");
  assert.equal(h.runtime.lifecycle.status(state.execution_id).owned_service.resourceId, "native-resource");
});

test("exact hub device result settles the same owned generation before complete", async t => {
  const f = await fixture(t), h = host(f);
  const state = (await h.guard("worker", { action: "begin_direct", project_root: f.root, ticket_path: f.ticket, plan_review_path: f.review })).details;
  const name = `ready-${state.execution_id}`;
  const request = { op: "start", name, application: process.execPath, ready: { port: 34567 }, cwd: f.root };
  assert.equal(await h.handlers.tool_call({ toolName: "write", toolCallId: "device-start", input: { path: "xd://hub", content: JSON.stringify(request) } }, h.context("worker")), undefined);
  assert.equal((await h.handlers.tool_call({ toolName: "hub", toolCallId: "device-start", input: { ...request, name: "foreign-service" } }, h.context("worker"))).block, true);
  assert.equal(await h.handlers.tool_call({ toolName: "hub", toolCallId: "device-start", input: request }, h.context("worker")), undefined);
  assert.equal((await h.handlers.tool_call({ toolName: "hub", toolCallId: "device-start", input: request }, h.context("worker"))).block, true);
  const daemon = { id: "device-owned-resource", name, owner: "host-owner", startedAt: 100, restartCount: 0, state: "ready", readyAt: 101, persist: false, detached: false };
  await h.handlers.tool_result({ toolName: "hub", toolCallId: "device-start", isError: false, details: { daemon } });
  await h.handlers.tool_result({ toolName: "write", toolCallId: "device-start", isError: false, details: { xdev: { tool: "hub", inner: { daemon } } } });
  await h.handlers.tool_call({ toolName: "write", toolCallId: "device-stop", input: { path: "xd://hub", content: JSON.stringify({ op: "stop", name }) } }, h.context("worker"));
  assert.equal(await h.handlers.tool_call({ toolName: "hub", toolCallId: "device-stop", input: { op: "stop", name } }, h.context("worker")), undefined);
  await h.handlers.tool_result({ toolName: "hub", toolCallId: "device-stop", isError: false, details: { daemon: { ...daemon, state: "exited" } } });
  await h.handlers.tool_result({ toolName: "write", toolCallId: "device-stop", isError: false, details: { xdev: { tool: "hub", inner: { daemon: { ...daemon, state: "exited" } } } } });
  await h.runtime.lifecycle.complete(state.execution_id, "worker");
  assert.equal(f.store.readActiveTicket(f.root, f.ticket), null);
});
