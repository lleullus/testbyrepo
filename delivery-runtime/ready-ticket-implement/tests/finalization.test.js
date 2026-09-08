import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fixture, executeArgv } from "./helpers.js";
import { finalizeVerification } from "../src/core.js";
import { hashBytes } from "../src/plan-binding.js";
import { readyCandidate } from "../src/finalization.js";

async function verifier(f) {
  return f.lifecycle.beginDirect({ sessionId: "verifier", projectRoot: f.root, ticketPath: f.ticket, purpose: "verify" });
}

test("DIRECT status-only progression needs no parent checkpoint and preserves other bytes and mode", async t => {
  const f = await fixture(t);
  const before = fs.readFileSync(f.ticket); const mode = fs.statSync(f.ticket).mode;
  const state = await verifier(f);
  const result = await finalizeVerification(f.lifecycle, state.execution_id, "verifier", "VERIFIED");
  assert.equal(result.ticket_progression, "COMPLETED", JSON.stringify(result));
  assert.deepEqual(fs.readFileSync(f.ticket), readyCandidate(before));
  assert.equal(fs.statSync(f.ticket).mode, mode);
  assert.equal(f.store.readActiveTicket(f.root, f.ticket), null);
});

test("post-validator failure restores only its exact candidate and leaves recovery intent", async t => {
  const f = await fixture(t);
  const before = fs.readFileSync(f.ticket), state = await verifier(f);
  f.lifecycle.executeArgv = async (argv, options) => argv[0] === "python3" && fs.readFileSync(f.ticket, "utf8").includes("Status: done") ? { exitCode: 1, interrupted: false, terminationState: "settled", stdout: "INVALID", stderr: "injected postcheck" } : executeArgv(argv, options);
  const result = await finalizeVerification(f.lifecycle, state.execution_id, "verifier", "VERIFIED");
  assert.equal(result.verification_verdict, "VERIFIED"); assert.equal(result.ticket_progression, "FAILED"); assert.equal(result.ticket_status_after, "ready");
  assert.deepEqual(fs.readFileSync(f.ticket), before);
  assert.ok(f.store.readActiveTicket(f.root, f.ticket));
  assert.equal(f.lifecycle.status(state.execution_id).pause.kind, "RECOVERY_REQUIRED");
  f.lifecycle.executeArgv = executeArgv;
  const recovered = await finalizeVerification(f.lifecycle, state.execution_id, "verifier", "VERIFIED");
  assert.equal(recovered.ticket_progression, "COMPLETED", JSON.stringify(recovered));
});

test("external post-write edit is never overwritten by rollback", async t => {
  const f = await fixture(t), state = await verifier(f);
  let changed = false;
  f.lifecycle.executeArgv = async (argv, options) => {
    if (argv[0] === "python3" && fs.readFileSync(f.ticket, "utf8").includes("Status: done")) {
      changed = true; fs.appendFileSync(f.ticket, "\nExternal writer content\n");
      return { exitCode: 1, interrupted: false, terminationState: "settled", stdout: "INVALID", stderr: "external write" };
    }
    return executeArgv(argv, options);
  };
  const result = await finalizeVerification(f.lifecycle, state.execution_id, "verifier", "VERIFIED");
  assert.equal(changed, true); assert.equal(result.ticket_progression, "FAILED");
  assert.match(fs.readFileSync(f.ticket, "utf8"), /External writer content/);
  assert.ok(f.store.readActiveTicket(f.root, f.ticket));
});

test("persisted candidate crash intent requires canonical postcheck before durable completion", async t => {
  const f = await fixture(t), state = await verifier(f);
  const before = fs.readFileSync(f.ticket), candidate = readyCandidate(before);
  const operation = f.lifecycle.beginOperation(state.execution_id, "verifier", { kind: "finalization", effect_surface: f.ticket, before_sha256: hashBytes(before), candidate_sha256: hashBytes(candidate), before_bytes: before.toString("base64"), candidate_bytes: candidate.toString("base64"), mode: fs.statSync(f.ticket).mode & 0o777 });
  fs.writeFileSync(f.ticket, candidate);
  f.lifecycle.recoverInterruptedOperation("verifier");
  assert.equal(f.lifecycle.status(state.execution_id).active_operation.operation_id, operation.operation_id);
  const result = await finalizeVerification(f.lifecycle, state.execution_id, "verifier", "VERIFIED");
  assert.equal(result.ticket_progression, "COMPLETED", JSON.stringify(result));
});

test("source drift never mutates the Ticket during finalization", async t => {
  const f = await fixture(t);
  const before = fs.readFileSync(f.ticket);
  const state = await f.lifecycle.beginDirect({ sessionId: "verifier", projectRoot: f.root, ticketPath: f.ticket, purpose: "verify" });
  fs.appendFileSync(path.join(f.root, "cli.js"), "console.log('changed');\n");
  const result = await finalizeVerification(f.lifecycle, state.execution_id, "verifier", "VERIFIED");
  assert.equal(result.ticket_progression, "FAILED"); assert.deepEqual(fs.readFileSync(f.ticket), before);
});

test("delegated VERIFIED requires parent progression release after runtime release", async t => {
  const f = await fixture(t);
  const before = fs.readFileSync(f.ticket);
  const assignment = await f.lifecycle.assignSubagent({ parentSessionId: "parent", projectRoot: f.root, ticketPath: f.ticket, purpose: "verify" });
  const state = await f.lifecycle.beginDelegated({ childSessionId: "child", assignmentId: assignment.assignment_id });
  await f.lifecycle.releaseCheckpoint(state.execution_id, "parent", "CONTINUE");
  const rejected = await finalizeVerification(f.lifecycle, state.execution_id, "child", "VERIFIED");
  assert.equal(rejected.ticket_progression, "FAILED");
  assert.match(rejected.progression_detail, /PRE_PROGRESSION/);
  assert.deepEqual(fs.readFileSync(f.ticket), before);
  await f.lifecycle.releaseCheckpoint(state.execution_id, "parent", "CONTINUE");
  f.lifecycle.checkpoint(state.execution_id, "child", "PRE_PROGRESSION", "all authored evidence and cleanup closed");
  await f.lifecycle.releaseCheckpoint(state.execution_id, "parent", "CONTINUE");
  const completed = await finalizeVerification(f.lifecycle, state.execution_id, "child", "VERIFIED");
  assert.equal(completed.ticket_progression, "COMPLETED", JSON.stringify(completed));
});
