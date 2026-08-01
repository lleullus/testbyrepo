'use strict';

const assert = require('node:assert/strict');
const childProcess = require('node:child_process');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const HOST_IDENTITIES = [
  ['fixture-reviewer', 'fixture-ai-model'],
  ['stable-reviewer', 'fixture-ai-model'],
  ['replacement-reviewer', 'fixture-ai-model'],
  ['duplicate-reviewer', 'good-model'],
  ['duplicate-reviewer', 'weak-model']
];
const HOST_KEYS = new Map(HOST_IDENTITIES.map(([id, model]) => [`${id}\u0000${model}`, crypto.generateKeyPairSync('ed25519')]));
const hostRegistryDirectory = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-host-registry-'));
const hostRegistryPath = path.join(hostRegistryDirectory, 'reviewers.json');
fs.writeFileSync(hostRegistryPath, JSON.stringify({
  kind: 'node-policy-checker-reviewer-registry',
  reviewers: HOST_IDENTITIES.map(([id, model]) => ({
    id,
    model,
    publicKey: HOST_KEYS.get(`${id}\u0000${model}`).publicKey.export({ format: 'pem', type: 'spki' })
  }))
}), { mode: 0o600 });
fs.chmodSync(hostRegistryPath, 0o600);
const previousRegistryPath = process.env.NODE_POLICY_CHECKER_REVIEWER_REGISTRY;
process.env.NODE_POLICY_CHECKER_REVIEWER_REGISTRY = hostRegistryPath;
const { admitChange, gateProject } = require('..');

const cliPath = path.join(__dirname, '..', 'src', 'cli.js');
const REQUEST = 'Update the existing value behavior. Keep startup unchanged. If the update fails, show an error message.';
const CATEGORY_IDS = ['b-1', 'b-2', 'b-3', 'c-1', 'c-2', 'c-3', 'c-4', 'c-5', 'd-1', 'd-2', 'd-3'];

test.after(() => {
  removeProject(hostRegistryDirectory);
  if (previousRegistryPath === undefined) {
    delete process.env.NODE_POLICY_CHECKER_REVIEWER_REGISTRY;
  } else {
    process.env.NODE_POLICY_CHECKER_REVIEWER_REGISTRY = previousRegistryPath;
  }
});

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

function cleanProject(source = 'export const value: number = 42;\n', main = 'src/index.ts') {
  return {
    'package.json': JSON.stringify({ name: 'final-gate-fixture', main }),
    'tsconfig.json': JSON.stringify({ compilerOptions: { strict: true } }),
    [main]: source
  };
}

function digest(directory) {
  const hash = crypto.createHash('sha256');
  function visit(current) {
    for (const entry of fs.readdirSync(current, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name))) {
      const absolutePath = path.join(current, entry.name);
      const relativePath = path.relative(directory, absolutePath);
      hash.update(`${entry.isDirectory() ? 'directory' : 'file'}\u0000${relativePath}\u0000`);
      if (entry.isDirectory()) {
        visit(absolutePath);
      } else if (entry.isFile()) {
        hash.update(fs.readFileSync(absolutePath));
        hash.update('\u0000');
      }
    }
  }
  visit(directory);
  return hash.digest('hex');
}

function aiReviewer(decide = () => 'PASS', options = {}) {
  const id = options.id || 'fixture-reviewer';
  const model = options.model || 'fixture-ai-model';
  const keyPair = options.untrustedKey
    ? crypto.generateKeyPairSync('ed25519')
    : HOST_KEYS.get(`${id}\u0000${model}`);
  assert.ok(keyPair, `missing host fixture key for ${id}`);
  const publicKey = keyPair.publicKey.export({ format: 'pem', type: 'spki' });
  return {
    kind: 'ai-semantic-reviewer',
    id,
    model,
    publicKey,
    review(request) {
      const decision = decide(request);
      if (decision instanceof Error) {
        throw decision;
      }
      const verdict = typeof decision === 'string' ? decision : decision.verdict;
      const evidencePath = typeof decision === 'object' && decision.path
        ? decision.path
        : options.path || request.impactPaths[0] || 'src/index.ts';
      const judgment = {
        id: request.requirement.id,
        category: request.requirement.category,
        verdict,
        rule: request.requirement.id,
        evidence: [{ path: evidencePath, line: 1, column: 1 }],
        attestation: {
          reviewerId: id,
          model,
          requestDigest: request.requestDigest,
          sourceDigest: request.sourceDigest,
          signature: null
        }
      };
      if (verdict === 'FAIL') {
        judgment.falsifier = 'A source review demonstrating that the stated condition is absent would falsify this finding.';
      }
      judgment.attestation.signature = crypto.sign(
        null,
        Buffer.from(canonicalJson(semanticAttestationPayload(judgment))),
        keyPair.privateKey
      ).toString('base64');
      if (options.mutate) {
        options.mutate(judgment, request);
      }
      return judgment;
    }
  };
}

