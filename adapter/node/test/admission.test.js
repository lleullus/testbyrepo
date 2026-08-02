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

test('AST reusable-symbol evidence covers CommonJS exports, object methods, and class methods', (t) => {
  const fixtures = [
    {
      source: 'module.exports = function validate(value) { return value; };\n',
      symbol: 'validate'
    },
    {
      source: 'module.exports = { validate(value) { return value; } };\n',
      symbol: 'validate'
    },
    {
      source: 'class Validator { validate(value) { return value; } }\nmodule.exports = Validator;\n',
      symbol: 'validate'
    },
    {
      source: 'class Validator {}\nmodule.exports = Validator;\nValidator.prototype.validate = function(value) { return value; };\n',
      symbol: 'validate'
    }
  ];
  for (const fixture of fixtures) {
    const directory = makeProject({
      'package.json': JSON.stringify({ name: 'ast-symbols', main: 'src/index.js' }),
      'src/index.js': fixture.source
    });
    t.after(() => removeProject(directory));
    const request = 'Add a new function validate. Keep existing behavior unchanged. If input is invalid, show an error message.';
    const session = admitChange({ projectDirectory: directory, request });

    assert.equal(session.verdict, 'FAIL');
    assert.ok(session.details.reuse.observedSymbols.some((item) => item.symbol === fixture.symbol));
    assert.ok(session.details.reuse.matches.some((item) => item.symbol === fixture.symbol));
  }
});

test('computed CommonJS exports are reusable public symbols in observed and proposed code', (t) => {
  const sources = [
    "exports['validate'] = function validate(value) { return value; };\n",
    "module.exports['validate'] = function validate(value) { return value; };\n"
  ];
  const request = 'Add a new function validate. Keep existing behavior unchanged. If input is invalid, show an error message.';

  for (const source of sources) {
    const directory = makeProject({
      'package.json': JSON.stringify({ name: 'computed-exports', main: 'src/index.js' }),
      'src/index.js': source
    });
    t.after(() => removeProject(directory));
    const session = admitChange({ projectDirectory: directory, request });

    assert.equal(session.verdict, 'FAIL');
    assert.ok(session.details.reuse.observedSymbols.some((item) => item.symbol === 'validate'));

    const before = snapshot(directory);
    const denied = session.attemptWrite({
      request,
      writes: [{ path: 'src/new-validator.js', content: "exports['validate'] = function validate(value) { return Boolean(value); };\n" }]
    });
    assert.equal(denied.allowed, false);
    assert.equal(denied.reason.code, 'admission-not-passed');
    assert.deepEqual(snapshot(directory), before);
  }
});

test('static computed export keys resolve while unresolved keys fail closed', (t) => {
  const staticSources = [
    "const key = 'validate';\nexports[key] = function validate(value) { return value; };\n",
    "const key = 'validate';\nmodule.exports[key] = function validate(value) { return value; };\n"
  ];
  const request = 'Add a new function validate. Keep existing behavior unchanged. If input is invalid, show an error message.';

  for (const source of staticSources) {
    const directory = makeProject({
      'package.json': JSON.stringify({ name: 'static-computed-exports', main: 'src/index.js' }),
      'src/index.js': source
    });
    t.after(() => removeProject(directory));
    const session = admitChange({ projectDirectory: directory, request });

    assert.equal(session.verdict, 'FAIL');
    assert.ok(session.details.reuse.observedSymbols.some((item) => item.symbol === 'validate'));
    assert.equal(session.details.reuse.observedSymbols.some((item) => item.symbol === 'key'), false);
  }

  const unresolvedDirectory = makeProject({
    'package.json': JSON.stringify({ name: 'unresolved-computed-exports', main: 'src/index.js' }),
    'src/index.js': 'const key = getExportName();\nexports[key] = function validate(value) { return value; };\n'
  });
  t.after(() => removeProject(unresolvedDirectory));
  const unresolvedSession = admitChange({ projectDirectory: unresolvedDirectory, request });
  assert.equal(unresolvedSession.verdict, 'INCONCLUSIVE');
  assert.equal(unresolvedSession.details.reuse.observedSymbols.length, 0);

  const unresolvedWrite = unresolvedSession.attemptWrite({
    request,
    writes: [{ path: 'src/new-validator.js', content: 'const key = getExportName();\nexports[key] = function validate(value) { return value; };\n' }]
  });
  assert.equal(unresolvedWrite.allowed, false);
  assert.equal(unresolvedWrite.reason.code, 'admission-not-passed');

  const cleanDirectory = makeProject(singleBoundaryProject());
  t.after(() => removeProject(cleanDirectory));
  const cleanSession = admitChange({ projectDirectory: cleanDirectory, request, scope: 'src' });
  assert.equal(cleanSession.verdict, 'PASS');
  const unresolvedProposed = cleanSession.attemptWrite({
    request,
    writes: [{ path: 'src/new-validator.js', content: 'const key = getExportName();\nexports[key] = function validate(value) { return value; };\n' }]
  });
  assert.equal(unresolvedProposed.allowed, false);
  assert.equal(unresolvedProposed.reason.code, 'reuse-write-analysis-unavailable');
});

