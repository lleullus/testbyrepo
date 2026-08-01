'use strict';

const assert = require('node:assert/strict');
const childProcess = require('node:child_process');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const { diagnoseFastProject } = require('..');

const cliPath = path.join(__dirname, '..', 'src', 'cli.js');

function makeProject(files) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-fast-'));
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
        const contents = fs.readFileSync(absolutePath);
        hash.update(`file\u0000${relativePath}\u0000${contents.length}\u0000`);
        hash.update(contents);
        hash.update('\u0000');
      }
    }
  }

  visit(directory);
  return hash.digest('hex');
}

function fastCheck(result, id) {
  const check = result.checks.find((candidate) => candidate.id === id);
  assert.ok(check, `missing fast check ${id}`);
  return check;
}

function strictProject(source) {
  return {
    'package.json': JSON.stringify({ name: 'fast-fixture' }),
    'tsconfig.json': JSON.stringify({ compilerOptions: { strict: true } }),
    'src/index.ts': source
  };
}

function observedBoundaryEvidence(directory, allowedDependencies = []) {
  return {
    kind: 'fixed-observed-boundaries',
    projectRoot: directory,
    source: 'fixture pre-change observation',
    allowedDependencies
  };
}

test('fast API returns limited PASS evidence for a clean TypeScript fixture without changing source', (t) => {
  const directory = makeProject(strictProject([
    'export function normalize(value: number): number {',
    '  if (value > 0) {',
    '    return value;',
    '  }',
    '  return 0;',
    '}',
    ''
  ].join('\n')));
  t.after(() => removeProject(directory));
  const before = digest(directory);

  const result = diagnoseFastProject(directory, { boundaryEvidence: observedBoundaryEvidence(directory) });

  assert.equal(result.kind, 'limited-fast-definitive-rule-diagnosis');
  assert.equal(result.scope, 'mechanically-decidable-rules-only');
  assert.equal(result.verdict, 'PASS');
  assert.equal(result.completionApproval, false);
  assert.equal(result.finalCompletion.approved, false);
  assert.equal(result.finalCompletion.status, 'NOT_FINAL');
  assert.equal(result.details.sourceReadback.unchanged, true);
  assert.ok(result.checks.every((item) => item.verdict === 'PASS'));
  assert.equal(fastCheck(result, 'typescript-strict').verdict, 'PASS');
  assert.equal(fastCheck(result, 'no-as-any').verdict, 'PASS');
  assert.equal(fastCheck(result, 'no-as-unknown-as').verdict, 'PASS');
  assert.equal(digest(directory), before);
});

test('fast diagnosis is INCONCLUSIVE when fixed observed-boundary evidence is absent', (t) => {
  const directory = makeProject(strictProject('export const answer: number = 42;\n'));
  t.after(() => removeProject(directory));
  const before = digest(directory);

  const result = diagnoseFastProject(directory);
  const boundaryCheck = fastCheck(result, 'fixed-boundaries');

  assert.equal(result.verdict, 'INCONCLUSIVE');
  assert.equal(boundaryCheck.verdict, 'INCONCLUSIVE');
  assert.equal(boundaryCheck.evidence[0].kind, 'boundary-evidence');
  assert.match(boundaryCheck.evidence[0].error, /not.*supplied/);
  assert.equal(digest(directory), before);
});

