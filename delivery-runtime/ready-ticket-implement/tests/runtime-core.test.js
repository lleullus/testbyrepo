import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { isReadOnlyArgv, parseSimpleReadOnlyCommand, runArgv, validateExecutionRequest, validateInspectRequest, validateMutationRequest } from "../src/argv-policy.js";
import { inventoryAllowedForPhase, isBroadInventory } from "../src/inventory-policy.js";
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
  assert.equal(lifecycle.status(execution.execution_id).implementation_mutation_started, true);
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

test("admission cancellation clears only an armed unbound session and leaves bound states unchanged", async t => {
  const root = tempRoot();
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));

  const createLifecycle = name => {
    const projectRoot = path.join(root, name, "project");
    const ticketPath = path.join(projectRoot, "TICKET-001.md");
    fs.mkdirSync(projectRoot, { recursive: true });
    const store = new RuntimeStore(path.join(root, name, "state"));
    const lifecycle = new ReadyLifecycle({
      store,
      bindAuthority: async () => fakeBinding(projectRoot, ticketPath),
      checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
    });
    return { lifecycle, projectRoot, ticketPath };
  };

  const direct = createLifecycle("direct");
  direct.lifecycle.armSession("direct-owner");
  direct.lifecycle.armSession("other-session");
  const otherSession = direct.lifecycle.sessionState("other-session");
  const cancelled = direct.lifecycle.cancelAdmission("direct-owner");
  assert.equal(cancelled.armed, false);
  assert.equal(cancelled.purpose, null);
  assert.deepEqual(direct.lifecycle.sessionState("other-session"), otherSession);
  direct.lifecycle.armSession("direct-owner");
  const execution = await direct.lifecycle.beginDirect({
    sessionId: "direct-owner",
    projectRoot: direct.projectRoot,
    ticketPath: direct.ticketPath,
  });
  const activeSession = direct.lifecycle.sessionState("direct-owner");
  assert.throws(() => direct.lifecycle.cancelAdmission("direct-owner"), /unavailable after execution, assignment, parent, or worker binding/);
  assert.deepEqual(direct.lifecycle.sessionState("direct-owner"), activeSession);

  direct.lifecycle.beginOperation(execution.execution_id, { toolCallId: "uncertain-mutation", kind: "mutation" });
  direct.lifecycle.recoverInterruptedOperation("direct-owner");
  const uncertainExecution = direct.lifecycle.status(execution.execution_id);
  assert.equal(uncertainExecution.phase, "MUTATION_UNCERTAIN");
  assert.throws(() => direct.lifecycle.cancelAdmission("direct-owner"), /unavailable after execution, assignment, parent, or worker binding/);
  assert.deepEqual(direct.lifecycle.status(execution.execution_id), uncertainExecution);

  const terminal = createLifecycle("terminal");
  terminal.lifecycle.armSession("terminal-owner");
  const terminalExecution = await terminal.lifecycle.beginDirect({
    sessionId: "terminal-owner",
    projectRoot: terminal.projectRoot,
    ticketPath: terminal.ticketPath,
  });
  terminal.lifecycle.noteCurrentEvidence(terminalExecution.execution_id, 0);
  await terminal.lifecycle.complete(terminalExecution.execution_id, "terminal-owner");
  const completedHistory = terminal.lifecycle.status(terminalExecution.execution_id);
  assert.equal(completedHistory.phase, "COMPLETE");
  assert.throws(() => terminal.lifecycle.cancelAdmission("terminal-owner"), /requires the current session to be ARMED/);
  assert.deepEqual(terminal.lifecycle.status(terminalExecution.execution_id), completedHistory);

  const delegated = createLifecycle("delegated");
  delegated.lifecycle.armSession("parent");
  const assignment = await delegated.lifecycle.assignSubagent({
    parentSessionId: "parent",
    projectRoot: delegated.projectRoot,
    ticketPath: delegated.ticketPath,
  });
  const assignedParent = delegated.lifecycle.sessionState("parent");
  assert.throws(() => delegated.lifecycle.cancelAdmission("parent"), /unavailable after execution, assignment, parent, or worker binding/);
  assert.deepEqual(delegated.lifecycle.sessionState("parent"), assignedParent);

  delegated.lifecycle.armSession("child");
  const delegatedExecution = await delegated.lifecycle.beginDelegated({ childSessionId: "child", assignmentId: assignment.assignment_id });
  for (const sessionId of ["parent", "child"]) {
    const before = delegated.lifecycle.sessionState(sessionId);
    assert.throws(() => delegated.lifecycle.cancelAdmission(sessionId), /unavailable after execution, assignment, parent, or worker binding/);
    assert.deepEqual(delegated.lifecycle.sessionState(sessionId), before);
  }
  delegated.lifecycle.checkpointPreAction(delegatedExecution.execution_id, "child");
  delegated.lifecycle.releaseCheckpoint(delegatedExecution.execution_id, "parent", "CONTINUE");
  delegated.lifecycle.noteCurrentEvidence(delegatedExecution.execution_id, 0);
  await delegated.lifecycle.complete(delegatedExecution.execution_id, "child");
  delegated.lifecycle.armSession("parent");
  const nextAssignment = await delegated.lifecycle.assignSubagent({
    parentSessionId: "parent", projectRoot: delegated.projectRoot, ticketPath: delegated.ticketPath,
  });
  delegated.lifecycle.armSession("child");
  const nextExecution = await delegated.lifecycle.beginDelegated({ childSessionId: "child", assignmentId: nextAssignment.assignment_id });
  assert.equal(nextExecution.phase, "PRE_ACTION_PENDING");
  assert.equal(delegated.lifecycle.status(delegatedExecution.execution_id).phase, "COMPLETE");
});