test('reusable analysis only admits public methods, excludes constructors, and recognizes defaults', (t) => {
  const cases = [
    {
      name: 'private class method',
      source: 'class Internal { validate(value) { return value; } }\nmodule.exports = {};\n',
      expectedVerdict: 'PASS',
      expectedSymbols: []
    },
    {
      name: 'private object method',
      source: 'const helper = { validate(value) { return value; } };\nmodule.exports = {};\n',
      expectedVerdict: 'PASS',
      expectedSymbols: []
    },
    {
      name: 'exported class method',
      source: 'class Validator { constructor() {} validate(value) { return value; } }\nmodule.exports = Validator;\n',
      expectedVerdict: 'FAIL',
      expectedSymbols: ['Validator', 'validate']
    },
    {
      name: 'default export',
      source: 'export default function validate(value) { return value; }\n',
      request: 'Add a new default function. Keep existing behavior unchanged. If input is invalid, show an error message.',
      expectedVerdict: 'FAIL',
      expectedSymbols: ['default']
    }
  ];

  for (const fixture of cases) {
    const directory = makeProject({
      'package.json': JSON.stringify({ name: 'public-symbols', main: 'src/index.js' }),
      'src/index.js': fixture.source
    });
    t.after(() => removeProject(directory));
    const request = fixture.request || 'Add a new function validate. Keep existing behavior unchanged. If input is invalid, show an error message.';
    const session = admitChange({ projectDirectory: directory, request });
    const observed = session.details.reuse.observedSymbols.map((item) => item.symbol);

    assert.equal(session.verdict, fixture.expectedVerdict, fixture.name);
    for (const symbol of fixture.expectedSymbols) {
      assert.ok(observed.includes(symbol), `${fixture.name}: ${symbol}`);
    }
    assert.equal(observed.includes('constructor'), false, fixture.name);
    if (fixture.expectedSymbols.length === 0) {
      assert.equal(observed.includes('validate'), false, fixture.name);
    }
  }
});

test('default export identity stays distinct from its declared name during reuse checks', (t) => {
  const source = 'export default function validate(value) { return value; }\n';
  const request = 'Add a new function validate. Keep existing behavior unchanged. If input is invalid, show an error message.';
  const namedDirectory = makeProject({
    'package.json': JSON.stringify({ name: 'default-name-boundary', main: 'src/index.js' }),
    'src/index.js': source
  });
  t.after(() => removeProject(namedDirectory));

  const namedSession = admitChange({ projectDirectory: namedDirectory, request, scope: 'src' });
  assert.equal(namedSession.verdict, 'PASS');
  assert.deepEqual(
    namedSession.details.reuse.observedSymbols.map((item) => ({ publicKey: item.publicKey, symbol: item.symbol })),
    [{ publicKey: 'export:default', symbol: 'default' }]
  );
  const namedWrite = namedSession.attemptWrite({
    request,
    writes: [{ path: 'src/named.js', content: 'export function validate(value) { return Boolean(value); }\n' }]
  });
  assert.equal(namedWrite.allowed, true);

  const defaultDirectory = makeProject({
    'package.json': JSON.stringify({ name: 'default-public-symbol', main: 'src/index.js' }),
    'src/index.js': source
  });
  t.after(() => removeProject(defaultDirectory));
  const updateRequest = 'Update source behavior. Keep existing startup unchanged. If the update fails, show an error message.';
  const defaultSession = admitChange({ projectDirectory: defaultDirectory, request: updateRequest, scope: 'src' });
  assert.equal(defaultSession.verdict, 'PASS');
  const defaultWrite = defaultSession.attemptWrite({
    request: updateRequest,
    writes: [{ path: 'src/other-default.js', content: 'export default function other(value) { return Boolean(value); }\n' }]
  });
  assert.equal(defaultWrite.allowed, false);
  assert.equal(defaultWrite.reason.code, 'reuse-required-for-proposed-write-symbol');
});

