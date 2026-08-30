import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { installReadyRuntime } from "../src/omp-adapter.js";
import {
  assertAcceptanceEvidenceBinding,
  directTaint,
  environmentTaint,
  resolveAcceptanceRunner,
  scanFileGraph,
} from "../src/no-mock-policy.js";

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
  const invalidKindParams = {
    action: "acceptance", version: 1,
    argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_bad.py"],
    evidence_paths: ["tests/test_bad.py"], production_entrypoint: "app.py", dependency_paths: ["config.json"],
    authoritative_readback_path: "config.json",
  };
  await assert.rejects(
    argv.execute("accept-missing-kind", invalidKindParams, null, null, context("main", project)),
    /requires provenance_kind to be exactly one of/,
  );
  await assert.rejects(
    argv.execute("accept-unknown-kind", { ...invalidKindParams, provenance_kind: "LOCAL_FILE" }, null, null, context("main", project)),
    /requires provenance_kind to be exactly one of/,
  );
  await assert.rejects(
    argv.execute("accept", {
      action: "acceptance", version: 1, provenance_kind: "LOCAL_PATH",
      argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_bad.py"],
      evidence_paths: ["tests/test_bad.py"], production_entrypoint: "app.py", dependency_paths: ["config.json"],
      authoritative_readback_path: "config.json",
    }, null, null, context("main", project)),
    /mock-tainted or unproven evidence/,
  );
});

test("read-only observation cannot substitute for clean acceptance provenance at COMPLETE", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-empty-acceptance-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const { project, ticket } = makeProject(root);
  const app = path.join(project, "app.py");
  fs.writeFileSync(app, "def value():\n    return 1\n");

  const pi = mockPi();
  const runtime = installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => fixtureBinding(projectRoot, ticketPath),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  await armImplement(pi, "main", project);
  const guard = pi.tools.get("ready_guard");
  const begun = parse(await guard.execute("begin", {
    action: "begin_direct", ticket_path: ticket, project_root: project,
  }, null, null, context("main", project)));

  const readGate = await pi.emit("tool_call", {
    toolCallId: "current-read", toolName: "read", input: { path: "app.py" },
  }, context("main", project));
  await pi.emit("tool_result", {
    toolCallId: "current-read",
    toolName: "read",
    input: readGate.input,
    content: [{ type: "text", text: "def value():\n    return 1" }],
    isError: false,
  }, context("main", project));

  const observed = runtime.lifecycle.status(begun.execution_id);
  assert.equal(observed.zero_mock.observed_evidence[fs.realpathSync(app)].mutation_revision, 0);
  assert.deepEqual(observed.zero_mock.acceptance_provenance, []);
  await assert.rejects(
    guard.execute("complete", {
      action: "complete", execution_id: begun.execution_id,
    }, null, null, context("main", project)),
    /Zero-Mock Delivery blocks COMPLETE because clean Zero-Mock acceptance provenance is required/,
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
    action: "acceptance", version: 1, provenance_kind: "LOCAL_SQLITE",
    argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_real_db.py"],
    evidence_paths: ["tests/test_real_db.py"], production_entrypoint: "app.py", dependency_paths: ["schema.sql"],
    authoritative_readback_path: "actual.db",
  }, null, null, context("main", project)));
  assert.equal(accepted.status, "PASSED");
  assert.equal(accepted.mock_taint, false);
  assert.equal(accepted.provenance_kind, "LOCAL_SQLITE");
  const completed = parse(await guard.execute("complete", { action: "complete", execution_id: begun.execution_id }, null, null, context("main", project)));
  assert.equal(completed.phase, "COMPLETE");
  assert.equal(runtime.lifecycle.status(begun.execution_id).zero_mock.acceptance_provenance[0].authoritative_readback.available, true);
  const sqliteProvenance = runtime.lifecycle.status(begun.execution_id).zero_mock.acceptance_provenance[0];
  assert.equal(sqliteProvenance.provenance_kind, "LOCAL_SQLITE");
  assert.equal(sqliteProvenance.fingerprint.payload.provenance_kind, "LOCAL_SQLITE");
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
    action: "acceptance", version: 1, provenance_kind: "LOCAL_PATH",
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
    action: "acceptance", version: 1, provenance_kind: "LOCAL_PATH",
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
    action: "acceptance", version: 1, provenance_kind: "LOCAL_PATH",
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

