'use strict';

const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const { createAdmissionSession, resolveAdmissionCapability } = require('./admission');
const { captureSourceState, diagnoseFastProject } = require('./fast-diagnosis');
const { resolveHostReviewerTransport } = require('./reviewer-registry');

const GATE_AUTHORITIES = new WeakSet();
const DEFAULT_THRESHOLDS = Object.freeze({
  maxComplexity: 10,
  maxDepth: 2,
  maxFanIn: 10,
  maxFanOut: 10,
  maxFileLines: 300,
  maxFunctionLines: 50,
  maxReexports: 10
});

const FAST_CHECK_IDS = Object.freeze([
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
  'typescript-strict',
  'no-as-any',
  'no-as-unknown-as',
  'javascript-jsdoc',
  'circular-dependencies',
  'fixed-boundaries'
]);
const THRESHOLD_NAMES = Object.freeze([
  'maxComplexity',
  'maxDepth',
  'maxFanIn',
  'maxFanOut',
  'maxFileLines',
  'maxFunctionLines',
  'maxReexports'
]);
const SEMANTIC_REQUIREMENTS = Object.freeze([
  {
    category: 'b-1',
    id: 'b-1-error-handling-and-fallbacks',
    label: 'Error handling, meaningful fallbacks, and repeated caller defenses'
  },
  {
    category: 'b-2',
    id: 'b-2-depth-necessity',
    label: 'Necessity of deeply nested control flow'
  },
  {
    category: 'c-1',
    id: 'c-1-replacement-duplication',
    label: 'Replacement completeness, semantic duplication, and residual dead or commented code'
  },
  {
    category: 'c-2',
    id: 'c-2-silent-error-swallowing',
    label: 'Silent error swallowing'
  },
  {
    category: 'c-3',
    id: 'c-3-hidden-coupling',
    label: 'Hidden coupling, implicit contracts, initialization order, shared global state, and side-effect coupling'
  },
  {
    category: 'c-4',
    id: 'c-4-reexport-ssot-consistency',
    label: 'Re-export and canonical-source consistency'
  }
]);
const CATEGORY_DEFINITIONS = Object.freeze([
  {
    id: 'b-1',
    label: 'Error handling and fallbacks',
    mechanical: ['empty-catch'],
    semantic: ['b-1-error-handling-and-fallbacks']
  },
  {
    id: 'b-2',
    label: 'Nesting necessity',
    mechanical: ['max-depth'],
    semantic: ['b-2-depth-necessity']
  },
  {
    id: 'b-3',
    label: 'Function and file size',
    mechanical: ['function-size', 'file-size'],
    semantic: []
  },
  {
    id: 'c-1',
    label: 'Replacement, duplication, and dead code',
    mechanical: ['unreachable-code', 'dead-code', 'commented-out-code'],
    semantic: ['c-1-replacement-duplication']
  },
  {
    id: 'c-2',
    label: 'Silent error swallowing',
    mechanical: ['empty-catch'],
    semantic: ['c-2-silent-error-swallowing']
  },
  {
    id: 'c-3',
    label: 'Hidden coupling, implicit contracts, initialization order, shared global state, and side-effect coupling',
    mechanical: [],
    semantic: ['c-3-hidden-coupling']
  },
  {
    id: 'c-4',
    label: 'Re-export and SSOT consistency',
    mechanical: ['re-export-concentration'],
    semantic: ['c-4-reexport-ssot-consistency']
  },
  {
    id: 'c-5',
    label: 'Fan-in and fan-out concentration',
    mechanical: ['fan-in-concentration', 'fan-out-concentration'],
    semantic: []
  },
  {
    id: 'd-1',
    label: 'Type safety and JavaScript contracts',
    mechanical: ['typescript-strict', 'no-as-any', 'no-as-unknown-as', 'javascript-jsdoc'],
    semantic: []
  },
  {
    id: 'd-2',
    label: 'Dependency cycles and fixed boundaries',
    mechanical: ['circular-dependencies', 'fixed-boundaries'],
    semantic: []
  },
  {
    id: 'd-3',
    label: 'Complexity, depth, and function size',
    mechanical: ['complexity', 'max-depth', 'function-size'],
    semantic: []
  }
]);
const SEMANTIC_REQUIREMENT_BY_ID = new Map(SEMANTIC_REQUIREMENTS.map((item) => [item.id, item]));
const KNOWN_BASELINE_CHECK_IDS = new Set([...FAST_CHECK_IDS, ...SEMANTIC_REQUIREMENT_BY_ID.keys()]);
const ATTESTATION_FIELDS = Object.freeze([
  'reviewerId',
  'model',
  'requestDigest',
  'sourceDigest',
  'signature'
]);
const EVIDENCE_CONTRACT = Object.freeze({
  authority: {
    kind: 'wp001-admission-gate-authority',
    source: 'opaque in-process admission session'
  },
  policy: {
    kind: 'fixed-wp001-policy',
    required: ['id', 'source', 'projectRoot', 'boundaryEvidence', 'repositoryAuthority', 'thresholds']
  },
  preChange: {
    kind: 'fixed-pre-change-source-state',
    required: ['id', 'source', 'projectRoot', 'sourceReadback', 'violations']
  },
  impactScope: {
    kind: 'fixed-impact-scope',
    required: ['id', 'source', 'projectRoot', 'entries']
  },
  semanticJudgment: {
    required: ['id', 'category', 'verdict', 'rule', 'evidence', 'attestation'],
    failRequired: ['falsifier'],
    attestation: ['reviewerId', 'model', 'requestDigest', 'sourceDigest', 'signature']
  }
});

function createGatedAdmissionSession(options) {
  const { diagnoseProject } = require('./index');
  return createAdmissionSession(options, diagnoseProject, createFinalGateSession);
}

function createFinalGateSession(admissionCapability) {
  const admissionAuthority = resolveAdmissionCapability(admissionCapability);
  if (!admissionAuthority) {
    throw new TypeError('Final-Gate authority requires an opaque capability minted by createAdmissionSession.');
  }
  const authority = captureGateAuthority(admissionAuthority);
  GATE_AUTHORITIES.add(authority);
  return Object.freeze({
    run() {
      return gateProject(authority.projectRoot, { authority });
    }
  });
}