function hostReviewer(directory, reviewer) {
  setReviewerConfiguration(directory, { id: reviewer.id, model: reviewer.model });
  return reviewer;
}

function setReviewerConfiguration(directory, configuration) {
  const packagePath = path.join(directory, 'package.json');
  const packageValue = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
  packageValue.nodePolicyChecker = {
    ...(packageValue.nodePolicyChecker || {}),
    semanticReviewer: configuration
  };
  fs.writeFileSync(packagePath, JSON.stringify(packageValue));
}

function semanticAttestationPayload(judgment) {
  return {
    reviewerId: judgment.attestation.reviewerId,
    model: judgment.attestation.model,
    requestDigest: judgment.attestation.requestDigest,
    sourceDigest: judgment.attestation.sourceDigest,
    id: judgment.id,
    category: judgment.category,
    verdict: judgment.verdict,
    rule: judgment.rule,
    evidence: judgment.evidence,
    falsifier: judgment.falsifier || null
  };
}

function canonicalJson(value) {
  if (Array.isArray(value)) {
    return `[${value.map(canonicalJson).join(',')}]`;
  }
  if (value !== null && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

function category(result, id) {
  const item = result.categories.find((candidate) => candidate.id === id);
  assert.ok(item, `missing category ${id}`);
  return item;
}

function mechanical(result, id) {
  const item = result.details.mechanical.checks.find((candidate) => candidate.id === id);
  assert.ok(item, `missing mechanical check ${id}`);
  return item;
}

function childGate(directory, registryPath, withCallerReviewer, useRegistryIdentity = false) {
  const script = [
    "const crypto = require('node:crypto');",
    "const fs = require('node:fs');",
    "const path = require('node:path');",
    `const canonicalJson = ${canonicalJson.toString()};`,
    `const semanticAttestationPayload = ${semanticAttestationPayload.toString()};`,
    'const directory = process.argv[1];',
    withCallerReviewer ? [
      "const keyPair = crypto.generateKeyPairSync('ed25519');",
      "const callerPublicKey = keyPair.publicKey.export({ format: 'pem', type: 'spki' });",
      useRegistryIdentity
        ? "const registryReviewer = JSON.parse(fs.readFileSync(process.env.NODE_POLICY_CHECKER_REVIEWER_REGISTRY, 'utf8')).reviewers[0]; const identity = { id: registryReviewer.id, model: registryReviewer.model, publicKey: registryReviewer.publicKey };"
        : "const identity = { id: 'caller-reviewer', model: 'caller-model', publicKey: callerPublicKey };",
      "const packagePath = path.join(directory, 'package.json');",
      "const packageValue = JSON.parse(fs.readFileSync(packagePath, 'utf8'));",
      'packageValue.nodePolicyChecker = { semanticReviewer: { id: identity.id, model: identity.model } };',
      'fs.writeFileSync(packagePath, JSON.stringify(packageValue));',
      "const reviewer = { kind: 'ai-semantic-reviewer', id: identity.id, model: identity.model, publicKey: identity.publicKey, review(request) {",
      "  const judgment = { id: request.requirement.id, category: request.requirement.category, verdict: 'PASS', rule: request.requirement.id, evidence: [{ path: 'src/index.ts', line: 1, column: 1 }], attestation: { reviewerId: identity.id, model: identity.model, requestDigest: request.requestDigest, sourceDigest: request.sourceDigest, signature: null } };",
      "  judgment.attestation.signature = crypto.sign(null, Buffer.from(canonicalJson(semanticAttestationPayload(judgment))), keyPair.privateKey).toString('base64');",
      '  return judgment;',
      '} };'
    ].join(' ') : 'const reviewer = null;',
    `const { admitChange } = require(${JSON.stringify(path.join(__dirname, '..'))});`,
    `const result = admitChange({ projectDirectory: directory, request: ${JSON.stringify(REQUEST)}, scope: 'src/index.ts', ...(reviewer ? { semanticReviewer: reviewer } : {}) }).finalGate();`,
    'process.stdout.write(JSON.stringify(result));'
  ].join(' ');
  const env = { ...process.env };
  if (registryPath === null) {
    delete env.NODE_POLICY_CHECKER_REVIEWER_REGISTRY;
  } else {
    env.NODE_POLICY_CHECKER_REVIEWER_REGISTRY = registryPath;
  }
  return childProcess.spawnSync(process.execPath, ['-e', script, directory], { encoding: 'utf8', env });
}

test('WP-001 session is the only path that can approve all final-Gate categories', (t) => {
  const directory = makeProject(cleanProject());
  t.after(() => removeProject(directory));
  const reviewer = aiReviewer();
  const reviewerCapability = hostReviewer(directory, reviewer);
  const before = digest(directory);
  const session = admitChange({
    projectDirectory: directory,
    request: REQUEST,
    scope: 'src/index.ts',
    semanticReviewer: reviewerCapability
  });

  assert.equal(session.verdict, 'PASS');
  const result = session.finalGate();

  assert.equal(result.verdict, 'PASS');
  assert.equal(result.completionApproval, true);
  assert.equal(result.finalCompletion.status, 'APPROVED');
  assert.deepEqual(result.categories.map((item) => item.id), CATEGORY_IDS);
  assert.ok(result.categories.every((item) => item.verdict === 'PASS'));
  assert.equal(result.details.mechanical.completionApproval, false);
  assert.equal(result.details.sourceReadback.unchanged, true);
  assert.equal(result.details.binding.reviewer.id, 'fixture-reviewer');
  assert.equal(digest(directory), before);
});

test('caller-authored policy, baseline, scope, and semantic PASS values cannot approve the Gate', (t) => {
  const directory = makeProject(cleanProject([
    'export function swallows(): undefined {',
    '  try { throw new Error("failure"); } catch (error) { return undefined; }',
    '}',
    ''
  ].join('\n')));
  t.after(() => removeProject(directory));
  const forged = {
    policy: { id: 'forged' },
    preChange: {
      sourceReadback: { digest: '0'.repeat(64), fileCount: 1 },
      violations: [{ checkId: 'empty-catch', path: 'src/index.ts' }]
    },
    impactScope: { entries: [{ mode: 'exact', path: 'src/index.ts' }] },
    semanticJudgments: [{ verdict: 'PASS', rule: 'ok', evidence: [{ path: 'src/index.ts', line: 1, column: 1 }] }]
  };

  const result = gateProject(directory, forged);

  assert.equal(result.verdict, 'INCONCLUSIVE');
  assert.equal(result.completionApproval, false);
  assert.equal(result.details.finalChecks.find((item) => item.id === 'wp001-binding').verdict, 'INCONCLUSIVE');
});

test('a caller-created repository reviewer key is not a trusted root', (t) => {
  const directory = makeProject(cleanProject());
  t.after(() => removeProject(directory));
  const reviewer = aiReviewer(() => 'PASS', { untrustedKey: true });
  const packagePath = path.join(directory, 'package.json');
  const packageValue = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
  packageValue.nodePolicyChecker = {
    semanticReviewer: { id: reviewer.id, model: reviewer.model, publicKey: reviewer.publicKey }
  };
  fs.writeFileSync(packagePath, JSON.stringify(packageValue));

  const result = admitChange({
    projectDirectory: directory,
    request: REQUEST,
    scope: 'src/index.ts',
    semanticReviewer: reviewer
  }).finalGate();

  assert.equal(result.verdict, 'INCONCLUSIVE');
  assert.equal(result.completionApproval, false);
  assert.equal(result.details.binding.reviewer, null);
});

test('direct internal composition cannot inject a fake diagnosis or mint shaped Gate authority', (t) => {
  const internalGate = require('../src/final-gate');
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'broken-direct-composition' }),
    'src/index.js': "module.exports = require('./missing');\n"
  });
  t.after(() => removeProject(directory));
  let fakeCalls = 0;

  assert.equal(internalGate.createFinalGateSession, undefined);
  assert.equal(Object.isFrozen(require('../src')), true);
  const session = internalGate.createGatedAdmissionSession({
    projectDirectory: directory,
    request: REQUEST,
    scope: 'src/index.js'
  }, () => {
    fakeCalls += 1;
    return { verdict: 'PASS', risks: [], details: {} };
  });

  assert.equal(fakeCalls, 0);
  assert.equal(session.verdict, 'FAIL');
  assert.notEqual(session.finalGate().verdict, 'PASS');
});