test("cancel and rearm invalidate in-flight direct and assignment admission commits", async t => {
  const root = tempRoot();
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));

  for (const admission of ["direct", "assignment"]) {
    await t.test(admission, async () => {
      const projectRoot = path.join(root, admission, "project");
      const ticketPath = path.join(projectRoot, "TICKET-001.md");
      fs.mkdirSync(projectRoot, { recursive: true });
      const store = new RuntimeStore(path.join(root, admission, "state"));
      let signalEntered;
      let releaseBinding;
      const bindingEntered = new Promise(resolve => { signalEntered = resolve; });
      const bindingRelease = new Promise(resolve => { releaseBinding = resolve; });
      let bindingCalls = 0;
      const lifecycle = new ReadyLifecycle({
        store,
        bindAuthority: async () => {
          bindingCalls += 1;
          if (bindingCalls === 1) {
            signalEntered();
            await bindingRelease;
          }
          return fakeBinding(projectRoot, ticketPath);
        },
        checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
      });
      const sessionId = `${admission}-owner`;
      lifecycle.armSession(sessionId);
      const pending = admission === "direct"
        ? lifecycle.beginDirect({ sessionId, projectRoot, ticketPath })
        : lifecycle.assignSubagent({ parentSessionId: sessionId, projectRoot, ticketPath });
      await bindingEntered;
      lifecycle.cancelAdmission(sessionId);
      lifecycle.armSession(sessionId);
      releaseBinding();
      await assert.rejects(pending, /admission is no longer current/);
      assert.equal(lifecycle.sessionState(sessionId).armed, true);
      assert.equal(lifecycle.sessionState(sessionId).execution_id ?? null, null);
      assert.equal(lifecycle.sessionState(sessionId).assignment_id ?? null, null);
      assert.equal(store.readActiveTicket(projectRoot, ticketPath), null);

      const fresh = admission === "direct"
        ? await lifecycle.beginDirect({ sessionId, projectRoot, ticketPath })
        : await lifecycle.assignSubagent({ parentSessionId: sessionId, projectRoot, ticketPath });
      assert.equal(admission === "direct" ? fresh.phase : fresh.status, admission === "direct" ? "ACTIVE" : "issued");
    });
  }
});

test("observation ledger reopens an exact observation only when currentness or mutation revision changes", () => {
  const state = { mutation_revision: 0, observations: { entries: {} } };
  const first = prepareObservation(state, "read", { path: "src/a.js" }, false, "content-a");
  assert.equal(first.allowed, true);
  recordObservationResult(state, first.digest, { success: true, outputBytes: 12 });

  const duplicate = prepareObservation(state, "read", { path: "src/a.js" }, false, "content-a");
  assert.equal(duplicate.allowed, false);
  assert.match(duplicate.reason, /already succeeded/);

  const externallyChanged = prepareObservation(state, "read", { path: "src/a.js" }, false, "content-b");
  assert.equal(externallyChanged.allowed, true);
  recordObservationResult(state, externallyChanged.digest, { success: true, outputBytes: 12 });

  const unchangedAgain = prepareObservation(state, "read", { path: "src/a.js" }, false, "content-b");
  assert.equal(unchangedAgain.allowed, false);
  assert.match(unchangedAgain.reason, /already succeeded/);

  state.mutation_revision = 1;
  const afterMutation = prepareObservation(state, "read", { path: "src/a.js" }, false, "content-b");
  assert.equal(afterMutation.allowed, true);
});