function captureGateAuthority({ admission, admittedScope, currentSourceAuthorized, projectRoot, reviewer }) {
  const errors = [];
  const root = typeof projectRoot === 'string' && projectRoot.length > 0 ? path.resolve(projectRoot) : null;
  const sessionId = crypto.randomUUID();
  if (!root || !isPlainObject(admission) || admission.verdict !== 'PASS') {
    errors.push(inputEvidence('authority', 'A passing WP-001 admission session is required before final-Gate authority can be fixed.'));
  }
  if (!isPlainObject(admittedScope) || !Array.isArray(admittedScope.entries) || admittedScope.entries.length === 0) {
    errors.push(inputEvidence('authority.impactScope', 'WP-001 did not establish a fixed admitted scope.'));
  }
  if (typeof currentSourceAuthorized !== 'function') {
    errors.push(inputEvidence('authority.currentSource', 'The admission session cannot authorize current source identity.'));
  }

  const policyId = crypto.randomUUID();
  const preChangeId = crypto.randomUUID();
  const impactScopeId = crypto.randomUUID();
  const boundaryEvidence = fixedBoundaryEvidence(root, admission);
  const repositoryAuthority = fixedRepositoryAuthority(admission);
  const before = root ? captureSourceState(root) : { error: 'Project root is unavailable.' };
  let baseline = null;
  try {
    baseline = root ? diagnoseFastProject(root, {
      boundaryEvidence,
      fixedThresholds: DEFAULT_THRESHOLDS
    }) : null;
  } catch (error) {
    errors.push(capabilityEvidence('baseline-diagnosis', error.message));
  }
  if (!baseline || !baseline.details || !baseline.details.dependencyGraph || !before.digest) {
    errors.push(capabilityEvidence('baseline-diagnosis', 'The pre-change source, checks, or dependency graph could not be captured.'));
  }

  const thresholds = fixedThresholdValues(baseline);
  const entries = isPlainObject(admittedScope) && Array.isArray(admittedScope.entries)
    ? admittedScope.entries.map((entry) => ({ mode: entry.mode, path: entry.path }))
    : [];
  const graph = baseline && baseline.details ? baseline.details.dependencyGraph : null;
  const baselineGraphUnknown = graph && Array.isArray(graph.unknown) ? graph.unknown : null;
  if (!baselineGraphUnknown) {
    errors.push(capabilityEvidence('baseline-dependency-graph', 'The pre-change dependency graph did not report its completeness.'));
  } else if (baselineGraphUnknown.length > 0) {
    errors.push(...baselineGraphUnknown.map((item) => ({
      kind: 'import',
      path: item.path,
      line: item.line,
      column: item.column,
      error: item.message || 'A pre-change dependency edge was unresolved.'
    })));
  }
  const fixedPaths = graph ? dependencyClosure(graph, entries, []) : [];
  const policy = {
    kind: 'fixed-wp001-policy',
    id: policyId,
    source: `WP-001 admission session ${sessionId}`,
    projectRoot: root,
    boundaryEvidence,
    repositoryAuthority,
    thresholds
  };
  const preChange = {
    kind: 'fixed-pre-change-source-state',
    id: preChangeId,
    source: `WP-001 admission session ${sessionId}`,
    projectRoot: root,
    sourceReadback: before,
    violations: collectBaselineMechanicalViolations(baseline)
  };
  const impactScope = {
    kind: 'fixed-impact-scope',
    id: impactScopeId,
    source: `WP-001 admission session ${sessionId}`,
    projectRoot: root,
    entries,
    fixedPaths
  };
  const pinnedReviewer = resolvePinnedReviewer(root, reviewer);
  const authority = {
    currentSourceAuthorized,
    errors,
    impactScope,
    policy,
    preChange,
    projectRoot: root,
    reviewer: pinnedReviewer.reviewer,
    reviewerIdentity: reviewerIdentity(pinnedReviewer.reviewer),
    reviewerProblem: pinnedReviewer.error,
    sessionId
  };

  const baselineSemantic = collectReviewerJudgments(authority, 'pre-change', before, fixedPaths, true);
  const incompleteBaselineSemantic = [...baselineSemantic.checks.values()].filter((item) => !['PASS', 'FAIL'].includes(item.verdict));
  authority.baselineCompleteness = {
    mechanicalGraph: baselineGraphUnknown && baselineGraphUnknown.length === 0 ? 'PASS' : 'INCONCLUSIVE',
    semantic: incompleteBaselineSemantic.length === 0 ? 'PASS' : 'INCONCLUSIVE'
  };
  if (incompleteBaselineSemantic.length > 0) {
    errors.push(capabilityEvidence(
      'baseline-semantic-review',
      'At least one pre-change semantic obligation did not produce a fully valid PASS or FAIL.'
    ));
  }
  for (const [id, item] of baselineSemantic.checks) {
    if (item.verdict !== 'FAIL') {
      continue;
    }
    for (const evidence of item.evidence) {
      preChange.violations.push(baselineSemanticViolation(id, evidence));
    }
  }
  const after = root ? captureSourceState(root) : { error: 'Project root is unavailable.' };
  if (!before.digest || !after.digest || before.digest !== after.digest) {
    errors.push(inputEvidence('authority.sourceReadback', 'Source changed while WP-001 final-Gate authority was being captured.'));
  }
  return deepFreeze(authority);
}

function fixedBoundaryEvidence(projectRoot, admission) {
  const repositoryEvidence = admission && admission.details && admission.details.repositoryEvidence;
  const direction = repositoryEvidence && repositoryEvidence.dependencyDirection;
  const edges = direction && Array.isArray(direction.internalEdges) ? direction.internalEdges : [];
  const seen = new Set();
  const allowedDependencies = [];
  for (const edge of edges) {
    if (!edge || !safeBoundaryPath(edge.from) || !safeBoundaryPath(edge.to)) {
      continue;
    }
    const key = `${edge.from}\u0000${edge.to}`;
    if (!seen.has(key)) {
      seen.add(key);
      allowedDependencies.push({ from: edge.from, to: edge.to });
    }
  }
  return {
    kind: 'fixed-observed-boundaries',
    projectRoot,
    source: 'WP-001 observed pre-change dependency direction',
    allowedDependencies
  };
}

function fixedRepositoryAuthority(admission) {
  const evidence = admission && admission.details && admission.details.repositoryEvidence;
  return {
    executionPaths: evidence && Array.isArray(evidence.executionPaths) ? [...evidence.executionPaths] : [],
    canonicalSsot: evidence && isPlainObject(evidence.canonicalSsot)
      ? { path: evidence.canonicalSsot.path }
      : null
  };
}

function resolvePinnedReviewer(projectRoot, reviewerTransport) {
  const trustedReviewer = resolveHostReviewerTransport(reviewerTransport, projectRoot);
  if (trustedReviewer.error || !projectRoot) {
    return { error: trustedReviewer.error || 'The project root is unavailable.', reviewer: null };
  }
  let configuration;
  try {
    const packageValue = JSON.parse(fs.readFileSync(path.join(projectRoot, 'package.json'), 'utf8'));
    configuration = packageValue && packageValue.nodePolicyChecker && packageValue.nodePolicyChecker.semanticReviewer;
  } catch (error) {
    return { error: `The repository reviewer policy could not be read: ${error.message}`, reviewer: null };
  }
  if (!isPlainObject(configuration) || Object.hasOwn(configuration, 'publicKey') ||
    configuration.id !== trustedReviewer.reviewer.id ||
    !nonEmptyText(configuration.model) || configuration.model !== trustedReviewer.reviewer.model) {
    return { error: 'The target repository must explicitly pin the trusted host reviewer identity and exact model, not a trust key.', reviewer: null };
  }
  return trustedReviewer;
}

function fixedThresholdValues(baseline) {
  const observed = baseline && baseline.details && baseline.details.thresholds;
  return Object.fromEntries(THRESHOLD_NAMES.map((name) => [
    name,
    observed && observed[name] && Number.isSafeInteger(observed[name].effective)
      ? observed[name].effective
      : DEFAULT_THRESHOLDS[name]
  ]));
}

function collectBaselineMechanicalViolations(baseline) {
  if (!baseline || !Array.isArray(baseline.checks)) {
    return [];
  }
  return baseline.checks.flatMap((check) => {
    if (check.verdict !== 'FAIL' || !Array.isArray(check.evidence)) {
      return [];
    }
    return check.evidence.flatMap((evidence) => {
      if (!evidence || typeof evidence.path !== 'string') {
        return [];
      }
      return [{
        checkId: check.id,
        path: evidence.path,
        ...(Number.isSafeInteger(evidence.line) ? { line: evidence.line } : {}),
        ...(Number.isSafeInteger(evidence.column) ? { column: evidence.column } : {}),
        evidenceDigest: evidenceDigest(check.id, evidence)
      }];
    });
  });
}

function baselineSemanticViolation(checkId, evidence) {
  return {
    checkId,
    path: evidence.path,
    line: evidence.line,
    column: evidence.column,
    evidenceDigest: semanticEvidenceDigest(checkId, evidence)
  };
}

