import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import {
  captureVerification,
  executeArgvNode,
  finalizeVerification,
  ticketStatus,
} from "../src/core.js";
import { fixture } from "./helpers.js";

async function capture(f, name = "verify.json", executeArgv = executeArgvNode) {
  return captureVerification({
    projectRoot: f.root,
    ticketPath: f.ticket,
    stableTargetPaths: [f.stable],
    scenarioEffectPaths: [f.effect],
    bindingPath: path.join(f.base, name),
    validatorPath: f.validatorPath,
    executeArgv,
  });
}

test("VERIFIED performs the exact ready-to-done write and a bare retry is not a new completion", async t => {
  const f = await fixture(t);
  fs.chmodSync(f.ticket, 0o640);
  const binding = await capture(f);
  const result = await finalizeVerification({ bindingPath: binding.binding_path, bindingSha256: binding.binding_sha256, verdict: "VERIFIED", executeArgv: executeArgvNode });
  assert.equal(result.ticket_progression, "COMPLETED");
  assert.equal(result.progression_basis, "WRITE_PERFORMED_THIS_CALL");
  assert.equal(result.ticket_status_after, "done");
  assert.equal(ticketStatus(fs.readFileSync(f.ticket)), "done");
  assert.equal(fs.statSync(f.ticket).mode & 0o777, 0o640);

  const retry = await finalizeVerification({ bindingPath: binding.binding_path, bindingSha256: binding.binding_sha256, verdict: "VERIFIED", executeArgv: executeArgvNode });
  assert.equal(retry.ticket_progression, "NOT APPLICABLE");
  assert.equal(retry.progression_basis, "ALREADY_DONE_MATCHING_BINDING");

  const provenance = new Map([[`${binding.binding_path}:${binding.binding_sha256}`, result]]);
  const recovered = await finalizeVerification({ bindingPath: binding.binding_path, bindingSha256: binding.binding_sha256, verdict: "VERIFIED", executeArgv: executeArgvNode, provenance });
  assert.equal(recovered.ticket_progression, "COMPLETED");
  assert.equal(recovered.progression_basis, "RECOVERED_CAPTURED_FINALIZER_RESULT");
});

test("FAILED and INCONCLUSIVE never mutate a ready Ticket", async t => {
  const f = await fixture(t);
  const before = fs.readFileSync(f.ticket);
  const failedBinding = await capture(f, "failed.json");
  const failed = await finalizeVerification({ bindingPath: failedBinding.binding_path, bindingSha256: failedBinding.binding_sha256, verdict: "FAILED", executeArgv: executeArgvNode });
  assert.equal(failed.ticket_progression, "NOT APPLICABLE");
  assert.equal(failed.ticket_status_after, "ready");
  assert.deepEqual(fs.readFileSync(f.ticket), before);

  const inconclusiveBinding = await capture(f, "inconclusive.json");
  const inconclusive = await finalizeVerification({ bindingPath: inconclusiveBinding.binding_path, bindingSha256: inconclusiveBinding.binding_sha256, verdict: "INCONCLUSIVE", executeArgv: executeArgvNode });
  assert.equal(inconclusive.ticket_progression, "NOT APPLICABLE");
  assert.deepEqual(fs.readFileSync(f.ticket), before);
});

test("stable target or authority drift makes VERIFIED progression fail without done", async t => {
  const f = await fixture(t);
  const stableBinding = await capture(f, "stable-drift.json");
  fs.writeFileSync(f.stable, "console.log('changed during verification');\n");
  const stable = await finalizeVerification({ bindingPath: stableBinding.binding_path, bindingSha256: stableBinding.binding_sha256, verdict: "VERIFIED", executeArgv: executeArgvNode });
  assert.equal(stable.ticket_progression, "FAILED");
  assert.equal(stable.ticket_status_after, "ready");

  fs.writeFileSync(f.stable, "console.log('expected product output');\n");
  const authorityBinding = await capture(f, "authority-drift.json");
  fs.appendFileSync(f.behavior, "\nchanged authority\n");
  const authority = await finalizeVerification({ bindingPath: authorityBinding.binding_path, bindingSha256: authorityBinding.binding_sha256, verdict: "VERIFIED", executeArgv: executeArgvNode });
  assert.equal(authority.ticket_progression, "FAILED");
  assert.equal(authority.ticket_status_after, "ready");
});

test("post-write validation failure conditionally restores only this call's exact ready bytes", async t => {
  const f = await fixture(t);
  let failValidator = false;
  const executeArgv = async (argv, options) => {
    if (failValidator && argv[0] === "python3" && argv.includes(f.validatorPath)) {
      return { exitCode: 1, interrupted: false, terminationState: "settled", stdout: "INVALID", stderr: "fixture post-write rejection" };
    }
    return executeArgvNode(argv, options);
  };
  const binding = await capture(f, "rollback.json", executeArgv);
  const before = fs.readFileSync(f.ticket);
  const result = await finalizeVerification({
    bindingPath: binding.binding_path,
    bindingSha256: binding.binding_sha256,
    verdict: "VERIFIED",
    executeArgv,
    hooks: { afterRename: async () => { failValidator = true; } },
  });
  assert.equal(result.ticket_progression, "FAILED");
  assert.equal(result.ticket_status_after, "ready");
  assert.equal(result.rollback, "restored exact ready bytes");
  assert.deepEqual(fs.readFileSync(f.ticket), before);
});

test("a binding captured from an already-done Ticket is diagnostic only", async t => {
  const f = await fixture(t);
  const first = await capture(f, "first.json");
  await finalizeVerification({ bindingPath: first.binding_path, bindingSha256: first.binding_sha256, verdict: "VERIFIED", executeArgv: executeArgvNode });
  const diagnostic = await capture(f, "diagnostic.json");
  assert.equal(diagnostic.binding.ticket_status_at_capture, "done");
  const result = await finalizeVerification({ bindingPath: diagnostic.binding_path, bindingSha256: diagnostic.binding_sha256, verdict: "VERIFIED", executeArgv: executeArgvNode });
  assert.equal(result.ticket_progression, "NOT APPLICABLE");
  assert.equal(result.ticket_status_after, "done");
});
