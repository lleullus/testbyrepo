import assert from "node:assert/strict";
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import test from "node:test";
import { bindAuthority, executeArgvNode } from "../src/core.js";
import { fixture, materializeReadyBundle } from "./helpers.js";

function zodStub() {
  const node = () => ({ optional() { return this; } });
  return { string: node, enum: node, array: node, object: node };
}

function fakePi(terminals = new Map()) {
  const tools = [];
  const released = [];
  const pi = {
    tools,
    released,
    zod: zodStub(),
    pi: {
      resolveReadyVerifierFinalization(handle, parentId, sessionId) {
        const terminal = terminals.get(handle);
        if (!terminal || terminal.parent_id !== parentId || terminal.parent_session_id !== sessionId) return undefined;
        return terminal.finalization_result;
      },
      readyVerifierVerdictRecordPath(handle, parentId, sessionId) {
        const terminal = terminals.get(handle);
        if (!terminal || terminal.parent_id !== parentId || terminal.parent_session_id !== sessionId) throw new Error("unknown or foreign verifier terminal");
        return path.join(path.dirname(terminal.verification_binding), `${handle}-host-verdict.json`);
      },
      resolveReadyVerifierTerminal(handle, parentId, sessionId) {
        const terminal = terminals.get(handle);
        if (!terminal || terminal.parent_id !== parentId || terminal.parent_session_id !== sessionId) {
          throw new Error("unknown or foreign verifier terminal");
        }
        return terminal;
      },
      recordReadyVerifierFinalization(handle, parentId, sessionId, result) {
        const terminal = terminals.get(handle);
        if (!terminal || terminal.parent_id !== parentId || terminal.parent_session_id !== sessionId) {
          throw new Error("unknown or foreign verifier terminal");
        }
        if (terminal.finalization_result) {
          assert.deepEqual(terminal.finalization_result, result);
          return terminal.finalization_result;
        }
        terminal.finalization_result = structuredClone(result);
        return terminal.finalization_result;
      },
      releaseReadyVerifierTerminal(handle, parentId, sessionId) {
        const terminal = terminals.get(handle);
        if (!terminal || terminal.parent_id !== parentId || terminal.parent_session_id !== sessionId) throw new Error("unknown or foreign verifier terminal");
        terminals.delete(handle);
      },
      releaseReadyVerifierTerminalsForSession(parentId, sessionId) { released.push([parentId, sessionId]); },
    },
    registerTool(tool) { tools.push(tool); },
    on(name, handler) { assert.equal(name, "session_shutdown"); pi.shutdown = handler; },
  };
  return pi;
}

function acceptedTerminal(captured, verdict, handle, parentId = "Main", sessionId = "session-1") {
  const binding = captured.details.binding;
  return {
    schema: "iis-ready-host-terminal/v1",
    handle,
    owner_id: "Verifier",
    verifier_model: "test/verifier",
    parent_id: parentId,
    parent_session_id: sessionId,
    project_root: binding.project_root,
    ticket_path: binding.ticket_path,
    verification_binding: captured.details.binding_path,
    verification_binding_sha256: captured.details.binding_sha256,
    stable_target_paths: binding.stable_target_paths,
    scenario_effect_paths: binding.scenario_effect_paths,
    verification_verdict: verdict,
    ticket_progression: binding.ticket_status_at_capture === "ready" ? "PENDING CALLER FINALIZATION" : "NOT APPLICABLE",
    observed_ticket_status: binding.ticket_status_at_capture,
    report: `READY TICKET VERIFICATION RESULT\nVerification Verdict: ${verdict}`,
  };
}

const context = { agentId: "Main", sessionId: "session-1" };

async function installFromBundle(f, pi, options = {}) {
  const loaded = await materializeReadyBundle(f.base);
  const authority = await bindAuthority({
    projectRoot: f.root,
    ticketPath: f.ticket,
    validatorPath: f.validatorPath,
    executeArgv: executeArgvNode,
    bundleIdentity: loaded.bundleId,
  });
  f.reviewData.contracts = [{
    ticket_path: f.ticket,
    ticket_sha256: authority.ticket_sha256,
    authority_digest: authority.authority_digest,
  }];
  fs.writeFileSync(f.review, JSON.stringify(f.reviewData));
  loaded.module.installReadyBoundaryTools(pi, {
    executeArgv: executeArgvNode,
    validatorPath: f.validatorPath,
    ...options,
  });
  return loaded;
}

test("OMP extension registers exactly ready_contract and ready_finalize", async t => {
  const f = await fixture(t);
  const pi = fakePi();
  await installFromBundle(f, pi);
  assert.deepEqual(pi.tools.map(tool => tool.name), ["ready_contract", "ready_finalize"]);
});