/**
 * Runs the final read-only code and review quality Gate for one fixed change context.
 * The evidence envelope preserves the WP-001 policy, pre-change source state,
 * impact scope, and all required evidence-connected semantic judgments.
 *
 * @param {string} projectDirectory directory to inspect
 * @param {object} options opaque authority supplied only by a WP-001 admission session
 * @returns {object} final quality Gate result
 */
function gateProject(projectDirectory, options = {}) {
  if (typeof projectDirectory !== 'string' || projectDirectory.length === 0) {
    throw new TypeError('gateProject requires a project directory path.');
  }

  const projectRoot = path.resolve(projectDirectory);
  const beforeState = captureSourceState(projectRoot);
  const evidenceState = validateGateEvidence(options, projectRoot);
  const fastOutcome = runFastDiagnosis(projectRoot, evidenceState);
  const impactScopeAssessment = resolveImpactScope(evidenceState, fastOutcome);
  evidenceState.impactScopeAssessment = impactScopeAssessment;
  const mechanicalChecks = collectMechanicalChecks(fastOutcome, evidenceState);
  const semanticAssessment = collectSemanticChecks(evidenceState, beforeState);
  const afterState = captureSourceState(projectRoot);
  const sourceReadback = createSourceReadback(beforeState, afterState);
  const fullProjectAuthorization = recheckFullProjectAuthorization(evidenceState);
  if (fullProjectAuthorization.verdict !== 'PASS') {
    evidenceState.errors.push(...fullProjectAuthorization.evidence);
    evidenceState.valid = false;
  }
  const bindingEvidence = [...evidenceState.errors, ...impactScopeAssessment.evidence];
  const bindingCheck = evidenceState.valid && impactScopeAssessment.verdict === 'PASS'
    ? gateCheck('wp001-binding', 'PASS', 'Fixed WP-001 policy, pre-change state, and impact scope are complete and bound to this project.')
    : gateCheck('wp001-binding', 'INCONCLUSIVE', 'The fixed WP-001 policy, pre-change state, or dependency impact scope is incomplete.', bindingEvidence);
  const stabilityCheck = sourceReadback.unchanged
    ? gateCheck('target-source-stability', 'PASS', 'Target source bytes were identical before and after the final Gate.', [sourceStateEvidence(beforeState)])
    : gateCheck(
      'target-source-stability',
      'INCONCLUSIVE',
      'Target source bytes could not be confirmed identical before and after the final Gate.',
      [sourceStateEvidence(beforeState), sourceStateEvidence(afterState)]
    );
  const semanticInputCheck = semanticAssessment.unknown.length === 0
    ? gateCheck('semantic-input', 'PASS', 'No unrecognized semantic judgment was supplied.')
    : gateCheck(
      'semantic-input',
      'INCONCLUSIVE',
      'Unrecognized semantic judgments cannot be safely mapped to a required final-Gate obligation.',
      semanticAssessment.unknown
    );
  const baselineImpactCheck = assessBaselineImpact(evidenceState);
  const categories = CATEGORY_DEFINITIONS.map((definition) => createCategory(
    definition,
    bindingCheck,
    mechanicalChecks,
    semanticAssessment.checks
  ));
  const finalChecks = [bindingCheck, stabilityCheck, semanticInputCheck, fullProjectAuthorization, baselineImpactCheck];
  const verdict = aggregateVerdict([...categories, ...finalChecks]);
  const completionApproval = verdict === 'PASS';
  const counts = countVerdicts(categories);
  const mainFindings = collectMainFindings(categories, finalChecks);
  const finalCompletion = {
    approved: completionApproval,
    status: completionApproval ? 'APPROVED' : 'BLOCKED',
    reason: completionApproval
      ? 'Every required mechanical and semantic final-Gate obligation passed.'
      : 'A required mechanical check, semantic judgment, fixed-evidence binding, or source readback did not pass.'
  };
  const summary = {
    verdict,
    completionApproval,
    categoryCounts: counts,
    mainFindings
  };

  const result = {
    kind: 'final-code-and-review-quality-gate',
    scope: 'all-b-1-through-b-3-c-1-through-c-5-d-1-through-d-3',
    completionApproval,
    finalCompletion,
    verdict,
    categories,
    summary,
    details: {
      kind: 'final-code-and-review-quality-gate',
      scope: 'all-b-1-through-b-3-c-1-through-c-5-d-1-through-d-3',
      projectRoot,
      verdict,
      completionApproval,
      finalCompletion,
      categoryCounts: counts,
      mainFindings,
      binding: describeBinding(evidenceState),
      evidenceContract: EVIDENCE_CONTRACT,
      evidenceErrors: evidenceState.errors,
      categories,
      mechanical: describeMechanical(fastOutcome, mechanicalChecks),
      semantic: {
        required: SEMANTIC_REQUIREMENTS,
        checks: [...semanticAssessment.checks.values()],
        unrecognized: semanticAssessment.unknown
      },
      preExisting: describePreExisting(evidenceState),
      finalChecks,
      sourceReadback
    }
  };
  const projectionState = { cyclic: false, hostile: false };
  const projected = deepCopy(result, new WeakMap(), new WeakSet(), projectionState);
  if (projectionState.cyclic || projectionState.hostile) {
    const projectionCheck = gateCheck(
      'result-projection',
      'INCONCLUSIVE',
      'The final Gate result contained cyclic or unreadable internal evidence and could not be safely projected.',
      [capabilityEvidence('result-projection', projectionState.cyclic ? 'Cyclic result evidence was rejected.' : 'Result evidence could not be read safely.')]
    );
    const finalChecksWithProjection = Array.isArray(projected.details && projected.details.finalChecks)
      ? [...projected.details.finalChecks, projectionCheck]
      : [projectionCheck];
    const mainFinding = { id: projectionCheck.id, verdict: projectionCheck.verdict, message: projectionCheck.message };
    const mainFindings = [
      ...(projected.summary && Array.isArray(projected.summary.mainFindings) ? projected.summary.mainFindings : []),
      mainFinding
    ].slice(0, 5);
    const blockedCompletion = {
      approved: false,
      status: 'BLOCKED',
      reason: 'The final Gate result could not be safely projected because internal evidence was cyclic or unreadable.'
    };
    projected.verdict = 'INCONCLUSIVE';
    projected.completionApproval = false;
    projected.finalCompletion = blockedCompletion;
    projected.summary = {
      ...(projected.summary || {}),
      mainFindings,
      verdict: 'INCONCLUSIVE'
    };
    if (projected.details) {
      projected.details.verdict = 'INCONCLUSIVE';
      projected.details.completionApproval = false;
      projected.details.finalCompletion = blockedCompletion;
      projected.details.finalChecks = finalChecksWithProjection;
      projected.details.evidenceErrors = [
        ...(Array.isArray(projected.details.evidenceErrors) ? projected.details.evidenceErrors : []),
        ...projectionCheck.evidence
      ];
      projected.details.mainFindings = mainFindings;
    }
  }
  return projected;
}

function assessBaselineImpact(evidenceState) {
  const violations = evidenceState.preChange && Array.isArray(evidenceState.preChange.violations)
    ? evidenceState.preChange.violations.filter((violation, index) => {
      return impactScopeContains(evidenceState, violation.path) && evidenceState.observedBaselineViolations.has(index);
    })
    : [];
  if (violations.length === 0) {
    return gateCheck(
      'baseline-impact',
      'PASS',
      'No authentic pre-change mechanical or semantic violation inside the fixed impact scope remains present in current evidence.'
    );
  }
  return gateCheck(
    'baseline-impact',
    'FAIL',
    'An authentic pre-change mechanical or semantic violation inside the fixed impact scope remains present in current evidence.',
    violations.map((violation) => ({ kind: 'pre-existing-impact', ...violation }))
  );
}