test("stale verifier acceptance rejects VERIFIED but still permits INCONCLUSIVE without changing Ticket status", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-verify-stale-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const { project, ticket } = makeProject(root);
  fs.writeFileSync(path.join(project, "app.py"), "from pathlib import Path\nCONFIG = Path(__file__).with_name('config.json').read_text()\nREADBACK = Path(__file__).with_name('readback.txt')\ndef value():\n    return 1\n");
  fs.writeFileSync(path.join(project, "config.json"), "{}\n");
  fs.writeFileSync(path.join(project, "readback.txt"), "real\n");
  fs.writeFileSync(path.join(project, "tests", "test_clean.py"), "import unittest\nfrom app import value\nclass T(unittest.TestCase):\n    def test_value(self): self.assertEqual(value(), 1)\n");

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
  const argv = pi.tools.get("ready_argv");
  const evidence = parse(await argv.execute("accept", {
    action: "acceptance", version: 1, provenance_kind: "LOCAL_PATH",
    argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_clean.py"],
    evidence_paths: ["tests/test_clean.py"], production_entrypoint: "app.py",
    dependency_paths: ["config.json"], authoritative_readback_path: "readback.txt",
  }, null, null, context("verify", project)));
  assert.equal(evidence.status, "PASSED");

  fs.writeFileSync(path.join(project, "app.py"), "def value():\n    return 2\n");

  await assert.rejects(
    guard.execute("admit-stale", {
      action: "admit", execution_id: verify.execution_id, verdict: "VERIFIED",
    }, null, null, context("verify", project)),
    /EVIDENCE_STALE/,
  );
  const terminal = parse(await guard.execute("admit-inconclusive", {
    action: "admit", execution_id: verify.execution_id, verdict: "INCONCLUSIVE",
  }, null, null, context("verify", project)));
  assert.equal(terminal.phase, "VERIFY_TERMINAL");
  assert.match(fs.readFileSync(ticket, "utf8"), /^Status: ready$/m);
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
      action: "acceptance", version: 1, provenance_kind: "LOCAL_PATH",
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
  const runtime = installReadyRuntime(pi, {
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
  const runner = runtime.lifecycle.status(verify.execution_id).zero_mock.inspection_provenance[0].fingerprint.payload.runner;
  assert.deepEqual(runner, {
    command_argv: [],
    package_json: null,
    package_script: null,
    resolved_argv: [],
    runner: "direct-inspection",
  });
});

test("stale provenance fingerprint: out-of-band mutation of production, evidence test, dependency, or readback rejects complete", async t => {
  await t.test("out-of-band mutation of production entrypoint rejects complete", async t => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-stale-prod-"));
    t.after(() => fs.rmSync(root, { recursive: true, force: true }));
    const { project, ticket } = makeProject(root);
    fs.writeFileSync(path.join(project, "app.py"), [
      "from pathlib import Path",
      "CONFIG = Path(__file__).with_name('config.json').read_text()",
      "def run():",
      "    Path('readback.txt').write_text('clean-output\\n')",
      "    return 1",
      "",
    ].join("\n"));
    fs.writeFileSync(path.join(project, "config.json"), "{\"mode\": \"real\"}\n");
    fs.writeFileSync(path.join(project, "readback.txt"), "clean-output\n");
    fs.writeFileSync(path.join(project, "tests", "test_clean.py"), [
      "import unittest",
      "from app import run",
      "class T(unittest.TestCase):",
      "    def test_run(self):",
      "        self.assertEqual(run(), 1)",
      "",
    ].join("\n"));

    const pi = mockPi();
    installReadyRuntime(pi, {
      dataRoot: path.join(root, "state"),
      bindAuthority: async ({ projectRoot, ticketPath }) => fixtureBinding(projectRoot, ticketPath),
      checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
    });
    await armImplement(pi, "main", project);
    const guard = pi.tools.get("ready_guard");
    const begun = parse(await guard.execute("begin", { action: "begin_direct", ticket_path: ticket, project_root: project }, null, null, context("main", project)));
    const argv = pi.tools.get("ready_argv");
    const accepted = parse(await argv.execute("accept", {
      action: "acceptance", version: 1, provenance_kind: "LOCAL_PATH",
      argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_clean.py"],
      evidence_paths: ["tests/test_clean.py"],
      production_entrypoint: "app.py",
      dependency_paths: ["config.json"],
      authoritative_readback_path: "readback.txt",
    }, null, null, context("main", project)));
    assert.equal(accepted.status, "PASSED");

    fs.writeFileSync(path.join(project, "app.py"), "def run():\n    return 2\n");

    await assert.rejects(
      guard.execute("complete", { action: "complete", execution_id: begun.execution_id }, null, null, context("main", project)),
      /stale|fingerprint|changed/i,
      "expected complete to reject due to stale production entrypoint",
    );
  });

  await t.test("out-of-band mutation of evidence test rejects complete", async t => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-stale-evidence-"));
    t.after(() => fs.rmSync(root, { recursive: true, force: true }));
    const { project, ticket } = makeProject(root);
    fs.writeFileSync(path.join(project, "app.py"), [
      "from pathlib import Path",
      "CONFIG = Path(__file__).with_name('config.json').read_text()",
      "def run():",
      "    Path('readback.txt').write_text('clean-output\\n')",
      "    return 1",
      "",
    ].join("\n"));
    fs.writeFileSync(path.join(project, "config.json"), "{\"mode\": \"real\"}\n");
    fs.writeFileSync(path.join(project, "readback.txt"), "clean-output\n");
    fs.writeFileSync(path.join(project, "tests", "test_clean.py"), [
      "import unittest",
      "from app import run",
      "class T(unittest.TestCase):",
      "    def test_run(self):",
      "        self.assertEqual(run(), 1)",
      "",
    ].join("\n"));

    const pi = mockPi();
    installReadyRuntime(pi, {
      dataRoot: path.join(root, "state"),
      bindAuthority: async ({ projectRoot, ticketPath }) => fixtureBinding(projectRoot, ticketPath),
      checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
    });
    await armImplement(pi, "main", project);
    const guard = pi.tools.get("ready_guard");
    const begun = parse(await guard.execute("begin", { action: "begin_direct", ticket_path: ticket, project_root: project }, null, null, context("main", project)));
    const argv = pi.tools.get("ready_argv");
    const accepted = parse(await argv.execute("accept", {
      action: "acceptance", version: 1, provenance_kind: "LOCAL_PATH",
      argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_clean.py"],
      evidence_paths: ["tests/test_clean.py"],
      production_entrypoint: "app.py",
      dependency_paths: ["config.json"],
      authoritative_readback_path: "readback.txt",
    }, null, null, context("main", project)));
    assert.equal(accepted.status, "PASSED");

    fs.writeFileSync(path.join(project, "tests", "test_clean.py"), "import unittest\n# tampered\nclass T(unittest.TestCase):\n    def test_run(self): self.assertEqual(1, 1)\n");

    await assert.rejects(
      guard.execute("complete", { action: "complete", execution_id: begun.execution_id }, null, null, context("main", project)),
      /stale|fingerprint|changed/i,
      "expected complete to reject due to stale evidence test",
    );
  });

  await t.test("out-of-band mutation of dependency config rejects complete", async t => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-stale-dep-"));
    t.after(() => fs.rmSync(root, { recursive: true, force: true }));
    const { project, ticket } = makeProject(root);
    fs.writeFileSync(path.join(project, "app.py"), [
      "from pathlib import Path",
      "CONFIG = Path(__file__).with_name('config.json').read_text()",
      "def run():",
      "    Path('readback.txt').write_text('clean-output\\n')",
      "    return 1",
      "",
    ].join("\n"));
    fs.writeFileSync(path.join(project, "config.json"), "{\"mode\": \"real\"}\n");
    fs.writeFileSync(path.join(project, "readback.txt"), "clean-output\n");
    fs.writeFileSync(path.join(project, "tests", "test_clean.py"), [
      "import unittest",
      "from app import run",
      "class T(unittest.TestCase):",
      "    def test_run(self):",
      "        self.assertEqual(run(), 1)",
      "",
    ].join("\n"));

    const pi = mockPi();
    installReadyRuntime(pi, {
      dataRoot: path.join(root, "state"),
      bindAuthority: async ({ projectRoot, ticketPath }) => fixtureBinding(projectRoot, ticketPath),
      checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
    });
    await armImplement(pi, "main", project);
    const guard = pi.tools.get("ready_guard");
    const begun = parse(await guard.execute("begin", { action: "begin_direct", ticket_path: ticket, project_root: project }, null, null, context("main", project)));
    const argv = pi.tools.get("ready_argv");
    const accepted = parse(await argv.execute("accept", {
      action: "acceptance", version: 1, provenance_kind: "LOCAL_PATH",
      argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_clean.py"],
      evidence_paths: ["tests/test_clean.py"],
      production_entrypoint: "app.py",
      dependency_paths: ["config.json"],
      authoritative_readback_path: "readback.txt",
    }, null, null, context("main", project)));
    assert.equal(accepted.status, "PASSED");

    fs.writeFileSync(path.join(project, "config.json"), "{\"tampered\": true}\n");

    await assert.rejects(
      guard.execute("complete", { action: "complete", execution_id: begun.execution_id }, null, null, context("main", project)),
      /stale|fingerprint|changed/i,
      "expected complete to reject due to stale dependency config",
    );
  });

  await t.test("out-of-band mutation of authoritative readback rejects complete", async t => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-stale-readback-"));
    t.after(() => fs.rmSync(root, { recursive: true, force: true }));
    const { project, ticket } = makeProject(root);
    fs.writeFileSync(path.join(project, "app.py"), [
      "from pathlib import Path",
      "CONFIG = Path(__file__).with_name('config.json').read_text()",
      "def run():",
      "    Path('readback.txt').write_text('clean-output\\n')",
      "    return 1",
      "",
    ].join("\n"));
    fs.writeFileSync(path.join(project, "config.json"), "{\"mode\": \"real\"}\n");
    fs.writeFileSync(path.join(project, "readback.txt"), "clean-output\n");
    fs.writeFileSync(path.join(project, "tests", "test_clean.py"), [
      "import unittest",
      "from app import run",
      "class T(unittest.TestCase):",
      "    def test_run(self):",
      "        self.assertEqual(run(), 1)",
      "",
    ].join("\n"));

    const pi = mockPi();
    installReadyRuntime(pi, {
      dataRoot: path.join(root, "state"),
      bindAuthority: async ({ projectRoot, ticketPath }) => fixtureBinding(projectRoot, ticketPath),
      checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
    });
    await armImplement(pi, "main", project);
    const guard = pi.tools.get("ready_guard");
    const begun = parse(await guard.execute("begin", { action: "begin_direct", ticket_path: ticket, project_root: project }, null, null, context("main", project)));
    const argv = pi.tools.get("ready_argv");
    const accepted = parse(await argv.execute("accept", {
      action: "acceptance", version: 1, provenance_kind: "LOCAL_PATH",
      argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_clean.py"],
      evidence_paths: ["tests/test_clean.py"],
      production_entrypoint: "app.py",
      dependency_paths: ["config.json"],
      authoritative_readback_path: "readback.txt",
    }, null, null, context("main", project)));
    assert.equal(accepted.status, "PASSED");

    fs.writeFileSync(path.join(project, "readback.txt"), "tampered-output\n");

    await assert.rejects(
      guard.execute("complete", { action: "complete", execution_id: begun.execution_id }, null, null, context("main", project)),
      /stale|fingerprint|changed/i,
      "expected complete to reject due to stale authoritative readback",
    );
  });
});


