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

test('resolves aliases using the nearest nested tsconfig and its baseUrl', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'nested-aliases' }),
    'src/index.js': 'module.exports = true;\n',
    'packages/app/tsconfig.json': JSON.stringify({ compilerOptions: { strict: true, baseUrl: '.', paths: { '@/*': ['src/*'] } } }),
    'packages/app/src/index.ts': "import { value } from '@/value';\nexport const result: number = value;\n",
    'packages/app/src/value.ts': 'export const value: number = 1;\n'
  });
  t.after(() => removeProject(directory));

  const result = diagnoseProject(directory);

  assert.equal(result.verdict, 'PASS');
  assert.ok(result.details.dependencyDirection.internalReferences.some((reference) => {
    return reference.path === 'packages/app/src/index.ts' && reference.target === 'packages/app/src/value.ts';
  }));
});

test('merges local tsconfig extends and resolves inherited paths from the declaring config directory', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'extended-aliases', main: 'src/index.js' }),
    'src/index.js': 'module.exports = true;\n',
    'configs/base/tsconfig.json': JSON.stringify({ compilerOptions: { strict: true, baseUrl: 'src', paths: { '@/*': ['*'] } } }),
    'configs/base/src/value.ts': 'export const value: number = 1;\n',
    'packages/app/tsconfig.json': JSON.stringify({ extends: '../../configs/base/tsconfig.json' }),
    'packages/app/src/index.ts': "import { value } from '@/value';\nexport const result: number = value;\n"
  });
  t.after(() => removeProject(directory));

  const result = diagnoseProject(directory);

  assert.equal(result.verdict, 'PASS');
  assert.ok(result.details.dependencyDirection.internalReferences.some((reference) => {
    return reference.path === 'packages/app/src/index.ts' && reference.target === 'configs/base/src/value.ts';
  }));
});

test('selects the most specific matching TypeScript path pattern', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'specific-paths', main: 'src/index.ts' }),
    'tsconfig.json': JSON.stringify({ compilerOptions: {
      baseUrl: '.',
      paths: {
        '@/*': ['fallback/*'],
        '@app/*': ['specific/*']
      }
    } }),
    'src/index.ts': "import { value } from '@app/value';\nexport const result: number = value;\n",
    'fallback/app/value.ts': 'export const value = 0;\n',
    'specific/value.ts': 'export const value = 1;\n'
  });
  t.after(() => removeProject(directory));

  const result = diagnoseProject(directory);

  assert.equal(result.verdict, 'PASS');
  assert.ok(result.details.dependencyDirection.internalReferences.some((reference) => {
    return reference.path === 'src/index.ts' && reference.target === 'specific/value.ts';
  }));
});

test('fails closed for a cycle in a local tsconfig extends chain', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'cyclic-tsconfig', main: 'src/index.js' }),
    'src/index.js': 'module.exports = true;\n',
    'packages/app/tsconfig.json': JSON.stringify({ extends: '../base/tsconfig.json', compilerOptions: { strict: true } }),
    'packages/base/tsconfig.json': JSON.stringify({ extends: '../app/tsconfig.json', compilerOptions: { baseUrl: '.' } }),
    'packages/app/src/index.ts': 'export const value: number = 1;\n'
  });
  t.after(() => removeProject(directory));

  const result = diagnoseProject(directory);

  assert.equal(result.verdict, 'INCONCLUSIVE');
  assert.ok(result.risks.some((risk) => risk.code === 'required-invalid-tsconfig.json'));
});