test("broad inventory is exact and limited to one DIRECT pre-mutation inventory", () => {
  assert.equal(isBroadInventory("bash", { argv: ["rg", "--files"] }), true);
  assert.equal(isBroadInventory("bash", { argv: ["rg", "--files", "src"] }), false);
  assert.equal(isBroadInventory("bash", { argv: ["git", "ls-files"] }), true);
  assert.equal(isBroadInventory("bash", { argv: ["git", "worktree", "list"] }), false);
  assert.equal(isBroadInventory("glob", { pattern: "**/*" }), true);
  assert.equal(isBroadInventory("glob", { pattern: "src/**/*.js" }), false);

  const directPreflight = {
    phase: "ACTIVE",
    purpose: "implement",
    execution_mode: "DIRECT",
    implementation_mutation_started: false,
    preflight_broad_inventory_used: false,
  };
  assert.equal(inventoryAllowedForPhase(directPreflight, true).allowed, true);
  assert.equal(inventoryAllowedForPhase(directPreflight, true).allowed, false);

  const afterMutation = {
    ...directPreflight,
    implementation_mutation_started: true,
    preflight_broad_inventory_used: false,
  };
  const blockedAfterMutation = inventoryAllowedForPhase(afterMutation, true);
  assert.equal(blockedAfterMutation.allowed, false);
  assert.match(blockedAfterMutation.reason, /mutation begins/);

  const legacyActive = {
    phase: "ACTIVE",
    purpose: "implement",
    execution_mode: "DIRECT",
    preflight_broad_inventory_used: false,
  };
  assert.equal(inventoryAllowedForPhase(legacyActive, true).allowed, false);
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

test("structured argv accepts bounded read-only observations and rejects shell hiding or unsupported mutation", () => {
  const accepted = [
    { argv: ["cat", "README.md"], command: "cat README.md" },
    { argv: ["rg", "-n", "needle", "src"], command: "rg -n needle src" },
    { argv: ["rg", "-e", "--pre=literal", "src"], command: "rg -e '--pre=literal' src" },
    { argv: ["git", "grep", "-e", "-Oeditor", "--", "app.py"], command: "git grep -e '-Oeditor' -- app.py" },
    { argv: ["git", "rev-parse", "HEAD"], command: "git rev-parse HEAD" },
    { argv: ["git", "status", "--short"], command: "git status --short" },
    { argv: ["git", "diff", "--exit-code", "HEAD", "--", "app.py", "engine.py"], command: "git diff --exit-code HEAD -- app.py engine.py" },
    { argv: ["git", "log", "-n", "5", "--oneline"], command: "git log -n 5 --oneline" },
    { argv: ["git", "ls-files", "src"], command: "git ls-files src" },
    { argv: ["git", "worktree", "list", "--porcelain"], command: "git worktree list --porcelain" },
    { argv: ["sed", "-n", "1,20p", "README.md"], command: "sed -n '1,20p' README.md" },
    { argv: ["sed", "-ne1,20p", "README.md"], command: "sed -ne'1,20p' README.md" },
    { argv: ["find", "src", "-maxdepth", "2", "-type", "f", "-print"], command: "find src -maxdepth 2 -type f -print" },
    { argv: ["find", "src", "-name", "-delete", "-print"], command: "find src -name '-delete' -print" },
    { argv: ["sort", "-k1,1", "README.md"], command: "sort -k1,1 README.md" },
    { argv: ["tree", "-L", "2", "src"], command: "tree -L 2 src" },
    { argv: ["file", "-b", "README.md"], command: "file -b README.md" },
  ];

  for (const { argv, command } of accepted) {
    assert.deepEqual(validateInspectRequest({ version: 1, commands: [argv] }), {
      version: 1,
      commands: [argv],
    }, command);
    assert.equal(isReadOnlyArgv(argv), true, command);
    assert.deepEqual(parseSimpleReadOnlyCommand(command), argv, command);
  }

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

test("structured mutation and verification preserve empty argument positions in the child process", async () => {
  const argv = [process.execPath, "-e", "process.stdout.write(JSON.stringify(process.argv.slice(1)))", "--", "", "middle", ""];
  for (const validate of [validateMutationRequest, validateExecutionRequest]) {
    const result = await runArgv(validate({ version: 1, argv }).argv);
    assert.equal(result.exitCode, 0);
    assert.deepEqual(JSON.parse(result.stdout), ["", "middle", ""]);
  }
});

test("allowing empty arguments retains executable, type and read-only option protections", () => {
  for (const argv of [[], [""], ["", "argument"], [process.execPath, null], ["sh", "-c", ""]]) {
    for (const validate of [validateMutationRequest, validateExecutionRequest]) {
      assert.throws(() => validate({ version: 1, argv }));
    }
  }
  assert.throws(() => validateInspectRequest({ version: 1, commands: [["rg", "-e", "", "--pre=processor", "src"]] }), /read-only allowlist/);
});

test("read-only argv classification rejects side-effecting and external-execution options", () => {
  const rejected = [
    { argv: ["sed", "-i", "s/a/b/", "witness.txt"], command: "sed -i 's/a/b/' witness.txt" },
    { argv: ["sed", "-ni", "1p", "witness.txt"], command: "sed -ni 1p witness.txt" },
    { argv: ["sed", "--in-place=.bak", "s/a/b/", "witness.txt"], command: "sed --in-place=.bak 's/a/b/' witness.txt" },
    { argv: ["sed", "-n", "-e", "1e id", "witness.txt"], command: "sed -n -e '1e id' witness.txt" },
    { argv: ["sed", "-n", "-e", "1w out", "witness.txt"], command: "sed -n -e '1w out' witness.txt" },
    { argv: ["sed", "-n", "-f", "commands.sed", "witness.txt"], command: "sed -n -f commands.sed witness.txt" },
    { argv: ["sort", "-o", "result", "witness.txt"], command: "sort -o result witness.txt" },
    { argv: ["sort", "-uoresult", "witness.txt"], command: "sort -uoresult witness.txt" },
    { argv: ["sort", "--output=result", "witness.txt"], command: "sort --output=result witness.txt" },
    { argv: ["sort", "--compress-program", "gzip", "witness.txt"], command: "sort --compress-program gzip witness.txt" },
    { argv: ["sort", "-Ttmp", "witness.txt"], command: "sort -Ttmp witness.txt" },
    { argv: ["find", ".", "-exec", "truncate", "-s", "0", "{}", "+"], command: "find . -exec truncate -s 0 {} +" },
    { argv: ["find", ".", "-execdir", "touch", "{}", "+"], command: "find . -execdir touch {} +" },
    { argv: ["find", ".", "-delete"], command: "find . -delete" },
    { argv: ["find", ".", "-fprint", "inventory.txt"], command: "find . -fprint inventory.txt" },
    { argv: ["rg", "--pre=processor", "needle", "src"], command: "rg --pre=processor needle src" },
    { argv: ["rg", "-nz", "needle", "src"], command: "rg -nz needle src" },
    { argv: ["rg", "--search-zip", "needle", "src"], command: "rg --search-zip needle src" },
    { argv: ["rg", "--hostname-bin=hostname-helper", "needle", "src"], command: "rg --hostname-bin=hostname-helper needle src" },
    { argv: ["file", "-bC", "magic"], command: "file -bC magic" },
    { argv: ["file", "--compile", "-m", "magic"], command: "file --compile -m magic" },
    { argv: ["file", "-z", "archive.gz"], command: "file -z archive.gz" },
    { argv: ["file", "--no-sandbox", "README.md"], command: "file --no-sandbox README.md" },
    { argv: ["tree", "-o", "inventory.txt", "src"], command: "tree -o inventory.txt src" },
    { argv: ["tree", "-L", "2", "-R", "src"], command: "tree -L 2 -R src" },
    { argv: ["git", "diff", "--output=patch.txt", "HEAD"], command: "git diff --output=patch.txt HEAD" },
    { argv: ["git", "diff", "--ext-diff", "HEAD"], command: "git diff --ext-diff HEAD" },
    { argv: ["git", "log", "--textconv", "-n", "1"], command: "git log --textconv -n 1" },
    { argv: ["git", "grep", "--open-files-in-pager=editor", "needle"], command: "git grep --open-files-in-pager=editor needle" },
    { argv: ["git", "grep", "-Oeditor", "needle"], command: "git grep -Oeditor needle" },
    { argv: ["git", "cat-file", "--filters", "HEAD:file"], command: "git cat-file --filters HEAD:file" },
  ];
  for (const operation of ["add", "lock", "move", "prune", "remove", "repair", "unlock"]) {
    rejected.push({ argv: ["git", "worktree", operation, "target"], command: `git worktree ${operation} target` });
  }

  for (const { argv, command } of rejected) {
    assert.equal(isReadOnlyArgv(argv), false, command);
    assert.equal(parseSimpleReadOnlyCommand(command), null, command);
    assert.throws(
      () => validateInspectRequest({ version: 1, commands: [argv] }),
      /read-only allowlist/,
      command,
    );
  }
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