test('fast AST checks identify each required mechanical violation with source locations', (t) => {
  const largeFunction = [
    'export function large(value: number): number {',
    ...Array.from({ length: 51 }, () => '  // padding'),
    '  return value;',
    '}',
    ''
  ].join('\n');
  const oversizedSource = [
    largeFunction,
    ...Array.from({ length: 301 }, () => '// file padding'),
    'export function deeplyNested(value: number): number {',
    '  if (value > 0) {',
    '    if (value > 1) {',
    '      if (value > 2) {',
    '        return value;',
    '      }',
    '    }',
    '  }',
    '  return 0;',
    '}',
    'export function complex(value: number): number {',
    '  if (value === 1) return 1;',
    '  if (value === 2) return 2;',
    '  if (value === 3) return 3;',
    '  if (value === 4) return 4;',
    '  if (value === 5) return 5;',
    '  if (value === 6) return 6;',
    '  if (value === 7) return 7;',
    '  if (value === 8) return 8;',
    '  if (value === 9) return 9;',
    '  if (value === 10) return 10;',
    '  return 0;',
    '}',
    'export function swallows(): void {',
    '  try {',
    '    throw new Error("failure");',
    '  } catch (error) {}',
    '}',
    'export function returnsEarly(): number {',
    '  return 1;',
    '  const unreachable = 2;',
    '}',
    'function unusedPrivate(): number { return 1; }',
    'const value = {} as any;',
    'const converted = value as unknown as { name: string };',
    '// const oldImplementation = true;',
    ''
  ].join('\n');
  const files = strictProject(oversizedSource);
  files['src/reexports.ts'] = Array.from({ length: 11 }, (_, index) => `export { value${index} } from './reexport-${index}';`).join('\n');
  files['src/fan-out.ts'] = [
    ...Array.from({ length: 11 }, (_, index) => `import { fan${index} } from './fan-${index}';`),
    'export const fanOut = true;'
  ].join('\n');
  files['src/shared.ts'] = 'export const shared = true;\n';
  files['src/cycle-a.ts'] = "import { cycleB } from './cycle-b';\nexport const cycleA = cycleB;\n";
  files['src/cycle-b.ts'] = "import { cycleA } from './cycle-a';\nexport const cycleB = cycleA;\n";
  files['src/application/violates.ts'] = "import { database } from '../infrastructure/database';\nexport const violation = database;\n";
  files['src/infrastructure/database.ts'] = 'export const database = true;\n';
  files['src/no-doc.js'] = 'export function publicContract(value) { return value; }\n';
  for (let index = 0; index < 11; index += 1) {
    files[`src/reexport-${index}.ts`] = `export const value${index} = ${index};\n`;
    files[`src/fan-${index}.ts`] = `export const fan${index} = ${index};\n`;
    files[`src/fan-in-${index}.ts`] = `import { shared } from './shared';\nexport const fanIn${index} = shared;\n`;
  }
  const directory = makeProject(files);
  t.after(() => removeProject(directory));
  const before = digest(directory);

  const result = diagnoseFastProject(directory, {
    boundaryEvidence: {
      kind: 'fixed-observed-boundaries',
      projectRoot: directory,
      source: 'fixture pre-change observation',
      allowedDependencies: [{ from: 'src/application', to: 'src/domain' }]
    }
  });

  for (const id of [
    'empty-catch',
    'max-depth',
    'function-size',
    'file-size',
    'complexity',
    'unreachable-code',
    'dead-code',
    'commented-out-code',
    're-export-concentration',
    'fan-in-concentration',
    'fan-out-concentration',
    'no-as-any',
    'no-as-unknown-as',
    'javascript-jsdoc',
    'circular-dependencies',
    'fixed-boundaries'
  ]) {
    const item = fastCheck(result, id);
    assert.equal(item.verdict, 'FAIL', id);
    assert.ok(item.evidence.every((evidence) => evidence.path && Number.isInteger(evidence.line)), id);
  }
  assert.equal(result.verdict, 'FAIL');
  assert.ok(fastCheck(result, 'fixed-boundaries').evidence.some((evidence) => evidence.path === 'src/application/violates.ts' && evidence.line === 1));
  assert.equal(digest(directory), before);
});

