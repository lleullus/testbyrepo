'use strict';

const assert = require('node:assert/strict');
const childProcess = require('node:child_process');
const crypto = require('node:crypto');
const net = require('node:net');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const { admitChange } = require('..');

const REQUEST = 'Update the existing value behavior. Keep startup unchanged. If a value is invalid, show an error message.';
const INITIAL_SOURCE = "'use strict';\nexports.validate = function validate(value) { return value; };\n";
const REVISED_SOURCE = [
  "'use strict';",
  'exports.validate = function validate(value) {',
  "  if (value === null) { throw new Error('value is required'); }",
  "  if (value === '') { return 'empty'; }",
  "  if (value.length === 1) { return 'single'; }",
  "  return `value:${value}`;",
  '};',
  ''
].join('\n');

function makeProject(files) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-behavior-proof-'));
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

function behavioralTests(extra = '') {
  return [
    "'use strict';",
    "const assert = require('node:assert/strict');",
    "const test = require('node:test');",
    "const { validate } = require('../src/index');",
    "test('empty input returns an observable result', () => { assert.equal(validate(''), 'empty'); });",
    "test('null input reports an error', () => { assert.throws(() => validate(null), /value is required/); });",
    "test('boundary values preserve distinct output', () => { assert.equal(validate('a'), 'single'); assert.equal(validate('ab'), 'value:ab'); });",
    extra,
    ''
  ].join('\n');
}

function proofProject({ script = 'node --test test/index.test.js', source = INITIAL_SOURCE, tests = behavioralTests(), packageValue = {}, extraFiles = {} } = {}) {
  return {
    'package.json': JSON.stringify({
      main: 'src/index.js',
      name: 'behavior-proof-fixture',
      scripts: script === null ? {} : { test: script },
      ...packageValue
    }),
    'src/index.js': source,
    'test/index.test.js': tests,
    ...extraFiles
  };
}

function admittedRevision(directory, source = REVISED_SOURCE, options = {}) {
  const session = admitChange({
    projectDirectory: directory,
    request: REQUEST,
    scope: options.scope || 'src/index.js'
  });
  assert.equal(session.verdict, 'PASS');
  const write = session.attemptWrite({
    request: REQUEST,
    writes: [{ path: options.path || 'src/index.js', content: source }]
  });
  assert.equal(write.allowed, true);
  return session;
}

function check(result, id) {
  const item = result.details.checks.find((candidate) => candidate.id === id);
  assert.ok(item, `missing ${id}`);
  return item;
}

test('session-bound behavior proof executes related tests and detects a changed-code mutation without changing the target', (t) => {
  const directory = makeProject(proofProject());
  t.after(() => removeProject(directory));
  const session = admittedRevision(directory);
  const before = digest(directory);

  const result = session.behaviorProof();

  assert.equal(result.kind, 'focused-change-behavior-proof');
  assert.equal(result.verdict, 'PASS');
  assert.equal(result.summary.verdict, 'PASS');
  assert.deepEqual(result.summary.changedSources, ['src/index.js']);
  assert.equal(result.details.testExecution.status, 'PASS');
  assert.equal(result.details.mutation.status, 'PASS');
  assert.deepEqual(result.details.testExecution.relatedTests, ['test/index.test.js']);
  assert.deepEqual(result.details.mutation.relatedTests, ['test/index.test.js']);
  assert.ok(result.details.mutation.candidates.some((candidate) => candidate.result.status === 'FAIL'));
  assert.equal(check(result, 'observable-behavior').verdict, 'PASS');
  assert.equal(check(result, 'edge-case-regressions').verdict, 'PASS');
  assert.equal(check(result, 'defensive-handling').verdict, 'PASS');
  assert.equal(result.details.sourceReadback.unchanged, true);
  assert.equal(result.details.binding.qualityObligations.kind, 'fixed-wp002-quality-obligations');
  assert.ok(result.details.binding.qualityObligations.mechanical.includes('empty-catch'));
  assert.ok(result.details.binding.qualityObligations.semantic.includes('c-3-hidden-coupling'));
  assert.equal(digest(directory), before);
});

