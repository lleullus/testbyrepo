'use strict';

const assert = require('node:assert/strict');
const childProcess = require('node:child_process');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const { admitChange } = require('..');

const REQUEST = 'Update the existing value behavior. Keep startup unchanged. If a value is invalid, show an error message.';
const INITIAL_FORMAT = "'use strict';\nexports.format = function format(value) { return value; };\n";
const REVISED_FORMAT = [
  "'use strict';",
  'exports.format = function format(value) {',
  "  if (value === null) { throw new Error('value is required'); }",
  "  if (value === '') { return 'empty'; }",
  "  if (value.length === 1) { return 'single'; }",
  "  return 'value:' + value;",
  '};',
  ''
].join('\n');
const INDEX_WITH_OBSERVABLE_OUTPUT = [
  "'use strict';",
  "const { format } = require('./format');",
  "exports.validate = function validate(value) { return 'checked:' + format(value); };",
  ''
].join('\n');
const INDEX_WITHOUT_MUTATION_TARGET = [
  "'use strict';",
  "const { format } = require('./format');",
  'exports.validate = function validate(value) { return format(value); };',
  ''
].join('\n');

function makeProject(files) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-deep-behavior-proof-'));
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

function digest(directory) {
  const hash = crypto.createHash('sha256');
  function visit(currentDirectory) {
    for (const entry of fs.readdirSync(currentDirectory, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name))) {
      const absolutePath = path.join(currentDirectory, entry.name);
      const relativePath = path.relative(directory, absolutePath);
      if (entry.isDirectory()) {
        hash.update(`directory\u0000${relativePath}\u0000`);
        visit(absolutePath);
      } else if (entry.isFile()) {
        hash.update(`file\u0000${relativePath}\u0000`);
        hash.update(fs.readFileSync(absolutePath));
        hash.update('\u0000');
      }
    }
  }
  visit(directory);
  return hash.digest('hex');
}

function testsForIndex(prefix = 'checked:') {
  return [
    "'use strict';",
    "const assert = require('node:assert/strict');",
    "const test = require('node:test');",
    "const { validate } = require('../src/index');",
    `test('empty input returns an observable result', () => { assert.equal(validate(''), '${prefix}empty'); });`,
    "test('null input reports an error', () => { assert.throws(() => validate(null), /value is required/); });",
    `test('boundary values preserve distinct output', () => { assert.equal(validate('a'), '${prefix}single'); assert.equal(validate('ab'), '${prefix}value:ab'); });`,
    ''
  ].join('\n');
}

function testsForFormat() {
  return [
    "'use strict';",
    "const assert = require('node:assert/strict');",
    "const test = require('node:test');",
    "const { format } = require('../src/format');",
    "test('empty input returns an observable result', () => { assert.equal(format(''), 'empty'); });",
    "test('null input reports an error', () => { assert.throws(() => format(null), /value is required/); });",
    "test('boundary values preserve distinct output', () => { assert.equal(format('a'), 'single'); assert.equal(format('ab'), 'value:ab'); });",
    ''
  ].join('\n');
}

function project({ indexSource = INDEX_WITH_OBSERVABLE_OUTPUT, tests = testsForIndex(), extraFiles = {} } = {}) {
  return {
    'package.json': JSON.stringify({
      main: 'src/index.js',
      name: 'deep-behavior-proof-fixture',
      scripts: { test: 'node --test test/index.test.js' }
    }),
    'src/format.js': INITIAL_FORMAT,
    'src/index.js': indexSource,
    'test/index.test.js': tests,
    ...extraFiles
  };
}

function admittedRevision(directory, options = {}) {
  const request = options.request || REQUEST;
  const source = options.source || REVISED_FORMAT;
  const session = admitChange({
    projectDirectory: directory,
    request,
    scope: 'src'
  });
  assert.equal(session.verdict, 'PASS');
  const write = session.attemptWrite({
    request,
    writes: [{ path: 'src/format.js', content: source }]
  });
  assert.equal(write.allowed, true);
  return session;
}