test('proposed public symbols are checked from content even when request wording says reuse', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'content-recheck', main: 'src/index.js' }),
    'src/index.js': "exports['validate'] = function validate(value) { return value; };\n"
  });
  t.after(() => removeProject(directory));
  const request = 'Reuse the existing validation behavior. Keep existing startup unchanged. If validation fails, show an error message.';
  const session = admitChange({ projectDirectory: directory, request, scope: 'src' });
  assert.equal(session.verdict, 'PASS');

  const denied = session.attemptWrite({
    request,
    writes: [{ path: 'src/new-validator.js', content: "module.exports['validate'] = function validate(value) { return Boolean(value); };\n" }]
  });

  assert.equal(denied.allowed, false);
  assert.equal(denied.reason.code, 'reuse-required-for-proposed-write-symbol');
  assert.equal(fs.existsSync(path.join(directory, 'src', 'new-validator.js')), false);
});

test('a duplicate reusable symbol in a proposed write is denied before any file changes', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'duplicate-write', main: 'src/index.js' }),
    'src/index.js': 'function validate(value) { return value; }\nmodule.exports = { validate };\n'
  });
  t.after(() => removeProject(directory));
  const request = 'Add validation. Keep existing behavior unchanged. If invalid, show an error message.';
  const session = admitChange({ projectDirectory: directory, request, scope: 'src' });
  assert.equal(session.verdict, 'PASS');
  const before = snapshot(directory);

  const denied = session.attemptWrite({
    request,
    writes: [{ path: 'src/new-validator.js', content: 'function validate(value) { return Boolean(value); }\nmodule.exports = { validate };\n' }]
  });

  assert.equal(denied.allowed, false);
  assert.equal(denied.reason.code, 'reuse-required-for-proposed-write-symbol');
  assert.deepEqual(snapshot(directory), before);
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

  fs.symlinkSync(outside, path.join(directory, 'src', 'application', 'outside-link'), 'dir');
  const symlinkDenied = session.attemptWrite({
    request: REUSE_REQUEST,
    writes: [write('src/application/outside-link/escape.ts', 'export const escape = true;\n')]
  });
  assert.equal(symlinkDenied.allowed, false);
  assert.equal(symlinkDenied.reason.code, 'symlink-write-path');
  assert.equal(fs.existsSync(path.join(outside, 'escape.ts')), false);
});

test('rolls back earlier files when a later atomic commit fails', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'atomic-project', main: 'src/first.js' }),
     'src/first.js': 'module.exports = "first old";\n',
     'src/second.js': 'module.exports = "second old";\n'
  });
  t.after(() => removeProject(directory));
  const request = 'Update source behavior. Keep existing startup unchanged. If the update fails, show an error message.';
  const session = admitChange({ projectDirectory: directory, request });
  const before = snapshot(directory);
   const linkSync = fs.linkSync;
   let failed = false;

   fs.linkSync = (source, destination) => {
     if (!failed && String(destination).endsWith('/second.js')) {
       failed = true;
       const error = new Error('simulated second commit failure');
      error.code = 'EIO';
      throw error;
    }
    return linkSync(source, destination);
  };
  t.after(() => {
    fs.linkSync = linkSync;
  });

  const denied = session.attemptWrite({
    request,
    writes: [
       write('src/first.js', 'module.exports = "first new";\n'),
       write('src/second.js', 'module.exports = "second new";\n')
    ]
  });

   fs.linkSync = linkSync;
  assert.equal(denied.allowed, false);
  assert.equal(denied.reason.code, 'write-failed');
  assert.deepEqual(snapshot(directory), before);
  assert.deepEqual(
    fs.readdirSync(path.join(directory, 'src')).sort(),
    ['first.js', 'second.js']
  );
});