test('fast checks distinguish strict configuration failure, missing configuration, and JavaScript JSDoc compliance', (t) => {
  const nonStrict = makeProject({
    'package.json': JSON.stringify({ name: 'non-strict' }),
    'tsconfig.json': JSON.stringify({ compilerOptions: { strict: false } }),
    'src/index.ts': 'export const value: number = 1;\n'
  });
  const missingConfig = makeProject({
    'package.json': JSON.stringify({ name: 'missing-config' }),
    'src/index.ts': 'export const value: number = 1;\n'
  });
  const documentedJavaScript = makeProject({
    'package.json': JSON.stringify({ name: 'documented-javascript' }),
    'src/index.js': [
      '/**',
      ' * Doubles a value.',
      ' * @param {number} value input value',
      ' * @returns {number} doubled value',
      ' */',
      'export function double(value) { return value * 2; }',
      '/**',
      ' * Increments a value.',
      ' * @param {number} value input value',
      ' * @returns {number} incremented value',
      ' */',
      'exports.increment = function increment(value) { return value + 1; };',
      '/** Signals completion. */',
      'export function signal() {}',
      ''
    ].join('\n')
  });
  t.after(() => removeProject(nonStrict));
  t.after(() => removeProject(missingConfig));
  t.after(() => removeProject(documentedJavaScript));

  assert.equal(fastCheck(diagnoseFastProject(nonStrict), 'typescript-strict').verdict, 'FAIL');
  assert.equal(fastCheck(diagnoseFastProject(missingConfig), 'typescript-strict').verdict, 'INCONCLUSIVE');
  const documented = diagnoseFastProject(documentedJavaScript, {
    boundaryEvidence: observedBoundaryEvidence(documentedJavaScript)
  });
  assert.equal(documented.verdict, 'PASS');
  assert.equal(fastCheck(documented, 'javascript-jsdoc').verdict, 'PASS');
});

test('JavaScript JSDoc requires typed parameter and return contracts', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'incomplete-jsdoc' }),
    'src/index.js': [
      '/** Computes a value. */',
      'export function proseOnly(value) { return value; }',
      '/** @param {number} value input value */',
      'export function missingReturn(value) { return value; }',
      '/** @returns {number} output value */',
      'export function missingParameter(value) { return value; }',
      ''
    ].join('\n')
  });
  t.after(() => removeProject(directory));
  const before = digest(directory);

  const result = diagnoseFastProject(directory, {
    boundaryEvidence: observedBoundaryEvidence(directory)
  });
  const jsdocCheck = fastCheck(result, 'javascript-jsdoc');

  assert.equal(result.verdict, 'FAIL');
  assert.equal(jsdocCheck.verdict, 'FAIL');
  assert.ok(jsdocCheck.evidence.every((evidence) => evidence.path === 'src/index.js' && Number.isInteger(evidence.line)));
  assert.deepEqual(
    jsdocCheck.evidence.find((evidence) => evidence.subject === 'proseOnly').missingParameters,
    ['value']
  );
  assert.equal(jsdocCheck.evidence.find((evidence) => evidence.subject === 'missingReturn').missingReturn, true);
  assert.deepEqual(
    jsdocCheck.evidence.find((evidence) => evidence.subject === 'missingParameter').missingParameters,
    ['value']
  );
  assert.equal(digest(directory), before);
});