test("stale closure path-set: adding local import and new file to evidence closure after PASS rejects complete", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-closure-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const { project, ticket } = makeProject(root);
  fs.writeFileSync(path.join(project, "app.py"), [
    "from pathlib import Path",
    "CONFIG = Path(__file__).with_name('config.json').read_text()",
    "def run():",
    "    Path('readback.txt').write_text('clean-output\\n')",
    "    return 1",
    "",
  ].join("\n"));
  fs.writeFileSync(path.join(project, "config.json"), "{\"mode\": \"real\"}\n");
  fs.writeFileSync(path.join(project, "readback.txt"), "clean-output\n");
  fs.writeFileSync(path.join(project, "tests", "test_clean.py"), [
    "import unittest",
    "from app import run",
    "class T(unittest.TestCase):",
    "    def test_run(self):",
    "        self.assertEqual(run(), 1)",
    "",
  ].join("\n"));

  const pi = mockPi();
  installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => fixtureBinding(projectRoot, ticketPath),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  await armImplement(pi, "main", project);
  const guard = pi.tools.get("ready_guard");
  const begun = parse(await guard.execute("begin", { action: "begin_direct", ticket_path: ticket, project_root: project }, null, null, context("main", project)));
  const argv = pi.tools.get("ready_argv");
  const accepted = parse(await argv.execute("accept", {
    action: "acceptance", version: 1, provenance_kind: "LOCAL_PATH",
    argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_clean.py"],
    evidence_paths: ["tests/test_clean.py"],
    production_entrypoint: "app.py",
    dependency_paths: ["config.json"],
    authoritative_readback_path: "readback.txt",
  }, null, null, context("main", project)));
  assert.equal(accepted.status, "PASSED");

  fs.writeFileSync(path.join(project, "tests", "helper.py"), "def extra():\n    return 1\n");
  fs.writeFileSync(path.join(project, "tests", "test_clean.py"), [
    "import unittest",
    "from app import run",
    "from tests.helper import extra",
    "class T(unittest.TestCase):",
    "    def test_run(self):",
    "        self.assertEqual(run() + extra(), 2)",
    "",
  ].join("\n"));

  await assert.rejects(
    guard.execute("complete", { action: "complete", execution_id: begun.execution_id }, null, null, context("main", project)),
    /stale|fingerprint|closure|path-set|changed/i,
  );
});