test('mediated write denies a parent swap between planning and commit without touching outside state', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'toctou-project', main: 'src/first.js' }),
    'src/first.js': 'module.exports = "first old";\n'
  });
  const outside = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-toctou-outside-'));
  const sentinel = path.join(outside, 'sentinel.txt');
  fs.writeFileSync(sentinel, 'outside unchanged');
  t.after(() => removeProject(directory));
  t.after(() => removeProject(outside));
  const request = 'Update source behavior. Keep existing startup unchanged. If the update fails, show an error message.';
  const session = admitChange({ projectDirectory: directory, request });
  assert.equal(session.verdict, 'PASS');
  const renameSync = fs.renameSync;
  const linkSync = fs.linkSync;
  let swapped = false;
  fs.linkSync = (source, destination) => {
    if (!swapped && String(destination).endsWith('/first.js')) {
      swapped = true;
      renameSync(path.join(directory, 'src'), path.join(directory, '.moved-src'));
      fs.symlinkSync(outside, path.join(directory, 'src'), 'dir');
    }
    return linkSync(source, destination);
  };
  t.after(() => {
    fs.renameSync = renameSync;
    fs.linkSync = linkSync;
  });

  const denied = session.attemptWrite({
    request,
    writes: [{ path: 'src/first.js', content: 'module.exports = "first new";\n' }]
  });

  fs.renameSync = renameSync;
  fs.linkSync = linkSync;
  assert.equal(denied.allowed, false);
  assert.equal(denied.reason.code, 'write-failed');
  assert.equal(fs.readFileSync(sentinel, 'utf8'), 'outside unchanged');
});

test('FD-anchored staging cannot chmod an outside symlink target', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'pending-race', main: 'src/index.js' }),
    'src/index.js': 'module.exports = "old";\n'
  });
  const outside = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-pending-outside-'));
  const sentinel = path.join(outside, 'sentinel.txt');
  fs.writeFileSync(sentinel, 'outside unchanged');
  fs.chmodSync(sentinel, 0o600);
  t.after(() => removeProject(directory));
  t.after(() => removeProject(outside));

  const request = 'Update source behavior. Keep existing startup unchanged. If the update fails, show an error message.';
  const session = admitChange({ projectDirectory: directory, request });
  const originalFchmod = fs.fchmodSync;
  const outsideMode = fs.statSync(sentinel).mode & 0o777;
  let swapped = false;
  fs.fchmodSync = (fd, mode) => {
    if (!swapped) {
      swapped = true;
      const pendingPath = fs.readlinkSync(`/proc/self/fd/${fd}`);
      fs.unlinkSync(pendingPath);
      fs.symlinkSync(sentinel, pendingPath);
    }
    return originalFchmod(fd, mode);
  };
  t.after(() => {
    fs.fchmodSync = originalFchmod;
  });

  const denied = session.attemptWrite({
    request,
    writes: [{ path: 'src/index.js', content: 'module.exports = "new";\n' }]
  });

  fs.fchmodSync = originalFchmod;
  assert.equal(denied.allowed, false);
  assert.equal(denied.reason.code, 'write-failed');
  assert.equal(fs.statSync(sentinel).mode & 0o777, outsideMode);
  assert.equal(fs.readFileSync(path.join(directory, 'src', 'index.js'), 'utf8'), 'module.exports = "old";\n');
});

test('no-replace commit preserves a target introduced immediately before installation', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'target-race', main: 'src/index.js' }),
    'src/index.js': 'module.exports = "old";\n'
  });
  t.after(() => removeProject(directory));
  const request = 'Update source behavior. Keep existing startup unchanged. If the update fails, show an error message.';
  const session = admitChange({ projectDirectory: directory, request });
  const originalLink = fs.linkSync;
  let swapped = false;
  fs.linkSync = (source, destination) => {
    if (!swapped && String(destination).endsWith('/index.js')) {
      swapped = true;
      fs.writeFileSync(path.join(directory, 'src', 'index.js'), 'module.exports = "concurrent";\n');
    }
    return originalLink(source, destination);
  };
  t.after(() => {
    fs.linkSync = originalLink;
  });

  const denied = session.attemptWrite({
    request,
    writes: [{ path: 'src/index.js', content: 'module.exports = "new";\n' }]
  });

  fs.linkSync = originalLink;
  assert.equal(denied.allowed, false);
  assert.equal(denied.reason.code, 'write-failed');
  assert.equal(fs.readFileSync(path.join(directory, 'src', 'index.js'), 'utf8'), 'module.exports = "concurrent";\n');
  assert.match(denied.reason.message, /original target backup preserved at src\/\.node-policy-.*\.backup/);
  const backups = fs.readdirSync(path.join(directory, 'src')).filter((name) => name.endsWith('.backup'));
  assert.equal(backups.length, 1);
  assert.equal(
    fs.readFileSync(path.join(directory, 'src', backups[0]), 'utf8'),
    'module.exports = "old";\n'
  );
  assert.equal(fs.readdirSync(path.join(directory, 'src')).some((name) => name.endsWith('.pending')), false);
});

