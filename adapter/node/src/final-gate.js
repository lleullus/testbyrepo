'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { captureSourceState, diagnoseFastProject } = require('./fast-diagnosis');

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
const EVIDENCE_CONTRACT = Object.freeze({
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
    required: ['id', 'category', 'verdict', 'rule', 'evidence', 'binding'],
    failRequired: ['falsifier'],
    binding: ['policyId', 'preChangeId', 'impactScopeId']
  }
});

/**
 * Runs the final read-only code and review quality Gate for one fixed change context.
 * The evidence envelope preserves the WP-001 policy, pre-change source state,
 * impact scope, and all required evidence-connected semantic judgments.
 *
 * @param {string} projectDirectory directory to inspect
 * @param {object} evidence fixed Gate evidence
 * @returns {object} final quality Gate result
 */
function gateProject(projectDirectory, evidence = {}) {
  if (typeof projectDirectory !== 'string' || projectDirectory.length === 0) {
    throw new TypeError('gateProject requires a project directory path.');
  }

  const projectRoot = path.resolve(projectDirectory);
  const beforeState = captureSourceState(projectRoot);
  const evidenceState = validateGateEvidence(evidence, projectRoot);
  const fastOutcome = runFastDiagnosis(projectRoot, evidenceState);
  const impactScopeAssessment = resolveImpactScope(evidenceState, fastOutcome);
  evidenceState.impactScopeAssessment = impactScopeAssessment;
  const mechanicalChecks = collectMechanicalChecks(fastOutcome, evidenceState);
  const semanticAssessment = collectSemanticChecks(evidence, evidenceState, projectRoot);
  const afterState = captureSourceState(projectRoot);
  const sourceReadback = createSourceReadback(beforeState, afterState);
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
  const categories = CATEGORY_DEFINITIONS.map((definition) => createCategory(
    definition,
    bindingCheck,
    mechanicalChecks,
    semanticAssessment.checks
  ));
  const finalChecks = [bindingCheck, stabilityCheck, semanticInputCheck];
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

  return {
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
      evidenceState.observedBaselineViolations.add(match.index);
    } else {
      blockingEvidence.push(item);
      if (match) {
        evidenceState.observedBaselineViolations.add(match.index);
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

function collectSemanticChecks(evidence, evidenceState, projectRoot) {
  const input = isPlainObject(evidence) && Array.isArray(evidence.semanticJudgments)
    ? evidence.semanticJudgments
    : [];
  const malformedInput = !isPlainObject(evidence) || !Array.isArray(evidence.semanticJudgments);
  const unknown = input.filter((item) => !isPlainObject(item) || !SEMANTIC_REQUIREMENT_BY_ID.has(item.id));
  const checks = new Map();
  const sourceCache = new Map();

  for (const requirement of SEMANTIC_REQUIREMENTS) {
    const supplied = input.filter((item) => isPlainObject(item) && item.id === requirement.id);
    if (!evidenceState.valid || evidenceState.impactScopeAssessment.verdict !== 'PASS') {
      checks.set(requirement.id, gateCheck(
        requirement.id,
        'INCONCLUSIVE',
        'This semantic obligation cannot be judged without complete fixed WP-001 evidence.',
        [...evidenceState.errors, ...evidenceState.impactScopeAssessment.evidence],
        { category: requirement.category, label: requirement.label }
      ));
      continue;
    }
    if (malformedInput || supplied.length === 0) {
      checks.set(requirement.id, gateCheck(
        requirement.id,
        'INCONCLUSIVE',
        'The required evidence-connected semantic judgment was not supplied.',
        [],
        { category: requirement.category, label: requirement.label }
      ));
      continue;
    }

    const inspected = supplied.map((item) => inspectSemanticJudgment(item, requirement, evidenceState, projectRoot, sourceCache));
    const errors = inspected.flatMap((item) => item.errors);
    if (errors.length > 0) {
      checks.set(requirement.id, gateCheck(
        requirement.id,
        'INCONCLUSIVE',
        'The supplied semantic judgment is missing required evidence, binding, or AI FAIL fields.',
        errors,
        { category: requirement.category, label: requirement.label, judgments: supplied }
      ));
      continue;
    }

    const verdicts = new Set(supplied.map((item) => item.verdict));
    if (verdicts.size !== 1) {
      checks.set(requirement.id, gateCheck(
        requirement.id,
        'INCONCLUSIVE',
        'Conflicting semantic judgments cannot be normalized to PASS or FAIL.',
        supplied.flatMap((item) => item.evidence),
        { category: requirement.category, label: requirement.label, judgments: supplied }
      ));
      continue;
    }

    const verdict = supplied[0].verdict;
    const result = gateCheck(
      requirement.id,
      verdict,
      semanticMessage(requirement, verdict),
      supplied.flatMap((item) => item.evidence),
      { category: requirement.category, label: requirement.label, judgments: supplied }
    );
    checks.set(requirement.id, verdict === 'FAIL'
      ? scopeSemanticCheck(result, requirement.id, evidenceState)
      : result);
  }

  return { checks, unknown };
}

function inspectSemanticJudgment(judgment, requirement, evidenceState, projectRoot, sourceCache) {
  const errors = [];
  if (judgment.category !== requirement.category) {
    errors.push(inputEvidence(requirement.id, 'Semantic judgment category does not match its required obligation.'));
  }
  if (!['PASS', 'FAIL', 'INCONCLUSIVE'].includes(judgment.verdict)) {
    errors.push(inputEvidence(requirement.id, 'Semantic judgment verdict must be PASS, FAIL, or INCONCLUSIVE.'));
  }
  if (!nonEmptyText(judgment.rule)) {
    errors.push(inputEvidence(requirement.id, 'Semantic judgment must identify the reviewed rule.'));
  }
  if (!sameBinding(judgment.binding, evidenceState)) {
    errors.push(inputEvidence(requirement.id, 'Semantic judgment is not bound to the fixed policy, pre-change state, and impact scope.'));
  }
  if (!Array.isArray(judgment.evidence) || judgment.evidence.length === 0) {
    errors.push(inputEvidence(requirement.id, 'Semantic judgment must include target source evidence.'));
  } else {
    for (const location of judgment.evidence) {
      const error = validateSourceLocation(location, projectRoot, sourceCache);
      if (error) {
        errors.push(inputEvidence(requirement.id, error));
      } else if (
        !impactScopeContains(evidenceState, location.path) &&
        !(judgment.verdict === 'FAIL' && matchBaselineViolation(evidenceState, requirement.id, location))
      ) {
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
      evidenceState.observedBaselineViolations.add(match.index);
    } else {
      blockingEvidence.push(item);
      if (match) {
        evidenceState.observedBaselineViolations.add(match.index);
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
    errors,
    impactScope: null,
    observedBaselineViolations: new Set(),
    policy: null,
    preChange: null,
    valid: false
  };
  if (!isPlainObject(value)) {
    errors.push(inputEvidence('evidence', 'Final Gate evidence must be an object.'));
    return state;
  }
  if (isPlainObject(value.inputError) && nonEmptyText(value.inputError.message)) {
    errors.push({ kind: 'input', path: value.inputError.path || 'evidence', error: value.inputError.message });
  }

  state.policy = validatePolicy(value.policy, projectRoot, errors);
  state.preChange = validatePreChange(value.preChange, projectRoot, errors);
  state.impactScope = validateImpactScope(value.impactScope, projectRoot, errors);
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
  if (!isPlainObject(value) || !KNOWN_BASELINE_CHECK_IDS.has(value.checkId) || !safeRelativePath(value.path, false)) {
    errors.push(inputEvidence(name, 'Each pre-change violation requires a known check ID and safe source path.'));
    return;
  }
  if (value.line !== undefined && (!Number.isSafeInteger(value.line) || value.line < 1)) {
    errors.push(inputEvidence(`${name}.line`, 'Pre-change violation line must be a positive integer when supplied.'));
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
      (violation.line === undefined || violation.line === evidence.line);
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

  const adjacent = new Map(graph.files.map((file) => [file, new Set()]));
  for (const edge of graph.edges) {
    if (adjacent.has(edge.from) && adjacent.has(edge.to)) {
      adjacent.get(edge.from).add(edge.to);
      adjacent.get(edge.to).add(edge.from);
    }
  }
  const effective = new Set(graph.files.filter((file) => scopeContains(evidenceState.impactScope.entries, file)));
  const queue = [...effective];
  while (queue.length > 0) {
    const current = queue.shift();
    for (const related of adjacent.get(current) || []) {
      if (!effective.has(related)) {
        effective.add(related);
        queue.push(related);
      }
    }
  }
  return { effectivePaths: [...effective].sort(), evidence: [], verdict: 'PASS' };
}

function impactScopeContains(evidenceState, filePath) {
  return Boolean(
    evidenceState.impactScope &&
    (scopeContains(evidenceState.impactScope.entries, filePath) ||
      (evidenceState.impactScopeAssessment && evidenceState.impactScopeAssessment.effectivePaths.includes(filePath)))
  );
}

function scopeContains(entries, filePath) {
  return entries.some((entry) => {
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

function sameBinding(binding, evidenceState) {
  return isPlainObject(binding) && evidenceState.policy && evidenceState.preChange && evidenceState.impactScope &&
    binding.policyId === evidenceState.policy.id &&
    binding.preChangeId === evidenceState.preChange.id &&
    binding.impactScopeId === evidenceState.impactScope.id;
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
    ? evidenceState.preChange.violations
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
  return safeRelativePath(value, false);
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

function nonEmptyText(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

module.exports = { gateProject };
