'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const { admitChange } = require('..');

function makeProject(files = {}) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-admission-'));
  for (const [relativePath, contents] of Object.entries(files)) {
    const filePath = path.join(directory, relativePath);
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, contents);
  }
  return directory;
}

function removeProject(directory) {
  fs.rmSync(directory, { force: true, recursive: true });
}

function snapshot(directory) {
  const entries = new Map();

  function visit(currentDirectory) {
    for (const entry of fs.readdirSync(currentDirectory, { withFileTypes: true })) {
      const absolutePath = path.join(currentDirectory, entry.name);
      const relativePath = path.relative(directory, absolutePath);
      if (entry.isSymbolicLink()) {
        entries.set(relativePath, { target: fs.readlinkSync(absolutePath), type: 'symlink' });
      } else if (entry.isDirectory()) {
        visit(absolutePath);
      } else if (entry.isFile()) {
        entries.set(relativePath, fs.readFileSync(absolutePath));
      }
    }
  }

  visit(directory);
  return entries;
}

function validProject() {
  return {
    'package.json': JSON.stringify({ name: 'fixture-project', main: 'src/index.ts' }),
    'tsconfig.json': JSON.stringify({ compilerOptions: { baseUrl: '.', rootDir: 'src' } }),
    'src/index.ts': "export { createUser } from './application/create-user';\n",
    'src/application/create-user.ts': "import { User } from '../domain/user';\nexport function createUser(name: string): User { return { name }; }\n",
    'src/application/read-user.ts': "import { User } from '../domain/user';\nexport function readUser(user: User): User { return user; }\n",
    'src/domain/user.ts': 'export interface User { name: string }\n'
  };
}

function singleBoundaryProject() {
  return {
    'package.json': JSON.stringify({ name: 'single-boundary-project', main: 'src/index.js' }),
    'src/index.js': 'exports.createUser = (name) => ({ name });\n'
  };
}

const REUSE_REQUEST = "Reuse the existing createUser function to create a normalized user name. Keep existing user reading unchanged. If a name is empty, show 'A name is required'.";
const NEW_FUNCTION_REQUEST = "Add a new function to create users from a name. Keep existing user reading unchanged. If a name is empty, show 'A name is required'.";
const FIRST_REVISION = "import { User } from '../domain/user';\nexport function createUser(name: string): User { return { name: name.trim() }; }\n";
const SECOND_REVISION = "import { User } from '../domain/user';\nexport function createUser(name: string): User { return { name: name.trim().toLowerCase() }; }\n";

function write(pathValue, content) {
  return { content, path: pathValue };
}

test('infers scope without caller input and rejects a proposed new shape when reuse exists', (t) => {
  const directory = makeProject(validProject());
  t.after(() => removeProject(directory));
  const before = snapshot(directory);

  const session = admitChange({ projectDirectory: directory, request: NEW_FUNCTION_REQUEST });

  assert.equal(session.verdict, 'FAIL');
  assert.equal(session.admission.details.binding.admittedScope.origin, 'inferred');
  assert.deepEqual(session.admission.details.binding.admittedScope.entries, [{ mode: 'subtree', path: 'src/application' }]);
  assert.equal(session.admission.details.reuse.decision, 'reuse-possible');
  assert.ok(session.risks.some((risk) => risk.code === 'reuse-required-for-proposed-shape'));
  assert.deepEqual(snapshot(directory), before);

  const denied = session.attemptWrite({
    request: NEW_FUNCTION_REQUEST,
    writes: [write('src/application/create-user.ts', FIRST_REVISION)]
  });
  assert.equal(denied.allowed, false);
  assert.equal(denied.reason.code, 'admission-not-passed');
  assert.deepEqual(snapshot(directory), before);
});

test('rejects an exact observed function proposed again as new', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'exact-symbol-project', main: 'src/index.js' }),
    'src/index.js': 'function parse(input) { return input; }\nexports.parse = parse;\n'
  });
  t.after(() => removeProject(directory));
  const request = 'Add a new function parse. Keep existing behavior unchanged. If input is empty, show an error message.';
  const session = admitChange({ projectDirectory: directory, request });

  assert.equal(session.verdict, 'FAIL');
  assert.equal(session.details.reuse.decision, 'reuse-possible');
  assert.ok(session.risks.some((risk) => risk.code === 'reuse-required-for-proposed-shape'));
});

