import assert from "node:assert/strict";
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import test from "node:test";
import { executeArgvNode } from "../src/core.js";
import { installReadyBoundaryTools } from "../omp.js";
import { fixture } from "./helpers.js";

function zodStub() {
  const node = () => ({ optional() { return this; } });
  return {
    string: node,
    enum: node,
    array: node,
    object: node,
  };
}

function fakePi() {
  const tools = [];
  return {
    tools,
    zod: zodStub(),
    registerTool(tool) { tools.push(tool); },
    on() { throw new Error("boundary tools must not register global/session hooks"); },
  };
}

test("OMP extension registers exactly ready_contract and ready_finalize with zero interception hooks", () => {
  const pi = fakePi();
  installReadyBoundaryTools(pi, { executeArgv: executeArgvNode, bundleIdentity: "source" });
  assert.deepEqual(pi.tools.map(tool => tool.name), ["ready_contract", "ready_finalize"]);
});

test("registered tool surface performs admission, capture, verifier sealing, and caller finalization", async t => {
  const f = await fixture(t);
  const pi = fakePi();
  installReadyBoundaryTools(pi, { executeArgv: executeArgvNode, validatorPath: f.validatorPath, bundleIdentity: "source" });
  const contract = pi.tools.find(tool => tool.name === "ready_contract");
  const finalizer = pi.tools.find(tool => tool.name === "ready_finalize");
  const admission = await contract.execute("a", { action: "check_plan_admission", project_root: f.root, ticket_path: f.ticket, plan_review_path: f.review });
  assert.equal(admission.details.decision, "ADMIT");
  const bindingPath = path.join(f.base, "omp-binding.json");
  const captured = await contract.execute("b", { action: "capture_verification", project_root: f.root, ticket_path: f.ticket, plan_review_path: f.review, stable_target_paths: [f.stable], scenario_effect_paths: [f.effect], binding_path: bindingPath });
  const verdictPath = path.join(f.base, "omp-verdict.json");
  const sealed = await contract.execute("seal", { action: "seal_verdict", binding_path: captured.details.binding_path, binding_sha256: captured.details.binding_sha256, verdict: "VERIFIED", verdict_path: verdictPath });
  const finalized = await finalizer.execute("c", { verdict_path: sealed.details.verdict_path, verdict_sha256: sealed.details.verdict_sha256 });
  assert.equal(finalized.details.ticket_progression, "COMPLETED");
  assert.equal(finalized.details.progression_basis, "WRITE_PERFORMED_THIS_CALL");
  assert.equal(finalized.details.verification_verdict_record, sealed.details.verdict_path);
  const recovered = await finalizer.execute("d", { verdict_path: sealed.details.verdict_path, verdict_sha256: sealed.details.verdict_sha256 });
  assert.equal(recovered.details.progression_basis, "RECOVERED_CAPTURED_FINALIZER_RESULT");
});

test("ready_finalize public surface cannot upgrade a sealed FAILED verdict", async t => {
  const f = await fixture(t);
  const pi = fakePi();
  installReadyBoundaryTools(pi, { executeArgv: executeArgvNode, validatorPath: f.validatorPath, bundleIdentity: "source" });
  const contract = pi.tools.find(tool => tool.name === "ready_contract");
  const finalizer = pi.tools.find(tool => tool.name === "ready_finalize");
  const captured = await contract.execute("capture", {
    action: "capture_verification", project_root: f.root, ticket_path: f.ticket,
    stable_target_paths: [f.stable], binding_path: path.join(f.base, "failed-binding.json"),
  });
  const sealed = await contract.execute("seal", {
    action: "seal_verdict", binding_path: captured.details.binding_path,
    binding_sha256: captured.details.binding_sha256, verdict: "FAILED",
    verdict_path: path.join(f.base, "failed-verdict.json"),
  });
  const result = await finalizer.execute("finalize", {
    verdict_path: sealed.details.verdict_path,
    verdict_sha256: sealed.details.verdict_sha256,
    verdict: "VERIFIED",
  });
  assert.equal(result.details.verification_verdict, "FAILED");
  assert.equal(result.details.ticket_progression, "NOT APPLICABLE");
  assert.match(fs.readFileSync(f.ticket, "utf8"), /^Status: ready$/m);
});

test("settled exit 1 is an ordinary command result and does not prevent immediate edit/retry", async t => {
  const f = await fixture(t);
  const failed = await executeArgvNode([process.execPath, "-e", "process.exit(1)"], { cwd: f.root });
  assert.equal(failed.exitCode, 1);
  assert.equal(failed.interrupted, false);
  assert.equal(failed.terminationState, "settled");
  fs.writeFileSync(f.stable, "console.log('fixed after failure');\n");
  const retried = await executeArgvNode([process.execPath, f.stable], { cwd: f.root });
  assert.equal(retried.exitCode, 0);
  assert.equal(retried.stdout.trim(), "fixed after failure");
});