function recheckFullProjectAuthorization(evidenceState) {
  const authority = evidenceState.authority;
  if (!authority || typeof authority.currentSourceAuthorized !== 'function') {
    return gateCheck(
      'full-project-authorization',
      'INCONCLUSIVE',
      'The admission session cannot confirm the full project after semantic review.',
      [capabilityEvidence('authority.currentSource', 'No genuine admission authorization capability is available.')]
    );
  }
  try {
    if (authority.currentSourceAuthorized()) {
      return gateCheck(
        'full-project-authorization',
        'PASS',
        'The full project remains the state authorized by the admission session after all reviewer calls.'
      );
    }
    return gateCheck(
      'full-project-authorization',
      'INCONCLUSIVE',
      'The full project changed during the final Gate or differs from the admission-authorized state.',
      [inputEvidence('authority.currentSource', 'Full-project authorization failed after semantic review.')]
    );
  } catch (error) {
    return gateCheck(
      'full-project-authorization',
      'INCONCLUSIVE',
      'The full project could not be re-authorized after semantic review.',
      [inputEvidence('authority.currentSource', `Full-project authorization failed: ${error.message}`)]
    );
  }
}

function runFastDiagnosis(projectRoot, evidenceState) {
  try {
    return {
      error: null,
      result: diagnoseFastProject(projectRoot, {
        boundaryEvidence: evidenceState.policy ? evidenceState.policy.boundaryEvidence : undefined,
        fixedThresholds: evidenceState.policy ? evidenceState.policy.thresholds : undefined
      })
    };
  } catch (error) {
    return { error, result: null };
  }
}

function collectMechanicalChecks(fastOutcome, evidenceState) {
  const byId = new Map();
  const observed = fastOutcome.result && Array.isArray(fastOutcome.result.checks)
    ? new Map(fastOutcome.result.checks.map((item) => [item.id, item]))
    : new Map();

  for (const id of FAST_CHECK_IDS) {
    const raw = observed.get(id);
    if (!raw) {
      byId.set(id, gateCheck(
        id,
        'INCONCLUSIVE',
        fastOutcome.error
          ? `The required mechanical check could not run: ${fastOutcome.error.message}`
          : 'The required mechanical check was not reported by the fast diagnosis.',
        fastOutcome.error ? [capabilityEvidence('diagnoseFastProject', fastOutcome.error.message)] : []
      ));
      continue;
    }
    byId.set(id, scopeMechanicalCheck(raw, id, evidenceState));
  }
  return byId;
}

function scopeMechanicalCheck(raw, checkId, evidenceState) {
  if (raw.verdict !== 'FAIL' || !evidenceState.valid || !Array.isArray(raw.evidence) || raw.evidence.length === 0) {
    return { ...raw };
  }

  const blockingEvidence = [];
  const unrelatedPreExisting = [];
  for (const item of raw.evidence) {
    const match = matchBaselineViolation(evidenceState, checkId, item);
    if (match && !impactScopeContains(evidenceState, item.path)) {
      unrelatedPreExisting.push({ baseline: match.violation, evidence: item });
      observeBaselineViolation(evidenceState, checkId, item);
    } else {
      blockingEvidence.push(item);
      if (match) {
        observeBaselineViolation(evidenceState, checkId, item);
      }
    }
  }

  if (blockingEvidence.length === 0 && unrelatedPreExisting.length > 0) {
    return {
      ...raw,
      rawVerdict: raw.verdict,
      verdict: 'PASS',
      message: 'Observed failures are documented pre-existing violations outside the fixed impact scope.',
      evidence: [],
      unrelatedPreExisting
    };
  }
  return unrelatedPreExisting.length === 0
    ? { ...raw }
    : { ...raw, evidence: blockingEvidence, unrelatedPreExisting };
}

function collectSemanticChecks(evidenceState, currentState) {
  if (!evidenceState.valid || evidenceState.impactScopeAssessment.verdict !== 'PASS') {
    const checks = new Map(SEMANTIC_REQUIREMENTS.map((requirement) => [
      requirement.id,
      gateCheck(
        requirement.id,
        'INCONCLUSIVE',
        'This semantic obligation cannot run without current authoritative WP-001 session evidence.',
        [...evidenceState.errors, ...evidenceState.impactScopeAssessment.evidence],
        { category: requirement.category, label: requirement.label }
      )
    ]));
    return { checks, unknown: [] };
  }
  return collectReviewerJudgments(
    evidenceState.authority,
    'final',
    currentState,
    evidenceState.impactScopeAssessment.effectivePaths,
    false,
    evidenceState
  );
}

function collectReviewerJudgments(authority, phase, sourceState, impactPaths, allowOutsideScope, evidenceState = null) {
  const checks = new Map();
  const reviewer = authority && authority.reviewer;
  if (!validReviewer(reviewer)) {
    for (const requirement of SEMANTIC_REQUIREMENTS) {
      checks.set(requirement.id, gateCheck(
        requirement.id,
        'INCONCLUSIVE',
        'The required AI semantic reviewer capability is unavailable.',
        [capabilityEvidence('semantic-reviewer', authority && authority.reviewerProblem
          ? authority.reviewerProblem
          : 'No fixed AI semantic reviewer was present in the WP-001 session.')],
        { category: requirement.category, label: requirement.label }
      ));
    }
    return { checks, unknown: [] };
  }

  const sourceCache = new Map();
  for (const requirement of SEMANTIC_REQUIREMENTS) {
    const reviewed = invokeReviewer(authority, reviewer, requirement, phase, sourceState, impactPaths);
    if (reviewed.error) {
      checks.set(requirement.id, gateCheck(
        requirement.id,
        'INCONCLUSIVE',
        'The required AI semantic judgment could not be executed or attested.',
        [reviewed.error],
        { category: requirement.category, label: requirement.label }
      ));
      continue;
    }
    const inspected = inspectSemanticJudgment(
      reviewed.judgment,
      requirement,
      authority,
      reviewed.request,
      sourceCache,
      allowOutsideScope,
      evidenceState
    );
    if (inspected.errors.length > 0) {
      checks.set(requirement.id, gateCheck(
        requirement.id,
        'INCONCLUSIVE',
        'The executed AI semantic judgment has invalid evidence or attestation.',
        inspected.errors,
        { category: requirement.category, label: requirement.label }
      ));
      continue;
    }
    const judgment = reviewed.judgment;
    if (evidenceState && phase === 'final') {
      for (const evidence of judgment.evidence) {
        observeBaselineViolation(evidenceState, requirement.id, evidence);
      }
    }
    const result = gateCheck(
      requirement.id,
      judgment.verdict,
      semanticMessage(requirement, judgment.verdict),
      judgment.evidence,
      {
        category: requirement.category,
        label: requirement.label,
        reviewer: authority.reviewerIdentity,
        attestation: judgment.attestation
      }
    );
    checks.set(requirement.id, judgment.verdict === 'FAIL' && evidenceState
      ? scopeSemanticCheck(result, requirement.id, evidenceState)
      : result);
  }
  return { checks, unknown: [] };
}

function invokeReviewer(authority, reviewer, requirement, phase, sourceState, impactPaths) {
  const request = {
    kind: 'ai-semantic-review-request',
    phase,
    projectRoot: authority.projectRoot,
    requirement: {
      id: requirement.id,
      category: requirement.category,
      label: requirement.label
    },
    binding: {
      sessionId: authority.sessionId,
      policyId: authority.policy.id,
      preChangeId: authority.preChange.id,
      impactScopeId: authority.impactScope.id
    },
    sourceDigest: sourceState && sourceState.digest ? sourceState.digest : null,
    impactPaths: Array.isArray(impactPaths) ? [...impactPaths] : []
  };
  request.requestDigest = digestValue(request);
  try {
    const judgment = reviewer.review(Object.freeze(request));
    if (judgment && typeof judgment.then === 'function') {
      return { error: capabilityEvidence(requirement.id, 'Asynchronous reviewer results are unsupported by the synchronous final Gate.') };
    }
    if (!isPlainObject(judgment)) {
      return { error: capabilityEvidence(requirement.id, 'The AI reviewer returned no structured judgment.') };
    }
    return { judgment, request };
  } catch (error) {
    return { error: capabilityEvidence(requirement.id, normalizeThrownReviewerValue(error)) };
  }
}

