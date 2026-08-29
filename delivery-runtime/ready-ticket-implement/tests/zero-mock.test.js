import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { installReadyRuntime } from "../src/omp-adapter.js";
import { directTaint, environmentTaint, scanFileGraph } from "../src/no-mock-policy.js";

function schema() {
  return { optional() { return this; }, min() { return this; }, max() { return this; } };
}

function mockPi(extraTools = []) {
  const handlers = new Map();
  const tools = new Map();
  const builtin = ["read", "grep", "glob", "edit", "write", "bash"].map(name => ({
    name,
    sourceInfo: { source: "builtin", path: `<builtin:${name}>`, scope: "core", origin: "builtin" },
  }));
  return {
    handlers,
    tools,
    zod: {
      object: () => schema(), enum: () => schema(), string: () => schema(), array: () => schema(), literal: () => schema(),
    },
    on(name, handler) {
      const list = handlers.get(name) || [];
      list.push(handler);
      handlers.set(name, list);
    },
    registerTool(definition) { tools.set(definition.name, definition); },
    getAllTools() { return [...builtin, ...extraTools]; },
    async emit(name, event, ctx) {
      let result;
      for (const handler of handlers.get(name) || []) result = await handler(event, ctx);
      return result;
    },
  };
}

function context(session, cwd) {
  return { cwd, sessionManager: { getSessionId: () => session } };
}

function parse(result) {
  return JSON.parse(result.content[0].text);
}

function fixtureBinding(projectRoot, ticketPath, validatorPath = path.join(projectRoot, "validator.py")) {
  const root = fs.realpathSync(projectRoot);
  const ticket = fs.realpathSync(ticketPath);
  const spec = fs.realpathSync(path.join(root, "SPEC.md"));
  return {
    project_root: root,
    ticket_path: ticket,
    ticket_sha256: "ticket-sha",
    ticket_status_at_start: "ready",
    parent_spec_path: spec,
    parent_spec_sha256: "spec-sha",
    behavior_authorities: [],
    ui_authority: null,
    validator_path: validatorPath,
    validator_sha256: "validator-sha",
    git_head: "head",
    baseline_worktree_fingerprint: { status_digest: "status", tracked_changed_paths: [], preexisting_untracked_paths: [] },
    protected_artifacts: [
      { path: ticket, sha256: "ticket-sha", kind: "ticket" },
      { path: spec, sha256: "spec-sha", kind: "parent_spec" },
    ],
  };
}

function makeProject(root) {
  const project = path.join(root, "project");
  fs.mkdirSync(path.join(project, "tests"), { recursive: true });
  const ticket = path.join(project, "TICKET.md");
  fs.writeFileSync(ticket, `Status: ready\nProject-Root: ${project}\n`);
  fs.writeFileSync(path.join(project, "SPEC.md"), "Status: approved\n");
  fs.writeFileSync(path.join(project, "validator.py"), "print('VALID')\n");
  return { project, ticket };
}

async function armImplement(pi, sid, cwd) {
  await pi.emit("tool_call", { toolCallId: `skill-${sid}`, toolName: "read", input: { path: "skill://ready-ticket-implement" } }, context(sid, cwd));
}

async function armVerify(pi, sid, cwd) {
  await pi.emit("tool_call", { toolCallId: `verify-skill-${sid}`, toolName: "read", input: { path: "skill://ready-ticket-verify" } }, context(sid, cwd));
}