test('final Gate executes the pinned AI reviewer instead of accepting caller PASS assertions', (t) => {
  const directory = makeProject(cleanProject());
  t.after(() => removeProject(directory));
  let calls = 0;
  const reviewer = aiReviewer((request) => {
    calls += 1;
    const source = fs.readFileSync(path.join(request.projectRoot, 'src/index.ts'), 'utf8');
    if (request.phase === 'final' && /catch.*return undefined/.test(source) && ['b-1', 'c-2'].includes(request.requirement.category)) {
      return 'FAIL';
    }
    return 'PASS';
  });
  const reviewerCapability = hostReviewer(directory, reviewer);
  const session = admitChange({
    projectDirectory: directory,
    request: REQUEST,
    scope: 'src/index.ts',
    semanticReviewer: reviewerCapability
  });
  const written = session.attemptWrite({
    request: REQUEST,
    writes: [{
      path: 'src/index.ts',
      content: 'export function value(): undefined { try { throw new Error("failure"); } catch (error) { return undefined; } }\n'
    }]
  });

  assert.equal(written.allowed, true);
  const result = session.finalGate();

  assert.ok(calls >= 12, 'reviewer must run at baseline and final phases');
  assert.equal(category(result, 'b-1').verdict, 'FAIL');
  assert.equal(category(result, 'c-2').verdict, 'FAIL');
  assert.equal(result.verdict, 'FAIL');
  assert.equal(result.completionApproval, false);
});

