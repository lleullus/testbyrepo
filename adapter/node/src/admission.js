'use strict';

const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

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
const RISK_ORDER = { fail: 0, inconclusive: 1, risk: 2 };
const RESERVED_WRITE_SEGMENTS = new Set([
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
const SEARCH_STOP_WORDS = new Set([
  'a',
  'an',
  'add',
  'and',
  'behavior',
  'change',
  'for',
  'function',
  'helper',
  'implement',
  'in',
  'make',
  'new',
  'of',
  'or',
  'shape',
  'the',
  'to',
  'type',
  'with'
]);
const ADMISSION_CAPABILITIES = new WeakMap();

/**
 * Creates one read-only admission session for a user change request.
 * The returned attemptWrite method is the only authorization boundary for declarative file writes.
 * It accepts { request, scope?, writes: [{ path, content }] } and never executes caller code.
 *
 * @param {object} options admission input
 * @param {Function} diagnoseProject canonical structural diagnosis function
 * @param {Function} bindFinalGate private final-Gate binder
 * @returns {{admission: object, attemptWrite: Function, finalGate: Function}}
 */
function createAdmissionSession(options, diagnoseProject, bindFinalGate) {
  if (typeof diagnoseProject !== 'function') {
    throw new TypeError('createAdmissionSession requires the canonical diagnoseProject function.');
  }
  if (typeof bindFinalGate !== 'function') {
    throw new TypeError('createAdmissionSession requires its private final-Gate binder.');
  }

  const assessment = assessAdmission(options, diagnoseProject);
  const admissionCapability = Object.freeze(Object.create(null));
  ADMISSION_CAPABILITIES.set(admissionCapability, {
    admission: assessment.result,
    admittedScope: assessment.admittedScope,
    currentSourceAuthorized() {
      const current = assessment.projectRoot ? fingerprintProject(assessment.projectRoot) : null;
      return Boolean(current && current.digest && current.digest === assessment.currentDigest);
    },
    projectRoot: assessment.projectRoot,
    reviewer: isPlainObject(options) ? options.semanticReviewer : null
  });
  const finalGateSession = bindFinalGate(admissionCapability);
  return Object.freeze({
    ...assessment.result,
    admission: assessment.result,
    attemptWrite(gateOptions) {
      return attemptWrite(assessment, gateOptions);
    },
    finalGate() {
      return finalGateSession.run();
    }
  });
}

function resolveAdmissionCapability(capability) {
  return capability && typeof capability === 'object'
    ? ADMISSION_CAPABILITIES.get(capability) || null
    : null;
}

function assessAdmission(options, diagnoseProject) {
  const input = normalizeAdmissionInput(options);
  const risks = [...input.risks];
  const behavior = extractBehavior(input.requestText);
  const missingBehavior = missingBehaviorFields(behavior);
  let diagnosis = null;
  let diagnosisError = null;
  let beforeState = null;
  let afterState = null;
  let reinvestigation = {
    performed: false,
    reason: missingBehavior.length > 0 ? 'required-behavior-missing' : null,
    observed: null
  };

  if (input.projectRoot) {
    beforeState = fingerprintProject(input.projectRoot);
    if (!beforeState.digest) {
      risks.push(projectStateRisk(beforeState, 'before-admission'));
    }

    ({ diagnosis, error: diagnosisError } = diagnoseSafely(input.projectRoot, diagnoseProject));

    if (missingBehavior.length > 0) {
      const rechecked = diagnoseSafely(input.projectRoot, diagnoseProject);
      diagnosis = rechecked.diagnosis;
      diagnosisError = rechecked.error;
      reinvestigation = {
        performed: true,
        reason: 'required-behavior-missing',
        observed: describeReinvestigation(diagnosis)
      };
    }

  }

  if (diagnosisError) {
    risks.push(issue(
      'inconclusive',
      'diagnosis-unavailable',
      'Repository structure could not be established from the project files.',
      [fileEvidence('.', diagnosisError.message)]
    ));
  }

  const newProject = isCleanNewProject(diagnosis);
  if (diagnosis && !newProject) {
    risks.push(...copyDiagnosisRisks(diagnosis));
  }

  const questions = behaviorQuestions(behavior);
  for (const field of missingBehavior) {
    risks.push(issue(
      'inconclusive',
      `missing-${field}`,
      missingBehaviorMessage(field),
      []
    ));
  }

  let baseline = null;
  let selectedResponsibility = null;
  let inferredScope = null;
  if (newProject) {
    baseline = createBaseline(input, diagnosis);
    selectedResponsibility = proposedResponsibility(baseline);
    inferredScope = scopeForBaseline(baseline);
  } else if (diagnosis) {
    selectedResponsibility = selectObservedResponsibility(diagnosis, input.requestText);
    if (!selectedResponsibility) {
      const responsibilityReinvestigation = reinvestigateResponsibility(diagnosis, input.requestText);
      selectedResponsibility = responsibilityReinvestigation.responsibility;
      reinvestigation = {
        performed: true,
        reason: 'unresolved-change-responsibility',
        observed: responsibilityReinvestigation.observed
      };
    }
    if (!selectedResponsibility) {
      risks.push(issue(
        'inconclusive',
        'unresolved-change-responsibility',
        'Repository evidence did not establish one responsibility for this requested behavior and scope.',
        responsibilityEvidence(diagnosis)
      ));
      questions.push('Which user-visible action should this change affect?');
    } else {
      inferredScope = scopeForObservedResponsibility(selectedResponsibility, diagnosis);
    }
  }

  let admittedScope = inferredScope;
  if (inferredScope && input.suppliedScope.scope) {
    admittedScope = narrowScope(inferredScope, input.suppliedScope.scope);
    if (!admittedScope) {
      risks.push(issue(
        'inconclusive',
        'scope-outside-selected-responsibility',
        'The supplied programmatic scope does not narrow or confirm the responsibility established from repository evidence.',
        selectedResponsibility ? selectedResponsibility.evidence : []
      ));
    }
  }
  if (!admittedScope && selectedResponsibility) {
    risks.push(issue(
      'inconclusive',
      'unresolved-admitted-scope',
      'Repository evidence did not establish physical paths that can be admitted for this request.',
      selectedResponsibility.evidence
    ));
  }

  const reuse = assessReuse(input.projectRoot, diagnosis, input.requestText, newProject);
  if (reuse.risk) {
    risks.push(reuse.risk);
  }
  const repositoryAuthority = establishRepositoryAuthority(
    diagnosis,
    baseline,
    input.requestText,
    newProject
  );
  risks.push(...repositoryAuthority.risks);

  if (input.projectRoot) {
    afterState = fingerprintProject(input.projectRoot);
    if (!afterState.digest) {
      risks.push(projectStateRisk(afterState, 'after-admission'));
    } else if (beforeState.digest && beforeState.digest !== afterState.digest) {
      risks.push(issue(
        'inconclusive',
        'project-changed-during-admission',
        'The project source changed while admission evidence was being collected.',
        [
          sourceStateEvidence(beforeState),
          sourceStateEvidence(afterState)
        ]
      ));
    }
  }

  const testObligations = deriveTestObligations(behavior);
  const sortedRisks = sortRisks(risks);
  const verdict = verdictForRisks(sortedRisks);
  const summaryResponsibility = summarizeResponsibility(selectedResponsibility);
  const mainRisks = sortedRisks.slice(0, 3);
  const sourceState = stableSourceState(beforeState, afterState);
  const repositoryEvidence = describeRepositoryEvidence(diagnosis, repositoryAuthority);
  const details = {
    verdict,
    selectedResponsibility: summaryResponsibility,
    mainRisks,
    binding: {
      projectDirectory: input.projectRoot,
      normalizedIntent: input.intentKey,
      normalizedScope: admittedScope ? admittedScope.entries.map((entry) => entry.path) : null,
      admittedScope: describeScope(admittedScope),
      sourceState,
      originalSourceState: copySourceState(sourceState),
      currentSourceState: copySourceState(sourceState)
    },
    behavior,
    reinvestigation,
    repositoryEvidence,
    responsibilityEvidence: selectedResponsibility ? selectedResponsibility.evidence : [],
    proposedBaseline: baseline,
    reuse,
    testObligations,
    questions,
    risks: sortedRisks,
    evidencePolicy: 'Only project files read during admission establish structural evidence; unsupported claims do not alter this result.'
  };
  const summary = {
    verdict,
    selectedResponsibility: summaryResponsibility,
    mainRisks
  };
  const result = {
    verdict,
    responsibility: summaryResponsibility,
    risks: sortedRisks,
    questions,
    summary,
    details
  };

  return {
    result,
    verdict,
    projectRoot: input.projectRoot,
    intentKey: input.intentKey,
    admittedScope,
    inferredScope,
    scopeKey: admittedScope ? admittedScope.key : null,
    currentDigest: sourceState ? sourceState.digest : null
  };
}

function normalizeAdmissionInput(options) {
  const risks = [];
  const value = isPlainObject(options) ? options : {};
  let projectRoot = null;

  if (typeof value.projectDirectory === 'string' && normalizeText(value.projectDirectory)) {
    projectRoot = path.resolve(normalizeText(value.projectDirectory));
  } else {
    risks.push(issue(
      'inconclusive',
      'missing-project-directory',
      'A readable project directory is required for change admission.',
      []
    ));
  }

  const requestText = typeof value.request === 'string' ? normalizeText(value.request) : '';
  if (!requestText) {
    risks.push(issue(
      'inconclusive',
      'missing-request',
      'A natural-language change request is required for admission.',
      []
    ));
  }

  const suppliedScope = normalizeProgrammaticScope(
    value.scope,
    Object.hasOwn(value, 'scope') && value.scope !== undefined,
    projectRoot
  );
  if (suppliedScope.error) {
    risks.push(issue(
      'inconclusive',
      'invalid-programmatic-scope',
      'The supplied programmatic scope must be one or more safe relative project paths.',
      []
    ));
  }

  return {
    projectRoot,
    requestText,
    intentKey: requestText ? requestText.toLowerCase() : null,
    suppliedScope,
    risks
  };
}

function normalizeProgrammaticScope(scope, provided, projectRoot) {
  if (!provided) {
    return { error: null, provided: false, scope: null };
  }

  const rawValues = typeof scope === 'string' || isPlainObject(scope) ? [scope] : Array.isArray(scope) ? scope : null;
  if (!rawValues || rawValues.length === 0) {
    return { error: 'missing-path', provided: true, scope: null };
  }

  const entries = [];
  for (const value of rawValues) {
    const pathValue = isPlainObject(value) ? value.path : value;
    const normalized = normalizeRelativePath(pathValue);
    if (!normalized.path) {
      return { error: normalized.error, provided: true, scope: null };
    }
    const requestedMode = isPlainObject(value) ? value.mode : null;
    if (requestedMode !== null && requestedMode !== undefined && !['exact', 'subtree'].includes(requestedMode)) {
      return { error: 'invalid-mode', provided: true, scope: null };
    }
    entries.push({
      mode: requestedMode || inferExplicitScopeMode(projectRoot, normalized.path),
      path: normalized.path
    });
  }

  return { error: null, provided: true, scope: createScope('explicit', entries) };
}

function inferExplicitScopeMode(projectRoot, relativePath) {
  if (!projectRoot) {
    return 'exact';
  }
  try {
    return fs.lstatSync(path.join(projectRoot, relativePath)).isDirectory() ? 'subtree' : 'exact';
  } catch (error) {
    return 'exact';
  }
}

function normalizeRelativePath(value) {
  if (typeof value !== 'string' || value.length === 0 || value.includes('\u0000')) {
    return { error: 'invalid-path', path: null };
  }
  if (value.includes('\\') || path.posix.isAbsolute(value) || path.win32.isAbsolute(value) || /^[A-Za-z]:/.test(value)) {
    return { error: 'absolute-path', path: null };
  }

  const segments = value.split('/');
  if (segments.some((segment) => !segment || segment === '.' || segment === '..')) {
    return { error: 'traversal-path', path: null };
  }
  if (segments.some((segment) => RESERVED_WRITE_SEGMENTS.has(segment))) {
    return { error: 'reserved-path', path: null };
  }
  return { error: null, path: segments.join('/') };
}

function normalizeText(value) {
  return value.normalize('NFKC').trim().replace(/\s+/g, ' ');
}

function diagnoseSafely(projectRoot, diagnoseProject) {
  try {
    return { diagnosis: diagnoseProject(projectRoot), error: null };
  } catch (error) {
    return { diagnosis: null, error };
  }
}

function extractBehavior(requestText) {
  if (!requestText) {
    return {
      desiredBehavior: null,
      behaviorToPreserve: null,
      observableFailureOutcome: null
    };
  }

  const sentences = requestText.split(/[\n.!?;]+/).map((sentence) => sentence.trim()).filter(Boolean);
  const preservation = sentences.find(isPreservationSentence) || null;
  const failure = sentences.find(isFailureSentence) || null;
  const desired = sentences
    .filter((sentence) => !isFailureSentence(sentence))
    .map(extractDesiredClause)
    .find((sentence) => sentence && hasDesiredAction(sentence)) || null;

  const roleTexts = [desired, preservation, failure].filter(Boolean).map(normalizeText);
  const hasDuplicateRole = new Set(roleTexts.map((text) => text.toLowerCase())).size !== roleTexts.length;

  return {
    desiredBehavior: desired && !hasDuplicateRole ? requestedBehavior(desired) : null,
    behaviorToPreserve: preservation ? requestedBehavior(preservation) : null,
    observableFailureOutcome: failure ? requestedBehavior(failure) : null
  };
}

function extractDesiredClause(sentence) {
  const preservationMarker = sentence.search(
    /\b(?:keep|preserve|retain|leave)\b|\b(?:do not|don't|without)\s+(?:change|alter|break|affect|modify)\b|(?:기존|현재|원래)/i
  );
  const candidate = preservationMarker > 0 ? sentence.slice(0, preservationMarker) : sentence;
  return candidate
    .replace(/\b(?:and|but|while)\s*$/i, '')
    .replace(/(?:하고|하며|하되|그리고)\s*$/, '')
    .trim();
}

function requestedBehavior(text) {
  return { source: 'user-request', text };
}

function isPreservationSentence(sentence) {
  return /\b(keep|preserve|retain|leave)\b/i.test(sentence)
    || /\b(do not|don't|without)\s+(change|alter|break|affect|modify)\b/i.test(sentence)
    || /\b(existing|current|previous).*(unchanged|the same|continue)\b/i.test(sentence)
    || /(?:기존|현재|원래).*(?:그대로|유지|변경하지|바꾸지|건드리지|영향.*없|변함없|동일)/.test(sentence)
    || /(?:그대로.*유지|유지.*그대로|변경하지|바꾸지|건드리지)/.test(sentence);
}

function isFailureSentence(sentence) {
  const englishCondition = /\b(if|when|unless)\b/i.test(sentence)
    || /\bon\s+(failure|failures|error|errors|invalid)\b/i.test(sentence)
    || /\b(empty|null|undefined|missing|invalid|failure|fails)\b/i.test(sentence);
  const englishOutcome = /\b(show|display|return|respond|report|tell|see|visible|error|fail|reject|prevent|block|message)\b/i.test(sentence);
  const koreanCondition = /(?:이면|라면|으면|면|경우|실패|없|누락|null|잘못|유효하지)/.test(sentence);
  const koreanOutcome = /(?:보여|표시|반환|알려|오류|에러|실패|거부|막|차단|메시지)/.test(sentence);
  return (englishCondition && englishOutcome) || (koreanCondition && koreanOutcome);
}

function hasDesiredAction(sentence) {
  return /\b(add|allow|create|change|make|update|support|send|save|show|display|let|enable|prevent|remove|fix|implement|register|validate|check|accept|reject|calculate|list|find|load|read|write|delete|login|notify|reuse)\b/i.test(sentence)
    || /(?:추가|만들|생성|변경|수정|지원|보여|표시|저장|허용|막|방지|고쳐|개선|등록|삭제|로그인|가입|검증|확인|검사|계산|조회|읽|쓰기|알림|전송|재사용)/.test(sentence);
}

function missingBehaviorFields(behavior) {
  const missing = [];
  if (!behavior.desiredBehavior) {
    missing.push('desired-behavior');
  }
  if (!behavior.behaviorToPreserve) {
    missing.push('behavior-to-preserve');
  }
  if (!behavior.observableFailureOutcome) {
    missing.push('observable-failure-outcome');
  }
  return missing;
}

function behaviorQuestions(behavior) {
  const questions = [];
  if (!behavior.desiredBehavior) {
    questions.push('What should people be able to do after this change?');
  }
  if (!behavior.behaviorToPreserve) {
    questions.push('What should continue to work exactly as it does now?');
  }
  if (!behavior.observableFailureOutcome) {
    questions.push('What should people see or experience when the request cannot be completed?');
  }
  return questions;
}

function missingBehaviorMessage(field) {
  const messages = {
    'desired-behavior': 'The requested user-visible behavior was not stated.',
    'behavior-to-preserve': 'The behavior that must remain unchanged was not stated.',
    'observable-failure-outcome': 'The observable result when the request cannot be completed was not stated.'
  };
  return messages[field];
}

function describeReinvestigation(diagnosis) {
  if (!diagnosis || !diagnosis.details) {
    return null;
  }
  return {
    directories: diagnosis.details.structure ? diagnosis.details.structure.directories : [],
    sourceFiles: diagnosis.details.structure ? diagnosis.details.structure.sourceFiles : [],
    responsibilities: diagnosis.details.responsibilities || []
  };
}

function isCleanNewProject(diagnosis) {
  if (!diagnosis || !diagnosis.details || !diagnosis.details.structure || !diagnosis.details.project) {
    return false;
  }

  const sourceFiles = diagnosis.details.structure.sourceFiles;
  const project = diagnosis.details.project;
  if (!Array.isArray(sourceFiles) || sourceFiles.length > 0) {
    return false;
  }
  if (['invalid', 'unreadable'].includes(project.packageConfiguration && project.packageConfiguration.status)) {
    return false;
  }
  if (['invalid', 'unreadable'].includes(project.tsconfig && project.tsconfig.status)) {
    return false;
  }

  return (diagnosis.risks || []).every((risk) => {
    return risk.code === 'no-product-source-files' || risk.code === 'required-missing-package.json';
  });
}

function createBaseline(input, diagnosis) {
  const usesTypeScript = /\btype\s*script\b|\btypescript\b|타입스크립트/i.test(input.requestText)
    || (diagnosis.details.project.tsconfig && diagnosis.details.project.tsconfig.status === 'present');
  const extension = usesTypeScript ? 'ts' : 'js';
  const packageStatus = diagnosis.details.project.packageConfiguration && diagnosis.details.project.packageConfiguration.status;
  const tsconfigStatus = diagnosis.details.project.tsconfig && diagnosis.details.project.tsconfig.status;
  const entryPath = `src/index.${extension}`;
  const files = [
    {
      path: 'package.json',
      responsibility: 'Package entry and runtime configuration',
      status: packageStatus === 'present' ? 'observed' : 'proposed'
    }
  ];

  if (usesTypeScript) {
    files.push({
      path: 'tsconfig.json',
      responsibility: 'TypeScript compiler configuration',
      status: tsconfigStatus === 'present' ? 'observed' : 'proposed'
    });
  }
  files.push(
    {
      path: entryPath,
      responsibility: 'Requested behavior entry',
      status: 'proposed'
    },
    {
      path: `test/index.test.${extension}`,
      responsibility: 'Behavioral test coverage',
      status: 'proposed'
    }
  );

  return {
    status: 'proposed-not-created',
    language: usesTypeScript ? 'TypeScript' : 'Node.js',
    entryPath,
    files
  };
}

function proposedResponsibility(baseline) {
  return {
    ownerPath: baseline.entryPath,
    responsibility: 'Requested behavior entry in the proposed baseline',
    source: 'proposed',
    evidence: baseline.files.filter((file) => file.path === baseline.entryPath)
  };
}

function selectObservedResponsibility(diagnosis, requestText) {
  const details = diagnosis.details;
  const responsibilities = (details.responsibilities || []).filter((responsibility) => {
    return !['package.json', 'tsconfig.json'].includes(responsibility.ownerPath);
  });
  if (responsibilities.length === 0) {
    return null;
  }
  if (responsibilities.length === 1) {
    return { ...responsibilities[0], source: 'observed' };
  }

  const boundaries = new Map((details.structure.boundaries || []).map((boundary) => [boundary.path, boundary]));
  const searchTerms = extractSearchTerms(requestText);
  const scored = responsibilities.map((responsibility) => {
    const boundary = boundaries.get(responsibility.ownerPath);
    const corpus = [responsibility.ownerPath, ...(boundary ? boundary.files : [])].join(' ');
    const corpusTerms = new Set(extractSearchTerms(corpus));
    let score = 0;
    for (const term of searchTerms) {
      if (corpusTerms.has(term)) {
        score += 3;
      }
    }
    return { responsibility, score };
  }).sort((left, right) => {
    if (right.score !== left.score) {
      return right.score - left.score;
    }
    return right.responsibility.ownerPath.length - left.responsibility.ownerPath.length;
  });

  if (scored[0].score === 0) {
    return null;
  }

  const bestScore = scored[0].score;
  const tied = scored.filter((candidate) => candidate.score === bestScore);
  const deepestLength = Math.max(...tied.map((candidate) => candidate.responsibility.ownerPath.length));
  const deepest = tied.filter((candidate) => candidate.responsibility.ownerPath.length === deepestLength);
  if (deepest.length !== 1 || !tied.every((candidate) => {
    return candidate.responsibility.ownerPath === deepest[0].responsibility.ownerPath
      || deepest[0].responsibility.ownerPath.startsWith(`${candidate.responsibility.ownerPath}/`);
  })) {
    return null;
  }

  return { ...deepest[0].responsibility, source: 'observed' };
}

function reinvestigateResponsibility(diagnosis, requestText) {
  const details = diagnosis.details;
  const boundaries = new Map((details.structure.boundaries || []).map((boundary) => [boundary.path, boundary]));
  const requestTerms = extractSearchTerms(requestText);
  const requestTargetsTests = requestTerms.some((term) => ['test', 'tests', 'testing', '테스트', '검사'].includes(term));
  const candidates = (details.responsibilities || []).filter((responsibility) => {
    if (['package.json', 'tsconfig.json'].includes(responsibility.ownerPath)) {
      return false;
    }
    const boundary = boundaries.get(responsibility.ownerPath);
    return requestTargetsTests || !boundary || boundary.role !== 'test';
  });
  const dependencyDirection = details.dependencyDirection || {};
  const references = dependencyDirection.internalReferences || [];
  const entries = packageEntryPaths(details.responsibilities || []);
  const reuseCandidates = details.reuseCandidates || [];
  const scored = candidates.map((responsibility) => {
    const boundary = boundaries.get(responsibility.ownerPath);
    const files = boundary ? boundary.files : [];
    const relatedReferences = references.filter((reference) => {
      return pathBelongsToResponsibility(reference.path, responsibility.ownerPath)
        || pathBelongsToResponsibility(reference.target, responsibility.ownerPath);
    });
    const relatedReuse = reuseCandidates.filter((candidate) => {
      return pathBelongsToResponsibility(candidate.path, responsibility.ownerPath);
    });
    const corpus = [
      responsibility.ownerPath,
      ...files,
      ...relatedReferences.flatMap((reference) => [reference.path, reference.target, reference.specifier]),
      ...relatedReuse.flatMap((candidate) => [candidate.path, ...(candidate.symbols || [])])
    ].join(' ');
    const corpusTerms = new Set(extractSearchTerms(corpus));
    const termScore = requestTerms.filter((term) => corpusTerms.has(term)).length * 3;
    const entryScore = entries.some((entry) => pathBelongsToResponsibility(entry, responsibility.ownerPath)) ? 5 : 0;
    return {
      responsibility,
      score: termScore + entryScore,
      evidence: {
        entryPaths: entries.filter((entry) => pathBelongsToResponsibility(entry, responsibility.ownerPath)),
        references: relatedReferences,
        reuseCandidates: relatedReuse
      }
    };
  }).sort((left, right) => right.score - left.score || left.responsibility.ownerPath.localeCompare(right.responsibility.ownerPath));

  const best = scored[0];
  const tied = best ? scored.filter((candidate) => candidate.score === best.score) : [];
  const responsibility = best && (scored.length === 1 || (best.score > 0 && tied.length === 1))
    ? { ...best.responsibility, source: 'observed' }
    : null;
  return {
    responsibility,
    observed: {
      candidateScores: scored.map((candidate) => ({
        ownerPath: candidate.responsibility.ownerPath,
        score: candidate.score,
        evidence: candidate.evidence
      })),
      excludedTestResponsibilities: requestTargetsTests
        ? []
        : [...boundaries.values()].filter((boundary) => boundary.role === 'test').map((boundary) => boundary.path)
    }
  };
}

function packageEntryPaths(responsibilities) {
  const packageResponsibility = responsibilities.find((responsibility) => responsibility.ownerPath === 'package.json');
  if (!packageResponsibility) {
    return [];
  }
  return (packageResponsibility.evidence || []).flatMap((evidence) => {
    if (evidence.kind !== 'config' || !['bin', 'exports', 'main', 'module'].includes(evidence.key)) {
      return [];
    }
    return collectStringValues(evidence.value).map((value) => value.replace(/^\.\//, ''));
  });
}

function collectStringValues(value) {
  if (typeof value === 'string') {
    return [value];
  }
  if (Array.isArray(value)) {
    return value.flatMap(collectStringValues);
  }
  if (isPlainObject(value)) {
    return Object.values(value).flatMap(collectStringValues);
  }
  return [];
}

function pathBelongsToResponsibility(filePath, ownerPath) {
  return typeof filePath === 'string'
    && (filePath === ownerPath || filePath.startsWith(`${ownerPath}/`));
}

function summarizeResponsibility(responsibility) {
  if (!responsibility) {
    return null;
  }
  return {
    ownerPath: responsibility.ownerPath,
    responsibility: responsibility.responsibility,
    source: responsibility.source
  };
}

function responsibilityEvidence(diagnosis) {
  if (!diagnosis || !diagnosis.details) {
    return [];
  }
  return (diagnosis.details.responsibilities || []).flatMap((responsibility) => responsibility.evidence || []);
}

function scopeForBaseline(baseline) {
  return createScope('inferred', baseline.files.map((file) => ({ mode: 'exact', path: file.path })));
}

function scopeForObservedResponsibility(responsibility, diagnosis) {
  if (responsibility.ownerPath !== '.') {
    return createScope('inferred', [{ mode: 'subtree', path: responsibility.ownerPath }]);
  }

  const files = (diagnosis.details.structure.sourceFiles || [])
    .filter((sourceFile) => !sourceFile.includes('/'))
    .map((sourceFile) => ({ mode: 'exact', path: sourceFile }));
  return files.length > 0 ? createScope('inferred', files) : null;
}

function createScope(origin, entries) {
  const uniqueEntries = [];
  const seen = new Set();
  for (const entry of entries) {
    const key = `${entry.mode}:${entry.path}`;
    if (!seen.has(key)) {
      seen.add(key);
      uniqueEntries.push({ mode: entry.mode, path: entry.path });
    }
  }
  uniqueEntries.sort((left, right) => `${left.mode}:${left.path}`.localeCompare(`${right.mode}:${right.path}`));
  return {
    entries: uniqueEntries,
    key: uniqueEntries.map((entry) => `${entry.mode}:${entry.path}`).join('\u0000'),
    origin
  };
}

function narrowScope(inferredScope, explicitScope) {
  const entries = [];
  for (const explicitEntry of explicitScope.entries) {
    const containingEntries = inferredScope.entries.filter((entry) => scopeContains(entry, explicitEntry.path));
    if (containingEntries.length === 0) {
      return null;
    }
    if (explicitEntry.mode === 'subtree' && !containingEntries.some((entry) => entry.mode === 'subtree')) {
      return null;
    }
    entries.push({
      mode: explicitEntry.mode,
      path: explicitEntry.path
    });
  }
  return createScope('explicit', entries);
}

function scopeContains(entry, relativePath) {
  if (entry.mode === 'exact') {
    return entry.path === relativePath;
  }
  return relativePath === entry.path || relativePath.startsWith(`${entry.path}/`);
}

function scopeAllows(scope, relativePath) {
  return scope.entries.some((entry) => scopeContains(entry, relativePath));
}

function describeScope(scope) {
  if (!scope) {
    return null;
  }
  return {
    entries: scope.entries.map((entry) => ({ mode: entry.mode, path: entry.path })),
    origin: scope.origin,
    paths: scope.entries.map((entry) => entry.path)
  };
}

function assessReuse(projectRoot, diagnosis, requestText, newProject) {
  const requestedShapes = requestedShapesFor(requestText);
  const reuseCandidates = diagnosis && diagnosis.details ? diagnosis.details.reuseCandidates || [] : [];
  const result = {
    requestedShapes,
    searchTerms: extractSearchTerms(requestText),
    reuseCandidates,
    observedSymbols: [],
    decision: 'not-applicable',
    allowsCreation: null,
    reason: 'No new function, helper, type, or shape was proposed by the request.',
    risk: null
  };

  if (requestedShapes.length === 0) {
    return result;
  }

  if (newProject) {
    result.decision = 'creation-necessary';
    result.allowsCreation = true;
    result.reason = 'No existing project source was observed in the proposed baseline.';
    return result;
  }

  if (!projectRoot || !diagnosis || !diagnosis.details) {
    result.decision = 'inconclusive';
    result.allowsCreation = false;
    result.reason = 'Observed symbols and reuse candidates could not be searched.';
    result.risk = issue(
      'inconclusive',
      'reuse-search-unavailable',
      'A proposed code shape cannot be admitted until observed symbols and reuse candidates are searchable.',
      []
    );
    return result;
  }

  const symbolSearch = collectObservedSymbols(projectRoot, diagnosis);
  result.observedSymbols = symbolSearch.symbols;
  if (symbolSearch.errors.length > 0) {
    result.decision = 'inconclusive';
    result.allowsCreation = false;
    result.reason = 'Some observed source files could not be searched for reusable symbols.';
    result.risk = issue(
      'inconclusive',
      'reuse-search-unreadable',
      'A proposed code shape cannot be admitted because observed symbols could not be fully searched.',
      symbolSearch.errors.map((error) => fileEvidence(error.path, error.message))
    );
    return result;
  }

  const matches = findReuseMatches(result.searchTerms, result.observedSymbols, reuseCandidates, requestedShapes);
  result.matches = matches;
  if (matches.length > 0) {
    result.decision = 'reuse-possible';
    result.allowsCreation = false;
    result.reason = 'Observed symbols or reuse candidates match the requested behavior; creation is not admitted before reuse is considered.';
    result.risk = issue(
      'fail',
      'reuse-required-for-proposed-shape',
      'The request explicitly proposes a new code shape even though reusable observed code matches it. Reframe the request to reuse the observed candidate.',
      matches.flatMap((match) => match.evidence || [])
    );
  } else {
    result.decision = 'creation-necessary';
    result.allowsCreation = true;
    result.reason = 'No observed symbol or reuse candidate matched the proposed code shape.';
  }
  return result;
}

function establishRepositoryAuthority(diagnosis, baseline, requestText, newProject) {
  if (newProject) {
    return {
      executionPaths: baseline ? [baseline.entryPath] : [],
      canonicalSsot: baseline ? {
        evidence: baseline.files.filter((file) => file.path === baseline.entryPath),
        path: baseline.entryPath,
        source: 'proposed-baseline'
      } : null,
      risks: []
    };
  }
  if (!diagnosis || !diagnosis.details) {
    return {
      executionPaths: [],
      canonicalSsot: null,
      risks: [issue(
        'inconclusive',
        'repository-authority-unavailable',
        'Execution paths and canonical source authority could not be established.',
        []
      )]
    };
  }

  const sourceFiles = diagnosis.details.structure.sourceFiles || [];
  const entryEvidence = packageEntryEvidence(diagnosis.details.responsibilities || []);
  const configuredEntries = [...new Set(entryEvidence.flatMap((evidence) => collectStringValues(evidence.value)))];
  const executionPaths = [...new Set(configuredEntries
    .map((entry) => resolveObservedEntryPath(entry, sourceFiles))
    .filter(Boolean))].sort();
  const risks = [];
  if (configuredEntries.length === 0 || executionPaths.length === 0) {
    risks.push(issue(
      'inconclusive',
      'execution-path-unresolved',
      'No configured package execution entry could be resolved to observed source.',
      entryEvidence
    ));
  } else if (executionPaths.length < configuredEntries.length) {
    risks.push(issue(
      'inconclusive',
      'execution-entry-unresolved',
      'At least one configured package execution entry could not be resolved to observed source.',
      entryEvidence
    ));
  }

  const sourceCandidates = (diagnosis.details.ssotCandidates || []).filter((candidate) => {
    return !['package.json', 'tsconfig.json'].includes(candidate.path);
  });
  const requestTerms = extractSearchTerms(requestText);
  const scoredCandidates = sourceCandidates.map((candidate) => {
    const candidateTerms = new Set(extractSearchTerms(`${candidate.path} ${(candidate.symbols || []).join(' ')}`));
    return {
      candidate,
      score: requestTerms.filter((term) => candidateTerms.has(term)).length
    };
  }).sort((left, right) => right.score - left.score || left.candidate.path.localeCompare(right.candidate.path));
  const bestScore = scoredCandidates[0] ? scoredCandidates[0].score : 0;
  const bestCandidates = scoredCandidates.filter((candidate) => candidate.score === bestScore);
  let canonicalSsot = null;
  if (bestScore > 0 && bestCandidates.length === 1) {
    canonicalSsot = canonicalSsotFromCandidate(bestCandidates[0].candidate, 'request-match');
  } else if (sourceCandidates.length === 1) {
    canonicalSsot = canonicalSsotFromCandidate(sourceCandidates[0], 'single-source-candidate');
  } else {
    const executionCandidates = sourceCandidates.filter((candidate) => executionPaths.includes(candidate.path));
    if (executionCandidates.length === 1) {
      canonicalSsot = canonicalSsotFromCandidate(executionCandidates[0], 'configured-entry');
    } else if (sourceCandidates.length === 0 && executionPaths.length === 1) {
      canonicalSsot = {
        evidence: entryEvidence,
        path: executionPaths[0],
        source: 'configured-entry'
      };
    }
  }
  if (!canonicalSsot) {
    risks.push(issue(
      'inconclusive',
      'canonical-ssot-unresolved',
      'Repository evidence did not establish one canonical source of truth for the requested behavior.',
      sourceCandidates.flatMap((candidate) => candidate.evidence || [])
    ));
  }

  return { canonicalSsot, executionPaths, risks };
}

function packageEntryEvidence(responsibilities) {
  const packageResponsibility = responsibilities.find((responsibility) => responsibility.ownerPath === 'package.json');
  return packageResponsibility
    ? (packageResponsibility.evidence || []).filter((evidence) => {
      return evidence.kind === 'config' && ['bin', 'exports', 'main', 'module'].includes(evidence.key);
    })
    : [];
}

function resolveObservedEntryPath(entry, sourceFiles) {
  if (typeof entry !== 'string' || (!entry.startsWith('.') && !entry.includes('/'))) {
    return null;
  }
  const normalized = entry.replace(/^\.\//, '').replaceAll('\\', '/');
  if (sourceFiles.includes(normalized)) {
    return normalized;
  }
  const extension = path.posix.extname(normalized);
  const base = extension ? normalized.slice(0, -extension.length) : normalized;
  return sourceFiles.find((sourceFile) => {
    const sourceExtension = path.posix.extname(sourceFile);
    const sourceBase = sourceFile.slice(0, -sourceExtension.length);
    return sourceBase === base || sourceBase === `${normalized}/index`;
  }) || null;
}

function canonicalSsotFromCandidate(candidate, source) {
  return {
    evidence: candidate.evidence || [],
    path: candidate.path,
    source,
    symbols: candidate.symbols || []
  };
}

function requestedShapesFor(requestText) {
  const shapes = new Set();
  const english = /\b(?:add|create|make|introduce|implement|new)\b[^.!?\n]{0,48}?\b(function|helper|type|shape)\b/gi;
  for (let match = english.exec(requestText); match; match = english.exec(requestText)) {
    shapes.add(match[1].toLowerCase());
  }

  const korean = /(?:추가|새로운|새|만들|생성|도입|구현)[^.!?\n]{0,30}?(함수|헬퍼|타입|형태|구조)/g;
  for (let match = korean.exec(requestText); match; match = korean.exec(requestText)) {
    const shapeByWord = {
      구조: 'shape',
      타입: 'type',
      형태: 'shape',
      함수: 'function',
      헬퍼: 'helper'
    };
    shapes.add(shapeByWord[match[1]]);
  }
  return [...shapes];
}

function collectObservedSymbols(projectRoot, diagnosis) {
  const symbols = [];
  const seen = new Set();
  const errors = [];
  const sourceFiles = diagnosis.details.structure.sourceFiles || [];

  function add(pathValue, symbol, evidence, kind = 'unknown') {
    const key = `${pathValue}\u0000${symbol}`;
    if (!seen.has(key)) {
      seen.add(key);
      symbols.push({ evidence, kind, path: pathValue, symbol });
    }
  }

  for (const sourceFile of sourceFiles) {
    let contents;
    try {
      contents = fs.readFileSync(path.join(projectRoot, sourceFile), 'utf8');
    } catch (error) {
      errors.push({ path: sourceFile, message: error.message });
      continue;
    }
    const declaration = /(?:^|[;\n])\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?(function|class|interface|type|const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)/gm;
    for (let match = declaration.exec(contents); match; match = declaration.exec(contents)) {
      add(sourceFile, match[2], [symbolEvidence(sourceFile, match[2])], match[1]);
    }
    const commonJs = /\b(?:module\.exports|exports)\.([A-Za-z_$][A-Za-z0-9_$]*)\s*=/g;
    for (let match = commonJs.exec(contents); match; match = commonJs.exec(contents)) {
      add(sourceFile, match[1], [symbolEvidence(sourceFile, match[1])]);
    }
  }

  for (const candidate of diagnosis.details.reuseCandidates || []) {
    for (const symbol of candidate.symbols || []) {
      add(candidate.path, symbol, candidate.evidence || [symbolEvidence(candidate.path, symbol)]);
    }
  }

  return { errors, symbols };
}

function findReuseMatches(searchTerms, symbols, reuseCandidates, requestedShapes) {
  const matches = [];
  const seen = new Set();

  function add(kind, pathValue, symbol, evidence) {
    const key = `${kind}\u0000${pathValue}\u0000${symbol || ''}`;
    if (!seen.has(key)) {
      seen.add(key);
      matches.push({ kind, path: pathValue, symbol, evidence });
    }
  }

  for (const observed of symbols) {
    if (
      hasSearchMatch(searchTerms, `${observed.path} ${observed.symbol}`)
      || hasExactReusableSymbol(searchTerms, observed, requestedShapes)
    ) {
      add('symbol', observed.path, observed.symbol, observed.evidence);
    }
  }
  for (const candidate of reuseCandidates) {
    if (hasSearchMatch(searchTerms, `${candidate.path} ${(candidate.symbols || []).join(' ')}`)) {
      add('reuse-candidate', candidate.path, null, candidate.evidence || []);
    }
  }
  return matches;
}

function hasExactReusableSymbol(searchTerms, observed, requestedShapes) {
  if (!searchTerms.includes(observed.symbol.toLowerCase())) {
    return false;
  }

  const shapesByKind = {
    class: ['shape', 'type'],
    const: ['function', 'helper'],
    function: ['function', 'helper'],
    interface: ['shape', 'type'],
    let: ['function', 'helper'],
    type: ['shape', 'type'],
    var: ['function', 'helper']
  };
  return (shapesByKind[observed.kind] || []).some((shape) => requestedShapes.includes(shape));
}

function hasSearchMatch(searchTerms, text) {
  const candidateTerms = new Set(extractSearchTerms(text));
  return searchTerms.filter((term) => candidateTerms.has(term)).length >= 2;
}

function extractSearchTerms(text) {
  const terms = new Set();
  const words = text.match(/[A-Za-z][A-Za-z0-9_$]*|[가-힣]+/g) || [];

  function addTerm(value) {
    if (value.length > 1 && !SEARCH_STOP_WORDS.has(value)) {
      terms.add(value);
      if (/^[a-z]+$/.test(value) && value.length > 3 && value.endsWith('s')) {
        terms.add(value.slice(0, -1));
      }
    }
  }

  for (const word of words) {
    addTerm(word.toLowerCase());
    for (const part of word.replace(/([a-z])([A-Z])/g, '$1 $2').split(/[^A-Za-z0-9_$가-힣]+/)) {
      addTerm(part.toLowerCase());
    }
  }
  return [...terms];
}

function deriveTestObligations(behavior) {
  const failureOutcome = behavior.observableFailureOutcome
    ? behavior.observableFailureOutcome.text
    : 'the required observable failure outcome';
  return [
    {
      case: 'empty-input',
      obligation: 'Define and verify the observable behavior for an empty input.',
      phase: 'pre-write'
    },
    {
      case: 'null',
      obligation: 'Define and verify the observable behavior for null or undefined input.',
      phase: 'pre-write'
    },
    {
      case: 'boundary-values',
      obligation: 'Define and verify values at and immediately around the relevant boundary.',
      phase: 'pre-write'
    },
    {
      case: 'concurrency',
      obligation: 'Verify repeated or concurrent requests do not corrupt observable behavior when state or I/O is involved.',
      phase: 'pre-write'
    },
    {
      case: 'failure-path',
      obligation: `Verify the requested failure path produces: ${failureOutcome}`,
      phase: 'pre-write'
    },
    {
      case: 'side-effects',
      obligation: 'Verify requested side effects occur once and unrequested persistence or external calls do not occur.',
      phase: 'pre-write'
    }
  ];
}

function describeRepositoryEvidence(diagnosis, repositoryAuthority) {
  if (!diagnosis || !diagnosis.details) {
    return null;
  }
  const details = diagnosis.details;
  const responsibilities = details.responsibilities || [];
  const executionEntries = packageEntryEvidence(responsibilities);
  return {
    diagnosisVerdict: diagnosis.verdict,
    executionEntries,
    executionPaths: repositoryAuthority.executionPaths,
    canonicalSsot: repositoryAuthority.canonicalSsot,
    responsibilities,
    boundaries: details.structure ? details.structure.boundaries : [],
    dependencyDirection: details.dependencyDirection,
    ssotCandidates: details.ssotCandidates || [],
    directoryHierarchy: details.structure ? details.structure.directories : [],
    reuseCandidates: details.reuseCandidates || []
  };
}

function copyDiagnosisRisks(diagnosis) {
  return (diagnosis.risks || []).map((risk) => ({
    code: risk.code,
    evidence: risk.evidence || [],
    message: risk.message,
    severity: risk.severity
  }));
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
      const absolutePath = path.join(directory, entry.name);
      const relativePath = relativeDirectory ? `${relativeDirectory}/${entry.name}` : entry.name;
      const metadata = fs.lstatSync(absolutePath);
      if (entry.isSymbolicLink()) {
        update('symlink');
        update(relativePath);
        update(metadata.mode & 0o7777);
        update(fs.readlinkSync(absolutePath));
      } else if (entry.isDirectory()) {
        update('directory');
        update(relativePath);
        update(metadata.mode & 0o7777);
        if (!IGNORED_DIRECTORIES.has(entry.name)) {
          visit(absolutePath, relativePath);
        }
      } else if (entry.isFile()) {
        const contents = fs.readFileSync(absolutePath);
        update('file');
        update(relativePath);
        update(metadata.mode & 0o7777);
        update(contents.length);
        hash.update(contents);
        hash.update('\u0000');
        fileCount += 1;
      } else {
        update('other');
        update(relativePath);
        update(metadata.mode & 0o7777);
      }
    }
  }

  try {
    const root = fs.statSync(projectRoot);
    if (!root.isDirectory()) {
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

function projectStateRisk(state, stage) {
  return issue(
    'inconclusive',
    'unreadable-project-source',
    `The project source could not be read ${stage.replace('-', ' ')}.`,
    [fileEvidence('.', state.error)]
  );
}

function sourceStateEvidence(state) {
  return {
    digest: state.digest || null,
    fileCount: state.fileCount || 0,
    kind: 'source-state'
  };
}

function stableSourceState(beforeState, afterState) {
  if (!beforeState || !afterState || !beforeState.digest || beforeState.digest !== afterState.digest) {
    return null;
  }
  return {
    digest: afterState.digest,
    fileCount: afterState.fileCount
  };
}

function copySourceState(state) {
  return state ? { digest: state.digest, fileCount: state.fileCount } : null;
}

function sortRisks(risks) {
  return [...risks].sort((left, right) => {
    const order = RISK_ORDER[left.severity] - RISK_ORDER[right.severity];
    return order !== 0 ? order : left.code.localeCompare(right.code);
  });
}

function verdictForRisks(risks) {
  if (risks.some((risk) => risk.severity === 'fail')) {
    return 'FAIL';
  }
  if (risks.some((risk) => risk.severity === 'inconclusive')) {
    return 'INCONCLUSIVE';
  }
  return 'PASS';
}

function attemptWrite(assessment, gateOptions) {
  if (!isPlainObject(gateOptions)) {
    return deniedWrite(assessment, 'malformed-write-operation', 'Declarative write input is required.', 'INCONCLUSIVE');
  }
  if (assessment.verdict !== 'PASS') {
    return deniedWrite(assessment, 'admission-not-passed', 'The admission verdict does not allow file writes.', assessment.verdict);
  }

  const plannedWrites = prepareWritePlan(assessment.projectRoot, assessment.admittedScope, assessment.scopeKey, gateOptions.writes);
  if (plannedWrites.error) {
    return deniedWrite(assessment, plannedWrites.error.code, plannedWrites.error.message, 'INCONCLUSIVE');
  }

  const bindingProblem = validateWriteBinding(assessment, gateOptions);
  if (bindingProblem) {
    return deniedWrite(assessment, bindingProblem.code, bindingProblem.message, 'INCONCLUSIVE');
  }

  // This digest check is the final authorization step before any filesystem mutation.
  const currentState = assessment.projectRoot ? fingerprintProject(assessment.projectRoot) : null;
  if (!currentState || !currentState.digest || currentState.digest !== assessment.currentDigest) {
    return deniedWrite(assessment, 'stale-source', 'The project source differs from the state currently authorized by this admission session.', 'INCONCLUSIVE');
  }

  try {
    applyWritePlan(plannedWrites.plan);
  } catch (error) {
    recordCurrentSourceState(assessment, null);
    return deniedWrite(assessment, 'write-failed', `The mediated write could not be completed: ${error.message}`, 'INCONCLUSIVE');
  }

  const updatedState = fingerprintProject(assessment.projectRoot);
  if (!updatedState.digest) {
    recordCurrentSourceState(assessment, null);
    return deniedWrite(assessment, 'write-state-unreadable', 'The project source could not be read after the mediated write.', 'INCONCLUSIVE');
  }

  recordCurrentSourceState(assessment, updatedState);
  return {
    allowed: true,
    verdict: 'PASS',
    admission: assessment.result,
    currentSourceState: copySourceState(updatedState),
    writes: plannedWrites.plan.map((write) => write.relativePath)
  };
}

function validateWriteBinding(assessment, gateOptions) {
  const requestText = typeof gateOptions.request === 'string' ? normalizeText(gateOptions.request) : '';
  if (!requestText || requestText.toLowerCase() !== assessment.intentKey) {
    return writeProblem('changed-intent', 'The request intent differs from the admitted intent.');
  }

  const suppliedScope = normalizeProgrammaticScope(
    gateOptions.scope,
    Object.hasOwn(gateOptions, 'scope') && gateOptions.scope !== undefined,
    assessment.projectRoot
  );
  if (suppliedScope.error) {
    return writeProblem('changed-scope', 'The supplied scope is not a safe admitted project path.');
  }
  if (!suppliedScope.scope) {
    return null;
  }

  const gateScope = assessment.inferredScope ? narrowScope(assessment.inferredScope, suppliedScope.scope) : null;
  if (!gateScope || gateScope.key !== assessment.scopeKey) {
    return writeProblem('changed-scope', 'The supplied scope differs from the admitted scope.');
  }
  return null;
}

function prepareWritePlan(projectRoot, admittedScope, scopeKey, writes) {
  if (!Array.isArray(writes) || writes.length === 0) {
    return { error: writeProblem('missing-write-operations', 'At least one declarative file write is required.') };
  }
  if (!projectRoot || !admittedScope || !scopeKey) {
    return { error: writeProblem('unresolved-admitted-scope', 'No physical write scope was admitted for this request.') };
  }

  const plan = [];
  const paths = new Set();
  for (const operation of writes) {
    if (!isPlainObject(operation)) {
      return { error: writeProblem('malformed-write-operation', 'Each write must provide a relative path and text or bytes content.') };
    }
    const normalizedPath = normalizeRelativePath(operation.path);
    if (!normalizedPath.path) {
      return { error: writeProblem(writePathErrorCode(normalizedPath.error), 'A write path must be a safe relative project file path.') };
    }
    if (!scopeAllows(admittedScope, normalizedPath.path)) {
      return { error: writeProblem('out-of-scope-write', 'A requested file write is outside the admitted scope.') };
    }
    if (paths.has(normalizedPath.path)) {
      return { error: writeProblem('duplicate-write-path', 'A file can appear only once in a mediated write request.') };
    }
    if (plan.some((write) => {
      return normalizedPath.path.startsWith(`${write.relativePath}/`) || write.relativePath.startsWith(`${normalizedPath.path}/`);
    })) {
      return { error: writeProblem('conflicting-write-path', 'A mediated write cannot make one requested file the parent of another.') };
    }

    const content = normalizeWriteContent(operation.content);
    if (!content) {
      return { error: writeProblem('malformed-write-content', 'Write content must be text, a Buffer, or a Uint8Array.') };
    }
    const absolutePath = path.resolve(projectRoot, ...normalizedPath.path.split('/'));
    if (!isWithinProject(projectRoot, absolutePath)) {
      return { error: writeProblem('out-of-scope-write', 'A requested file write resolves outside the project directory.') };
    }
    const pathProblem = inspectSafeWriteTarget(projectRoot, normalizedPath.path);
    if (pathProblem) {
      return { error: pathProblem };
    }

    let existingMode = null;
    if (fs.existsSync(absolutePath)) {
      try {
        fs.accessSync(absolutePath, fs.constants.W_OK);
        existingMode = fs.statSync(absolutePath).mode & 0o777;
      } catch (error) {
        return { error: writeProblem('unwritable-write-target', 'An existing write target is not writable.') };
      }
    }

    paths.add(normalizedPath.path);
    plan.push({ absolutePath, content, existingMode, relativePath: normalizedPath.path });
  }
  return { error: null, plan };
}

function normalizeWriteContent(content) {
  if (typeof content === 'string') {
    return Buffer.from(content, 'utf8');
  }
  if (Buffer.isBuffer(content) || content instanceof Uint8Array) {
    return Buffer.from(content);
  }
  return null;
}

function inspectSafeWriteTarget(projectRoot, relativePath) {
  let rootStat;
  try {
    rootStat = fs.lstatSync(projectRoot);
  } catch (error) {
    return writeProblem('unreadable-project-source', 'The project root cannot be inspected for a safe write.');
  }
  if (rootStat.isSymbolicLink()) {
    return writeProblem('symlink-project-root', 'A symbolic-link project root cannot be used for mediated writes.');
  }
  if (!rootStat.isDirectory()) {
    return writeProblem('unsafe-project-root', 'The project root is not a directory.');
  }

  let currentPath = projectRoot;
  const segments = relativePath.split('/');
  for (let index = 0; index < segments.length; index += 1) {
    currentPath = path.join(currentPath, segments[index]);
    let entry;
    try {
      entry = fs.lstatSync(currentPath);
    } catch (error) {
      if (error && error.code === 'ENOENT') {
        return null;
      }
      return writeProblem('unreadable-write-path', 'A requested write path could not be inspected.');
    }

    if (entry.isSymbolicLink()) {
      return writeProblem('symlink-write-path', 'Mediated writes cannot follow symbolic links.');
    }
    if (index === segments.length - 1) {
      if (!entry.isFile()) {
        return writeProblem('special-write-target', 'Mediated writes may replace regular files only.');
      }
    } else if (!entry.isDirectory()) {
      return writeProblem('unsafe-write-parent', 'A requested write has a non-directory parent path.');
    }
  }
  return null;
}

function applyWritePlan(plan) {
  const transaction = crypto.randomUUID();
  const staged = [];
  const committed = [];
  const createdDirectories = [];

  try {
    for (let index = 0; index < plan.length; index += 1) {
      const write = plan[index];
      createMissingDirectories(path.dirname(write.absolutePath), createdDirectories);
      const temporaryPath = path.join(
        path.dirname(write.absolutePath),
        `.node-policy-${transaction}-${index}.pending`
      );
      const backupPath = path.join(
        path.dirname(write.absolutePath),
        `.node-policy-${transaction}-${index}.backup`
      );
      fs.writeFileSync(temporaryPath, write.content, { flag: 'wx' });
      if (write.existingMode !== null) {
        fs.chmodSync(temporaryPath, write.existingMode);
        fs.copyFileSync(write.absolutePath, backupPath, fs.constants.COPYFILE_EXCL);
      }
      staged.push({ ...write, backupPath, temporaryPath });
    }

    for (const write of staged) {
      fs.renameSync(write.temporaryPath, write.absolutePath);
      committed.push(write);
    }
  } catch (error) {
    const rollbackErrors = rollbackCommittedWrites(committed);
    cleanupWriteArtifacts(staged, createdDirectories);
    if (rollbackErrors.length > 0) {
      throw new Error(`${error.message}; rollback failed: ${rollbackErrors.join('; ')}`);
    }
    throw error;
  }

  cleanupWriteArtifacts(staged, []);
}

function createMissingDirectories(directory, createdDirectories) {
  const missing = [];
  let current = directory;
  while (!fs.existsSync(current)) {
    missing.push(current);
    current = path.dirname(current);
  }
  for (const directoryPath of missing.reverse()) {
    fs.mkdirSync(directoryPath);
    createdDirectories.push(directoryPath);
  }
}

function rollbackCommittedWrites(committed) {
  const errors = [];
  for (const write of [...committed].reverse()) {
    try {
      if (write.existingMode !== null) {
        fs.renameSync(write.backupPath, write.absolutePath);
      } else {
        fs.unlinkSync(write.absolutePath);
      }
    } catch (error) {
      errors.push(`${write.relativePath}: ${error.message}`);
    }
  }
  return errors;
}

function cleanupWriteArtifacts(staged, createdDirectories) {
  for (const write of staged) {
    for (const artifact of [write.temporaryPath, write.backupPath]) {
      try {
        fs.unlinkSync(artifact);
      } catch (error) {
        if (!error || error.code !== 'ENOENT') {
          // Cleanup is best-effort after the authoritative target state is restored.
        }
      }
    }
  }
  for (const directory of [...createdDirectories].reverse()) {
    try {
      fs.rmdirSync(directory);
    } catch (error) {
      if (!error || !['ENOENT', 'ENOTEMPTY'].includes(error.code)) {
        // Leave a concurrently populated directory intact.
      }
    }
  }
}

function recordCurrentSourceState(assessment, state) {
  assessment.currentDigest = state && state.digest ? state.digest : null;
  assessment.result.details.binding.currentSourceState = copySourceState(state);
}

function writePathErrorCode(error) {
  const codes = {
    'absolute-path': 'absolute-write-path',
    'reserved-path': 'reserved-write-path',
    'traversal-path': 'traversal-write-path'
  };
  return codes[error] || 'invalid-write-path';
}

function isWithinProject(projectRoot, candidatePath) {
  const relativePath = path.relative(path.resolve(projectRoot), path.resolve(candidatePath));
  return relativePath === '' || (!relativePath.startsWith(`..${path.sep}`) && relativePath !== '..' && !path.isAbsolute(relativePath));
}

function writeProblem(code, message) {
  return { code, message };
}

function deniedWrite(assessment, code, message, verdict) {
  return {
    allowed: false,
    verdict,
    admission: assessment.result,
    reason: { code, message }
  };
}

function issue(severity, code, message, evidence) {
  return { code, evidence, message, severity };
}

function fileEvidence(filePath, error) {
  return error ? { error, kind: 'file', path: filePath } : { kind: 'file', path: filePath };
}

function symbolEvidence(filePath, symbol) {
  return { kind: 'symbol', path: filePath, symbol };
}

function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

module.exports = { createAdmissionSession, resolveAdmissionCapability };