test("response loss after a real loopback effect does not lock authoritative readback or force replay", async t => {
  const f = await fixture(t);
  const state = { requests: 0, effect: false };
  const server = http.createServer((request, response) => {
    if (request.url === "/effect" && request.method === "POST") {
      state.requests += 1;
      state.effect = true;
      // Intentionally never acknowledge. The client timeout loses the response after the effect is applied.
      return;
    }
    if (request.url === "/readback") {
      response.setHeader("content-type", "application/json");
      response.end(JSON.stringify(state));
      return;
    }
    response.statusCode = 404;
    response.end();
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  t.after(() => server.close());
  const address = server.address();
  const endpoint = `http://127.0.0.1:${address.port}`;
  const sendScript = `
    const http = require('node:http');
    const request = http.request(${JSON.stringify(endpoint + "/effect")}, {method:'POST', headers:{'content-length':'2'}}, response => {
      response.resume(); response.on('end', () => process.exit(0));
    });
    request.on('error', error => { console.error(error.message); process.exit(2); });
    request.end('{}');
  `;
  const lost = await executeArgvNode([process.execPath, "-e", sendScript], { cwd: f.root, timeout: 500 });
  assert.equal(lost.interrupted, true);
  assert.equal(lost.terminationState, "unknown");
  assert.equal(state.requests, 1);
  assert.equal(state.effect, true);

  const readback = await executeArgvNode([
    process.execPath,
    "-e",
    `fetch(${JSON.stringify(endpoint + "/readback")}).then(r => r.text()).then(text => console.log(text))`,
  ], { cwd: f.root, timeout: 5000 });
  assert.equal(readback.exitCode, 0);
  assert.deepEqual(JSON.parse(readback.stdout), { requests: 1, effect: true });
  assert.equal(state.requests, 1, "authoritative readback must not replay the non-idempotent request");
  const evidence = path.join(f.base, "effect-evidence.json");
  fs.writeFileSync(evidence, readback.stdout);
  assert.deepEqual(JSON.parse(fs.readFileSync(evidence, "utf8")), { requests: 1, effect: true });
});

test("fresh host-contract smoke covers admission, fail/fix/retry, binding, verdict, caller finalization, and done", async t => {
  const f = await fixture(t);
  const pi = fakePi();
  installReadyBoundaryTools(pi, { executeArgv: executeArgvNode, validatorPath: f.validatorPath, bundleIdentity: "source" });
  const contract = pi.tools.find(tool => tool.name === "ready_contract");
  const finalizer = pi.tools.find(tool => tool.name === "ready_finalize");

  const startAdmission = await contract.execute("start", {
    action: "check_plan_admission", project_root: f.root, ticket_path: f.ticket, plan_review_path: f.review,
  });
  assert.equal(startAdmission.details.decision, "ADMIT");

  fs.writeFileSync(f.stable, "throw new Error('expected red test');\n");
  const failed = await executeArgvNode([process.execPath, f.stable], { cwd: f.root });
  assert.equal(failed.exitCode, 1);
  assert.equal(failed.terminationState, "settled");
  fs.writeFileSync(f.stable, "console.log('expected product output');\n");
  const fixed = await executeArgvNode([process.execPath, f.stable], { cwd: f.root });
  assert.equal(fixed.exitCode, 0);
  assert.equal(fixed.stdout.trim(), "expected product output");

  const endAdmission = await contract.execute("end", {
    action: "check_plan_admission", project_root: f.root, ticket_path: f.ticket, plan_review_path: f.review,
  });
  assert.equal(endAdmission.details.decision, "ADMIT");
  const bindingPath = path.join(f.base, "fresh-host-binding.json");
  const captured = await contract.execute("capture", {
    action: "capture_verification", project_root: f.root, ticket_path: f.ticket,
    plan_review_path: f.review, stable_target_paths: [f.stable], scenario_effect_paths: [f.effect],
    binding_path: bindingPath,
  });
  const verifierReadback = await executeArgvNode([process.execPath, f.stable], { cwd: f.root });
  assert.equal(verifierReadback.stdout.trim(), "expected product output");
  const semanticVerdict = "VERIFIED";
  const sealed = await contract.execute("seal", {
    action: "seal_verdict", binding_path: captured.details.binding_path,
    binding_sha256: captured.details.binding_sha256, verdict: semanticVerdict,
    verdict_path: path.join(f.base, "fresh-host-verdict.json"),
  });
  const finalized = await finalizer.execute("finalize", {
    verdict_path: sealed.details.verdict_path,
    verdict_sha256: sealed.details.verdict_sha256,
  });
  assert.equal(finalized.details.verification_verdict, semanticVerdict);
  assert.equal(finalized.details.verification_verdict_record, sealed.details.verdict_path);
  assert.equal(finalized.details.verification_verdict_record_sha256, sealed.details.verdict_sha256);
  assert.equal(finalized.details.ticket_progression, "COMPLETED");
  assert.equal(finalized.details.progression_basis, "WRITE_PERFORMED_THIS_CALL");
  assert.equal(finalized.details.ticket_status_after, "done");
  assert.match(fs.readFileSync(f.ticket, "utf8"), /^Status: done$/m);
});
