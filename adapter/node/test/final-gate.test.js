'use strict';

const assert = require('node:assert/strict');
const childProcess = require('node:child_process');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const { gateProject } = require('..');
const { captureSourceState } = require('../src/fast-diagnosis');

const cliPath = path.join(__dirname, '..', 'src', 'cli.js');
const THRESHOLDS = Object.freeze({
  maxComplexity: 10,
  maxDepth: 2,
  maxFanIn: 10,
  maxFanOut: 10,
  maxFileLines: 300,
  maxFunctionLines: 50,
  maxReexports: 10
});
const SEMANTIC_REQUIREMENTS = Object.freeze([
  ['b-1-error-handling-and-fallbacks', 'b-1'],
  ['b-2-depth-necessity', 'b-2'],
  ['c-1-replacement-duplication', 'c-1'],
  ['c-2-silent-error-swallowing', 'c-2'],
  ['c-3-hidden-coupling', 'c-3'],
  ['c-4-reexport-ssot-consistency', 'c-4']
]);

function makeProject(files) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-final-gate-'));
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

function cleanProject(source = 'export const answer: number = 42;\n') {
  return {
    'package.json': JSON.stringify({ name: 'final-gate-fixture', main: 'src/index.ts' }),
    'tsconfig.json': JSON.stringify({ compilerOptions: { strict: true } }),
    'src/index.ts': source
  };
}

function gateEvidence(directory, options = {}) {
  const policyId = 'fixture-policy';
  const preChangeId = 'fixture-pre-change';
  const impactScopeId = 'fixture-impact-scope';
  const sourcePath = options.sourcePath || 'src/index.ts';
  const binding = { policyId, preChangeId, impactScopeId };
  const state = captureSourceState(directory);
  const semanticJudgments = SEMANTIC_REQUIREMENTS.map(([id, category]) => ({
    id,
    category,
    verdict: 'PASS',
    rule: `Reviewed ${id}`,
    evidence: [{ path: sourcePath, line: 1, column: 1 }],
    binding
  }));

  return {
    policy: {
      kind: 'fixed-wp001-policy',
      id: policyId,
      source: 'fixture WP-001 admission',
      projectRoot: directory,
      boundaryEvidence: {
        kind: 'fixed-observed-boundaries',
        source: 'fixture pre-change observation',
        projectRoot: directory,
        allowedDependencies: options.allowedDependencies || []
      },
      repositoryAuthority: {
        executionPaths: [sourcePath],
        canonicalSsot: { path: sourcePath }
      },
      thresholds: { ...THRESHOLDS, ...(options.thresholds || {}) }
    },
    preChange: {
      kind: 'fixed-pre-change-source-state',
      id: preChangeId,
      source: 'fixture pre-change readback',
      projectRoot: directory,
      sourceReadback: state,
      violations: options.violations || []
    },
    impactScope: {
      kind: 'fixed-impact-scope',
      id: impactScopeId,
      source: 'fixture fixed changed-module and dependency impact scope',
      projectRoot: directory,
      entries: options.scope || [{ mode: 'subtree', path: 'src' }]
    },
    semanticJudgments
  };
}

function category(result, id) {
  const value = result.categories.find((item) => item.id === id);
  assert.ok(value, `missing category ${id}`);
  return value;
}

function mechanical(result, id) {
  const value = result.details.mechanical.checks.find((item) => item.id === id);
  assert.ok(value, `missing mechanical check ${id}`);
  return value;
}