test('missing, throwing, or incorrectly attested reviewer capability is INCONCLUSIVE', (t) => {
  const missingDirectory = makeProject(cleanProject());
  const unpinnedDirectory = makeProject(cleanProject());
  const throwingDirectory = makeProject(cleanProject());
  const attestationDirectory = makeProject(cleanProject());
  t.after(() => removeProject(missingDirectory));
  t.after(() => removeProject(unpinnedDirectory));
  t.after(() => removeProject(throwingDirectory));
  t.after(() => removeProject(attestationDirectory));

  const missing = admitChange({ projectDirectory: missingDirectory, request: REQUEST, scope: 'src/index.ts' }).finalGate();
  const untrustedReviewer = aiReviewer();
  const unpinned = admitChange({
    projectDirectory: unpinnedDirectory,
    request: REQUEST,
    scope: 'src/index.ts',
    semanticReviewer: untrustedReviewer
  }).finalGate();
  const throwingReviewer = aiReviewer(() => new Error('review unavailable'));
  const badAttestationReviewer = aiReviewer(() => 'PASS', {
    mutate(judgment) {
      judgment.attestation.sourceDigest = '0'.repeat(64);
    }
  });
  const throwingCapability = hostReviewer(throwingDirectory, throwingReviewer);
  const badAttestationCapability = hostReviewer(attestationDirectory, badAttestationReviewer);
  const throwing = admitChange({
    projectDirectory: throwingDirectory,
    request: REQUEST,
    scope: 'src/index.ts',
    semanticReviewer: throwingCapability
  }).finalGate();
  const badAttestation = admitChange({
    projectDirectory: attestationDirectory,
    request: REQUEST,
    scope: 'src/index.ts',
    semanticReviewer: badAttestationCapability
  }).finalGate();

  assert.equal(missing.verdict, 'INCONCLUSIVE');
  assert.equal(unpinned.verdict, 'INCONCLUSIVE');
  assert.equal(throwing.verdict, 'INCONCLUSIVE');
  assert.equal(badAttestation.verdict, 'INCONCLUSIVE');
});

test('every JavaScript value thrown by the reviewer becomes structured INCONCLUSIVE evidence', (t) => {
  const thrownValues = [null, undefined, 'review unavailable', new Error('review unavailable')];

  for (const thrownValue of thrownValues) {
    const directory = makeProject(cleanProject());
    t.after(() => removeProject(directory));
    const reviewer = aiReviewer(() => {
      throw thrownValue;
    });
    const reviewerCapability = hostReviewer(directory, reviewer);
    let result;

    assert.doesNotThrow(() => {
      result = admitChange({
        projectDirectory: directory,
        request: REQUEST,
        scope: 'src/index.ts',
        semanticReviewer: reviewerCapability
      }).finalGate();
    });
    assert.equal(result.verdict, 'INCONCLUSIVE');
    assert.equal(result.completionApproval, false);
  }
});

test('cyclic and unknown attestation fields fail closed without crashing result projection', (t) => {
  const cyclicDirectory = makeProject(cleanProject());
  const unknownDirectory = makeProject(cleanProject());
  t.after(() => removeProject(cyclicDirectory));
  t.after(() => removeProject(unknownDirectory));
  const cyclicCapability = hostReviewer(cyclicDirectory, aiReviewer(() => 'PASS', {
    mutate(judgment) {
      judgment.attestation.self = judgment.attestation;
    }
  }));
  const unknownCapability = hostReviewer(unknownDirectory, aiReviewer(() => 'PASS', {
    mutate(judgment) {
      judgment.attestation.extra = 'not part of the attestation contract';
    }
  }));

  let cyclic;
  let unknown;
  assert.doesNotThrow(() => {
    cyclic = admitChange({
      projectDirectory: cyclicDirectory,
      request: REQUEST,
      scope: 'src/index.ts',
      semanticReviewer: cyclicCapability
    }).finalGate();
    unknown = admitChange({
      projectDirectory: unknownDirectory,
      request: REQUEST,
      scope: 'src/index.ts',
      semanticReviewer: unknownCapability
    }).finalGate();
  });

  assert.equal(cyclic.verdict, 'INCONCLUSIVE');
  assert.equal(unknown.verdict, 'INCONCLUSIVE');
  assert.equal(cyclic.details.semantic.checks[0].verdict, 'INCONCLUSIVE');
  assert.equal(unknown.details.semantic.checks[0].verdict, 'INCONCLUSIVE');
});