test('repository thresholds only strengthen defaults and report their effective source', (t) => {
  const tightened = makeProject({
    'package.json': JSON.stringify({
      name: 'tightened-threshold',
      eslintConfig: { rules: { 'max-lines': ['error', 2] } }
    }),
    'src/index.js': 'export const first = 1;\nexport const second = 2;\nexport const third = 3;\n'
  });
  const loosened = makeProject({
    'package.json': JSON.stringify({
      name: 'loosened-threshold',
      eslintConfig: { rules: { 'max-lines': ['error', 999] } }
    }),
    'src/index.js': Array.from({ length: 301 }, (_, index) => `export const value${index} = ${index};`).join('\n')
  });
  t.after(() => removeProject(tightened));
  t.after(() => removeProject(loosened));

  const tightenedResult = diagnoseFastProject(tightened);
  const tightenedCheck = fastCheck(tightenedResult, 'file-size');
  assert.equal(tightenedCheck.verdict, 'FAIL');
  assert.equal(tightenedCheck.threshold.effective, 2);
  assert.match(tightenedCheck.threshold.source, /package\.json#eslintConfig\.rules\.max-lines/);

  const loosenedResult = diagnoseFastProject(loosened);
  const loosenedCheck = fastCheck(loosenedResult, 'file-size');
  assert.equal(loosenedCheck.verdict, 'FAIL');
  assert.equal(loosenedCheck.threshold.effective, 300);
  assert.equal(loosenedCheck.threshold.source, 'checker-default');
  assert.ok(loosenedCheck.threshold.observed.some((candidate) => candidate.value === 999 && candidate.ignored));
});

test('re-export concentration counts every named re-export specifier in one declaration', (t) => {
  const names = Array.from({ length: 11 }, (_, index) => `value${index}`);
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'named-reexports' }),
    'tsconfig.json': JSON.stringify({ compilerOptions: { strict: true } }),
    'src/reexports.ts': `export { ${names.join(', ')} } from './values';\n`,
    'src/star.ts': "export * from './values';\n",
    'src/values.ts': names.map((name, index) => `export const ${name} = ${index};`).join('\n')
  });
  t.after(() => removeProject(directory));
  const before = digest(directory);

  const result = diagnoseFastProject(directory, {
    boundaryEvidence: observedBoundaryEvidence(directory, [{ from: 'src', to: 'src' }])
  });
  const reexportCheck = fastCheck(result, 're-export-concentration');

  assert.equal(result.verdict, 'FAIL');
  assert.equal(reexportCheck.verdict, 'FAIL');
  const namedEvidence = reexportCheck.evidence.filter((evidence) => evidence.path === 'src/reexports.ts');
  assert.equal(namedEvidence.length, 11);
  assert.ok(namedEvidence.every((evidence) => evidence.line === 1 && evidence.reexports === 11));
  assert.ok(reexportCheck.evidence.some((evidence) => evidence.path === 'src/star.ts' && evidence.reexports === 'unbounded'));
  assert.equal(digest(directory), before);
});

test('unsupported configuration and a missing parser capability fail closed as INCONCLUSIVE', (t) => {
  const unsupportedConfig = makeProject({
    'package.json': JSON.stringify({ name: 'unsupported-config' }),
    'eslint.config.js': 'export default [];\n',
    'src/index.js': 'export const value = 1;\n'
  });
  const parserTarget = makeProject({
    'package.json': JSON.stringify({ name: 'parser-capability' }),
    'src/index.js': 'export const value = 1;\n'
  });
  t.after(() => removeProject(unsupportedConfig));
  t.after(() => removeProject(parserTarget));

  const unsupportedResult = diagnoseFastProject(unsupportedConfig);
  assert.equal(fastCheck(unsupportedResult, 'file-size').verdict, 'INCONCLUSIVE');
  assert.equal(unsupportedResult.verdict, 'INCONCLUSIVE');

  const script = [
    "const Module = require('node:module');",
    'const load = Module._load;',
    "Module._load = function(request, parent, isMain) { if (request === '@babel/parser') throw new Error('forced parser unavailability'); return load.call(this, request, parent, isMain); };",
    `const { diagnoseFastProject } = require(${JSON.stringify(path.join(__dirname, '..'))});`,
    'const result = diagnoseFastProject(process.argv[1]);',
    'process.stdout.write(JSON.stringify(result));'
  ].join(' ');
  const child = childProcess.spawnSync(process.execPath, ['-e', script, parserTarget], {
    encoding: 'utf8',
    env: { ...process.env, NODE_PATH: '' }
  });
  assert.equal(child.status, 0, child.stderr);
  const missingParser = JSON.parse(child.stdout);
  assert.equal(missingParser.verdict, 'INCONCLUSIVE');
  assert.equal(missingParser.checks.find((item) => item.id === 'empty-catch').verdict, 'INCONCLUSIVE');
});