test('fails closed when a tsconfig extends an external symlink under ignored node_modules', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'external-extends-symlink', main: 'src/index.js' }),
    'src/index.js': 'module.exports = true;\n',
    'packages/app/tsconfig.json': JSON.stringify({ extends: '../../node_modules/shared/tsconfig.json' }),
    'packages/app/src/index.ts': 'export const value: number = 1;\n'
  });
  const linkedConfig = path.join(directory, 'node_modules', 'shared', 'tsconfig.json');
  fs.mkdirSync(path.dirname(linkedConfig), { recursive: true });
  fs.symlinkSync(path.join(__dirname, '..', 'package.json'), linkedConfig);
  t.after(() => removeProject(directory));

  const result = diagnoseProject(directory);

  assert.equal(result.verdict, 'INCONCLUSIVE');
  assert.ok(result.risks.some((risk) => risk.code === 'required-unsupported-tsconfig.json'));
});

test('resolves a valid baseUrl-only import and leaves a missing baseUrl fallback external', (t) => {
  const valid = makeProject({
    'package.json': JSON.stringify({ name: 'baseurl-only' }),
    'tsconfig.json': JSON.stringify({ compilerOptions: { strict: true, baseUrl: 'src' } }),
    'src/index.ts': "import { value } from 'shared';\nexport const result: number = value;\n",
    'src/shared.ts': 'export const value: number = 1;\n'
  });
  const external = makeProject({
    'package.json': JSON.stringify({ name: 'external-baseurl', dependencies: { react: '^1.0.0' } }),
    'tsconfig.json': JSON.stringify({ compilerOptions: { strict: true, baseUrl: 'src' } }),
    'src/index.ts': "import React from 'react';\nexport const result = React;\n"
  });
  t.after(() => removeProject(valid));
  t.after(() => removeProject(external));

  const validResult = diagnoseProject(valid);
  const externalResult = diagnoseProject(external);

  assert.equal(validResult.verdict, 'PASS');
  assert.equal(externalResult.verdict, 'PASS');
  assert.ok(externalResult.details.dependencyDirection.externalImports.some((item) => item.specifier === 'react'));
});

test('reports a missing explicit paths mapping as an unresolved alias', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'broken-explicit-alias' }),
    'tsconfig.json': JSON.stringify({ compilerOptions: { strict: true, paths: { '@/*': ['src/*'] } } }),
    'src/index.ts': "import { value } from '@/missing';\nexport const result: number = value;\n"
  });
  t.after(() => removeProject(directory));

  const result = diagnoseProject(directory);

  assert.equal(result.verdict, 'FAIL');
  assert.ok(result.risks.some((risk) => risk.code === 'unresolved-path-alias'));
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

test('a skipped source symlink makes structural diagnosis INCONCLUSIVE', (t) => {
  const outside = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-diagnosis-symlink-'));
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'symlink-source', main: 'src/index.js' }),
    'src/index.js': 'exports.value = 1;\n'
  });
  fs.writeFileSync(path.join(outside, 'outside.js'), 'exports.outside = true;\n');
  fs.symlinkSync(path.join(outside, 'outside.js'), path.join(directory, 'src', 'linked.js'));
  t.after(() => removeProject(directory));
  t.after(() => removeProject(outside));

  const result = diagnoseProject(directory);

  assert.equal(result.verdict, 'INCONCLUSIVE');
  assert.ok(result.risks.some((risk) => risk.code === 'skipped-symbolic-link' && risk.severity === 'inconclusive'));
});

test('configured missing package execution entry is not reported as PASS', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'missing-entry', main: 'missing.js' }),
    'src/index.js': 'exports.value = 1;\n'
  });
  t.after(() => removeProject(directory));

  const result = diagnoseProject(directory);

  assert.equal(result.verdict, 'INCONCLUSIVE');
  assert.equal(result.details.repositoryAuthority.executionPaths.length, 0);
  assert.equal(result.details.repositoryAuthority.canonicalSsot, null);
  assert.ok(result.risks.some((risk) => risk.code === 'execution-entry-unresolved'));
});

test('root main and bin entries resolve as observed execution paths', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'root-entries', main: 'index.js', bin: 'cli.js' }),
    'index.js': 'exports.value = 1;\n',
    'cli.js': '#!/usr/bin/env node\n'
  });
  t.after(() => removeProject(directory));

  const result = diagnoseProject(directory);

  assert.equal(result.verdict, 'PASS');
  assert.deepEqual(result.details.repositoryAuthority.executionPaths, ['cli.js', 'index.js']);
  assert.equal(result.details.repositoryAuthority.canonicalSsot.path, 'index.js');
});