test('pre-change reviewer throw or explicit INCONCLUSIVE permanently makes baseline incomplete', (t) => {
  const throwingDirectory = makeProject(cleanProject());
  const inconclusiveDirectory = makeProject(cleanProject());
  t.after(() => removeProject(throwingDirectory));
  t.after(() => removeProject(inconclusiveDirectory));
  const throwingReviewer = aiReviewer((request) => request.phase === 'pre-change'
    ? new Error('baseline reviewer unavailable')
    : 'PASS');
  const inconclusiveReviewer = aiReviewer((request) => request.phase === 'pre-change'
    ? 'INCONCLUSIVE'
    : 'PASS');
  const throwingCapability = hostReviewer(throwingDirectory, throwingReviewer);
  const inconclusiveCapability = hostReviewer(inconclusiveDirectory, inconclusiveReviewer);

  const throwing = admitChange({
    projectDirectory: throwingDirectory,
    request: REQUEST,
    scope: 'src/index.ts',
    semanticReviewer: throwingCapability
  }).finalGate();
  const inconclusive = admitChange({
    projectDirectory: inconclusiveDirectory,
    request: REQUEST,
    scope: 'src/index.ts',
    semanticReviewer: inconclusiveCapability
  }).finalGate();

  assert.equal(throwing.verdict, 'INCONCLUSIVE');
  assert.equal(throwing.details.binding.baselineCompleteness.semantic, 'INCONCLUSIVE');
  assert.equal(inconclusive.verdict, 'INCONCLUSIVE');
  assert.equal(inconclusive.details.binding.baselineCompleteness.semantic, 'INCONCLUSIVE');
});

test('mutating one final-Gate result cannot alter private authority or a later result', (t) => {
  const directory = makeProject(cleanProject());
  t.after(() => removeProject(directory));
  const reviewerCapability = hostReviewer(directory, aiReviewer());
  const session = admitChange({
    projectDirectory: directory,
    request: REQUEST,
    scope: 'src/index.ts',
    semanticReviewer: reviewerCapability
  });
  const first = session.finalGate();
  const expectedFixedPaths = [...first.details.binding.impactScope.fixedPaths];

  first.details.binding.impactScope.fixedPaths.push('src/forged.ts');
  first.details.binding.policy.repositoryAuthority.executionPaths.push('src/forged.ts');
  first.details.semantic.required[0].id = 'forged-semantic-rule';
  const second = session.finalGate();

  assert.equal(second.verdict, 'PASS');
  assert.deepEqual(second.details.binding.impactScope.fixedPaths, expectedFixedPaths);
  assert.ok(!second.details.binding.policy.repositoryAuthority.executionPaths.includes('src/forged.ts'));
  assert.equal(second.details.semantic.required[0].id, 'b-1-error-handling-and-fallbacks');
});

test('reviewer key and callable swaps after admission do not change captured authority', (t) => {
  const directory = makeProject(cleanProject());
  t.after(() => removeProject(directory));
  const reviewerA = aiReviewer(() => 'PASS', { id: 'stable-reviewer' });
  const reviewerB = aiReviewer(() => 'FAIL', { id: 'replacement-reviewer' });
  const reviewerCapability = hostReviewer(directory, reviewerA);
  const session = admitChange({
    projectDirectory: directory,
    request: REQUEST,
    scope: 'src/index.ts',
    semanticReviewer: reviewerCapability
  });

  const registryContents = fs.readFileSync(hostRegistryPath);
  let result;
  try {
    fs.writeFileSync(hostRegistryPath, JSON.stringify({
      kind: 'node-policy-checker-reviewer-registry',
      reviewers: [{ id: reviewerA.id, model: reviewerA.model, publicKey: reviewerB.publicKey }]
    }));
    reviewerA.publicKey = reviewerB.publicKey;
    reviewerA.review = reviewerB.review;
    result = session.finalGate();
  } finally {
    fs.writeFileSync(hostRegistryPath, registryContents);
  }

  assert.equal(result.verdict, 'PASS');
  assert.equal(result.details.binding.reviewer.id, 'stable-reviewer');
});

test('the target reviewer model is mandatory and prevents weak duplicate-ID substitution', (t) => {
  const omittedGoodDirectory = makeProject(cleanProject());
  const omittedWeakDirectory = makeProject(cleanProject());
  const mismatchDirectory = makeProject(cleanProject());
  t.after(() => removeProject(omittedGoodDirectory));
  t.after(() => removeProject(omittedWeakDirectory));
  t.after(() => removeProject(mismatchDirectory));

  const goodReviewer = aiReviewer(() => 'PASS', { id: 'duplicate-reviewer', model: 'good-model' });
  const weakReviewer = aiReviewer(() => 'PASS', { id: 'duplicate-reviewer', model: 'weak-model' });
  hostReviewer(omittedGoodDirectory, goodReviewer);
  hostReviewer(omittedWeakDirectory, weakReviewer);
  setReviewerConfiguration(omittedGoodDirectory, { id: goodReviewer.id });
  setReviewerConfiguration(omittedWeakDirectory, { id: weakReviewer.id });
  hostReviewer(mismatchDirectory, goodReviewer);

  const omittedGood = admitChange({
    projectDirectory: omittedGoodDirectory,
    request: REQUEST,
    scope: 'src/index.ts',
    semanticReviewer: goodReviewer
  }).finalGate();
  const omittedWeak = admitChange({
    projectDirectory: omittedWeakDirectory,
    request: REQUEST,
    scope: 'src/index.ts',
    semanticReviewer: weakReviewer
  }).finalGate();
  const mismatchedWeak = admitChange({
    projectDirectory: mismatchDirectory,
    request: REQUEST,
    scope: 'src/index.ts',
    semanticReviewer: weakReviewer
  }).finalGate();

  assert.equal(omittedGood.verdict, 'INCONCLUSIVE');
  assert.equal(omittedWeak.verdict, 'INCONCLUSIVE');
  assert.equal(mismatchedWeak.verdict, 'INCONCLUSIVE');
  assert.equal(mismatchedWeak.details.binding.reviewer, null);
});