function inspectSemanticJudgment(judgment, requirement, authority, request, sourceCache, allowOutsideScope, evidenceState) {
  const errors = [];
  if (judgment.id !== requirement.id) {
    errors.push(inputEvidence(requirement.id, 'AI judgment ID does not match the executed requirement.'));
  }
  if (judgment.category !== requirement.category) {
    errors.push(inputEvidence(requirement.id, 'Semantic judgment category does not match its required obligation.'));
  }
  if (!['PASS', 'FAIL', 'INCONCLUSIVE'].includes(judgment.verdict)) {
    errors.push(inputEvidence(requirement.id, 'Semantic judgment verdict must be PASS, FAIL, or INCONCLUSIVE.'));
  }
  if (judgment.rule !== requirement.id) {
    errors.push(inputEvidence(requirement.id, 'Semantic judgment must identify the exact executed rule ID.'));
  }
  if (!validAttestation(judgment, authority, request)) {
    errors.push(inputEvidence(requirement.id, 'Semantic judgment attestation does not match the invoked reviewer, request, and current source digest.'));
  }
  if (!Array.isArray(judgment.evidence) || judgment.evidence.length === 0) {
    errors.push(inputEvidence(requirement.id, 'Semantic judgment must include target source evidence.'));
  } else {
    for (const location of judgment.evidence) {
      const error = validateSourceLocation(location, authority.projectRoot, sourceCache);
      if (error) {
        errors.push(inputEvidence(requirement.id, error));
      } else if (!allowOutsideScope && evidenceState && !impactScopeContains(evidenceState, location.path) && !(judgment.verdict === 'FAIL' && matchBaselineViolation(evidenceState, requirement.id, location))) {
        errors.push(inputEvidence(requirement.id, 'Semantic evidence is outside the fixed changed-module and dependency impact scope.'));
      }
    }
  }
  if (judgment.verdict === 'FAIL' && !nonEmptyText(judgment.falsifier)) {
    errors.push(inputEvidence(requirement.id, 'AI FAIL requires a falsifier or counterevidence condition.'));
  }
  return { errors };
}

function scopeSemanticCheck(raw, checkId, evidenceState) {
  const blockingEvidence = [];
  const unrelatedPreExisting = [];
  for (const item of raw.evidence) {
    const match = matchBaselineViolation(evidenceState, checkId, item);
    if (match && !impactScopeContains(evidenceState, item.path)) {
      unrelatedPreExisting.push({ baseline: match.violation, evidence: item });
      observeBaselineViolation(evidenceState, checkId, item);
    } else {
      blockingEvidence.push(item);
      if (match) {
        observeBaselineViolation(evidenceState, checkId, item);
      }
    }
  }
  if (blockingEvidence.length === 0 && unrelatedPreExisting.length > 0) {
    return {
      ...raw,
      rawVerdict: raw.verdict,
      verdict: 'PASS',
      message: 'Semantic failures are documented pre-existing violations outside the fixed impact scope.',
      evidence: [],
      unrelatedPreExisting
    };
  }
  return unrelatedPreExisting.length === 0
    ? raw
    : { ...raw, evidence: blockingEvidence, unrelatedPreExisting };
}

function observeBaselineViolation(evidenceState, checkId, evidence) {
  const match = matchBaselineViolation(evidenceState, checkId, evidence);
  if (match) {
    evidenceState.observedBaselineViolations.add(match.index);
  }
}

function createCategory(definition, bindingCheck, mechanicalChecks, semanticChecks) {
  const mechanical = definition.mechanical.map((id) => mechanicalChecks.get(id) || gateCheck(
    id,
    'INCONCLUSIVE',
    'The required mechanical check was not available.'
  ));
  const semantic = definition.semantic.map((id) => semanticChecks.get(id) || gateCheck(
    id,
    'INCONCLUSIVE',
    'The required semantic judgment was not available.'
  ));
  const checks = [bindingCheck, ...mechanical, ...semantic];
  return {
    id: definition.id,
    label: definition.label,
    verdict: aggregateVerdict(checks),
    binding: bindingCheck,
    mechanical,
    semantic
  };
}

function validateGateEvidence(value, projectRoot) {
  const errors = [];
  const state = {
    authority: null,
    errors,
    impactScope: null,
    observedBaselineViolations: new Set(),
    policy: null,
    preChange: null,
    valid: false
  };
  const authority = isPlainObject(value) ? value.authority : null;
  if (!authority || !GATE_AUTHORITIES.has(authority)) {
    errors.push(inputEvidence('authority', 'Final Gate approval requires the opaque authority of the current WP-001 admission session.'));
    return state;
  }
  state.authority = authority;
  errors.push(...authority.errors);
  if (authority.projectRoot !== projectRoot) {
    errors.push(inputEvidence('authority.projectRoot', 'WP-001 authority is bound to a different project root.'));
  }
  try {
    if (!authority.currentSourceAuthorized()) {
      errors.push(inputEvidence('authority.currentSource', 'Current source is not the state last authorized by the WP-001 session.'));
    }
  } catch (error) {
    errors.push(inputEvidence('authority.currentSource', `Current source authorization failed: ${error.message}`));
  }
  state.policy = validatePolicy(authority.policy, projectRoot, errors);
  state.preChange = validatePreChange(authority.preChange, projectRoot, errors);
  state.impactScope = validateImpactScope(authority.impactScope, projectRoot, errors);
  state.valid = errors.length === 0;
  return state;
}

function validatePolicy(value, projectRoot, errors) {
  if (!isPlainObject(value)) {
    errors.push(inputEvidence('policy', 'Fixed WP-001 policy evidence is required.'));
    return null;
  }
  requireKind(value, 'fixed-wp001-policy', 'policy', errors);
  requireId(value, 'policy', errors);
  requireSource(value, 'policy', errors);
  requireProjectRoot(value, projectRoot, 'policy', errors);
  validateBoundaryEvidence(value.boundaryEvidence, projectRoot, errors);
  validateRepositoryAuthority(value.repositoryAuthority, projectRoot, 'policy.repositoryAuthority', errors);
  validateThresholds(value.thresholds, 'policy.thresholds', errors);
  return value;
}

function validatePreChange(value, projectRoot, errors) {
  if (!isPlainObject(value)) {
    errors.push(inputEvidence('preChange', 'Fixed pre-change source-state evidence is required.'));
    return null;
  }
  requireKind(value, 'fixed-pre-change-source-state', 'preChange', errors);
  requireId(value, 'preChange', errors);
  requireSource(value, 'preChange', errors);
  requireProjectRoot(value, projectRoot, 'preChange', errors);
  if (!isPlainObject(value.sourceReadback) || !validDigest(value.sourceReadback.digest) || !validFileCount(value.sourceReadback.fileCount)) {
    errors.push(inputEvidence('preChange.sourceReadback', 'Pre-change source readback requires a SHA-256 digest and non-negative file count.'));
  }
  if (!Array.isArray(value.violations)) {
    errors.push(inputEvidence('preChange.violations', 'Pre-change evidence must provide an explicit violation list, including an empty list when none were observed.'));
  } else {
    value.violations.forEach((violation, index) => validateBaselineViolation(violation, index, errors));
  }
  return value;
}