test('content and metadata changes after authorization are rejected before target mutation', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'content-race', main: 'src/index.js' }),
    'src/index.js': 'module.exports = "old";\n'
  });
  t.after(() => removeProject(directory));
  const target = path.join(directory, 'src', 'index.js');
  const request = 'Update source behavior. Keep existing startup unchanged. If the update fails, show an error message.';
  const session = admitChange({ projectDirectory: directory, request });
  const originalRename = fs.renameSync;
  let changed = false;
  fs.renameSync = (source, destination) => {
    if (!changed && String(destination).endsWith('.backup')) {
      changed = true;
      fs.writeFileSync(target, 'module.exports = "concurrent";\n');
    }
    return originalRename(source, destination);
  };
  t.after(() => {
    fs.renameSync = originalRename;
  });

  const denied = session.attemptWrite({
    request,
    writes: [{ path: 'src/index.js', content: 'module.exports = "new";\n' }]
  });

  fs.renameSync = originalRename;
  assert.equal(denied.allowed, false);
  assert.equal(denied.reason.code, 'write-failed');
  assert.equal(fs.readFileSync(target, 'utf8'), 'module.exports = "concurrent";\n');
});

test('pending descriptor content must remain equal to the planned bytes', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'pending-content-race', main: 'src/index.js' }),
    'src/index.js': 'module.exports = "old";\n'
  });
  t.after(() => removeProject(directory));
  const target = path.join(directory, 'src', 'index.js');
  const request = 'Update source behavior. Keep existing startup unchanged. If the update fails, show an error message.';
  const session = admitChange({ projectDirectory: directory, request });
  const originalFchmod = fs.fchmodSync;
  let tampered = false;
  fs.fchmodSync = (fd, mode) => {
    const result = originalFchmod(fd, mode);
    if (!tampered) {
      tampered = true;
      fs.writeFileSync(fs.readlinkSync(`/proc/self/fd/${fd}`), 'tampered\n');
    }
    return result;
  };
  t.after(() => {
    fs.fchmodSync = originalFchmod;
  });

  const denied = session.attemptWrite({
    request,
    writes: [{ path: 'src/index.js', content: 'module.exports = "new";\n' }]
  });

  fs.fchmodSync = originalFchmod;
  assert.equal(denied.allowed, false);
  assert.equal(denied.reason.code, 'write-failed');
  assert.equal(fs.readFileSync(target, 'utf8'), 'module.exports = "old";\n');
  assert.equal(fs.readdirSync(path.join(directory, 'src')).some((name) => name.endsWith('.pending')), false);
});

test('a target mutation immediately after installation is denied with recoverable bytes', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'post-install-race', main: 'src/index.js' }),
    'src/index.js': 'module.exports = "old";\n'
  });
  t.after(() => removeProject(directory));
  const target = path.join(directory, 'src', 'index.js');
  const request = 'Update source behavior. Keep existing startup unchanged. If the update fails, show an error message.';
  const session = admitChange({ projectDirectory: directory, request });
  const originalUnlink = fs.unlinkSync;
  let changed = false;
  fs.unlinkSync = (filePath) => {
    const result = originalUnlink(filePath);
    if (!changed && String(filePath).endsWith('.pending')) {
      changed = true;
      fs.writeFileSync(target, 'changed after installation\n');
    }
    return result;
  };
  t.after(() => {
    fs.unlinkSync = originalUnlink;
  });

  const denied = session.attemptWrite({
    request,
    writes: [{ path: 'src/index.js', content: 'module.exports = "new";\n' }]
  });

  fs.unlinkSync = originalUnlink;
  assert.equal(denied.allowed, false);
  assert.equal(denied.reason.code, 'write-failed');
  assert.match(denied.reason.message, /installed target recovery preserved at src\/\.node-policy-.*\.recovery/);
  assert.equal(fs.readFileSync(target, 'utf8'), 'module.exports = "old";\n');
  const recoveries = fs.readdirSync(path.join(directory, 'src')).filter((name) => name.endsWith('.recovery'));
  assert.equal(recoveries.length, 1);
  assert.equal(fs.readFileSync(path.join(directory, 'src', recoveries[0]), 'utf8'), 'changed after installation\n');
});