test('reviewer mutation of package.json makes final full-project authorization INCONCLUSIVE', (t) => {
  const directory = makeProject(cleanProject());
  t.after(() => removeProject(directory));
  let mutated = false;
  const reviewer = aiReviewer((request) => {
    if (request.phase === 'final' && !mutated) {
      mutated = true;
      const packagePath = path.join(directory, 'package.json');
      const packageValue = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
      packageValue.reviewerSideEffect = true;
      fs.writeFileSync(packagePath, JSON.stringify(packageValue));
    }
    return 'PASS';
  });
  const reviewerCapability = hostReviewer(directory, reviewer);
  const session = admitChange({
    projectDirectory: directory,
    request: REQUEST,
    scope: 'src/index.ts',
    semanticReviewer: reviewerCapability
  });

  const result = session.finalGate();

  assert.equal(result.verdict, 'INCONCLUSIVE');
  assert.equal(result.details.sourceReadback.unchanged, true);
  assert.equal(result.details.finalChecks.find((item) => item.id === 'full-project-authorization').verdict, 'INCONCLUSIVE');
});

test('authentic pre-existing violations outside fixed impact scope are reported without blocking', (t) => {
  const directory = makeProject({
    ...cleanProject('export const value: number = 1;\n', 'src/changed.ts'),
    'src/unrelated.ts': 'export function oldFailure(): void { try { throw new Error("old"); } catch (error) {} }\n'
  });
  t.after(() => removeProject(directory));
  const reviewer = aiReviewer(() => 'PASS', { path: 'src/changed.ts' });
  const reviewerCapability = hostReviewer(directory, reviewer);
  const session = admitChange({
    projectDirectory: directory,
    request: REQUEST,
    scope: 'src/changed.ts',
    semanticReviewer: reviewerCapability
  });

  const result = session.finalGate();

  assert.equal(result.verdict, 'PASS');
  assert.equal(mechanical(result, 'empty-catch').rawVerdict, 'FAIL');
  assert.equal(mechanical(result, 'empty-catch').verdict, 'PASS');
  assert.ok(result.details.preExisting.unrelated.some((item) => item.path === 'src/unrelated.ts' && item.observedNow));
});

test('a valid pre-change semantic FAIL remains authentic evidence without making the baseline incomplete', (t) => {
  const directory = makeProject({
    ...cleanProject('export const value: number = 1;\n', 'src/changed.ts'),
    'src/unrelated.ts': 'export const coupledState: Record<string, unknown> = {};\n'
  });
  t.after(() => removeProject(directory));
  const reviewer = aiReviewer((request) => request.requirement.id === 'c-3-hidden-coupling'
    ? { verdict: 'FAIL', path: 'src/unrelated.ts' }
    : { verdict: 'PASS', path: 'src/changed.ts' });
  const reviewerCapability = hostReviewer(directory, reviewer);
  const session = admitChange({
    projectDirectory: directory,
    request: REQUEST,
    scope: 'src/changed.ts',
    semanticReviewer: reviewerCapability
  });

  const result = session.finalGate();

  assert.equal(result.verdict, 'PASS');
  assert.equal(result.details.binding.baselineCompleteness.semantic, 'PASS');
  assert.ok(result.details.preExisting.unrelated.some((item) => {
    return item.checkId === 'c-3-hidden-coupling' && item.path === 'src/unrelated.ts' && item.observedNow;
  }));
});

test('an impacted baseline semantic FAIL cannot be overwritten by a same-location final PASS', (t) => {
  const directory = makeProject(cleanProject('export const value: number = 1;\n', 'src/changed.ts'));
  t.after(() => removeProject(directory));
  const reviewer = aiReviewer((request) => {
    if (request.requirement.id === 'c-3-hidden-coupling' && request.phase === 'pre-change') {
      return { verdict: 'FAIL', path: 'src/changed.ts' };
    }
    return { verdict: 'PASS', path: 'src/changed.ts' };
  });
  const reviewerCapability = hostReviewer(directory, reviewer);
  const result = admitChange({
    projectDirectory: directory,
    request: REQUEST,
    scope: 'src/changed.ts',
    semanticReviewer: reviewerCapability
  }).finalGate();

  assert.equal(result.details.binding.baselineCompleteness.semantic, 'PASS');
  assert.ok(result.details.preExisting.impacted.some((item) => {
    return item.checkId === 'c-3-hidden-coupling' && item.path === 'src/changed.ts' && item.observedNow;
  }));
  assert.equal(result.details.semantic.checks.find((item) => item.id === 'c-3-hidden-coupling').verdict, 'PASS');
  assert.equal(result.details.finalChecks.find((item) => item.id === 'baseline-impact').verdict, 'FAIL');
  assert.equal(result.verdict, 'FAIL');
  assert.equal(result.completionApproval, false);
});

