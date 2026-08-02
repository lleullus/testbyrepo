'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const NodePolicyGatePlugin = require('../plugins/node-policy-gate');

function put(root, relativePath, content) {
  const filePath = path.join(root, relativePath);
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, content);
}

function context(sessionID, worktree) {
  return {
    agent: 'build',
    directory: worktree,
    messageID: `message-${sessionID}`,
    sessionID,
    worktree
  };
}

test('OpenCode hook blocks ordinary mutation tools and writes only through current admission', async (t) => {
  const worktree = fs.mkdtempSync(path.join(os.tmpdir(), 'opencode-policy-gate-'));
  const project = path.join(worktree, 'project');
  t.after(() => fs.rmSync(worktree, { force: true, recursive: true }));
  put(project, 'package.json', JSON.stringify({ name: 'plugin-project', main: 'src/index.js' }));
  put(project, 'src/index.js', 'exports.createUser = (name) => ({ name });\n');
  const hooks = await NodePolicyGatePlugin({ directory: worktree, worktree });
  const request = 'Update user creation behavior. Keep startup unchanged. If creation fails, show an error message.';

  await hooks['chat.message'](
    { sessionID: 'session-pass' },
    { parts: [{ type: 'text', text: request }] }
  );

  for (const toolName of ['edit', 'write', 'apply_patch', 'bash', 'task', 'unknown_mutator']) {
    await assert.rejects(
      hooks['tool.execute.before']({ tool: toolName, sessionID: 'session-pass', callID: `call-${toolName}` }),
      /Node policy gate blocked tool/
    );
  }
  await hooks['tool.execute.before']({ tool: 'read', sessionID: 'session-pass', callID: 'call-read' });

  const admitted = JSON.parse(await hooks.tool.node_policy_admit.execute(
    { projectDirectory: 'project' },
    context('session-pass', worktree)
  ));
  assert.equal(admitted.verdict, 'PASS');

  const written = JSON.parse(await hooks.tool.node_policy_write.execute(
    { writes: [{ path: 'src/index.js', content: 'exports.createUser = (name) => ({ name: name.trim() });\n' }] },
    context('session-pass', worktree)
  ));
  assert.equal(written.allowed, true);
  assert.match(fs.readFileSync(path.join(project, 'src/index.js'), 'utf8'), /trim/);

  await assert.rejects(
    hooks['tool.execute.before']({ tool: 'functions.apply_patch', sessionID: 'session-pass', callID: 'call-namespaced' }),
    /Node policy gate blocked tool/
  );
});

test('OpenCode write tool remains fail-closed for an INCONCLUSIVE authoritative request', async (t) => {
  const worktree = fs.mkdtempSync(path.join(os.tmpdir(), 'opencode-policy-inconclusive-'));
  const project = path.join(worktree, 'project');
  t.after(() => fs.rmSync(worktree, { force: true, recursive: true }));
  put(project, 'package.json', JSON.stringify({ name: 'plugin-project', main: 'src/index.js' }));
  put(project, 'src/index.js', 'exports.value = true;\n');
  const hooks = await NodePolicyGatePlugin({ directory: worktree, worktree });
  const request = 'Update user behavior. Keep startup unchanged.';

  await hooks['chat.message'](
    { sessionID: 'session-denied' },
    { parts: [{ type: 'text', text: request }] }
  );
  const admitted = JSON.parse(await hooks.tool.node_policy_admit.execute(
    { projectDirectory: 'project' },
    context('session-denied', worktree)
  ));
  assert.equal(admitted.verdict, 'INCONCLUSIVE');
  const before = fs.readFileSync(path.join(project, 'src/index.js'), 'utf8');

  const denied = JSON.parse(await hooks.tool.node_policy_write.execute(
    { writes: [{ path: 'src/index.js', content: 'exports.value = false;\n' }] },
    context('session-denied', worktree)
  ));
  assert.equal(denied.allowed, false);
  assert.equal(denied.reason.code, 'admission-not-passed');
  assert.equal(fs.readFileSync(path.join(project, 'src/index.js'), 'utf8'), before);

  await hooks['chat.message'](
    { sessionID: 'session-denied' },
    { parts: [{ type: 'text', text: 'If the update fails, show an error message.' }] }
  );
  const clarified = JSON.parse(await hooks.tool.node_policy_admit.execute(
    { projectDirectory: 'project' },
    context('session-denied', worktree)
  ));
  assert.equal(clarified.verdict, 'PASS');
});

test('OpenCode tool allowlisting requires exact registered IDs', async (t) => {
  const worktree = fs.mkdtempSync(path.join(os.tmpdir(), 'opencode-policy-exact-tools-'));
  t.after(() => fs.rmSync(worktree, { force: true, recursive: true }));
  const hooks = await NodePolicyGatePlugin({ directory: worktree, worktree });

  for (const tool of ['node_policy_write', 'node_policy_admit', 'read']) {
    await assert.doesNotReject(hooks['tool.execute.before']({ tool, sessionID: 'exact', callID: `call-${tool}` }));
  }
  for (const tool of ['attacker/node_policy_write', 'attacker.node_policy_write', 'foo:node_policy_admit']) {
    await assert.rejects(
      hooks['tool.execute.before']({ tool, sessionID: 'exact', callID: `call-${tool}` }),
      /Node policy gate blocked tool/
    );
  }
});
