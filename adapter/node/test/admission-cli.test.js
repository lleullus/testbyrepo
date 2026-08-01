'use strict';

const assert = require('node:assert/strict');
const childProcess = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const { admitChange } = require('..');

const cliPath = path.join(__dirname, '..', 'src', 'cli.js');
const PASS_REQUEST = 'Allow people to create a user with a name. Keep existing user lookup unchanged. If a name is empty, show an error message.';

function makeProject(files) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-admission-cli-'));
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
  const files = [];

  function visit(currentDirectory) {
    for (const entry of fs.readdirSync(currentDirectory, { withFileTypes: true })) {
      const absolutePath = path.join(currentDirectory, entry.name);
      if (entry.isDirectory()) {
        visit(absolutePath);
      } else if (entry.isFile()) {
        files.push([path.relative(directory, absolutePath), fs.readFileSync(absolutePath, 'base64')]);
      }
    }
  }

  visit(directory);
  return files.sort((left, right) => left[0].localeCompare(right[0]));
}

function validProject() {
  return {
    'package.json': JSON.stringify({ name: 'cli-fixture-project', main: 'src/index.ts' }),
    'tsconfig.json': JSON.stringify({ compilerOptions: { baseUrl: '.', rootDir: 'src' } }),
    'src/index.ts': "export { createUser } from './application/create-user';\n",
    'src/application/create-user.ts': "import { User } from '../domain/user';\nexport function createUser(name: string): User { return { name }; }\n",
    'src/application/read-user.ts': "import { User } from '../domain/user';\nexport function readUser(user: User): User { return user; }\n",
    'src/domain/user.ts': 'export interface User { name: string }\n'
  };
}

function invoke(...arguments_) {
  return childProcess.spawnSync(process.execPath, [cliPath, ...arguments_], { encoding: 'utf8' });
}

function assertParity(directory, request, expectedExitCode) {
  const concise = invoke('admit', directory, request);
  const detailed = invoke('admit', '--details', directory, request);
  const api = admitChange({ projectDirectory: directory, request });
  const details = JSON.parse(detailed.stdout);

  assert.equal(concise.status, expectedExitCode, concise.stderr);
  assert.equal(detailed.status, expectedExitCode, detailed.stderr);
  assert.deepEqual(
    {
      mainRisks: details.mainRisks,
      selectedResponsibility: details.selectedResponsibility,
      verdict: details.verdict
    },
    {
      mainRisks: api.summary.mainRisks,
      selectedResponsibility: api.summary.selectedResponsibility,
      verdict: api.summary.verdict
    }
  );
  assert.match(concise.stdout, new RegExp(`^Verdict: ${api.summary.verdict}$`, 'm'));
  assert.match(concise.stdout, /^Selected change responsibility:/m);
  assert.match(concise.stdout, /^Main risks:/m);
  for (const risk of api.summary.mainRisks) {
    assert.ok(concise.stdout.includes(risk.message));
  }
  return { api, concise, details };
}

test('admit CLI shows a passing nontechnical preflight with concise/detail parity', (t) => {
  const directory = makeProject(validProject());
  t.after(() => removeProject(directory));
  const before = snapshot(directory);

  const result = assertParity(directory, PASS_REQUEST, 0);

  assert.equal(result.api.verdict, 'PASS');
  assert.equal(result.details.selectedResponsibility.ownerPath, 'src/application');
  assert.match(result.concise.stdout, /^Selected change responsibility: src\/application /m);
  assert.deepEqual(snapshot(directory), before);
});

test('admit CLI exposes unresolved nontechnical questions and returns INCONCLUSIVE', (t) => {
  const directory = makeProject(validProject());
  t.after(() => removeProject(directory));
  const before = snapshot(directory);
  const request = 'Allow people to create a user with a name. Keep existing user lookup unchanged.';

  const result = assertParity(directory, request, 2);

  assert.equal(result.api.verdict, 'INCONCLUSIVE');
  assert.match(result.concise.stdout, /^Unresolved nontechnical questions:$/m);
  assert.match(result.concise.stdout, /What should people see or experience when the request cannot be completed\?/);
  assert.ok(result.details.questions.some((question) => question.includes('people see or experience')));
  assert.deepEqual(snapshot(directory), before);
});

test('admit CLI returns FAIL for repository failures without changing the target', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'cli-broken-project' }),
    'src/index.js': "module.exports = require('./missing');\n"
  });
  t.after(() => removeProject(directory));
  const before = snapshot(directory);
  const request = 'Allow people to see a greeting. Keep existing startup behavior unchanged. If a name is missing, show an error message.';

  const result = assertParity(directory, request, 1);

  assert.equal(result.api.verdict, 'FAIL');
  assert.match(result.concise.stdout, /relative import does not resolve/i);
  assert.deepEqual(snapshot(directory), before);
});

test('admit invalid invocation uses exit code 2 and diagnosis invocation remains compatible', (t) => {
  const directory = makeProject(validProject());
  t.after(() => removeProject(directory));
  const before = snapshot(directory);

  const invalid = invoke('admit', directory);
  assert.equal(invalid.status, 2);
  assert.match(invalid.stderr, /^Usage: node-policy-checker /m);

  const diagnosis = invoke(directory);
  assert.equal(diagnosis.status, 0, diagnosis.stderr);
  assert.match(diagnosis.stdout, /^Verdict: PASS$/m);
  assert.match(diagnosis.stdout, /^Observed source responsibility:/m);
  assert.deepEqual(snapshot(directory), before);
});
