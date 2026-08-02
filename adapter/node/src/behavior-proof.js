'use strict';

const childProcess = require('node:child_process');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { resolveAdmissionCapability } = require('./admission');

const BEHAVIOR_AUTHORITIES = new WeakSet();
const IGNORED_DIRECTORIES = new Set([
  '.git',
  '.hg',
  '.svn',
  '.cache',
  '.next',
  'build',
  'coverage',
  'dist',
  'node_modules',
  'out'
]);
const SOURCE_EXTENSIONS = ['.cts', '.mts', '.tsx', '.jsx', '.ts', '.mjs', '.cjs', '.js'];
const TEST_TIMEOUT_MS = 30000;
const CHANGE_DIFF_MAX_BYTES = 4 * 1024 * 1024;
const CHANGE_DIFF_MAX_EXACT_CHARS = 16 * 1024;
const CHANGE_DIFF_MAX_LINES = 5000;
const CHANGE_DIFF_MAX_FRONTIER_WORK = 4 * 1024 * 1024;
const BUBBLEWRAP_COMMAND = 'bwrap';
const SANDBOX_ROOT = '/tmp/node-policy-project';
const DIRECTORY_BIND_FD = 3;
const SANDBOX_SECURITY_PROBE = "if (process.cwd() !== '/tmp/node-policy-project' || !require('node:fs').existsSync(process.execPath)) process.exit(42);";
const SANDBOX_RUNTIME_TREES = ['/lib', '/lib64', '/usr/lib', '/usr/lib64'];
let sandboxRuntime = null;

/**
 * Creates a behavior-proof runner that can only be reached through the opaque
 * admission capability held by the final-Gate composition.
 *
 * @param {object} admissionCapability opaque WP-001 capability
 * @param {object} qualityObligations fixed WP-002 obligations
 * @param {object} wp002ImpactScopeBasis private final-Gate scope basis
 * @returns {{run: Function}} session-bound behavior proof
 */
function createBehaviorProofSession(admissionCapability, qualityObligations, wp002ImpactScopeBasis) {
  const admissionAuthority = resolveAdmissionCapability(admissionCapability);
  if (!admissionAuthority) {
    throw new TypeError('Behavior-proof authority requires an opaque capability minted by createAdmissionSession.');
  }

  const authority = captureBehaviorAuthority(admissionAuthority, qualityObligations, wp002ImpactScopeBasis);
  BEHAVIOR_AUTHORITIES.add(authority);
  return Object.freeze({
    run(proofOptions) {
      return proveBehavior(authority.projectRoot, { authority, proofOptions });
    }
  });
}

function captureBehaviorAuthority(admissionAuthority, qualityObligations, wp002ImpactScopeBasis) {
  const errors = [];
  const deepErrors = [];
  const projectRoot = typeof admissionAuthority.projectRoot === 'string'
    ? path.resolve(admissionAuthority.projectRoot)
    : null;
  const admission = admissionAuthority.admission;
  if (!projectRoot || !isPlainObject(admission) || admission.verdict !== 'PASS') {
    errors.push(capabilityEvidence('authority', 'A passing WP-001 admission session is required before behavior proof can run.'));
  }
  if (!isPlainObject(admissionAuthority.admittedScope) || !Array.isArray(admissionAuthority.admittedScope.entries) || admissionAuthority.admittedScope.entries.length === 0) {
    errors.push(capabilityEvidence('authority.impactScope', 'WP-001 did not establish a fixed changed scope.'));
  }
  if (typeof admissionAuthority.currentSourceAuthorized !== 'function') {
    errors.push(capabilityEvidence('authority.currentSource', 'The admission session cannot authorize current source identity.'));
  }
  if (!validQualityObligations(qualityObligations)) {
    errors.push(capabilityEvidence('authority.qualityObligations', 'The fixed WP-002 quality obligations are unavailable.'));
  }

  const entries = admissionAuthority.admittedScope && Array.isArray(admissionAuthority.admittedScope.entries)
    ? admissionAuthority.admittedScope.entries.map((entry) => ({ mode: entry.mode, path: entry.path }))
    : [];
  const proposedBaselinePaths = proposedBaselineSourcePaths(admission, entries);
  const sourceSnapshot = projectRoot ? captureScopedSources(projectRoot, entries) : { errors: ['Project root is unavailable.'], files: [] };
  if (sourceSnapshot.errors.length > 0) {
    errors.push(...sourceSnapshot.errors.map((error) => capabilityEvidence('authority.changedSource', error)));
  }
  if (sourceSnapshot.files.length === 0 && proposedBaselinePaths.length === 0) {
    errors.push(capabilityEvidence('authority.changedSource', 'The fixed changed scope did not contain readable Node or TypeScript product source.'));
  }

  const before = projectRoot ? fingerprintProject(projectRoot) : { error: 'Project root is unavailable.' };
  const after = projectRoot ? fingerprintProject(projectRoot) : { error: 'Project root is unavailable.' };
  if (!before.digest || !after.digest || before.digest !== after.digest) {
    errors.push(capabilityEvidence('authority.sourceReadback', 'Source changed while behavior-proof authority was being captured.'));
  }

  const repositoryEvidence = admission && admission.details && admission.details.repositoryEvidence;
  const impactScope = captureWp002ImpactScope(projectRoot, wp002ImpactScopeBasis, deepErrors);
  const impactSnapshot = impactScope && projectRoot
    ? captureFixedSources(projectRoot, impactScope.fixedPaths)
    : { errors: [], files: [] };
  if (impactScope && impactSnapshot.errors.length > 0) {
    deepErrors.push(...impactSnapshot.errors.map((error) => capabilityEvidence('authority.impactSource', error)));
  }
  if (impactScope && impactSnapshot.files.length === 0) {
    deepErrors.push(capabilityEvidence('authority.impactSource', 'The fixed WP-002 impact scope did not contain readable Node or TypeScript product source.'));
  }
  const testObligations = admission && admission.details && Array.isArray(admission.details.testObligations)
    ? admission.details.testObligations.map((obligation) => ({
      ...obligation,
      ...(obligation && obligation.expectedFailureOutcome ? {
        expectedFailureOutcome: {
          ...obligation.expectedFailureOutcome,
          constraints: Array.isArray(obligation.expectedFailureOutcome.constraints)
            ? obligation.expectedFailureOutcome.constraints.map((constraint) => ({ ...constraint }))
            : obligation.expectedFailureOutcome.constraints
        }
      } : {})
    }))
    : [];
  if (testObligations.length === 0) {
    errors.push(capabilityEvidence('authority.testObligations', 'WP-001 did not retain the required edge-case obligations.'));
  }

  return deepFreeze({
    currentSourceAuthorized: admissionAuthority.currentSourceAuthorized,
    changedScope: { entries },
    deepErrors,
    errors,
    externalBoundaries: fixedExternalBoundaries(
      repositoryEvidence,
      impactScope ? impactScope.fixedPaths : sourceSnapshot.files.map((file) => file.path)
    ),
    impactScope,
    impactScopeCompleteness: isPlainObject(wp002ImpactScopeBasis) ? wp002ImpactScopeBasis.completeness : 'INCONCLUSIVE',
    preChange: {
      sourceReadback: before,
      sources: sourceSnapshot.files,
      absentPaths: proposedBaselinePaths.filter((filePath) => !sourceSnapshot.files.some((file) => file.path === filePath)),
      impactSources: impactSnapshot.files
    },
    projectRoot,
    qualityObligations,
    testObligations
  });
}

/**
 * Runs a session-bound focused or deep behavior proof. The target project is
 * read only; test and mutation commands always run from disposable copies.
 *
 * @param {string} projectDirectory target project directory
 * @param {{authority?: object}} [options] private authority envelope
 * @returns {object} behavior-proof result
 */
function proveBehavior(projectDirectory, options = {}) {
  const invocation = resolveProofInvocation(options);
  if (invocation.error) {
    return invalidProofInvocation(invocation.error);
  }
  return invocation.mode === 'deep'
    ? proveDeepBehavior(projectDirectory, options)
    : proveFocusedBehavior(projectDirectory, options);
}

function proveFocusedBehavior(projectDirectory, options = {}) {
  if (typeof projectDirectory !== 'string' || projectDirectory.length === 0) {
    throw new TypeError('proveBehavior requires a project directory path.');
  }

  const projectRoot = path.resolve(projectDirectory);
  const before = fingerprintProject(projectRoot);
  const evidence = validateAuthority(options, projectRoot);
  const sourceReadback = {
    after: null,
    before: sourceStateEvidence(before),
    authorizationAfter: null,
    authorizationBefore: authorizationState(evidence.authority),
    unchanged: false
  };
  const changedSource = evidence.valid ? collectChangedSources(evidence.authority, projectRoot) : unavailableChangedSource();
  const related = evidence.valid && changedSource.files.length > 0
    ? collectRelatedTests(projectRoot, changedSource.files.map((file) => file.path))
    : { files: [], reason: 'A valid current changed-source scope was not available.' };
  const relatedProductFiles = uniqueProofFiles(related.closureFiles || related.files).filter((file) => isProductSource(file.path));
  const testCapability = evidence.valid && changedSource.files.length > 0
    ? resolveTestCapability(projectRoot, related.files)
    : { available: false, reason: 'A valid current changed-source scope was not available.' };
  const observability = assessObservability(related.closureFiles || related.files, relatedProductFiles, projectRoot);
  const edgeCases = assessEdgeCases(relatedProductFiles, {
    ...related,
    applicableSourceFiles: changedSource.files
  }, projectRoot, evidence.authority ? evidence.authority.testObligations : []);
  const mockBoundaries = assessMockBoundaries(
    related.closureFiles || related.files,
    evidence.authority && evidence.authority.externalBoundaries,
    changedSource.contents.map((file) => file.path)
  );
  let execution = { status: 'NOT_RUN' };
  let mutation = { status: 'NOT_RUN' };

  if (testCapability.available && evidence.valid && changedSource.files.length > 0) {
    execution = runRepositoryTests(projectRoot, testCapability);
    if (execution.status === 'PASS') {
      mutation = runMutationProbes(projectRoot, testCapability, changedSource.files);
    }
  }

  const defensiveHandling = assessDefensiveHandling(
    changedSource,
    edgeCases,
    mutation
  );
  const after = fingerprintProject(projectRoot);
  sourceReadback.after = sourceStateEvidence(after);
  sourceReadback.authorizationAfter = authorizationState(evidence.authority);
  sourceReadback.unchanged = Boolean(
    before.digest &&
    after.digest &&
    before.digest === after.digest &&
    sourceReadback.authorizationBefore === 'PASS' &&
    sourceReadback.authorizationAfter === 'PASS'
  );

  const checks = [
    bindingCheck(evidence),
    sourceStabilityCheck(sourceReadback),
    changedSourceCheck(changedSource),
    relatedTestsCheck(related),
    testCapabilityCheck(testCapability),
    executionCheck(execution),
    mutationCheck(mutation),
    observabilityCheck(observability),
    edgeCaseCheck(edgeCases),
    mockBoundaryCheck(mockBoundaries),
    defensiveHandlingCheck(defensiveHandling)
  ];
  const verdict = evidence.valid ? aggregateVerdict(checks) : 'INCONCLUSIVE';
  const summary = {
    verdict,
    changedSources: changedSource.files.map((file) => file.path),
    mainFindings: checks.filter((check) => check.verdict !== 'PASS').slice(0, 5).map((check) => ({
      id: check.id,
      message: check.message,
      verdict: check.verdict
    }))
  };

  return {
    kind: 'focused-change-behavior-proof',
    verdict,
    summary,
    details: {
      binding: describeBinding(evidence.authority),
      changedSource,
      edgeCases,
      mockBoundaries,
      observability,
      sourceReadback,
      testExecution: execution,
      testSelection: {
        relatedTests: related.files.map((file) => file.path),
        reason: related.reason || null,
        testCapability
      },
      mutation,
      defensiveHandling,
      checks
    }
  };
}

function proveDeepBehavior(projectDirectory, options = {}) {
  if (typeof projectDirectory !== 'string' || projectDirectory.length === 0) {
    throw new TypeError('proveBehavior requires a project directory path.');
  }

  const projectRoot = path.resolve(projectDirectory);
  const before = fingerprintProject(projectRoot);
  const evidence = validateDeepAuthority(validateAuthority(options, projectRoot), projectRoot);
  const sourceReadback = {
    after: null,
    before: sourceStateEvidence(before),
    authorizationAfter: null,
    authorizationBefore: authorizationState(evidence.authority),
    unchanged: false
  };
  const changedSource = evidence.valid ? collectChangedSources(evidence.authority, projectRoot) : unavailableChangedSource();
  const impactSources = evidence.valid ? collectImpactSources(evidence.authority, projectRoot, changedSource) : unavailableImpactSources();
  const related = evidence.valid && impactSources.files.length > 0
    ? collectImpactRelatedTests(projectRoot, impactSources.files)
    : unavailableImpactTests();
  const testCapability = evidence.valid && impactSources.status === 'PASS' && impactSources.files.length > 0
    ? resolveImpactTestCapability(projectRoot, related)
    : { available: false, reason: 'A valid fixed dependency impact closure was not available.' };
  const observability = assessImpactObservability(related, impactSources.files, projectRoot);
  const edgeCases = assessImpactEdgeCases(
    impactSources.files,
    related,
    projectRoot,
    evidence.authority ? evidence.authority.testObligations : []
  );
  const mockBoundaries = assessMockBoundaries(
    related.closureFiles || related.files,
    evidence.authority && evidence.authority.externalBoundaries,
    impactSources.files.map((file) => file.path)
  );
  let execution = impactExecution('NOT_RUN', related);
  let mutation = impactMutationNotRun(impactSources.files, related);

  if (testCapability.available && evidence.valid && impactSources.files.length > 0) {
    execution = attachImpactExecution(runRepositoryTests(projectRoot, testCapability), related);
    if (execution.status === 'PASS') {
      mutation = runImpactMutationProbes(projectRoot, testCapability, impactSources.files, related);
    }
  }

  const defensiveHandling = assessImpactDefensiveHandling(impactSources, edgeCases, mutation);
  const after = fingerprintProject(projectRoot);
  sourceReadback.after = sourceStateEvidence(after);
  sourceReadback.authorizationAfter = authorizationState(evidence.authority);
  sourceReadback.unchanged = Boolean(
    before.digest &&
    after.digest &&
    before.digest === after.digest &&
    sourceReadback.authorizationBefore === 'PASS' &&
    sourceReadback.authorizationAfter === 'PASS'
  );

  const checks = [
    bindingCheck(evidence),
    sourceStabilityCheck(sourceReadback),
    changedSourceCheck(changedSource),
    impactSourceCheck(impactSources),
    impactRelatedTestsCheck(related),
    impactTestCapabilityCheck(testCapability),
    impactExecutionCheck(execution),
    impactMutationCheck(mutation),
    observabilityCheck(observability),
    edgeCaseCheck(edgeCases),
    mockBoundaryCheck(mockBoundaries),
    defensiveHandlingCheck(defensiveHandling)
  ];
  const verdict = evidence.valid ? aggregateDeepVerdict(checks) : 'INCONCLUSIVE';
  const summary = {
    verdict,
    changedSources: changedSource.files.map((file) => file.path),
    impactSources: impactSources.files.map((file) => file.path),
    mainFindings: checks.filter((check) => check.verdict !== 'PASS').slice(0, 5).map((check) => ({
      id: check.id,
      message: check.message,
      verdict: check.verdict
    }))
  };

  return {
    kind: 'deep-impact-behavior-proof',
    verdict,
    summary,
    details: {
      binding: describeBinding(evidence.authority),
      changedSource,
      impact: describeImpactCoverage(impactSources, related, execution, mutation),
      impactSources,
      edgeCases,
      mockBoundaries,
      observability,
      sourceReadback,
      testExecution: execution,
      testSelection: {
        impactSources: impactSources.files.map((file) => file.path),
        relatedTests: related.files.map((file) => file.path),
        reason: related.reason || null,
        perSource: related.perSource.map((item) => ({
          path: item.path,
          tests: item.files.map((file) => file.path)
        })),
        testCapability
      },
      mutation,
      defensiveHandling,
      checks
    }
  };
}

function resolveProofInvocation(options) {
  const proofOptions = isPlainObject(options) && Object.hasOwn(options, 'proofOptions')
    ? options.proofOptions
    : undefined;
  if (proofOptions === undefined || (isPlainObject(proofOptions) && !Object.hasOwn(proofOptions, 'mode'))) {
    return { mode: 'focused' };
  }
  if (!isPlainObject(proofOptions) || !['focused', 'deep'].includes(proofOptions.mode)) {
    return { error: 'Behavior proof mode must be focused or deep.' };
  }
  return { mode: proofOptions.mode };
}

function invalidProofInvocation(message) {
  const modeCheck = check('proof-mode', 'INCONCLUSIVE', message);
  return {
    kind: 'behavior-proof',
    verdict: 'INCONCLUSIVE',
    summary: {
      changedSources: [],
      mainFindings: [{ id: modeCheck.id, message: modeCheck.message, verdict: modeCheck.verdict }],
      verdict: 'INCONCLUSIVE'
    },
    details: { checks: [modeCheck] }
  };
}

function validateAuthority(value, projectRoot) {
  const errors = [];
  const authority = isPlainObject(value) ? value.authority : null;
  if (!authority || !BEHAVIOR_AUTHORITIES.has(authority)) {
    errors.push(capabilityEvidence('authority', 'Behavior proof requires the opaque authority of the current WP-001 admission session.'));
    return { authority: null, errors, valid: false };
  }
  if (authority.projectRoot !== projectRoot) {
    errors.push(capabilityEvidence('authority.projectRoot', 'Behavior-proof authority is bound to a different project root.'));
  }
  errors.push(...authority.errors);
  if (!authorizationState(authority) || authorizationState(authority) !== 'PASS') {
    errors.push(capabilityEvidence('authority.currentSource', 'Current source is not the state authorized by the WP-001 session.'));
  }
  return { authority, errors, valid: errors.length === 0 };
}

function validateDeepAuthority(evidence, projectRoot) {
  const errors = [...evidence.errors];
  const authority = evidence.authority;
  if (!authority) {
    return { authority: null, errors, valid: false };
  }
  errors.push(...(authority.deepErrors || []));
  if (!authority.impactScope || authority.impactScope.projectRoot !== projectRoot) {
    errors.push(capabilityEvidence('authority.wp002ImpactScope', 'The current final-Gate session did not provide a WP-002 fixed impact scope for deep proof.'));
  }
  return { authority, errors, valid: errors.length === 0 };
}

function authorizationState(authority) {
  if (!authority || typeof authority.currentSourceAuthorized !== 'function') {
    return 'INCONCLUSIVE';
  }
  try {
    return authority.currentSourceAuthorized() ? 'PASS' : 'INCONCLUSIVE';
  } catch (error) {
    return 'INCONCLUSIVE';
  }
}

function fixedExternalBoundaries(repositoryEvidence, fixedPaths) {
  const direction = repositoryEvidence && repositoryEvidence.dependencyDirection;
  const references = direction && Array.isArray(direction.externalImports) ? direction.externalImports : [];
  return [...new Set(references
    .filter((reference) => reference && fixedPaths.includes(reference.path) && !isTestFile(reference.path) && typeof reference.specifier === 'string')
    .map((reference) => reference.specifier))].sort();
}

function validQualityObligations(value) {
  return isPlainObject(value) &&
    value.kind === 'fixed-wp002-quality-obligations' &&
    Array.isArray(value.mechanical) && value.mechanical.length > 0 &&
    Array.isArray(value.semantic) && value.semantic.length > 0;
}

function captureWp002ImpactScope(projectRoot, basis, errors) {
  if (!isPlainObject(basis) || basis.kind !== 'wp002-final-gate-impact-scope-basis') {
    errors.push(capabilityEvidence('authority.wp002ImpactScope', 'The same final-Gate session did not provide a WP-002 fixed impact-scope basis.'));
    return null;
  }
  if (typeof basis.projectRoot !== 'string' || basis.projectRoot !== projectRoot || typeof basis.sessionId !== 'string' || basis.sessionId.length === 0) {
    errors.push(capabilityEvidence('authority.wp002ImpactScope.projectRoot', 'The WP-002 fixed impact scope is bound to a different project root.'));
  }
  if (basis.completeness !== 'PASS') {
    errors.push(capabilityEvidence('authority.wp002ImpactScope.completeness', 'The WP-002 dependency graph or required capability was incomplete when its impact scope was captured.'));
  }
  const impactScope = basis.impactScope;
  if (!isPlainObject(impactScope) || impactScope.kind !== 'fixed-impact-scope' ||
    typeof impactScope.id !== 'string' || impactScope.id.length === 0 ||
    typeof impactScope.source !== 'string' || impactScope.source.length === 0 ||
    typeof impactScope.projectRoot !== 'string' || impactScope.projectRoot !== projectRoot ||
    !Array.isArray(impactScope.entries) || impactScope.entries.length === 0 ||
    !Array.isArray(impactScope.fixedPaths) || impactScope.fixedPaths.length === 0) {
    errors.push(capabilityEvidence('authority.wp002ImpactScope', 'The final-Gate WP-002 impact scope is incomplete or malformed.'));
    return null;
  }
  if (!impactScope.source.includes(basis.sessionId) || impactScope.entries.some((entry) => !isPlainObject(entry) ||
    !['exact', 'subtree'].includes(entry.mode) || !safeRelativePath(entry.path, true)) ||
    impactScope.fixedPaths.some((filePath) => !safeRelativePath(filePath, false))) {
    errors.push(capabilityEvidence('authority.wp002ImpactScope', 'The final-Gate WP-002 impact scope is not a complete fixed session authority.'));
    return null;
  }
  return impactScope;
}

function captureScopedSources(projectRoot, entries) {
  const files = [];
  const errors = [];
  for (const filePath of collectSourcePaths(projectRoot, entries, errors)) {
    try {
      const contents = fs.readFileSync(path.join(projectRoot, ...filePath.split('/')));
      files.push({ digest: digestBuffer(contents), path: filePath, contents: contents.toString('utf8') });
    } catch (error) {
      errors.push(`${filePath}: ${error.message}`);
    }
  }
  return { errors, files };
}

function proposedBaselineSourcePaths(admission, entries) {
  const baseline = admission && admission.details && admission.details.proposedBaseline;
  if (!isPlainObject(baseline) || baseline.status !== 'proposed-not-created' || !Array.isArray(baseline.files)) {
    return [];
  }
  return [...new Set(baseline.files
    .filter((file) => file && file.status === 'proposed' && typeof file.path === 'string' && isProductSource(file.path))
    .map((file) => file.path)
    .filter((filePath) => admittedScopeContains(entries, filePath)))].sort();
}

function admittedScopeContains(entries, filePath) {
  return entries.some((entry) => entry && (
    entry.mode === 'subtree'
      ? filePath === entry.path || filePath.startsWith(`${entry.path}/`)
      : entry.mode === 'exact' && filePath === entry.path
  ));
}