test("basename string attribution bypass: comments or unrelated strings cannot prove production, dependency, or readback", async t => {
  await t.test("production entrypoint mentioned only in comments is rejected as PRODUCTION_PATH_UNPROVEN", async t => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-basename-prod-"));
    t.after(() => fs.rmSync(root, { recursive: true, force: true }));
    const { project, ticket } = makeProject(root);
    fs.writeFileSync(path.join(project, "app.py"), [
      "from pathlib import Path",
      "CONFIG = Path(__file__).with_name('config.json').read_text()",
      "def run():",
      "    Path('readback.txt').write_text('clean-output\\n')",
      "    return 1",
      "",
    ].join("\n"));
    fs.writeFileSync(path.join(project, "config.json"), "{\"mode\": \"real\"}\n");
    fs.writeFileSync(path.join(project, "readback.txt"), "clean-output\n");

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

    // Production entrypoint only mentioned in a comment, not imported/executed
    fs.writeFileSync(path.join(project, "tests", "test_fake_prod.py"), [
      "import unittest",
      "# Note: app.py is mentioned in this comment only",
      "class T(unittest.TestCase):",
      "    def test_pure(self):",
      "        self.assertEqual(1, 1)",
      "",
    ].join("\n"));
    await assert.rejects(
      argv.execute("accept-prod", {
        action: "acceptance", version: 1, provenance_kind: "LOCAL_PATH",
        argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_fake_prod.py"],
        evidence_paths: ["tests/test_fake_prod.py"],
        production_entrypoint: "app.py",
        dependency_paths: ["config.json"],
        authoritative_readback_path: "readback.txt",
      }, null, null, context("main", project)),
      /PRODUCTION_PATH_UNPROVEN|unproven/i,
    );
  });

  await t.test("dependency path mentioned only in comments is rejected as DEPENDENCY_PATH_UNPROVEN", async t => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-basename-dep-"));
    t.after(() => fs.rmSync(root, { recursive: true, force: true }));
    const { project, ticket } = makeProject(root);
    fs.writeFileSync(path.join(project, "app.py"), [
      "from pathlib import Path",
      "def run():",
      "    Path('readback.txt').write_text('clean-output\\n')",
      "    return 1",
      "",
    ].join("\n"));
    fs.writeFileSync(path.join(project, "config.json"), "{\"mode\": \"unused\"}\n");
    fs.writeFileSync(path.join(project, "readback.txt"), "clean-output\n");

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

    // Dependency config only mentioned in a comment, never used
    fs.writeFileSync(path.join(project, "tests", "test_fake_dep.py"), [
      "import unittest",
      "from app import run",
      "# Note: config.json is mentioned in this comment only",
      "class T(unittest.TestCase):",
      "    def test_run(self):",
      "        self.assertEqual(run(), 1)",
      "",
    ].join("\n"));
    await assert.rejects(
      argv.execute("accept-dep", {
        action: "acceptance", version: 1, provenance_kind: "LOCAL_PATH",
        argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_fake_dep.py"],
        evidence_paths: ["tests/test_fake_dep.py"],
        production_entrypoint: "app.py",
        dependency_paths: ["config.json"],
        authoritative_readback_path: "readback.txt",
      }, null, null, context("main", project)),
      /DEPENDENCY_PATH_UNPROVEN|unproven/i,
    );
  });

  await t.test("unmodified preexisting readback mentioned only in comments fails acceptance", async t => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-basename-readback-"));
    t.after(() => fs.rmSync(root, { recursive: true, force: true }));
    const { project, ticket } = makeProject(root);
    fs.writeFileSync(path.join(project, "app.py"), [
      "from pathlib import Path",
      "CONFIG = Path(__file__).with_name('config.json').read_text()",
      "def run(): return 1",
      "",
    ].join("\n"));
    fs.writeFileSync(path.join(project, "config.json"), "{\"mode\": \"real\"}\n");
    fs.writeFileSync(path.join(project, "readback.txt"), "preexisting-unchanged\n");

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

    // Readback path only mentioned in a comment, never written or modified
    fs.writeFileSync(path.join(project, "tests", "test_fake_readback.py"), [
      "import unittest",
      "from app import run",
      "# Note: readback.txt is mentioned in this comment; file is untouched",
      "class T(unittest.TestCase):",
      "    def test_run(self):",
      "        self.assertEqual(run(), 1)",
      "",
    ].join("\n"));
    const readbackResult = parse(await argv.execute("accept-readback", {
      action: "acceptance", version: 1, provenance_kind: "LOCAL_PATH",
      argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_fake_readback.py"],
      evidence_paths: ["tests/test_fake_readback.py"],
      production_entrypoint: "app.py",
      dependency_paths: ["config.json"],
      authoritative_readback_path: "readback.txt",
    }, null, null, context("main", project)));
    assert.notEqual(readbackResult.status, "PASSED");
  });
});


test("structural import scanning: Python from pkg import helper discovers submodule mock taint", t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-py-submodule-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  fs.mkdirSync(path.join(root, "pkg"), { recursive: true });
  fs.writeFileSync(path.join(root, "pkg", "__init__.py"), "# package init\n");
  fs.writeFileSync(path.join(root, "pkg", "helper.py"), "from unittest.mock import patch\n\ndef mock_fn():\n    return patch('target')\n");
  fs.writeFileSync(path.join(root, "test_submodule.py"), "from pkg import helper\n\ndef test_feature():\n    helper.mock_fn()\n");

  const report = scanFileGraph(root, [path.join(root, "test_submodule.py")]);
  assert.equal(report.mock_taint, true);
  assert.ok(
    report.violations.some(item => item.path.endsWith(path.join("pkg", "helper.py")) && item.code === "PY_UNITTEST_MOCK"),
    "expected mock taint violation on pkg/helper.py",
  );
});

