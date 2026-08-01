'use strict';

const assert = require('node:assert/strict');
const childProcess = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const { diagnoseProject } = require('..');

function makeProject(files) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-'));
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
  const files = new Map();

  function visit(currentDirectory) {
    for (const entry of fs.readdirSync(currentDirectory, { withFileTypes: true })) {
      const absolutePath = path.join(currentDirectory, entry.name);
      if (entry.isDirectory()) {
        visit(absolutePath);
      } else if (entry.isFile()) {
        files.set(path.relative(directory, absolutePath), fs.readFileSync(absolutePath));
      }
    }
  }

  visit(directory);
  return files;
}

function validTypeScriptProject() {
  return {
    'package.json': JSON.stringify({
      name: 'fixture-project',
      main: 'src/index.ts',
      scripts: { test: 'node --test' }
    }, null, 2),
    'tsconfig.json': JSON.stringify({
      compilerOptions: { baseUrl: '.', rootDir: 'src' }
    }, null, 2),
    'src/index.ts': "export { createUser } from './application/create-user';\n",
    'src/application/create-user.ts': "import { User } from '../domain/user';\nexport function createUser(name: string): User { return { name }; }\n",
    'src/application/read-user.ts': "import { User } from '../domain/user';\nexport function readUser(user: User): User { return user; }\n",
    'src/domain/user.ts': 'export interface User { name: string }\n'
  };
}

test('diagnoses actual structure with evidence-grounded responsibilities and reuse candidates', (t) => {
  const directory = makeProject(validTypeScriptProject());
  t.after(() => removeProject(directory));
  const before = snapshot(directory);

  const result = diagnoseProject(directory);

  assert.equal(result.verdict, 'PASS');
  assert.deepEqual(result.summary, {
    verdict: result.details.verdict,
    observedResponsibility: result.details.observedResponsibility,
    mainRisks: result.details.mainRisks
  });
  assert.ok(result.details.structure.boundaries.some((boundary) => boundary.path === 'src'));
  assert.ok(result.details.structure.boundaries.some((boundary) => boundary.path === 'src/application'));
  assert.ok(result.details.structure.boundaries.some((boundary) => boundary.path === 'src/domain'));
  assert.ok(result.details.dependencyDirection.internalEdges.some((edge) => edge.from === 'src/application' && edge.to === 'src/domain'));
  assert.ok(result.details.ssotCandidates.some((candidate) => candidate.path === 'package.json'));

  for (const responsibility of result.details.responsibilities) {
    assert.ok(responsibility.evidence.length > 0);
    assert.ok(responsibility.evidence.every((evidence) => evidence.path));
  }

  const reusedDomainModule = result.details.reuseCandidates.find((candidate) => candidate.path === 'src/domain/user.ts');
  assert.equal(reusedDomainModule.observedImportCount, 2);
  assert.ok(reusedDomainModule.symbols.includes('User'));
  assert.ok(reusedDomainModule.evidence.some((evidence) => evidence.kind === 'import'));
  assert.ok(reusedDomainModule.evidence.some((evidence) => evidence.kind === 'symbol' && evidence.symbol === 'User'));
  assert.deepEqual(snapshot(directory), before);
});

test('uses INCONCLUSIVE rather than PASS when required TypeScript configuration is missing', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'missing-tsconfig' }),
    'src/index.ts': 'export const answer = 42;\n'
  });
  t.after(() => removeProject(directory));

  const result = diagnoseProject(directory);

  assert.equal(result.verdict, 'INCONCLUSIVE');
  const risk = result.risks.find((candidate) => candidate.code === 'required-missing-tsconfig.json');
  assert.ok(risk);
  assert.ok(risk.evidence.some((evidence) => evidence.path === 'src/index.ts'));
});

test('does not require a root tsconfig for a configured nested TypeScript fixture', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'nested-typescript-fixture' }),
    'src/index.js': 'module.exports = 42;\n',
    'tests/fixtures/typescript-project/tsconfig.json': JSON.stringify({ compilerOptions: { strict: true } }),
    'tests/fixtures/typescript-project/src/index.ts': 'export const answer: number = 42;\n'
  });
  t.after(() => removeProject(directory));

  const result = diagnoseProject(directory);

  assert.equal(result.verdict, 'PASS');
  assert.equal(result.details.project.tsconfig.status, 'missing');
  assert.ok(!result.risks.some((risk) => risk.code === 'required-missing-tsconfig.json'));
});