test('records Node default index.js as the package execution entry when no entry is configured', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'default-entry' }),
    'index.js': 'module.exports = true;\n'
  });
  t.after(() => removeProject(directory));

  const result = diagnoseProject(directory);

  assert.equal(result.verdict, 'PASS');
  assert.deepEqual(result.details.repositoryAuthority.executionPaths, ['index.js']);
  assert.deepEqual(result.details.repositoryAuthority.canonicalSsot, {
    evidence: [{ kind: 'file', path: 'index.js' }],
    path: 'index.js',
    source: 'node-default-entry'
  });
});

test('ignores package export subpath patterns as execution entries', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({
      name: 'wildcard-exports',
      exports: { '.': './index.js', './*': './src/*.js' }
    }),
    'index.js': 'module.exports = true;\n',
    'src/feature.js': 'module.exports = true;\n'
  });
  t.after(() => removeProject(directory));

  const result = diagnoseProject(directory);

  assert.equal(result.verdict, 'PASS');
  assert.deepEqual(result.details.repositoryAuthority.executionPaths, ['index.js']);
  assert.equal(result.details.repositoryAuthority.canonicalSsot.path, 'index.js');
});

test('prefers an unambiguous package-root export over package main for canonical authority', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({
      name: 'exports-over-main',
      main: './main.js',
      exports: { '.': './index.js' }
    }),
    'index.js': 'module.exports = "exports";\n',
    'main.js': 'module.exports = "main";\n'
  });
  t.after(() => removeProject(directory));

  const result = diagnoseProject(directory);

  assert.equal(result.verdict, 'PASS');
  assert.deepEqual(result.details.repositoryAuthority.executionPaths, ['index.js', 'main.js']);
  assert.equal(result.details.repositoryAuthority.canonicalSsot.path, 'index.js');
  assert.equal(result.details.repositoryAuthority.canonicalSsot.source, 'configured-exports-root-entry');
});

test('does not let a shadowed missing main block a valid package-root export', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({
      name: 'exports-shadowed-main',
      exports: './src/index.js',
      main: './missing.js'
    }),
    'src/index.js': 'module.exports = "exports";\n'
  });
  t.after(() => removeProject(directory));

  const result = diagnoseProject(directory);

  assert.equal(result.verdict, 'PASS');
  assert.deepEqual(result.details.repositoryAuthority.executionPaths, ['src/index.js']);
  assert.equal(result.details.repositoryAuthority.canonicalSsot.path, 'src/index.js');
  assert.equal(result.details.repositoryAuthority.canonicalSsot.source, 'configured-exports-root-entry');
  assert.ok(!result.risks.some((risk) => risk.code === 'execution-entry-unresolved'));
});

test('keeps independent bin and module execution failures visible beside a valid root export', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({
      name: 'exports-independent-surfaces',
      exports: './src/index.js',
      main: './missing-main.js',
      bin: './missing-cli.js',
      module: './missing-module.js'
    }),
    'src/index.js': 'module.exports = "exports";\n'
  });
  t.after(() => removeProject(directory));

  const result = diagnoseProject(directory);
  const unresolved = result.risks.find((risk) => risk.code === 'execution-entry-unresolved');

  assert.equal(result.verdict, 'INCONCLUSIVE');
  assert.ok(unresolved);
  assert.ok(unresolved.evidence.some((evidence) => evidence.value === './missing-cli.js'));
  assert.ok(unresolved.evidence.some((evidence) => evidence.value === './missing-module.js'));
  assert.ok(!unresolved.evidence.some((evidence) => evidence.value === './missing-main.js'));
  assert.equal(result.details.repositoryAuthority.canonicalSsot.path, 'src/index.js');
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