test('mediates only declared in-scope writes and retains a pass for same-intent revisions', (t) => {
  const directory = makeProject(validProject());
  t.after(() => removeProject(directory));
  const before = snapshot(directory);

  const session = admitChange({ projectDirectory: directory, request: REUSE_REQUEST });

  assert.equal(session.verdict, 'PASS');
  assert.deepEqual(session.summary, {
    verdict: session.details.verdict,
    selectedResponsibility: session.details.selectedResponsibility,
    mainRisks: session.details.mainRisks
  });
  assert.equal(session.details.selectedResponsibility.ownerPath, 'src/application');
  assert.deepEqual(snapshot(directory), before);
  const originalState = session.details.binding.originalSourceState;

  const first = session.attemptWrite({
    request: REUSE_REQUEST,
    scope: 'src/application',
    writes: [write('src/application/create-user.ts', FIRST_REVISION)]
  });
  assert.equal(first.allowed, true);
  assert.deepEqual(first.writes, ['src/application/create-user.ts']);
  assert.equal(fs.readFileSync(path.join(directory, 'src/application/create-user.ts'), 'utf8'), FIRST_REVISION);
  assert.deepEqual(session.details.binding.originalSourceState, originalState);
  assert.notEqual(session.details.binding.currentSourceState.digest, originalState.digest);

  const second = session.attemptWrite({
    request: REUSE_REQUEST,
    writes: [write('src/application/create-user.ts', SECOND_REVISION)]
  });
  assert.equal(second.allowed, true);
  assert.equal(fs.readFileSync(path.join(directory, 'src/application/create-user.ts'), 'utf8'), SECOND_REVISION);
});

test('allows an explicit new shape when repository evidence finds no reusable candidate', (t) => {
  const directory = makeProject(singleBoundaryProject());
  t.after(() => removeProject(directory));
  const request = 'Add a new helper to validate a user name. Keep existing user reading unchanged. If a name is empty, show an error message.';
  const session = admitChange({
    projectDirectory: directory,
    request,
    scope: 'src/validate-name.js'
  });

  assert.equal(session.verdict, 'PASS');
  assert.equal(session.details.binding.admittedScope.origin, 'explicit');
  assert.deepEqual(session.details.binding.admittedScope.entries, [{ mode: 'exact', path: 'src/validate-name.js' }]);
  assert.equal(session.details.reuse.decision, 'creation-necessary');
  assert.equal(session.details.reuse.allowsCreation, true);
  const allowed = session.attemptWrite({
    request,
    writes: [write('src/validate-name.js', 'exports.validateName = (name) => Boolean(name);\n')]
  });
  assert.equal(allowed.allowed, true);

  const child = session.attemptWrite({
    request,
    writes: [write('src/validate-name.js/child.js', 'module.exports = true;\n')]
  });
  assert.equal(child.allowed, false);
  assert.equal(child.reason.code, 'out-of-scope-write');
  assert.equal(fs.existsSync(path.join(directory, 'src/validate-name.js/child.js')), false);
});

