import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { validateInspectRequest, validateMutationRequest } from "../src/argv-policy.js";
import { isBroadInventory } from "../src/inventory-policy.js";
import { ReadyLifecycle } from "../src/lifecycle.js";
import { prepareObservation, recordObservationResult } from "../src/observation-ledger.js";
import { classifyError, mayRetryRead } from "../src/retry-policy.js";
import { RuntimeStore } from "../src/state-store.js";

function tempRoot() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "iis-ready-runtime-test-"));
}

function fakeBinding(projectRoot, ticketPath) {
  return {
    project_root: projectRoot,
    ticket_path: ticketPath,
    ticket_sha256: "ticket-sha",
    ticket_status_at_start: "ready",
    parent_spec_path: path.join(projectRoot, "SPEC.md"),
    parent_spec_sha256: "spec-sha",
    behavior_authorities: [],
    ui_authority: null,
    validator_path: "/tmp/validate_ticket.py",
    validator_sha256: "validator-sha",
    git_head: "0123456789abcdef",
    baseline_worktree_fingerprint: {
      status_digest: "status-sha",
      tracked_changed_paths: [],
      preexisting_untracked_paths: [],
    },
    protected_artifacts: [
      { path: ticketPath, sha256: "ticket-sha", kind: "ticket" },
      { path: path.join(projectRoot, "SPEC.md"), sha256: "spec-sha", kind: "parent_spec" },
    ],
  };
}

test("DIRECT lifecycle binds once, serializes operations, increments mutation revision, and closes terminally", async t => {
  const root = tempRoot();
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const projectRoot = path.join(root, "project");
  const ticketPath = path.join(projectRoot, "TICKET-001.md");
  fs.mkdirSync(projectRoot, { recursive: true });

  const store = new RuntimeStore(path.join(root, "state"));
  const lifecycle = new ReadyLifecycle({
    store,
    bindAuthority: async () => fakeBinding(projectRoot, ticketPath),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });

  lifecycle.armSession("session-main");
  const execution = await lifecycle.beginDirect({
    sessionId: "session-main",
    projectRoot,
    ticketPath,
  });
  assert.equal(execution.phase, "ACTIVE");
  assert.equal(execution.mutation_revision, 0);

  lifecycle.beginOperation(execution.execution_id, {
    toolCallId: "call-1",
    kind: "mutation",
  });
  assert.throws(
    () => lifecycle.beginOperation(execution.execution_id, { toolCallId: "call-2", kind: "observation" }),
    /active guarded operation/,
  );
  lifecycle.finishOperation(execution.execution_id, "call-1", { mutationApplied: true });
  assert.equal(lifecycle.status(execution.execution_id).mutation_revision, 1);

  lifecycle.noteCurrentEvidence(execution.execution_id, 1);
  const terminal = await lifecycle.complete(execution.execution_id, "session-main");
  assert.equal(terminal.phase, "COMPLETE");
  assert.equal(store.readActiveTicket(projectRoot, ticketPath), null);
});

test("SUBAGENT is one-use, PRE_ACTION gated, MATERIAL_TURN gated, and never falls back to DIRECT", async t => {
  const root = tempRoot();
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const projectRoot = path.join(root, "project");
  const ticketPath = path.join(projectRoot, "TICKET-001.md");
  fs.mkdirSync(projectRoot, { recursive: true });

  const store = new RuntimeStore(path.join(root, "state"));
  const lifecycle = new ReadyLifecycle({
    store,
    bindAuthority: async () => fakeBinding(projectRoot, ticketPath),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });

  lifecycle.armSession("parent");
  lifecycle.armSession("child");
  lifecycle.armSession("child-2");
  const assignment = await lifecycle.assignSubagent({
    parentSessionId: "parent",
    projectRoot,
    ticketPath,
  });
  const child = await lifecycle.beginDelegated({ childSessionId: "child", assignmentId: assignment.assignment_id });
  assert.equal(child.phase, "PRE_ACTION_PENDING");
  await assert.rejects(
    lifecycle.beginDelegated({ childSessionId: "child-2", assignmentId: assignment.assignment_id }),
    /already consumed/,
  );

  lifecycle.checkpointPreAction(child.execution_id, "child");
  lifecycle.releaseCheckpoint(child.execution_id, "parent", "CONTINUE");
  assert.equal(lifecycle.status(child.execution_id).phase, "ACTIVE");

  lifecycle.checkpointMaterialTurn(child.execution_id, "child", "material direction changed");
  assert.equal(lifecycle.status(child.execution_id).phase, "MATERIAL_TURN_PENDING");
  lifecycle.releaseCheckpoint(child.execution_id, "parent", "STEER");
  assert.equal(lifecycle.status(child.execution_id).phase, "MATERIAL_TURN_PENDING");
  lifecycle.checkpointMaterialTurn(child.execution_id, "child", "steered direction re-reported");
  lifecycle.releaseCheckpoint(child.execution_id, "parent", "CONTINUE");
  assert.equal(lifecycle.status(child.execution_id).phase, "ACTIVE");
});

