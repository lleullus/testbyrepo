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
import { sealVerificationVerdict } from "../src/verification-binding.js";
import { fixture } from "./helpers.js";

async function capture(f, name = "verify.json", executeArgv = executeArgvNode, bundleIdentity = "source") {
  return captureVerification({
    projectRoot: f.root,
    ticketPath: f.ticket,
    stableTargetPaths: [f.stable],
    scenarioEffectPaths: [f.effect],
    bindingPath: path.join(f.base, name),
    validatorPath: f.validatorPath,
    executeArgv,
    bundleIdentity,
  });
}

function terminal(binding, verdict, handle = `${verdict.toLowerCase()}-terminal`) {
  const captured = binding.binding;
  return {
    schema: "iis-ready-host-terminal/v1",
    handle,
    owner_id: "Verifier",
    project_root: captured.project_root,
    ticket_path: captured.ticket_path,
    verification_binding: binding.binding_path,
    verification_binding_sha256: binding.binding_sha256,
    stable_target_paths: captured.stable_target_paths,
    scenario_effect_paths: captured.scenario_effect_paths,
    verification_verdict: verdict,
    ticket_progression: captured.ticket_status_at_capture === "ready" ? "PENDING CALLER FINALIZATION" : "NOT APPLICABLE",
    observed_ticket_status: captured.ticket_status_at_capture,
    report: `READY TICKET VERIFICATION RESULT\nVerification Verdict: ${verdict}`,
  };
}

function input(f, binding, verdict, name, options = {}) {
  return {
    acceptedTerminal: terminal(binding, verdict, options.handle),
    verdictRecordPath: options.verdictRecordPath ?? path.join(f.base, `${name}-verdict.json`),
    executeArgv: options.executeArgv ?? executeArgvNode,
    bundleIdentity: options.bundleIdentity ?? binding.binding.bundle_identity,
    ...(options.boundaryProtocol ? { boundaryProtocol: options.boundaryProtocol } : {}),
    ...(options.recordResult ? { recordResult: options.recordResult } : {}),
    ...(options.hooks ? { hooks: options.hooks } : {}),
  };
}

test("public caller-shaped verdict arguments cannot reach finalization", async t => {
  const f = await fixture(t);
  const before = fs.readFileSync(f.ticket);
  const binding = await capture(f, "failed-binding.json");
  await assert.rejects(finalizeVerification({
    verdictPath: binding.binding_path,
    verdictSha256: binding.binding_sha256,
    verdict: "VERIFIED",
    executeArgv: executeArgvNode,
    bundleIdentity: "source",
  }), /only a host verifier terminal/);
  assert.deepEqual(fs.readFileSync(f.ticket), before);
});

test("a host-accepted INCONCLUSIVE verdict cannot progress", async t => {
  const f = await fixture(t);
  const before = fs.readFileSync(f.ticket);
  const binding = await capture(f, "inconclusive-binding.json");
  const result = await finalizeVerification(input(f, binding, "INCONCLUSIVE", "inconclusive"));
  assert.equal(result.verification_verdict, "INCONCLUSIVE");
  assert.equal(result.ticket_progression, "NOT APPLICABLE");
  assert.equal(result.ticket_status_after, "ready");
  assert.equal(result.verification_owner, "Verifier");
  assert.deepEqual(fs.readFileSync(f.ticket), before);
});

test("a stale boundary bundle cannot finalize an accepted terminal", async t => {
  const f = await fixture(t);
  const before = fs.readFileSync(f.ticket);
  const binding = await capture(f, "bundle-a-binding.json", executeArgvNode, "bundle-A");
  const result = await finalizeVerification(input(f, binding, "VERIFIED", "bundle", { bundleIdentity: "bundle-B" }));
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
  const result = await finalizeVerification(input(f, binding, "VERIFIED", "protocol", {
    boundaryProtocol: "iis-ready-boundary/v2",
  }));
  assert.equal(result.ticket_progression, "FAILED");
  assert.equal(result.progression_basis, "NONE");
  assert.equal(result.ticket_status_after, "ready");
  assert.deepEqual(fs.readFileSync(f.ticket), before);
});

test("an exact existing host verdict record resumes finalization without caller input", async t => {
  const f = await fixture(t);
  const binding = await capture(f, "resume-binding.json");
  const verdictRecordPath = path.join(f.base, "resume-verdict.json");
  sealVerificationVerdict({
    bindingPath: binding.binding_path,
    bindingSha256: binding.binding_sha256,
    verdict: "VERIFIED",
    verdictPath: verdictRecordPath,
  });
  const result = await finalizeVerification(input(f, binding, "VERIFIED", "resume-terminal", { verdictRecordPath }));
  assert.equal(result.ticket_progression, "COMPLETED");
  assert.equal(result.verification_verdict_record, verdictRecordPath);
  assert.match(fs.readFileSync(f.ticket, "utf8"), /^Status: done$/m);
});