test("structural JS mock authority follows global, destructuring, assignment, and alias flows", async t => {
  const assertTainted = (code, message) => {
    assert.ok(directTaint(code).length > 0, message);
  };
  const assertClean = (code, message) => {
    assert.deepEqual(directTaint(code), [], message);
  };

  await t.test("static object and class definition names are not runtime global reads", () => {
    const cases = [
      "const obj = { vi() { return 1; } };\n",
      "class C { jest() { return 1; } }\n",
      "const obj = { get sinon() { return 1; } };\n",
      "const obj = { vi: () => 1, jest: 1, sinon: value };\n",
      "class C { vi = () => 1; }\n",
      "const obj = { async vi() { return 1; }, *jest() { yield 1; }, set sinon(value) {} };\n",
      "class C { static async vi() { return 1; } static *jest() { yield 1; } static get sinon() { return 1; } }\n",
    ];
    for (const code of cases) assertClean(code, `definition name must remain clean: ${code}`);
  });

  await t.test("method bodies and computed keys retain runtime mock authority", () => {
    const cases = [
      "function f() { vi.fn(); }\n",
      "const obj = { vi() { return globalThis.vi.fn(); } };\n",
      "const obj = { [globalThis.vi]() { return 1; } };\n",
    ];
    for (const code of cases) assertTainted(code, `runtime mock authority must taint: ${code}`);
  });

  await t.test("globalThis mock object alias", () => {
    assertTainted(
      "const potato = globalThis.vi;\npotato.fn();\n",
      "globalThis.vi alias must taint",
    );
  });

  await t.test("destructured global authority and alias-to-alias", () => {
    assertTainted(
      "const { vi: potato } = globalThis;\nconst second = potato;\nsecond.spyOn(target, 'method');\n",
      "destructured global authority must propagate through aliases",
    );
  });

  await t.test("static computed destructuring follows mock authority", () => {
    const cases = [
      "const { ['vi']: potato } = globalThis;\npotato.fn();\n",
      "const { ['vi']: potato = fallback } = globalThis;\nconst second = potato;\nsecond.spyOn(target, 'method');\n",
      "const { ['jest']: potato } = globalThis;\npotato.fn();\n",
      "const { ['sinon']: potato } = globalThis;\npotato.stub(service, 'call');\n",
    ];
    for (const code of cases) assertTainted(code, `static computed mock property must taint: ${code}`);
    assertClean(
      "const { ['location']: potato } = globalThis;\npotato.assign('/safe');\n",
      "an unrelated static computed global property must remain clean",
    );
  });

  await t.test("dynamic computed destructuring fails closed only from tracked authority", () => {
    assertTainted(
      "const key = getMockKey();\nconst { [key]: potato } = globalThis;\npotato.fn();\n",
      "an unsupported dynamic key from a global host must not bypass mock admission",
    );
    assertClean(
      "const key = getPropertyKey();\nconst { [key]: potato } = localObject;\npotato.fn();\n",
      "a dynamic property from an unrelated source must not gain mock taint",
    );
  });

  await t.test("computed destructuring targets retain lexical scope", () => {
    assertClean(
      "function localOnly() { const { ['value']: vi } = localObject; return vi.fn(); }\n",
      "a computed destructuring target must shadow the bare mock-global name in its own scope",
    );
    assertTainted(
      "function localOnly() { const { ['value']: vi } = localObject; return vi.fn(); }\nfunction sibling() { return vi.fn(); }\n",
      "a computed destructuring target must not shadow a mock-global name in a sibling scope",
    );
  });

  await t.test("destructured member-function alias", () => {
    assertTainted(
      "const { fn: fakeFn } = globalThis.vi;\nfakeFn();\n",
      "mock member-function aliases must taint",
    );
  });

  await t.test("simple assignment from static window member", () => {
    assertTainted(
      "let potato;\npotato = window.jest;\npotato.mock('./dependency');\n",
      "simple assignment from window.jest must taint",
    );
  });

  await t.test("static bracket member and Sinon global alias", () => {
    assertTainted(
      "const potato = self['sinon'];\nconst second = potato;\nsecond.stub(service, 'call');\n",
      "static bracket Sinon authority must propagate through aliases",
    );
  });

  await t.test("direct global authority in a wrapper body", () => {
    assertTainted(
      "const potato = vi;\nexport function makeFake() { return potato.fn(); }\n",
      "wrapper body use of a tracked alias must taint its source file",
    );
  });

  await t.test("member function alias follows an object alias", () => {
    assertTainted(
      "const potato = globalThis.vi;\nconst second = potato;\nconst fakeFn = second.fn;\nfakeFn();\n",
      "member-function aliases must propagate from tracked object aliases",
    );
  });

  await t.test("destructured require aliases and namespace invocations remain tainted", () => {
    const cases = [
      "const { vi: potato } = require('vitest');\npotato.fn();\n",
      "const { jest: myJest } = require('@jest/globals');\nmyJest.fn();\n",
      "const { fn, spyOn } = require('vitest');\nconst mock = fn();\n",
      "const vitest = require('vitest');\nvitest.vi.fn();\n",
      "import * as vitest from 'vitest';\nvitest.vi.fn();\n",
    ];
    for (const code of cases) assertTainted(code, `expected structural taint for ${code}`);
  });

  await t.test("local wrapper import closure reports the parent-to-wrapper import chain", () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-js-global-wrapper-"));
    t.after(() => fs.rmSync(root, { recursive: true, force: true }));
    const parent = path.join(root, "parent.test.js");
    const wrapper = path.join(root, "mock-wrapper.js");
    fs.writeFileSync(wrapper, [
      "const potato = globalThis.vi;",
      "export function makeFake() { return potato.fn(); }",
      "",
    ].join("\n"));
    fs.writeFileSync(parent, "import { makeFake } from './mock-wrapper.js';\nmakeFake();\n");

    const report = scanFileGraph(root, [parent]);
    assert.equal(report.mock_taint, true);
    assert.ok(
      report.violations.some(item => item.path === wrapper
        && item.import_chain?.length === 2
        && item.import_chain[0] === parent
        && item.import_chain[1] === wrapper),
      "wrapper taint must retain the parent-to-wrapper import chain",
    );
  });

  await t.test("mock-global shadowing follows lexical scope ancestry", () => {
    assertTainted(
      "function clean(vi) { return vi.fn(); }\nexport function test() { return vi.fn(); }\n",
      "a parameter in one function must not hide the real global in a sibling function",
    );
    assertClean(
      "function clean(vi) { function nested() { return vi.fn(); } return nested(); }\nconst alsoClean = function (jest) { return () => jest.fn(); };\n",
      "nested functions and function expressions must inherit their enclosing parameter shadows",
    );
    assertClean(
      "function first(vi) { return vi.fn(); }\nfunction second(jest) { return jest.fn(); }\nconst third = (sinon) => sinon.stub();\n",
      "independent sibling-local mock-global names must remain clean in their own scopes",
    );
  });

  await t.test("block and module bindings have their JavaScript lexical reach", () => {
    assertTainted(
      "{ let vi = local; vi.fn(); }\nvi.fn();\n",
      "a block let binding must not hide a global use outside its block",
    );
    assertClean(
      "{ let vi = local; vi.fn(); }\n",
      "a block let binding must hide the bare name inside its block",
    );
    const moduleControls = [
      "const vi = local;\nvi.fn();\n",
      "vi.fn();\nconst vi = local;\n",
      "import { something as vi } from './local.js';\nvi.fn();\n",
    ];
    for (const code of moduleControls) assertClean(code, `module binding must shadow throughout the module: ${code}`);
  });

  await t.test("destructured parameters shadow bare names but not explicit global hosts", () => {
    assertClean(
      "function clean({ local: vi }, [jest], { sinon }) { vi.fn(); jest.fn(); sinon.stub(); }\n",
      "destructured function parameters must establish local bindings",
    );
    const explicitGlobals = [
      "function clean(vi) { return globalThis.vi.fn(); }\n",
      "const vi = local; window.jest.fn();\n",
      "{ let sinon = local; self.sinon.stub(); }\n",
    ];
    for (const code of explicitGlobals) assertTainted(code, `explicit global host must remain tainted: ${code}`);
  });

  await t.test("unrelated names and members remain clean", () => {
    const controls = [
      "function use(vi) { return vi.fn(); }\n",
      "const value = 1;\nconst object = { vi: value };\n",
      "const object = getObject();\nobject.fn();\n",
    ];
    for (const code of controls) {
      assert.deepEqual(directTaint(code), [], `unexpected structural taint for ${code}`);
    }
  });
});