test("observation ledger blocks identical success only in the same mutation revision", () => {
  const state = { mutation_revision: 0, observations: { entries: {} } };
  const first = prepareObservation(state, "read", { path: "src/a.js" }, false);
  assert.equal(first.allowed, true);
  recordObservationResult(state, first.digest, { success: true, outputBytes: 12 });

  const duplicate = prepareObservation(state, "read", { path: "src/a.js" }, false);
  assert.equal(duplicate.allowed, false);
  assert.match(duplicate.reason, /already succeeded/);

  state.mutation_revision = 1;
  const afterMutation = prepareObservation(state, "read", { path: "src/a.js" }, false);
  assert.equal(afterMutation.allowed, true);
});

test("broad inventory is exact and phase-sensitive at the policy boundary", () => {
  assert.equal(isBroadInventory("bash", { argv: ["rg", "--files"] }), true);
  assert.equal(isBroadInventory("bash", { argv: ["rg", "--files", "src"] }), false);
  assert.equal(isBroadInventory("bash", { argv: ["git", "ls-files"] }), true);
  assert.equal(isBroadInventory("bash", { argv: ["git", "worktree", "list"] }), false);
  assert.equal(isBroadInventory("glob", { pattern: "**/*" }), true);
  assert.equal(isBroadInventory("glob", { pattern: "src/**/*.js" }), false);
});

test("retry policy retries only identical read-only transport failures up to three attempts", () => {
  assert.equal(classifyError("Connection failed"), "TRANSPORT_NETWORK");
  assert.equal(classifyError("session not found"), "PROTOCOL_SESSION");
  assert.equal(classifyError("permission denied"), "DOMAIN_DATA");
  assert.equal(classifyError("validator returned invalid"), "DOMAIN_DATA");
  assert.equal(classifyError("unexpected parser failure"), "TOOL_APPLICATION");

  assert.equal(mayRetryRead({ classification: "TRANSPORT_NETWORK", attempts: 1, sameInput: true }), true);
  assert.equal(mayRetryRead({ classification: "TRANSPORT_NETWORK", attempts: 2, sameInput: true }), true);
  assert.equal(mayRetryRead({ classification: "TRANSPORT_NETWORK", attempts: 3, sameInput: true }), false);
  assert.equal(mayRetryRead({ classification: "DOMAIN_DATA", attempts: 1, sameInput: true }), false);
  assert.equal(mayRetryRead({ classification: "TRANSPORT_NETWORK", attempts: 1, sameInput: false }), false);
});

test("structured argv accepts explicit read-only argv and rejects shell hiding or unsupported mutation", () => {
  assert.deepEqual(validateInspectRequest({ version: 1, commands: [["git", "status", "--short"], ["rg", "needle", "src"]] }), {
    version: 1,
    commands: [["git", "status", "--short"], ["rg", "needle", "src"]],
  });
  assert.throws(
    () => validateInspectRequest({ version: 1, commands: [["bash", "-lc", "cat a"]] }),
    /shell interpreter/,
  );
  assert.throws(
    () => validateInspectRequest({ version: 1, commands: [["rm", "-rf", "tmp"]] }),
    /read-only allowlist/,
  );
  assert.deepEqual(validateMutationRequest({ version: 1, argv: ["python3", "scripts/update.py"] }), {
    version: 1,
    argv: ["python3", "scripts/update.py"],
  });
  assert.throws(
    () => validateMutationRequest({ version: 1, argv: ["sh", "-c", "echo x > file"] }),
    /shell interpreter/,
  );
});

test("persisted interrupted operations recover as incomplete observation or mutation uncertainty", async t => {
  const root = tempRoot();
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const projectRoot = path.join(root, "project");
  const ticketPath = path.join(projectRoot, "TICKET-001.md");
  fs.mkdirSync(projectRoot, { recursive: true });

  const store = new RuntimeStore(path.join(root, "state"));
  const lifecycle = new ReadyLifecycle({
    store,
    bindAuthority: async () => fakeBinding(projectRoot, ticketPath),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  lifecycle.armSession("resume");
  const execution = await lifecycle.beginDirect({ sessionId: "resume", projectRoot, ticketPath });

  const observationState = lifecycle.status(execution.execution_id);
  const prepared = prepareObservation(observationState, "read", { path: "src/a.js" }, false);
  store.writeExecution(observationState);
  lifecycle.beginOperation(execution.execution_id, {
    toolCallId: "read-interrupted",
    kind: "observation",
    observationDigest: prepared.digest,
  });
  let recovered = lifecycle.recoverInterruptedOperation("resume");
  assert.equal(recovered.active_operation, null);
  assert.equal(recovered.observations.entries[prepared.digest].status, "incomplete");

  lifecycle.beginOperation(execution.execution_id, {
    toolCallId: "mutation-interrupted",
    kind: "mutation",
    mutationDigest: "same-mutation",
  });
  recovered = lifecycle.recoverInterruptedOperation("resume");
  assert.equal(recovered.phase, "MUTATION_UNCERTAIN");
  assert.equal(recovered.uncertainty.operation.mutation_digest, "same-mutation");
});