test('a final pre-commit project readback rejects an unrelated concurrent change', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'final-readback', main: 'src/index.js' }),
    'src/index.js': 'module.exports = "old";\n'
  });
  t.after(() => removeProject(directory));
  const target = path.join(directory, 'src', 'index.js');
  const unrelated = path.join(directory, 'src', 'unrelated.js');
  const request = 'Update source behavior. Keep existing startup unchanged. If the update fails, show an error message.';
  const session = admitChange({ projectDirectory: directory, request });
  const originalWrite = fs.writeSync;
  let changed = false;
  fs.writeSync = (fd, buffer, offset, length) => {
    const descriptorPath = fs.readlinkSync(`/proc/self/fd/${fd}`);
    if (!changed && descriptorPath.endsWith('.pending')) {
      changed = true;
      fs.writeFileSync(unrelated, 'concurrent unrelated change\n');
    }
    return originalWrite(fd, buffer, offset, length);
  };
  t.after(() => {
    fs.writeSync = originalWrite;
  });

  const denied = session.attemptWrite({
    request,
    writes: [{ path: 'src/index.js', content: 'module.exports = "new";\n' }]
  });

  fs.writeSync = originalWrite;
  assert.equal(denied.allowed, false);
  assert.equal(denied.reason.code, 'write-failed');
  assert.equal(fs.readFileSync(target, 'utf8'), 'module.exports = "old";\n');
  assert.equal(fs.readFileSync(unrelated, 'utf8'), 'concurrent unrelated change\n');
});

test('a planned existing parent identity must match the opened directory handle', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'parent-identity', main: 'src/child/index.js' }),
    'src/child/index.js': 'module.exports = "old";\n'
  });
  t.after(() => removeProject(directory));
  const request = 'Update child behavior. Keep existing startup unchanged. If the update fails, show an error message.';
  const session = admitChange({ projectDirectory: directory, request, scope: 'src/child/index.js' });
  const originalOpen = fs.openSync;
  let swapped = false;
  fs.openSync = (filePath, flags, mode) => {
    if (!swapped && String(filePath).endsWith('/child')) {
      swapped = true;
      fs.renameSync(path.join(directory, 'src', 'child'), path.join(directory, 'src', 'child-old'));
      fs.mkdirSync(path.join(directory, 'src', 'child'));
    }
    return originalOpen(filePath, flags, mode);
  };
  t.after(() => {
    fs.openSync = originalOpen;
  });

  const denied = session.attemptWrite({
    request,
    writes: [{ path: 'src/child/index.js', content: 'module.exports = "new";\n' }]
  });

  fs.openSync = originalOpen;
  assert.equal(denied.allowed, false);
  assert.equal(denied.reason.code, 'write-failed');
  assert.equal(fs.readFileSync(path.join(directory, 'src', 'child-old', 'index.js'), 'utf8'), 'module.exports = "old";\n');
});

