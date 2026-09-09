import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import {
  captureVerification,
  executeArgvNode,
  finalizeVerification,
  sealVerificationVerdict,
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

async function seal(f, binding, verdict, name = `${verdict.toLowerCase()}-verdict.json`) {
  return sealVerificationVerdict({
    bindingPath: binding.binding_path,
    bindingSha256: binding.binding_sha256,
    verdict,
    verdictPath: path.join(f.base, name),
  });
}

test("a caller cannot upgrade a verifier-owned FAILED verdict", async t => {
  const f = await fixture(t);
  const before = fs.readFileSync(f.ticket);
  const binding = await capture(f, "failed-binding.json");
  const verdict = await seal(f, binding, "FAILED");
  await assert.rejects(finalizeVerification({
    verdictPath: verdict.verdict_path,
    verdictSha256: verdict.verdict_sha256,
    verdict: "VERIFIED",
    executeArgv: executeArgvNode,
  }), /only verdict record identity/);
  assert.deepEqual(fs.readFileSync(f.ticket), before);
});

test("a verifier-owned INCONCLUSIVE verdict cannot progress", async t => {
  const f = await fixture(t);
  const before = fs.readFileSync(f.ticket);
  const binding = await capture(f, "inconclusive-binding.json");
  const verdict = await seal(f, binding, "INCONCLUSIVE");
  const result = await finalizeVerification({
    verdictPath: verdict.verdict_path,
    verdictSha256: verdict.verdict_sha256,
    executeArgv: executeArgvNode,
  });
  assert.equal(result.verification_verdict, "INCONCLUSIVE");
  assert.equal(result.ticket_progression, "NOT APPLICABLE");
  assert.equal(result.ticket_status_after, "ready");
  assert.deepEqual(fs.readFileSync(f.ticket), before);
});

test("a verdict record cannot be rebound to a different verification binding", async t => {
  const f = await fixture(t);
  const bindingA = await capture(f, "binding-a.json");
  const bindingB = await capture(f, "binding-b.json");
  const verdictA = await seal(f, bindingA, "VERIFIED", "verdict-a.json");
  await assert.rejects(finalizeVerification({
    bindingPath: bindingB.binding_path,
    bindingSha256: bindingB.binding_sha256,
    verdictPath: verdictA.verdict_path,
    verdictSha256: verdictA.verdict_sha256,
    executeArgv: executeArgvNode,
  }), /only verdict record identity/);
  assert.equal(ticketStatus(fs.readFileSync(f.ticket)), "ready");
});

test("a tampered verdict record SHA is rejected without Ticket mutation", async t => {
  const f = await fixture(t);
  const before = fs.readFileSync(f.ticket);
  const binding = await capture(f, "tamper-binding.json");
  const verdict = await seal(f, binding, "VERIFIED", "tamper-verdict.json");
  fs.appendFileSync(verdict.verdict_path, " ");
  await assert.rejects(finalizeVerification({
    verdictPath: verdict.verdict_path,
    verdictSha256: verdict.verdict_sha256,
    executeArgv: executeArgvNode,
  }), /verdict record SHA256 mismatch/);
  assert.deepEqual(fs.readFileSync(f.ticket), before);
});

test("a stale boundary bundle cannot finalize its verdict record", async t => {
  const f = await fixture(t);
  const before = fs.readFileSync(f.ticket);
  const binding = await captureVerification({
    projectRoot: f.root,
    ticketPath: f.ticket,
    stableTargetPaths: [f.stable],
    scenarioEffectPaths: [f.effect],
    bindingPath: path.join(f.base, "bundle-a-binding.json"),
    validatorPath: f.validatorPath,
    executeArgv: executeArgvNode,
    bundleIdentity: "bundle-A",
  });
  const verdict = await seal(f, binding, "VERIFIED", "bundle-a-verdict.json");
  const result = await finalizeVerification({
    verdictPath: verdict.verdict_path,
    verdictSha256: verdict.verdict_sha256,
    executeArgv: executeArgvNode,
    bundleIdentity: "bundle-B",
  });
  assert.equal(result.ticket_progression, "FAILED");
  assert.equal(result.progression_basis, "NONE");
  assert.equal(result.ticket_status_after, "ready");
  assert.match(result.progression_detail, /different boundary bundle\/protocol/);
  assert.deepEqual(fs.readFileSync(f.ticket), before);
});

test("a boundary protocol mismatch fails before Ticket mutation", async t => {
  const f = await fixture(t);
  const before = fs.readFileSync(f.ticket);
  const binding = await capture(f, "protocol-binding.json");
  const verdict = await seal(f, binding, "VERIFIED", "protocol-verdict.json");
  const result = await finalizeVerification({
    verdictPath: verdict.verdict_path,
    verdictSha256: verdict.verdict_sha256,
    executeArgv: executeArgvNode,
    bundleIdentity: "source",
    boundaryProtocol: "iis-ready-boundary/v2",
  });
  assert.equal(result.ticket_progression, "FAILED");
  assert.equal(result.progression_basis, "NONE");
  assert.equal(result.ticket_status_after, "ready");
  assert.match(result.progression_detail, /different boundary bundle\/protocol/);
  assert.deepEqual(fs.readFileSync(f.ticket), before);
});

test("VERIFIED performs the exact ready-to-done write and a bare retry is not a new completion", async t => {
  const f = await fixture(t);
  fs.chmodSync(f.ticket, 0o640);
  const binding = await capture(f);
  const verdict = await seal(f, binding, "VERIFIED", "verified-verdict.json");
  const finalizerInput = { verdictPath: verdict.verdict_path, verdictSha256: verdict.verdict_sha256, executeArgv: executeArgvNode };
  const result = await finalizeVerification(finalizerInput);
  assert.equal(result.ticket_progression, "COMPLETED");
  assert.equal(result.progression_basis, "WRITE_PERFORMED_THIS_CALL");
  assert.equal(result.ticket_status_after, "done");
  assert.equal(result.verification_verdict_record, verdict.verdict_path);
  assert.equal(result.verification_verdict_record_sha256, verdict.verdict_sha256);
  assert.equal(ticketStatus(fs.readFileSync(f.ticket)), "done");
  assert.equal(fs.statSync(f.ticket).mode & 0o777, 0o640);

  const retry = await finalizeVerification(finalizerInput);
  assert.equal(retry.ticket_progression, "NOT APPLICABLE");
  assert.equal(retry.progression_basis, "ALREADY_DONE_MATCHING_BINDING");

  const provenance = new Map([[`${verdict.verdict_path}:${verdict.verdict_sha256}`, result]]);
  const recovered = await finalizeVerification({ ...finalizerInput, provenance });
  assert.equal(recovered.ticket_progression, "COMPLETED");
  assert.equal(recovered.progression_basis, "RECOVERED_CAPTURED_FINALIZER_RESULT");
});

test("FAILED and INCONCLUSIVE never mutate a ready Ticket", async t => {
  const f = await fixture(t);
  const before = fs.readFileSync(f.ticket);
  const failedBinding = await capture(f, "failed.json");
  const failedVerdict = await seal(f, failedBinding, "FAILED", "failed-result.json");
  const failed = await finalizeVerification({ verdictPath: failedVerdict.verdict_path, verdictSha256: failedVerdict.verdict_sha256, executeArgv: executeArgvNode });
  assert.equal(failed.ticket_progression, "NOT APPLICABLE");
  assert.equal(failed.ticket_status_after, "ready");
  assert.deepEqual(fs.readFileSync(f.ticket), before);

  const inconclusiveBinding = await capture(f, "inconclusive.json");
  const inconclusiveVerdict = await seal(f, inconclusiveBinding, "INCONCLUSIVE", "inconclusive-result.json");
  const inconclusive = await finalizeVerification({ verdictPath: inconclusiveVerdict.verdict_path, verdictSha256: inconclusiveVerdict.verdict_sha256, executeArgv: executeArgvNode });
  assert.equal(inconclusive.ticket_progression, "NOT APPLICABLE");
  assert.deepEqual(fs.readFileSync(f.ticket), before);
});

test("stable target or authority drift makes VERIFIED progression fail without done", async t => {
  const f = await fixture(t);
  const stableBinding = await capture(f, "stable-drift.json");
  const stableVerdict = await seal(f, stableBinding, "VERIFIED", "stable-drift-verdict.json");
  fs.writeFileSync(f.stable, "console.log('changed during verification');\n");
  const stable = await finalizeVerification({ verdictPath: stableVerdict.verdict_path, verdictSha256: stableVerdict.verdict_sha256, executeArgv: executeArgvNode });
  assert.equal(stable.ticket_progression, "FAILED");
  assert.equal(stable.ticket_status_after, "ready");

  fs.writeFileSync(f.stable, "console.log('expected product output');\n");
  const authorityBinding = await capture(f, "authority-drift.json");
  const authorityVerdict = await seal(f, authorityBinding, "VERIFIED", "authority-drift-verdict.json");
  fs.appendFileSync(f.behavior, "\nchanged authority\n");
  const authority = await finalizeVerification({ verdictPath: authorityVerdict.verdict_path, verdictSha256: authorityVerdict.verdict_sha256, executeArgv: executeArgvNode });
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
  const verdict = await seal(f, binding, "VERIFIED", "rollback-verdict.json");
  const before = fs.readFileSync(f.ticket);
  const result = await finalizeVerification({
    verdictPath: verdict.verdict_path,
    verdictSha256: verdict.verdict_sha256,
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
  const firstVerdict = await seal(f, first, "VERIFIED", "first-verdict.json");
  await finalizeVerification({ verdictPath: firstVerdict.verdict_path, verdictSha256: firstVerdict.verdict_sha256, executeArgv: executeArgvNode });
  const diagnostic = await capture(f, "diagnostic.json");
  assert.equal(diagnostic.binding.ticket_status_at_capture, "done");
  const diagnosticVerdict = await seal(f, diagnostic, "VERIFIED", "diagnostic-verdict.json");
  const result = await finalizeVerification({ verdictPath: diagnosticVerdict.verdict_path, verdictSha256: diagnosticVerdict.verdict_sha256, executeArgv: executeArgvNode });
  assert.equal(result.ticket_progression, "NOT APPLICABLE");
  assert.equal(result.ticket_status_after, "done");
});