function captureFixedSources(projectRoot, filePaths) {
  const files = [];
  const errors = [];
  for (const filePath of filePaths || []) {
    if (!safeRelativePath(filePath, false)) {
      errors.push(`The fixed dependency impact closure contains an unsafe path: ${filePath}.`);
      continue;
    }
    const absolute = path.resolve(projectRoot, ...filePath.split('/'));
    if (!isWithin(projectRoot, absolute)) {
      errors.push(`The fixed dependency impact closure leaves the project: ${filePath}.`);
      continue;
    }
    let stat;
    try {
      stat = fs.lstatSync(absolute);
    } catch (error) {
      errors.push(`${filePath}: ${error.message}`);
      continue;
    }
    if (!isProductSource(filePath)) {
      continue;
    }
    if (stat.isSymbolicLink() || !stat.isFile()) {
      errors.push(`${filePath}: fixed impact source must be a readable regular file.`);
      continue;
    }
    try {
      const contents = fs.readFileSync(absolute);
      files.push({ digest: digestBuffer(contents), path: filePath, contents: contents.toString('utf8') });
    } catch (error) {
      errors.push(`${filePath}: ${error.message}`);
    }
  }
  return { errors, files };
}

function collectChangedSources(authority, projectRoot) {
  if (!authority) {
    return unavailableChangedSource();
  }
  const errors = [];
  const current = captureScopedSources(projectRoot, authority.changedScope.entries);
  errors.push(...current.errors);
  const before = new Map((authority.preChange.sources || []).map((file) => [file.path, file]));
  for (const filePath of authority.preChange.absentPaths || []) {
    if (!before.has(filePath)) {
      before.set(filePath, { absent: true, path: filePath });
    }
  }
  const files = current.files
    .filter((file) => !before.has(file.path) || before.get(file.path).digest !== file.digest)
    .map((file) => {
      const changedRegions = computeChangedRegions(
        before.get(file.path) && before.get(file.path).contents,
        file.contents,
        file.path
      );
      return {
        ...file,
        changedRegions,
        changedLines: changedRegions.flatMap((region) => region.lines)
      };
    });
  const changedLines = files.flatMap((file) => addedDefensiveLines(
    before.get(file.path) && before.get(file.path).contents,
    file.contents,
    file.path,
    file.changedRegions
  ));
  return {
    changedLines,
    contents: current.files,
    errors,
    files,
    status: errors.length > 0 ? 'INCONCLUSIVE' : files.length > 0 ? 'PASS' : 'INCONCLUSIVE'
  };
}

function unavailableChangedSource() {
  return { changedLines: [], contents: [], errors: [], files: [], status: 'INCONCLUSIVE' };
}

function collectImpactSources(authority, projectRoot, changedSource = null) {
  if (!authority || !authority.impactScope || !Array.isArray(authority.impactScope.fixedPaths)) {
    return unavailableImpactSources();
  }
  const current = captureFixedSources(projectRoot, authority.impactScope.fixedPaths);
  const before = new Map(((authority.preChange && authority.preChange.impactSources) || []).map((file) => [file.path, file]));
  const expectedPaths = [...before.keys()].sort();
  const currentPaths = new Set(current.files.map((file) => file.path));
  const missing = expectedPaths.filter((filePath) => !currentPaths.has(filePath));
  const errors = [...current.errors, ...missing.map((filePath) => `${filePath}: fixed impact source is no longer readable.`)];
  const files = current.files.map((file) => {
    const changedRegions = computeChangedRegions(before.get(file.path) && before.get(file.path).contents, file.contents, file.path);
    return {
      ...file,
      changedRegions,
      changedLines: addedDefensiveLines(
        before.get(file.path) && before.get(file.path).contents,
        file.contents,
        file.path,
        changedRegions
      ),
      changed: !before.has(file.path) || before.get(file.path).digest !== file.digest
    };
  }).sort((left, right) => left.path.localeCompare(right.path));
  const fixedPathSet = new Set(authority.impactScope.fixedPaths);
  const closureErrors = [];
  const currentScopePaths = [...new Set([
    ...authority.impactScope.fixedPaths,
    ...((changedSource && changedSource.files) || []).map((file) => file.path)
  ])].filter((filePath) => isProductSource(filePath));
  const currentReachablePaths = new Set();
  for (const sourcePath of currentScopePaths) {
    const closure = collectModuleClosureDetails(projectRoot, sourcePath);
    closureErrors.push(...closure.unresolved.map((item) => `${item.from}: configured TypeScript module ${item.specifier} could not be resolved.`));
    for (const reachable of closure.paths) {
      if (isProductSource(reachable)) {
        currentReachablePaths.add(reachable);
      }
    }
  }
  const uncoveredReachableSources = [...currentReachablePaths]
    .filter((filePath) => !fixedPathSet.has(filePath))
    .sort();
  const uncoveredChangedSources = changedSource && Array.isArray(changedSource.files)
    ? changedSource.files.filter((file) => isProductSource(file.path) && !fixedPathSet.has(file.path)).map((file) => file.path).sort()
    : [];
  const completenessErrors = uncoveredChangedSources.map((filePath) => `${filePath}: changed product source is absent from the immutable WP-002 impact closure.`);
  const closureCompletenessErrors = uncoveredReachableSources.map((filePath) => `${filePath}: current dependency closure is absent from the immutable WP-002 impact closure.`);
  return {
    errors: [...errors, ...closureErrors, ...completenessErrors, ...closureCompletenessErrors],
    files,
    fixedPaths: authority.impactScope.fixedPaths,
    status: errors.length > 0 || closureErrors.length > 0 || completenessErrors.length > 0 || closureCompletenessErrors.length > 0 || files.length === 0 ? 'INCONCLUSIVE' : 'PASS',
    currentReachablePaths: [...currentReachablePaths].sort(),
    uncoveredChangedSources,
    uncoveredReachableSources
  };
}

function unavailableImpactSources() {
  return { currentReachablePaths: [], errors: [], files: [], fixedPaths: [], status: 'INCONCLUSIVE', uncoveredChangedSources: [], uncoveredReachableSources: [] };
}

function collectSourcePaths(projectRoot, entries, errors) {
  const paths = new Set();
  for (const entry of entries || []) {
    if (!entry || !['exact', 'subtree'].includes(entry.mode) || !safeRelativePath(entry.path, true)) {
      errors.push('The fixed changed scope contains an unsafe path.');
      continue;
    }
    const absolute = path.resolve(projectRoot, ...entry.path.split('/'));
    if (!isWithin(projectRoot, absolute)) {
      errors.push(`The fixed changed scope leaves the project: ${entry.path}.`);
      continue;
    }
    let stat;
    try {
      stat = fs.lstatSync(absolute);
    } catch (error) {
      if (error && error.code === 'ENOENT') {
        continue;
      }
      errors.push(`${entry.path}: ${error.message}`);
      continue;
    }
    if (stat.isSymbolicLink()) {
      errors.push(`${entry.path}: symbolic links cannot establish changed source.`);
    } else if (stat.isFile() && isProductSource(entry.path)) {
      paths.add(entry.path);
    } else if (stat.isDirectory() && entry.mode === 'subtree') {
      collectSourcePathsFromDirectory(projectRoot, absolute, entry.path, paths, errors);
    }
  }
  return [...paths].sort();
}

function collectSourcePathsFromDirectory(projectRoot, directory, relativeDirectory, paths, errors) {
  let entries;
  try {
    entries = fs.readdirSync(directory, { withFileTypes: true });
  } catch (error) {
    errors.push(`${relativeDirectory}: ${error.message}`);
    return;
  }
  for (const entry of entries) {
    const relative = `${relativeDirectory}/${entry.name}`;
    const absolute = path.join(directory, entry.name);
    if (entry.isSymbolicLink()) {
      errors.push(`${relative}: symbolic links cannot establish changed source.`);
    } else if (entry.isDirectory()) {
      if (!IGNORED_DIRECTORIES.has(entry.name)) {
        collectSourcePathsFromDirectory(projectRoot, absolute, relative, paths, errors);
      }
    } else if (entry.isFile() && isProductSource(relative)) {
      paths.add(relative);
    }
  }
}

function collectRelatedTests(projectRoot, changedPaths) {
  const testPaths = collectProjectTestPaths(projectRoot);
  const files = [];
  const closureByTest = [];
  for (const testPath of testPaths) {
    const dependencies = collectModuleClosure(projectRoot, testPath);
    if (dependencies.some((dependency) => changedPaths.includes(dependency))) {
      const file = readProofFile(projectRoot, testPath);
      if (file) {
        files.push(file);
        closureByTest.push({
          files: dependencies.map((dependency) => readProofFile(projectRoot, dependency)).filter(Boolean),
          path: testPath
        });
      }
    }
  }
  return files.length > 0
    ? {
      closureFiles: uniqueTestClosureFiles(closureByTest.flatMap((item) => item.files)),
      files,
      reason: null
    }
    : { files: [], reason: 'No repository test has a resolvable dependency on the fixed changed source.' };
}

function collectImpactRelatedTests(projectRoot, impactFiles) {
  const sourcePaths = impactFiles.map((file) => file.path);
  const selected = new Map(sourcePaths.map((sourcePath) => [sourcePath, []]));
  const selectedClosures = new Map(sourcePaths.map((sourcePath) => [sourcePath, []]));
  const testFiles = [];
  const closureFiles = [];
  for (const testPath of collectProjectTestPaths(projectRoot)) {
    const dependencies = collectModuleClosure(projectRoot, testPath);
    const covered = sourcePaths.filter((sourcePath) => dependencies.includes(sourcePath));
    if (covered.length === 0) {
      continue;
    }
    const file = readProofFile(projectRoot, testPath);
    if (!file) {
      continue;
    }
    testFiles.push(file);
    closureFiles.push(...dependencies.map((dependency) => readProofFile(projectRoot, dependency)).filter(Boolean));
    for (const sourcePath of covered) {
      selected.get(sourcePath).push(file);
      selectedClosures.get(sourcePath).push(...dependencies.map((dependency) => readProofFile(projectRoot, dependency)).filter(Boolean));
    }
  }
  const perSource = sourcePaths.map((sourcePath) => ({
    closureFiles: uniqueProofFiles(selectedClosures.get(sourcePath)),
    files: selected.get(sourcePath),
    path: sourcePath
  }));
  const missingSources = perSource.filter((item) => item.files.length === 0).map((item) => item.path);
  return {
    closureFiles: uniqueTestClosureFiles(closureFiles),
    files: testFiles,
    missingSources,
    perSource,
    reason: missingSources.length > 0
      ? `No retained repository test has a resolvable dependency on fixed impact source: ${missingSources.join(', ')}.`
      : null
  };
}

function unavailableImpactTests() {
  return { closureFiles: [], files: [], missingSources: [], perSource: [], reason: 'A valid fixed dependency impact closure was not available.' };
}

function readProofFile(projectRoot, relativePath) {
  if (typeof relativePath !== 'string' || !safeRelativePath(relativePath, false)) {
    return null;
  }
  try {
    return {
      contents: fs.readFileSync(path.join(projectRoot, ...relativePath.split('/')), 'utf8'),
      path: relativePath
    };
  } catch (error) {
    return null;
  }
}

function uniqueProofFiles(files) {
  const byPath = new Map();
  for (const file of files) {
    if (file && !byPath.has(file.path)) {
      byPath.set(file.path, file);
    }
  }
  return [...byPath.values()].sort((left, right) => left.path.localeCompare(right.path));
}

function uniqueTestClosureFiles(files) {
  // A helper can be imported from any project path; naming conventions are not an authority boundary.
  return uniqueProofFiles(files);
}

function isTestOrHelperPath(filePath) {
  return isTestFile(filePath) ||
    /(?:^|\/)(?:test|tests|__tests__|helpers?|support)(?:\/|$)/i.test(filePath) ||
    /(?:^|[-_.])(?:test|spec|helper)(?:[-_.]|$)/i.test(path.posix.basename(filePath));
}

function collectProjectTestPaths(projectRoot) {
  const paths = [];
  function visit(directory, relativeDirectory) {
    let entries;
    try {
      entries = fs.readdirSync(directory, { withFileTypes: true });
    } catch (error) {
      return;
    }
    for (const entry of entries) {
      const relative = relativeDirectory ? `${relativeDirectory}/${entry.name}` : entry.name;
      const absolute = path.join(directory, entry.name);
      if (entry.isDirectory()) {
        if (!IGNORED_DIRECTORIES.has(entry.name)) {
          visit(absolute, relative);
        }
      } else if (entry.isFile() && isTestFile(relative)) {
        paths.push(relative);
      }
    }
  }
  visit(projectRoot, '');
  return paths.sort();
}

function collectModuleClosure(projectRoot, entryPath) {
  return collectModuleClosureDetails(projectRoot, entryPath).paths;
}

function collectModuleClosureDetails(projectRoot, entryPath) {
  const visited = new Set();
  const unresolved = [];
  const tsconfigCache = new Map();
  const queue = [entryPath];
  while (queue.length > 0) {
    const current = queue.shift();
    if (visited.has(current)) {
      continue;
    }
    visited.add(current);
    let contents;
    try {
      contents = fs.readFileSync(path.join(projectRoot, ...current.split('/')), 'utf8');
    } catch (error) {
      continue;
    }
    for (const specifier of collectModuleSpecifiers(contents)) {
      const resolution = resolveProofModuleSpecifier(projectRoot, current, specifier, tsconfigCache);
      if (resolution.status === 'source' && !visited.has(resolution.path)) {
        queue.push(resolution.path);
      } else if (resolution.status === 'unresolved-configured') {
        unresolved.push({ from: current, specifier });
      }
    }
  }
  return { paths: [...visited], unresolved };
}