test('pre-change dependency closure remains blocking after the current import is removed', (t) => {
  const directory = makeProject({
    ...cleanProject("import { shared } from './shared';\nexport const value = shared;\n", 'src/changed.ts'),
    'src/shared.ts': 'export function shared(): void { try { throw new Error("old"); } catch (error) {} }\n'
  });
  t.after(() => removeProject(directory));
  const reviewer = aiReviewer(() => 'PASS', { path: 'src/changed.ts' });
  const reviewerCapability = hostReviewer(directory, reviewer);
  const session = admitChange({
    projectDirectory: directory,
    request: REQUEST,
    scope: 'src/changed.ts',
    semanticReviewer: reviewerCapability
  });
  assert.ok(session.details.binding.admittedScope.entries.some((entry) => entry.path === 'src/changed.ts'));
  const written = session.attemptWrite({
    request: REQUEST,
    writes: [{ path: 'src/changed.ts', content: 'export const value: number = 1;\n' }]
  });

  assert.equal(written.allowed, true);
  const result = session.finalGate();

  assert.ok(result.details.binding.impactScope.fixedPaths.includes('src/shared.ts'));
  assert.ok(result.details.binding.impactScope.effectivePaths.includes('src/shared.ts'));
  assert.equal(mechanical(result, 'empty-catch').verdict, 'FAIL');
  assert.equal(result.verdict, 'FAIL');
});

test('a pre-change unknown dependency edge remains INCONCLUSIVE after the import is removed', (t) => {
  const directory = makeProject({
    ...cleanProject([
      "const dependency = './shared';",
      'export async function value(): Promise<unknown> { return import(dependency); }',
      ''
    ].join('\n')),
    'src/shared.ts': 'export const shared: number = 1;\n'
  });
  t.after(() => removeProject(directory));
  const reviewerCapability = hostReviewer(directory, aiReviewer());
  const session = admitChange({
    projectDirectory: directory,
    request: REQUEST,
    scope: 'src/index.ts',
    semanticReviewer: reviewerCapability
  });
  assert.equal(session.verdict, 'PASS');
  const written = session.attemptWrite({
    request: REQUEST,
    writes: [{ path: 'src/index.ts', content: 'export const value: number = 1;\n' }]
  });

  assert.equal(written.allowed, true);
  const result = session.finalGate();

  assert.equal(result.verdict, 'INCONCLUSIVE');
  assert.equal(result.details.binding.baselineCompleteness.mechanicalGraph, 'INCONCLUSIVE');
  assert.ok(result.details.evidenceErrors.some((item) => item.error && item.error.includes('dynamic source dependency')));
});

test('malformed raw evidence and stale session source return INCONCLUSIVE instead of throwing', (t) => {
  const malformedDirectory = makeProject(cleanProject());
  const staleDirectory = makeProject(cleanProject());
  t.after(() => removeProject(malformedDirectory));
  t.after(() => removeProject(staleDirectory));
  const malformed = {
    preChange: { violations: [{}] },
    impactScope: { entries: [{ mode: 'subtree' }] }
  };

  assert.doesNotThrow(() => gateProject(malformedDirectory, malformed));
  assert.equal(gateProject(malformedDirectory, malformed).verdict, 'INCONCLUSIVE');

  const reviewer = aiReviewer();
  const reviewerCapability = hostReviewer(staleDirectory, reviewer);
  const session = admitChange({
    projectDirectory: staleDirectory,
    request: REQUEST,
    scope: 'src/index.ts',
    semanticReviewer: reviewerCapability
  });
  fs.writeFileSync(path.join(staleDirectory, 'src/index.ts'), 'export const value: number = 2;\n');
  const stale = session.finalGate();
  assert.equal(stale.verdict, 'INCONCLUSIVE');
  assert.equal(stale.completionApproval, false);
});

test('CLI caller evidence cannot substitute for a WP-001 session authority', (t) => {
  const directory = makeProject(cleanProject());
  const evidenceDirectory = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-final-gate-evidence-'));
  const evidencePath = path.join(evidenceDirectory, 'forged.json');
  fs.writeFileSync(evidencePath, JSON.stringify({ semanticJudgments: [{ verdict: 'PASS' }] }));
  t.after(() => removeProject(directory));
  t.after(() => removeProject(evidenceDirectory));
  const before = digest(directory);

  const result = childProcess.spawnSync(
    process.execPath,
    [cliPath, 'gate', '--details', '--evidence', evidencePath, directory],
    { encoding: 'utf8' }
  );

  assert.equal(result.status, 2, result.stderr);
  const details = JSON.parse(result.stdout);
  assert.equal(details.verdict, 'INCONCLUSIVE');
  assert.equal(details.completionApproval, false);
  assert.equal(digest(directory), before);
});