test('fast CLI exposes limited non-final status in concise and detailed output without changing its target', (t) => {
  const directory = makeProject(strictProject('export const answer: number = 42;\n'));
  const evidenceDirectory = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-clean-boundary-evidence-'));
  const evidencePath = path.join(evidenceDirectory, 'boundaries.json');
  fs.writeFileSync(evidencePath, JSON.stringify(observedBoundaryEvidence(directory)));
  t.after(() => removeProject(directory));
  t.after(() => removeProject(evidenceDirectory));
  const before = digest(directory);

  const concise = childProcess.spawnSync(process.execPath, [cliPath, 'fast', '--boundary-evidence', evidencePath, directory], { encoding: 'utf8' });
  const detailed = childProcess.spawnSync(process.execPath, [cliPath, 'fast', '--details', '--boundary-evidence', evidencePath, directory], { encoding: 'utf8' });

  assert.equal(concise.status, 0, concise.stderr);
  assert.match(concise.stdout, /^Fast diagnostic verdict: PASS$/m);
  assert.match(concise.stdout, /^Scope: mechanically-decidable-rules-only$/m);
  assert.match(concise.stdout, /^Completion approval: false$/m);
  assert.equal(detailed.status, 0, detailed.stderr);
  const details = JSON.parse(detailed.stdout);
  assert.equal(details.kind, 'limited-fast-definitive-rule-diagnosis');
  assert.equal(details.completionApproval, false);
  assert.equal(details.finalCompletion.status, 'NOT_FINAL');
  assert.equal(digest(directory), before);
});

test('fast CLI applies supplied fixed boundary evidence without changing its target', (t) => {
  const files = {
    'package.json': JSON.stringify({ name: 'boundary-cli' }),
    'tsconfig.json': JSON.stringify({ compilerOptions: { strict: true } }),
    'src/application/index.ts': "import { database } from '../infrastructure/database';\nexport const value = database;\n",
    'src/infrastructure/database.ts': 'export const database = true;\n'
  };
  const directory = makeProject(files);
  const evidenceDirectory = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-boundary-evidence-'));
  const evidencePath = path.join(evidenceDirectory, 'boundaries.json');
  fs.writeFileSync(evidencePath, JSON.stringify({
    kind: 'fixed-observed-boundaries',
    projectRoot: directory,
    source: 'fixture pre-change observation',
    allowedDependencies: [{ from: 'src/application', to: 'src/domain' }]
  }));
  t.after(() => removeProject(directory));
  t.after(() => removeProject(evidenceDirectory));
  const before = digest(directory);

  const detailed = childProcess.spawnSync(
    process.execPath,
    [cliPath, 'fast', '--details', '--boundary-evidence', evidencePath, directory],
    { encoding: 'utf8' }
  );

  assert.equal(detailed.status, 1, detailed.stderr);
  const details = JSON.parse(detailed.stdout);
  const boundaryCheck = details.checks.find((item) => item.id === 'fixed-boundaries');
  assert.equal(boundaryCheck.verdict, 'FAIL');
  assert.equal(boundaryCheck.evidence[0].path, 'src/application/index.ts');
  assert.equal(boundaryCheck.evidence[0].line, 1);
  assert.equal(digest(directory), before);
});

test('fast API accepts an internal dependency allowed by fixed observed-boundary evidence', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'boundary-pass' }),
    'tsconfig.json': JSON.stringify({ compilerOptions: { strict: true } }),
    'src/application/index.ts': "import { value } from '../domain/value';\nexport const applicationValue = value;\n",
    'src/domain/value.ts': 'export const value = 1;\n'
  });
  t.after(() => removeProject(directory));
  const before = digest(directory);

  const result = diagnoseFastProject(directory, {
    boundaryEvidence: {
      kind: 'fixed-observed-boundaries',
      projectRoot: directory,
      source: 'fixture pre-change observation',
      allowedDependencies: [{ from: 'src/application', to: 'src/domain' }]
    }
  });

  const boundaryCheck = fastCheck(result, 'fixed-boundaries');
  assert.equal(result.verdict, 'PASS');
  assert.equal(boundaryCheck.verdict, 'PASS');
  assert.equal(boundaryCheck.boundaryEvidenceSource, 'fixture pre-change observation');
  assert.equal(digest(directory), before);
});