function check(result, id) {
  const item = result.details.checks.find((candidate) => candidate.id === id);
  assert.ok(item, `missing ${id}`);
  return item;
}

test('deep behavior proof executes and mutates every fixed dependency-impact source without changing the target', (t) => {
  const directory = makeProject(project());
  t.after(() => removeProject(directory));
  const session = admittedRevision(directory);
  const before = digest(directory);

  const result = session.behaviorProof({ mode: 'deep' });

  assert.equal(result.kind, 'deep-impact-behavior-proof');
  assert.equal(result.verdict, 'PASS');
  assert.equal(result.details.binding.impactScopeCompleteness, 'PASS');
  assert.equal(result.details.binding.impactScope.kind, 'fixed-impact-scope');
  assert.ok(result.details.binding.impactScope.id);
  assert.match(result.details.binding.impactScope.source, /^WP-002 final-Gate session /);
  assert.deepEqual(result.details.impact.fixedPaths, result.details.binding.impactScope.fixedPaths);
  assert.deepEqual(result.summary.impactSources, ['src/format.js', 'src/index.js']);
  assert.equal(check(result, 'fixed-impact-sources').verdict, 'PASS');
  assert.equal(check(result, 'impact-related-tests').verdict, 'PASS');
  assert.equal(check(result, 'impact-test-execution').verdict, 'PASS');
  assert.equal(check(result, 'impact-mutation-detection').verdict, 'PASS');
  assert.equal(check(result, 'edge-case-regressions').verdict, 'PASS');
  assert.equal(check(result, 'defensive-handling').verdict, 'PASS');
  assert.deepEqual(result.details.testExecution.perSource.map((item) => item.path), ['src/format.js', 'src/index.js']);
  assert.deepEqual(result.details.mutation.perSource.map((item) => [item.path, item.status]), [
    ['src/format.js', 'PASS'],
    ['src/index.js', 'PASS']
  ]);
  assert.ok(result.details.impact.perSource.every((item) => item.tests.includes('test/index.test.js')));
  assert.equal(result.details.sourceReadback.unchanged, true);
  assert.equal(digest(directory), before);
});