test("registered surface captures binding and finalizes only a host-accepted verifier terminal", async t => {
  const f = await fixture(t);
  const terminals = new Map();
  const pi = fakePi(terminals);
  let verdictCounter = 0;
  await installFromBundle(f, pi, {
    verdictRecordPath: () => path.join(f.base, `host-verdict-${++verdictCounter}.json`),
  });
  const contract = pi.tools.find(tool => tool.name === "ready_contract");
  const finalizer = pi.tools.find(tool => tool.name === "ready_finalize");
  const admission = await contract.execute("a", {
    action: "check_plan_admission", project_root: f.root, ticket_path: f.ticket, plan_review_path: f.review,
  });
  assert.equal(admission.details.decision, "ADMIT");
  const captured = await contract.execute("b", {
    action: "capture_verification", project_root: f.root, ticket_path: f.ticket,
    plan_review_path: f.review, stable_target_paths: [f.stable], scenario_effect_paths: [f.effect],
    binding_path: path.join(f.base, "omp-binding.json"),
  });
  const accepted = acceptedTerminal(captured, "VERIFIED", "terminal-verified");
  terminals.set(accepted.handle, accepted);
  const finalized = await finalizer.execute("c", { terminal_handle: accepted.handle }, undefined, undefined, context);
  assert.equal(finalized.details.ticket_progression, "COMPLETED");
  assert.equal(finalized.details.progression_basis, "WRITE_PERFORMED_THIS_CALL");
  assert.equal(finalized.details.verification_terminal, accepted.handle);
  assert.equal(finalized.details.verification_owner, "Verifier");
  assert.ok(fs.existsSync(finalized.details.verification_verdict_record));
  assert.match(fs.readFileSync(f.ticket, "utf8"), /^Status: done$/m);

  const recovered = await finalizer.execute("d", { terminal_handle: accepted.handle }, undefined, undefined, context);

  assert.deepEqual(recovered.details, finalized.details);
  assert.equal(recovered.details.progression_basis, "WRITE_PERFORMED_THIS_CALL");
});

test("caller recapture cannot rebind an accepted terminal, while a fresh verifier rerun remains valid", async t => {
  const f = await fixture(t);
  const terminals = new Map();
  const pi = fakePi(terminals);
  let verdictCounter = 0;
  await installFromBundle(f, pi, {
    verdictRecordPath: () => path.join(f.base, `rerun-verdict-${++verdictCounter}.json`),
  });
  const contract = pi.tools.find(tool => tool.name === "ready_contract");
  const finalizer = pi.tools.find(tool => tool.name === "ready_finalize");
  const first = await contract.execute("capture-first", {
    action: "capture_verification", project_root: f.root, ticket_path: f.ticket,
    stable_target_paths: [f.stable], binding_path: path.join(f.base, "first-binding.json"),
  });
  const recaptured = await contract.execute("capture-second", {
    action: "capture_verification", project_root: f.root, ticket_path: f.ticket,
    stable_target_paths: [f.stable], binding_path: path.join(f.base, "second-binding.json"),
  });
  const failedTerminal = acceptedTerminal(first, "FAILED", "terminal-first");
  terminals.set(failedTerminal.handle, failedTerminal);
  const failed = await finalizer.execute(
    "failed",
    { terminal_handle: failedTerminal.handle, binding_path: recaptured.details.binding_path },
    undefined,
    undefined,
    context,
  );
  assert.equal(failed.details.verification_binding, first.details.binding_path);
  assert.equal(failed.details.ticket_progression, "NOT APPLICABLE");
  assert.equal(terminals.get(failedTerminal.handle).finalization_result.ticket_progression, "NOT APPLICABLE");

  const freshTerminal = acceptedTerminal(recaptured, "VERIFIED", "terminal-second");
  terminals.set(freshTerminal.handle, freshTerminal);
  const completed = await finalizer.execute(
    "fresh",
    { terminal_handle: freshTerminal.handle },
    undefined,
    undefined,
    context,
  );
  assert.equal(completed.details.verification_binding, recaptured.details.binding_path);
  assert.equal(completed.details.ticket_progression, "COMPLETED");
  assert.match(fs.readFileSync(f.ticket, "utf8"), /^Status: done$/m);
});

test("ordinary task output or caller verdict fields cannot reach ready_finalize", async t => {
  const f = await fixture(t);
  const pi = fakePi();
  await installFromBundle(f, pi);
  const finalizer = pi.tools.find(tool => tool.name === "ready_finalize");
  await assert.rejects(
    finalizer.execute("finalize", { terminal_handle: "ordinary-result", verdict: "VERIFIED" }, undefined, undefined, context),
    /unknown or foreign verifier terminal/,
  );
  assert.match(fs.readFileSync(f.ticket, "utf8"), /^Status: ready$/m);
});

test("a host-accepted FAILED verdict cannot be upgraded by the caller", async t => {
  const f = await fixture(t);
  const terminals = new Map();
  const pi = fakePi(terminals);
  await installFromBundle(f, pi, {
    verdictRecordPath: () => path.join(f.base, "failed-verdict.json"),
  });
  const contract = pi.tools.find(tool => tool.name === "ready_contract");
  const finalizer = pi.tools.find(tool => tool.name === "ready_finalize");
  const captured = await contract.execute("capture", {
    action: "capture_verification", project_root: f.root, ticket_path: f.ticket,
    stable_target_paths: [f.stable], binding_path: path.join(f.base, "failed-binding.json"),
  });
  const accepted = acceptedTerminal(captured, "FAILED", "terminal-failed");
  terminals.set(accepted.handle, accepted);
  const result = await finalizer.execute(
    "finalize",
    { terminal_handle: accepted.handle, verdict: "VERIFIED" },
    undefined,
    undefined,
    context,
  );
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
});
