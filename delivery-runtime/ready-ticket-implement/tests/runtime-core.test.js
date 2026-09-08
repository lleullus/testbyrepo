import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fixture } from "./helpers.js";
import { RuntimeStore } from "../src/core.js";
import { isReadOnlyArgv, validateExecutionRequest } from "../src/argv-policy.js";

test("current reviewed DIRECT starts ACTIVE, performs real CLI change, and closes without read quota", async t => {
  const f = await fixture(t);
  await assert.rejects(f.lifecycle.beginDirect({ sessionId: "worker", projectRoot: f.root, ticketPath: f.ticket }), /PLAN_REVIEW_REQUIRED/);
  assert.equal(f.store.readActiveTicket(f.root, f.ticket), null);
  const state = await f.lifecycle.beginDirect({ sessionId: "worker", ...f.input });
  assert.equal(state.phase, "ACTIVE");
  const operation = f.lifecycle.beginOperation(state.execution_id, "worker", { kind: "local_file", effect_surface: "cli.js" });
  fs.writeFileSync(path.join(f.root, "cli.js"), "console.log('changed observable output');\n");
  f.lifecycle.finishOperation(state.execution_id, "worker", operation.operation_id);
  const actual = await f.lifecycle.executeArgv([process.execPath, "cli.js"], { cwd: f.root });
  assert.equal(actual.stdout.trim(), "changed observable output");
  await f.lifecycle.complete(state.execution_id, "worker");
  assert.equal(f.store.readActiveTicket(f.root, f.ticket), null);
  assert.throws(() => f.lifecycle.assertDispatch(state.execution_id, "worker"), /SUPERSEDED|COMPLETE/);
});

test("assignment is one-use and old owner cannot dispatch or deliver late results after replacement", async t => {
  const f = await fixture(t);
  const assignment = await f.lifecycle.assignSubagent({ parentSessionId: "parent", ...f.input });
  const old = await f.lifecycle.beginDelegated({ childSessionId: "old", assignmentId: assignment.assignment_id });
  assert.equal(old.phase, "ACTIVE");
  await assert.rejects(f.lifecycle.beginDelegated({ childSessionId: "other", assignmentId: assignment.assignment_id }), /one-use/);
  const op = f.lifecycle.beginOperation(old.execution_id, "old", { kind: "local_file", effect_surface: "cli.js" });
  assert.throws(() => f.lifecycle.suspendWorker(old.execution_id, "old"), /settle/);
  f.lifecycle.finishOperation(old.execution_id, "old", op.operation_id);
  f.lifecycle.suspendWorker(old.execution_id, "old");
  const replacement = await f.lifecycle.replaceWorker(old.execution_id, "parent");
  const current = await f.lifecycle.beginDelegated({ childSessionId: "new", assignmentId: replacement.assignment_id });
  assert.equal(current.phase, "ACTIVE");
  assert.throws(() => f.lifecycle.assertDispatch(old.execution_id, "old"), /inactive|SUPERSEDED/);
  assert.throws(() => f.lifecycle.finishOperation(old.execution_id, "old", op.operation_id), /inactive|SUPERSEDED/);
  assert.equal(f.lifecycle.assertDispatch(current.execution_id, "new", true).session_id, "new");
});

test("plan drift pauses mutation and parent CONTINUE cannot substitute current review", async t => {
  const f = await fixture(t);
  const state = await f.lifecycle.beginDirect({ sessionId: "worker", ...f.input });
  fs.appendFileSync(f.plan, "\nChanged shared owner.\n");
  await assert.rejects(f.lifecycle.ensureCurrent(state.execution_id, "worker", { effect: true }), /PLAN_DRIFT/);
  assert.equal(f.lifecycle.assertDispatch(state.execution_id, "worker").phase, "PAUSED");
  await assert.rejects(f.lifecycle.releaseCheckpoint(state.execution_id, "worker", "CONTINUE"), /PLAN_REVIEW_REQUIRED/);
  await assert.rejects(f.lifecycle.releaseCheckpoint(state.execution_id, "worker", "CONTINUE", { planReviewPath: f.review }), /PLAN_REVIEW_STALE/);
});