function collectModuleSpecifiers(contents) {
  const values = new Set();
  const patterns = [
    /\brequire\s*\(\s*(['"])([^'"\n]+)\1\s*\)/g,
    /\b(?:import|export)\s+(?:[^'"\n]*?\s+from\s+)?(['"])([^'"\n]+)\1/g,
    /\bimport\s*\(\s*(['"])([^'"\n]+)\1\s*\)/g
  ];
  for (const pattern of patterns) {
    for (let match = pattern.exec(contents); match; match = pattern.exec(contents)) {
      values.add(match[2]);
    }
  }
  return [...values];
}

function resolveLocalModule(projectRoot, fromPath, specifier) {
  if (!specifier.startsWith('.')) {
    return null;
  }
  const base = path.resolve(projectRoot, path.dirname(fromPath), specifier);
  if (!isWithin(projectRoot, base)) {
    return null;
  }
  if (base === path.resolve(projectRoot)) {
    return resolvePackageRootModule(projectRoot);
  }
  const candidates = [base];
  if (!path.extname(base)) {
    for (const extension of SOURCE_EXTENSIONS) {
      candidates.push(`${base}${extension}`);
      candidates.push(path.join(base, `index${extension}`));
    }
  }
  for (const candidate of candidates) {
    try {
      if (fs.lstatSync(candidate).isFile()) {
        return displayPath(projectRoot, candidate);
      }
    } catch (error) {
      // Try the next Node and TypeScript resolution candidate.
    }
  }
  return null;
}

function resolveProofModuleSpecifier(projectRoot, fromPath, specifier, tsconfigCache = new Map()) {
  if (specifier.startsWith('.')) {
    const resolved = resolveLocalModule(projectRoot, fromPath, specifier);
    return resolved ? { path: resolved, status: 'source' } : { status: 'missing' };
  }
  const configuration = resolveProofTypeScriptConfiguration(projectRoot, fromPath, tsconfigCache);
  if (!configuration || configuration.status !== 'present') {
    return configuration && configuration.status === 'unsafe'
      ? { status: 'unresolved-configured' }
      : { status: 'external' };
  }
  return resolveConfiguredProofModule(projectRoot, specifier, configuration);
}

function resolveProofTypeScriptConfiguration(projectRoot, fromPath, cache) {
  const sourcePath = path.resolve(projectRoot, ...fromPath.split('/'));
  let directory = path.dirname(sourcePath);
  const root = path.resolve(projectRoot);
  let configPath = null;
  while (isWithin(root, directory)) {
    const candidate = path.join(directory, 'tsconfig.json');
    if (fs.existsSync(candidate)) {
      configPath = candidate;
      break;
    }
    if (directory === root) {
      break;
    }
    directory = path.dirname(directory);
  }
  if (!configPath) {
    return null;
  }
  return resolveProofTsconfig(projectRoot, configPath, cache, new Set());
}

function resolveProofTsconfig(projectRoot, configPath, cache, stack) {
  const normalized = path.resolve(configPath);
  if (cache.has(normalized)) {
    return cache.get(normalized);
  }
  if (!isSafeProofConfigPath(projectRoot, normalized)) {
    const result = { status: 'unsafe' };
    cache.set(normalized, result);
    return result;
  }
  if (stack.has(normalized)) {
    return { status: 'invalid' };
  }
  stack.add(normalized);
  let value;
  try {
    value = readProofTsconfig(normalized);
  } catch (error) {
    const result = { status: 'invalid' };
    cache.set(normalized, result);
    stack.delete(normalized);
    return result;
  }
  if (!isPlainObject(value)) {
    const result = { status: 'invalid' };
    cache.set(normalized, result);
    stack.delete(normalized);
    return result;
  }
  let inherited = { compilerOptionOrigins: {}, compilerOptions: {} };
  if (value.extends !== undefined) {
    if (typeof value.extends !== 'string' || !isRelativeSpecifier(value.extends)) {
      const result = { status: 'invalid' };
      cache.set(normalized, result);
      stack.delete(normalized);
      return result;
    }
    const inheritedResolution = resolveProofLocalConfig(projectRoot, path.dirname(normalized), value.extends);
    if (inheritedResolution.status === 'unsafe') {
      const result = { status: 'unsafe' };
      cache.set(normalized, result);
      stack.delete(normalized);
      return result;
    }
    const inheritedPath = inheritedResolution.path;
    if (!inheritedPath || !isWithin(projectRoot, inheritedPath)) {
      const result = { status: 'invalid' };
      cache.set(normalized, result);
      stack.delete(normalized);
      return result;
    }
    const parent = resolveProofTsconfig(projectRoot, inheritedPath, cache, stack);
    if (parent.status !== 'present') {
      cache.set(normalized, parent);
      stack.delete(normalized);
      return parent;
    }
    inherited = parent;
  }
  const compilerOptions = value.compilerOptions === undefined ? {} : value.compilerOptions;
  if (!isPlainObject(compilerOptions) ||
    (Object.hasOwn(compilerOptions, 'baseUrl') && typeof compilerOptions.baseUrl !== 'string') ||
    (Object.hasOwn(compilerOptions, 'paths') && !isPlainObject(compilerOptions.paths)) ||
    (isPlainObject(compilerOptions.paths) && Object.values(compilerOptions.paths).some((value) => !Array.isArray(value) || value.some((item) => typeof item !== 'string')))) {
    const result = { status: 'invalid' };
    cache.set(normalized, result);
    stack.delete(normalized);
    return result;
  }
  const compilerOptionOrigins = { ...inherited.compilerOptionOrigins };
  for (const key of Object.keys(compilerOptions)) {
    compilerOptionOrigins[key] = path.dirname(normalized);
  }
  const result = {
    compilerOptionOrigins,
    compilerOptions: { ...inherited.compilerOptions, ...compilerOptions },
    configDirectory: path.dirname(normalized),
    status: 'present'
  };
  cache.set(normalized, result);
  stack.delete(normalized);
  return result;
}

function readProofTsconfig(configPath) {
  const contents = fs.readFileSync(configPath, 'utf8');
  let stripped = '';
  let quote = null;
  for (let index = 0; index < contents.length; index += 1) {
    const character = contents[index];
    const next = contents[index + 1];
    if (quote) {
      stripped += character;
      if (character === '\\') {
        stripped += next || '';
        index += 1;
      } else if (character === quote) {
        quote = null;
      }
      continue;
    }
    if (character === '"') {
      quote = character;
      stripped += character;
      continue;
    }
    if (character === '/' && next === '/') {
      index += 2;
      while (index < contents.length && contents[index] !== '\n' && contents[index] !== '\r') {
        index += 1;
      }
      index -= 1;
      continue;
    }
    if (character === '/' && next === '*') {
      index += 2;
      while (index < contents.length) {
        const current = contents[index];
        const following = contents[index + 1];
        if (current === '*' && following === '/') {
          index += 1;
          break;
        }
        stripped += current === '\n' || current === '\r' ? current : ' ';
        index += 1;
      }
      continue;
    }
    stripped += character;
  }
  return JSON.parse(removeProofTrailingCommas(stripped));
}

function removeProofTrailingCommas(contents) {
  let result = '';
  let quote = null;
  for (let index = 0; index < contents.length; index += 1) {
    const character = contents[index];
    if (quote) {
      result += character;
      if (character === '\\') {
        result += contents[index + 1] || '';
        index += 1;
      } else if (character === quote) {
        quote = null;
      }
      continue;
    }
    if (character === '"') {
      quote = character;
      result += character;
      continue;
    }
    if (character === ',') {
      let next = index + 1;
      while (next < contents.length && /\s/.test(contents[next])) {
        next += 1;
      }
      if (contents[next] === '}' || contents[next] === ']') {
        continue;
      }
    }
    result += character;
  }
  return result;
}

function resolveProofLocalConfig(projectRoot, directory, extendsValue) {
  const base = path.resolve(directory, extendsValue);
  const candidates = path.extname(base) ? [base] : [base, `${base}.json`];
  let unsafe = false;
  for (const candidate of candidates) {
    let exists = false;
    try {
      fs.lstatSync(candidate);
      exists = true;
    } catch (error) {
      if (!error || error.code !== 'ENOENT') {
        unsafe = true;
      }
    }
    if (!exists) {
      continue;
    }
    if (!isSafeProofConfigPath(projectRoot, candidate)) {
      unsafe = true;
      continue;
    }
    return { path: candidate, status: 'present' };
  }
  return { path: null, status: unsafe ? 'unsafe' : 'missing' };
}

function isSafeProofConfigPath(projectRoot, configPath) {
  const root = path.resolve(projectRoot);
  const absolute = path.resolve(configPath);
  if (!isWithin(root, absolute)) {
    return false;
  }
  const relative = path.relative(root, absolute);
  if (relative.split(path.sep).includes('node_modules')) {
    return false;
  }
  let current = root;
  try {
    if (fs.lstatSync(current).isSymbolicLink()) {
      return false;
    }
    for (const segment of relative.split(path.sep).filter(Boolean)) {
      current = path.join(current, segment);
      if (fs.lstatSync(current).isSymbolicLink()) {
        return false;
      }
    }
    const realRoot = fs.realpathSync(root);
    const realConfig = fs.realpathSync(absolute);
    return isWithin(realRoot, realConfig);
  } catch (error) {
    return false;
  }
}

function resolveConfiguredProofModule(projectRoot, specifier, configuration) {
  const compilerOptions = configuration.compilerOptions || {};
  const baseUrl = typeof compilerOptions.baseUrl === 'string'
    ? path.resolve(
      (configuration.compilerOptionOrigins && configuration.compilerOptionOrigins.baseUrl) || configuration.configDirectory,
      compilerOptions.baseUrl
    )
    : null;
  const paths = isPlainObject(compilerOptions.paths) ? compilerOptions.paths : null;
  const matches = paths
    ? Object.entries(paths)
      .map(([pattern, substitutions], declarationOrder) => ({
        declarationOrder,
        pattern,
        substitutions,
        wildcard: matchProofTypeScriptPathPattern(pattern, specifier)
      }))
      .filter((match) => match.wildcard !== null)
      .sort(compareProofTypeScriptPathMatches)
    : [];

  for (const match of matches) {
    const resolutionBase = baseUrl || path.resolve(
      (configuration.compilerOptionOrigins && configuration.compilerOptionOrigins.paths) || configuration.configDirectory
    );
    for (const substitution of match.substitutions) {
      const candidate = path.resolve(resolutionBase, substitution.replaceAll('*', match.wildcard));
      const resolved = resolveProofSourceCandidate(projectRoot, candidate);
      if (resolved.status === 'source') {
        return resolved;
      }
    }
    return { status: 'unresolved-configured' };
  }
  if (baseUrl) {
    const resolved = resolveProofSourceCandidate(projectRoot, path.resolve(baseUrl, specifier));
    return resolved.status === 'source' ? resolved : { status: 'external' };
  }
  return { status: 'external' };
}

function resolveProofSourceCandidate(projectRoot, basePath) {
  if (!isWithin(projectRoot, basePath) || displayPath(projectRoot, basePath).split('/').includes('node_modules')) {
    return { status: 'outside' };
  }
  for (const candidate of proofSourceCandidates(basePath)) {
    if (!isWithin(projectRoot, candidate) || displayPath(projectRoot, candidate).split('/').includes('node_modules')) {
      continue;
    }
    if (!SOURCE_EXTENSIONS.some((extension) => candidate.endsWith(extension))) {
      continue;
    }
    try {
      if (fs.lstatSync(candidate).isFile()) {
        return { path: displayPath(projectRoot, candidate), status: 'source' };
      }
    } catch (error) {
      // Try the next source candidate.
    }
  }
  return { status: 'missing' };
}

function proofSourceCandidates(basePath) {
  const candidates = [basePath];
  if (!path.extname(basePath)) {
    for (const extension of SOURCE_EXTENSIONS) {
      candidates.push(`${basePath}${extension}`, path.join(basePath, `index${extension}`));
    }
  }
  return candidates;
}

function matchProofTypeScriptPathPattern(pattern, specifier) {
  const wildcard = pattern.indexOf('*');
  if (wildcard === -1) {
    return pattern === specifier ? '' : null;
  }
  const prefix = pattern.slice(0, wildcard);
  const suffix = pattern.slice(wildcard + 1);
  return specifier.startsWith(prefix) && specifier.endsWith(suffix)
    ? specifier.slice(prefix.length, specifier.length - suffix.length || undefined)
    : null;
}

function compareProofTypeScriptPathMatches(left, right) {
  const leftWildcard = left.pattern.indexOf('*');
  const rightWildcard = right.pattern.indexOf('*');
  if (leftWildcard === -1 || rightWildcard === -1) {
    if (leftWildcard === -1 && rightWildcard !== -1) {
      return -1;
    }
    if (leftWildcard !== -1 && rightWildcard === -1) {
      return 1;
    }
  }
  const prefixDifference = rightWildcard - leftWildcard;
  if (prefixDifference !== 0) {
    return prefixDifference;
  }
  const leftSuffixLength = leftWildcard === -1 ? 0 : left.pattern.length - leftWildcard - 1;
  const rightSuffixLength = rightWildcard === -1 ? 0 : right.pattern.length - rightWildcard - 1;
  const suffixDifference = rightSuffixLength - leftSuffixLength;
  return suffixDifference !== 0 ? suffixDifference : left.declarationOrder - right.declarationOrder;
}

function resolvePackageRootModule(projectRoot) {
  let packageValue;
  try {
    packageValue = JSON.parse(fs.readFileSync(path.join(projectRoot, 'package.json'), 'utf8'));
  } catch (error) {
    return null;
  }
  const entry = packageEntryTarget(packageValue);
  const candidates = entry ? [path.resolve(projectRoot, entry)] : [path.join(projectRoot, 'index.js')];
  for (const candidate of candidates) {
    if (!isWithin(projectRoot, candidate)) {
      continue;
    }
    const resolved = resolveLocalModuleFile(projectRoot, candidate);
    if (resolved) {
      return resolved;
    }
  }
  return null;
}

function packageEntryTarget(packageValue) {
  if (!packageValue || typeof packageValue !== 'object') {
    return null;
  }
  const exportsValue = packageValue.exports;
  const exportTarget = simplePackageExportTarget(exportsValue);
  if (exportTarget) {
    return exportTarget;
  }
  if (typeof packageValue.main === 'string') {
    return packageValue.main;
  }
  return null;
}

function simplePackageExportTarget(value) {
  if (typeof value === 'string') {
    return value;
  }
  if (Array.isArray(value)) {
    for (const candidate of value) {
      const target = simplePackageExportTarget(candidate);
      if (target) {
        return target;
      }
    }
    return null;
  }
  if (!value || typeof value !== 'object') {
    return null;
  }
  const root = Object.hasOwn(value, '.') ? value['.'] : value;
  if (root !== value) {
    return simplePackageExportTarget(root);
  }
  for (const [key, candidate] of Object.entries(root)) {
    if (['require', 'node', 'default'].includes(key)) {
      const target = simplePackageExportTarget(candidate);
      if (target) {
        return target;
      }
    }
  }
  return null;
}

function resolveLocalModuleFile(projectRoot, base) {
  const candidates = [base];
  if (!path.extname(base)) {
    for (const extension of SOURCE_EXTENSIONS) {
      candidates.push(`${base}${extension}`);
      candidates.push(path.join(base, `index${extension}`));
    }
  }
  for (const candidate of candidates) {
    try {
      if (fs.lstatSync(candidate).isFile()) {
        return displayPath(projectRoot, candidate);
      }
    } catch (error) {
      // Try the next Node and TypeScript resolution candidate.
    }
  }
  return null;
}

function resolveTestCapability(projectRoot, relatedTests) {
  let packageValue;
  try {
    packageValue = JSON.parse(fs.readFileSync(path.join(projectRoot, 'package.json'), 'utf8'));
  } catch (error) {
    return { available: false, reason: `The repository test script could not be read: ${error.message}` };
  }
  const command = packageValue && packageValue.scripts && packageValue.scripts.test;
  if (typeof command !== 'string' || command.trim().length === 0) {
    return { available: false, reason: 'The repository does not define a test script.' };
  }
  if (relatedTests.length === 0) {
    return { available: false, reason: 'No directly related repository test was found.' };
  }
  const parsedCommand = parseApprovedTestCommand(command);
  if (parsedCommand.error) {
    return { available: false, reason: parsedCommand.error };
  }
  const includedTests = includedRelatedTests(parsedCommand.targets, relatedTests.map((file) => file.path));
  if (!includedTests) {
    return {
      available: false,
      reason: 'The repository-defined test command does not explicitly include every directly related test.'
    };
  }
  return {
    available: true,
    command,
    relatedTests: includedTests,
    runner: `${process.execPath} --test ${includedTests.join(' ')}`
  };
}

function resolveImpactTestCapability(projectRoot, related) {
  if (related.missingSources.length > 0) {
    return {
      available: false,
      reason: `No retained repository test covers every fixed impact source: ${related.missingSources.join(', ')}.`
    };
  }
  return resolveTestCapability(projectRoot, related.files);
}

function parseApprovedTestCommand(command) {
  if (typeof command !== 'string' || command.length === 0 || command !== command.trim()) {
    return { error: 'The repository test script must use the exact direct node --test form.' };
  }
  if (/[\u0000-\u001f\u007f]/.test(command) || /[^\S ]/.test(command) || /[`'"$;&|<>\\()[\]{}]/.test(command)) {
    return { error: 'The repository test script contains control whitespace or shell syntax.' };
  }
  if (!/^node --test [^ ]+(?: [^ ]+)*$/.test(command)) {
    return { error: 'The repository test script must be exactly node --test followed by safe test targets.' };
  }
  const targets = command.split(' ').slice(2);
  if (targets.length === 0 || targets.some((target) => target.startsWith('-') || !safeTestTarget(target))) {
    return { error: 'The repository test script contains an unsafe target or unsupported flag.' };
  }
  return { error: null, targets };
}

function includedRelatedTests(targets, relatedTests) {
  if (targets.length === 0 || targets.some((target) => target.startsWith('-'))) {
    return null;
  }
  return relatedTests.every((testPath) => targets.some((target) => testTargetMatches(target, testPath)))
    ? [...relatedTests]
    : null;
}

function testTargetMatches(target, testPath) {
  if (!safeTestTarget(target)) {
    return false;
  }
  const normalized = target.replace(/^\.\//, '');
  let expression = '^';
  for (let index = 0; index < normalized.length; index += 1) {
    const character = normalized[index];
    if (character === '*' && normalized[index + 1] === '*') {
      if (normalized[index + 2] === '/') {
        expression += '(?:.*/)?';
        index += 2;
      } else {
        expression += '.*';
        index += 1;
      }
    } else if (character === '*') {
      expression += '[^/]*';
    } else if (character === '?') {
      expression += '[^/]';
    } else {
      expression += character.replace(/[|\\{}()[\]^$+?.]/g, '\\$&');
    }
  }
  return new RegExp(`${expression}$`).test(testPath);
}

function safeTestTarget(value) {
  return typeof value === 'string' && value.length > 0 && !value.includes('\\') &&
    !path.posix.isAbsolute(value) && !path.win32.isAbsolute(value) && !/^[A-Za-z]:/.test(value) &&
    !value.includes('\u0000') && !/[\u0000-\u001f\u007f]/.test(value) && !/\s/.test(value) &&
    !value.split('/').some((part) => part === '..' || part === '') &&
    value.split('/').every((part, index) => !(part === '.' && index !== 0));
}

function runRepositoryTests(projectRoot, capability) {
  return withDisposableCopy(projectRoot, (copyRoot, copyRootFd) => {
    const outcome = runTestCommand(copyRoot, capability.relatedTests, copyRootFd);
    return {
      ...outcome,
      command: capability.command,
      relatedTests: capability.relatedTests,
      status: outcome.status === 'PASS' ? 'PASS' : outcome.status
    };
  });
}

function impactExecution(status, related) {
  return {
    perSource: related.perSource.map((item) => ({
      path: item.path,
      relatedTests: item.files.map((file) => file.path),
      status
    })),
    relatedTests: related.files.map((file) => file.path),
    status
  };
}

function attachImpactExecution(execution, related) {
  return {
    ...execution,
    perSource: related.perSource.map((item) => ({
      path: item.path,
      relatedTests: item.files.map((file) => file.path),
      status: execution.status
    }))
  };
}

function runMutationProbes(projectRoot, capability, changedFiles) {
  const generated = collectMutationCandidates(changedFiles, { changedOnly: true });
  if (generated.error) {
    return mutationCapabilityFailure(generated.error, capability.relatedTests);
  }
  return executeMutationGroups(projectRoot, capability.relatedTests, changedFiles, generated.candidates, 'related');
}

function runImpactMutationProbes(projectRoot, capability, impactFiles, related) {
  const perSource = impactFiles.map((file) => runImpactSourceMutation(projectRoot, capability, file, related));
  const candidates = perSource.flatMap((item) => item.candidates);
  const status = perSource.some((item) => item.status === 'INCONCLUSIVE')
    ? 'INCONCLUSIVE'
    : perSource.some((item) => item.status === 'FAIL')
      ? 'FAIL'
      : 'PASS';
  return {
    candidates,
    detected: perSource.filter((item) => item.status === 'PASS').length,
    message: status === 'PASS'
      ? 'Every fixed impact source had a valid mutation detected by repository-defined impact tests.'
      : status === 'FAIL'
        ? 'At least one fixed impact source had valid mutations that repository-defined impact tests did not detect.'
        : 'At least one fixed impact source did not have trustworthy mutation capability or reliable mutation execution.',
    perSource,
    relatedTests: capability.relatedTests,
    status
  };
}

function runImpactSourceMutation(projectRoot, capability, sourceFile, related) {
  const generated = collectMutationCandidates([sourceFile], { changedOnly: sourceFile.changed });
  if (generated.error) {
    return mutationCapabilityFailure(generated.error, related.perSource.find((item) => item.path === sourceFile.path)?.files.map((file) => file.path) || [], sourceFile.path);
  }
  const candidates = generated.candidates;
  const relatedTests = related.perSource.find((item) => item.path === sourceFile.path);
  if (candidates.length === 0) {
    return {
      candidates: [],
      message: 'No trustworthy runtime mutation could be generated for this fixed impact source.',
      path: sourceFile.path,
      relatedTests: relatedTests ? relatedTests.files.map((file) => file.path) : [],
      status: 'INCONCLUSIVE'
    };
  }
  const relatedPaths = relatedTests ? relatedTests.files.map((file) => file.path) : [];
  const result = executeMutationGroups(projectRoot, relatedPaths, [sourceFile], candidates, 'impact');
  return {
    ...result,
    message: result.status === 'PASS'
      ? 'A repository-defined impact test detected a valid mutation in every changed region of this fixed impact source.'
      : result.status === 'FAIL'
        ? 'Repository-defined impact tests did not detect a valid mutation in every changed region of this fixed impact source.'
        : result.message,
    path: sourceFile.path,
    relatedTests: relatedPaths
  };
}

function impactMutationNotRun(impactFiles, related) {
  return {
    candidates: [],
    detected: 0,
    message: 'Required fixed-impact mutation execution was not run.',
    perSource: impactFiles.map((file) => ({
      candidates: [],
      message: 'Required fixed-impact mutation execution was not run.',
      path: file.path,
      relatedTests: related.perSource.find((item) => item.path === file.path)?.files.map((testFile) => testFile.path) || [],
      status: 'NOT_RUN'
    })),
    relatedTests: related.files.map((file) => file.path),
    status: 'NOT_RUN'
  };
}

function withDisposableCopy(projectRoot, action) {
  let temporaryDirectory;
  let copyRootFd;
  try {
    validateDisposableSource(projectRoot);
    temporaryDirectory = fs.mkdtempSync(path.join(os.tmpdir(), 'node-policy-checker-behavior-proof-'));
    const copyRoot = path.join(temporaryDirectory, 'project');
    fs.cpSync(projectRoot, copyRoot, { dereference: false, recursive: true, verbatimSymlinks: true });
    const copyRootIdentity = fs.lstatSync(copyRoot);
    validateDisposableSource(copyRoot);
    copyRootFd = openDisposableDirectory(copyRoot, copyRootIdentity);
    return action(copyRoot, copyRootFd);
  } catch (error) {
    return { error: error.message, status: 'INCONCLUSIVE' };
  } finally {
    if (copyRootFd !== undefined) {
      try {
        fs.closeSync(copyRootFd);
      } catch (error) {
        // The descriptor is best-effort cleanup after the disposable result is fixed.
      }
    }
    if (temporaryDirectory) {
      fs.rmSync(temporaryDirectory, { force: true, recursive: true });
    }
  }
}

function openDisposableDirectory(directory, expectedIdentity = null) {
  if (process.platform !== 'linux' || typeof fs.constants.O_NOFOLLOW !== 'number' || typeof fs.constants.O_DIRECTORY !== 'number') {
    throw new Error('Race-resistant disposable-directory binding is unavailable on this platform.');
  }
  const fd = fs.openSync(directory, fs.constants.O_RDONLY | fs.constants.O_DIRECTORY | fs.constants.O_NOFOLLOW);
  try {
    const stat = fs.fstatSync(fd);
    if (!stat.isDirectory() || (expectedIdentity && (stat.dev !== expectedIdentity.dev || stat.ino !== expectedIdentity.ino))) {
      throw new Error('The disposable project root must remain a directory.');
    }
    return fd;
  } catch (error) {
    fs.closeSync(fd);
    throw error;
  }
}

function disposablePath(directory, directoryFd, relativePath) {
  return directoryFd === undefined
    ? path.join(directory, ...relativePath.split('/'))
    : path.join('/proc/self/fd', String(directoryFd), ...relativePath.split('/'));
}

function validateDisposableSource(projectRoot) {
  let root;
  try {
    root = fs.lstatSync(projectRoot);
  } catch (error) {
    throw new Error(`The disposable project root could not be inspected: ${error.message}`);
  }
  if (root.isSymbolicLink() || !root.isDirectory()) {
    throw new Error('The disposable project root must be a regular directory.');
  }
  validateSymlinkTree(projectRoot, projectRoot);
}

function validateSymlinkTree(directory, treeRoot) {
  let entries;
  try {
    entries = fs.readdirSync(directory, { withFileTypes: true });
  } catch (error) {
    throw new Error(`The disposable project tree could not be read: ${error.message}`);
  }
  for (const entry of entries) {
    const absolutePath = path.join(directory, entry.name);
    if (entry.isSymbolicLink()) {
      validateSymlink(absolutePath, treeRoot);
    } else if (entry.isDirectory()) {
      validateSymlinkTree(absolutePath, treeRoot);
    }
  }
}

function validateSymlink(linkPath, treeRoot) {
  const target = fs.readlinkSync(linkPath);
  if (path.posix.isAbsolute(target) || path.win32.isAbsolute(target) || /^[A-Za-z]:/.test(target)) {
    throw new Error(`The copied symbolic link is absolute: ${displayPath(treeRoot, linkPath)}.`);
  }
  let current = linkPath;
  const seen = new Set();
  for (;;) {
    if (seen.has(current)) {
      throw new Error(`The copied symbolic link is cyclic: ${displayPath(treeRoot, linkPath)}.`);
    }
    seen.add(current);
    let currentTarget;
    try {
      currentTarget = fs.readlinkSync(current);
    } catch (error) {
      break;
    }
    if (path.posix.isAbsolute(currentTarget) || path.win32.isAbsolute(currentTarget) || /^[A-Za-z]:/.test(currentTarget)) {
      throw new Error(`The copied symbolic link chain is absolute: ${displayPath(treeRoot, linkPath)}.`);
    }
    const resolved = path.resolve(path.dirname(current), currentTarget);
    if (!isWithin(treeRoot, resolved)) {
      throw new Error(`The copied symbolic link leaves the project: ${displayPath(treeRoot, linkPath)}.`);
    }
    try {
      fs.lstatSync(resolved);
    } catch (error) {
      throw new Error(`The copied symbolic link is dangling: ${displayPath(treeRoot, linkPath)}.`);
    }
    current = resolved;
  }
  let realTarget;
  try {
    realTarget = fs.realpathSync(linkPath);
  } catch (error) {
    throw new Error(`The copied symbolic link cannot be resolved: ${displayPath(treeRoot, linkPath)}.`);
  }
  if (!isWithin(treeRoot, realTarget)) {
    throw new Error(`The copied symbolic link ultimately leaves the project: ${displayPath(treeRoot, linkPath)}.`);
  }
}

function runTestCommand(directory, testPaths, directoryFd = undefined) {
  if (!Array.isArray(testPaths) || testPaths.length === 0 || testPaths.some((testPath) => !safeTestTarget(testPath))) {
    return { error: 'The selected repository test paths are unavailable or unsafe.', status: 'INCONCLUSIVE' };
  }
  const sandbox = ensureSandboxCapability(directory, directoryFd);
  if (sandbox.error) {
    return { error: sandbox.error, status: 'INCONCLUSIVE' };
  }
  let result;
  try {
    result = childProcess.spawnSync(BUBBLEWRAP_COMMAND, sandboxArguments(directory, [
      process.execPath,
      '--test',
      ...testPaths
    ], directoryFd), {
      encoding: 'utf8',
      env: testEnvironment(),
      maxBuffer: 1024 * 1024,
      ...(directoryFd === undefined ? {} : { stdio: ['ignore', 'pipe', 'pipe', directoryFd] }),
      timeout: TEST_TIMEOUT_MS
    });
  } catch (error) {
    return { error: error.message, status: 'INCONCLUSIVE' };
  }
  if (result.error || result.signal || result.status === null) {
    return {
      error: result.error ? result.error.message : result.signal ? `Test command ended with ${result.signal}.` : 'Test command did not report an exit status.',
      status: 'INCONCLUSIVE'
    };
  }
  return {
    exitCode: result.status,
    stderr: limitOutput(result.stderr),
    stdout: limitOutput(result.stdout),
    status: result.status === 0 ? 'PASS' : 'FAIL'
  };
}

let sandboxCapability = null;

function ensureSandboxCapability(directory, directoryFd = undefined) {
  if (sandboxCapability) {
    return sandboxCapability;
  }
  let probe;
  try {
    probe = childProcess.spawnSync(BUBBLEWRAP_COMMAND, sandboxArguments(directory, [
      process.execPath,
      '-e',
      SANDBOX_SECURITY_PROBE
    ], directoryFd), {
      encoding: 'utf8',
      env: testEnvironment(),
      maxBuffer: 1024 * 1024,
      ...(directoryFd === undefined ? {} : { stdio: ['ignore', 'pipe', 'pipe', directoryFd] }),
      timeout: TEST_TIMEOUT_MS
    });
  } catch (error) {
    sandboxCapability = { error: `The Linux process sandbox could not be started: ${error.message}` };
    return sandboxCapability;
  }
  if (probe.error || probe.signal || probe.status !== 0) {
    sandboxCapability = {
      error: `The Linux process sandbox capability is unavailable: ${probe.error ? probe.error.message : limitOutput(probe.stderr || probe.stdout)}`
    };
    return sandboxCapability;
  }
  sandboxCapability = { error: null };
  return sandboxCapability;
}

function sandboxArguments(directory, command, directoryFd = undefined) {
  if (!Number.isInteger(directoryFd)) {
    throw new Error('The disposable project directory FD is required for sandbox binding.');
  }
  const runtime = resolveSandboxRuntime();
  const argumentsList = [
    '--die-with-parent',
    '--unshare-all',
    '--unshare-net',
    '--new-session',
    '--clearenv',
    '--tmpfs',
    '/',
  ];
  const createdDirectories = new Set(['/']);
  for (const mount of runtime.mounts) {
    addSandboxDirectory(argumentsList, mount.destination, mount.type === 'file', createdDirectories);
    argumentsList.push('--ro-bind', mount.source, mount.destination);
  }
  argumentsList.push(
    '--tmpfs',
    '/tmp',
    '--proc',
    '/proc',
    '--dev',
    '/dev',
    '--dir',
    SANDBOX_ROOT,
    '--dir',
    '/tmp/home',
    '--bind',
    directoryFd === undefined ? directory : `/proc/self/fd/${DIRECTORY_BIND_FD}`,
    SANDBOX_ROOT,
    '--chdir',
    SANDBOX_ROOT,
    '--setenv',
    'PATH',
    runtime.nodeBinDirectory,
    '--setenv',
    'HOME',
    '/tmp/home',
    '--setenv',
    'TMPDIR',
    '/tmp',
    '--setenv',
    'NODE_OPTIONS',
    '',
    ...command
  );
  return argumentsList;
}

function resolveSandboxRuntime() {
  if (sandboxRuntime) {
    return sandboxRuntime;
  }
  if (process.platform !== 'linux') {
    throw new Error('The Linux process sandbox is unavailable on this platform.');
  }
  const execPath = path.resolve(process.execPath);
  const mounts = [];
  for (const source of SANDBOX_RUNTIME_TREES) {
    assertSandboxRuntimeSource(source, 'directory');
    mounts.push({ destination: source, source, type: 'directory' });
  }
  const nodeRoot = nvmNodeInstallationRoot(execPath);
  if (nodeRoot) {
    assertSandboxRuntimeSource(nodeRoot, 'directory');
    mounts.push({ destination: nodeRoot, source: nodeRoot, type: 'directory' });
  } else {
    assertSandboxRuntimeSource(execPath, 'file');
    mounts.push({ destination: execPath, source: execPath, type: 'file' });
  }
  sandboxRuntime = {
    mounts,
    nodeBinDirectory: path.dirname(execPath)
  };
  return sandboxRuntime;
}

function nvmNodeInstallationRoot(execPath) {
  const marker = `${path.sep}.nvm${path.sep}versions${path.sep}node${path.sep}`;
  const markerIndex = execPath.indexOf(marker);
  if (markerIndex === -1 || path.basename(path.dirname(execPath)) !== 'bin') {
    return null;
  }
  const versionStart = markerIndex + marker.length;
  const versionEnd = execPath.indexOf(path.sep, versionStart);
  return versionEnd > versionStart ? execPath.slice(0, versionEnd) : null;
}

function assertSandboxRuntimeSource(source, type) {
  let stat;
  try {
    stat = fs.statSync(source);
  } catch (error) {
    throw new Error(`The sandbox runtime source could not be established: ${source}: ${error.message}`);
  }
  if ((type === 'directory' && !stat.isDirectory()) || (type === 'file' && !stat.isFile())) {
    throw new Error(`The sandbox runtime source has the wrong type: ${source}.`);
  }
}

function addSandboxDirectory(argumentsList, destination, isFile, createdDirectories) {
  const directory = isFile ? path.posix.dirname(destination) : destination;
  const segments = directory.split('/').filter(Boolean);
  let current = '';
  for (const segment of segments) {
    current += `/${segment}`;
    if (!createdDirectories.has(current)) {
      createdDirectories.add(current);
      argumentsList.push('--dir', current);
    }
  }
}

function collectMutationCandidates(changedFiles, options = {}) {
  const parser = loadBehaviorParser();
  if (parser.error) {
    return { candidates: [], error: parser.error };
  }
  const candidates = [];
  for (const file of changedFiles) {
    let parsed;
    try {
      parsed = parser.parse(file.contents, {
        plugins: proofParserPlugins(file.path),
        ranges: true,
        sourceType: 'unambiguous'
      }).program;
    } catch (error) {
      return { candidates: [], error: `${file.path}: ${error.message}` };
    }
    const regions = options.changedOnly === false || file.changed === false
      ? [wholeFileRegion(file)]
      : (file.changedRegions || []);
    for (const region of regions) {
      let regionCount = 0;
      visitBehaviorNode(parsed, (node, ancestors) => {
        if (regionCount >= 12 || !Number.isInteger(node.start) || !Number.isInteger(node.end) || !mutationNodeInRegion(node, region) || isNonExecutableMutationNode(node, ancestors)) {
          return;
        }
        if (['StringLiteral', 'BooleanLiteral', 'NumericLiteral', 'NullLiteral', 'TemplateLiteral'].includes(node.type)) {
          const replacement = mutationReplacement(node, file.contents);
          if (replacement) {
            const candidate = addAstMutation(candidates, file, node, replacement, literalMutationKind(node), region);
            regionCount += candidate ? 1 : 0;
          }
        } else if (['IfStatement', 'ConditionalExpression'].includes(node.type) && node.test && node.test.type === 'BooleanLiteral' && mutationNodeInRegion(node.test, region)) {
          const replacement = node.test.type === 'BooleanLiteral' && node.test.value === true ? 'false' : 'true';
          const candidate = addAstMutation(candidates, file, node.test, replacement, 'condition', region);
          regionCount += candidate ? 1 : 0;
        } else if (['BinaryExpression', 'LogicalExpression'].includes(node.type)) {
          const operator = operatorSourceSpan(node, file.contents);
          const replacement = operator && mutationOperatorReplacement(node.operator);
          if (operator && replacement && region.spans.some((span) => spansOverlap(operator.start, operator.end, span))) {
            const candidate = addMutation(
              candidates,
              file,
              operator.start,
              operator.end,
              replacement,
              `operator:${node.operator}`,
              region,
              node.loc && node.loc.start ? node.loc.start.line : lineAt(file.contents, operator.start)
            );
            regionCount += candidate ? 1 : 0;
          }
        }
      });
    }
  }
  return { candidates, error: null };
}

function loadBehaviorParser() {
  try {
    const parser = require('@babel/parser');
    if (typeof parser.parse !== 'function') {
      throw new TypeError('@babel/parser does not expose parse.');
    }
    return { error: null, parse: parser.parse };
  } catch (error) {
    return { error: error.message };
  }
}

function proofParserPlugins(filePath) {
  const plugins = [];
  if (/\.(cts|mts|tsx|ts)$/.test(filePath)) {
    plugins.push('typescript');
  }
  if (/\.(jsx|tsx)$/.test(filePath)) {
    plugins.push('jsx');
  }
  return plugins;
}

function visitBehaviorNode(node, visitor, ancestors = []) {
  if (!isBehaviorAstNode(node)) {
    return;
  }
  visitor(node, ancestors);
  for (const value of Object.values(node)) {
    if (isBehaviorAstNode(value)) {
      visitBehaviorNode(value, visitor, [...ancestors, node]);
    } else if (Array.isArray(value)) {
      for (const item of value) {
        if (isBehaviorAstNode(item)) {
          visitBehaviorNode(item, visitor, [...ancestors, node]);
        }
      }
    }
  }
}

function isBehaviorAstNode(value) {
  return Boolean(value && typeof value === 'object' && typeof value.type === 'string' && !value.type.startsWith('Comment'));
}

function isNonExecutableMutationNode(node, ancestors) {
  if (node.type === 'DirectiveLiteral') {
    return true;
  }
  if (ancestors.some((ancestor) => ['TSTypeAnnotation', 'TSLiteralType', 'TSTemplateLiteralType', 'TSTypeParameter', 'TSInterfaceBody', 'TSInterfaceDeclaration', 'TSTypeAliasDeclaration'].includes(ancestor.type))) {
    return true;
  }
  if (ancestors.some((ancestor) => ['ObjectProperty', 'ObjectMethod', 'ClassMethod', 'ClassProperty'].includes(ancestor.type) && ancestor.key === node && !ancestor.computed)) {
    return true;
  }
  if (ancestors.some((ancestor) => ancestor.type === 'CallExpression' && ancestor.callee && ancestor.callee.type === 'Identifier' && ancestor.callee.name === 'require')) {
    return true;
  }
  if (ancestors.some((ancestor) => [
    'ImportDeclaration',
    'ExportAllDeclaration',
    'ExportSpecifier',
    'ExportNamespaceSpecifier',
    'ExportDefaultSpecifier'
  ].includes(ancestor.type))) {
    return true;
  }
  const parent = ancestors.at(-1);
  return Boolean(parent && parent.type === 'ExportNamedDeclaration' && parent.source === node);
}

function nodeInRegion(node, region) {
  const startLine = node.loc && node.loc.start ? node.loc.start.line : lineAt(region.contents || '', node.start);
  const endLine = node.loc && node.loc.end ? node.loc.end.line : startLine;
  return startLine <= region.currentEnd && endLine >= region.currentStart;
}

function mutationReplacement(node, contents) {
  if (node.type === 'StringLiteral') {
    return JSON.stringify('__behavior_proof_mutated__');
  }
  if (node.type === 'BooleanLiteral') {
    return node.value ? 'false' : 'true';
  }
  if (node.type === 'NumericLiteral' && Number.isFinite(node.value)) {
    return String(node.value === 0 ? 1 : node.value + 1);
  }
  if (node.type === 'NullLiteral') {
    return 'undefined';
  }
  if (node.type === 'TemplateLiteral') {
    return JSON.stringify('__behavior_proof_mutated__');
  }
  return contents.slice(node.start, node.end);
}

function literalMutationKind(node) {
  return node.type === 'StringLiteral'
    ? 'string-literal'
    : node.type === 'BooleanLiteral'
      ? 'boolean-literal'
      : node.type === 'NumericLiteral'
        ? 'numeric-literal'
        : node.type === 'TemplateLiteral'
          ? 'template-literal'
          : 'null-literal';
}

function addAstMutation(candidates, file, node, after, kind, region) {
  return addMutation(
    candidates,
    file,
    node.start,
    node.end,
    after,
    kind,
    region,
    node.loc && node.loc.start ? node.loc.start.line : lineAt(file.contents, node.start)
  );
}

function addMutation(candidates, file, start, end, after, kind, region, line) {
  const before = file.contents.slice(start, end);
  if (before === after || candidates.some((candidate) => candidate.path === file.path && candidate.index === start)) {
    return null;
  }
  candidates.push({
    after,
    before,
    contents: `${file.contents.slice(0, start)}${after}${file.contents.slice(end)}`,
    index: start,
    kind,
    line,
    path: file.path,
    regionId: region.id
  });
  return candidates.at(-1);
}

function mutationCapabilityFailure(error, relatedTests, pathValue = undefined) {
  return {
    candidates: [],
    ...(pathValue ? { path: pathValue } : {}),
    message: `Mutation AST or sandbox capability is unavailable: ${error}`,
    relatedTests,
    status: 'INCONCLUSIVE'
  };
}

function executeMutationGroups(projectRoot, relatedTests, sourceFiles, candidates, scope) {
  const probes = [];
  const perRegion = [];
  for (const file of sourceFiles) {
    const regions = file.changed === false ? [wholeFileRegion(file)] : (file.changedRegions || []);
    for (const region of regions) {
      const regionCandidates = candidates.filter((candidate) => {
        return candidate.path === file.path && candidate.regionId === region.id;
      });
      if (regionCandidates.length === 0) {
        perRegion.push({
          candidates: [],
          path: file.path,
          regionId: region.id,
          status: 'INCONCLUSIVE'
        });
        continue;
      }
      let detected = false;
      let undetected = false;
      let inconclusive = false;
      let status = 'FAIL';
      for (const candidate of regionCandidates) {
        const outcome = withDisposableCopy(projectRoot, (copyRoot, copyRootFd) => {
          try {
            fs.writeFileSync(disposablePath(copyRoot, copyRootFd, candidate.path), candidate.contents, 'utf8');
          } catch (error) {
            return { error: error.message, status: 'INCONCLUSIVE' };
          }
          return runTestCommand(copyRoot, relatedTests, copyRootFd);
        });
        const probe = {
          after: candidate.after,
          before: candidate.before,
          kind: candidate.kind,
          line: candidate.line,
          path: candidate.path,
          regionId: candidate.regionId,
          result: outcome
        };
        probes.push(probe);
        if (outcome.status === 'FAIL') {
          detected = true;
        } else if (outcome.status === 'INCONCLUSIVE') {
          inconclusive = true;
        } else {
          undetected = true;
        }
      }
      status = inconclusive
        ? 'INCONCLUSIVE'
        : undetected
          ? 'FAIL'
          : detected
            ? 'PASS'
            : 'FAIL';
      perRegion.push({
        candidates: probes.filter((candidate) => candidate.path === file.path && candidate.regionId === region.id),
        detected,
        path: file.path,
        regionId: region.id,
        status
      });
    }
  }
  const status = perRegion.length === 0 || perRegion.some((region) => region.status === 'INCONCLUSIVE')
    ? 'INCONCLUSIVE'
    : perRegion.some((region) => region.status === 'FAIL')
      ? 'FAIL'
      : 'PASS';
  return {
    candidates: probes,
    detected: perRegion.filter((region) => region.status === 'PASS').length,
    message: status === 'PASS'
      ? `Every applicable ${scope} changed region had a trustworthy mutation detected by retained repository tests.`
      : status === 'FAIL'
        ? `Retained repository tests did not detect a trustworthy mutation in every applicable ${scope} changed region.`
        : `At least one applicable ${scope} changed region lacks trustworthy mutation or sandbox evidence.`,
    perRegion,
    relatedTests,
    status
  };
}

function wholeFileRegion(file) {
  const lineCount = file.contents.split(/\r?\n/).length;
  return {
    beforeEnd: 0,
    beforeStart: 0,
    currentEnd: Math.max(1, lineCount),
    currentStart: 1,
    id: `whole:${file.path}`,
    lines: file.contents.split(/\r?\n/).map((text, index) => ({
      line: index + 1,
      path: file.path,
      text: text.trim()
    })),
    spans: [{ start: 0, end: file.contents.length }]
  };
}

function computeChangedRegions(beforeContents, afterContents, filePath) {
  const afterText = String(afterContents);
  if (beforeContents === undefined || beforeContents === null) {
    return changeDiffWithinBudget('', afterText)
      ? [wholeFileRegion({ contents: afterText, path: filePath })]
      : [budgetExceededChangedRegion(afterText, filePath)];
  }
  const beforeText = String(beforeContents);
  if (beforeText === afterText) {
    return [];
  }
  if (!changeDiffWithinBudget(beforeText, afterText)) {
    return [budgetExceededChangedRegion(afterText, filePath)];
  }
  const changedSpans = computeChangedSpans(beforeText, afterText);
  if (!changedSpans) {
    return [budgetExceededChangedRegion(afterText, filePath)];
  }
  const beforeLines = beforeText.split(/\r?\n/);
  const afterLines = afterText.split(/\r?\n/);
  const operations = boundedDiffLineOperations(beforeLines, afterLines);
  if (!operations) {
    return [budgetExceededChangedRegion(afterText, filePath)];
  }
  const regions = [];
  let beforeLine = 1;
  let currentLine = 1;
  let pending = null;
  const flush = () => {
    if (!pending) {
      return;
    }
    const currentEnd = pending.inserted > 0 ? currentLine - 1 : pending.currentStart - 1;
    const rangeStart = offsetAtLine(afterContents, pending.currentStart);
    const rangeEnd = offsetAtLine(afterContents, currentEnd + 1);
    regions.push({
      beforeEnd: beforeLine - 1,
      beforeStart: pending.beforeStart,
      currentEnd,
      currentStart: pending.currentStart,
      id: `${filePath}:${regions.length + 1}`,
      lines: currentEnd >= pending.currentStart
        ? afterLines.slice(pending.currentStart - 1, currentEnd).map((text, index) => ({
          line: pending.currentStart + index,
          path: filePath,
          text: text.trim()
        }))
        : [],
      spans: changedSpans.filter((span) => {
        const point = span.end > span.start ? span.start : span.start - 1;
        return point >= rangeStart && point < Math.max(rangeEnd, rangeStart + 1);
      })
    });
    pending = null;
  };
  for (const operation of operations) {
    if (operation === 'equal') {
      flush();
      beforeLine += 1;
      currentLine += 1;
      continue;
    }
    if (!pending) {
      pending = { beforeStart: beforeLine, currentStart: currentLine, inserted: 0 };
    }
    if (operation === 'delete') {
      beforeLine += 1;
    } else {
      currentLine += 1;
      pending.inserted += 1;
    }
  }
  flush();
  return regions;
}

function changeDiffWithinBudget(beforeContents, afterContents) {
  const totalBytes = Buffer.byteLength(beforeContents, 'utf8') + Buffer.byteLength(afterContents, 'utf8');
  if (totalBytes > CHANGE_DIFF_MAX_BYTES) {
    return false;
  }
  const beforeLines = physicalLineCount(beforeContents);
  const afterLines = physicalLineCount(afterContents);
  return beforeLines <= CHANGE_DIFF_MAX_LINES && afterLines <= CHANGE_DIFF_MAX_LINES;
}

function boundedDiffLineOperations(beforeLines, afterLines) {
  const prefix = commonPrefixLength(beforeLines, afterLines);
  const suffix = commonSuffixLength(beforeLines, afterLines, prefix);
  const beforeEnd = beforeLines.length - suffix;
  const afterEnd = afterLines.length - suffix;
  const beforeMiddle = beforeLines.slice(prefix, beforeEnd);
  const afterMiddle = afterLines.slice(prefix, afterEnd);
  const frontier = beforeMiddle.length + afterMiddle.length;
  if (frontier * frontier > CHANGE_DIFF_MAX_FRONTIER_WORK) {
    return null;
  }
  return [
    ...Array(prefix).fill('equal'),
    ...diffLineOperations(beforeMiddle, afterMiddle),
    ...Array(suffix).fill('equal')
  ];
}

function budgetExceededChangedRegion(contents, filePath) {
  return {
    beforeEnd: 0,
    beforeStart: 0,
    budgetExceeded: true,
    currentEnd: physicalLineCount(contents),
    currentStart: 1,
    id: `budget:${filePath}`,
    lines: [],
    spans: []
  };
}

function physicalLineCount(contents) {
  if (!contents) {
    return 0;
  }
  let lines = 1;
  for (let index = 0; index < contents.length; index += 1) {
    if (contents[index] === '\n') {
      lines += 1;
    }
  }
  return lines;
}

function mutationNodeInRegion(node, region) {
  if (!region || !Array.isArray(region.spans)) {
    return nodeInRegion(node, region);
  }
  return region.spans.some((span) => spansOverlap(node.start, node.end, span));
}

function spansOverlap(start, end, span) {
  if (!span || !Number.isInteger(span.start) || !Number.isInteger(span.end)) {
    return false;
  }
  return span.end > span.start
    ? start < span.end && end > span.start
    : start < span.start && end >= span.start;
}

function computeChangedSpans(beforeContents, afterContents) {
  if (beforeContents === afterContents) {
    return [];
  }
  const prefix = commonPrefixLength(beforeContents, afterContents);
  const suffix = commonSuffixLength(beforeContents, afterContents, prefix);
  const beforeEnd = beforeContents.length - suffix;
  const afterEnd = afterContents.length - suffix;
  const beforeMiddle = beforeContents.slice(prefix, beforeEnd);
  const afterMiddle = afterContents.slice(prefix, afterEnd);
  const frontier = beforeMiddle.length + afterMiddle.length;
  if (beforeMiddle.length > CHANGE_DIFF_MAX_EXACT_CHARS ||
    afterMiddle.length > CHANGE_DIFF_MAX_EXACT_CHARS ||
    frontier * frontier > CHANGE_DIFF_MAX_FRONTIER_WORK) {
    return null;
  }
  const beforeUnits = beforeMiddle.split('');
  const afterUnits = afterMiddle.split('');
  const operations = diffLineOperations(beforeUnits, afterUnits);
  const spans = [];
  let beforeIndex = 0;
  let afterIndex = 0;
  let start = null;
  let end = null;
  const flush = () => {
    if (start !== null) {
      spans.push({ start, end });
      start = null;
      end = null;
    }
  };
  for (const operation of operations) {
    if (operation === 'equal') {
      flush();
      beforeIndex += 1;
      afterIndex += 1;
      continue;
    }
    if (start === null) {
      start = prefix + afterIndex;
    }
    if (operation === 'delete') {
      beforeIndex += 1;
    } else {
      afterIndex += 1;
    }
    end = prefix + afterIndex;
  }
  flush();
  return spans;
}

function commonPrefixLength(left, right) {
  const limit = Math.min(left.length, right.length);
  let length = 0;
  while (length < limit && left[length] === right[length]) {
    length += 1;
  }
  return length;
}

function commonSuffixLength(left, right, prefix) {
  const limit = Math.min(left.length, right.length) - prefix;
  let length = 0;
  while (length < limit && left[left.length - length - 1] === right[right.length - length - 1]) {
    length += 1;
  }
  return length;
}

function offsetAtLine(contents, line) {
  let offset = 0;
  for (let currentLine = 1; currentLine < line; currentLine += 1) {
    const newline = contents.indexOf('\n', offset);
    if (newline === -1) {
      return contents.length;
    }
    offset = newline + 1;
  }
  return offset;
}

function operatorSourceSpan(node, contents) {
  if (!node || !node.operator || !node.left || !node.right) {
    return null;
  }
  const start = findOperatorToken(contents, node.left.end, node.right.start, node.operator);
  return start === -1 || start >= node.right.start
    ? null
    : { start, end: start + node.operator.length };
}

function findOperatorToken(contents, start, end, operator) {
  let index = start;
  while (index < end) {
    if (contents.startsWith('//', index)) {
      const newline = contents.indexOf('\n', index + 2);
      index = newline === -1 || newline >= end ? end : newline + 1;
      continue;
    }
    if (contents.startsWith('/*', index)) {
      const close = contents.indexOf('*/', index + 2);
      index = close === -1 || close + 2 >= end ? end : close + 2;
      continue;
    }
    if (contents.startsWith(operator, index)) {
      return index;
    }
    index += 1;
  }
  return -1;
}

function mutationOperatorReplacement(operator) {
  const replacements = {
    '!==': '===',
    '===': '!==',
    '!=': '==',
    '==': '!=',
    '>=': '>',
    '>': '>=',
    '<=': '<',
    '<': '<=',
    '&&': '||',
    '||': '&&',
    '??': '||'
  };
  return replacements[operator] || null;
}

function diffLineOperations(beforeLines, afterLines) {
  const n = beforeLines.length;
  const m = afterLines.length;
  const max = n + m;
  const trace = [];
  let vector = { 1: 0 };
  let endDistance = 0;
  outer: for (let distance = 0; distance <= max; distance += 1) {
    trace.push({ ...vector });
    for (let diagonal = -distance; diagonal <= distance; diagonal += 2) {
      const down = diagonal === -distance || (diagonal !== distance && (vector[diagonal - 1] ?? -1) < (vector[diagonal + 1] ?? -1));
      let x = down ? (vector[diagonal + 1] ?? 0) : (vector[diagonal - 1] ?? 0) + 1;
      let y = x - diagonal;
      while (x < n && y < m && beforeLines[x] === afterLines[y]) {
        x += 1;
        y += 1;
      }
      vector[diagonal] = x;
      if (x >= n && y >= m) {
        endDistance = distance;
        break outer;
      }
    }
  }

  const operations = [];
  let x = n;
  let y = m;
  for (let distance = endDistance; distance > 0; distance -= 1) {
    const previous = trace[distance];
    const diagonal = x - y;
    const down = diagonal === -distance || (diagonal !== distance && (previous[diagonal - 1] ?? -1) < (previous[diagonal + 1] ?? -1));
    const previousDiagonal = down ? diagonal + 1 : diagonal - 1;
    const previousX = previous[previousDiagonal] ?? 0;
    const previousY = previousX - previousDiagonal;
    while (x > previousX && y > previousY) {
      operations.unshift('equal');
      x -= 1;
      y -= 1;
    }
    if (x === previousX) {
      operations.unshift('insert');
      y -= 1;
    } else {
      operations.unshift('delete');
      x -= 1;
    }
  }
  while (x > 0 && y > 0) {
    operations.unshift('equal');
    x -= 1;
    y -= 1;
  }
  while (x > 0) {
    operations.unshift('delete');
    x -= 1;
  }
  while (y > 0) {
    operations.unshift('insert');
    y -= 1;
  }
  return operations;
}

function createBindingModel(ast) {
  const parentByNode = new WeakMap();
  const scopeByNode = new WeakMap();
  const declarationBindings = new WeakMap();
  const referenceBindings = new WeakMap();
  const rootScope = createBindingScope(null, 'program');

  function assignScopes(node, parent, parentScope) {
    if (!isBehaviorAstNode(node)) {
      return;
    }
    parentByNode.set(node, parent || null);
    let scope = parentScope;
    if (node !== ast && isBindingFunction(node)) {
      scope = createBindingScope(parentScope, 'function');
    } else if (node !== ast && node.type === 'BlockStatement') {
      scope = createBindingScope(parentScope, 'block');
    }
    scopeByNode.set(node, scope);
    for (const child of astChildren(node)) {
      assignScopes(child, node, scope);
    }
  }

  assignScopes(ast, null, rootScope);

  visitBehaviorNode(ast, (node) => {
    const parent = parentByNode.get(node);
    const scope = scopeByNode.get(node);
    if (node.type === 'VariableDeclarator') {
      const declaration = parent && parent.type === 'VariableDeclaration' ? parent : null;
      const targetScope = declaration && declaration.kind === 'var'
        ? nearestBindingScope(scope, 'function')
        : scope;
      declareBindingPattern(node.id, targetScope);
    } else if (node.type === 'FunctionDeclaration' && node.id) {
      declareIdentifier(node.id, scopeByNode.get(parent) || rootScope);
      for (const parameter of node.params || []) {
        declareBindingPattern(parameter, scope);
      }
    } else if (node.type === 'ClassDeclaration' && node.id) {
      declareIdentifier(node.id, scopeByNode.get(parent) || rootScope);
    } else if (isBindingFunction(node)) {
      if (node.type === 'FunctionExpression' && node.id) {
        declareIdentifier(node.id, scope);
      }
      for (const parameter of node.params || []) {
        declareBindingPattern(parameter, scope);
      }
    } else if (node.type === 'CatchClause' && node.param) {
      declareBindingPattern(node.param, scope);
    } else if (node.type === 'ImportDeclaration') {
      for (const specifier of node.specifiers || []) {
        declareIdentifier(specifier.local, scope);
      }
    }
  });

  visitBehaviorNode(ast, (node) => {
    if (node.type === 'Identifier' && isReferenceIdentifier(node, parentByNode, declarationBindings)) {
      referenceBindings.set(node, resolveBinding(node.name, scopeByNode.get(node)));
    }
  });

  function declareIdentifier(identifier, scope) {
    if (!identifier || identifier.type !== 'Identifier' || !scope) {
      return;
    }
    let binding = scope.bindings.get(identifier.name);
    if (!binding) {
      binding = { declaration: identifier, name: identifier.name, scope };
      scope.bindings.set(identifier.name, binding);
    }
    declarationBindings.set(identifier, binding);
  }

  function declareBindingPattern(pattern, scope) {
    if (!pattern || !scope) {
      return;
    }
    if (pattern.type === 'Identifier') {
      declareIdentifier(pattern, scope);
    } else if (pattern.type === 'RestElement') {
      declareBindingPattern(pattern.argument, scope);
    } else if (pattern.type === 'AssignmentPattern') {
      declareBindingPattern(pattern.left, scope);
    } else if (pattern.type === 'ArrayPattern') {
      for (const element of pattern.elements || []) {
        declareBindingPattern(element, scope);
      }
    } else if (pattern.type === 'ObjectPattern') {
      for (const property of pattern.properties || []) {
        if (property.type === 'RestElement') {
          declareBindingPattern(property.argument, scope);
        } else if (property.type === 'ObjectProperty') {
          declareBindingPattern(property.value, scope);
        }
      }
    }
  }

  return {
    ast,
    declarationBinding(identifier) {
      return declarationBindings.get(identifier) || null;
    },
    parentOf(node) {
      return parentByNode.get(node) || null;
    },
    referenceBinding(identifier) {
      return referenceBindings.get(identifier) || null;
    },
    scopeOf(node) {
      return scopeByNode.get(node) || null;
    }
  };

  function resolveBinding(name, scope) {
    let current = scope;
    while (current) {
      const binding = current.bindings.get(name);
      if (binding) {
        return binding;
      }
      current = current.parent;
    }
    return null;
  }
}

function createBindingScope(parent, kind) {
  return { bindings: new Map(), kind, parent };
}

function nearestBindingScope(scope, kind) {
  let current = scope;
  while (current && current.kind !== kind && current.kind !== 'program') {
    current = current.parent;
  }
  return current || scope;
}

function isBindingFunction(node) {
  return ['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'].includes(node.type);
}

function astChildren(node) {
  const children = [];
  for (const value of Object.values(node)) {
    if (isBehaviorAstNode(value)) {
      children.push(value);
    } else if (Array.isArray(value)) {
      children.push(...value.filter(isBehaviorAstNode));
    }
  }
  return children;
}

function isReferenceIdentifier(node, parentByNode, declarationBindings) {
  if (declarationBindings.has(node)) {
    return false;
  }
  const parent = parentByNode.get(node);
  if (!parent) {
    return true;
  }
  if (parent.type === 'MemberExpression' && parent.property === node && !parent.computed) {
    return false;
  }
  if (['ObjectMethod', 'ClassMethod', 'ClassPrivateMethod', 'ClassProperty'].includes(parent.type) && parent.key === node && !parent.computed) {
    return false;
  }
  if (parent.type === 'ObjectProperty' && parent.key === node && !parent.computed && !parent.shorthand) {
    return false;
  }
  if (['LabeledStatement', 'BreakStatement', 'ContinueStatement'].includes(parent.type) && parent.label === node) {
    return false;
  }
  if (['ImportSpecifier', 'ImportDefaultSpecifier', 'ImportNamespaceSpecifier', 'ExportSpecifier'].includes(parent.type)) {
    return parent.local === node;
  }
  return true;
}

function assessObservability(testFiles, sourceFiles = [], projectRoot = null) {
  const behavioral = [];
  const rejected = [];
  const sourceFacts = sourceFiles.map(buildSourceFacts);
  const errors = sourceFacts.filter((fact) => fact.error).map((fact) => ({ path: fact.file.path, error: fact.error }));
  for (const file of testFiles) {
    const analysis = analyzeTestFile(file, sourceFacts, projectRoot);
    errors.push(...analysis.errors.map((error) => ({ path: file.path, error })));
    rejected.push(...analysis.rejected);
    behavioral.push(...analysis.behavioral);
  }
  if (errors.length > 0) {
    return { behavioral, errors, rejected, status: 'INCONCLUSIVE' };
  }
  return {
    behavioral,
    errors,
    rejected,
    status: rejected.length > 0 ? 'FAIL' : behavioral.length > 0 ? 'PASS' : 'FAIL'
  };
}

function analyzeTestFile(file, sourceFacts = [], projectRoot = null) {
  const parser = loadBehaviorParser();
  if (parser.error) {
    return { behavioral: [], errors: [parser.error], rejected: [] };
  }
  let ast;
  try {
    ast = parser.parse(file.contents, {
      plugins: proofParserPlugins(file.path),
      ranges: true,
      sourceType: 'unambiguous'
    }).program;
  } catch (error) {
    return { behavioral: [], errors: [error.message], rejected: [] };
  }
  const bindingModel = createBindingModel(ast);
  const moduleBindingsValue = moduleBindings(file, sourceFacts.filter((fact) => !fact.error).map((fact) => fact.file.path), bindingModel, projectRoot);
  const rejected = [];
  const errors = [];
  const uncertainInspections = [];
  const uncertainInspectionBindings = new Set();
  visitBehaviorNode(ast, (node) => {
    const inspection = sourceInspectionEvidence(node, moduleBindingsValue, projectRoot, file.path);
    if (inspection === 'source') {
      rejected.push({ end: node.end, path: file.path, start: node.start, text: sourceText(file.contents, node), reason: 'implementation-inspection' });
    } else if (inspection === 'unknown') {
      uncertainInspections.push({ end: node.end, path: file.path, start: node.start, text: sourceText(file.contents, node) });
      const binding = sourceInspectionResultBinding(node, bindingModel);
      if (binding) {
        uncertainInspectionBindings.add(binding);
      }
    }
  });
  const blocks = extractTestBlocksFromAst(ast, file, bindingModel);
  const behavioral = [];
  for (const block of blocks) {
    const assertions = assertionNodes(block.node);
    const productCalls = collectProductCalls(block, sourceFacts, projectRoot);
    const productResults = productResultBindings(block.node, productCalls, bindingModel);
    for (const assertion of assertions) {
      const text = sourceText(file.contents, assertion);
      const uncertainInspection = uncertainInspections.some((entry) => entry.start >= assertion.start && entry.end <= assertion.end) ||
        assertionReferencesBindingSet(assertion, uncertainInspectionBindings, bindingModel);
      if (uncertainInspection) {
        errors.push(`The assertion in ${file.path} contains an unresolved source inspection target.`);
      }
      if (isImplementationAssertionNode(assertion) || rejected.some((entry) => entry.start >= assertion.start && entry.end <= assertion.end) || uncertainInspection) {
        continue;
      }
      const assertionCalls = behaviorCallNodes(assertion);
      const directProduct = assertionCalls.filter((call) => productCalls.some((productCall) => productCall.node === call));
      const resultObservation = assertionReferencesAny(assertion, productResults, bindingModel);
      if (directProduct.some((call) => isDirectlyObservedProductCall(call, assertion, bindingModel)) || resultObservation.observed) {
        behavioral.push({
          end: block.end,
          kind: 'ast-behavior',
          path: file.path,
          start: block.start,
          text,
          title: block.title
        });
      }
      if ((directProduct.some((call) => !isDirectlyObservedProductCall(call, assertion, bindingModel)) && !resultObservation.observed) || resultObservation.uncertain) {
        errors.push(`The assertion in ${file.path} consumes a product result through an unresolved helper or indirect call.`);
      }
    }
  }
  return { behavioral, errors, rejected: uniqueEvidence(rejected) };
}

function productResultBindings(root, productCalls, bindingModel) {
  const bindings = new Set();
  const uncertain = new Set();
  visitBehaviorNode(root, (node) => {
    if (node.type === 'VariableDeclarator' && node.id && node.id.type === 'Identifier' && containsProductCall(node.init, productCalls)) {
      const binding = bindingModel.declarationBinding(node.id);
      if (binding) {
        bindings.add(binding);
        if (containsUnresolvedCallAroundProduct(node.init, productCalls)) {
          uncertain.add(binding);
        }
      }
    } else if (node.type === 'AssignmentExpression' && node.left && node.left.type === 'Identifier' && containsProductCall(node.right, productCalls)) {
      const binding = bindingModel.referenceBinding(node.left);
      if (binding) {
        bindings.add(binding);
        if (containsUnresolvedCallAroundProduct(node.right, productCalls)) {
          uncertain.add(binding);
        }
      }
    }
  });
  return { bindings, uncertain };
}

function containsProductCall(node, productCalls) {
  return Boolean(node && productCalls.some((productCall) => {
    return productCall.node.start >= node.start && productCall.node.end <= node.end;
  }));
}

function containsUnresolvedCallAroundProduct(node, productCalls) {
  let unresolved = false;
  visitBehaviorNode(node, (current) => {
    if (unresolved || current.type !== 'CallExpression' || productCalls.some((productCall) => productCall.node === current)) {
      return;
    }
    if (!isAssertionCall(current) && !isSafeObservationCall(current)) {
      unresolved = true;
    }
  });
  return unresolved;
}

function assertionReferencesAny(assertion, resultBindings, bindingModel) {
  if (!resultBindings || resultBindings.bindings.size === 0) {
    return { observed: false, uncertain: false };
  }
  let referenced = false;
  let uncertain = false;
  visitBehaviorNode(assertion, (node) => {
    if (node.type !== 'Identifier' || bindingModel.referenceBinding(node) === null) {
      return;
    }
    if (!resultBindings.bindings.has(bindingModel.referenceBinding(node))) {
      return;
    }
    if (resultBindings.uncertain.has(bindingModel.referenceBinding(node))) {
      uncertain = true;
      return;
    }
    if (hasUnresolvedCallBetween(node, assertion, bindingModel)) {
      uncertain = true;
    } else {
      referenced = true;
    }
  });
  return { observed: referenced, uncertain };
}

function isDirectlyObservedProductCall(call, assertion, bindingModel) {
  return !hasUnresolvedCallBetween(call, assertion, bindingModel);
}

function hasUnresolvedCallBetween(node, ancestor, bindingModel) {
  let current = bindingModel.parentOf(node);
  while (current && current !== ancestor) {
    if (current.type === 'CallExpression' && !isAssertionCall(current) && !isSafeObservationCall(current)) {
      return true;
    }
    current = bindingModel.parentOf(current);
  }
  return false;
}

function isSafeObservationCall(node) {
  if (!node || !node.callee || node.callee.type !== 'MemberExpression') {
    return false;
  }
  if (['filter', 'join', 'map', 'slice', 'sort'].includes(staticMemberName(node.callee))) {
    return true;
  }
  return node.callee.object && node.callee.object.type === 'Identifier' && node.callee.object.name === 'Promise' &&
    ['all', 'allSettled', 'any', 'race'].includes(staticMemberName(node.callee));
}

function assessImpactObservability(related, impactFiles, projectRoot = null) {
  const perSource = related.perSource.map((item) => ({
    path: item.path,
    ...assessObservability(item.closureFiles || item.files, impactFiles, projectRoot)
  }));
  return {
    behavioral: perSource.flatMap((item) => item.behavioral),
    perSource,
    rejected: perSource.flatMap((item) => item.rejected),
    status: perSource.some((item) => item.status === 'INCONCLUSIVE')
      ? 'INCONCLUSIVE'
      : perSource.length > 0 && perSource.every((item) => item.status === 'PASS') ? 'PASS' : 'FAIL'
  };
}

function extractTestBlocksFromAst(ast, file, bindingModel = createBindingModel(ast)) {
  const blocks = [];
  visitBehaviorNode(ast, (node) => {
    if (node.type !== 'CallExpression' || !node.callee || node.callee.type !== 'Identifier' || !['test', 'it'].includes(node.callee.name)) {
      return;
    }
    const title = node.arguments && node.arguments[0] && node.arguments[0].type === 'StringLiteral'
      ? node.arguments[0].value
      : null;
    const callback = node.arguments && node.arguments.find((argument) => {
      return argument && ['ArrowFunctionExpression', 'FunctionExpression'].includes(argument.type);
    });
    if (!callback) {
      return;
    }
    blocks.push({
      end: node.end,
      file,
      node: callback.body,
      bindingModel,
      path: file.path,
      start: node.start,
      title
    });
  });
  return blocks.length > 0
    ? blocks
    : [{ end: ast.end, file, node: ast, path: file.path, start: ast.start || 0, title: null }];
}

function extractTestBlocks(contents, filePath, sourceFacts = [], projectRoot = null) {
  const file = { contents, path: filePath };
  const analysis = analyzeTestFile(file, sourceFacts, projectRoot);
  const parser = loadBehaviorParser();
  if (parser.error) {
    return [];
  }
  try {
    const ast = parser.parse(contents, { plugins: proofParserPlugins(filePath), ranges: true, sourceType: 'unambiguous' }).program;
    const blocks = extractTestBlocksFromAst(ast, file, createBindingModel(ast));
    return blocks.map((block) => ({
      ...block,
      behavioral: analysis.behavioral.some((item) => item.path === filePath && item.start === block.start && item.end === block.end) &&
        analysis.rejected.length === 0,
      contents: contents.slice(block.start, block.end)
    }));
  } catch (error) {
    return [];
  }
}

function isSourceInspectionNode(node, bindings = null, projectRoot = null, filePath = null) {
  return sourceInspectionEvidence(node, bindings, projectRoot, filePath) === 'source';
}

function sourceInspectionEvidence(node, bindings = null, projectRoot = null, filePath = null) {
  if (node.type === 'CallExpression') {
    const callee = node.callee;
    if (callee && callee.type === 'Identifier' && callee.name === 'require' && !isRequireCall(node)) {
      return 'source';
    }
    if (callee && callee.type === 'MemberExpression') {
      const property = staticMemberName(callee);
      const objectTarget = moduleTargetForExpression(callee.object, bindings);
      if (isFilesystemApiTarget(objectTarget) && ['readFile', 'readFileSync', 'open', 'openSync', 'readSync'].includes(property)) {
        return sourceInspectionCallStatus(node, bindings, projectRoot, filePath, new Set());
      }
      if (property === 'toString' && isInternalModuleTarget(objectTarget)) {
        return 'source';
      }
    }
    const target = callee && callee.type === 'Identifier' ? moduleTargetForExpression(callee, bindings) : null;
    if (target && isFilesystemApiTarget(target) && ['readFile', 'readFileSync', 'open', 'openSync', 'readSync'].includes(target.exportName)) {
      return sourceInspectionCallStatus(node, bindings, projectRoot, filePath, new Set());
    }
    if (callee && callee.type === 'MemberExpression' && staticMemberName(callee) === 'resolve' &&
      callee.object && callee.object.type === 'Identifier' && callee.object.name !== 'require') {
      return null;
    }
  }
  if (node.type === 'MemberExpression') {
    const property = staticMemberName(node);
    const objectTarget = moduleTargetForExpression(node.object, bindings);
    if (node.computed && !property && (isFilesystemApiTarget(objectTarget) || isInternalModuleTarget(objectTarget))) {
      return 'source';
    }
    if (property === 'toString' && isInternalModuleTarget(objectTarget)) {
      return 'source';
    }
    if (['callCount', 'calls', 'called', 'calledOnce', 'calledTwice', 'snapshot', 'sourceCode', 'spy'].includes(property)) {
      return 'source';
    }
  }
  if (node.type === 'Identifier' && ['sourceCode', 'sourceContents'].includes(node.name)) {
    return 'source';
  }
  return null;
}

function sourceInspectionResultBinding(node, bindingModel) {
  let current = node;
  while (current) {
    const parent = bindingModel.parentOf(current);
    if (!parent) {
      return null;
    }
    if (parent.type === 'VariableDeclarator' && parent.init && parent.init.start <= node.start && parent.init.end >= node.end) {
      return parent.id && parent.id.type === 'Identifier'
        ? bindingModel.declarationBinding(parent.id)
        : null;
    }
    if (parent.type === 'AssignmentExpression' && parent.right && parent.right.start <= node.start && parent.right.end >= node.end &&
      parent.left && parent.left.type === 'Identifier') {
      return bindingModel.referenceBinding(parent.left);
    }
    current = parent;
  }
  return null;
}

function assertionReferencesBindingSet(assertion, bindings, bindingModel) {
  let referenced = false;
  visitBehaviorNode(assertion, (node) => {
    if (referenced || node.type !== 'Identifier') {
      return;
    }
    const binding = bindingModel.referenceBinding(node);
    if (binding && bindings.has(binding)) {
      referenced = true;
    }
  });
  return referenced;
}

function sourceInspectionCallStatus(node, bindings, projectRoot, filePath, seen) {
  const api = sourceInspectionApi(node, bindings);
  if (!api) {
    return null;
  }
  if (api.name === 'readSync') {
    return sourceInspectionFileDescriptorStatus(node.arguments[0], bindings, projectRoot, filePath, seen);
  }
  const argument = node.arguments[0];
  if (!argument) {
    return 'unknown';
  }
  return sourceInspectionPathStatus(argument, bindings, projectRoot, filePath, seen);
}

function sourceInspectionApi(node, bindings) {
  if (!node || node.type !== 'CallExpression') {
    return null;
  }
  if (node.callee.type === 'Identifier') {
    const target = moduleTargetForExpression(node.callee, bindings);
    return target && isFilesystemApiTarget(target) ? { name: target.exportName, target } : null;
  }
  if (node.callee.type === 'MemberExpression') {
    const target = moduleTargetForExpression(node.callee.object, bindings);
    const name = staticMemberName(node.callee);
    return target && isFilesystemApiTarget(target) ? { name, target } : null;
  }
  return null;
}

function sourceInspectionPathStatus(node, bindings, projectRoot, filePath, seen) {
  if (!node) {
    return 'unknown';
  }
  if (node.type === 'StringLiteral') {
    const candidate = path.resolve(projectRoot, node.value);
    const resolved = resolveProofSourceCandidate(projectRoot, candidate);
    return resolved.status === 'source' ? 'source' : 'external';
  }
  if (node.type === 'CallExpression' && node.callee.type === 'MemberExpression' &&
    node.callee.object.type === 'Identifier' && node.callee.object.name === 'require' &&
    staticMemberName(node.callee) === 'resolve' && isRequireCall({ ...node, callee: node.callee.object })) {
    const specifier = node.arguments[0] && node.arguments[0].type === 'StringLiteral' ? node.arguments[0].value : null;
    if (!specifier) {
      return 'unknown';
    }
    const resolved = resolveLocalModule(projectRoot, filePath, specifier);
    return resolved && isProductSource(resolved) ? 'source' : 'external';
  }
  if (node.type === 'CallExpression' && node.callee.type === 'MemberExpression') {
    const object = node.callee.object;
    const property = staticMemberName(node.callee);
    if (object.type === 'Identifier' && object.name === 'path' && ['join', 'resolve'].includes(property)) {
      const values = node.arguments.map((argument) => argument.type === 'StringLiteral' ? argument.value : null);
      if (values.every((value) => value !== null)) {
        const resolved = resolveProofSourceCandidate(projectRoot, path.resolve(projectRoot, ...values));
        return resolved.status === 'source' ? 'source' : 'external';
      }
    }
  }
  if (node.type === 'Identifier') {
    const binding = bindings && bindings.model && bindings.model.referenceBinding(node);
    if (!binding || seen.has(binding)) {
      return 'unknown';
    }
    seen.add(binding);
    const parent = bindings.model.parentOf(binding.declaration);
    if (parent && parent.type === 'VariableDeclarator') {
      return sourceInspectionPathStatus(parent.init, bindings, projectRoot, filePath, seen);
    }
  }
  return 'unknown';
}

function sourceInspectionFileDescriptorStatus(node, bindings, projectRoot, filePath, seen) {
  if (!node || node.type !== 'Identifier') {
    return 'unknown';
  }
  const binding = bindings && bindings.model && bindings.model.referenceBinding(node);
  if (!binding || seen.has(binding)) {
    return 'unknown';
  }
  seen.add(binding);
  const parent = bindings.model.parentOf(binding.declaration);
  if (parent && parent.type === 'VariableDeclarator' && parent.init && parent.init.type === 'CallExpression') {
    const api = sourceInspectionApi(parent.init, bindings);
    if (api && api.name === 'openSync') {
      return sourceInspectionCallStatus(parent.init, bindings, projectRoot, filePath, seen);
    }
  }
  return 'unknown';
}

function moduleTargetForExpression(node, bindings) {
  if (!node || !bindings || !bindings.model) {
    return null;
  }
  if (node.type === 'AwaitExpression') {
    return moduleTargetForExpression(node.argument, bindings);
  }
  if (isDynamicImportCall(node)) {
    return {
      dynamicImport: true,
      exportName: null,
      modulePath: null,
      specifier: dynamicImportSpecifier(node)
    };
  }
  if (node.type === 'Identifier') {
    const binding = bindings.model.referenceBinding(node);
    return binding ? bindings.byBinding.get(binding) || null : null;
  }
  if (node.type === 'MemberExpression') {
    return moduleTargetForExpression(node.object, bindings);
  }
  if (isRequireCall(node)) {
    const specifier = node.arguments[0].value;
    return { modulePath: null, specifier, exportName: null };
  }
  return null;
}

function isFilesystemTarget(target) {
  return Boolean(target && ['fs', 'node:fs', 'fs/promises', 'node:fs/promises'].includes(target.specifier));
}

function isFilesystemApiTarget(target) {
  return isFilesystemTarget(target) || Boolean(target && target.dynamicImport);
}

function isInternalModuleTarget(target) {
  return Boolean(target && typeof target.specifier === 'string' && target.specifier.startsWith('.'));
}

function isImplementationAssertionNode(node) {
  let implementation = false;
  visitBehaviorNode(node, (current) => {
    if (current.type === 'UnaryExpression' && current.operator === 'typeof') {
      implementation = true;
    }
    if (current.type === 'MemberExpression' && ['toMatchSnapshot', 'toHaveBeenCalled', 'callCount', 'calls', 'called', 'calledOnce', 'calledTwice'].includes(staticMemberName(current))) {
      implementation = true;
    }
  });
  return implementation;
}

function assertionNodes(root) {
  const results = [];
  visitBehaviorNode(root, (node, ancestors) => {
    if (node.type !== 'CallExpression' || isNestedAssertion(ancestors)) {
      return;
    }
    if (isAssertionCall(node)) {
      results.push(node);
    }
  });
  return results;
}

function isNestedAssertion(ancestors) {
  return ancestors.some((ancestor) => ancestor.type === 'CallExpression' && isAssertionCall(ancestor));
}

function isAssertionCall(node) {
  if (!node || node.type !== 'CallExpression') {
    return false;
  }
  if (node.callee.type === 'MemberExpression') {
    const property = staticMemberName(node.callee);
    if (node.callee.object && node.callee.object.type === 'Identifier' && node.callee.object.name === 'assert') {
      return ['deepEqual', 'deepStrictEqual', 'equal', 'fail', 'match', 'notDeepEqual', 'notEqual', 'notStrictEqual', 'ok', 'rejects', 'strictEqual', 'throws'].includes(property);
    }
    if (node.callee.object && node.callee.object.type === 'CallExpression' && node.callee.object.callee.type === 'Identifier' && node.callee.object.callee.name === 'expect') {
      return true;
    }
  }
  return false;
}

function isErrorAssertion(node) {
  return node.callee && node.callee.type === 'MemberExpression' && ['throws', 'rejects'].includes(staticMemberName(node.callee));
}

function behaviorCallNodes(root) {
  const results = [];
  visitBehaviorNode(root, (node) => {
    if (node.type === 'CallExpression' && !isAssertionCall(node)) {
      results.push(node);
    }
  });
  return results;
}

function isLikelyProductCall(node) {
  if (!node || !node.callee) {
    return false;
  }
  if (node.callee.type === 'Identifier') {
    return !['require', 'test', 'it', 'describe', 'before', 'after', 'beforeEach', 'afterEach', 'expect', 'assert', 'log'].includes(node.callee.name);
  }
  if (node.callee.type === 'MemberExpression') {
    const object = node.callee.object;
    const property = staticMemberName(node.callee);
    if (object && object.type === 'Identifier' && ['assert', 'console', 'mock', 'jest', 'vi', 'fs', 'sinon'].includes(object.name)) {
      return false;
    }
    return !['then', 'catch', 'finally', 'map', 'filter', 'push', 'slice', 'join'].includes(property);
  }
  return false;
}

function staticMemberName(node) {
  if (!node || node.type !== 'MemberExpression') {
    return null;
  }
  if (!node.computed && node.property && node.property.type === 'Identifier') {
    return node.property.name;
  }
  return evaluateStaticString(node.property);
}

function evaluateStaticString(node) {
  if (!node) {
    return null;
  }
  if (node.type === 'StringLiteral') {
    return node.value;
  }
  if (node.type === 'BinaryExpression' && node.operator === '+') {
    const left = evaluateStaticString(node.left);
    const right = evaluateStaticString(node.right);
    return left !== null && right !== null ? left + right : null;
  }
  return null;
}

function sourceText(contents, node) {
  return contents.slice(node.start, node.end).replace(/\s+/g, ' ').trim();
}

function assessEdgeCases(sourceFiles, related, projectRoot = null, testObligations = []) {
  const sourceFacts = (related.sourceFiles || sourceFiles).map(buildSourceFacts);
  const applicableSourceFacts = (related.applicableSourceFiles || sourceFiles).map(buildSourceFacts);
  const blocks = (related.files || []).flatMap((file) => extractTestBlocks(file.contents, file.path, sourceFacts, projectRoot));
  const parserErrors = [...sourceFacts, ...applicableSourceFacts].flatMap((fact) => fact.error ? [fact.error] : []);
  if (parserErrors.length > 0 || blocks.length === 0) {
    return {
      categories: edgeCategoryIds().map((id) => ({ id, rationale: parserErrors.join('; ') || 'No retained test block could be parsed.', status: 'INCONCLUSIVE' })),
      status: 'INCONCLUSIVE'
    };
  }
  const categories = edgeCategoryIds().map((id) => assessEdgeCategory(
    id,
    sourceFacts,
    blocks,
    related.onlySource,
    projectRoot,
    applicableSourceFacts,
    testObligations
  ));
  return {
    categories,
    status: categories.some((category) => category.status === 'INCONCLUSIVE')
      ? 'INCONCLUSIVE'
      : categories.every((category) => category.status === 'PASS' || category.status === 'NOT_APPLICABLE') ? 'PASS' : 'FAIL'
  };
}

function assessImpactEdgeCases(impactFiles, related, projectRoot = null, testObligations = []) {
  const perSource = impactFiles.map((file) => {
    const selected = related.perSource.find((item) => item.path === file.path);
    const assessment = assessEdgeCases(impactFiles, {
      ...(selected || { files: [] }),
      onlySource: file.path,
      sourceFiles: impactFiles
    }, projectRoot, testObligations);
    return {
      path: file.path,
      ...assessment,
      categories: assessment.categories.map((category) => category.status === 'NOT_APPLICABLE'
        ? { ...category, rationale: `${file.path}: ${category.rationale}` }
        : category)
    };
  });
  const categories = ['empty-input', 'null', 'boundary-values', 'concurrency', 'failure-path', 'side-effects'].map((id) => {
    const scoped = perSource.map((item) => ({
      path: item.path,
      ...item.categories.find((category) => category.id === id)
    }));
    const applicable = scoped.filter((category) => category.status !== 'NOT_APPLICABLE');
    const failures = scoped.filter((category) => category.status === 'FAIL');
    const inconclusive = scoped.filter((category) => category.status === 'INCONCLUSIVE');
    return {
      evidence: scoped.flatMap((category) => (category.evidence || []).map((evidence) => ({
        ...evidence,
        impactSource: category.path
      }))),
      id,
      rationale: scoped.filter((category) => category.status === 'NOT_APPLICABLE').map((category) => ({
        impactSource: category.path,
        rationale: category.rationale
      })),
      status: inconclusive.length > 0 ? 'INCONCLUSIVE' : failures.length > 0 ? 'FAIL' : applicable.length === 0 ? 'NOT_APPLICABLE' : 'PASS'
    };
  });
  return {
    categories,
    perSource,
    status: categories.some((category) => category.status === 'INCONCLUSIVE')
      ? 'INCONCLUSIVE'
      : perSource.length > 0 && categories.every((category) => category.status === 'PASS' || category.status === 'NOT_APPLICABLE')
        ? 'PASS'
        : 'FAIL'
  };
}

function edgeCategoryIds() {
  return ['empty-input', 'null', 'boundary-values', 'concurrency', 'failure-path', 'side-effects'];
}

function assessEdgeCategory(
  id,
  sourceFacts,
  blocks,
  onlySource = null,
  projectRoot = null,
  applicableSourceFacts = sourceFacts,
  testObligations = []
) {
  const applicablePaths = new Set(applicableSourceFacts.map((fact) => fact.file.path));
  const applicable = sourceFacts.filter((fact) => applicablePaths.has(fact.file.path) && (!onlySource || fact.file.path === onlySource) && isEdgeApplicable(fact, id));
  if (applicable.length === 0) {
    return { id, rationale: edgeNotApplicableReason(id), status: 'NOT_APPLICABLE' };
  }
  const failureObligation = id === 'failure-path'
    ? parseFailurePathObligation(testObligations)
    : null;
  if (failureObligation && !failureObligation.valid) {
    return { id, rationale: failureObligation.reason, status: 'INCONCLUSIVE' };
  }
  const evidence = [];
  for (const fact of applicable) {
    for (const block of blocks) {
      const observation = blockIsBehavioral(block);
      const calls = collectProductCalls(block, sourceFacts, projectRoot);
      if (!observation || !calls.some((call) => call.affectedPaths.includes(fact.file.path))) {
        continue;
      }
      if (!edgeCallMatches(id, calls, block, fact, failureObligation)) {
        continue;
      }
      const failureEvidence = id === 'failure-path'
        ? matchingFailureAssertion(block, calls, fact, failureObligation)
        : null;
      evidence.push({
        calls: calls.filter((call) => call.affectedPaths.includes(fact.file.path)).map((call) => ({
          argumentCount: call.node.arguments.length,
          exportName: call.exportName,
          module: call.modulePath
        })),
        path: block.path,
        title: block.title,
        ...(failureEvidence ? { assertion: failureEvidence } : {})
      });
    }
  }
  return evidence.length > 0
    ? { evidence, id, status: 'PASS' }
    : { id, rationale: 'No retained test invokes the applicable product API with the required actual argument and observes its result or effect.', status: 'FAIL' };
}

function buildSourceFacts(file) {
  const parser = loadBehaviorParser();
  if (parser.error) {
    return { error: parser.error, file };
  }
  let ast;
  try {
    ast = parser.parse(file.contents, {
      plugins: proofParserPlugins(file.path),
      ranges: true,
      sourceType: 'unambiguous'
    }).program;
  } catch (error) {
    return { error: `${file.path}: ${error.message}`, file };
  }
  const bindingModel = createBindingModel(ast);
  const regions = file.changed === false ? [wholeFileRegion(file)] : (file.changedRegions || [wholeFileRegion(file)]);
  const relevant = (node) => regions.some((region) => mutationNodeInRegion(node, region));
  const facts = {
    boundaryValues: [],
    concurrency: false,
    failure: false,
    input: false,
    io: false,
    relevantNodes: [],
    sideEffects: false
  };
  visitBehaviorNode(ast, (node) => {
    if (!relevant(node)) {
      return;
    }
    facts.relevantNodes.push(node);
    if (['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'].includes(node.type) && node.params && node.params.length > 0) {
      const bodyChanged = node.body && regions.some((region) => mutationNodeInRegion(node.body, region));
      if (bodyChanged) {
        facts.input = true;
      }
    }
    if (node.type === 'BinaryExpression' && ['<', '<=', '>', '>=', '===', '!=='].includes(node.operator)) {
      facts.boundaryValues.push(...numericValues(node.left), ...numericValues(node.right));
    }
    if (node.type === 'MemberExpression' && staticMemberName(node) === 'length') {
      facts.boundaryValues.push(...numericValues(node.object));
      facts.boundaryValues.push(1);
    }
    if (node.type === 'NumericLiteral' && Number.isFinite(node.value)) {
      facts.boundaryValues.push(node.value);
    }
    if (node.type === 'ThrowStatement' || node.type === 'CatchClause' || (node.type === 'NewExpression' && propertyOrIdentifierName(node.callee) === 'Error')) {
      facts.failure = true;
    }
    if (node.type === 'CallExpression') {
      const property = node.callee && node.callee.type === 'MemberExpression' ? staticMemberName(node.callee) : null;
      if (property === 'reject' || property === 'rejects') {
        facts.failure = true;
      }
      if (isIoCall(node)) {
        facts.io = true;
        facts.sideEffects = true;
        facts.concurrency = true;
      }
    }
    const exportedAssignment = node.type === 'AssignmentExpression' && node.left && node.left.type === 'MemberExpression' &&
      node.left.object && node.left.object.type === 'Identifier' && ['exports', 'module'].includes(node.left.object.name);
    if ((!exportedAssignment && node.type === 'AssignmentExpression' && isSharedStateAssignment(node, bindingModel)) ||
      (!exportedAssignment && node.type === 'UpdateExpression' && isSharedStateTarget(node.argument, bindingModel)) ||
      (node.type === 'NewExpression' && ['Map', 'Set'].includes(propertyOrIdentifierName(node.callee)) && isSharedCollectionCreation(node, bindingModel))) {
      facts.concurrency = true;
    }
  });
  facts.boundaryValues = [...new Set(facts.boundaryValues.filter((value) => Number.isFinite(value)))];
  return { ast, facts, file, error: null };
}

function isSharedStateAssignment(node, bindingModel) {
  return node.left && node.left.type === 'Identifier'
    ? isSharedStateBinding(bindingModel.referenceBinding(node.left))
    : isSharedStateTarget(node.left, bindingModel);
}

function isSharedStateTarget(node, bindingModel) {
  if (!node) {
    return true;
  }
  if (node.type === 'Identifier') {
    return isSharedStateBinding(bindingModel.referenceBinding(node));
  }
  if (node.type === 'MemberExpression') {
    let object = node.object;
    while (object && object.type === 'MemberExpression') {
      object = object.object;
    }
    return object && object.type === 'Identifier'
      ? isSharedStateBinding(bindingModel.referenceBinding(object))
      : true;
  }
  return true;
}

function isSharedStateBinding(binding) {
  if (!binding) {
    return true;
  }
  let scope = binding.scope;
  while (scope && scope.kind !== 'program') {
    if (scope.kind === 'function') {
      return false;
    }
    scope = scope.parent;
  }
  return true;
}

function isSharedCollectionCreation(node, bindingModel) {
  const parent = bindingModel.parentOf(node);
  if (parent && parent.type === 'VariableDeclarator' && parent.id.type === 'Identifier') {
    return isSharedStateBinding(bindingModel.declarationBinding(parent.id));
  }
  if (parent && parent.type === 'AssignmentExpression') {
    return isSharedStateTarget(parent.left, bindingModel);
  }
  return true;
}

function numericValues(node) {
  if (node && node.type === 'NumericLiteral' && Number.isFinite(node.value)) {
    return [node.value];
  }
  return [];
}

function propertyOrIdentifierName(node) {
  if (!node) {
    return null;
  }
  if (node.type === 'Identifier') {
    return node.name;
  }
  if (node.type === 'MemberExpression') {
    return staticMemberName(node);
  }
  return null;
}

function isIoCall(node) {
  if (!node || node.type !== 'CallExpression') {
    return false;
  }
  const text = sourceTextFromNode(node);
  return /\b(?:readFile|writeFile|appendFile|mkdir|rm|unlink|rename|copyFile|fetch|request|send|exec|spawn|database|persist|save)\b/i.test(text) ||
    (node.callee && node.callee.type === 'MemberExpression' && ['writeFileSync', 'readFileSync', 'appendFileSync'].includes(staticMemberName(node.callee)));
}

function sourceTextFromNode(node) {
  if (!node) {
    return '';
  }
  if (node.callee && node.callee.type === 'MemberExpression') {
    return `${propertyOrIdentifierName(node.callee.object) || ''}.${staticMemberName(node.callee) || ''}`;
  }
  return propertyOrIdentifierName(node.callee) || '';
}

function isEdgeApplicable(fact, id) {
  if (fact.error) {
    return true;
  }
  const values = fact.facts;
  return id === 'empty-input'
    ? values.input
    : id === 'null'
      ? values.input
      : id === 'boundary-values'
        ? values.boundaryValues.length > 0
        : id === 'concurrency'
          ? values.concurrency
          : id === 'failure-path'
            ? values.failure
            : values.sideEffects;
}

function edgeNotApplicableReason(id) {
  const reasons = {
    'boundary-values': 'No changed executable comparison, length, or numeric boundary was observed.',
    concurrency: 'No changed shared-state or I/O operation was observed; unrelated pre-existing async code does not impose concurrency evidence.',
    'empty-input': 'No changed callable with an input parameter was observed.',
    failure: 'No changed executable failure or error path was observed.',
    'failure-path': 'No changed executable failure or error path was observed.',
    null: 'No changed callable with an input parameter was observed.',
    'side-effects': 'No changed observable external-effect operation was observed.'
  };
  return reasons[id] || 'The edge case is not applicable to the changed executable region.';
}

function blockIsBehavioral(block) {
  return block.behavioral === true;
}

function collectProductCalls(block, sourceFacts, projectRoot = null) {
  const sourcePaths = sourceFacts.filter((fact) => !fact.error).map((fact) => fact.file.path);
  const bindings = moduleBindings(block.file, sourcePaths, block.bindingModel, projectRoot);
  const calls = [];
  visitBehaviorNode(block.node, (node) => {
    if (node.type !== 'CallExpression') {
      return;
    }
    const target = resolveCallTarget(node, bindings, sourcePaths, block.file.path, projectRoot);
    if (!target) {
      return;
    }
    const affectedPaths = reachableSourcePaths(target.modulePath, sourceFacts, projectRoot);
    if (affectedPaths.length === 0) {
      return;
    }
    calls.push({
      affectedPaths,
      exportName: target.exportName,
      modulePath: target.modulePath,
      node
    });
  });
  return calls;
}

function moduleBindings(file, sourcePaths, bindingModel = null, projectRoot = null) {
  let model = bindingModel;
  if (!model) {
    const parser = loadBehaviorParser();
    if (parser.error) {
      return { byBinding: new Map(), model: null };
    }
    try {
      model = createBindingModel(parser.parse(file.contents, {
        plugins: proofParserPlugins(file.path),
        sourceType: 'unambiguous'
      }).program);
    } catch (error) {
      return { byBinding: new Map(), model: null };
    }
  }
  const byBinding = new Map();
  const add = (identifier, target) => {
    if (!identifier || identifier.type !== 'Identifier') {
      return;
    }
    const binding = model.declarationBinding(identifier);
    if (binding) {
      byBinding.set(binding, target);
    }
  };
  visitBehaviorNode(model.ast, (node) => {
    if (node.type === 'VariableDeclarator' && node.init) {
      let target = null;
      if (isRequireCall(node.init)) {
        const specifier = node.init.arguments[0].value;
        target = {
          exportName: null,
          modulePath: resolveKnownSource(file.path, specifier, sourcePaths, projectRoot),
          specifier
        };
      } else {
        target = moduleBindingExpressionTarget(node.init, { byBinding, model });
      }
      if (!target) {
        return;
      }
      if (node.id.type === 'Identifier') {
        add(node.id, target);
      } else if (node.id.type === 'ObjectPattern') {
        for (const property of node.id.properties || []) {
          if (property.type !== 'ObjectProperty' || property.computed || property.key.type !== 'Identifier') {
            continue;
          }
          const local = property.value.type === 'Identifier'
            ? property.value
            : property.value && property.value.type === 'AssignmentPattern' && property.value.left.type === 'Identifier'
              ? property.value.left
              : null;
          if (local) {
            add(local, moduleTargetWithExport(target, property.key.name));
          }
        }
      }
    } else if (node.type === 'ImportDeclaration' && node.source && typeof node.source.value === 'string') {
      const specifier = node.source.value;
      const modulePath = resolveKnownSource(file.path, specifier, sourcePaths, projectRoot);
      for (const imported of node.specifiers || []) {
        if (imported.type === 'ImportSpecifier') {
          add(imported.local, moduleTargetWithExport({ modulePath, specifier, exportName: null }, imported.imported.name || imported.imported.value));
        } else if (imported.type === 'ImportDefaultSpecifier') {
          add(imported.local, moduleTargetWithExport({ modulePath, specifier, exportName: null }, 'default'));
        } else if (imported.type === 'ImportNamespaceSpecifier') {
          add(imported.local, { modulePath, specifier, exportName: null });
        }
      }
    }
  });
  return { byBinding, model };
}

function moduleBindingExpressionTarget(node, bindings) {
  if (!node || !bindings || !bindings.model) {
    return null;
  }
  if (node.type === 'AwaitExpression') {
    return moduleBindingExpressionTarget(node.argument, bindings);
  }
  if (isDynamicImportCall(node)) {
    return {
      dynamicImport: true,
      exportName: null,
      modulePath: null,
      specifier: dynamicImportSpecifier(node)
    };
  }
  if (isRequireCall(node)) {
    return {
      exportName: null,
      modulePath: null,
      specifier: node.arguments[0].value
    };
  }
  if (node.type === 'Identifier') {
    const binding = bindings.model.referenceBinding(node);
    return binding ? bindings.byBinding.get(binding) || null : null;
  }
  if (node.type === 'MemberExpression') {
    const target = moduleBindingExpressionTarget(node.object, bindings);
    const property = staticMemberName(node);
    return target && property ? moduleTargetWithExport(target, property) : null;
  }
  return null;
}

function moduleTargetWithExport(target, exportName) {
  const inheritedPath = Array.isArray(target && target.exportPath)
    ? target.exportPath
    : target && target.exportName
      ? [target.exportName]
      : [];
  return {
    ...target,
    exportName,
    exportPath: [...inheritedPath, exportName]
  };
}

function isRequireCall(node) {
  return node && node.type === 'CallExpression' && node.callee && node.callee.type === 'Identifier' && node.callee.name === 'require' &&
    node.arguments && node.arguments[0] && node.arguments[0].type === 'StringLiteral';
}

function isDynamicImportCall(node) {
  return Boolean(node && (
    (node.type === 'ImportExpression' && node.source) ||
    (node.type === 'CallExpression' && node.callee && node.callee.type === 'Import')
  ));
}

function dynamicImportSpecifier(node) {
  const source = node.type === 'ImportExpression' ? node.source : node.arguments && node.arguments[0];
  return source && source.type === 'StringLiteral' ? source.value : null;
}

function resolveCallTarget(node, bindings, sourcePaths, fromPath, projectRoot = null) {
  if (node.callee.type === 'Identifier') {
    const binding = bindings.model && bindings.model.referenceBinding(node.callee);
    return binding ? bindings.byBinding.get(binding) || null : null;
  }
  if (node.callee.type === 'MemberExpression' && node.callee.object && node.callee.object.type === 'Identifier') {
    const binding = bindings.model && bindings.model.referenceBinding(node.callee.object);
    const target = binding ? bindings.byBinding.get(binding) : null;
    if (!target || !target.modulePath) {
      return null;
    }
    return { ...target, exportName: staticMemberName(node.callee) || target.exportName };
  }
  if (node.callee.type === 'MemberExpression' && isRequireCall(node.callee.object)) {
    const modulePath = resolveKnownSource(fromPath, node.callee.object.arguments[0].value, sourcePaths, projectRoot);
    return modulePath ? { modulePath, exportName: staticMemberName(node.callee) } : null;
  }
  return null;
}

function resolveKnownSource(fromPath, specifier, sourcePaths, projectRoot = null) {
  if (projectRoot) {
    const resolved = resolveProofModuleSpecifier(projectRoot, fromPath, specifier);
    return resolved.status === 'source' && sourcePaths.includes(resolved.path) ? resolved.path : null;
  }
  if (typeof specifier !== 'string' || !specifier.startsWith('.')) {
    return null;
  }
  const base = path.posix.normalize(path.posix.join(path.posix.dirname(fromPath), specifier));
  const candidates = [base];
  if (base === '.') {
    const packageEntry = projectRoot && resolvePackageRootModule(projectRoot);
    if (packageEntry) {
      candidates.push(packageEntry);
    }
  }
  if (!path.posix.extname(base)) {
    for (const extension of SOURCE_EXTENSIONS) {
      candidates.push(`${base}${extension}`, `${base}/index${extension}`);
    }
  }
  for (const candidate of candidates) {
    const normalized = candidate.replace(/^\.\//, '');
    if (sourcePaths.includes(normalized)) {
      return normalized;
    }
  }
  return null;
}

function reachableSourcePaths(startPath, sourceFacts, projectRoot = null) {
  const byPath = new Map(sourceFacts.filter((fact) => !fact.error).map((fact) => [fact.file.path, fact.file]));
  if (projectRoot && startPath) {
    return collectModuleClosure(projectRoot, startPath).filter((filePath) => byPath.has(filePath));
  }
  const reachable = new Set();
  const queue = startPath ? [startPath] : [];
  while (queue.length > 0) {
    const current = queue.shift();
    if (reachable.has(current)) {
      continue;
    }
    reachable.add(current);
    const file = byPath.get(current);
    if (!file) {
      continue;
    }
    for (const specifier of collectModuleSpecifiers(file.contents)) {
      const target = resolveKnownSource(current, specifier, [...byPath.keys()]);
      if (target) {
        queue.push(target);
      }
    }
  }
  return [...reachable];
}

function edgeCallMatches(id, calls, block, fact, failureObligation = null) {
  const relevantCalls = calls.filter((call) => call.affectedPaths.includes(fact.file.path));
  if (id === 'empty-input') {
    return relevantCalls.some((call) => call.node.arguments.some(isEmptyArgument));
  }
  if (id === 'null') {
    return relevantCalls.some((call) => call.node.arguments.some(isNullArgument));
  }
  if (id === 'boundary-values') {
    const values = relevantCalls.flatMap((call) => call.node.arguments.map(argumentValue));
    return fact.facts.boundaryValues.some((boundary) => {
      return values.some((value) => typeof value === 'string' && [boundary, boundary + 1, Math.max(0, boundary - 1)].includes(value.length)) ||
        values.some((value) => typeof value === 'number' && Math.abs(value - boundary) <= 1);
    });
  }
  if (id === 'failure-path') {
    return Boolean(matchingFailureAssertion(block, calls, fact, failureObligation));
  }
  if (id === 'concurrency') {
    return hasConcurrentProductCalls(block.node, relevantCalls);
  }
  return assertionNodes(block.node).some((assertion) => assertionObservesEffect(assertion, block.bindingModel)) && relevantCalls.length > 0;
}

function parseFailurePathObligation(testObligations) {
  if (!Array.isArray(testObligations)) {
    return { reason: 'The retained failure-path obligation is unavailable.', valid: false };
  }
  const obligations = testObligations.filter((obligation) => obligation && obligation.case === 'failure-path');
  if (obligations.length !== 1 || typeof obligations[0].obligation !== 'string') {
    return { reason: 'The retained failure-path obligation is missing or malformed.', valid: false };
  }
  const outcome = validateExpectedFailureOutcome(obligations[0].expectedFailureOutcome);
  if (!outcome.valid) {
    return { reason: outcome.reason, valid: false };
  }
  return {
    obligation: obligations[0].obligation,
    outcome,
    valid: true
  };
}

function validateExpectedFailureOutcome(outcome) {
  if (!outcome || outcome.kind !== 'error' || typeof outcome.generic !== 'boolean' || !Array.isArray(outcome.constraints)) {
    return { reason: 'The retained failure-path obligation has no supported structured expected failure outcome.', valid: false };
  }
  const constraints = [];
  for (const constraint of outcome.constraints) {
    if (!constraint || !['message', 'name'].includes(constraint.kind) || !['exact', 'regex'].includes(constraint.type)) {
      return { reason: 'The retained structured expected failure outcome is malformed.', valid: false };
    }
    if (constraint.type === 'exact' && typeof constraint.value !== 'string') {
      return { reason: 'The retained structured expected failure outcome is malformed.', valid: false };
    }
    if (constraint.type === 'regex' && (typeof constraint.pattern !== 'string' || typeof constraint.flags !== 'string')) {
      return { reason: 'The retained structured expected failure outcome is malformed.', valid: false };
    }
    constraints.push({ ...constraint });
  }
  if (!outcome.generic && constraints.length === 0) {
    return { reason: 'The retained structured expected failure outcome has no observable constraint.', valid: false };
  }
  return { constraints, generic: outcome.generic, valid: true };
}

function matchingFailureAssertion(block, calls, fact, failureObligation) {
  if (!failureObligation || !failureObligation.valid) {
    return null;
  }
  const relevantCalls = calls.filter((call) => call.affectedPaths.includes(fact.file.path));
  for (const assertion of assertionNodes(block.node)) {
    if (!isErrorAssertion(assertion) || !behaviorCallNodes(assertion).some((call) => relevantCalls.some((candidate) => candidate.node === call))) {
      continue;
    }
    const matcher = failureAssertionMatcher(assertion);
    if (!matcher || !failureMatcherMatchesOutcome(matcher, failureObligation.outcome)) {
      continue;
    }
    return {
      matcher: describeFailureMatcher(matcher),
      text: sourceText(block.file.contents, assertion),
      outcome: failureObligation.outcome
    };
  }
  return null;
}

function failureAssertionMatcher(assertion) {
  const expected = assertion.arguments && assertion.arguments[1];
  return expected ? parseFailureMatcher(expected) : null;
}

function parseFailureMatcher(node) {
  if (node.type === 'RegExpLiteral') {
    return { kind: 'message', type: 'regex', pattern: node.pattern, flags: node.flags || '' };
  }
  if (node.type === 'Identifier' && FAILURE_CONSTRUCTOR_NAMES.has(node.name)) {
    return { kind: 'name', type: 'exact', value: node.name };
  }
  if (node.type === 'NewExpression' && node.callee && node.callee.type === 'Identifier' && FAILURE_CONSTRUCTOR_NAMES.has(node.callee.name)) {
    const message = node.arguments && node.arguments[0] ? parseFailureMatcherValue(node.arguments[0]) : null;
    return {
      kind: 'error',
      message,
      name: node.callee.name
    };
  }
  if (node.type === 'ObjectExpression') {
    const properties = [];
    for (const property of node.properties || []) {
      if (property.type !== 'ObjectProperty' || property.computed) {
        return null;
      }
      const name = property.key && (property.key.name || property.key.value);
      const value = parseFailureMatcherValue(property.value);
      if (typeof name !== 'string' || !value) {
        return null;
      }
      properties.push({ name, value });
    }
    return properties.length > 0 ? { kind: 'object', properties } : null;
  }
  return null;
}

function parseFailureMatcherValue(node) {
  if (node.type === 'RegExpLiteral') {
    return { type: 'regex', pattern: node.pattern, flags: node.flags || '' };
  }
  if (node.type === 'StringLiteral') {
    return { type: 'exact', value: node.value };
  }
  if (node.type === 'NumericLiteral' || node.type === 'BooleanLiteral') {
    return { type: 'exact', value: node.value };
  }
  return null;
}

function failureMatcherMatchesOutcome(matcher, outcome) {
  if (!matcher || !outcome || !outcome.valid) {
    return false;
  }
  if (outcome.generic) {
    return true;
  }
  return outcome.constraints.every((constraint) => failureMatcherMatchesConstraint(matcher, constraint));
}

function failureMatcherMatchesConstraint(matcher, constraint) {
  if (matcher.kind === 'message') {
    return matchFailureValue(matcher, constraint);
  }
  if (matcher.kind === 'name') {
    return constraint.kind === 'name'
      ? matchFailureValue({ type: matcher.type, value: matcher.value }, constraint)
      : false;
  }
  if (matcher.kind === 'error') {
    if (constraint.kind === 'name' && constraint.type === 'exact') {
      return matcher.name === constraint.value;
    }
    return matcher.message ? matchFailureValue(matcher.message, constraint) : false;
  }
  if (matcher.kind === 'object') {
    const property = matcher.properties.find((candidate) => candidate.name === constraint.kind);
    return property ? matchFailureValue(property.value, constraint) : false;
  }
  return false;
}

function matchFailureValue(matcher, constraint) {
  if (matcher.type === 'exact' && constraint.type === 'exact') {
    return String(matcher.value) === String(constraint.value);
  }
  if (matcher.type === 'regex' && constraint.type === 'exact') {
    return testFailureRegex(matcher, String(constraint.value));
  }
  if (matcher.type === 'exact' && constraint.type === 'regex') {
    return testFailureRegex(constraint, String(matcher.value));
  }
  return matcher.type === 'regex' && constraint.type === 'regex' &&
    matcher.pattern === constraint.pattern && matcher.flags === constraint.flags;
}

function testFailureRegex(matcher, value) {
  try {
    const regex = new RegExp(matcher.pattern, matcher.flags);
    return regex.test(value);
  } catch (error) {
    return false;
  }
}

function describeFailureMatcher(matcher) {
  if (matcher.kind === 'message') {
    return matcher.type === 'regex'
      ? `/${matcher.pattern}/${matcher.flags}`
      : matcher.value;
  }
  if (matcher.kind === 'name') {
    return matcher.value;
  }
  if (matcher.kind === 'error') {
    return { name: matcher.name, message: matcher.message ? describeFailureMatcherValue(matcher.message) : null };
  }
  return Object.fromEntries(matcher.properties.map((property) => [property.name, describeFailureMatcherValue(property.value)]));
}

function describeFailureMatcherValue(value) {
  return value.type === 'regex' ? `/${value.pattern}/${value.flags}` : value.value;
}

const FAILURE_CONSTRUCTOR_NAMES = new Set([
  'AggregateError',
  'Error',
  'EvalError',
  'RangeError',
  'ReferenceError',
  'SyntaxError',
  'TypeError',
  'URIError'
]);

function hasConcurrentProductCalls(root, relevantCalls) {
  let matched = false;
  visitBehaviorNode(root, (node) => {
    if (matched || node.type !== 'CallExpression' || !node.callee || node.callee.type !== 'MemberExpression') {
      return;
    }
    const object = node.callee.object;
    const method = staticMemberName(node.callee);
    if (!object || object.type !== 'Identifier' || object.name !== 'Promise' || !['all', 'allSettled', 'any', 'race'].includes(method)) {
      return;
    }
    const iterable = node.arguments && node.arguments[0];
    if (!iterable || iterable.type !== 'ArrayExpression') {
      return;
    }
    const immediateCalls = iterable.elements
      .filter((element) => element && element.type === 'CallExpression')
      .filter((element) => relevantCalls.some((call) => call.node === element));
    matched = immediateCalls.length >= 2;
  });
  return matched;
}

function assertionObservesEffect(assertion, bindingModel = null) {
  let observed = false;
  visitBehaviorNode(assertion, (node) => {
    const binding = node.type === 'Identifier' && bindingModel ? bindingModel.referenceBinding(node) : null;
    if (binding && /(?:write|state|effect|event|record|persist|file|output|external|saved)/i.test(node.name) && bindingHasMutation(binding, bindingModel)) {
      observed = true;
    }
    if (node.type === 'CallExpression' && node.callee && node.callee.type === 'MemberExpression' &&
      ['existsSync', 'statSync', 'accessSync'].includes(staticMemberName(node.callee))) {
      observed = true;
    }
  });
  return observed;
}

function bindingHasMutation(binding, bindingModel) {
  if (!binding || !bindingModel) {
    return false;
  }
  let mutated = false;
  visitBehaviorNode(bindingModel.ast, (node) => {
    if (mutated) {
      return;
    }
    if (node.type === 'AssignmentExpression' && isSharedStateTargetForBinding(node.left, binding, bindingModel)) {
      mutated = true;
    } else if (node.type === 'UpdateExpression' && isSharedStateTargetForBinding(node.argument, binding, bindingModel)) {
      mutated = true;
    } else if (node.type === 'CallExpression' && node.callee && node.callee.type === 'MemberExpression' &&
      ['add', 'push', 'set', 'splice'].includes(staticMemberName(node.callee)) &&
      isSharedStateTargetForBinding(node.callee.object, binding, bindingModel)) {
      mutated = true;
    }
  });
  return mutated;
}

function isSharedStateTargetForBinding(node, binding, bindingModel) {
  if (!node) {
    return false;
  }
  if (node.type === 'Identifier') {
    return bindingModel.referenceBinding(node) === binding;
  }
  if (node.type === 'MemberExpression') {
    let object = node.object;
    while (object && object.type === 'MemberExpression') {
      object = object.object;
    }
    return object && object.type === 'Identifier' && bindingModel.referenceBinding(object) === binding;
  }
  return false;
}

function isEmptyArgument(node) {
  return Boolean(node && ((node.type === 'StringLiteral' && node.value === '') ||
    (node.type === 'ArrayExpression' && node.elements.length === 0) ||
    (node.type === 'ObjectExpression' && node.properties.length === 0)));
}

function isNullArgument(node) {
  return Boolean(node && (node.type === 'NullLiteral' || (node.type === 'Identifier' && node.name === 'undefined')));
}

function argumentValue(node) {
  if (!node) {
    return undefined;
  }
  if (['StringLiteral', 'NumericLiteral', 'BooleanLiteral'].includes(node.type)) {
    return node.value;
  }
  if (node.type === 'NullLiteral') {
    return null;
  }
  return undefined;
}

function uniqueEvidence(values) {
  const seen = new Set();
  return values.filter((value) => {
    const key = `${value.path}\u0000${value.text}\u0000${value.reason || ''}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

function assessMockBoundaries(testFiles, externalBoundaries = [], productPaths = []) {
  const internal = [];
  const unobservedExternal = [];
  const allowedExternal = [];
  const closureFiles = uniqueProofFiles(testFiles);
  const availablePaths = closureFiles.map((file) => file.path);
  for (const file of closureFiles) {
    for (const mock of mockTargetsFromAst(file, closureFiles, availablePaths, productPaths)) {
      const entry = { path: file.path, target: mock.target };
      if (mock.internal) {
        internal.push(entry);
      } else if (externalBoundaries.includes(mock.target)) {
        allowedExternal.push(entry);
      } else {
        unobservedExternal.push(entry);
      }
    }
  }
  return {
    allowedExternal,
    internal,
    status: internal.length === 0 && unobservedExternal.length === 0 ? 'PASS' : 'FAIL',
    unobservedExternal
  };
}

function mockTargetsFromAst(file, availableFiles = [file], availablePaths = availableFiles.map((item) => item.path), productPaths = []) {
  const targets = [];
  const parser = loadBehaviorParser();
  if (parser.error) {
    return targets;
  }
  let ast;
  try {
    ast = parser.parse(file.contents, { plugins: proofParserPlugins(file.path), sourceType: 'unambiguous' }).program;
  } catch (error) {
    return targets;
  }
  const bindingModel = createBindingModel(ast);
  const bindings = moduleBindings(file, availablePaths, bindingModel);
  const localMutationFunctions = localMutationFunctionSummaries(ast, bindingModel);
  const importedMutationFunctions = importedMutationFunctionSummaries(bindings, availableFiles, productPaths);
  function add(target) {
    if (typeof target !== 'string' || target.length === 0) {
      return;
    }
    targets.push({ internal: target.startsWith('.') || target.startsWith('internal:'), target });
  }
  visitBehaviorNode(ast, (node) => {
    if (node.type === 'CallExpression') {
      const helper = mutationFunctionForCall(node, bindingModel, bindings, localMutationFunctions, importedMutationFunctions);
      if (helper) {
        for (const parameterIndex of helper.parameterIndices) {
          const provenance = mutationArgumentProvenance(
            node.arguments[parameterIndex],
            bindings,
            bindingModel,
            availablePaths,
            productPaths,
            file.path,
            new Set()
          );
          add(provenance.target || (provenance.kind === 'unresolved'
            ? 'internal:unresolved-product-mutation-target'
            : null));
        }
        return;
      }
    }
    if (node.type === 'CallExpression' && node.callee && node.callee.type === 'MemberExpression') {
      const object = node.callee.object;
      const method = staticMemberName(node.callee);
      const objectTarget = moduleTargetForExpression(object, bindings);
      const mockApi = object && object.type === 'Identifier' && (
        ['mock', 'jest', 'vi', 'sinon'].includes(object.name) ||
        (objectTarget && objectTarget.specifier === 'node:test' && objectTarget.exportName === 'mock') ||
        (objectTarget && objectTarget.specifier === 'sinon')
      );
      if (object && object.type === 'Identifier' && ['mock', 'jest', 'vi'].includes(object.name) && ['mock', 'module'].includes(method)) {
        const target = node.arguments[0] && evaluateStaticString(node.arguments[0]);
        add(target || 'internal:dynamic-mock-target');
        return;
      }
      if (mockApi && ['method', 'property', 'spyOn', 'stub', 'replace', 'replaceProperty', 'spy'].includes(method)) {
        add(bindingTarget(node.arguments[0], bindings) || 'internal:unresolved-mock-target');
        return;
      }
      if (object && object.type === 'Identifier' && object.name === 'Object' && ['defineProperty', 'assign'].includes(method)) {
        add(bindingTarget(node.arguments[0], bindings));
        return;
      }
      if (object && object.type === 'Identifier' && object.name === 'Reflect' && method === 'set') {
        add(bindingTarget(node.arguments[0], bindings));
        return;
      }
    }
    if (node.type === 'CallExpression' && node.callee && node.callee.type === 'Identifier' && ['stub', 'replace', 'spy'].includes(node.callee.name)) {
      const calleeTarget = moduleTargetForExpression(node.callee, bindings);
      if (['sinon', 'node:test'].includes(calleeTarget && calleeTarget.specifier)) {
        add(bindingTarget(node.arguments[0], bindings) || 'internal:unresolved-mock-target');
      }
    }
    if (node.type === 'AssignmentExpression' && node.left && node.left.type === 'MemberExpression') {
      add(monkeyPatchTarget(node.left.object, bindings));
    }
  });
  return targets;
}

function localMutationFunctionSummaries(ast, bindingModel) {
  const summaries = new Map();
  function add(functionNode, binding) {
    if (!functionNode || !binding) {
      return;
    }
    const summary = mutationFunctionSummary(functionNode, bindingModel);
    if (summary) {
      summaries.set(binding, summary);
    }
  }
  visitBehaviorNode(ast, (node) => {
    if (node.type === 'FunctionDeclaration' && node.id) {
      add(node, bindingModel.declarationBinding(node.id));
    } else if (node.type === 'VariableDeclarator' && node.id && node.id.type === 'Identifier' &&
      node.init && ['ArrowFunctionExpression', 'FunctionExpression'].includes(node.init.type)) {
      add(node.init, bindingModel.declarationBinding(node.id));
    }
  });
  return summaries;
}

function importedMutationFunctionSummaries(bindings, availableFiles, productPaths) {
  const byBinding = new Map();
  const byTarget = new Map();
  const productPathSet = new Set(productPaths);
  const parsed = new Map();
  for (const [binding, target] of bindings.byBinding) {
    if (!target.modulePath || !target.exportName || productPathSet.has(target.modulePath)) {
      continue;
    }
    const file = availableFiles.find((candidate) => candidate.path === target.modulePath);
    if (!file) {
      continue;
    }
    let summaries = parsed.get(file.path);
    if (!summaries) {
      const parser = loadBehaviorParser();
      if (parser.error) {
        continue;
      }
      try {
        const ast = parser.parse(file.contents, {
          plugins: proofParserPlugins(file.path),
          sourceType: 'unambiguous'
        }).program;
        summaries = exportedMutationFunctionSummaries(ast, createBindingModel(ast));
        parsed.set(file.path, summaries);
      } catch (error) {
        continue;
      }
    }
    const summary = summaries.get(target.exportName);
    if (summary) {
      byBinding.set(binding, summary);
      byTarget.set(`${target.modulePath}\u0000${target.exportName}`, summary);
    }
  }
  return { byBinding, byTarget };
}

function exportedMutationFunctionSummaries(ast, bindingModel) {
  const summaries = new Map();
  const localFunctions = localMutationFunctionSummaries(ast, bindingModel);
  const add = (name, summary) => {
    if (name && summary) {
      summaries.set(name, summary);
    }
  };
  visitBehaviorNode(ast, (node) => {
    if (node.type === 'ExportNamedDeclaration') {
      addExportedMutationDeclaration(node.declaration, bindingModel, localFunctions, add);
      for (const specifier of node.specifiers || []) {
        if (specifier.type !== 'ExportSpecifier') {
          continue;
        }
        const localBinding = bindingModel.referenceBinding(specifier.local) || bindingModel.declarationBinding(specifier.local);
        add(exportedSpecifierName(specifier.exported), localFunctions.get(localBinding));
      }
      return;
    }
    if (node.type === 'ExportDefaultDeclaration') {
      const declaration = node.declaration;
      if (declaration && ['ArrowFunctionExpression', 'FunctionExpression'].includes(declaration.type)) {
        add('default', mutationFunctionSummary(declaration, bindingModel));
      } else if (declaration && declaration.type === 'FunctionDeclaration') {
        add('default', localFunctions.get(bindingModel.declarationBinding(declaration.id)) || mutationFunctionSummary(declaration, bindingModel));
      } else if (declaration && declaration.type === 'Identifier') {
        add('default', localFunctions.get(bindingModel.referenceBinding(declaration)));
      }
      return;
    }
    if (node.type === 'AssignmentExpression' && node.right) {
      const exportName = exportedFunctionName(node.left);
      const summary = exportName
        ? ['ArrowFunctionExpression', 'FunctionExpression'].includes(node.right.type)
          ? mutationFunctionSummary(node.right, bindingModel)
          : node.right.type === 'Identifier'
            ? localFunctions.get(bindingModel.referenceBinding(node.right)) || null
            : null
        : null;
      add(exportName, summary);
    }
  });
  return summaries;
}

function addExportedMutationDeclaration(declaration, bindingModel, localFunctions, add) {
  if (!declaration) {
    return;
  }
  if (declaration.type === 'FunctionDeclaration' && declaration.id) {
    add(declaration.id.name, localFunctions.get(bindingModel.declarationBinding(declaration.id)) || mutationFunctionSummary(declaration, bindingModel));
    return;
  }
  if (declaration.type !== 'VariableDeclaration') {
    return;
  }
  for (const declarator of declaration.declarations || []) {
    if (!declarator.id || declarator.id.type !== 'Identifier') {
      continue;
    }
    add(declarator.id.name, localFunctions.get(bindingModel.declarationBinding(declarator.id)) ||
      (declarator.init && ['ArrowFunctionExpression', 'FunctionExpression'].includes(declarator.init.type)
        ? mutationFunctionSummary(declarator.init, bindingModel)
        : null));
  }
}

function exportedSpecifierName(node) {
  return node && node.type === 'Identifier'
    ? node.name
    : node && node.type === 'StringLiteral'
      ? node.value
      : null;
}

function exportedFunctionName(node) {
  if (!node || node.type !== 'MemberExpression' || node.computed) {
    return null;
  }
  if (node.object && node.object.type === 'Identifier' && node.object.name === 'exports') {
    return staticMemberName(node);
  }
  if (node.object && node.object.type === 'MemberExpression' && !node.object.computed &&
    node.object.object && node.object.object.type === 'Identifier' && node.object.object.name === 'module' &&
    staticMemberName(node.object) === 'exports') {
    return staticMemberName(node);
  }
  return null;
}

function mutationFunctionSummary(functionNode, bindingModel) {
  const parameterIndices = mutationParameterIndices(functionNode, bindingModel);
  return parameterIndices.length > 0 ? { parameterIndices } : null;
}

function mutationFunctionForCall(node, bindingModel, bindings, localFunctions, importedFunctions) {
  if (!node.callee) {
    return null;
  }
  if (node.callee.type === 'Identifier') {
    const binding = bindingModel.referenceBinding(node.callee);
    return localFunctions.get(binding) || importedFunctions.byBinding.get(binding) || mockMutationFunctionSummary(binding, bindings);
  }
  if (node.callee.type === 'MemberExpression' && node.callee.object && node.callee.object.type === 'Identifier') {
    const binding = bindingModel.referenceBinding(node.callee.object);
    const target = binding ? bindings.byBinding.get(binding) : null;
    const exportName = target && staticMemberName(node.callee);
    return target && exportName
      ? importedFunctions.byTarget.get(`${target.modulePath}\u0000${exportName}`) || null
      : null;
  }
  return null;
}

function mockMutationFunctionSummary(binding, bindings) {
  const target = binding ? bindings.byBinding.get(binding) : null;
  if (!target || !isMockMutationTarget(target)) {
    return null;
  }
  return { parameterIndices: [0] };
}

function isMockMutationTarget(target) {
  const pathValue = Array.isArray(target.exportPath)
    ? target.exportPath
    : target.exportName
      ? [target.exportName]
      : [];
  return target && (
    (target.specifier === 'node:test' && pathValue.length === 2 && pathValue[0] === 'mock' && pathValue[1] === 'method') ||
    (target.specifier === 'sinon' && pathValue.length === 1 && ['replace', 'spy', 'stub'].includes(pathValue[0]))
  );
}

function mutationArgumentProvenance(node, bindings, bindingModel, availablePaths, productPaths, fromPath, seen) {
  if (!node) {
    return { kind: 'unknown', target: null };
  }
  const moduleTarget = mutationModuleTarget(node, bindings, availablePaths, fromPath);
  if (moduleTarget) {
    return {
      kind: moduleTarget.modulePath && productPaths.includes(moduleTarget.modulePath) ? 'product' : 'module',
      target: moduleTarget.specifier
    };
  }
  if (['ArrayExpression', 'BooleanLiteral', 'FunctionExpression', 'NullLiteral', 'NumericLiteral', 'ObjectExpression', 'StringLiteral', 'TemplateLiteral', 'ArrowFunctionExpression', 'NewExpression'].includes(node.type)) {
    return { kind: 'local', target: null };
  }
  if (['AwaitExpression', 'TSAsExpression', 'TSTypeAssertion', 'TypeCastExpression'].includes(node.type)) {
    return mutationArgumentProvenance(node.argument || node.expression, bindings, bindingModel, availablePaths, productPaths, fromPath, seen);
  }
  if (node.type === 'Identifier') {
    const binding = bindingModel.referenceBinding(node);
    if (!binding || seen.has(binding)) {
      return { kind: 'unknown', target: null };
    }
    seen.add(binding);
    const declaration = binding.declaration;
    const parent = bindingModel.parentOf(declaration);
    if (parent && parent.type === 'VariableDeclarator' && parent.init) {
      return mutationArgumentProvenance(parent.init, bindings, bindingModel, availablePaths, productPaths, fromPath, seen);
    }
    return { kind: 'unknown', target: null };
  }
  if (node.type === 'ConditionalExpression') {
    const left = mutationArgumentProvenance(node.consequent, bindings, bindingModel, availablePaths, productPaths, fromPath, new Set(seen));
    const right = mutationArgumentProvenance(node.alternate, bindings, bindingModel, availablePaths, productPaths, fromPath, new Set(seen));
    if (left.kind === 'local' && right.kind === 'local') {
      return { kind: 'local', target: null };
    }
    if (left.target && left.target === right.target) {
      return { kind: left.kind, target: left.target };
    }
    return { kind: 'unresolved', target: null };
  }
  if (node.type === 'CallExpression') {
    const target = mutationModuleTarget(node.callee, bindings, availablePaths, fromPath);
    return target
      ? { kind: 'unresolved', target: null }
      : { kind: 'unknown', target: null };
  }
  if (node.type === 'MemberExpression') {
    const root = memberRoot(node);
    return root
      ? mutationArgumentProvenance(root, bindings, bindingModel, availablePaths, productPaths, fromPath, new Set(seen))
      : { kind: 'unknown', target: null };
  }
  return { kind: 'unknown', target: null };
}

function mutationModuleTarget(node, bindings, availablePaths, fromPath) {
  const target = moduleTargetForExpression(node, bindings);
  if (target && (target.modulePath || (target.specifier && !target.specifier.startsWith('.')))) {
    return target;
  }
  if (isRequireCall(node)) {
    const specifier = node.arguments[0].value;
    const modulePath = resolveKnownSource(fromPath, specifier, availablePaths);
    return { exportName: null, modulePath, specifier };
  }
  return null;
}

function mutationParameterIndices(functionNode, bindingModel) {
  const parameters = new Map();
  for (const [index, parameter] of (functionNode.params || []).entries()) {
    if (parameter.type === 'Identifier') {
      const binding = bindingModel.declarationBinding(parameter);
      if (binding) {
        parameters.set(binding, index);
      }
    }
  }
  const indices = new Set();
  visitBehaviorNode(functionNode.body, (node) => {
    const receiver = mutationReceiver(node);
    if (!receiver) {
      return;
    }
    const binding = receiver.type === 'Identifier'
      ? bindingModel.referenceBinding(receiver)
      : bindingModel.referenceBinding(receiver.object);
    if (parameters.has(binding)) {
      indices.add(parameters.get(binding));
    }
  });
  return [...indices].sort((left, right) => left - right);
}

function mutationReceiver(node) {
  if (node.type === 'AssignmentExpression' && node.left && node.left.type === 'MemberExpression') {
    return memberRoot(node.left);
  }
  if (node.type !== 'CallExpression' || !node.callee || node.callee.type !== 'MemberExpression') {
    return null;
  }
  const object = node.callee.object;
  const method = staticMemberName(node.callee);
  if (object && object.type === 'Identifier' && object.name === 'Reflect' && method === 'set') {
    return node.arguments[0] && node.arguments[0].type === 'Identifier' ? node.arguments[0] : null;
  }
  if (object && object.type === 'Identifier' && object.name === 'Object' && ['assign', 'defineProperty'].includes(method)) {
    return node.arguments[0] && node.arguments[0].type === 'Identifier' ? node.arguments[0] : null;
  }
  return null;
}

function memberRoot(node) {
  let current = node && node.object;
  while (current && current.type === 'MemberExpression') {
    current = current.object;
  }
  return current && current.type === 'Identifier' ? current : null;
}

function bindingTarget(node, bindings) {
  if (!node || !bindings || !bindings.model) {
    return null;
  }
  const target = moduleTargetForExpression(node, bindings);
  return target ? target.specifier : null;
}

function monkeyPatchTarget(node, bindings) {
  return bindingTarget(node, bindings);
}

function assessDefensiveHandling(changedSource, edgeCases, mutation) {
  const added = changedSource.changedLines || [];
  if (added.length === 0) {
    return {
      rationale: 'No new defensive branch, catch, fallback, or nullish handling was observed in changed source.',
      status: 'NOT_APPLICABLE'
    };
  }
  const failure = edgeCases.categories.find((category) => category.id === 'failure-path');
  if (failure && failure.status === 'PASS' && mutation.status === 'PASS') {
    return {
      evidence: added,
      rationale: 'Added defensive handling is connected to a retained observable failure-path regression test and a detected changed-code mutation.',
      status: 'PASS'
    };
  }
  return {
    evidence: added,
    rationale: 'Changed source contains defensive handling, but execution and mutation evidence cannot establish that it implements approved behavior rather than masks a test-only failure.',
    status: 'INCONCLUSIVE'
  };
}

function assessImpactDefensiveHandling(impactSources, edgeCases, mutation) {
  const perSource = impactSources.files.map((sourceFile) => {
    const added = sourceFile.changedLines || [];
    if (added.length === 0) {
      return {
        path: sourceFile.path,
        rationale: 'No new defensive branch, catch, fallback, or nullish handling was observed in this fixed impact source.',
        status: 'NOT_APPLICABLE'
      };
    }
    const scopedEdges = edgeCases.perSource.find((item) => item.path === sourceFile.path);
    const failure = scopedEdges && scopedEdges.categories.find((category) => category.id === 'failure-path');
    const scopedMutation = mutation.perSource && mutation.perSource.find((item) => item.path === sourceFile.path);
    if (failure && failure.status === 'PASS' && scopedMutation && scopedMutation.status === 'PASS') {
      return {
        evidence: added,
        path: sourceFile.path,
        rationale: 'Added defensive handling is connected to a retained observable failure-path regression test and a detected mutation in this fixed impact source.',
        status: 'PASS'
      };
    }
    return {
      evidence: added,
      path: sourceFile.path,
      rationale: 'Changed defensive handling in this fixed impact source cannot be distinguished from test-masking behavior using retained failure-path and per-source mutation evidence.',
      status: 'INCONCLUSIVE'
    };
  });
  const applicable = perSource.filter((item) => item.status !== 'NOT_APPLICABLE');
  return {
    perSource,
    rationale: applicable.length === 0
      ? 'No new defensive handling was observed anywhere in the fixed dependency impact closure.'
      : 'Every changed defensive branch in the fixed dependency impact closure requires retained failure-path and per-source mutation evidence.',
    status: perSource.some((item) => item.status === 'INCONCLUSIVE')
      ? 'INCONCLUSIVE'
      : applicable.length === 0
        ? 'NOT_APPLICABLE'
        : 'PASS'
  };
}

function addedDefensiveLines(before, after, filePath, regions = null) {
  const scopedLines = regions
    ? regions.flatMap((region) => region.lines)
    : after.split(/\r?\n/).map((text, index) => ({ line: index + 1, path: filePath, text: text.trim() }));
  return scopedLines.filter((line) => /\b(?:try|catch|throw)\b|\?\?|\.catch\s*\(|\bif\s*\([^)]*(?:!|null|undefined|length)/.test(line.text));
}

function bindingCheck(evidence) {
  return evidence.valid
    ? check('wp001-wp002-binding', 'PASS', 'A genuine current WP-001 session fixed the changed scope and WP-002 quality obligations.')
    : check('wp001-wp002-binding', 'INCONCLUSIVE', 'The required WP-001 session authority or fixed WP-002 basis is incomplete.', evidence.errors);
}

function sourceStabilityCheck(readback) {
  return readback.unchanged
    ? check('target-source-stability', 'PASS', 'Target source identity was unchanged before and after behavior proof.', [readback.before])
    : check('target-source-stability', 'INCONCLUSIVE', 'Target source identity could not be confirmed unchanged before and after behavior proof.', [readback.before, readback.after]);
}

function changedSourceCheck(changedSource) {
  if (changedSource.status === 'PASS') {
    return check('changed-source', 'PASS', 'Current source differs from the source fixed when this admission session began.', changedSource.files.map((file) => ({ kind: 'source', path: file.path })));
  }
  return check('changed-source', 'INCONCLUSIVE', 'No readable changed Node or TypeScript source was established from the fixed scope.', changedSource.errors.map((error) => capabilityEvidence('changedSource', error)));
}

function impactSourceCheck(impactSources) {
  if (impactSources.status === 'PASS') {
    return check(
      'fixed-impact-sources',
      'PASS',
      'The fixed WP-001 dependency impact closure contains readable product sources.',
      impactSources.files.map((file) => ({ changed: file.changed, kind: 'source', path: file.path }))
    );
  }
  return check(
    'fixed-impact-sources',
    'INCONCLUSIVE',
    'The fixed WP-001 dependency impact closure could not be read completely.',
    impactSources.errors.map((error) => capabilityEvidence('impactSource', error))
  );
}

function relatedTestsCheck(related) {
  return related.files.length > 0
    ? check('directly-related-tests', 'PASS', 'Repository tests with a resolvable dependency on changed source were found.', related.files.map((file) => ({ kind: 'test', path: file.path })))
    : check('directly-related-tests', 'FAIL', related.reason || 'No directly related repository test was found.');
}

function impactRelatedTestsCheck(related) {
  return related.files.length > 0 && related.missingSources.length === 0
    ? check(
      'impact-related-tests',
      'PASS',
      'Retained repository tests have resolvable dependencies on every fixed impact source.',
      related.perSource.map((item) => ({ kind: 'impact-test-coverage', path: item.path, tests: item.files.map((file) => file.path) }))
    )
    : check(
      'impact-related-tests',
      'INCONCLUSIVE',
      related.reason || 'No retained repository test covers every fixed impact source.',
      related.missingSources.map((pathValue) => capabilityEvidence('impactTest', pathValue))
    );
}

function testCapabilityCheck(capability) {
  return capability.available
    ? check('test-capability', 'PASS', 'A repository-defined recognized test command is available.', [{ kind: 'command', path: 'package.json', command: capability.command }])
    : check('test-capability', 'INCONCLUSIVE', capability.reason || 'A trustworthy repository-defined test command is unavailable.');
}

function impactTestCapabilityCheck(capability) {
  return capability.available
    ? check('impact-test-capability', 'PASS', 'A repository-defined recognized test command explicitly includes every retained impact test.', [{ kind: 'command', path: 'package.json', command: capability.command }])
    : check('impact-test-capability', 'INCONCLUSIVE', capability.reason || 'A trustworthy repository-defined impact test command is unavailable.');
}

function executionCheck(execution) {
  if (execution.status === 'PASS') {
    return check('test-execution', 'PASS', 'Directly related repository tests passed in an isolated disposable copy.');
  }
  if (execution.status === 'FAIL') {
    return check('test-execution', 'FAIL', 'The repository-defined related test command failed in an isolated disposable copy.', [execution]);
  }
  return check('test-execution', 'INCONCLUSIVE', 'The required repository-defined related test command could not be executed.', [execution]);
}

function impactExecutionCheck(execution) {
  if (execution.status === 'PASS') {
    return check('impact-test-execution', 'PASS', 'Repository-defined retained impact tests passed in an isolated disposable copy.', execution.perSource);
  }
  if (execution.status === 'FAIL') {
    return check('impact-test-execution', 'FAIL', 'The repository-defined impact test command failed in an isolated disposable copy.', [execution]);
  }
  return check('impact-test-execution', 'INCONCLUSIVE', 'The required repository-defined impact test command could not be executed.', [execution]);
}

function mutationCheck(mutation) {
  if (mutation.status === 'PASS') {
    return check('mutation-detection', 'PASS', mutation.message, mutation.candidates);
  }
  if (mutation.status === 'FAIL') {
    return check('mutation-detection', 'FAIL', mutation.message, mutation.candidates);
  }
  return check('mutation-detection', 'INCONCLUSIVE', mutation.message || 'Required changed-code mutation evidence is unavailable.', mutation.candidates || []);
}

function impactMutationCheck(mutation) {
  if (mutation.status === 'PASS') {
    return check('impact-mutation-detection', 'PASS', mutation.message, mutation.perSource);
  }
  if (mutation.status === 'FAIL') {
    return check('impact-mutation-detection', 'FAIL', mutation.message, mutation.perSource);
  }
  return check('impact-mutation-detection', 'INCONCLUSIVE', mutation.message || 'Required fixed-impact mutation evidence is unavailable.', mutation.perSource || []);
}

function observabilityCheck(observability) {
  if (observability.status === 'INCONCLUSIVE') {
    return check('observable-behavior', 'INCONCLUSIVE', 'Retained test/helper closure could not be parsed or classified safely.', observability.errors || []);
  }
  return observability.status === 'PASS'
    ? check('observable-behavior', 'PASS', 'Related tests assert user-observable output, state, errors, or effects.', observability.behavioral)
    : check('observable-behavior', 'FAIL', 'Related tests do not establish user-observable behavior; implementation-only assertions are insufficient.', observability.rejected);
}

function edgeCaseCheck(edgeCases) {
  if (edgeCases.status === 'INCONCLUSIVE') {
    return check('edge-case-regressions', 'INCONCLUSIVE', 'Applicable edge-case evidence could not be established from parsed changed regions and retained test calls.', edgeCases.categories);
  }
  return edgeCases.status === 'PASS'
    ? check('edge-case-regressions', 'PASS', 'Every applicable edge-case category has a retained observable repository regression test.', edgeCases.categories)
    : check('edge-case-regressions', 'FAIL', 'An applicable edge-case category lacks a retained observable repository regression test.', edgeCases.categories.filter((category) => category.status === 'FAIL'));
}

function mockBoundaryCheck(mockBoundaries) {
  return mockBoundaries.status === 'PASS'
    ? check('mock-boundaries', 'PASS', 'Related tests use no mocks or only WP-001-observed external boundaries.', mockBoundaries.allowedExternal)
    : check('mock-boundaries', 'FAIL', 'Related tests mock an internal implementation or an unobserved external boundary.', [...mockBoundaries.internal, ...mockBoundaries.unobservedExternal]);
}

function defensiveHandlingCheck(defensiveHandling) {
  const verdict = defensiveHandling.status === 'NOT_APPLICABLE' ? 'PASS' : defensiveHandling.status;
  return check('defensive-handling', verdict, defensiveHandling.rationale, defensiveHandling.evidence || []);
}

function describeBinding(authority) {
  if (!authority) {
    return null;
  }
  return {
    impactScopeCompleteness: authority.impactScopeCompleteness,
    impactScope: authority.impactScope,
    qualityObligations: authority.qualityObligations,
    testObligations: authority.testObligations
  };
}

function describeImpactCoverage(impactSources, related, execution, mutation) {
  return {
    fixedPaths: impactSources.fixedPaths,
    perSource: impactSources.files.map((sourceFile) => {
      const tests = related.perSource.find((item) => item.path === sourceFile.path);
      const executed = execution.perSource && execution.perSource.find((item) => item.path === sourceFile.path);
      const mutated = mutation.perSource && mutation.perSource.find((item) => item.path === sourceFile.path);
      return {
        changed: sourceFile.changed,
        mutation: mutated ? {
          candidates: mutated.candidates.map((candidate) => ({
            kind: candidate.kind,
            line: candidate.line,
            result: candidate.result && candidate.result.status
          })),
          status: mutated.status
        } : { status: 'NOT_RUN' },
        path: sourceFile.path,
        testExecution: executed ? executed.status : 'NOT_RUN',
        tests: tests ? tests.files.map((file) => file.path) : []
      };
    })
  };
}

function fingerprintProject(projectRoot) {
  const hash = crypto.createHash('sha256');
  let fileCount = 0;
  function update(value) {
    hash.update(String(value));
    hash.update('\u0000');
  }
  function visit(directory, relativeDirectory) {
    const entries = fs.readdirSync(directory, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name));
    for (const entry of entries) {
      const absolute = path.join(directory, entry.name);
      const relative = relativeDirectory ? `${relativeDirectory}/${entry.name}` : entry.name;
      const metadata = fs.lstatSync(absolute);
      if (entry.isSymbolicLink()) {
        update('symlink');
        update(relative);
        update(metadata.mode & 0o7777);
        update(fs.readlinkSync(absolute));
      } else if (entry.isDirectory()) {
        update('directory');
        update(relative);
        update(metadata.mode & 0o7777);
        if (!IGNORED_DIRECTORIES.has(entry.name)) {
          visit(absolute, relative);
        }
      } else if (entry.isFile()) {
        const contents = fs.readFileSync(absolute);
        update('file');
        update(relative);
        update(metadata.mode & 0o7777);
        update(contents.length);
        hash.update(contents);
        hash.update('\u0000');
        fileCount += 1;
      }
    }
  }
  try {
    if (!fs.statSync(projectRoot).isDirectory()) {
      return { error: 'The project root is not a directory.' };
    }
    update('root');
    update(fs.lstatSync(projectRoot).mode & 0o7777);
    visit(projectRoot, '');
    return { digest: hash.digest('hex'), fileCount };
  } catch (error) {
    return { error: error.message };
  }
}

function isProductSource(filePath) {
  return SOURCE_EXTENSIONS.some((extension) => filePath.endsWith(extension)) && !isTestFile(filePath);
}

function isTestFile(filePath) {
  return filePath.split('/').some((segment) => ['__tests__', 'test', 'tests'].includes(segment)) || /\.(spec|test)\.[cm]?[jt]sx?$/.test(filePath);
}

function isRelativeSpecifier(specifier) {
  return specifier === '.' || specifier === '..' || specifier.startsWith('./') || specifier.startsWith('../');
}

function safeRelativePath(value, allowRoot) {
  if (value === '.' && allowRoot) {
    return true;
  }
  return typeof value === 'string' && value.length > 0 && !value.includes('\u0000') && !value.includes('\\') &&
    !path.posix.isAbsolute(value) && !path.win32.isAbsolute(value) && !/^[A-Za-z]:/.test(value) &&
    !value.split('/').some((segment) => !segment || segment === '.' || segment === '..');
}

function isWithin(projectRoot, candidate) {
  const relative = path.relative(path.resolve(projectRoot), path.resolve(candidate));
  return relative === '' || (!relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative));
}

function displayPath(projectRoot, absolute) {
  const relative = path.relative(projectRoot, absolute);
  return relative ? relative.split(path.sep).join('/') : '.';
}

function sourceStateEvidence(state) {
  return {
    digest: state.digest || null,
    fileCount: state.fileCount || 0,
    kind: 'source-state',
    ...(state.error ? { error: state.error } : {})
  };
}

function capabilityEvidence(pathValue, error) {
  return { error, kind: 'capability', path: pathValue };
}

function digestBuffer(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function lineAt(contents, index) {
  return contents.slice(0, index).split(/\r?\n/).length;
}

function limitOutput(value) {
  return typeof value === 'string' && value.length > 4000 ? `${value.slice(0, 4000)}\n[output truncated]` : value || '';
}

function testEnvironment() {
  const runtime = resolveSandboxRuntime();
  return {
    LANG: process.env.LANG || 'C',
    PATH: process.env.PATH || `${runtime.nodeBinDirectory}:/usr/bin:/bin`
  };
}

function check(id, verdict, message, evidence = []) {
  return { evidence, id, message, verdict };
}

function aggregateVerdict(checks) {
  if (checks.some((check) => check.verdict === 'FAIL')) {
    return 'FAIL';
  }
  if (checks.some((check) => check.verdict === 'INCONCLUSIVE')) {
    return 'INCONCLUSIVE';
  }
  return 'PASS';
}

function aggregateDeepVerdict(checks) {
  // A deep proof cannot convert missing closure-wide evidence into a definitive failure.
  if (checks.some((check) => check.verdict === 'INCONCLUSIVE')) {
    return 'INCONCLUSIVE';
  }
  return aggregateVerdict(checks);
}

function deepFreeze(value, seen = new WeakSet()) {
  if (value === null || typeof value !== 'object' || seen.has(value)) {
    return value;
  }
  seen.add(value);
  for (const item of Object.values(value)) {
    deepFreeze(item, seen);
  }
  return Object.freeze(value);
}

function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

module.exports = { createBehaviorProofSession };