test('deep behavior proof rejects a retained wrong failure outcome despite passing impact tests', (t) => {
  const request = 'Update the existing value behavior. Keep startup unchanged. If a value is invalid, show "EXPECTED_FAILURE".';
  const wrongFailureSource = REVISED_FORMAT.replace('value is required', 'WRONG_FAILURE');
  const wrongFailureTests = testsForIndex().replace(
    "assert.throws(() => validate(null), /value is required/)",
    "assert.throws(() => validate(null), /WRONG_FAILURE/)"
  );
  const directory = makeProject(project({ tests: wrongFailureTests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory, { request, source: wrongFailureSource }).behaviorProof({ mode: 'deep' });

  assert.equal(result.details.testExecution.status, 'PASS');
  assert.equal(result.details.edgeCases.categories.find((item) => item.id === 'failure-path').status, 'FAIL');
  assert.notEqual(check(result, 'edge-case-regressions').verdict, 'PASS');
  assert.notEqual(check(result, 'defensive-handling').verdict, 'PASS');
  assert.notEqual(result.verdict, 'PASS');
});

test('deep behavior proof consumes a structured Korean generic error outcome', (t) => {
  const request = '사용자가 값을 수정할 수 있게 하고 기존 시작 동작은 그대로 유지하세요. 실패하면 오류를 보여 주세요.';
  const koreanFailureSource = REVISED_FORMAT.replace('value is required', '오류');
  const koreanFailureTests = testsForIndex().replace('/value is required/', '/오류/');
  const directory = makeProject(project({ tests: koreanFailureTests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory, { request, source: koreanFailureSource }).behaviorProof({ mode: 'deep' });

  assert.equal(result.details.edgeCases.categories.find((item) => item.id === 'failure-path').status, 'PASS');
  assert.equal(check(result, 'edge-case-regressions').verdict, 'PASS');
  assert.equal(check(result, 'defensive-handling').verdict, 'PASS');
  assert.equal(result.verdict, 'PASS');
});

test('deep behavior proof is INCONCLUSIVE when a new product source is admitted outside immutable WP-002 closure', (t) => {
  const directory = makeProject(project());
  t.after(() => removeProject(directory));
  const request = REQUEST;
  const session = admitChange({ projectDirectory: directory, request, scope: 'src' });
  assert.equal(session.verdict, 'PASS');
  const written = session.attemptWrite({
    request,
    writes: [
      { path: 'src/format.js', content: REVISED_FORMAT },
      { path: 'src/new-source.js', content: 'exports.newSource = () => "new";\n' }
    ]
  });
  assert.equal(written.allowed, true);

  const result = session.behaviorProof({ mode: 'deep' });

  assert.equal(result.verdict, 'INCONCLUSIVE');
  assert.ok(result.details.impactSources.uncoveredChangedSources.includes('src/new-source.js'));
  assert.equal(check(result, 'fixed-impact-sources').verdict, 'INCONCLUSIVE');
  assert.notEqual(result.details.binding.impactScope.fixedPaths.includes('src/new-source.js'), true);
});

test('deep behavior proof resolves configured TypeScript aliases in the current closure', (t) => {
  const directory = makeProject(project({
    extraFiles: {
      'tsconfig.json': JSON.stringify({ compilerOptions: { baseUrl: '.', paths: { '@/*': ['shared/*'] } } }),
      'shared/disconnected.js': "exports.extra = function extra(value) { return value; };\n"
    }
  }));
  t.after(() => removeProject(directory));
  const request = REQUEST;
  const session = admitChange({ projectDirectory: directory, request, scope: 'src' });
  assert.equal(session.verdict, 'PASS');
  const revised = [
    "'use strict';",
    "const { extra } = require('@/disconnected');",
    'exports.format = function format(value) { return extra(value); };',
    ''
  ].join('\n');
  const written = session.attemptWrite({
    request,
    writes: [{ path: 'src/format.js', content: revised }]
  });
  assert.equal(written.allowed, true);

  const result = session.behaviorProof({ mode: 'deep' });

  assert.equal(result.verdict, 'INCONCLUSIVE');
  assert.ok(result.details.impactSources.uncoveredReachableSources.includes('shared/disconnected.js'));
  assert.equal(check(result, 'fixed-impact-sources').verdict, 'INCONCLUSIVE');
});

test('deep behavior proof resolves a configured baseUrl internal specifier', (t) => {
  const directory = makeProject(project({
    extraFiles: {
      'tsconfig.json': JSON.stringify({ compilerOptions: { baseUrl: 'shared' } }),
      'shared/disconnected.js': "exports.extra = function extra(value) { return value; };\n"
    }
  }));
  t.after(() => removeProject(directory));
  const request = REQUEST;
  const session = admitChange({ projectDirectory: directory, request, scope: 'src' });
  assert.equal(session.verdict, 'PASS');
  const revised = [
    "'use strict';",
    "const { extra } = require('disconnected');",
    'exports.format = function format(value) { return extra(value); };',
    ''
  ].join('\n');
  const written = session.attemptWrite({
    request,
    writes: [{ path: 'src/format.js', content: revised }]
  });
  assert.equal(written.allowed, true);

  const result = session.behaviorProof({ mode: 'deep' });

  assert.equal(result.verdict, 'INCONCLUSIVE');
  assert.ok(result.details.impactSources.uncoveredReachableSources.includes('shared/disconnected.js'));
});

test('deep behavior proof rejects tsconfig extends through ignored or symlinked paths', (t) => {
  const outside = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-tsconfig-outside-'));
  fs.writeFileSync(path.join(outside, 'base.json'), JSON.stringify({
    compilerOptions: { baseUrl: '.', paths: { '@/*': ['shared/*'] } }
  }));
  const directory = makeProject(project({
    extraFiles: {
      'tsconfig.json': JSON.stringify({ extends: './node_modules/base.json' }),
      'shared/disconnected.js': "exports.extra = function extra(value) { return value; };\n"
    }
  }));
  fs.mkdirSync(path.join(directory, 'node_modules'));
  fs.symlinkSync(path.join(outside, 'base.json'), path.join(directory, 'node_modules', 'base.json'));
  t.after(() => removeProject(directory));
  t.after(() => removeProject(outside));
  const request = REQUEST;
  const session = admitChange({ projectDirectory: directory, request, scope: 'src' });
  assert.equal(session.verdict, 'PASS');
  const revised = [
    "'use strict';",
    "const { extra } = require('@/disconnected');",
    'exports.format = function format(value) { return extra(value); };',
    ''
  ].join('\n');
  const written = session.attemptWrite({
    request,
    writes: [{ path: 'src/format.js', content: revised }]
  });
  assert.equal(written.allowed, true);

  const result = session.behaviorProof({ mode: 'deep' });

  assert.equal(result.verdict, 'INCONCLUSIVE');
  assert.ok(result.details.impactSources.errors.some((error) => /configured TypeScript module/.test(error)));
  assert.equal(result.details.impactSources.uncoveredReachableSources.includes('shared/disconnected.js'), false);
});

test('deep behavior proof is INCONCLUSIVE when one fixed impact source lacks mutation capability', (t) => {
  const directory = makeProject(project({
    indexSource: INDEX_WITHOUT_MUTATION_TARGET,
    tests: testsForIndex('')
  }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof({ mode: 'deep' });

  assert.equal(result.verdict, 'INCONCLUSIVE');
  assert.equal(check(result, 'impact-test-execution').verdict, 'PASS');
  assert.equal(check(result, 'impact-mutation-detection').verdict, 'INCONCLUSIVE');
  assert.deepEqual(result.details.mutation.perSource.map((item) => [item.path, item.status]), [
    ['src/format.js', 'PASS'],
    ['src/index.js', 'INCONCLUSIVE']
  ]);
});

test('deep behavior proof is INCONCLUSIVE when retained tests do not cover every fixed impact source', (t) => {
  const directory = makeProject(project({ tests: testsForFormat() }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof({ mode: 'deep' });

  assert.equal(result.verdict, 'INCONCLUSIVE');
  assert.equal(check(result, 'impact-related-tests').verdict, 'INCONCLUSIVE');
  assert.equal(check(result, 'impact-test-capability').verdict, 'INCONCLUSIVE');
  assert.equal(result.details.testExecution.status, 'NOT_RUN');
  assert.equal(result.details.mutation.status, 'NOT_RUN');
  assert.match(result.details.testSelection.testCapability.reason, /src\/index\.js/);
});

test('deep behavior proof rejects an internal implementation mock anywhere in the impact closure', (t) => {
  const tests = `${testsForIndex()}\n${[
    "const { mock } = require('node:test');",
    "const api = require('../src/index');",
    "test('internal mock is not deep behavioral proof', () => {",
    "  const replacement = mock.method(api, 'validate', () => 'mocked');",
    "  assert.equal(api.validate('anything'), 'mocked');",
    '  replacement.mock.restore();',
    '});',
    ''
  ].join('\n')}`;
  const directory = makeProject(project({ tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof({ mode: 'deep' });

  assert.equal(result.verdict, 'FAIL');
  assert.equal(check(result, 'mock-boundaries').verdict, 'FAIL');
  assert.deepEqual(result.details.mockBoundaries.internal.map((item) => item.target), ['../src/index']);
});

test('deep behavior proof checks an internal mock in an imported non-helper-named module', (t) => {
  const utility = [
    'function replace(object) {',
    '  const original = object.validate;',
    "  Reflect.set(object, 'validate', () => 'mocked');",
    "  const result = object.validate('ok');",
    "  Reflect.set(object, 'validate', original);",
    '  return result;',
    '}',
    'exports.replace = replace;',
    ''
  ].join('\n');
  const tests = `${testsForIndex()}\n${[
    "const api = require('../src/index');",
    "const { replace } = require('../utility');",
    "test('imported utility mock is not deep behavioral proof', () => { assert.equal(replace(api), 'mocked'); });",
    ''
  ].join('\n')}`;
  const directory = makeProject(project({ tests, extraFiles: { 'utility.js': utility } }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof({ mode: 'deep' });

  assert.equal(check(result, 'mock-boundaries').verdict, 'FAIL');
  assert.ok(result.details.mockBoundaries.internal.some((item) => item.target === '../src/index'));
});

test('deep behavior proof fails closed when the final-Gate dependency capability cannot capture a WP-002 scope', () => {
  const script = [
    "const Module = require('node:module');",
    "const assert = require('node:assert/strict');",
    "const fs = require('node:fs');",
    "const os = require('node:os');",
    "const path = require('node:path');",
    "const load = Module._load;",
    "Module._load = function(request, parent, isMain) { if (request === '@babel/parser') throw new Error('forced parser unavailability'); return load.call(this, request, parent, isMain); };",
    `const { admitChange } = require(${JSON.stringify(path.join(__dirname, '..'))});`,
    "const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-deep-basis-'));",
    "try {",
    "  fs.mkdirSync(path.join(directory, 'src'));",
    "  fs.mkdirSync(path.join(directory, 'test'));",
    "  fs.writeFileSync(path.join(directory, 'package.json'), JSON.stringify({ name: 'deep-basis-fixture', main: 'src/index.js', scripts: { test: 'node --test test/index.test.js' } }));",
    "  fs.writeFileSync(path.join(directory, 'src/index.js'), \"exports.validate = function validate(value) { return value; };\\n\");",
    "  fs.writeFileSync(path.join(directory, 'test/index.test.js'), \"const test = require('node:test'); test('retained', () => {});\\n\");",
    `  const request = ${JSON.stringify(REQUEST)};`,
    "  const session = admitChange({ projectDirectory: directory, request, scope: 'src/index.js' });",
    "  assert.equal(session.verdict, 'PASS');",
     "  const write = session.attemptWrite({ request, writes: [{ path: 'src/index.js', content: \"exports.validate = function validate(value) { return 'changed:' + value; };\\n\" }] });",
     "  assert.equal(write.allowed, false);",
    "  const result = session.behaviorProof({ mode: 'deep' });",
    "  assert.equal(result.verdict, 'INCONCLUSIVE');",
    "  assert.equal(result.details.binding.impactScopeCompleteness, 'INCONCLUSIVE');",
    "  assert.equal(result.details.binding.impactScope, null);",
    "  assert.deepEqual(result.details.impact.fixedPaths, []);",
    "  assert.equal(result.details.testExecution.status, 'NOT_RUN');",
    "} finally { fs.rmSync(directory, { force: true, recursive: true }); }"
  ].join('\n');
  const child = childProcess.spawnSync(process.execPath, ['-e', script], {
    cwd: path.join(__dirname, '..'),
    encoding: 'utf8'
  });

  assert.equal(child.status, 0, child.stderr || child.stdout);
});

test('deep behavior proof compares current reachability with the immutable closure when an import reaches existing source', (t) => {
  const directory = makeProject(project({
    extraFiles: { 'node_modules/existing.js': "exports.existing = () => 'existing';\n" }
  }));
  t.after(() => removeProject(directory));
  const session = admitChange({
    projectDirectory: directory,
    request: REQUEST,
    scope: 'src'
  });
  assert.equal(session.verdict, 'PASS');
  const revisedIndex = INDEX_WITH_OBSERVABLE_OUTPUT.replace(
    "const { format } = require('./format');",
    "const { format } = require('./format');\nrequire('../node_modules/existing');"
  );
  const written = session.attemptWrite({
    request: REQUEST,
    writes: [
      { path: 'src/format.js', content: REVISED_FORMAT },
      { path: 'src/index.js', content: revisedIndex }
    ]
  });
  assert.equal(written.allowed, true);

  const result = session.behaviorProof({ mode: 'deep' });

  assert.equal(result.verdict, 'INCONCLUSIVE');
  assert.ok(result.details.impactSources.uncoveredReachableSources.includes('node_modules/existing.js'));
  assert.equal(check(result, 'fixed-impact-sources').verdict, 'INCONCLUSIVE');
});