test("acceptance binds invoked test roots exactly before direct or package execution", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-binding-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const { project, ticket } = makeProject(root);
  fs.writeFileSync(path.join(project, "app.py"), "VALUE = 1\n");
  fs.writeFileSync(path.join(project, "config.json"), "{}\n");
  fs.writeFileSync(path.join(project, "tests", "test_green.py"), [
    "import unittest",
    "from pathlib import Path",
    "class GreenTest(unittest.TestCase):",
    "    def test_green(self):",
    "        Path('green-test-executed').write_text('executed')",
    "        self.assertTrue(True)",
    "",
  ].join("\n"));
  fs.writeFileSync(path.join(project, "tests", "test_claimed.py"), [
    "import unittest",
    "from app import VALUE",
    "class ClaimedTest(unittest.TestCase):",
    "    def test_claim(self):",
    "        self.assertEqual(VALUE, 1)",
    "",
  ].join("\n"));
  fs.writeFileSync(path.join(project, "package.json"), JSON.stringify({
    scripts: { acceptance: "python3 -m unittest discover -s tests -p" },
  }));

  const pi = mockPi();
  const runtime = installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => fixtureBinding(projectRoot, ticketPath),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  await armImplement(pi, "binding", project);
  const guard = pi.tools.get("ready_guard");
  const begun = parse(await guard.execute("begin", { action: "begin_direct", ticket_path: ticket, project_root: project }, null, null, context("binding", project)));
  const argv = pi.tools.get("ready_argv");
  const common = {
    action: "acceptance", version: 1, provenance_kind: "LOCAL_PATH",
    production_entrypoint: "app.py", dependency_paths: ["config.json"],
    authoritative_readback_path: "readback.txt",
  };

  await assert.rejects(
    argv.execute("direct-mismatch", {
      ...common,
      argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_green.py"],
      evidence_paths: ["tests/test_claimed.py"],
    }, null, null, context("binding", project)),
    /ACCEPTANCE_EVIDENCE_BINDING_MISMATCH/,
  );
  assert.equal(fs.existsSync(path.join(project, "green-test-executed")), false);

  await assert.rejects(
    argv.execute("extra-evidence", {
      ...common,
      argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_green.py"],
      evidence_paths: ["tests/test_green.py", "tests/test_claimed.py"],
    }, null, null, context("binding", project)),
    /ACCEPTANCE_EVIDENCE_BINDING_MISMATCH/,
  );

  await assert.rejects(
    argv.execute("package-mismatch", {
      ...common,
      argv: ["npm", "run", "acceptance", "--", "test_green.py"],
      evidence_paths: ["tests/test_claimed.py"],
    }, null, null, context("binding", project)),
    /ACCEPTANCE_EVIDENCE_BINDING_MISMATCH/,
  );
  assert.equal(fs.existsSync(path.join(project, "green-test-executed")), false);

  const resolved = resolveAcceptanceRunner(["npm", "run", "acceptance", "--", "test_green.py"], project);
  assert.deepEqual(resolved.command_argv, ["npm", "run", "acceptance", "--", "test_green.py"]);
  assert.deepEqual(resolved.resolved_argv, ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_green.py"]);
  assert.deepEqual(
    assertAcceptanceEvidenceBinding(project, resolved, ["tests/test_green.py"]),
    [fs.realpathSync(path.join(project, "tests", "test_green.py"))],
  );
  await assert.rejects(
    argv.execute("provider-mismatch", {
      ...common,
      provenance_kind: "EXTERNAL_HTTP_PROVIDER",
      argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_green.py"],
      evidence_paths: ["tests/test_claimed.py"],
    }, null, null, context("binding", project)),
    /ACCEPTANCE_EVIDENCE_BINDING_MISMATCH/,
  );
  assert.equal(fs.existsSync(path.join(project, "green-test-executed")), false);
  assert.deepEqual(runtime.lifecycle.status(begun.execution_id).zero_mock.acceptance_provenance, []);
});