test("uncertain opaque effect retains slot even after BLOCKED report and needs exact owner readback", async t => {
  const f = await fixture(t);
  const state = await f.lifecycle.beginDirect({ sessionId: "worker", ...f.input });
  const operation = f.lifecycle.beginOperation(state.execution_id, "worker", { kind: "opaque_program", effect_surface: "loopback-counter" });
  f.lifecycle.finishOperation(state.execution_id, "worker", operation.operation_id, { uncertain: true, detail: "response lost after remote effect" });
  f.lifecycle.block(state.execution_id, "worker", "cannot establish readback yet");
  assert.equal(f.lifecycle.status(state.execution_id).phase, "EFFECT_UNCERTAIN");
  await assert.rejects(f.lifecycle.beginDirect({ sessionId: "other", ...f.input }), /TICKET_BUSY/);
  assert.throws(() => f.lifecycle.beginOperation(state.execution_id, "worker", { kind: "opaque_program" }), /ACTIVE/);
  const evidence = path.join(f.base, "recovery.json");
  fs.writeFileSync(evidence, JSON.stringify({ execution_id: state.execution_id, operation_id: operation.operation_id, effect_surface: "loopback-counter", owner: "worker", outcome: "applied", readback_reference: "operator-owned counter readback" }));
  f.lifecycle.resolveMutationUncertainty(state.execution_id, "worker", { operationId: operation.operation_id, effectSurface: "loopback-counter", evidenceReference: evidence, outcome: "applied" });
  await f.lifecycle.releaseCheckpoint(state.execution_id, "worker", "CONTINUE");
  assert.equal(f.lifecycle.status(state.execution_id).phase, "ACTIVE");
});

test("reservation crash preserves exclusion; designated evidence cleanup permits fresh start and rejects late commit", async t => {
  const f = await fixture(t, { recoveryOwner: "recovery" });
  const binding = await f.lifecycle.prepare(f.input);
  const reservation = f.lifecycle.reserve(binding, "worker", {});
  await assert.rejects(f.lifecycle.beginDirect({ sessionId: "other", ...f.input }), /TICKET_BUSY/);
  const evidence = path.join(f.base, "orphan.json");
  fs.writeFileSync(evidence, JSON.stringify({ reservation_id: reservation.identity, project_root: f.root, ticket_path: f.ticket, owner: "recovery", admission_disposition: "terminated_or_withdrawn", live_work: "absent", uncertain_effects: "absent", readback_reference: "operator inspected terminated invocation and effects" }));
  assert.equal(f.lifecycle.recoverAdmission({ actor: "recovery", projectRoot: f.root, ticketPath: f.ticket, reservationId: reservation.identity, recoveryEvidenceReference: evidence }).released, true);
  const fresh = await f.lifecycle.beginDirect({ sessionId: "worker", ...f.input });
  assert.throws(() => f.store.withLock(() => f.lifecycle.commitExecution(f.lifecycle.newExecution(binding, "worker", reservation), reservation)), /ADMISSION_REVOKED/);
  assert.equal(f.store.readActiveTicket(f.root, f.ticket).execution_id, fresh.execution_id);
});

test("state rejects v1 records and never steals an old live lock", async t => {
  const f = await fixture(t);
  fs.writeFileSync(path.join(f.store.executions, "legacy.json"), JSON.stringify({ schema_version: 1, phase: "ACTIVE" }));
  assert.throws(() => f.store.readExecution("legacy"), /STATE_SCHEMA_UNSUPPORTED/);
  const lock = path.join(f.store.locks, "state.lock");
  fs.writeFileSync(lock, JSON.stringify({ pid: process.pid })); fs.utimesSync(lock, 0, 0);
  assert.throws(() => f.store.withLock(() => true), /STATE_LOCK_BUSY/);
  assert.equal(fs.existsSync(lock), true);
  assert.throws(() => new RuntimeStore(f.store.root).readExecution("../escape"), /invalid execution/);
});

test("inspection argv cannot perform hidden writes or invoke shell paths", () => {
  assert.equal(isReadOnlyArgv(["sed", "-n", "1,20p", "file"]), true);
  assert.equal(isReadOnlyArgv(["sed", "-i", "s/a/b/", "file"]), false);
  assert.equal(isReadOnlyArgv(["find", ".", "-delete"]), false);
  assert.equal(isReadOnlyArgv(["git", "diff", "--ext-diff"]), false);
  assert.throws(() => validateExecutionRequest({ version: 1, argv: ["/bin/bash", "-c", "echo bad"] }), /shell interpreter/);
});
