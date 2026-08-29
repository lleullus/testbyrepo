import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { bindAuthority, checkAuthorityCurrentness } from "../src/authority-binding.js";
import { ReadyLifecycle } from "../src/lifecycle.js";
import { ManagedServiceRegistry } from "../src/service-supervisor.js";
import { RuntimeStore } from "../src/state-store.js";

function tempRoot() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "iis-ready-authority-test-"));
}

function git(root, ...args) {
  const result = spawnSync("git", ["-C", root, ...args], { encoding: "utf8", shell: false });
  assert.equal(result.status, 0, result.stderr);
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
    validator_path: "/tmp/validator.py",
    validator_sha256: "validator-sha",
    git_head: "head",
    baseline_worktree_fingerprint: { status_digest: "status", tracked_changed_paths: [], preexisting_untracked_paths: [] },
    protected_artifacts: [],
  };
}

test("authority binding computes its own canonical validator and detects protected authority drift", async t => {
  const root = tempRoot();
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const project = path.join(root, "project");
  const workflow = path.join(root, "workflow", "SKILL.md");
  const toTickets = path.join(root, "to-tickets", "SKILL.md");
  const validator = path.join(root, "to-tickets", "validate_ticket.py");
  fs.mkdirSync(project, { recursive: true });
  fs.mkdirSync(path.dirname(workflow), { recursive: true });
  fs.mkdirSync(path.dirname(toTickets), { recursive: true });

  fs.writeFileSync(workflow, `# IIS\n\n### To Tickets\n\nAn explicit request routes to:\n\n${toTickets}\n`);
  fs.writeFileSync(toTickets, "# To Tickets\n");
  fs.writeFileSync(validator, "import sys\nprint('VALID')\n");
  fs.writeFileSync(path.join(project, "SPEC.md"), "# Spec\n\nStatus: approved\n\n## UI / UX\n\n- ./UI-UX.md | Scope: exact rendered surface\n");
  fs.writeFileSync(path.join(project, "behavior.md"), "# Behavior\n");
  fs.writeFileSync(path.join(project, "UI-UX.md"), "# UI authority\n");
  const ticket = path.join(project, "TICKET-001.md");
  fs.writeFileSync(ticket, [
    "# Ticket",
    "",
    "Status: ready",
    "Parent-Spec: ./SPEC.md",
    `Project-Root: ${project}`,
    "UI: yes",
    "",
    "## Behavior Authorities",
    "",
    "- behavior.md | Scope: exact behavior",
    "",
    "## References",
    "",
    "- ./SPEC.md",
    "",
  ].join("\n"));

  git(project, "init");
  git(project, "config", "user.email", "ready-runtime@example.invalid");
  git(project, "config", "user.name", "Ready Runtime Test");
  git(project, "add", ".");
  git(project, "commit", "-m", "fixture");

  const previous = process.env.IIS_READY_IIS_WORKFLOW_SKILL;
  process.env.IIS_READY_IIS_WORKFLOW_SKILL = workflow;
  t.after(() => {
    if (previous === undefined) delete process.env.IIS_READY_IIS_WORKFLOW_SKILL;
    else process.env.IIS_READY_IIS_WORKFLOW_SKILL = previous;
  });

  const binding = await bindAuthority({ projectRoot: project, ticketPath: ticket });
  assert.equal(binding.ticket_status_at_start, "ready");
  assert.equal(binding.validator_path, fs.realpathSync(validator));
  assert.equal(binding.behavior_authorities.length, 1);
  assert.equal(binding.ui_authority.path, fs.realpathSync(path.join(project, "UI-UX.md")));
  assert.deepEqual(binding.protected_artifacts.map(item => item.kind), ["ticket", "parent_spec", "behavior", "ui", "validator"]);
  assert.equal((await checkAuthorityCurrentness(binding)).current, true);

  fs.appendFileSync(path.join(project, "behavior.md"), "changed\n");
  const drift = await checkAuthorityCurrentness(binding);
  assert.equal(drift.current, false);
  assert.equal(drift.changed[0].kind, "behavior");
});

test("managed service is execution-owned and mutation uncertainty is explicit rather than retried", async t => {
  const root = tempRoot();
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const project = path.join(root, "project");
  const ticket = path.join(project, "TICKET.md");
  fs.mkdirSync(project, { recursive: true });

  const lifecycle = new ReadyLifecycle({
    store: new RuntimeStore(path.join(root, "state")),
    bindAuthority: async () => fakeBinding(project, ticket),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  lifecycle.armSession("main");
  const execution = await lifecycle.beginDirect({ sessionId: "main", projectRoot: project, ticketPath: ticket });

  const services = new ManagedServiceRegistry({ lifecycle });
  const service = services.start(execution.execution_id, "main", {
    version: 1,
    argv: [process.execPath, "-e", "setInterval(() => {}, 1000)"],
  });
  assert.ok(service.pid > 0);
  assert.throws(
    () => services.start(execution.execution_id, "main", { version: 1, argv: [process.execPath, "-e", "0"] }),
    /already owns a managed service/,
  );
  await services.stop(execution.execution_id, "main");
  assert.equal(services.status(execution.execution_id), null);

  lifecycle.beginOperation(execution.execution_id, { toolCallId: "mut-1", kind: "mutation" });
  lifecycle.markMutationUncertain(execution.execution_id, "mut-1", "transport timeout");
  assert.equal(lifecycle.status(execution.execution_id).phase, "MUTATION_UNCERTAIN");
  assert.throws(
    () => lifecycle.beginOperation(execution.execution_id, { toolCallId: "mut-1-retry", kind: "mutation" }),
    /not runnable/,
  );
  lifecycle.resolveMutationUncertainty(execution.execution_id, "not_applied");
  assert.equal(lifecycle.status(execution.execution_id).mutation_revision, 0);
  assert.equal(lifecycle.status(execution.execution_id).phase, "ACTIVE");
});