test("package acceptance rejects adjacent lifecycle hooks before local or provider execution", async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-package-hooks-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const { project, ticket } = makeProject(root);
  fs.writeFileSync(path.join(project, "app.py"), "VALUE = 1\n");
  fs.writeFileSync(path.join(project, "config.json"), "{}\n");
  fs.writeFileSync(path.join(project, "tests", "test_claimed.py"), [
    "import unittest",
    "from pathlib import Path",
    "class ClaimedTest(unittest.TestCase):",
    "    def test_claim(self):",
    "        Path('runner-marker').write_text('ran')",
    "        Path('readback.txt').write_text('1')",
    "        self.assertTrue(True)",
    "",
  ].join("\n"));
  fs.writeFileSync(path.join(project, "package.json"), JSON.stringify({
    scripts: {
      acceptance: "python3 -m unittest discover -s tests -p",
      preacceptance: "python3 -c \"open('pre-hook-marker', 'w').write('ran')\"",
      postacceptance: "python3 -c \"open('post-hook-marker', 'w').write('ran')\"",
      unrelated: "python3 -c \"open('unrelated-marker', 'w').write('ran')\"",
    },
  }));

  for (const command of [
    ["npm", "run", "acceptance", "--", "test_claimed.py"],
    ["pnpm", "run", "acceptance", "--", "test_claimed.py"],
    ["yarn", "run", "acceptance", "test_claimed.py"],
  ]) {
    assert.throws(
      () => resolveAcceptanceRunner(command, project),
      /PACKAGE_ACCEPTANCE_LIFECYCLE_HOOK_UNSUPPORTED.*preacceptance/,
    );
  }

  const pi = mockPi();
  const runtime = installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => fixtureBinding(projectRoot, ticketPath),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  await armImplement(pi, "package-hooks", project);
  const guard = pi.tools.get("ready_guard");
  const begun = parse(await guard.execute("begin", { action: "begin_direct", ticket_path: ticket, project_root: project }, null, null, context("package-hooks", project)));
  const argv = pi.tools.get("ready_argv");
  const acceptance = {
    action: "acceptance", version: 1,
    argv: ["npm", "run", "acceptance", "--", "test_claimed.py"],
    evidence_paths: ["tests/test_claimed.py"], production_entrypoint: "app.py",
    dependency_paths: ["config.json"], authoritative_readback_path: "readback.txt",
  };
  await assert.rejects(
    argv.execute("local-hook", { ...acceptance, provenance_kind: "LOCAL_PATH" }, null, null, context("package-hooks", project)),
    /PACKAGE_ACCEPTANCE_LIFECYCLE_HOOK_UNSUPPORTED/,
  );
  await assert.rejects(
    argv.execute("provider-hook", { ...acceptance, provenance_kind: "EXTERNAL_HTTP_PROVIDER" }, null, null, context("package-hooks", project)),
    /PACKAGE_ACCEPTANCE_LIFECYCLE_HOOK_UNSUPPORTED/,
  );
  for (const marker of ["pre-hook-marker", "post-hook-marker", "runner-marker", "unrelated-marker"]) {
    assert.equal(fs.existsSync(path.join(project, marker)), false);
  }
  assert.deepEqual(runtime.lifecycle.status(begun.execution_id).zero_mock.acceptance_provenance, []);

  fs.writeFileSync(path.join(project, "package.json"), JSON.stringify({
    scripts: { acceptance: "python3 -m unittest discover -s tests -p", preacceptance: "" },
  }));
  assert.throws(
    () => resolveAcceptanceRunner(["npm", "run", "acceptance", "--", "test_claimed.py"], project),
    /PACKAGE_ACCEPTANCE_LIFECYCLE_HOOK_UNSUPPORTED.*preacceptance/,
  );
});