function validateImpactScope(value, projectRoot, errors) {
  if (!isPlainObject(value)) {
    errors.push(inputEvidence('impactScope', 'Fixed changed-module and dependency impact scope is required.'));
    return null;
  }
  requireKind(value, 'fixed-impact-scope', 'impactScope', errors);
  requireId(value, 'impactScope', errors);
  requireSource(value, 'impactScope', errors);
  requireProjectRoot(value, projectRoot, 'impactScope', errors);
  if (!Array.isArray(value.entries) || value.entries.length === 0) {
    errors.push(inputEvidence('impactScope.entries', 'Impact scope must contain one or more fixed exact or subtree paths.'));
    return value;
  }
  value.entries.forEach((entry, index) => {
    if (!isPlainObject(entry) || !['exact', 'subtree'].includes(entry.mode) || !safeRelativePath(entry.path, true)) {
      errors.push(inputEvidence(`impactScope.entries[${index}]`, 'Each impact-scope entry requires mode exact or subtree and a safe relative path.'));
    }
  });
  if (!Array.isArray(value.fixedPaths) || value.fixedPaths.some((filePath) => !safeRelativePath(filePath, false))) {
    errors.push(inputEvidence('impactScope.fixedPaths', 'WP-001 authority must retain its exact pre-change dependency closure.'));
  }
  return value;
}

function validateBoundaryEvidence(value, projectRoot, errors) {
  if (!isPlainObject(value)) {
    errors.push(inputEvidence('policy.boundaryEvidence', 'Fixed observed-boundary evidence is required.'));
    return;
  }
  if (value.kind !== 'fixed-observed-boundaries') {
    errors.push(inputEvidence('policy.boundaryEvidence.kind', 'Boundary evidence must use kind fixed-observed-boundaries.'));
  }
  if (!nonEmptyText(value.source)) {
    errors.push(inputEvidence('policy.boundaryEvidence.source', 'Boundary evidence must identify its fixed observed source.'));
  }
  if (typeof value.projectRoot !== 'string' || path.resolve(value.projectRoot) !== projectRoot) {
    errors.push(inputEvidence('policy.boundaryEvidence.projectRoot', 'Boundary evidence must be bound to this project root.'));
  }
  if (!Array.isArray(value.allowedDependencies)) {
    errors.push(inputEvidence('policy.boundaryEvidence.allowedDependencies', 'Boundary evidence must provide allowed dependencies.'));
    return;
  }
  value.allowedDependencies.forEach((item, index) => {
    if (!isPlainObject(item) || !safeBoundaryPath(item.from) || !safeBoundaryPath(item.to)) {
      errors.push(inputEvidence(`policy.boundaryEvidence.allowedDependencies[${index}]`, 'Each allowed dependency requires safe relative from and to boundary paths.'));
    }
  });
}

function validateRepositoryAuthority(value, projectRoot, name, errors) {
  if (!isPlainObject(value)) {
    errors.push(inputEvidence(name, 'Fixed repository authority is required.'));
    return;
  }
  if (!Array.isArray(value.executionPaths) || value.executionPaths.length === 0 || value.executionPaths.some((item) => !safeRelativePath(item, false))) {
    errors.push(inputEvidence(`${name}.executionPaths`, 'Repository authority requires observed safe execution paths.'));
  } else {
    for (const executionPath of value.executionPaths) {
      if (!isReadableTargetFile(projectRoot, executionPath)) {
        errors.push(inputEvidence(`${name}.executionPaths`, 'A fixed execution path is no longer an observed regular target file.'));
        break;
      }
    }
  }
  if (!isPlainObject(value.canonicalSsot) || !safeRelativePath(value.canonicalSsot.path, false)) {
    errors.push(inputEvidence(`${name}.canonicalSsot`, 'Repository authority requires one canonical source-of-truth path.'));
  } else if (!isReadableTargetFile(projectRoot, value.canonicalSsot.path)) {
    errors.push(inputEvidence(`${name}.canonicalSsot`, 'The fixed canonical source-of-truth path is no longer an observed regular target file.'));
  }
}

function validateThresholds(value, name, errors) {
  if (!isPlainObject(value)) {
    errors.push(inputEvidence(name, 'Fixed safety thresholds are required.'));
    return;
  }
  for (const key of Object.keys(value)) {
    if (!THRESHOLD_NAMES.includes(key)) {
      errors.push(inputEvidence(`${name}.${key}`, 'Unknown fixed threshold.'));
    }
  }
  for (const key of THRESHOLD_NAMES) {
    if (!Number.isSafeInteger(value[key]) || value[key] <= 0) {
      errors.push(inputEvidence(`${name}.${key}`, 'Each fixed threshold must be a positive integer.'));
    }
  }
}

function validateBaselineViolation(value, index, errors) {
  const name = `preChange.violations[${index}]`;
  if (!isPlainObject(value) || !KNOWN_BASELINE_CHECK_IDS.has(value.checkId) || !safeRelativePath(value.path, false) || !validDigest(value.evidenceDigest)) {
    errors.push(inputEvidence(name, 'Each pre-change violation requires a known check ID, safe source path, and exact evidence digest.'));
    return;
  }
  if (value.line !== undefined && (!Number.isSafeInteger(value.line) || value.line < 1)) {
    errors.push(inputEvidence(`${name}.line`, 'Pre-change violation line must be a positive integer when supplied.'));
  }
  if (value.column !== undefined && (!Number.isSafeInteger(value.column) || value.column < 1)) {
    errors.push(inputEvidence(`${name}.column`, 'Pre-change violation column must be a positive integer when supplied.'));
  }
}

function requireKind(value, expected, name, errors) {
  if (value.kind !== expected) {
    errors.push(inputEvidence(`${name}.kind`, `Expected ${expected}.`));
  }
}

function requireId(value, name, errors) {
  if (!nonEmptyText(value.id)) {
    errors.push(inputEvidence(`${name}.id`, 'A stable fixed-evidence ID is required.'));
  }
}

function requireSource(value, name, errors) {
  if (!nonEmptyText(value.source)) {
    errors.push(inputEvidence(`${name}.source`, 'A fixed-evidence source description is required.'));
  }
}

function requireProjectRoot(value, projectRoot, name, errors) {
  if (typeof value.projectRoot !== 'string' || path.resolve(value.projectRoot) !== projectRoot) {
    errors.push(inputEvidence(`${name}.projectRoot`, 'Evidence must be bound to the target project root.'));
  }
}

function matchBaselineViolation(evidenceState, checkId, evidence) {
  if (!evidenceState.preChange || !Array.isArray(evidenceState.preChange.violations) || !evidence || typeof evidence.path !== 'string') {
    return null;
  }
  const index = evidenceState.preChange.violations.findIndex((violation) => {
    return violation.checkId === checkId &&
      violation.path === evidence.path &&
      violation.line === evidence.line &&
      violation.column === evidence.column &&
      violation.evidenceDigest === (SEMANTIC_REQUIREMENT_BY_ID.has(checkId)
        ? semanticEvidenceDigest(checkId, evidence)
        : evidenceDigest(checkId, evidence));
  });
  return index === -1 ? null : { index, violation: evidenceState.preChange.violations[index] };
}