test("static Zero-Mock rules catch direct APIs, interception/fake persistence, and renamed wrapper taint", t => {
  assert.ok(directTaint("from unittest.mock import patch\n").some(item => item.code === "PY_UNITTEST_MOCK"));
  assert.ok(directTaint("import nock from 'nock';\n").some(item => item.code === "JS_INTERCEPT_LIBRARY"));
  assert.ok(directTaint("import { vi as potato } from 'vitest';\npotato.fn();\n").some(item => item.code === "JS_MOCK_OBJECT_IMPORT"));
  assert.ok(directTaint("from pytest import MonkeyPatch as Potato\n").some(item => item.code === "PY_PYTEST_MONKEYPATCH_CLASS"));
  assert.ok(directTaint("class FakeProviderClient {}\n").some(item => item.code === "FAKE_IMPLEMENTATION"));
  assert.ok(directTaint("const db = newDb(); // pg-mem\n").some(item => item.code === "IN_MEMORY_PERSISTENCE"));
  assert.ok(environmentTaint({ USE_MOCK_PROVIDER: "1", NORMAL: "1" }).some(item => item.code === "MOCK_MODE_ENV_ACTIVE"));

  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-static-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  fs.writeFileSync(path.join(root, "helper.py"), "from unittest.mock import patch\n\ndef gateway():\n    return patch('x.y')\n");
  fs.writeFileSync(path.join(root, "test_real.py"), "from helper import gateway\n\ndef test_it():\n    gateway()\n");
  const report = scanFileGraph(root, [path.join(root, "test_real.py")]);
  assert.equal(report.mock_taint, true);
  assert.ok(report.violations.some(item => item.path.endsWith("helper.py") && item.import_chain?.[0].endsWith("test_real.py")));
});

test("implementation blocks mock mutation before execution and fail-closes unknown MCP runners", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-gates-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const { project, ticket } = makeProject(root);
  fs.writeFileSync(path.join(project, "app.py"), "VALUE = 1\n");
  const pi = mockPi([{ name: "mcp_runner", sourceInfo: { source: "mcp", path: "mcp://runner", scope: "temporary", origin: "top-level" } }]);
  const runtime = installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => fixtureBinding(projectRoot, ticketPath),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  await armImplement(pi, "main", project);
  const guard = pi.tools.get("ready_guard");
  const begun = parse(await guard.execute("begin", { action: "begin_direct", ticket_path: ticket, project_root: project }, null, null, context("main", project)));

  const blocked = await pi.emit("tool_call", {
    toolCallId: "mock-write", toolName: "write", input: { path: "app.py", content: "from unittest.mock import patch\n" },
  }, context("main", project));
  assert.equal(blocked.block, true);
  assert.match(blocked.reason, /Zero-Mock Delivery blocked mutation/);

  const readyArgv = pi.tools.get("ready_argv");
  await assert.rejects(
    readyArgv.execute("mock-env", {
      action: "mutate", version: 1, argv: ["env", "USE_MOCK_PROVIDER=1", "python3", "-c", "print(1)"], target_paths: ["app.py"],
    }, null, null, context("main", project)),
    /Zero-Mock Delivery blocked structured mutation/,
  );

  const mcp = await pi.emit("tool_call", { toolCallId: "mcp", toolName: "mcp_runner", input: {} }, context("main", project));
  assert.equal(mcp.block, true);
  assert.match(mcp.reason, /without verifiable execution provenance/);
  assert.equal(runtime.lifecycle.status(begun.execution_id).mutation_revision, 0);
});

test("acceptance gate rejects existing mock evidence and renamed wrapper use", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-accept-reject-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const { project, ticket } = makeProject(root);
  fs.writeFileSync(path.join(project, "app.py"), "from pathlib import Path\nCONFIG = Path(__file__).with_name('config.json').read_text()\ndef value():\n    return 1\n");
  fs.writeFileSync(path.join(project, "config.json"), "{}\n");
  fs.writeFileSync(path.join(project, "tests", "helper.py"), "from unittest.mock import patch\n\ndef renamed():\n    return patch('app.value')\n");
  fs.writeFileSync(path.join(project, "tests", "test_bad.py"), "from tests.helper import renamed\nfrom app import value\n");
  const pi = mockPi();
  installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => fixtureBinding(projectRoot, ticketPath),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  await armImplement(pi, "main", project);
  const guard = pi.tools.get("ready_guard");
  await guard.execute("begin", { action: "begin_direct", ticket_path: ticket, project_root: project }, null, null, context("main", project));
  const argv = pi.tools.get("ready_argv");
  await assert.rejects(
    argv.execute("accept", {
      action: "acceptance", version: 1,
      argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_bad.py"],
      evidence_paths: ["tests/test_bad.py"], production_entrypoint: "app.py", dependency_paths: ["config.json"],
      authoritative_readback_path: "config.json",
    }, null, null, context("main", project)),
    /mock-tainted or unproven evidence/,
  );
});