test("VERIFIED performs the exact ready-to-done write", async t => {
  const f = await fixture(t);
  fs.chmodSync(f.ticket, 0o640);
  const binding = await capture(f);
  const accepted = terminal(binding, "VERIFIED", "verified-terminal");
  const firstInput = {
    acceptedTerminal: accepted,
    verdictRecordPath: path.join(f.base, "verified-verdict.json"),
    executeArgv: executeArgvNode,
    bundleIdentity: binding.binding.bundle_identity,
  };
  const result = await finalizeVerification(firstInput);
  assert.equal(result.ticket_progression, "COMPLETED");
  assert.equal(result.progression_basis, "WRITE_PERFORMED_THIS_CALL");
  assert.equal(result.ticket_status_after, "done");
  assert.equal(result.verification_terminal, "verified-terminal");
  assert.equal(ticketStatus(fs.readFileSync(f.ticket)), "done");
  assert.equal(fs.statSync(f.ticket).mode & 0o777, 0o640);

});

test("a host-ledger write failure rolls the Ticket back before finalization returns", async t => {
  const f = await fixture(t);
  const binding = await capture(f, "ledger-failure-binding.json");
  const before = fs.readFileSync(f.ticket);
  await assert.rejects(finalizeVerification(input(f, binding, "VERIFIED", "ledger-failure", {
    recordResult: () => { throw new Error("host ledger unavailable"); },
  })), /host ledger unavailable/);
  assert.deepEqual(fs.readFileSync(f.ticket), before);
});

test("FAILED and INCONCLUSIVE never mutate a ready Ticket", async t => {
  const f = await fixture(t);
  const before = fs.readFileSync(f.ticket);
  const failedBinding = await capture(f, "failed.json");
  const failed = await finalizeVerification(input(f, failedBinding, "FAILED", "failed"));
  assert.equal(failed.ticket_progression, "NOT APPLICABLE");
  assert.equal(failed.ticket_status_after, "ready");
  assert.deepEqual(fs.readFileSync(f.ticket), before);

  const inconclusiveBinding = await capture(f, "inconclusive.json");
  const inconclusive = await finalizeVerification(input(f, inconclusiveBinding, "INCONCLUSIVE", "inconclusive-two"));
  assert.equal(inconclusive.ticket_progression, "NOT APPLICABLE");
  assert.deepEqual(fs.readFileSync(f.ticket), before);
});

test("stable target or authority drift makes VERIFIED progression fail without done", async t => {
  const f = await fixture(t);
  const stableBinding = await capture(f, "stable-drift.json");
  fs.writeFileSync(f.stable, "console.log('changed during verification');\n");
  const stable = await finalizeVerification(input(f, stableBinding, "VERIFIED", "stable-drift"));
  assert.equal(stable.ticket_progression, "FAILED");
  assert.equal(stable.ticket_status_after, "ready");

  fs.writeFileSync(f.stable, "console.log('expected product output');\n");
  const authorityBinding = await capture(f, "authority-drift.json");
  fs.appendFileSync(f.behavior, "\nchanged authority\n");
  const authority = await finalizeVerification(input(f, authorityBinding, "VERIFIED", "authority-drift"));
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
  const result = await finalizeVerification(input(f, binding, "VERIFIED", "rollback", {
    executeArgv,
    hooks: { afterRename: async () => { failValidator = true; } },
  }));
  assert.equal(result.ticket_progression, "FAILED");
  assert.equal(result.ticket_status_after, "ready");
  assert.equal(result.rollback, "restored exact ready bytes");
  assert.deepEqual(fs.readFileSync(f.ticket), before);
});

test("a binding captured from an already-done Ticket is diagnostic only", async t => {
  const f = await fixture(t);
  const first = await capture(f, "first.json");
  await finalizeVerification(input(f, first, "VERIFIED", "first"));
  const diagnostic = await capture(f, "diagnostic.json");
  assert.equal(diagnostic.binding.ticket_status_at_capture, "done");
  const result = await finalizeVerification(input(f, diagnostic, "VERIFIED", "diagnostic"));
  assert.equal(result.ticket_progression, "NOT APPLICABLE");
  assert.equal(result.ticket_status_after, "done");
});