function semantic(evidence, id) {
  const value = evidence.semanticJudgments.find((item) => item.id === id);
  assert.ok(value, `missing semantic judgment ${id}`);
  return value;
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

test('final Gate produces a PASS only after all categories, fixed evidence, and semantic judgments pass', (t) => {
  const directory = makeProject(cleanProject());
  t.after(() => removeProject(directory));
  const before = digest(directory);
  const evidence = gateEvidence(directory);

  const result = gateProject(directory, evidence);

  assert.equal(result.kind, 'final-code-and-review-quality-gate');
  assert.equal(result.verdict, 'PASS');
  assert.equal(result.completionApproval, true);
  assert.equal(result.finalCompletion.status, 'APPROVED');
  assert.deepEqual(result.categories.map((item) => item.id), [
    'b-1', 'b-2', 'b-3', 'c-1', 'c-2', 'c-3', 'c-4', 'c-5', 'd-1', 'd-2', 'd-3'
  ]);
  assert.ok(result.categories.every((item) => item.verdict === 'PASS'));
  assert.equal(result.details.mechanical.completionApproval, false);
  assert.equal(result.details.sourceReadback.unchanged, true);
  assert.equal(result.details.sourceReadback.before.digest, result.details.sourceReadback.after.digest);
  assert.equal(result.details.binding.policy.id, 'fixture-policy');
  assert.equal(digest(directory), before);
});

test('final Gate reports clear violations for every required category', (t) => {
  const source = [
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
    'export function large(value: number): number {',
    ...Array.from({ length: 51 }, () => '  // function padding'),
    '  return value;',
    '}',
    'export function swallows(): void {',
    '  try {',
    '    throw new Error("failure");',
    '  } catch (error) {}',
    '}',
    'export function unreachable(): number {',
    '  return 1;',
    '  const neverReached = 2;',
    '}',
    'function unusedPrivate(): number { return 1; }',
    'const unsafe = {} as any;',
    'const converted = unsafe as unknown as { name: string };',
    '// const oldImplementation = true;',
    ...Array.from({ length: 301 }, () => '// file padding'),
    ''
  ].join('\n');
  const files = cleanProject(source);
  files['src/reexports.ts'] = Array.from({ length: 11 }, (_, index) => `export { value${index} } from './reexport-${index}';`).join('\n');
  files['src/fan-out.ts'] = [
    ...Array.from({ length: 11 }, (_, index) => `import { fan${index} } from './fan-${index}';`),
    'export const fanOut = true;'
  ].join('\n');
  files['src/shared.ts'] = 'export const shared = true;\n';
  files['src/cycle-a.ts'] = "import { cycleB } from './cycle-b';\nexport const cycleA = cycleB;\n";
  files['src/cycle-b.ts'] = "import { cycleA } from './cycle-a';\nexport const cycleB = cycleA;\n";
  for (let index = 0; index < 11; index += 1) {
    files[`src/reexport-${index}.ts`] = `export const value${index} = ${index};\n`;
    files[`src/fan-${index}.ts`] = `export const fan${index} = ${index};\n`;
    files[`src/fan-in-${index}.ts`] = `import { shared } from './shared';\nexport const fanIn${index} = shared;\n`;
  }
  const directory = makeProject(files);
  t.after(() => removeProject(directory));
  const before = digest(directory);
  const evidence = gateEvidence(directory, {
    allowedDependencies: [{ from: 'src', to: 'src' }]
  });
  for (const judgment of evidence.semanticJudgments) {
    judgment.verdict = 'FAIL';
    judgment.falsifier = 'A direct source-level review showing no violation would disprove this judgment.';
  }

  const result = gateProject(directory, evidence);

  assert.equal(result.verdict, 'FAIL');
  for (const id of ['b-1', 'b-2', 'b-3', 'c-1', 'c-2', 'c-3', 'c-4', 'c-5', 'd-1', 'd-2', 'd-3']) {
    assert.equal(category(result, id).verdict, 'FAIL', id);
  }
  assert.equal(mechanical(result, 'empty-catch').verdict, 'FAIL');
  assert.equal(mechanical(result, 're-export-concentration').verdict, 'FAIL');
  assert.equal(mechanical(result, 'fan-in-concentration').verdict, 'FAIL');
  assert.equal(mechanical(result, 'fan-out-concentration').verdict, 'FAIL');
  assert.equal(mechanical(result, 'circular-dependencies').verdict, 'FAIL');
  assert.equal(digest(directory), before);
});

test('missing, malformed, and conflicting semantic judgments fail closed as INCONCLUSIVE', (t) => {
  const directory = makeProject(cleanProject());
  t.after(() => removeProject(directory));
  const before = digest(directory);

  const missing = gateEvidence(directory);
  missing.semanticJudgments = missing.semanticJudgments.filter((item) => item.id !== 'b-1-error-handling-and-fallbacks');
  const missingResult = gateProject(directory, missing);
  assert.equal(missingResult.verdict, 'INCONCLUSIVE');
  assert.equal(category(missingResult, 'b-1').semantic[0].verdict, 'INCONCLUSIVE');

  const malformed = gateEvidence(directory);
  const malformedFail = semantic(malformed, 'c-3-hidden-coupling');
  malformedFail.verdict = 'FAIL';
  delete malformedFail.falsifier;
  const malformedResult = gateProject(directory, malformed);
  assert.equal(malformedResult.verdict, 'INCONCLUSIVE');
  assert.equal(category(malformedResult, 'c-3').semantic[0].verdict, 'INCONCLUSIVE');

  const conflicting = gateEvidence(directory);
  const conflict = clone(semantic(conflicting, 'c-3-hidden-coupling'));
  conflict.verdict = 'FAIL';
  conflict.falsifier = 'A source review showing no hidden coupling would disprove this judgment.';
  conflicting.semanticJudgments.push(conflict);
  const conflictingResult = gateProject(directory, conflicting);
  assert.equal(conflictingResult.verdict, 'INCONCLUSIVE');
  assert.equal(category(conflictingResult, 'c-3').semantic[0].verdict, 'INCONCLUSIVE');
  assert.equal(digest(directory), before);
});

test('fixed policy thresholds can strengthen defaults but cannot loosen them', (t) => {
  const tightenedDirectory = makeProject(cleanProject([
    'export const first: number = 1;',
    'export const second: number = 2;',
    'export const third: number = 3;',
    ''
  ].join('\n')));
  const loosenedDirectory = makeProject(cleanProject([
    ...Array.from({ length: 301 }, (_, index) => `export const value${index}: number = ${index};`),
    ''
  ].join('\n')));
  t.after(() => removeProject(tightenedDirectory));
  t.after(() => removeProject(loosenedDirectory));

  const tightened = gateProject(tightenedDirectory, gateEvidence(tightenedDirectory, {
    thresholds: { maxFileLines: 2 }
  }));
  assert.equal(tightened.verdict, 'FAIL');
  assert.equal(mechanical(tightened, 'file-size').threshold.effective, 2);
  assert.equal(mechanical(tightened, 'file-size').threshold.source, 'fixed-policy.thresholds.maxFileLines');

  const loosened = gateProject(loosenedDirectory, gateEvidence(loosenedDirectory, {
    thresholds: { maxFileLines: 999 }
  }));
  assert.equal(loosened.verdict, 'FAIL');
  assert.equal(mechanical(loosened, 'file-size').threshold.effective, 300);
  assert.equal(mechanical(loosened, 'file-size').threshold.source, 'checker-default');
});

test('unavailable mechanical capability keeps a complete final Gate INCONCLUSIVE', (t) => {
  const directory = makeProject(cleanProject());
  t.after(() => removeProject(directory));
  const evidenceDirectory = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-final-gate-unavailable-'));
  const evidencePath = path.join(evidenceDirectory, 'gate-evidence.json');
  fs.writeFileSync(evidencePath, JSON.stringify(gateEvidence(directory)));
  t.after(() => removeProject(evidenceDirectory));

  const result = childProcess.spawnSync(
    process.execPath,
    [cliPath, 'gate', '--details', '--evidence', evidencePath, directory],
    { encoding: 'utf8', env: { ...process.env, NODE_PATH: '' } }
  );

  assert.equal(result.status, 2, result.stderr);
  const details = JSON.parse(result.stdout);
  assert.equal(details.verdict, 'INCONCLUSIVE');
  assert.equal(details.mechanical.checks.find((item) => item.id === 'empty-catch').verdict, 'INCONCLUSIVE');
});

test('pre-existing violations outside impact scope are reported without blocking, while impacted violations block', (t) => {
  const unrelatedDirectory = makeProject({
    ...cleanProject(),
    'src/changed.ts': 'export const changed: number = 1;\n',
    'src/unrelated.ts': [
      'export function oldViolation(): void {',
      '  try { throw new Error("old"); } catch (error) {}',
      '}',
      ''
    ].join('\n')
  });
  const impactedDirectory = makeProject({
    ...cleanProject(),
    'src/changed.ts': [
      'export function changedViolation(): void {',
      '  try { throw new Error("changed"); } catch (error) {}',
      '}',
      ''
    ].join('\n'),
    'src/unrelated.ts': [
      'export function oldViolation(): void {',
      '  try { throw new Error("old"); } catch (error) {}',
      '}',
      ''
    ].join('\n')
  });
  t.after(() => removeProject(unrelatedDirectory));
  t.after(() => removeProject(impactedDirectory));

  const unrelatedEvidence = gateEvidence(unrelatedDirectory, {
    sourcePath: 'src/changed.ts',
    scope: [{ mode: 'exact', path: 'src/changed.ts' }],
    violations: [{ checkId: 'empty-catch', path: 'src/unrelated.ts' }]
  });
  const unrelatedResult = gateProject(unrelatedDirectory, unrelatedEvidence);
  assert.equal(unrelatedResult.verdict, 'PASS');
  assert.equal(mechanical(unrelatedResult, 'empty-catch').rawVerdict, 'FAIL');
  assert.equal(mechanical(unrelatedResult, 'empty-catch').verdict, 'PASS');
  assert.deepEqual(unrelatedResult.details.preExisting.unrelated, [{
    checkId: 'empty-catch',
    path: 'src/unrelated.ts',
    observedNow: true
  }]);

  const impactedEvidence = gateEvidence(impactedDirectory, {
    sourcePath: 'src/changed.ts',
    scope: [{ mode: 'exact', path: 'src/changed.ts' }],
    violations: [
      { checkId: 'empty-catch', path: 'src/changed.ts' },
      { checkId: 'empty-catch', path: 'src/unrelated.ts' }
    ]
  });
  const impactedResult = gateProject(impactedDirectory, impactedEvidence);
  assert.equal(impactedResult.verdict, 'FAIL');
  assert.equal(mechanical(impactedResult, 'empty-catch').verdict, 'FAIL');
  assert.equal(impactedResult.details.preExisting.impacted[0].observedNow, true);
  assert.equal(impactedResult.details.preExisting.unrelated[0].observedNow, true);
});

test('dependency impact expands a fixed changed-module scope before classifying pre-existing violations', (t) => {
  const directory = makeProject({
    ...cleanProject(),
    'src/changed.ts': "import { shared } from './shared';\nexport const changed = shared;\n",
    'src/shared.ts': [
      'export function shared(): void {',
      '  try { throw new Error("old"); } catch (error) {}',
      '}',
      ''
    ].join('\n')
  });
  t.after(() => removeProject(directory));
  const evidence = gateEvidence(directory, {
    sourcePath: 'src/changed.ts',
    allowedDependencies: [{ from: 'src', to: 'src' }],
    scope: [{ mode: 'exact', path: 'src/changed.ts' }],
    violations: [{ checkId: 'empty-catch', path: 'src/shared.ts' }]
  });

  const result = gateProject(directory, evidence);

  assert.equal(result.verdict, 'FAIL');
  assert.ok(result.details.binding.impactScope.effectivePaths.includes('src/shared.ts'));
  assert.deepEqual(result.details.preExisting.impacted, [{
    checkId: 'empty-catch',
    path: 'src/shared.ts',
    observedNow: true
  }]);
});

test('final Gate CLI returns final PASS details and preserves its target source', (t) => {
  const directory = makeProject(cleanProject());
  const evidenceDirectory = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-final-gate-evidence-'));
  const evidencePath = path.join(evidenceDirectory, 'gate-evidence.json');
  fs.writeFileSync(evidencePath, JSON.stringify(gateEvidence(directory)));
  t.after(() => removeProject(directory));
  t.after(() => removeProject(evidenceDirectory));
  const before = digest(directory);

  const result = childProcess.spawnSync(
    process.execPath,
    [cliPath, 'gate', '--details', '--evidence', evidencePath, directory],
    { encoding: 'utf8' }
  );

  assert.equal(result.status, 0, result.stderr);
  const details = JSON.parse(result.stdout);
  assert.equal(details.verdict, 'PASS');
  assert.equal(details.completionApproval, true);
  assert.equal(details.sourceReadback.unchanged, true);
  assert.equal(details.sourceReadback.before.digest, details.sourceReadback.after.digest);
  assert.equal(digest(directory), before);
});