test('rejects unsafe or mixed declarative writes before changing either target', (t) => {
  const directory = makeProject(validProject());
  const outside = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-outside-'));
  t.after(() => removeProject(directory));
  t.after(() => removeProject(outside));
  fs.symlinkSync(outside, path.join(directory, 'src', 'application', 'outside-link'), 'dir');
  const before = snapshot(directory);
  const session = admitChange({ projectDirectory: directory, request: REUSE_REQUEST });
  assert.equal(session.verdict, 'PASS');

  let callbackCalled = false;
  const callbackDenied = session.attemptWrite({
    request: REUSE_REQUEST,
    mutate() {
      callbackCalled = true;
    }
  });
  assert.equal(callbackDenied.allowed, false);
  assert.equal(callbackDenied.reason.code, 'missing-write-operations');
  assert.equal(callbackCalled, false);

  const cases = [
    {
      name: 'outside scope',
      operation: write('src/domain/escape.ts', 'export const escape = true;\n'),
      code: 'out-of-scope-write'
    },
    {
      name: 'traversal',
      operation: write('../escape.js', 'module.exports = true;\n'),
      code: 'traversal-write-path'
    },
    {
      name: 'absolute path',
      operation: write(path.join(directory, 'src', 'application', 'escape.ts'), 'export const escape = true;\n'),
      code: 'absolute-write-path'
    },
    {
      name: 'symbolic link',
      operation: write('src/application/outside-link/escape.ts', 'export const escape = true;\n'),
      code: 'symlink-write-path'
    },
    {
      name: 'special target',
      operation: write('src/application', 'not a file'),
      code: 'special-write-target'
    }
  ];

  for (const candidate of cases) {
    const denied = session.attemptWrite({ request: REUSE_REQUEST, writes: [candidate.operation] });
    assert.equal(denied.allowed, false, candidate.name);
    assert.equal(denied.reason.code, candidate.code, candidate.name);
    assert.deepEqual(snapshot(directory), before, candidate.name);
  }

  const mixed = session.attemptWrite({
    request: REUSE_REQUEST,
    writes: [
      write('src/application/create-user.ts', FIRST_REVISION),
      write('src/domain/escape.ts', 'export const escape = true;\n')
    ]
  });
  assert.equal(mixed.allowed, false);
  assert.equal(mixed.reason.code, 'out-of-scope-write');
  assert.deepEqual(snapshot(directory), before);
  assert.equal(fs.existsSync(path.join(outside, 'escape.ts')), false);
});

test('rolls back earlier files when a later atomic commit fails', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'atomic-project', main: 'src/first.js' }),
    'src/first.js': 'first old\n',
    'src/second.js': 'second old\n'
  });
  t.after(() => removeProject(directory));
  const request = 'Update source behavior. Keep existing startup unchanged. If the update fails, show an error message.';
  const session = admitChange({ projectDirectory: directory, request });
  const before = snapshot(directory);
  const renameSync = fs.renameSync;

  fs.renameSync = (source, destination) => {
    if (destination === path.join(directory, 'src/second.js')) {
      const error = new Error('simulated second commit failure');
      error.code = 'EIO';
      throw error;
    }
    return renameSync(source, destination);
  };
  t.after(() => {
    fs.renameSync = renameSync;
  });

  const denied = session.attemptWrite({
    request,
    writes: [
      write('src/first.js', 'first new\n'),
      write('src/second.js', 'second new\n')
    ]
  });

  fs.renameSync = renameSync;
  assert.equal(denied.allowed, false);
  assert.equal(denied.reason.code, 'write-failed');
  assert.deepEqual(snapshot(directory), before);
  assert.deepEqual(
    fs.readdirSync(path.join(directory, 'src')).sort(),
    ['first.js', 'second.js']
  );
});

test('denies pre-pass, changed intent or scope, and external source changes without writes', (t) => {
  const directory = makeProject(validProject());
  t.after(() => removeProject(directory));
  const incompleteRequest = 'Reuse the existing createUser behavior. Keep existing user reading unchanged.';
  const before = snapshot(directory);
  const incomplete = admitChange({
    projectDirectory: directory,
    request: incompleteRequest,
    evidence: [{ verdict: 'PASS' }],
    verdict: 'PASS'
  });

  assert.equal(incomplete.verdict, 'INCONCLUSIVE');
  assert.equal(incomplete.details.reinvestigation.performed, true);
  const prePassDenied = incomplete.attemptWrite({
    request: incompleteRequest,
    writes: [write('src/application/create-user.ts', FIRST_REVISION)]
  });
  assert.equal(prePassDenied.allowed, false);
  assert.equal(prePassDenied.reason.code, 'admission-not-passed');
  assert.deepEqual(snapshot(directory), before);

  const session = admitChange({ projectDirectory: directory, request: REUSE_REQUEST });
  assert.equal(session.verdict, 'PASS');
  const changedIntent = session.attemptWrite({
    request: `${REUSE_REQUEST} Also notify administrators.`,
    writes: [write('src/application/create-user.ts', FIRST_REVISION)]
  });
  assert.equal(changedIntent.reason.code, 'changed-intent');
  const changedScope = session.attemptWrite({
    request: REUSE_REQUEST,
    scope: 'src/domain',
    writes: [write('src/application/create-user.ts', FIRST_REVISION)]
  });
  assert.equal(changedScope.reason.code, 'changed-scope');
  assert.deepEqual(snapshot(directory), before);

  fs.writeFileSync(path.join(directory, 'src', 'application', 'external.ts'), 'export const external = true;\n');
  const afterExternalChange = snapshot(directory);
  const stale = session.attemptWrite({
    request: REUSE_REQUEST,
    writes: [write('src/application/create-user.ts', FIRST_REVISION)]
  });
  assert.equal(stale.allowed, false);
  assert.equal(stale.reason.code, 'stale-source');
  assert.deepEqual(snapshot(directory), afterExternalChange);
});

