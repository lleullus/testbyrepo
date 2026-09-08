import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fixture, executeArgv } from "./helpers.js";
import { bindAuthority, checkAuthorityCurrentness, captureVerificationTarget, checkVerificationTarget } from "../src/core.js";

test("authority is product plus pinned validator/protocol, independent of normal source changes", async t => {
  const f = await fixture(t);
  fs.appendFileSync(path.join(f.root, "cli.js"), "// local implementation change\n");
  assert.equal((await checkAuthorityCurrentness(f.authority)).current, true);
  const current = await bindAuthority({ projectRoot: f.root, ticketPath: f.ticket, validatorPath: f.validatorPath, executeArgv });
  assert.equal(current.authority_digest, f.authority.authority_digest);
  fs.appendFileSync(f.authority.behavior_authorities[0].path, "changed product authority\n");
  assert.equal((await checkAuthorityCurrentness(f.authority)).current, false);
});

test("method-only context drift is separate; undeclared file and required plan product cause product drift", async t => {
  const f = await fixture(t);
  const target = await captureVerificationTarget({ projectRoot: f.root, methodPaths: [f.plan, f.review], executeArgv });
  fs.appendFileSync(f.plan, "navigation refinement\n");
  const navigation = await checkVerificationTarget(target, { executeArgv });
  assert.equal(navigation.current, true); assert.equal(navigation.method_current, false);
  fs.writeFileSync(path.join(f.root, "UNDECLARED-PLAN.md"), "not declared context\n");
  assert.equal((await checkVerificationTarget(target, { executeArgv })).current, false);
  const required = await captureVerificationTarget({ projectRoot: f.root, methodPaths: [f.plan], productPaths: [f.plan], executeArgv });
  fs.appendFileSync(f.plan, "product deliverable change\n");
  assert.equal((await checkVerificationTarget(required, { executeArgv })).current, false);
  await assert.rejects(captureVerificationTarget({ projectRoot: f.root, allowedOutputPaths: [f.root], executeArgv }), /outside-root/);
});

test("verification-only needs no implementation plan, while delegated actual runtime waits PRE_RUNTIME", async t => {
  const f = await fixture(t);
  const assignment = await f.lifecycle.assignSubagent({ parentSessionId: "parent", projectRoot: f.root, ticketPath: f.ticket, purpose: "verify" });
  const state = await f.lifecycle.beginDelegated({ childSessionId: "verifier", assignmentId: assignment.assignment_id });
  assert.throws(() => f.lifecycle.beginOperation(state.execution_id, "verifier", { kind: "opaque_program" }), /ACTIVE/);
  f.lifecycle.checkpoint(state.execution_id, "verifier", "PRE_RUNTIME", "bounded ordinary scenario");
  await assert.rejects(f.lifecycle.releaseCheckpoint(state.execution_id, "verifier", "CONTINUE"), /OWNER_MISMATCH/);
  await f.lifecycle.releaseCheckpoint(state.execution_id, "parent", "CONTINUE");
  assert.equal(f.lifecycle.assertDispatch(state.execution_id, "verifier", true).phase, "ACTIVE");
});