test('sequential mediated writes rescan symbols introduced by the prior write', (t) => {
  const directory = makeProject(singleBoundaryProject());
  t.after(() => removeProject(directory));
  const request = 'Update validation behavior. Keep existing startup unchanged. If validation fails, show an error message.';
  const session = admitChange({ projectDirectory: directory, request, scope: 'src' });
  assert.equal(session.verdict, 'PASS');

  const first = session.attemptWrite({
    request,
    writes: [{ path: 'src/first-validator.js', content: 'exports.validate = function validate(value) { return Boolean(value); };\n' }]
  });
  assert.equal(first.allowed, true);

  const second = session.attemptWrite({
    request,
    writes: [{ path: 'src/second-validator.js', content: 'exports.validate = function validate(value) { return Boolean(value); };\n' }]
  });
  assert.equal(second.allowed, false);
  assert.equal(second.reason.code, 'reuse-required-for-proposed-write-symbol');
  assert.equal(fs.existsSync(path.join(directory, 'src', 'second-validator.js')), false);
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

test('source tree symlinks fail closed during admission without writes', (t) => {
  const outside = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-admission-symlink-'));
  const directory = makeProject(singleBoundaryProject());
  fs.writeFileSync(path.join(outside, 'outside.js'), 'exports.outside = true;\n');
  fs.symlinkSync(path.join(outside, 'outside.js'), path.join(directory, 'src', 'linked.js'));
  t.after(() => removeProject(directory));
  t.after(() => removeProject(outside));
  const before = snapshot(directory);
  const request = 'Update user creation behavior. Keep existing startup unchanged. If creation fails, show an error message.';

  const session = admitChange({ projectDirectory: directory, request });

  assert.equal(session.verdict, 'INCONCLUSIVE');
  assert.ok(session.risks.some((risk) => risk.code === 'skipped-symbolic-link'));
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
  const failureObligation = session.details.testObligations.find((obligation) => obligation.case === 'failure-path');
  assert.deepEqual(failureObligation.expectedFailureOutcome, {
    constraints: [],
    generic: true,
    kind: 'error'
  });
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

test('imperative reject behavior is distinct from conditional failure outcome', (t) => {
  const directory = makeProject(singleBoundaryProject());
  t.after(() => removeProject(directory));
  const request = 'Reject invalid input. Keep valid behavior unchanged. If invalid, show an error message.';

  const session = admitChange({ projectDirectory: directory, request });

  assert.equal(session.verdict, 'PASS');
  assert.equal(session.details.behavior.desiredBehavior.text, 'Reject invalid input');
  assert.equal(session.details.behavior.behaviorToPreserve.text, 'Keep valid behavior unchanged');
  assert.equal(session.details.behavior.observableFailureOutcome.text, 'If invalid, show an error message');
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

test('uses configured package authority when multiple source candidates are otherwise observed', (t) => {
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

  assert.equal(session.verdict, 'PASS');
  assert.deepEqual(session.details.repositoryEvidence.executionPaths, ['src/index.js']);
  assert.equal(session.details.repositoryEvidence.canonicalSsot.path, 'src/index.js');
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

test('uses diagnosis authority for Node default index and root exports precedence', (t) => {
  const indexOnly = makeProject({
    'package.json': JSON.stringify({ name: 'index-only' }),
    'index.js': 'exports.start = () => true;\n'
  });
  t.after(() => removeProject(indexOnly));
  const request = 'Update startup behavior. Keep existing startup unchanged. If startup fails, show an error message.';
  const indexSession = admitChange({ projectDirectory: indexOnly, request, scope: 'index.js' });
  assert.equal(indexSession.verdict, 'PASS');
  assert.deepEqual(indexSession.details.repositoryEvidence.executionPaths, ['index.js']);
  assert.equal(indexSession.details.repositoryEvidence.canonicalSsot.path, 'index.js');
  assert.equal(indexSession.details.repositoryEvidence.canonicalSsot.source, 'node-default-entry');

  const exportsRoot = makeProject({
    'package.json': JSON.stringify({
      name: 'exports-root-precedence',
      exports: { '.': './src/root.js', './feature': './src/feature.js' },
      main: './src/main.js'
    }),
    'src/root.js': 'exports.start = () => true;\n',
    'src/feature.js': 'exports.feature = () => true;\n',
    'src/main.js': 'exports.legacy = () => true;\n'
  });
  t.after(() => removeProject(exportsRoot));
  const exportsSession = admitChange({ projectDirectory: exportsRoot, request, scope: 'src/root.js' });
  assert.equal(exportsSession.verdict, 'PASS');
  assert.deepEqual(exportsSession.details.repositoryEvidence.executionPaths, ['src/root.js']);
  assert.equal(exportsSession.details.repositoryEvidence.canonicalSsot.path, 'src/root.js');

  const wildcard = makeProject({
    'package.json': JSON.stringify({ name: 'wildcard-only', exports: { './feature': './src/feature.js' } }),
    'src/feature.js': 'exports.feature = () => true;\n'
  });
  t.after(() => removeProject(wildcard));
  const wildcardSession = admitChange({ projectDirectory: wildcard, request, scope: 'src/feature.js' });
  assert.equal(wildcardSession.details.repositoryEvidence.executionPaths.length, 0);
  assert.equal(wildcardSession.details.repositoryEvidence.canonicalSsot, null);
  assert.equal(wildcardSession.verdict, 'INCONCLUSIVE');
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