test("real SQLite persistence is allowed and clean acceptance provenance can COMPLETE", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-sqlite-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const { project, ticket } = makeProject(root);
  fs.writeFileSync(path.join(project, "schema.sql"), "CREATE TABLE IF NOT EXISTS items(id INTEGER PRIMARY KEY, value TEXT NOT NULL);\n");
  fs.writeFileSync(path.join(project, "app.py"), [
    "import sqlite3",
    "from pathlib import Path",
    "ROOT = Path(__file__).parent",
    "DB = ROOT / 'actual.db'",
    "SCHEMA = (ROOT / 'schema.sql').read_text()",
    "def persist(value):",
    "    with sqlite3.connect(DB) as db:",
    "        db.executescript(SCHEMA)",
    "        db.execute('insert into items(value) values (?)', (value,))",
    "        db.commit()",
    "def values():",
    "    with sqlite3.connect(DB) as db:",
    "        return [row[0] for row in db.execute('select value from items order by id')]",
    "",
  ].join("\n"));
  fs.writeFileSync(path.join(project, "tests", "test_real_db.py"), [
    "import unittest",
    "from app import DB, persist, values",
    "class RealDbTest(unittest.TestCase):",
    "    def setUp(self):",
    "        if DB.exists(): DB.unlink()",
    "    def test_persistence(self):",
    "        persist('real')",
    "        self.assertEqual(values(), ['real'])",
    "",
  ].join("\n"));
  const pi = mockPi();
  const runtime = installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => fixtureBinding(projectRoot, ticketPath),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  await armImplement(pi, "main", project);
  const guard = pi.tools.get("ready_guard");
  const begun = parse(await guard.execute("begin", { action: "begin_direct", ticket_path: ticket, project_root: project }, null, null, context("main", project)));
  const argv = pi.tools.get("ready_argv");
  const accepted = parse(await argv.execute("accept", {
    action: "acceptance", version: 1,
    argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_real_db.py"],
    evidence_paths: ["tests/test_real_db.py"], production_entrypoint: "app.py", dependency_paths: ["schema.sql"],
    authoritative_readback_path: "actual.db",
  }, null, null, context("main", project)));
  assert.equal(accepted.status, "PASSED");
  assert.equal(accepted.mock_taint, false);
  const completed = parse(await guard.execute("complete", { action: "complete", execution_id: begun.execution_id }, null, null, context("main", project)));
  assert.equal(completed.phase, "COMPLETE");
  assert.equal(runtime.lifecycle.status(begun.execution_id).zero_mock.acceptance_provenance[0].authoritative_readback.available, true);
});