test("exact package-script acceptance preserves command and resolved runner identity", async t => {

  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-package-happy-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const { project, ticket } = makeProject(root);
  fs.writeFileSync(path.join(project, "app.py"), [
    "from pathlib import Path",
    "CONFIG = Path(__file__).with_name('config.json').read_text()",
    "VALUE = 1",
    "",
  ].join("\n"));
  fs.writeFileSync(path.join(project, "config.json"), "{}\n");
  fs.writeFileSync(path.join(project, "package.json"), JSON.stringify({
    scripts: {
      acceptance: "python3 -m unittest discover -s tests -p",
      unrelated: "python3 -c \"open('unrelated-marker', 'w').write('ran')\"",
    },
  }));
  fs.writeFileSync(path.join(project, "tests", "test_claimed.py"), [
    "import unittest",
    "from pathlib import Path",
    "from app import VALUE",
    "class ClaimedTest(unittest.TestCase):",
    "    def test_claim(self):",
    "        Path('readback.txt').write_text(str(VALUE))",
    "        self.assertEqual(VALUE, 1)",
    "",
  ].join("\n"));
  const pi = mockPi();
  const runtime = installReadyRuntime(pi, {
    dataRoot: path.join(root, "state"),
    bindAuthority: async ({ projectRoot, ticketPath }) => fixtureBinding(projectRoot, ticketPath),
    checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
  });
  await armImplement(pi, "package-happy", project);
  const guard = pi.tools.get("ready_guard");
  const begun = parse(await guard.execute("begin", { action: "begin_direct", ticket_path: ticket, project_root: project }, null, null, context("package-happy", project)));
  const accepted = parse(await pi.tools.get("ready_argv").execute("accept", {
    action: "acceptance", version: 1, provenance_kind: "LOCAL_PATH",
    argv: ["npm", "run", "acceptance", "--", "test_claimed.py"],
    evidence_paths: ["tests/test_claimed.py"], production_entrypoint: "app.py",
    dependency_paths: ["config.json"], authoritative_readback_path: "readback.txt",
  }, null, null, context("package-happy", project)));
  assert.equal(accepted.status, "PASSED");
  const runner = runtime.lifecycle.status(begun.execution_id).zero_mock.acceptance_provenance[0].fingerprint.payload.runner;
  assert.deepEqual(runner.command_argv, ["npm", "run", "acceptance", "--", "test_claimed.py"]);
  assert.deepEqual(runner.resolved_argv, ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_claimed.py"]);
  assert.equal(runner.package_script, "acceptance");
  assert.match(runner.package_json.sha256, /^[a-f0-9]{64}$/);
  fs.writeFileSync(path.join(project, "package.json"), JSON.stringify({
    scripts: {
      acceptance: "python3 -m unittest discover -s tests -p",
      postacceptance: "python3 -c \"open('post-hook-marker', 'w').write('ran')\"",
    },
  }));
  await assert.rejects(
    guard.execute("complete", { action: "complete", execution_id: begun.execution_id }, null, null, context("package-happy", project)),
    /EVIDENCE_STALE:.*PACKAGE_ACCEPTANCE_LIFECYCLE_HOOK_UNSUPPORTED.*postacceptance/,
  );
  assert.equal(fs.existsSync(path.join(project, "post-hook-marker")), false);
});

test("external provider provenance: unproven EXTERNAL_HTTP_PROVIDER blocks implementation COMPLETE and verifier VERIFIED", async t => {
  await t.test("unproven EXTERNAL_HTTP_PROVIDER blocks implementation COMPLETE", async t => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-external-provider-impl-"));
    t.after(() => fs.rmSync(root, { recursive: true, force: true }));
    const { project, ticket } = makeProject(root);
    fs.writeFileSync(path.join(project, "app.py"), [
      "from pathlib import Path",
      "CONFIG = Path(__file__).with_name('config.json').read_text()",
      "def call_provider():",
      "    Path('readback.txt').write_text('provider-output\\n')",
      "    return 1",
      "",
    ].join("\n"));
    fs.writeFileSync(path.join(project, "config.json"), "{\"provider_url\": \"https://api.example.com\"}\n");
    fs.writeFileSync(path.join(project, "readback.txt"), "provider-output\n");
    fs.writeFileSync(path.join(project, "tests", "test_provider.py"), [
      "import unittest",
      "from pathlib import Path",
      "from app import call_provider",
      "class ProviderTest(unittest.TestCase):",
      "    def test_call(self):",
      "        Path('provider-test-executed').write_text('executed')",
      "        self.assertEqual(call_provider(), 1)",
      "",
    ].join("\n"));

    const pi = mockPi();
    installReadyRuntime(pi, {
      dataRoot: path.join(root, "impl-state"),
      bindAuthority: async ({ projectRoot, ticketPath }) => fixtureBinding(projectRoot, ticketPath),
      checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
    });
    await armImplement(pi, "impl", project);
    const guard = pi.tools.get("ready_guard");
    const impl = parse(await guard.execute("begin", { action: "begin_direct", ticket_path: ticket, project_root: project }, null, null, context("impl", project)));
    const argv = pi.tools.get("ready_argv");

    const evidence = parse(await argv.execute("accept", {
      action: "acceptance", version: 1,
      argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_provider.py"],
      evidence_paths: ["tests/test_provider.py"],
      production_entrypoint: "app.py",
      dependency_paths: ["config.json"],
      authoritative_readback_path: "readback.txt",
      provenance_kind: "EXTERNAL_HTTP_PROVIDER",
    }, null, null, context("impl", project)));
    assert.equal(evidence.status, "INCONCLUSIVE");
    assert.equal(evidence.fingerprint, null);
    assert.equal(evidence.authoritative_readback.available, false);
    assert.equal(evidence.authoritative_readback.kind, "external_provider_execution_correlation_unsupported");
    assert.match(evidence.authoritative_readback.error, /external provider execution correlation is unsupported/);
    assert.equal(fs.existsSync(path.join(project, "provider-test-executed")), false);

    await assert.rejects(
      guard.execute("complete", { action: "complete", execution_id: impl.execution_id }, null, null, context("impl", project)),
      /provider|correlation|EXTERNAL_HTTP_PROVIDER|Zero-Mock/i,
    );
  });

  await t.test("unproven EXTERNAL_HTTP_PROVIDER blocks verifier VERIFIED", async t => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-zero-mock-external-provider-verify-"));
    t.after(() => fs.rmSync(root, { recursive: true, force: true }));
    const { project, ticket } = makeProject(root);
    fs.writeFileSync(path.join(project, "app.py"), [
      "from pathlib import Path",
      "CONFIG = Path(__file__).with_name('config.json').read_text()",
      "def call_provider():",
      "    Path('readback.txt').write_text('provider-output\\n')",
      "    return 1",
      "",
    ].join("\n"));
    fs.writeFileSync(path.join(project, "config.json"), "{\"provider_url\": \"https://api.example.com\"}\n");
    fs.writeFileSync(path.join(project, "readback.txt"), "provider-output\n");
    fs.writeFileSync(path.join(project, "tests", "test_provider.py"), [
      "import unittest",
      "from pathlib import Path",
      "from app import call_provider",
      "class ProviderTest(unittest.TestCase):",
      "    def test_call(self):",
      "        Path('provider-test-executed').write_text('executed')",
      "        self.assertEqual(call_provider(), 1)",
      "",
    ].join("\n"));

    const pi = mockPi();
    installReadyRuntime(pi, {
      dataRoot: path.join(root, "verify-state"),
      bindAuthority: async ({ projectRoot, ticketPath }) => fixtureBinding(projectRoot, ticketPath),
      checkAuthorityCurrentness: async () => ({ current: true, changed: [] }),
    });
    await armVerify(pi, "verify", project);
    const guard = pi.tools.get("ready_verify_guard");
    const verify = parse(await guard.execute("begin-v", { action: "begin", ticket_path: ticket, project_root: project }, null, null, context("verify", project)));
    const argv = pi.tools.get("ready_argv");

    const evidence = parse(await argv.execute("accept-v", {
      action: "acceptance", version: 1,
      argv: ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_provider.py"],
      evidence_paths: ["tests/test_provider.py"],
      production_entrypoint: "app.py",
      dependency_paths: ["config.json"],
      authoritative_readback_path: "readback.txt",
      provenance_kind: "EXTERNAL_HTTP_PROVIDER",
    }, null, null, context("verify", project)));
    assert.equal(evidence.status, "INCONCLUSIVE");
    assert.equal(evidence.fingerprint, null);
    assert.equal(evidence.authoritative_readback.kind, "external_provider_execution_correlation_unsupported");
    assert.equal(fs.existsSync(path.join(project, "provider-test-executed")), false);

    await assert.rejects(
      guard.execute("admit-v", { action: "admit", execution_id: verify.execution_id, verdict: "VERIFIED" }, null, null, context("verify", project)),
      /provider|correlation|EXTERNAL_HTTP_PROVIDER|Zero-Mock/i,
    );
    const terminal = parse(await guard.execute("admit-i", {
      action: "admit", execution_id: verify.execution_id, verdict: "INCONCLUSIVE",
    }, null, null, context("verify", project)));
    assert.equal(terminal.phase, "VERIFY_TERMINAL");
  });
});