function resolveImpactScope(evidenceState, fastOutcome) {
  if (!evidenceState.valid) {
    return { effectivePaths: [], evidence: [], verdict: 'INCONCLUSIVE' };
  }
  const graph = fastOutcome.result && fastOutcome.result.details && fastOutcome.result.details.dependencyGraph;
  if (!graph || !Array.isArray(graph.files) || !Array.isArray(graph.edges) || !Array.isArray(graph.unknown)) {
    return {
      effectivePaths: [],
      evidence: [capabilityEvidence('dependency-impact-scope', 'The mechanical dependency graph was unavailable.')],
      verdict: 'INCONCLUSIVE'
    };
  }
  if (graph.unknown.length > 0) {
    return {
      effectivePaths: [],
      evidence: graph.unknown.map((item) => ({
        kind: 'import',
        path: item.path,
        line: item.line,
        column: item.column,
        error: item.message
      })),
      verdict: 'INCONCLUSIVE'
    };
  }

  const fixedPaths = Array.isArray(evidenceState.impactScope.fixedPaths)
    ? evidenceState.impactScope.fixedPaths
    : [];
  const effectivePaths = dependencyClosure(graph, evidenceState.impactScope.entries, fixedPaths);
  return { effectivePaths, evidence: [], verdict: 'PASS' };
}

function dependencyClosure(graph, entries, retainedPaths) {
  if (!graph || !Array.isArray(graph.files) || !Array.isArray(graph.edges)) {
    return [];
  }
  const adjacent = new Map(graph.files.map((file) => [file, new Set()]));
  for (const edge of graph.edges) {
    if (adjacent.has(edge.from) && adjacent.has(edge.to)) {
      adjacent.get(edge.from).add(edge.to);
      adjacent.get(edge.to).add(edge.from);
    }
  }
  const effective = new Set(Array.isArray(retainedPaths) ? retainedPaths : []);
  for (const file of graph.files) {
    if (scopeContains(entries, file)) {
      effective.add(file);
    }
  }
  const queue = [...effective].filter((file) => adjacent.has(file));
  while (queue.length > 0) {
    const current = queue.shift();
    for (const related of adjacent.get(current) || []) {
      if (!effective.has(related)) {
        effective.add(related);
        queue.push(related);
      }
    }
  }
  return [...effective].sort();
}

function impactScopeContains(evidenceState, filePath) {
  return Boolean(
    evidenceState.impactScope &&
    (scopeContains(evidenceState.impactScope.entries, filePath) ||
      (evidenceState.impactScopeAssessment && evidenceState.impactScopeAssessment.effectivePaths.includes(filePath)))
  );
}

function scopeContains(entries, filePath) {
  if (!Array.isArray(entries) || typeof filePath !== 'string') {
    return false;
  }
  return entries.some((entry) => {
    if (!isPlainObject(entry) || typeof entry.path !== 'string') {
      return false;
    }
    if (entry.path === '.') {
      return true;
    }
    return entry.mode === 'exact'
      ? entry.path === filePath
      : filePath === entry.path || filePath.startsWith(`${entry.path}/`);
  });
}

function validateSourceLocation(value, projectRoot, cache) {
  if (!isPlainObject(value) || !safeRelativePath(value.path, false) || !Number.isSafeInteger(value.line) || value.line < 1 || !Number.isSafeInteger(value.column) || value.column < 1) {
    return 'Semantic evidence requires an exact safe source path, positive line, and positive column.';
  }
  let lines = cache.get(value.path);
  if (!lines) {
    const absolutePath = path.resolve(projectRoot, ...value.path.split('/'));
    if (!isWithin(projectRoot, absolutePath)) {
      return 'Semantic evidence path leaves the target project.';
    }
    try {
      if (!fs.lstatSync(absolutePath).isFile()) {
        return 'Semantic evidence must identify a regular target source file.';
      }
      lines = fs.readFileSync(absolutePath, 'utf8').split(/\r\n|\r|\n/);
      cache.set(value.path, lines);
    } catch (error) {
      return `Semantic evidence source could not be read: ${error.message}`;
    }
  }
  if (value.line > lines.length || value.column > lines[value.line - 1].length + 1) {
    return 'Semantic evidence location does not exist in the current target source.';
  }
  return null;
}

function isReadableTargetFile(projectRoot, relativePath) {
  try {
    const absolutePath = path.resolve(projectRoot, ...relativePath.split('/'));
    return isWithin(projectRoot, absolutePath) && fs.lstatSync(absolutePath).isFile();
  } catch (error) {
    return false;
  }
}

function createSourceReadback(before, after) {
  return {
    before: sourceStateEvidence(before),
    after: sourceStateEvidence(after),
    unchanged: Boolean(before.digest && after.digest && before.digest === after.digest)
  };
}

function describeBinding(evidenceState) {
  return {
    sessionId: evidenceState.authority ? evidenceState.authority.sessionId : null,
    reviewer: evidenceState.authority ? evidenceState.authority.reviewerIdentity : null,
    baselineCompleteness: evidenceState.authority ? evidenceState.authority.baselineCompleteness : null,
    policy: evidenceState.policy ? {
      id: evidenceState.policy.id,
      kind: evidenceState.policy.kind,
      source: evidenceState.policy.source,
      repositoryAuthority: evidenceState.policy.repositoryAuthority,
      thresholds: evidenceState.policy.thresholds
    } : null,
    preChange: evidenceState.preChange ? {
      id: evidenceState.preChange.id,
      kind: evidenceState.preChange.kind,
      source: evidenceState.preChange.source,
      sourceReadback: evidenceState.preChange.sourceReadback
    } : null,
    impactScope: evidenceState.impactScope ? {
      id: evidenceState.impactScope.id,
      kind: evidenceState.impactScope.kind,
      source: evidenceState.impactScope.source,
      entries: evidenceState.impactScope.entries,
      fixedPaths: evidenceState.impactScope.fixedPaths,
      effectivePaths: evidenceState.impactScopeAssessment ? evidenceState.impactScopeAssessment.effectivePaths : [],
      verdict: evidenceState.impactScopeAssessment ? evidenceState.impactScopeAssessment.verdict : 'INCONCLUSIVE'
    } : null
  };
}

function describeMechanical(fastOutcome, mechanicalChecks) {
  return {
    kind: fastOutcome.result ? fastOutcome.result.kind : null,
    fastVerdict: fastOutcome.result ? fastOutcome.result.verdict : 'INCONCLUSIVE',
    completionApproval: false,
    checks: [...mechanicalChecks.values()],
    thresholds: fastOutcome.result && fastOutcome.result.details ? fastOutcome.result.details.thresholds : null,
    thresholdConfiguration: fastOutcome.result && fastOutcome.result.details ? fastOutcome.result.details.thresholdConfiguration : null,
    sourceReadback: fastOutcome.result && fastOutcome.result.details ? fastOutcome.result.details.sourceReadback : null,
    error: fastOutcome.error ? fastOutcome.error.message : null
  };
}

function describePreExisting(evidenceState) {
  const violations = evidenceState.preChange && Array.isArray(evidenceState.preChange.violations)
    ? evidenceState.preChange.violations.filter((violation) => {
      return isPlainObject(violation) && typeof violation.path === 'string' && typeof violation.checkId === 'string';
    })
    : [];
  const partition = (belongsToScope) => violations.flatMap((violation, index) => {
    return impactScopeContains(evidenceState, violation.path) === belongsToScope
      ? [{ ...violation, observedNow: evidenceState.observedBaselineViolations.has(index) }]
      : [];
  });
  return {
    impacted: partition(true),
    unrelated: partition(false)
  };
}

function semanticMessage(requirement, verdict) {
  if (verdict === 'PASS') {
    return `${requirement.label} passed its evidence-connected semantic judgment.`;
  }
  if (verdict === 'FAIL') {
    return `${requirement.label} failed its evidence-connected semantic judgment.`;
  }
  return `${requirement.label} could not be determined by its semantic judgment.`;
}