test('large full replacements stop at the changed-span budget instead of exhausting diff memory', (t) => {
  const initialValue = 'A'.repeat(2_100_000);
  const revisedValue = 'B'.repeat(2_100_000);
  const source = `'use strict';\nexports.validate = function validate(value) { return '${initialValue}'; };\n`;
  const revised = source.replace(initialValue, revisedValue);
  const tests = [
    "'use strict';",
    "const assert = require('node:assert/strict');",
    "const test = require('node:test');",
    "const { validate } = require('../src/index');",
    `test('large result remains observable', () => { assert.equal(validate('ok').length, ${revisedValue.length}); });`,
    ''
  ].join('\n');
  const directory = makeProject(proofProject({ source, tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory, revised).behaviorProof();

  assert.equal(result.details.testExecution.status, 'PASS');
  assert.equal(result.details.mutation.status, 'INCONCLUSIVE');
  assert.equal(result.details.changedSource.files[0].changedRegions[0].budgetExceeded, true);
});

test('asymmetric one-character replacements stop before a quadratic edit frontier', (t) => {
  const replacement = 'B'.repeat(16 * 1024);
  const source = "'use strict';\nexports.validate = function validate(value) { return 'A'; };\n";
  const revised = source.replace("return 'A';", `return '${replacement}';`);
  const tests = [
    "'use strict';",
    "const assert = require('node:assert/strict');",
    "const test = require('node:test');",
    "const { validate } = require('../src/index');",
    `test('asymmetric replacement remains observable', () => { assert.equal(validate('ok').length, ${replacement.length}); });`,
    ''
  ].join('\n');
  const directory = makeProject(proofProject({ source, tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory, revised).behaviorProof();

  assert.equal(result.details.testExecution.status, 'PASS');
  assert.equal(result.details.mutation.status, 'INCONCLUSIVE');
  assert.equal(result.details.changedSource.files[0].changedRegions[0].budgetExceeded, true);
});

test('focused proof admits a proposed baseline written into a clean project', (t) => {
  const directory = makeProject({});
  t.after(() => removeProject(directory));
  const session = admitChange({
    projectDirectory: directory,
    request: REQUEST
  });
  assert.equal(session.verdict, 'PASS');
  assert.equal(session.details.proposedBaseline.status, 'proposed-not-created');
  const write = session.attemptWrite({
    request: REQUEST,
    writes: [
      {
        path: 'package.json',
        content: JSON.stringify({
          main: 'src/index.js',
          name: 'greenfield-behavior-proof-fixture',
          scripts: { test: 'node --test test/index.test.js' }
        })
      },
      { path: 'src/index.js', content: REVISED_SOURCE },
      { path: 'test/index.test.js', content: behavioralTests() }
    ]
  });
  assert.equal(write.allowed, true);

  const result = session.behaviorProof();

  assert.equal(result.verdict, 'PASS');
  assert.deepEqual(result.summary.changedSources, ['src/index.js']);
  assert.equal(result.details.testExecution.status, 'PASS');
  assert.equal(result.details.mutation.status, 'PASS');
  assert.equal(result.details.sourceReadback.unchanged, true);
});

test('disposable proof rejects an escaping symlink in an ignored directory without touching outside state', (t) => {
  const outside = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-proof-outside-'));
  const sentinel = path.join(outside, 'sentinel.txt');
  fs.writeFileSync(sentinel, 'untouched');
  const directory = makeProject(proofProject());
  fs.mkdirSync(path.join(directory, '.cache'));
  fs.symlinkSync(outside, path.join(directory, '.cache', 'escape'), 'dir');
  t.after(() => removeProject(directory));
  t.after(() => removeProject(outside));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(result.verdict, 'INCONCLUSIVE');
  assert.equal(check(result, 'test-execution').verdict, 'INCONCLUSIVE');
  assert.equal(fs.readFileSync(sentinel, 'utf8'), 'untouched');
  assert.equal(fs.existsSync(path.join(outside, 'escape.txt')), false);
});

test('behavior proof rejects unsafe test targets and does not execute lifecycle scripts', (t) => {
  const outside = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-proof-lifecycle-'));
  const marker = path.join(outside, 'marker.txt');
  const directory = makeProject(proofProject({
    script: 'node --test test/index.test.js',
    packageValue: {
      scripts: {
        pretest: `node -e "require('fs').writeFileSync(${JSON.stringify(marker)}, 'pre')"`,
        posttest: `node -e "require('fs').writeFileSync(${JSON.stringify(marker)}, 'post')"`,
        test: 'node --test test/index.test.js'
      }
    }
  }));
  t.after(() => removeProject(directory));
  t.after(() => removeProject(outside));

  const session = admittedRevision(directory);
  const result = session.behaviorProof();

  assert.equal(result.verdict, 'PASS');
  assert.equal(fs.existsSync(marker), false);

  for (const script of [
    'node --test test/index.test.js\nnode -e injected',
    'node --test /tmp/outside.test.js',
    'node --test test/../outside.test.js'
  ]) {
    const unsafeDirectory = makeProject(proofProject({ script }));
    t.after(() => removeProject(unsafeDirectory));
    const unsafe = admittedRevision(unsafeDirectory).behaviorProof();
    assert.equal(unsafe.verdict, 'INCONCLUSIVE');
    assert.equal(check(unsafe, 'test-capability').verdict, 'INCONCLUSIVE');
    assert.equal(unsafe.details.testExecution.status, 'NOT_RUN');
  }
});

test('focused mutation proof only mutates literals in actual changed regions', (t) => {
  const source = `${REVISED_SOURCE}const stable = 'stable';\nconst changed = 'before';\n`;
  const revised = source.replace("const changed = 'before';", "const changed = 'after';");
  const directory = makeProject(proofProject({ source, tests: behavioralTests("test('normal input', () => { assert.equal(validate('normal'), 'value:normal'); });") }));
  t.after(() => removeProject(directory));
  const result = admittedRevision(directory, revised).behaviorProof();

  assert.equal(result.verdict, 'FAIL');
  assert.equal(result.details.mutation.status, 'FAIL');
  assert.ok(result.details.mutation.candidates.every((candidate) => candidate.before !== 'stable'));
  const changedLine = revised.split('\n').findIndex((line) => line.includes("const changed = 'after'")) + 1;
  assert.ok(result.details.mutation.candidates.every((candidate) => candidate.line === changedLine));
});

test('focused mutation proof does not mutate an unchanged condition around a changed branch body', (t) => {
  const source = [
    "'use strict';",
    'exports.validate = function validate(value) {',
    '  if (value) {',
    "    return 'before';",
    '  }',
    "  return 'empty';",
    '};',
    ''
  ].join('\n');
  const revised = source.replace("return 'before';", "return 'after';");
  const tests = [
    "'use strict';",
    "const assert = require('node:assert/strict');",
    "const test = require('node:test');",
    "const { validate } = require('../src/index');",
    "test('changed branch result', () => { assert.equal(validate('normal'), 'after'); });",
    ''
  ].join('\n');
  const directory = makeProject(proofProject({ source, tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory, revised).behaviorProof();
  const changedLine = revised.split('\n').findIndex((line) => line.includes("return 'after'")) + 1;

  assert.equal(result.details.mutation.status, 'PASS');
  assert.ok(result.details.mutation.candidates.every((candidate) => candidate.line === changedLine));
  assert.ok(result.details.mutation.candidates.every((candidate) => candidate.kind !== 'condition'));
});

test('package-root related tests resolve through the package entry', (t) => {
  const tests = behavioralTests().replace("require('../src/index')", "require('..')");
  const directory = makeProject(proofProject({ tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(result.verdict, 'PASS');
  assert.equal(result.details.testSelection.relatedTests[0], 'test/index.test.js');
});

test('edge evidence ignores a false title and requires the actual empty argument', (t) => {
  const tests = behavioralTests().replace(
    "test('empty input returns an observable result', () => { assert.equal(validate(''), 'empty'); });",
    "test('empty input returns an observable result', () => { assert.equal(validate('normal'), 'value:normal'); });"
  );
  const directory = makeProject(proofProject({ tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(check(result, 'edge-case-regressions').verdict, 'FAIL');
  assert.equal(result.details.edgeCases.categories.find((item) => item.id === 'empty-input').status, 'FAIL');
});

test('pre-existing async code does not impose concurrency on an unrelated changed literal', (t) => {
  const source = [
    "'use strict';",
    'async function preExisting(value) { return value; }',
    'exports.validate = function validate(value) { return value; };',
    "const changed = 'before';",
    ''
  ].join('\n');
  const revised = source.replace("const changed = 'before';", "const changed = 'after';");
  const directory = makeProject(proofProject({ source, tests: behavioralTests() }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory, revised).behaviorProof();

  assert.equal(result.details.edgeCases.categories.find((item) => item.id === 'concurrency').status, 'NOT_APPLICABLE');
});

test('two sequential product calls do not count as concurrency evidence', (t) => {
  const source = "'use strict';\nlet state = 0;\nexports.validate = async function validate(value) { state = value; return state; };\n";
  const revised = source.replace('state = value;', 'state = value + 0;');
  const tests = [
    "'use strict';",
    "const assert = require('node:assert/strict');",
    "const test = require('node:test');",
    "const { validate } = require('../src/index');",
    "test('sequential calls', async () => { const first = await validate(1); const second = await validate(2); assert.deepEqual([first, second], [1, 2]); });",
    ''
  ].join('\n');
  const directory = makeProject(proofProject({ source, tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory, revised).behaviorProof();

  assert.equal(result.details.edgeCases.categories.find((item) => item.id === 'concurrency').status, 'FAIL');
});

test('Promise combinators with multiple product calls count as concurrency evidence', (t) => {
  const source = "'use strict';\nlet state = 0;\nexports.validate = async function validate(value) { state = value; return state; };\n";
  const revised = source.replace('state = value;', 'state = value + 0;');
  const tests = [
    "'use strict';",
    "const assert = require('node:assert/strict');",
    "const test = require('node:test');",
    "const { validate } = require('../src/index');",
    "test('concurrent calls', async () => { const results = await Promise.all([validate(1), validate(2)]); assert.deepEqual(results.sort(), [1, 2]); });",
    ''
  ].join('\n');
  const directory = makeProject(proofProject({ source, tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory, revised).behaviorProof();

  assert.equal(result.details.edgeCases.categories.find((item) => item.id === 'concurrency').status, 'PASS');
});

test('observability requires a call bound to product source', (t) => {
  const tests = [
    "'use strict';",
    "const assert = require('node:assert/strict');",
    "const test = require('node:test');",
    "require('../src/index');",
    'function localHelper() { return 1; }',
    "test('unrelated assertion', () => { assert.equal(localHelper(), 1); });",
    ''
  ].join('\n');
  const directory = makeProject(proofProject({ tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(check(result, 'observable-behavior').verdict, 'FAIL');
  assert.equal(result.details.observability.behavioral.length, 0);
});

test('observability rejects a discarded product result followed by an unrelated assertion', (t) => {
  const tests = [
    "'use strict';",
    "const assert = require('node:assert/strict');",
    "const test = require('node:test');",
    "const { validate } = require('../src/index');",
    "test('discarded result', () => { validate('normal'); assert.equal(1, 1); });",
    ''
  ].join('\n');
  const directory = makeProject(proofProject({ tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(check(result, 'observable-behavior').verdict, 'FAIL');
  assert.equal(result.details.observability.behavioral.length, 0);
});

test('observability rejects computed source reads outside assertions', (t) => {
  const tests = behavioralTests([
    "const fs = require('node:fs');",
    "test('computed source inspection is not behavior', () => {",
    "  const source = fs['read' + 'FileSync'](require.resolve('../src/index'), 'utf8');",
    "  assert.equal(validate('ok'), 'value:ok');",
    '  assert.ok(source);',
    '});'
  ].join('\n'));
  const directory = makeProject(proofProject({ tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(check(result, 'observable-behavior').verdict, 'FAIL');
  assert.ok(result.details.observability.rejected.some((item) => /read|FileSync|resolve/.test(item.text)));
});

test('dynamic import filesystem aliases are rejected when they inspect product source', (t) => {
  const tests = behavioralTests([
    "test('dynamic source inspection', async () => {",
    "  const fs = await import('node:fs');",
    "  const { readFile } = await import('node:fs/promises');",
    "  const source = fs.readFileSync(require.resolve('../src/index'), 'utf8');",
    "  const promisedSource = await readFile(require.resolve('../src/index'), 'utf8');",
    "  assert.equal(validate('ok'), 'value:ok');",
    '  assert.ok(source && promisedSource);',
    '});'
  ].join('\n'));
  const directory = makeProject(proofProject({ tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(check(result, 'observable-behavior').verdict, 'FAIL');
  assert.ok(result.details.observability.rejected.some((item) => /readFile/.test(item.text)));
});

test('observability rejects Sinon-style internal monkey patches', (t) => {
  const tests = behavioralTests([
    "const api = require('../src/index');",
    "const sinon = { stub(object, name) { const original = object[name]; object[name] = () => 'mocked'; return { restore() { object[name] = original; } }; } };",
    "test('internal Sinon replacement is not behavior', () => {",
    "  const replacement = sinon.stub(api, 'validate');",
    "  assert.equal(api.validate('ok'), 'mocked');",
    '  replacement.restore();',
    '});'
  ].join('\n'));
  const directory = makeProject(proofProject({ tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(check(result, 'mock-boundaries').verdict, 'FAIL');
  assert.ok(result.details.mockBoundaries.internal.some((item) => item.target === '../src/index'));
});

test('mock detection includes an internal monkey patch hidden in an imported helper', (t) => {
  const helper = [
    "const api = require('../src/index');",
    'exports.run = function run() {',
    "  const original = api.validate;",
    "  api.validate = () => 'mocked';",
    "  const result = api.validate('ok');",
    '  api.validate = original;',
    '  return result;',
    '};',
    ''
  ].join('\n');
  const tests = behavioralTests([
    "const { run } = require('./helper');",
    "test('helper internal replacement is not behavior', () => { assert.equal(run(), 'mocked'); });"
  ].join('\n'));
  const directory = makeProject(proofProject({ tests, extraFiles: { 'test/helper.js': helper } }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(check(result, 'mock-boundaries').verdict, 'FAIL');
  assert.ok(result.details.mockBoundaries.internal.some((item) => item.path === 'test/helper.js'));
});

test('proof rejects implementation-only source assertions even when they detect a mutation', (t) => {
  const implementationOnly = [
    "'use strict';",
    "const assert = require('node:assert/strict');",
    "const fs = require('node:fs');",
    "require('../src/index');",
    "const test = require('node:test');",
    "test('source implementation', () => { assert.match(fs.readFileSync(require.resolve('../src/index'), 'utf8'), /return/); });",
    ''
  ].join('\n');
  const directory = makeProject(proofProject({ tests: implementationOnly }));
  t.after(() => removeProject(directory));
  const result = admittedRevision(directory).behaviorProof();

  assert.equal(result.verdict, 'FAIL');
  assert.equal(check(result, 'observable-behavior').verdict, 'FAIL');
  assert.ok(result.details.observability.rejected.length > 0);
});

test('proof permits a mock only when it targets a WP-001-observed external boundary', (t) => {
  const source = [
    "'use strict';",
    "const fs = require('node:fs');",
    'exports.validate = function validate(value) { return value; };',
    ''
  ].join('\n');
  const revised = [
    "'use strict';",
    "const fs = require('node:fs');",
    'exports.validate = function validate(value) {',
    "  if (value === null) { throw new Error('value is required'); }",
    "  if (value === '') { return 'empty'; }",
    "  if (value.length === 1) { return 'single'; }",
    "  return `value:${value}`;",
    '};',
    'exports.record = function record(value) { fs.writeFileSync("ignored", value); return `stored:${value}`; };',
    ''
  ].join('\n');
  const tests = behavioralTests([
    "const { mock } = require('node:test');",
    "const fs = require('node:fs');",
    "test('side effect writes once through the observed filesystem boundary', () => {",
    '  const writes = [];',
    "  const replacement = mock.method(fs, 'writeFileSync', (target, value) => writes.push([target, value]));",
    "  const api = require('../src/index');",
    "  assert.equal(api.record('ok'), 'stored:ok');",
    "  assert.deepEqual(writes, [['ignored', 'ok']]);",
    '  replacement.mock.restore();',
    '});'
  ].join('\n'));
  const directory = makeProject(proofProject({ source, tests }));
  t.after(() => removeProject(directory));
  const result = admittedRevision(directory, revised).behaviorProof();

  assert.equal(result.verdict, 'FAIL');
  assert.equal(check(result, 'mock-boundaries').verdict, 'PASS');
  assert.deepEqual(result.details.mockBoundaries.allowedExternal.map((item) => item.target), ['node:fs']);
});

test('proof blocks an internal module mock even when the unmocked regression cases execute', (t) => {
  const tests = behavioralTests([
    "const { mock } = require('node:test');",
    "const api = require('../src/index');",
    "test('internal mock is not behavioral proof', () => {",
    "  const replacement = mock.method(api, 'validate', () => 'mocked');",
    "  assert.equal(api.validate('anything'), 'mocked');",
    '  replacement.mock.restore();',
    '});'
  ].join('\n'));
  const directory = makeProject(proofProject({ tests }));
  t.after(() => removeProject(directory));
  const result = admittedRevision(directory).behaviorProof();

  assert.equal(result.verdict, 'FAIL');
  assert.equal(check(result, 'mock-boundaries').verdict, 'FAIL');
  assert.deepEqual(result.details.mockBoundaries.internal.map((item) => item.target), ['../src/index']);
});

test('missing repository test capability is INCONCLUSIVE without a fallback command', (t) => {
  const directory = makeProject(proofProject({ script: null }));
  t.after(() => removeProject(directory));
  const result = admittedRevision(directory).behaviorProof();

  assert.equal(result.verdict, 'INCONCLUSIVE');
  assert.equal(check(result, 'test-capability').verdict, 'INCONCLUSIVE');
  assert.equal(result.details.testExecution.status, 'NOT_RUN');
  assert.equal(result.details.mutation.status, 'NOT_RUN');
});

test('a recognized node test command targeting only an unrelated test cannot satisfy related-test execution', (t) => {
  const directory = makeProject(proofProject({
    script: 'node --test test/unrelated.test.js',
    extraFiles: {
      'test/unrelated.test.js': "const test = require('node:test');\ntest('unrelated', () => {});\n"
    }
  }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(result.verdict, 'INCONCLUSIVE');
  assert.equal(check(result, 'directly-related-tests').verdict, 'PASS');
  assert.equal(check(result, 'test-capability').verdict, 'INCONCLUSIVE');
  assert.match(result.details.testSelection.testCapability.reason, /does not explicitly include/);
  assert.equal(result.details.testExecution.status, 'NOT_RUN');
  assert.equal(result.details.mutation.status, 'NOT_RUN');
});

test('source changed outside the admitted write path loses current session authority', (t) => {
  const directory = makeProject(proofProject());
  t.after(() => removeProject(directory));
  const session = admittedRevision(directory);
  fs.writeFileSync(path.join(directory, 'src', 'index.js'), `${REVISED_SOURCE}\n// unauthorized change\n`);

  const result = session.behaviorProof();

  assert.equal(result.verdict, 'INCONCLUSIVE');
  assert.equal(check(result, 'wp001-wp002-binding').verdict, 'INCONCLUSIVE');
  assert.equal(result.details.sourceReadback.authorizationBefore, 'INCONCLUSIVE');
});

test('an unproven added defensive branch remains INCONCLUSIVE instead of being normalized to PASS', (t) => {
  const noFailureRegression = behavioralTests().replace(
    "test('null input reports an error', () => { assert.throws(() => validate(null), /value is required/); });",
    "test('null input is invoked', () => { assert.equal(typeof validate, 'function'); });"
  );
  const directory = makeProject(proofProject({ tests: noFailureRegression }));
  t.after(() => removeProject(directory));
  const result = admittedRevision(directory).behaviorProof();

  assert.notEqual(result.verdict, 'PASS');
  assert.equal(check(result, 'defensive-handling').verdict, 'INCONCLUSIVE');
});

test('forged public policy cannot mint a behavior-proof runner', () => {
  const { createBehaviorProofSession } = require('../src/behavior-proof');
  const api = require('..');

  assert.equal(api.proveBehavior, undefined);
  assert.throws(
    () => createBehaviorProofSession({}, {
      kind: 'fixed-wp002-quality-obligations',
      mechanical: ['empty-catch'],
      semantic: ['c-3-hidden-coupling']
    }),
    /opaque capability/
  );
});

test('sandbox capability hides host control sockets and dangerous devices before tests run', (t) => {
  const tests = behavioralTests([
    "const fs = require('node:fs');",
    "test('sandbox has no host controls', () => {",
    "  assert.equal(fs.existsSync('/run/docker.sock'), false);",
    "  assert.equal(fs.existsSync('/var/run/docker.sock'), false);",
    "  assert.equal(fs.existsSync('/dev/kvm'), false);",
    '});'
  ].join('\n'));
  const directory = makeProject(proofProject({ tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(result.details.testExecution.status, 'PASS');
});

test('sandbox does not expose a Unix socket created under the host HOME', async (t) => {
  const hostHome = process.env.HOME;
  if (!hostHome) {
    t.skip('HOME is unavailable in the host test environment.');
    return;
  }
  const socketDirectory = fs.mkdtempSync(path.join(hostHome, '.node-policy-checker-home-socket-'));
  const socketPath = path.join(socketDirectory, 'host.sock');
  const server = net.createServer();
  t.after(() => removeProject(socketDirectory));
  t.after(() => new Promise((resolve) => server.close(resolve)));
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(socketPath, resolve);
  });

  const tests = behavioralTests([
    "const fs = require('node:fs');",
    "test('host HOME socket is unavailable', () => {",
    `  assert.equal(fs.existsSync(${JSON.stringify(socketPath)}), false);`,
    '});'
  ].join('\n'));
  const directory = makeProject(proofProject({ tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(result.details.testExecution.status, 'PASS');
});

test('disposable bind remains anchored when its pathname is replaced at spawn time', (t) => {
  const tests = behavioralTests([
    "const fs = require('node:fs');",
    "const path = require('node:path');",
    "test('copy remains disposable', () => { fs.writeFileSync(path.join(__dirname, 'escaped.txt'), 'escaped'); });"
  ].join('\n'));
  const directory = makeProject(proofProject({ tests }));
  const outside = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-proof-race-outside-'));
  fs.cpSync(directory, outside, { recursive: true });
  t.after(() => removeProject(directory));
  t.after(() => removeProject(outside));

  const originalSpawnSync = childProcess.spawnSync;
  let swapped = false;
  childProcess.spawnSync = function patchedSpawnSync(command, argumentsList, options) {
    if (command === 'bwrap' && !swapped) {
      const bindIndex = argumentsList.indexOf('--bind');
      const source = bindIndex === -1 ? null : argumentsList[bindIndex + 1];
      if (source && !source.startsWith('/proc/self/fd/')) {
        fs.renameSync(source, `${source}.original`);
        fs.symlinkSync(outside, source, 'dir');
        swapped = true;
      }
    }
    return originalSpawnSync.call(this, command, argumentsList, options);
  };

  let result;
  try {
    result = admittedRevision(directory).behaviorProof();
  } finally {
    childProcess.spawnSync = originalSpawnSync;
  }

  assert.equal(swapped, false);
  assert.equal(fs.existsSync(path.join(outside, 'test', 'escaped.txt')), false);
  assert.equal(result.details.testExecution.status, 'PASS');
});

test('same-line operator changes generate only an operator mutation candidate', (t) => {
  const source = [
    "'use strict';",
    'exports.validate = function validate(value) {',
    "  return value > 1 ? 'high' : 'low';",
    '};',
    ''
  ].join('\n');
  const revised = source.replace('value > 1', 'value /* >= */ >= 1');
  const tests = [
    "'use strict';",
    "const assert = require('node:assert/strict');",
    "const test = require('node:test');",
    "const { validate } = require('../src/index');",
    "test('changed comparison', () => { assert.equal(validate(1), 'high'); });",
    ''
  ].join('\n');
  const directory = makeProject(proofProject({ source, tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory, revised).behaviorProof();
  const candidates = result.details.mutation.candidates;

  assert.equal(result.details.mutation.status, 'PASS');
  assert.ok(candidates.some((candidate) => candidate.kind === 'operator:>=' && candidate.before === '>=' && candidate.after === '>'));
  assert.ok(candidates.every((candidate) => candidate.kind === 'operator:>='));
});

test('exported TypeScript functions retain executable mutation candidates', (t) => {
  const initial = [
    'export function validate(value: string): string {',
    "  return 'before:' + value;",
    '}',
    ''
  ].join('\n');
  const revised = initial.replace("return 'before:'", "return 'after:'");
  const directory = makeProject({
    'package.json': JSON.stringify({
      main: 'src/index.ts',
      name: 'behavior-proof-esm-typescript-fixture',
      scripts: { test: 'node --test test/index.test.mjs' }
    }),
    'tsconfig.json': JSON.stringify({ compilerOptions: { strict: true } }),
    'src/index.ts': initial,
    'test/index.test.mjs': [
      "import assert from 'node:assert/strict';",
      "import test from 'node:test';",
      "import { validate } from '../src/index.ts';",
      "test('exported function result', () => { assert.equal(validate('ok'), 'after:ok'); });",
      ''
    ].join('\n')
  });
  t.after(() => removeProject(directory));
  const session = admitChange({
    projectDirectory: directory,
    request: REQUEST,
    scope: 'src/index.ts'
  });
  assert.equal(session.verdict, 'PASS');
  const write = session.attemptWrite({
    request: REQUEST,
    writes: [{ path: 'src/index.ts', content: revised }]
  });
  assert.equal(write.allowed, true);

  const result = session.behaviorProof();

  assert.equal(result.details.mutation.status, 'PASS');
  assert.ok(result.details.mutation.candidates.some((candidate) => candidate.before === "'after:'"));
});

test('same-line unchanged literals cannot satisfy mutation proof for a changed literal', (t) => {
  const source = [
    "'use strict';",
    'exports.values = function values() {',
    "  return { stable: 'stable', changed: 'before' };",
    '};',
    ''
  ].join('\n');
  const revised = source.replace("changed: 'before'", "changed: 'after'");
  const tests = [
    "'use strict';",
    "const assert = require('node:assert/strict');",
    "const test = require('node:test');",
    "const { values } = require('../src/index');",
    "test('stable value only', () => { assert.equal(values().stable, 'stable'); });",
    ''
  ].join('\n');
  const directory = makeProject(proofProject({ source, tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory, revised).behaviorProof();

  assert.equal(result.details.mutation.status, 'FAIL');
  assert.ok(result.details.mutation.candidates.length > 0);
  assert.ok(result.details.mutation.candidates.every((candidate) => candidate.before === "'after'"));
});

test('independent same-line changes require independent mutation detection', (t) => {
  const source = [
    "'use strict';",
    'exports.values = function values() { return { first: \'before\', second: \'before\' }; };',
    ''
  ].join('\n');
  const revised = source.replace("first: 'before', second: 'before'", "first: 'after', second: 'after'");
  const tests = [
    "'use strict';",
    "const assert = require('node:assert/strict');",
    "const test = require('node:test');",
    "const { values } = require('../src/index');",
    "test('only first changed value is covered', () => { assert.equal(values().first, 'after'); });",
    ''
  ].join('\n');
  const directory = makeProject(proofProject({ source, tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory, revised).behaviorProof();

  assert.equal(result.details.mutation.status, 'FAIL');
  assert.equal(result.verdict, 'FAIL');
  assert.ok(result.details.mutation.candidates.length >= 2);
  assert.ok(result.details.mutation.candidates.some((candidate) => candidate.result.status === 'FAIL'));
  assert.ok(result.details.mutation.candidates.some((candidate) => candidate.result.status === 'PASS'));
});

test('duplicate test titles keep non-behavioral blocks out of edge evidence', (t) => {
  const source = "'use strict';\nexports.validate = function validate(value) { return value; };\n";
  const revised = [
    "'use strict';",
    'exports.validate = function validate(value) {',
    "  if (value === '') { return 'empty'; }",
    '  return value;',
    '};',
    ''
  ].join('\n');
  const tests = [
    "'use strict';",
    "const assert = require('node:assert/strict');",
    "const test = require('node:test');",
    "const { validate } = require('../src/index');",
    "test('duplicate title', () => { assert.equal(validate('normal'), 'normal'); });",
    "test('duplicate title', () => { validate(''); assert.equal(1, 1); });",
    ''
  ].join('\n');
  const directory = makeProject(proofProject({ source, tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory, revised).behaviorProof();

  assert.equal(check(result, 'edge-case-regressions').verdict, 'FAIL');
});

test('callable body changes make input edge cases applicable even when the declaration line is unchanged', (t) => {
  const source = [
    "'use strict';",
    'exports.validate = function validate(value) {',
    '  return value;',
    '};',
    ''
  ].join('\n');
  const revised = source.replace(
    '  return value;',
    "  if (value === null) { throw new Error('value is required'); }\n  return value;"
  );
  const directory = makeProject(proofProject({ tests: behavioralTests(), source }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory, revised).behaviorProof();
  const categories = result.details.edgeCases.categories;

  assert.notEqual(categories.find((item) => item.id === 'empty-input').status, 'NOT_APPLICABLE');
  assert.notEqual(categories.find((item) => item.id === 'null').status, 'NOT_APPLICABLE');
});

test('focused proof resolves an unchanged public entry to a changed helper', (t) => {
  const directory = makeProject(proofProject({
    extraFiles: {
      'src/index.js': "module.exports = require('./helper');\n",
      'src/helper.js': INITIAL_SOURCE
    }
  }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory, REVISED_SOURCE, {
    path: 'src/helper.js',
    scope: 'src/helper.js'
  }).behaviorProof();

  assert.equal(result.details.testExecution.status, 'PASS');
  assert.equal(check(result, 'observable-behavior').verdict, 'PASS');
  assert.equal(check(result, 'edge-case-regressions').verdict, 'PASS');
});

test('observability uses binding identity instead of object-property names', (t) => {
  const tests = [
    "'use strict';",
    "const assert = require('node:assert/strict');",
    "const test = require('node:test');",
    "const { validate } = require('../src/index');",
    "test('unrelated property uses the same spelling', () => { const result = validate(''); assert.equal(({ result: 1 }).result, 1); });",
    ''
  ].join('\n');
  const directory = makeProject(proofProject({ tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(check(result, 'observable-behavior').verdict, 'FAIL');
  assert.equal(result.details.observability.behavioral.length, 0);
});

test('observability fails closed when a product result crosses an unresolved helper', (t) => {
  const tests = [
    "'use strict';",
    "const assert = require('node:assert/strict');",
    "const test = require('node:test');",
    "const { validate } = require('../src/index');",
    'function unresolved(value) { return value; }',
    "test('unresolved result flow', () => { const result = validate(''); assert.equal(unresolved(result), 'empty'); });",
    ''
  ].join('\n');
  const directory = makeProject(proofProject({ tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(check(result, 'observable-behavior').verdict, 'INCONCLUSIVE');
  assert.equal(result.details.observability.behavioral.length, 0);
});

test('observability fails closed when an assigned result flows through an unresolved call', (t) => {
  const tests = [
    "'use strict';",
    "const assert = require('node:assert/strict');",
    "const test = require('node:test');",
    "const { validate } = require('../src/index');",
    'function transform(value) { return value; }',
    "test('transformed result', () => { const result = transform(validate('')); assert.equal(result, 'empty'); });",
    ''
  ].join('\n');
  const directory = makeProject(proofProject({ tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(check(result, 'observable-behavior').verdict, 'INCONCLUSIVE');
  assert.equal(result.details.observability.behavioral.length, 0);
});

test('awaited and deferred Promise.all entries do not count as concurrent product calls', (t) => {
  const source = "'use strict';\nlet state = 0;\nexports.validate = async function validate(value) { state = value; return state; };\n";
  const revised = source.replace('state = value;', 'state = value + 0;');
  const variants = [
    "test('awaited entries', async () => { const results = await Promise.all([await validate(1), await validate(2)]); assert.deepEqual(results, [1, 2]); });",
    "test('deferred entries', async () => { const results = await Promise.all([() => validate(1), () => validate(2)]); assert.equal(results.length, 2); });"
  ];

  for (const body of variants) {
    const tests = [
      "'use strict';",
      "const assert = require('node:assert/strict');",
      "const test = require('node:test');",
      "const { validate } = require('../src/index');",
      body,
      ''
    ].join('\n');
    const directory = makeProject(proofProject({ source, tests }));
    t.after(() => removeProject(directory));
    const result = admittedRevision(directory, revised).behaviorProof();
    assert.notEqual(result.details.edgeCases.categories.find((item) => item.id === 'concurrency').status, 'PASS');
  }
});

test('local assignment and update do not make concurrency applicable', (t) => {
  const source = [
    "'use strict';",
    'exports.validate = function validate(value) {',
    '  let local = 0;',
    '  local = value;',
    '  return local;',
    '};',
    ''
  ].join('\n');
  const revised = source.replace('  local = value;', '  local = value + 0;');
  const tests = [
    "'use strict';",
    "const assert = require('node:assert/strict');",
    "const test = require('node:test');",
    "const { validate } = require('../src/index');",
    "test('local state', () => { assert.equal(validate(1), 1); });",
    ''
  ].join('\n');
  const directory = makeProject(proofProject({ source, tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory, revised).behaviorProof();

  assert.equal(result.details.edgeCases.categories.find((item) => item.id === 'concurrency').status, 'NOT_APPLICABLE');
});

test('computed filesystem reads and internal function toString are rejected as implementation inspection', (t) => {
  const tests = behavioralTests([
    "const fs = require('node:fs');",
    "const method = 'read' + 'FileSync';",
    "const api = require('../src/index');",
    "const modulePath = '../src/index';",
    'const dynamicApi = require(modulePath);',
    "test('computed source inspection', () => { assert.ok(fs[method](require.resolve('../src/index'), 'utf8')); assert.ok(api.validate.toString().includes('validate')); assert.equal(dynamicApi.validate('ok'), 'value:ok'); });"
  ].join('\n'));
  const directory = makeProject(proofProject({ tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(check(result, 'observable-behavior').verdict, 'FAIL');
  assert.ok(result.details.observability.rejected.some((item) => /read|toString/.test(item.text)));
});

test('filesystem source inspection APIs retain aliases and byte-read provenance', (t) => {
  const tests = behavioralTests([
    "const { readFile, openSync, readSync, closeSync } = require('node:fs');",
    "const fs = require('node:fs');",
    'const load = fs.readFileSync;',
    'const open = fs.openSync;',
    'const read = fs.readSync;',
    "const sourcePath = require.resolve('../src/index');",
    "test('aliased source inspection', async () => {",
    "  const source = await new Promise((resolve, reject) => readFile(sourcePath, 'utf8', (error, value) => error ? reject(error) : resolve(value)));",
    '  const descriptor = openSync(sourcePath);',
    '  const bytes = Buffer.alloc(16);',
    '  readSync(descriptor, bytes, 0, bytes.length, 0);',
    '  closeSync(descriptor);',
    "  const assigned = load('/dev/null', 'utf8');",
    '  const assignedDescriptor = open(sourcePath);',
    '  read(assignedDescriptor, bytes, 0, bytes.length, 0);',
    '  closeSync(assignedDescriptor);',
    "  assert.equal(validate('ok'), 'value:ok');",
    '  assert.ok(source && assigned === \'\');',
    '});'
  ].join('\n'));
  const directory = makeProject(proofProject({ tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(check(result, 'observable-behavior').verdict, 'FAIL');
  assert.ok(result.details.observability.rejected.some((item) => /readFile|openSync|readSync/.test(item.text)));
});

test('unresolved source inspection results remain tainted when asserted later', (t) => {
  const tests = behavioralTests([
    "const fs = require('node:fs');",
    "const sourcePath = '../src/index';",
    'function transform(value) { return value; }',
    "test('tainted source result', () => {",
    "  const source = fs.readFileSync(transform(sourcePath), 'utf8');",
    "  assert.equal(validate('ok'), 'value:ok');",
    '  assert.match(source, /return/);',
    '});'
  ].join('\n'));
  const directory = makeProject(proofProject({ tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(check(result, 'observable-behavior').verdict, 'INCONCLUSIVE');
  assert.equal(result.details.observability.behavioral.length, 5);
  assert.ok(result.details.observability.errors.some((error) => /unresolved source inspection target/.test(error.error)));
});

test('aliased node:test mocks and reflective internal writes are rejected', (t) => {
  const tests = behavioralTests([
    "const nodeTest = require('node:test');",
    "const { mock: mocked } = nodeTest;",
    'const method = mocked.method;',
    "const api = require('../src/index');",
    "test('aliased internal replacement', () => { const replacement = method(api, 'validate', () => 'mocked'); assert.equal(api.validate('ok'), 'mocked'); replacement.mock.restore(); });",
    "test('reflective internal replacement', () => { const original = api.validate; Object.defineProperty(api, 'validate', { configurable: true, writable: true, value: () => 'defined' }); Object.assign(api, { validate: () => 'assigned' }); Reflect.set(api, 'validate', () => 'reflected'); api.validate = original; assert.equal(api.validate('ok'), 'value:ok'); });"
  ].join('\n'));
  const directory = makeProject(proofProject({ tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(check(result, 'mock-boundaries').verdict, 'FAIL');
  assert.ok(result.details.mockBoundaries.internal.length >= 4);
});

test('dynamic import node:test mocks are rejected as internal replacements', (t) => {
  const tests = behavioralTests([
    "const api = require('../src/index');",
    "test('dynamic internal replacement', async () => {",
    "  const { mock: testMock } = await import('node:test');",
    "  const replacement = testMock.method(api, 'validate', () => 'mocked');",
    "  assert.equal(api.validate('ok'), 'mocked');",
    '  replacement.mock.restore();',
    '});'
  ].join('\n'));
  const directory = makeProject(proofProject({ tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(check(result, 'mock-boundaries').verdict, 'FAIL');
  assert.ok(result.details.mockBoundaries.internal.some((item) => item.target === '../src/index'));
});

test('ESM imported mutation helpers retain exported function summaries', (t) => {
  const utility = [
    'export function patchFunction(object) {',
    "  const original = object.validate; Reflect.set(object, 'validate', () => 'mocked');",
    "  const result = object.validate('ok'); Reflect.set(object, 'validate', original);",
    '  return result;',
    '}',
    'export const patchConst = (object) => {',
    "  const original = object.validate; Reflect.set(object, 'validate', () => 'mocked');",
    "  const result = object.validate('ok'); Reflect.set(object, 'validate', original);",
    '  return result;',
    '};',
    'export default function patchDefault(object) {',
    "  const original = object.validate; Reflect.set(object, 'validate', () => 'mocked');",
    "  const result = object.validate('ok'); Reflect.set(object, 'validate', original);",
    '  return result;',
    '}',
    ''
  ].join('\n');
  const esmTests = [
    "import assert from 'node:assert/strict';",
    "import test from 'node:test';",
    "import api from '../src/index.js';",
    "import patchDefault, { patchConst, patchFunction } from '../utility.mjs';",
    "test('ESM mutation helpers are not behavior', () => {",
    "  assert.equal(patchFunction(api), 'mocked');",
    "  assert.equal(patchConst(api), 'mocked');",
    "  assert.equal(patchDefault(api), 'mocked');",
    '});',
    ''
  ].join('\n');
  const directory = makeProject(proofProject({
    script: 'node --test test/index.test.js test/esm-helper.test.mjs',
    extraFiles: {
      'test/esm-helper.test.mjs': esmTests,
      'utility.mjs': utility
    }
  }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(check(result, 'mock-boundaries').verdict, 'FAIL');
  assert.ok(result.details.mockBoundaries.internal.filter((item) => item.target === '../src/index.js').length >= 3);
});

test('Reflect.set helper arguments bound to the product module are rejected', (t) => {
  const tests = behavioralTests([
    "const api = require('../src/index');",
    'const replaceInternally = (object, name) => {',
    '  const original = object[name];',
    "  Reflect.set(object, name, () => 'mocked');",
    '  return () => Reflect.set(object, name, original);',
    '};',
    "test('interprocedural internal replacement', () => {",
    "  const restore = replaceInternally(api, 'validate');",
    "  assert.equal(api.validate('x'), 'mocked');",
    '  restore();',
    '});'
  ].join('\n'));
  const directory = makeProject(proofProject({ tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(check(result, 'mock-boundaries').verdict, 'FAIL');
  assert.ok(result.details.mockBoundaries.internal.some((item) => item.target === '../src/index'));
});

test('unresolved product mutation helper arguments fail closed without classifying ordinary calls as mocks', (t) => {
  const factory = "module.exports = () => require('./src/index');\n";
  const tests = behavioralTests([
    "const makeApi = require('../factory');",
    'const replaceInternally = (object, name) => {',
    "  Reflect.set(object, name, () => 'mocked');",
    '};',
    "test('unresolved product replacement', () => { const api = makeApi(); replaceInternally(api, 'validate'); assert.equal(api.validate('x'), 'mocked'); });"
  ].join('\n'));
  const directory = makeProject(proofProject({ tests, extraFiles: { 'factory.js': factory } }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(check(result, 'mock-boundaries').verdict, 'FAIL');
  assert.ok(result.details.mockBoundaries.internal.some((item) => item.target === 'internal:unresolved-product-mutation-target'));
});

test('ordinary local object mutation helpers do not become product mocks', (t) => {
  const tests = behavioralTests([
    'const fill = (object) => {',
    "  Reflect.set(object, 'value', 1);",
    "  return () => Reflect.set(object, 'value', 0);",
    '};',
    "test('local object mutation', () => { const local = {}; const restore = fill(local); assert.equal(local.value, 1); restore(); });"
  ].join('\n'));
  const directory = makeProject(proofProject({ tests }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(check(result, 'mock-boundaries').verdict, 'PASS');
});

test('helper modules outside helper naming conventions remain in the proof closure', (t) => {
  const helper = [
    "const api = require('./src/index');",
    'exports.run = function run() {',
    "  const original = api.validate;",
    "  api.validate = () => 'mocked';",
    "  const result = api.validate('ok');",
    '  api.validate = original;',
    '  return result;',
    '};',
    ''
  ].join('\n');
  const tests = behavioralTests([
    "const { run } = require('../shared');",
    "test('unnamed helper replacement', () => { assert.equal(run(), 'mocked'); });"
  ].join('\n'));
  const directory = makeProject(proofProject({ tests, extraFiles: { 'shared.js': helper } }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(directory).behaviorProof();

  assert.equal(check(result, 'mock-boundaries').verdict, 'FAIL');
  assert.ok(result.details.mockBoundaries.internal.some((item) => item.path === 'shared.js'));
});

test('package-root calls resolve through the configured package main entry', (t) => {
  const tests = behavioralTests().replace("require('../src/index')", "require('..')");
  const directory = makeProject(proofProject({
    packageValue: { main: 'lib/api.js' },
    source: REVISED_SOURCE,
    tests,
    extraFiles: { 'lib/api.js': "module.exports = require('../src/index');\n" }
  }));
  t.after(() => removeProject(directory));

  const result = admittedRevision(
    directory,
    "module.exports = { validate: require('../src/index').validate };\n",
    { path: 'lib/api.js', scope: 'lib' }
  ).behaviorProof();

  assert.equal(result.details.testExecution.status, 'PASS');
  assert.equal(check(result, 'observable-behavior').verdict, 'PASS');
});