test('invalid or target-controlled host registries fail closed in fresh processes', (t) => {
  const missingDirectory = makeProject(cleanProject());
  const callerDirectory = makeProject(cleanProject());
  const publicOnlyDirectory = makeProject(cleanProject());
  const relativeDirectory = makeProject(cleanProject());
  const malformedDirectory = makeProject(cleanProject());
  const insideDirectory = makeProject(cleanProject());
  const writableDirectory = makeProject(cleanProject());
  const registryDirectory = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-invalid-registry-'));
  const malformedPath = path.join(registryDirectory, 'malformed.json');
  const writablePath = path.join(registryDirectory, 'writable.json');
  const insidePath = path.join(insideDirectory, 'reviewers.json');
  fs.writeFileSync(malformedPath, '{not-json');
  fs.copyFileSync(hostRegistryPath, writablePath);
  fs.chmodSync(writablePath, 0o666);
  fs.copyFileSync(hostRegistryPath, insidePath);
  t.after(() => removeProject(missingDirectory));
  t.after(() => removeProject(callerDirectory));
  t.after(() => removeProject(publicOnlyDirectory));
  t.after(() => removeProject(relativeDirectory));
  t.after(() => removeProject(malformedDirectory));
  t.after(() => removeProject(insideDirectory));
  t.after(() => removeProject(writableDirectory));
  t.after(() => removeProject(registryDirectory));

  const outcomes = [
    { outcome: childGate(missingDirectory, null, false), trustedTransport: false },
    { outcome: childGate(callerDirectory, null, true), trustedTransport: false },
    { outcome: childGate(publicOnlyDirectory, hostRegistryPath, true, true), trustedTransport: true },
    { outcome: childGate(relativeDirectory, 'relative-reviewers.json', true), trustedTransport: false },
    { outcome: childGate(malformedDirectory, malformedPath, true), trustedTransport: false },
    { outcome: childGate(insideDirectory, insidePath, true, true), trustedTransport: false },
    { outcome: childGate(writableDirectory, writablePath, true, true), trustedTransport: false }
  ];

  for (const { outcome, trustedTransport } of outcomes) {
    assert.equal(outcome.status, 0, outcome.stderr);
    const result = JSON.parse(outcome.stdout);
    assert.equal(result.verdict, 'INCONCLUSIVE');
    assert.equal(result.completionApproval, false);
    if (trustedTransport) {
      assert.equal(result.details.binding.reviewer.id, 'fixture-reviewer');
      assert.equal(result.details.binding.baselineCompleteness.semantic, 'INCONCLUSIVE');
    } else {
      assert.equal(result.details.binding.reviewer, null);
    }
  }
});

test('root-level module boundaries accept the canonical dot boundary', (t) => {
  const directory = makeProject({
    'package.json': JSON.stringify({ name: 'root-boundary', main: 'index.js' }),
    'index.js': "const { value } = require('./util');\nexports.value = value;\n",
    'util.js': 'exports.value = 1;\n'
  });
  t.after(() => removeProject(directory));
  const { diagnoseFastProject } = require('..');

  const result = diagnoseFastProject(directory, {
    boundaryEvidence: {
      kind: 'fixed-observed-boundaries',
      projectRoot: directory,
      source: 'fixture root boundary',
      allowedDependencies: [{ from: '.', to: '.' }]
    }
  });

  assert.equal(result.checks.find((item) => item.id === 'fixed-boundaries').verdict, 'PASS');
});

test('forced parser unavailability keeps a session final Gate INCONCLUSIVE', (t) => {
  const directory = makeProject(cleanProject());
  t.after(() => removeProject(directory));
  const script = [
    "const Module = require('node:module');",
    'const load = Module._load;',
    "Module._load = function(request, parent, isMain) { if (request === '@babel/parser') throw new Error('forced parser unavailability'); return load.call(this, request, parent, isMain); };",
    `const { admitChange } = require(${JSON.stringify(path.join(__dirname, '..'))});`,
    `const session = admitChange({ projectDirectory: process.argv[1], request: ${JSON.stringify(REQUEST)}, scope: 'src/index.ts' });`,
    'process.stdout.write(JSON.stringify(session.finalGate()));'
  ].join(' ');

  const result = childProcess.spawnSync(process.execPath, ['-e', script, directory], { encoding: 'utf8' });

  assert.equal(result.status, 0, result.stderr);
  const details = JSON.parse(result.stdout);
  assert.equal(details.verdict, 'INCONCLUSIVE');
  assert.equal(details.details.mechanical.checks.find((item) => item.id === 'empty-catch').verdict, 'INCONCLUSIVE');
});