test('greenfield admission permits only its fixed baseline paths', (t) => {
  const directory = makeProject();
  t.after(() => removeProject(directory));
  const request = 'Add account creation. Keep existing sign-in behavior unchanged. If a name is empty, show an error message.';
  const before = snapshot(directory);
  const session = admitChange({ projectDirectory: directory, request });

  assert.equal(session.verdict, 'PASS');
  assert.equal(session.details.proposedBaseline.status, 'proposed-not-created');
  assert.deepEqual(session.details.binding.admittedScope.entries, [
    { mode: 'exact', path: 'package.json' },
    { mode: 'exact', path: 'src/index.js' },
    { mode: 'exact', path: 'test/index.test.js' }
  ]);
  assert.deepEqual(snapshot(directory), before);

  const outside = session.attemptWrite({ request, writes: [write('src/other.js', 'module.exports = null;\n')] });
  assert.equal(outside.allowed, false);
  assert.equal(outside.reason.code, 'out-of-scope-write');
  assert.deepEqual(snapshot(directory), before);

  const first = session.attemptWrite({
    request,
    writes: [
      write('package.json', JSON.stringify({ name: 'greenfield-project', main: 'src/index.js' })),
      write('src/index.js', 'exports.createAccount = (name) => ({ name });\n'),
      write('test/index.test.js', "const test = require('node:test');\ntest('placeholder', () => {});\n")
    ]
  });
  assert.equal(first.allowed, true);
  const second = session.attemptWrite({
    request,
    writes: [write('src/index.js', 'exports.createAccount = (name) => ({ name: name.trim() });\n')]
  });
  assert.equal(second.allowed, true);
  assert.equal(fs.existsSync(path.join(directory, 'src', 'other.js')), false);
});

test('proposes TypeScript baseline paths without creating them', (t) => {
  const directory = makeProject();
  t.after(() => removeProject(directory));
  const before = snapshot(directory);
  const session = admitChange({
    projectDirectory: directory,
    request: 'Create a TypeScript account flow. Keep current sign-in behavior unchanged. If a name is empty, show an error message.'
  });

  assert.equal(session.verdict, 'PASS');
  assert.equal(session.details.proposedBaseline.language, 'TypeScript');
  assert.deepEqual(session.details.binding.admittedScope.entries, [
    { mode: 'exact', path: 'package.json' },
    { mode: 'exact', path: 'src/index.ts' },
    { mode: 'exact', path: 'test/index.test.ts' },
    { mode: 'exact', path: 'tsconfig.json' }
  ]);
  assert.deepEqual(snapshot(directory), before);
});

test('propagates structural failure and performs no writes', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'broken-project' }),
    'src/index.js': "module.exports = require('./missing');\n"
  });
  t.after(() => removeProject(directory));
  const request = 'Reuse the existing greeting behavior. Keep existing startup behavior unchanged. If a name is missing, show an error message.';
  const before = snapshot(directory);
  const session = admitChange({ projectDirectory: directory, request });

  assert.equal(session.verdict, 'FAIL');
  const denied = session.attemptWrite({ request, writes: [write('src/index.js', 'module.exports = true;\n')] });
  assert.equal(denied.allowed, false);
  assert.equal(denied.verdict, 'FAIL');
  assert.deepEqual(snapshot(directory), before);
});