test('keeps an unconfigured nested TypeScript source inconclusive with path evidence', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'partially-configured-typescript-fixtures' }),
    'src/index.js': 'module.exports = 42;\n',
    'tests/fixtures/configured/tsconfig.json': JSON.stringify({ compilerOptions: { strict: true } }),
    'tests/fixtures/configured/src/index.ts': 'export const configured: number = 42;\n',
    'tests/fixtures/unconfigured/src/index.ts': 'export const unconfigured: number = 42;\n'
  });
  t.after(() => removeProject(directory));

  const result = diagnoseProject(directory);

  assert.equal(result.verdict, 'INCONCLUSIVE');
  const risk = result.risks.find((candidate) => candidate.code === 'required-missing-tsconfig.json');
  assert.ok(risk);
  assert.ok(risk.evidence.some((evidence) => evidence.path === 'tests/fixtures/unconfigured/src/index.ts'));
});

test('uses INCONCLUSIVE for a TypeScript source with an invalid containing tsconfig', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'invalid-nested-tsconfig' }),
    'src/index.js': 'module.exports = 42;\n',
    'tests/fixtures/typescript-project/tsconfig.json': '{ invalid json',
    'tests/fixtures/typescript-project/src/index.ts': 'export const answer: number = 42;\n'
  });
  t.after(() => removeProject(directory));

  const result = diagnoseProject(directory);

  assert.equal(result.verdict, 'INCONCLUSIVE');
  const risk = result.risks.find((candidate) => candidate.code === 'required-invalid-tsconfig.json');
  assert.ok(risk);
  assert.ok(risk.evidence.some((evidence) => evidence.path === 'tests/fixtures/typescript-project/tsconfig.json'));
  assert.ok(risk.evidence.some((evidence) => evidence.path === 'tests/fixtures/typescript-project/src/index.ts'));
});

test('uses FAIL for an observed unresolved relative import', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'broken-import' }),
    'src/index.js': "module.exports = require('./missing');\n"
  });
  t.after(() => removeProject(directory));

  const result = diagnoseProject(directory);

  assert.equal(result.verdict, 'FAIL');
  const failure = result.risks.find((risk) => risk.code === 'unresolved-relative-import');
  assert.equal(failure.evidence[0].path, 'src/index.js');
  assert.equal(failure.evidence[0].specifier, './missing');
});

test('resolves a relative package-root import through package main', () => {
  const result = diagnoseProject(path.join(__dirname, '..'));

  assert.equal(result.verdict, 'PASS');
  const reference = result.details.dependencyDirection.internalReferences.find((candidate) => {
    return candidate.path === 'test/diagnose.test.js' && candidate.specifier === '..';
  });
  assert.equal(reference.target, 'src/index.js');
  assert.equal(result.details.dependencyDirection.outsideTargetImports.length, 0);
});

test('the direct CLI emits concise and detailed output without changing its target', (t) => {
  const directory = makeProject(validTypeScriptProject());
  t.after(() => removeProject(directory));
  const before = snapshot(directory);
  const cliPath = path.join(__dirname, '..', 'src', 'cli.js');

  const concise = childProcess.spawnSync(process.execPath, [cliPath, directory], { encoding: 'utf8' });
  assert.equal(concise.status, 0, concise.stderr);
  assert.match(concise.stdout, /^Verdict: PASS/m);
  assert.match(concise.stdout, /^Observed source responsibility:/m);
  assert.match(concise.stdout, /^Main risks:/m);

  const detailed = childProcess.spawnSync(process.execPath, [cliPath, '--details', directory], { encoding: 'utf8' });
  assert.equal(detailed.status, 0, detailed.stderr);
  const details = JSON.parse(detailed.stdout);
  assert.equal(details.verdict, 'PASS');
  assert.equal(details.observedResponsibility, diagnoseProject(directory).summary.observedResponsibility);
  assert.deepEqual(snapshot(directory), before);
});