test("unavailable authoritative readback blocks implementation COMPLETE and verifier VERIFIED but permits INCONCLUSIVE", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-unavailable-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const { project, ticket } = makeProject(root);
  fs.writeFileSync(path.join(project, "app.py"), "from pathlib import Path\nCONFIG = Path(__file__).with_name('config.json').read_text()\ndef value():\n    return 1\n");
  fs.writeFileSync(path.join(project, "config.json"), "{}\n");
  fs.writeFileSync(path.join(project, "tests", "test_clean.py"), "import unittest\nfrom app import value\nclass T(unittest.TestCase):\n    def test_value(self): self.assertEqual(value(), 1)\n");

  const makeRuntime = (pi, stateDir) => installReadyRuntime(pi, {
    dataRoot: stateDir,
    bindAuthority: async ({ projectRoot, ticketPath }) => fixtureBinding(projectRoot, ticketPath),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });

  const implPi = mockPi();
  makeRuntime(implPi, path.join(root, "impl-state"));
  await armImplement(implPi, "impl", project);
  const implGuard = implPi.tools.get("ready_guard");
  const impl = parse(await implGuard.execute("begin", { action: "begin_direct", ticket_path: ticket, project_root: project }, null, null, context("impl", project)));
  const implArgv = implPi.tools.get("ready_argv");
  const inconclusive = parse(await implArgv.execute("accept", {
    action: "acceptance", version: 1,
    argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_clean.py"],
    evidence_paths: ["tests/test_clean.py"], production_entrypoint: "app.py", dependency_paths: ["config.json"],
    authoritative_readback_path: "missing-provider-readback.json",
  }, null, null, context("impl", project)));
  assert.equal(inconclusive.status, "INCONCLUSIVE");
  await assert.rejects(
    implGuard.execute("complete", { action: "complete", execution_id: impl.execution_id }, null, null, context("impl", project)),
    /Zero-Mock Delivery blocks COMPLETE/,
  );
  const blocked = parse(await implGuard.execute("block", {
    action: "block", execution_id: impl.execution_id, reason: "actual authoritative dependency/readback unavailable",
  }, null, null, context("impl", project)));
  assert.equal(blocked.phase, "BLOCKED");

  const verifyPi = mockPi();
  makeRuntime(verifyPi, path.join(root, "verify-state"));
  await armVerify(verifyPi, "verify", project);
  const verifyGuard = verifyPi.tools.get("ready_verify_guard");
  const verify = parse(await verifyGuard.execute("begin-v", { action: "begin", ticket_path: ticket, project_root: project }, null, null, context("verify", project)));
  const verifyArgv = verifyPi.tools.get("ready_argv");
  const verifyEvidence = parse(await verifyArgv.execute("accept-v", {
    action: "acceptance", version: 1,
    argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_clean.py"],
    evidence_paths: ["tests/test_clean.py"], production_entrypoint: "app.py", dependency_paths: ["config.json"],
    authoritative_readback_path: "missing-provider-readback.json",
  }, null, null, context("verify", project)));
  assert.equal(verifyEvidence.status, "INCONCLUSIVE");
  await assert.rejects(
    verifyGuard.execute("admit-v", { action: "admit", execution_id: verify.execution_id, verdict: "VERIFIED" }, null, null, context("verify", project)),
    /VERIFIED requires current Zero-Mock acceptance or direct-inspection provenance/,
  );
  const terminal = parse(await verifyGuard.execute("admit-i", { action: "admit", execution_id: verify.execution_id, verdict: "INCONCLUSIVE" }, null, null, context("verify", project)));
  assert.equal(terminal.phase, "VERIFY_TERMINAL");
});

test("clean verifier evidence admits VERIFIED, blocks product mutation, and allows one Ticket progression with post validation", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-verify-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const { project, ticket } = makeProject(root);
  fs.writeFileSync(path.join(project, "app.py"), "from pathlib import Path\nCONFIG = Path(__file__).with_name('config.json').read_text()\nREADBACK = Path(__file__).with_name('readback.txt')\ndef value():\n    return 1\n");
  fs.writeFileSync(path.join(project, "config.json"), "{}\n");
  fs.writeFileSync(path.join(project, "readback.txt"), "real\n");
  fs.writeFileSync(path.join(project, "tests", "test_clean.py"), "import unittest\nfrom app import value\nclass T(unittest.TestCase):\n    def test_value(self): self.assertEqual(value(), 1)\n");
  const validator = path.join(project, "validator.py");
  fs.writeFileSync(validator, "print('VALID')\n");

  const pi = mockPi();
  installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => fixtureBinding(projectRoot, ticketPath, validator),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  await armVerify(pi, "verify", project);
  const guard = pi.tools.get("ready_verify_guard");
  const verify = parse(await guard.execute("begin", { action: "begin", ticket_path: ticket, project_root: project }, null, null, context("verify", project)));
  const argv = pi.tools.get("ready_argv");
  const evidence = parse(await argv.execute("accept", {
    action: "acceptance", version: 1,
    argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_clean.py"],
    evidence_paths: ["tests/test_clean.py"], production_entrypoint: "app.py", dependency_paths: ["config.json"],
    authoritative_readback_path: "readback.txt",
  }, null, null, context("verify", project)));
  assert.equal(evidence.status, "PASSED");
  const admitted = parse(await guard.execute("admit", { action: "admit", execution_id: verify.execution_id, verdict: "VERIFIED" }, null, null, context("verify", project)));
  assert.equal(admitted.phase, "VERIFY_VERIFIED_ADMITTED");

  const sourceWrite = await pi.emit("tool_call", { toolCallId: "source-write", toolName: "write", input: { path: "app.py", content: "def value(): return 2\n" } }, context("verify", project));
  assert.equal(sourceWrite.block, true);
  assert.match(sourceWrite.reason, /read-only except/);

  const ticketEdit = await pi.emit("tool_call", { toolCallId: "done-edit", toolName: "edit", input: { path: ticket, oldText: "Status: ready", newText: "Status: done" } }, context("verify", project));
  assert.equal(ticketEdit?.block, undefined);
  fs.writeFileSync(ticket, `Status: done\nProject-Root: ${project}\n`);
  await pi.emit("tool_result", { toolCallId: "done-edit", toolName: "edit", input: { path: ticket }, content: [{ type: "text", text: "done" }], isError: false }, context("verify", project));
  const closed = parse(await guard.execute("post", { action: "post_validate", execution_id: verify.execution_id }, null, null, context("verify", project)));
  assert.equal(closed.phase, "VERIFY_DONE");
});