function collectMainFindings(categories, finalChecks) {
  const findings = [];
  for (const category of categories) {
    if (category.verdict === 'PASS') {
      continue;
    }
    const failed = [...category.mechanical, ...category.semantic].find((item) => item.verdict !== 'PASS');
    findings.push({
      id: category.id,
      verdict: category.verdict,
      message: failed ? failed.message : `Category ${category.id} did not pass.`
    });
  }
  for (const item of finalChecks) {
    if (item.verdict !== 'PASS') {
      findings.push({ id: item.id, verdict: item.verdict, message: item.message });
    }
  }
  return findings.slice(0, 5);
}

function countVerdicts(items) {
  const counts = { FAIL: 0, INCONCLUSIVE: 0, PASS: 0 };
  for (const item of items) {
    counts[item.verdict] += 1;
  }
  return counts;
}

function aggregateVerdict(items) {
  if (items.some((item) => item.verdict === 'FAIL')) {
    return 'FAIL';
  }
  if (items.some((item) => item.verdict === 'INCONCLUSIVE')) {
    return 'INCONCLUSIVE';
  }
  return 'PASS';
}

function gateCheck(id, verdict, message, evidence = [], extra = {}) {
  return { id, verdict, message, evidence, ...extra };
}

function sourceStateEvidence(state) {
  return {
    kind: 'source-state',
    digest: state.digest || null,
    fileCount: state.fileCount || 0,
    ...(state.error ? { error: state.error } : {})
  };
}

function capabilityEvidence(pathValue, error) {
  return { kind: 'capability', path: pathValue, error };
}

function inputEvidence(pathValue, error) {
  return { kind: 'input', path: pathValue, error };
}

function safeRelativePath(value, allowRoot) {
  if (value === '.' && allowRoot) {
    return true;
  }
  if (typeof value !== 'string' || value.length === 0 || value.includes('\u0000') || value.includes('\\') || path.posix.isAbsolute(value) || path.win32.isAbsolute(value) || /^[A-Za-z]:/.test(value)) {
    return false;
  }
  return !value.split('/').some((segment) => !segment || segment === '.' || segment === '..');
}

function safeBoundaryPath(value) {
  return value === '.' || safeRelativePath(value, false);
}

function isWithin(projectRoot, candidate) {
  const relative = path.relative(projectRoot, candidate);
  return relative === '' || (!relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative));
}

function validDigest(value) {
  return typeof value === 'string' && /^[a-f0-9]{64}$/i.test(value);
}

function validFileCount(value) {
  return Number.isSafeInteger(value) && value >= 0;
}

function validReviewer(value) {
  return isPlainObject(value) &&
    value.kind === 'ai-semantic-reviewer' &&
    nonEmptyText(value.id) &&
    nonEmptyText(value.model) &&
    value.publicKey && typeof value.publicKey === 'object' &&
    typeof value.review === 'function';
}

function reviewerIdentity(value) {
  return validReviewer(value)
    ? {
      id: value.id,
      kind: value.kind,
      model: value.model,
      publicKeyFingerprint: crypto.createHash('sha256').update(value.publicKey.export({ format: 'der', type: 'spki' })).digest('hex')
    }
    : null;
}

function validAttestation(judgment, authority, request) {
  try {
    const value = judgment && judgment.attestation;
    if (!isPlainRecord(value) || !hasExactDataFields(value, ATTESTATION_FIELDS) || !authority.reviewerIdentity ||
      value.reviewerId !== authority.reviewerIdentity.id ||
      value.model !== authority.reviewerIdentity.model ||
      value.requestDigest !== request.requestDigest ||
      value.sourceDigest !== request.sourceDigest ||
      !nonEmptyText(value.signature)) {
      return false;
    }
    const payload = semanticAttestationPayload(judgment, value);
    return crypto.verify(
      null,
      Buffer.from(canonicalJson(payload)),
      authority.reviewer.publicKey,
      Buffer.from(value.signature, 'base64')
    );
  } catch (error) {
    return false;
  }
}

function hasExactDataFields(value, expectedFields) {
  const keys = Reflect.ownKeys(value);
  if (keys.length !== expectedFields.length || keys.some((key) => typeof key !== 'string' || !expectedFields.includes(key))) {
    return false;
  }
  return keys.every((key) => {
    const descriptor = Object.getOwnPropertyDescriptor(value, key);
    return descriptor && Object.hasOwn(descriptor, 'value');
  });
}

function semanticAttestationPayload(judgment, attestation) {
  return {
    reviewerId: attestation.reviewerId,
    model: attestation.model,
    requestDigest: attestation.requestDigest,
    sourceDigest: attestation.sourceDigest,
    id: judgment.id,
    category: judgment.category,
    verdict: judgment.verdict,
    rule: judgment.rule,
    evidence: judgment.evidence,
    falsifier: judgment.falsifier || null
  };
}

function evidenceDigest(checkId, evidence) {
  return digestValue({ checkId, evidence });
}

function semanticEvidenceDigest(checkId, evidence) {
  return digestValue({
    checkId,
    path: evidence && evidence.path,
    line: evidence && evidence.line,
    column: evidence && evidence.column
  });
}

function digestValue(value) {
  return crypto.createHash('sha256').update(canonicalJson(value)).digest('hex');
}

function canonicalJson(value) {
  if (Array.isArray(value)) {
    return `[${value.map(canonicalJson).join(',')}]`;
  }
  if (isPlainObject(value)) {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

function normalizeThrownReviewerValue(value) {
  if (value === null) {
    return 'The reviewer threw null.';
  }
  if (value === undefined) {
    return 'The reviewer threw undefined.';
  }
  if (typeof value === 'string') {
    return `The reviewer threw a string: ${value}`;
  }
  if (value !== null && (typeof value === 'object' || typeof value === 'function')) {
    try {
      const descriptor = Object.getOwnPropertyDescriptor(value, 'message');
      if (descriptor && Object.hasOwn(descriptor, 'value') && nonEmptyText(descriptor.value)) {
        return descriptor.value;
      }
    } catch (error) {
      return 'The reviewer threw an unreadable object value.';
    }
    return `The reviewer threw a ${typeof value} value.`;
  }
  return `The reviewer threw a ${typeof value} value.`;
}

function nonEmptyText(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function deepCopy(value, seen = new WeakMap(), ancestors = new WeakSet(), state = { cyclic: false, hostile: false }) {
  if (value === null || typeof value !== 'object') {
    return value;
  }

  let isRecord;
  try {
    isRecord = isPlainRecord(value);
  } catch (error) {
    state.hostile = true;
    return null;
  }
  const isArray = Array.isArray(value);
  if (!isArray && !isRecord) {
    return value;
  }
  if (ancestors.has(value)) {
    state.cyclic = true;
    return null;
  }
  if (seen.has(value)) {
    return seen.get(value);
  }

  const copy = isArray ? [] : {};
  seen.set(value, copy);
  ancestors.add(value);
  try {
    if (isArray) {
      for (let index = 0; index < value.length; index += 1) {
        copy.push(deepCopy(value[index], seen, ancestors, state));
      }
    } else {
      for (const [key, item] of Object.entries(value)) {
        copy[key] = deepCopy(item, seen, ancestors, state);
      }
    }
  } catch (error) {
    state.hostile = true;
  } finally {
    ancestors.delete(value);
  }
  return copy;
}

function deepFreeze(value, seen = new WeakSet()) {
  if (!Array.isArray(value) && !isPlainRecord(value)) {
    return value;
  }
  if (seen.has(value)) {
    return value;
  }
  seen.add(value);
  for (const item of Object.values(value)) {
    deepFreeze(item, seen);
  }
  return Object.freeze(value);
}

function isPlainRecord(value) {
  if (value === null || typeof value !== 'object') {
    return false;
  }
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

module.exports = { createGatedAdmissionSession, gateProject };