test('separates Korean desired and preserved behavior instead of reusing the failure clause', (t) => {
  const directory = makeProject(singleBoundaryProject());
  t.after(() => removeProject(directory));
  const request = '사용자가 이름을 수정할 수 있게 하고 기존 로그인은 그대로 유지하세요. 실패하면 오류를 보여 주세요.';

  const session = admitChange({ projectDirectory: directory, request });

  assert.equal(session.verdict, 'PASS');
  assert.match(session.details.behavior.desiredBehavior.text, /이름을 수정/);
  assert.match(session.details.behavior.behaviorToPreserve.text, /기존 로그인/);
  assert.match(session.details.behavior.observableFailureOutcome.text, /실패하면 오류/);
  assert.notEqual(
    session.details.behavior.desiredBehavior.text,
    session.details.behavior.observableFailureOutcome.text
  );
});

test('fails closed when only preservation and failure behavior are stated', (t) => {
  const directory = makeProject(singleBoundaryProject());
  t.after(() => removeProject(directory));
  const request = '기존 로그인은 그대로 유지하세요. 실패하면 오류를 보여 주세요.';

  const session = admitChange({ projectDirectory: directory, request });

  assert.equal(session.verdict, 'INCONCLUSIVE');
  assert.equal(session.details.behavior.desiredBehavior, null);
  assert.ok(session.questions.includes('What should people be able to do after this change?'));
});

test('reinvestigates ambiguous source and test matches before selecting product responsibility', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'reinvestigation-project', main: 'src/admission.js' }),
    'src/admission.js': 'exports.admit = () => true;\n',
    'test/admission.test.js': 'const admission = require(\'../src/admission\');\n'
  });
  t.after(() => removeProject(directory));
  const request = 'Update admission behavior. Keep existing diagnosis unchanged. If admission fails, show an error message.';

  const session = admitChange({ projectDirectory: directory, request });

  assert.equal(session.verdict, 'PASS');
  assert.equal(session.details.selectedResponsibility.ownerPath, 'src');
  assert.equal(session.details.reinvestigation.performed, true);
  assert.equal(session.details.reinvestigation.reason, 'unresolved-change-responsibility');
  assert.deepEqual(session.details.reinvestigation.observed.excludedTestResponsibilities, ['test']);
  assert.equal(session.questions.length, 0);
});

test('fails closed when multiple source SSOT candidates cannot be resolved for the request', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'ambiguous-ssot', main: 'src/index.js' }),
    'src/index.js': "require('./a'); require('./b');\n",
    'src/other.js': "require('./a'); require('./b');\n",
    'src/a.js': 'exports.sharedA = true;\n',
    'src/b.js': 'exports.sharedB = true;\n'
  });
  t.after(() => removeProject(directory));
  const request = 'Update shared behavior. Keep existing startup unchanged. If the update fails, show an error message.';

  const session = admitChange({ projectDirectory: directory, request });

  assert.equal(session.verdict, 'INCONCLUSIVE');
  assert.deepEqual(session.details.repositoryEvidence.executionPaths, ['src/index.js']);
  assert.equal(session.details.repositoryEvidence.canonicalSsot, null);
  assert.ok(session.risks.some((risk) => risk.code === 'canonical-ssot-unresolved'));
});

test('records resolved execution path and canonical SSOT before passing admission', (t) => {
  const directory = makeProject(singleBoundaryProject());
  t.after(() => removeProject(directory));
  const request = 'Update user creation behavior. Keep existing startup unchanged. If creation fails, show an error message.';

  const session = admitChange({ projectDirectory: directory, request });

  assert.equal(session.verdict, 'PASS');
  assert.deepEqual(session.details.repositoryEvidence.executionPaths, ['src/index.js']);
  assert.equal(session.details.repositoryEvidence.canonicalSsot.path, 'src/index.js');
});

test('invalidates admission when a source file permission mode changes', (t) => {
  const directory = makeProject(singleBoundaryProject());
  t.after(() => removeProject(directory));
  const request = 'Update user creation behavior. Keep existing startup unchanged. If creation fails, show an error message.';
  const target = path.join(directory, 'src/index.js');
  const session = admitChange({ projectDirectory: directory, request });
  const originalMode = fs.statSync(target).mode & 0o777;

  fs.chmodSync(target, originalMode | 0o111);
  const stale = session.attemptWrite({
    request,
    writes: [write('src/index.js', 'exports.createUser = () => null;\n')]
  });

  assert.equal(stale.allowed, false);
  assert.equal(stale.reason.code, 'stale-source');
  assert.match(fs.readFileSync(target, 'utf8'), /createUser/);
});