test("acceptance runner cannot mutate its production or evidence inputs", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-readonly-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const { project, ticket } = makeProject(root);
  fs.writeFileSync(path.join(project, "config.json"), "{}\n");
  fs.writeFileSync(path.join(project, "app.py"), "from pathlib import Path\nCONFIG = Path(__file__).with_name('config.json').read_text()\ndef value():\n    return 1\n");
  fs.writeFileSync(path.join(project, "readback.txt"), "actual\n");
  fs.writeFileSync(path.join(project, "tests", "test_mutating.py"), [
    "import unittest",
    "from pathlib import Path",
    "from app import value",
    "class T(unittest.TestCase):",
    "    def test_mutates_source(self):",
    "        self.assertEqual(value(), 1)",
    "        Path('app.py').write_text('def value():\\n    return 2\\n')",
    "",
  ].join("\n"));
  const pi = mockPi();
  installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => fixtureBinding(projectRoot, ticketPath),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  await armVerify(pi, "verify", project);
  const verifyGuard = pi.tools.get("ready_verify_guard");
  await verifyGuard.execute("begin", { action: "begin", ticket_path: ticket, project_root: project }, null, null, context("verify", project));
  const argv = pi.tools.get("ready_argv");
  await assert.rejects(
    argv.execute("accept", {
      action: "acceptance", version: 1,
      argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_mutating.py"],
      evidence_paths: ["tests/test_mutating.py"], production_entrypoint: "app.py", dependency_paths: ["config.json"],
      authoritative_readback_path: "readback.txt",
    }, null, null, context("verify", project)),
    /ACCEPTANCE_EVIDENCE_MUTATION/,
  );
});


test("direct canonical inspection can admit VERIFIED without inventing an acceptance test", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-inspection-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const { project, ticket } = makeProject(root);
  fs.writeFileSync(path.join(project, "app.py"), "VALUE = 1\n");
  const pi = mockPi();
  installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => fixtureBinding(projectRoot, ticketPath),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  await armVerify(pi, "verify", project);
  const guard = pi.tools.get("ready_verify_guard");
  const verify = parse(await guard.execute("begin", {
    action: "begin", ticket_path: ticket, project_root: project,
  }, null, null, context("verify", project)));

  const readGate = await pi.emit("tool_call", {
    toolCallId: "canonical-read", toolName: "read", input: { path: "app.py" },
  }, context("verify", project));
  await pi.emit("tool_result", {
    toolCallId: "canonical-read", toolName: "read", input: readGate.input,
    content: [{ type: "text", text: "VALUE = 1" }], isError: false,
  }, context("verify", project));

  const admitted = parse(await guard.execute("admit", {
    action: "admit", execution_id: verify.execution_id, verdict: "VERIFIED",
    production_entrypoint: "app.py", authoritative_readback_path: "app.py",
  }, null, null, context("verify", project)));
  assert.equal(admitted.phase, "VERIFY_VERIFIED_ADMITTED");
  assert.equal(admitted.zero_mock.inspection_provenance, 1);
});
