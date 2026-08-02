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
 * @returns {{admission: object, attemptWrite: Function, finalGate: Function, behaviorProof: Function}}
 */
function createAdmissionSession(options, diagnoseProject, bindFinalGate, bindBehaviorProof) {
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
  const behaviorProofSession = typeof bindBehaviorProof === 'function'
    ? bindBehaviorProof(admissionCapability)
    : null;
  return Object.freeze({
    ...assessment.result,
    admission: assessment.result,
    attemptWrite(gateOptions) {
      return attemptWrite(assessment, gateOptions);
    },
    finalGate() {
      return finalGateSession.run();
    },
    behaviorProof(options) {
      if (!behaviorProofSession) {
        throw new TypeError('Behavior proof is unavailable for this admission session.');
      }
      return behaviorProofSession.run(options);
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
  let rootIdentity = null;
  let reinvestigation = {
    performed: false,
    reason: missingBehavior.length > 0 ? 'required-behavior-missing' : null,
    observed: null
  };

  if (input.projectRoot) {
    rootIdentity = captureDirectoryIdentity(input.projectRoot);
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
    diagnosis,
    projectRoot: input.projectRoot,
    rootIdentity,
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
    || /\bon\s+(failure|failures|error|errors|invalid)\b/i.test(sentence);
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

  const diagnosedAuthority = diagnosis.details.repositoryAuthority;
  if (diagnosedAuthority && Array.isArray(diagnosedAuthority.executionPaths)) {
    return authorityFromDiagnosis(diagnosedAuthority, diagnosis.details);
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
  const mainEvidence = entryEvidence.find((evidence) => evidence.key === 'main');
  const mainPath = mainEvidence ? resolveObservedEntryPath(mainEvidence.value, sourceFiles) : null;
  if (mainPath && executionPaths.includes(mainPath) && sourceCandidates.length === 0) {
    canonicalSsot = {
      evidence: [mainEvidence],
      path: mainPath,
      source: 'configured-main-entry'
    };
  } else if (bestScore > 0 && bestCandidates.length === 1) {
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

function authorityFromDiagnosis(authority, details) {
  const sourceFiles = details.structure && details.structure.sourceFiles || [];
  const observedPaths = new Set(sourceFiles);
  const rootExports = packageRootExportPaths(details.responsibilities || [], sourceFiles);
  const rootExportConfigured = packageHasRootExport(details.responsibilities || []);
  const rawExecutionPaths = rootExportConfigured
    ? rootExports
    : rootExports.length > 0
    ? rootExports
    : [...new Set(authority.executionPaths.filter((value) => typeof value === 'string'))];
  const executionPaths = [...new Set(rawExecutionPaths.filter((value) => {
    return !value.includes('*') && observedPaths.has(value);
  }))].sort();
  const risks = [];
  if (executionPaths.length === 0) {
    risks.push(issue(
      'inconclusive',
      'execution-path-unresolved',
      'Diagnosis did not establish a concrete package execution source.',
      authority.evidence || []
    ));
  } else if (executionPaths.length < rawExecutionPaths.length) {
    risks.push(issue(
      'inconclusive',
      'execution-entry-unresolved',
      'Diagnosis included a package execution entry that could not be resolved to observed source.',
      authority.evidence || []
    ));
  }

  const rootExportEvidence = packageEntryEvidence(details.responsibilities || []).find((evidence) => evidence.key === 'exports');
  const diagnosedCanonical = rootExportConfigured && rootExports.length === 1
    ? {
      evidence: rootExportEvidence ? [rootExportEvidence] : [],
      path: executionPaths[0],
      source: 'configured-exports-root'
    }
    : rootExportConfigured ? null : authority.canonicalSsot;
  const canonicalSsot = diagnosedCanonical
    && typeof diagnosedCanonical.path === 'string'
    && observedPaths.has(diagnosedCanonical.path)
    && !diagnosedCanonical.path.includes('*')
    ? { ...diagnosedCanonical }
    : null;
  if (!canonicalSsot) {
    risks.push(issue(
      'inconclusive',
      'canonical-ssot-unresolved',
      'Diagnosis did not establish one concrete canonical source of truth for the requested behavior.',
      authority.evidence || []
    ));
  }
  return { canonicalSsot, executionPaths, risks };
}

function packageRootExportPaths(responsibilities, sourceFiles) {
  const exportsEvidence = packageEntryEvidence(responsibilities).find((evidence) => evidence.key === 'exports');
  if (!exportsEvidence) {
    return [];
  }
  return [...new Set(collectPackageRootExportTargets(exportsEvidence.value)
    .map((entry) => resolveObservedEntryPath(entry, sourceFiles))
    .filter(Boolean))].sort();
}

function packageHasRootExport(responsibilities) {
  const exportsEvidence = packageEntryEvidence(responsibilities).find((evidence) => evidence.key === 'exports');
  if (!exportsEvidence) {
    return false;
  }
  const value = exportsEvidence.value;
  if (typeof value === 'string') {
    return true;
  }
  if (!isPlainObject(value)) {
    return false;
  }
  return Object.hasOwn(value, '.') || !Object.keys(value).some((key) => key.startsWith('.'));
}

function collectPackageRootExportTargets(value) {
  if (typeof value === 'string') {
    return [value];
  }
  if (!isPlainObject(value)) {
    return [];
  }
  if (Object.hasOwn(value, '.')) {
    return collectPackageConditionTargets(value['.']);
  }
  if (Object.keys(value).some((key) => key.startsWith('.'))) {
    return [];
  }
  return collectPackageConditionTargets(value);
}

function collectPackageConditionTargets(value) {
  if (typeof value === 'string') {
    return [value];
  }
  if (Array.isArray(value)) {
    return value.flatMap(collectPackageConditionTargets);
  }
  if (isPlainObject(value)) {
    return Object.entries(value)
      .filter(([key]) => key !== 'types')
      .flatMap(([, target]) => collectPackageConditionTargets(target));
  }
  return [];
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
  if (typeof entry !== 'string' || entry.length === 0 || entry.includes('\\') || path.posix.isAbsolute(entry) || path.win32.isAbsolute(entry) || /^[A-Za-z]:/.test(entry)) {
    return null;
  }
  const normalized = entry.replace(/^\.\//, '').replaceAll('\\', '/');
  if (normalized.split('/').some((segment) => !segment || segment === '.' || segment === '..')) {
    return null;
  }
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

function collectObservedSymbols(projectRoot, diagnosis, sourceFileState = null) {
  const symbols = [];
  const seen = new Set();
  const errors = sourceFileState ? [...sourceFileState.errors] : [];
  const sourceFiles = sourceFileState
    ? sourceFileState.files
    : diagnosis.details.structure.sourceFiles || [];

  function add(pathValue, symbol, evidence, kind = 'unknown') {
    const publicKey = symbol.publicKey || symbol.symbol || symbol;
    const symbolName = symbol.symbol || symbol;
    const key = `${pathValue}\u0000${publicKey}`;
    if (!seen.has(key)) {
      seen.add(key);
      symbols.push({
        evidence,
        kind: symbol.kind || kind,
        path: pathValue,
        publicKey,
        symbol: symbolName
      });
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
    const parsed = parseReusableSymbols(contents, sourceFile);
    if (parsed.error) {
      errors.push({ path: sourceFile, message: parsed.error });
      continue;
    }
    for (const symbol of parsed.symbols) {
      add(sourceFile, symbol, [symbol.evidence], symbol.kind);
    }
  }

  for (const candidate of diagnosis.details.reuseCandidates || []) {
    for (const symbol of candidate.symbols || []) {
      add(
        candidate.path,
        { publicKey: `export:${symbol}`, symbol },
        candidate.evidence || [symbolEvidence(candidate.path, symbol)]
      );
    }
  }

  return { errors, symbols };
}

function collectCurrentSourceFiles(projectRoot) {
  const files = [];
  const errors = [];

  function visit(directory, relativeDirectory) {
    let entries;
    try {
      entries = fs.readdirSync(directory, { withFileTypes: true });
    } catch (error) {
      errors.push({
        path: relativeDirectory || '.',
        message: error.message
      });
      return;
    }
    for (const entry of entries) {
      const absolutePath = path.join(directory, entry.name);
      const relativePath = relativeDirectory ? `${relativeDirectory}/${entry.name}` : entry.name;
      if (entry.isSymbolicLink()) {
        if (isReusableCodePath(relativePath)) {
          errors.push({ path: relativePath, message: 'A current source file is a symbolic link.' });
        }
      } else if (entry.isDirectory()) {
        if (!IGNORED_DIRECTORIES.has(entry.name)) {
          visit(absolutePath, relativePath);
        }
      } else if (entry.isFile() && isReusableCodePath(relativePath)) {
        files.push(relativePath);
      }
    }
  }

  visit(projectRoot, '');
  files.sort();
  return { errors, files };
}

function validatePlannedWriteReuse(assessment, plan) {
  const codeWrites = plan.filter((write) => isReusableCodePath(write.relativePath));
  if (codeWrites.length === 0) {
    return null;
  }
  const parser = loadAdmissionParser();
  if (parser.error) {
    return writeProblem('reuse-write-analysis-unavailable', `Proposed code writes cannot be safely analyzed: ${parser.error}`);
  }
  if (!assessment.diagnosis || !assessment.projectRoot) {
    return writeProblem('reuse-write-analysis-unavailable', 'Current reusable symbols cannot be established before a proposed code write.');
  }
  const currentSourceFiles = collectCurrentSourceFiles(assessment.projectRoot);
  const observed = collectObservedSymbols(assessment.projectRoot, assessment.diagnosis, currentSourceFiles);
  if (observed.errors.length > 0) {
    return writeProblem('reuse-write-analysis-unavailable', 'Current reusable symbols could not be completely established before a proposed code write.');
  }
  const currentBySymbol = new Map();
  for (const symbol of observed.symbols) {
    const publicKey = symbol.publicKey || `export:${symbol.symbol}`;
    let paths = currentBySymbol.get(publicKey);
    if (!paths) {
      paths = new Set();
      currentBySymbol.set(publicKey, paths);
    }
    paths.add(symbol.path);
  }
  const proposed = [];
  for (const write of codeWrites) {
    const parsed = parseReusableSymbols(write.content.toString('utf8'), write.relativePath);
    if (parsed.error) {
      return writeProblem('reuse-write-analysis-unavailable', `Proposed code write ${write.relativePath} could not be parsed: ${parsed.error}`);
    }
    for (const symbol of parsed.symbols) {
      const publicKey = symbol.publicKey || `export:${symbol.symbol}`;
      const currentPaths = currentBySymbol.get(publicKey) || new Set();
      if ([...currentPaths].some((currentPath) => currentPath !== write.relativePath)) {
        return writeProblem(
          'reuse-required-for-proposed-write-symbol',
          `The proposed write introduces reusable symbol ${symbol.symbol}, which already exists in observed source. Reuse or update the existing symbol instead.`
        );
      }
      const otherProposed = proposed.find((candidate) => candidate.publicKey === publicKey && candidate.path !== write.relativePath);
      if (otherProposed) {
        return writeProblem(
          'duplicate-proposed-write-symbol',
          `The proposed writes introduce reusable symbol ${symbol.symbol} more than once.`
        );
      }
      proposed.push({ path: write.relativePath, publicKey, symbol: symbol.symbol });
    }
  }
  return null;
}

function isReusableCodePath(filePath) {
  return typeof filePath === 'string' && /\.(?:cjs|mjs|jsx|js|cts|mts|tsx|ts)$/.test(filePath);
}

function loadAdmissionParser() {
  try {
    const parser = require('@babel/parser');
    if (typeof parser.parse !== 'function') {
      throw new TypeError('@babel/parser does not expose parse.');
    }
    return { error: null, parse: parser.parse };
  } catch (error) {
    return { error: error.message, parse: null };
  }
}

function parseReusableSymbols(contents, filePath) {
  const parser = loadAdmissionParser();
  if (parser.error) {
    return { error: parser.error, symbols: [] };
  }
  let ast;
  try {
    ast = parser.parse(contents, {
      plugins: admissionParserPlugins(filePath),
      ranges: true,
      sourceType: 'unambiguous'
    }).program;
  } catch (error) {
    return { error: error.message, symbols: [] };
  }

  const bindings = new Map();
  const classOwners = new Map();
  let moduleClassOwner = null;
  const symbols = [];
  const seen = new Set();
  function addSymbol(symbol, node, kind, publicKey = `export:${symbol}`) {
    if (!symbol || symbol === 'constructor' || !/^[A-Za-z_$][A-Za-z0-9_$]*$/.test(symbol)) {
      return;
    }
    const key = `${publicKey}\u0000${node.start || 0}`;
    if (seen.has(key)) {
      return;
    }
    seen.add(key);
    symbols.push({
      evidence: {
        column: node.loc && node.loc.start ? node.loc.start.column + 1 : 1,
        kind: 'symbol',
        line: node.loc && node.loc.start ? node.loc.start.line : 1,
        path: filePath,
        symbol
      },
      kind,
      publicKey,
      symbol
    });
  }

  function unwrapExpression(node) {
    let current = node;
    while (current && ['ParenthesizedExpression', 'TSAsExpression', 'TSTypeAssertion', 'TypeCastExpression'].includes(current.type)) {
      current = current.expression;
    }
    return current;
  }

  function registerDeclaration(node) {
    if (!node) {
      return;
    }
    if (['FunctionDeclaration', 'ClassDeclaration'].includes(node.type) && node.id) {
      bindings.set(node.id.name, {
        kind: node.type === 'ClassDeclaration' ? 'class' : 'function',
        node,
        name: node.id.name
      });
      return;
    }
    if (['TSInterfaceDeclaration', 'TSTypeAliasDeclaration', 'TSEnumDeclaration'].includes(node.type) && node.id) {
      bindings.set(node.id.name, { kind: 'type', node, name: node.id.name });
      return;
    }
    if (node.type !== 'VariableDeclaration') {
      return;
    }
    for (const declarator of node.declarations || []) {
      if (!declarator.id || declarator.id.type !== 'Identifier') {
        continue;
      }
      const init = unwrapExpression(declarator.init);
      let kind = 'value';
      let staticString = null;
      if (init && ['ArrowFunctionExpression', 'FunctionExpression'].includes(init.type)) {
        kind = 'function';
      } else if (init && init.type === 'ClassExpression') {
        kind = 'class';
      } else if (init && init.type === 'ObjectExpression') {
        kind = 'object';
      } else if (node.kind === 'const' && staticStringValue(init) !== null) {
        kind = 'constant-string';
        staticString = staticStringValue(init);
      }
      bindings.set(declarator.id.name, {
        init,
        kind,
        name: declarator.id.name,
        node: declarator,
        staticString
      });
    }
  }

  for (const statement of ast.body || []) {
    registerDeclaration(statement.type === 'ExportNamedDeclaration' ? statement.declaration : statement);
    if (statement.type === 'ExportDefaultDeclaration') {
      registerDeclaration(statement.declaration);
    }
  }

  function classMethodKey(owner, name) {
    return `class:${filePath}:${owner}.${name}`;
  }

  function objectMethodKey(owner, name) {
    return owner
      ? `object:${filePath}:${owner}.${name}`
      : `export:${name}`;
  }

  function addClassExport(exportName, bindingName, node, evidenceNode = node) {
    const classNode = node && node.type === 'ClassDeclaration' ? node : node;
    addSymbol(exportName, evidenceNode.id || evidenceNode, 'class', `export:${exportName}`);
    if (bindingName) {
      classOwners.set(bindingName, exportName);
    }
    for (const element of classNode.body && classNode.body.body || []) {
      if (!['ClassMethod', 'ClassPrivateMethod', 'ClassProperty', 'ClassPrivateProperty', 'ClassField'].includes(element.type)) {
        continue;
      }
      if (element.type.includes('Private')) {
        continue;
      }
      const name = admissionPropertyName(element.key);
      if (!name || name === 'constructor') {
        continue;
      }
      const value = unwrapExpression(element.value);
      if (['ClassProperty', 'ClassField'].includes(element.type) && value && !['ArrowFunctionExpression', 'FunctionExpression'].includes(value.type)) {
        continue;
      }
      addSymbol(name, element.key, 'method', classMethodKey(exportName, name));
    }
  }

  function addFunctionExport(exportName, node, publicKey = `export:${exportName}`) {
    addSymbol(exportName, node.id || node, 'function', publicKey);
  }

  function addTypeExport(exportName, node) {
    addSymbol(exportName, node.id || node, 'type', `export:${exportName}`);
  }

  function addBindingExport(exportName, bindingName, evidenceNode) {
    const binding = bindings.get(bindingName);
    if (!binding) {
      addSymbol(exportName, evidenceNode, 'function', `export:${exportName}`);
      return;
    }
    if (binding.kind === 'class') {
      addClassExport(exportName, bindingName, binding.node, evidenceNode || binding.node);
    } else if (binding.kind === 'function') {
      addFunctionExport(exportName, binding.node.id || binding.node, `export:${exportName}`);
    } else if (binding.kind === 'type') {
      addTypeExport(exportName, binding.node);
    } else if (binding.kind === 'object') {
      addSymbol(exportName, binding.node, 'object', `export:${exportName}`);
      collectObjectMembers(binding.init, exportName === 'default' ? 'default' : exportName);
    }
  }

  function addValueExport(exportName, valueNode, evidenceNode, publicKey = `export:${exportName}`) {
    const value = unwrapExpression(valueNode);
    if (!value) {
      return;
    }
    if (value.type === 'Identifier') {
      const binding = bindings.get(value.name);
      if (binding && binding.kind === 'class') {
        addClassExport(exportName, value.name, binding.node, evidenceNode || value);
      } else if (binding && binding.kind === 'function') {
        addSymbol(exportName, evidenceNode || value, 'function', publicKey);
      } else if (binding && binding.kind === 'object') {
        addSymbol(exportName, evidenceNode || value, 'object', publicKey);
        collectObjectMembers(binding.init, exportName);
      }
      return;
    }
    if (['FunctionExpression', 'ArrowFunctionExpression'].includes(value.type)) {
      addFunctionExport(exportName, value, publicKey);
    } else if (value.type === 'ClassExpression') {
      addClassExport(exportName, null, value, evidenceNode || value);
    } else if (value.type === 'ObjectExpression') {
      addSymbol(exportName, evidenceNode || value, 'object', publicKey);
      collectObjectMembers(value, exportName);
    }
  }

  function collectObjectMembers(objectNode, owner) {
    if (!objectNode || objectNode.type !== 'ObjectExpression') {
      return;
    }
    for (const property of objectNode.properties || []) {
      if (!['ObjectMethod', 'ObjectProperty'].includes(property.type)) {
        continue;
      }
      const name = admissionPropertyName(property.key);
      if (!name || name === 'constructor') {
        continue;
      }
      const publicKey = objectMethodKey(owner, name);
      if (property.type === 'ObjectMethod') {
        addSymbol(name, property.key, 'method', publicKey);
        continue;
      }
      const value = unwrapExpression(property.value);
      if (value && value.type === 'Identifier') {
        const binding = bindings.get(value.name);
        if (binding && binding.kind === 'class') {
          addSymbol(name, property.key, 'class', publicKey);
          classOwners.set(value.name, name);
          for (const element of binding.node.body && binding.node.body.body || []) {
            if (element.type !== 'ClassMethod' || admissionPropertyName(element.key) === 'constructor') {
              continue;
            }
            const methodName = admissionPropertyName(element.key);
            if (methodName) {
              addSymbol(methodName, element.key, 'method', classMethodKey(name, methodName));
            }
          }
        } else if (binding && binding.kind === 'function') {
          addSymbol(name, property.key, 'function', publicKey);
        } else if (binding && binding.kind === 'object') {
          addSymbol(name, property.key, 'object', publicKey);
          collectObjectMembers(binding.init, owner ? `${owner}.${name}` : name);
        }
      } else if (value && ['FunctionExpression', 'ArrowFunctionExpression'].includes(value.type)) {
        addSymbol(name, property.key, 'function', publicKey);
      } else if (value && value.type === 'ClassExpression') {
        addClassExport(name, null, value, property.key);
      } else if (value && value.type === 'ObjectExpression') {
        addSymbol(name, property.key, 'object', publicKey);
        collectObjectMembers(value, owner ? `${owner}.${name}` : name);
      }
    }
  }

  function addDefaultExport(node) {
    const declaration = unwrapExpression(node);
    if (!declaration) {
      return;
    }
    if (declaration.type === 'Identifier') {
      addBindingExport('default', declaration.name, declaration);
    } else if (declaration.type === 'ClassDeclaration') {
      addClassExport('default', declaration.id && declaration.id.name, declaration, declaration.id || declaration);
    } else if (declaration.type === 'FunctionDeclaration') {
      addFunctionExport('default', declaration, 'export:default');
    } else {
      addValueExport('default', declaration, declaration, 'export:default');
    }
  }

  function addNamedDeclaration(declaration) {
    if (!declaration) {
      return;
    }
    if (['FunctionDeclaration', 'ClassDeclaration'].includes(declaration.type) && declaration.id) {
      addBindingExport(declaration.id.name, declaration.id.name, declaration.id);
    } else if (['TSInterfaceDeclaration', 'TSTypeAliasDeclaration', 'TSEnumDeclaration'].includes(declaration.type) && declaration.id) {
      addTypeExport(declaration.id.name, declaration);
    } else if (declaration.type === 'VariableDeclaration') {
      for (const declarator of declaration.declarations || []) {
        if (declarator.id && declarator.id.type === 'Identifier') {
          addBindingExport(declarator.id.name, declarator.id.name, declarator.id);
        }
      }
    }
  }

  for (const statement of ast.body || []) {
    if (statement.type === 'ExportNamedDeclaration') {
      addNamedDeclaration(statement.declaration);
      for (const specifier of statement.specifiers || []) {
        if (specifier.type === 'ExportNamespaceSpecifier') {
          const exported = admissionPropertyName(specifier.exported);
          if (exported) {
            addSymbol(exported, specifier.exported, 'object', `export:${exported}`);
          }
          continue;
        }
        const exported = admissionPropertyName(specifier.exported);
        const local = admissionPropertyName(specifier.local);
        if (exported) {
          if (statement.source) {
            addSymbol(exported, specifier.exported, 'function', `reexport:${filePath}:${exported}`);
          } else if (local) {
            addBindingExport(exported, local, specifier.exported);
          }
        }
      }
    } else if (statement.type === 'ExportDefaultDeclaration') {
      addDefaultExport(statement.declaration);
    }
  }

  const assignments = [];
  let unresolvedComputedExport = false;
  for (const statement of ast.body || []) {
    visitAdmissionNode(statement, (node, ancestors) => {
      if (node.type !== 'AssignmentExpression' || node.operator !== '=') {
        return;
      }
      if (ancestors.some((ancestor) => [
        'ArrowFunctionExpression',
        'ClassMethod',
        'ClassPrivateMethod',
        'FunctionDeclaration',
        'FunctionExpression',
        'ObjectMethod'
      ].includes(ancestor.type))) {
        return;
      }
      if (hasUnresolvedCommonJsExportKey(node.left, bindings)) {
        unresolvedComputedExport = true;
      }
      assignments.push(node);
    });
  }

  function prototypeOwner(left) {
    if (!left || left.type !== 'MemberExpression') {
      return null;
    }
    const prototype = left.object;
    if (!prototype || prototype.type !== 'MemberExpression' || admissionPropertyName(prototype.property) !== 'prototype') {
      return null;
    }
    if (prototype.object.type === 'Identifier') {
      return classOwners.get(prototype.object.name) || null;
    }
    if (isModuleExportsAssignment(prototype.object, bindings)) {
      return moduleClassOwner;
    }
    const exportedClass = commonJsExportName(prototype.object, bindings);
    if (exportedClass && classOwners.has(exportedClass)) {
      return classOwners.get(exportedClass);
    }
    return null;
  }

  function addPrototypeAssignment(node) {
    const owner = prototypeOwner(node.left);
    const name = admissionPropertyName(node.left.property);
    if (!owner || !name || name === 'constructor') {
      return;
    }
    const value = unwrapExpression(node.right);
    if (value && value.type === 'Identifier') {
      const binding = bindings.get(value.name);
      if (!binding || binding.kind !== 'function') {
        return;
      }
    } else if (!value || !['FunctionExpression', 'ArrowFunctionExpression'].includes(value.type)) {
      return;
    }
    addSymbol(name, node.left.property || node.left, 'method', classMethodKey(owner, name));
  }

  function addCommonJsAssignment(node) {
    const target = commonJsExportName(node.left, bindings);
    if (target === 'module.exports') {
      const value = unwrapExpression(node.right);
      if (value && ['FunctionExpression', 'ArrowFunctionExpression'].includes(value.type)) {
        addFunctionExport(value.id && value.id.name ? value.id.name : 'default', value, `export:${value.id && value.id.name ? value.id.name : 'default'}`);
      } else if (value && value.type === 'ClassExpression') {
        const exportName = value.id && value.id.name ? value.id.name : 'default';
        addClassExport(exportName, null, value, value.id || value);
        moduleClassOwner = exportName;
      } else if (value && value.type === 'Identifier') {
        const binding = bindings.get(value.name);
        if (binding && binding.kind === 'class') {
          addBindingExport(value.name, value.name, value);
          moduleClassOwner = value.name;
        } else if (binding && binding.kind === 'function') {
          addBindingExport(value.name, value.name, value);
        } else if (binding && binding.kind === 'object') {
          collectObjectMembers(binding.init, null);
        }
      } else if (value && value.type === 'ObjectExpression') {
        collectObjectMembers(value, null);
      }
      return;
    }
    if (target) {
      addValueExport(target, node.right, node.left.property || node.left, `export:${target}`);
    }
  }

  for (const assignment of assignments) {
    if (!prototypeOwner(assignment.left)) {
      addCommonJsAssignment(assignment);
    }
  }
  for (const assignment of assignments) {
    if (prototypeOwner(assignment.left)) {
      addPrototypeAssignment(assignment);
    }
  }

  if (unresolvedComputedExport) {
    return {
      error: 'A computed CommonJS export key could not be resolved to a static string.',
      symbols: []
    };
  }
  return { error: null, symbols };
}

function admissionParserPlugins(filePath) {
  const plugins = [];
  if (/\.(?:cts|mts|tsx|ts)$/.test(filePath)) {
    plugins.push('typescript');
  }
  if (/\.(?:jsx|tsx)$/.test(filePath)) {
    plugins.push('jsx');
  }
  return plugins;
}

function visitAdmissionNode(node, visitor, ancestors = []) {
  if (!node || typeof node !== 'object' || typeof node.type !== 'string' || node.type.startsWith('Comment')) {
    return;
  }
  visitor(node, ancestors);
  for (const [key, value] of Object.entries(node)) {
    if (['comments', 'loc', 'start', 'end', 'extra', 'tokens', 'leadingComments', 'innerComments', 'trailingComments'].includes(key)) {
      continue;
    }
    if (value && typeof value === 'object' && typeof value.type === 'string') {
      visitAdmissionNode(value, visitor, [...ancestors, node]);
    } else if (Array.isArray(value)) {
      for (const item of value) {
        if (item && typeof item === 'object' && typeof item.type === 'string') {
          visitAdmissionNode(item, visitor, [...ancestors, node]);
        }
      }
    }
  }
}

function admissionPropertyName(node) {
  return node && node.type === 'Identifier'
    ? node.name
    : node && ['StringLiteral', 'Literal', 'NumericLiteral'].includes(node.type) && (typeof node.value === 'string' || typeof node.value === 'number')
      ? String(node.value)
      : null;
}

function staticStringValue(node) {
  if (node && ['StringLiteral', 'Literal'].includes(node.type) && typeof node.value === 'string') {
    return node.value;
  }
  if (node && node.type === 'TemplateLiteral' && node.expressions.length === 0 && node.quasis.length === 1) {
    return node.quasis[0].value.cooked;
  }
  return null;
}

function memberPropertyName(node, bindings) {
  if (!node) {
    return null;
  }
  if (!node.computed) {
    return admissionPropertyName(node.property);
  }
  const literal = node.property;
  if (literal && ['StringLiteral', 'Literal', 'NumericLiteral'].includes(literal.type)
    && (typeof literal.value === 'string' || typeof literal.value === 'number')) {
    return String(literal.value);
  }
  if (literal && literal.type === 'Identifier' && bindings) {
    const binding = bindings.get(literal.name);
    if (binding && binding.kind === 'constant-string') {
      return binding.staticString;
    }
  }
  return null;
}

function commonJsExportName(node, bindings) {
  if (!node || node.type !== 'MemberExpression') {
    return null;
  }
  const property = memberPropertyName(node, bindings);
  if (!property) {
    return null;
  }
  if (node.object && node.object.type === 'Identifier' && node.object.name === 'exports') {
    return property;
  }
  if (node.object && node.object.type === 'MemberExpression' &&
    node.object.object && node.object.object.type === 'Identifier' && node.object.object.name === 'module' &&
    memberPropertyName(node.object, bindings) === 'exports') {
    return property;
  }
  return isModuleExportsAssignment(node, bindings) ? 'module.exports' : null;
}

function isModuleExportsAssignment(node, bindings) {
  return Boolean(node && node.type === 'MemberExpression' && node.object && node.object.type === 'Identifier' &&
    node.object.name === 'module' && memberPropertyName(node, bindings) === 'exports');
}

function hasUnresolvedCommonJsExportKey(node, bindings) {
  if (!node || node.type !== 'MemberExpression' || !node.computed) {
    return false;
  }
  if (node.object && node.object.type === 'Identifier' && node.object.name === 'exports') {
    return !memberPropertyName(node, bindings);
  }
  return Boolean(node.object && node.object.type === 'MemberExpression'
    && isModuleExportsAssignment(node.object, bindings)
    && !memberPropertyName(node, bindings));
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
    method: ['function', 'helper'],
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

function fingerprintProject(projectRoot, ignoredPaths = new Set(), ignoredDirectories = new Set()) {
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
      const ignoredDirectory = ignoredDirectories.has(relativePath);
      if (ignoredPaths.has(relativePath) && !ignoredDirectory) {
        continue;
      }
      const metadata = fs.lstatSync(absolutePath);
      if (entry.isSymbolicLink()) {
        update('symlink');
        update(relativePath);
        update(metadata.mode & 0o7777);
        update(fs.readlinkSync(absolutePath));
      } else if (entry.isDirectory()) {
        if (!ignoredDirectory) {
          update('directory');
          update(relativePath);
          update(metadata.mode & 0o7777);
        }
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

function captureDirectoryIdentity(projectRoot) {
  try {
    const stat = fs.lstatSync(projectRoot);
    return stat.isDirectory() && !stat.isSymbolicLink()
      ? { dev: stat.dev, ino: stat.ino }
      : null;
  } catch (error) {
    return null;
  }
}

function fileIdentity(stat) {
  return { dev: stat.dev, ino: stat.ino };
}

function sameFileIdentity(left, right) {
  return Boolean(left && right && left.dev === right.dev && left.ino === right.ino);
}

function digestBuffer(contents) {
  return crypto.createHash('sha256').update(contents).digest('hex');
}

function sameFileMetadata(left, right) {
  return Boolean(left && right
    && left.mode === right.mode
    && left.size === right.size
    && left.mtimeNs === right.mtimeNs
    && left.ctimeNs === right.ctimeNs);
}

function sameFileState(left, right) {
  return Boolean(left && right
    && sameFileIdentity(left, right)
    && sameFileMetadata(left, right)
    && left.digest === right.digest);
}

function sameFileContentState(left, right) {
  return Boolean(left && right
    && sameFileIdentity(left, right)
    && left.mode === right.mode
    && left.size === right.size
    && left.mtimeNs === right.mtimeNs
    && left.digest === right.digest);
}

function readFileDescriptorState(fd) {
  const before = fs.fstatSync(fd);
  if (!before.isFile()) {
    throw new Error('A mediated file changed into a non-regular file while being read.');
  }
  const hash = crypto.createHash('sha256');
  const buffer = Buffer.alloc(64 * 1024);
  let position = 0;
  while (true) {
    const bytesRead = fs.readSync(fd, buffer, 0, buffer.length, position);
    if (bytesRead === 0) {
      break;
    }
    hash.update(buffer.subarray(0, bytesRead));
    position += bytesRead;
  }
  const after = fs.fstatSync(fd);
  if (!sameFileMetadata(fileStateMetadata(before), fileStateMetadata(after)) || after.size !== position) {
    throw new Error('A mediated file changed while its content was being read.');
  }
  return {
    ...fileStateMetadata(after),
    ...fileIdentity(after),
    digest: hash.digest('hex')
  };
}

function fileStateMetadata(stat) {
  return {
    ctimeNs: stat.ctimeNs,
    mode: stat.mode & 0o7777,
    mtimeNs: stat.mtimeNs,
    size: stat.size
  };
}

function readRegularFileState(filePath) {
  const fd = fs.openSync(filePath, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW);
  try {
    return readFileDescriptorState(fd);
  } finally {
    fs.closeSync(fd);
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

  const reuseProblem = validatePlannedWriteReuse(assessment, plannedWrites.plan);
  if (reuseProblem) {
    return deniedWrite(assessment, reuseProblem.code, reuseProblem.message, 'INCONCLUSIVE');
  }

  // This digest check is the final authorization step before any filesystem mutation.
  const currentState = assessment.projectRoot ? fingerprintProject(assessment.projectRoot) : null;
  if (!currentState || !currentState.digest || currentState.digest !== assessment.currentDigest) {
    return deniedWrite(assessment, 'stale-source', 'The project source differs from the state currently authorized by this admission session.', 'INCONCLUSIVE');
  }

  try {
    applyWritePlan(
      plannedWrites.plan,
      assessment.projectRoot,
      assessment.rootIdentity,
      assessment.currentDigest
    );
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

    const relativeDirectory = path.posix.dirname(normalizedPath.path) === '.'
      ? ''
      : path.posix.dirname(normalizedPath.path);
    const parentState = captureExistingParentIdentities(projectRoot, relativeDirectory);
    if (parentState.error) {
      return { error: parentState.error };
    }

    let existingMode = null;
    let existingIdentity = null;
    let existingState = null;
    try {
      const existing = fs.lstatSync(absolutePath);
      if (!existing.isFile()) {
        return { error: writeProblem('special-write-target', 'Mediated writes may replace regular files only.') };
      }
      fs.accessSync(absolutePath, fs.constants.W_OK);
      existingState = readRegularFileState(absolutePath);
      existingMode = existingState.mode;
      existingIdentity = fileIdentity(existingState);
    } catch (error) {
      if (!error || error.code !== 'ENOENT') {
        return { error: writeProblem('unreadable-write-target', 'An existing write target could not be authenticated.') };
      }
    }

    paths.add(normalizedPath.path);
    plan.push({
      absolutePath,
      content,
      contentDigest: digestBuffer(content),
      existingIdentity,
      existingMode,
      existingState,
      parentIdentities: parentState.identities,
      relativePath: normalizedPath.path
    });
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

function captureExistingParentIdentities(projectRoot, relativeDirectory) {
  const identities = [];
  if (!relativeDirectory) {
    return { error: null, identities };
  }

  let currentPath = projectRoot;
  for (const segment of relativeDirectory.split('/')) {
    currentPath = path.join(currentPath, segment);
    let entry;
    try {
      entry = fs.lstatSync(currentPath);
    } catch (error) {
      if (error && error.code === 'ENOENT') {
        return { error: null, identities };
      }
      return {
        error: writeProblem('unreadable-write-path', 'A requested write parent could not be authenticated.'),
        identities: []
      };
    }
    if (entry.isSymbolicLink() || !entry.isDirectory()) {
      return {
        error: writeProblem('unsafe-write-parent', 'A requested write parent is not a stable directory.'),
        identities: []
      };
    }
    identities.push({ identity: fileIdentity(entry), relativePath: identities.length ? `${identities.at(-1).relativePath}/${segment}` : segment });
  }
  return { error: null, identities };
}

function applyWritePlan(plan, projectRoot, rootIdentity, authorizedDigest) {
  assertSafeWriteCapability();
  const transaction = crypto.randomUUID();
  const staged = [];
  const createdDirectories = [];
  const handles = new Map();
  const rootFd = openDirectoryHandle(projectRoot, rootIdentity);
  handles.set('', { fd: rootFd, relativePath: '' });

  try {
    for (let index = 0; index < plan.length; index += 1) {
      const write = plan[index];
      const relativeDirectory = path.posix.dirname(write.relativePath) === '.' ? '' : path.posix.dirname(write.relativePath);
      const parent = openRelativeDirectoryHandle(
        handles,
        relativeDirectory,
        createdDirectories,
        transaction,
        write.parentIdentities
      );
      const name = path.posix.basename(write.relativePath);
      const targetPath = handlePath(parent.fd, name);
      const temporaryPath = handlePath(parent.fd, `.node-policy-${transaction}-${index}.pending`);
      const backupPath = handlePath(parent.fd, `.node-policy-${transaction}-${index}.backup`);
      const backupRelativePath = relativeDirectory
        ? `${relativeDirectory}/.node-policy-${transaction}-${index}.backup`
        : `.node-policy-${transaction}-${index}.backup`;
      const stagedWrite = {
        ...write,
        backupPath,
        backupRelativePath,
        backupState: 'none',
        parent,
        pendingFd: null,
        pendingIdentity: null,
        pendingState: null,
        recoveryPath: handlePath(parent.fd, `.node-policy-${transaction}-${index}.recovery`),
        recoveryRelativePath: relativeDirectory
          ? `${relativeDirectory}/.node-policy-${transaction}-${index}.recovery`
          : `.node-policy-${transaction}-${index}.recovery`,
        recoveryState: 'none',
        temporaryRelativePath: relativeDirectory
          ? `${relativeDirectory}/.node-policy-${transaction}-${index}.pending`
          : `.node-policy-${transaction}-${index}.pending`,
        targetPath,
        targetState: write.existingMode === null ? 'absent' : 'present',
        temporaryPath
      };
      staged.push(stagedWrite);
      createPendingFile(stagedWrite);
    }

    const ignoredPaths = new Set(staged.map((write) => write.temporaryRelativePath));
    const ignoredDirectories = new Set();
    for (const directory of createdDirectories) {
      ignoredPaths.add(directory.relativePath);
      ignoredDirectories.add(directory.relativePath);
    }
    const preCommitState = fingerprintProject(projectRoot, ignoredPaths, ignoredDirectories);
    if (!preCommitState.digest || preCommitState.digest !== authorizedDigest) {
      throw new Error('The project source changed before the mediated commit began.');
    }

    for (const write of staged) {
      verifyDirectoryHandle(write.parent, projectRoot);
      commitStagedWrite(write);
      verifyDirectoryHandle(write.parent, projectRoot);
    }
    for (const write of staged) {
      verifyCommittedTarget(write);
    }
  } catch (error) {
    const rollbackErrors = rollbackCommittedWrites(staged);
    cleanupWriteArtifacts(staged, createdDirectories);
    closeDirectoryHandles(handles);
    if (rollbackErrors.length > 0) {
      throw new Error(`${error.message}; rollback failed: ${rollbackErrors.join('; ')}`);
    }
    throw error;
  }

  cleanupWriteArtifacts(staged, []);
  closeDirectoryHandles(handles);
}

function assertSafeWriteCapability() {
  if (process.platform !== 'linux'
    || typeof fs.constants.O_NOFOLLOW !== 'number'
    || typeof fs.constants.O_DIRECTORY !== 'number'
    || typeof fs.fchmodSync !== 'function'
    || typeof fs.linkSync !== 'function') {
    throw new Error('Race-resistant mediated writes are unavailable on this platform.');
  }
  try {
    if (!fs.statSync('/proc/self/fd').isDirectory()) {
      throw new Error('The directory-handle path is unavailable.');
    }
  } catch (error) {
    throw new Error(`Race-resistant mediated writes are unavailable: ${error.message}`);
  }
}

function createPendingFile(write) {
  const flags = fs.constants.O_RDWR
    | fs.constants.O_CREAT
    | fs.constants.O_EXCL
    | fs.constants.O_NOFOLLOW;
  let fd;
  try {
    fd = fs.openSync(write.temporaryPath, flags, 0o666);
    let offset = 0;
    while (offset < write.content.length) {
      offset += fs.writeSync(fd, write.content, offset, write.content.length - offset);
    }
    if (write.existingMode !== null) {
      fs.fchmodSync(fd, write.existingMode);
    }
    write.pendingFd = fd;
    write.pendingState = readFileDescriptorState(fd);
    write.pendingIdentity = fileIdentity(write.pendingState);
    if (write.pendingState.digest !== write.contentDigest || write.pendingState.size !== write.content.length) {
      throw new Error('The mediated pending file does not contain the planned content.');
    }
  } catch (error) {
    if (fd !== undefined) {
      fs.closeSync(fd);
    }
    throw error;
  }
}

function commitStagedWrite(write) {
  verifyPendingFile(write);
  if (write.existingMode !== null) {
    const existingState = verifyExistingTarget(write);
    fs.renameSync(write.targetPath, write.backupPath);
    write.backupState = 'moved';
    const moved = readRegularFileState(write.backupPath);
    if (!sameFileState(moved, existingState) || !sameFileState(moved, write.existingState)) {
      const restoreError = restoreMovedTarget(write);
      throw new Error(restoreError
        ? `A mediated write target changed before commit; rollback failed: ${restoreError}`
        : 'A mediated write target changed before commit.');
    }
  }

  installPendingWithoutReplacement(write);
  verifyCommittedTarget(write);
  if (write.existingMode !== null) {
    const backupState = readRegularFileState(write.backupPath);
    if (!sameFileState(backupState, write.existingState)) {
      throw new Error('The existing target changed during the mediated commit.');
    }
  }
}

function verifyCommittedTarget(write) {
  let installed;
  try {
    installed = readRegularFileState(write.targetPath);
  } catch (error) {
    write.committedTargetMismatch = true;
    throw new Error(`The installed target could not be authenticated: ${error.message}`);
  }
  if (!sameFileContentState(installed, write.pendingState)
    || installed.digest !== write.contentDigest
    || installed.size !== write.content.length
    || (write.committedState && !sameFileState(installed, write.committedState))) {
    write.committedTargetMismatch = true;
    throw new Error('The installed target changed before the mediated commit completed.');
  }
  write.committedState = installed;
}

function verifyPendingFile(write) {
  const descriptorState = readFileDescriptorState(write.pendingFd);
  if (!sameFileState(descriptorState, write.pendingState)
    || descriptorState.digest !== write.contentDigest
    || descriptorState.size !== write.content.length) {
    throw new Error('A mediated pending file changed or no longer contains the planned content.');
  }
  const pathState = readRegularFileState(write.temporaryPath);
  if (!sameFileState(pathState, descriptorState)) {
    throw new Error('A mediated pending pathname changed before commit.');
  }
}

function verifyExistingTarget(write) {
  let targetState;
  try {
    targetState = readRegularFileState(write.targetPath);
  } catch (error) {
    if (error && error.code === 'ENOENT') {
      throw new Error('A mediated write target disappeared before commit.');
    }
    throw error;
  }
  if (!sameFileState(targetState, write.existingState)) {
    throw new Error('A mediated write target changed before commit.');
  }
  return targetState;
}

function installPendingWithoutReplacement(write) {
  if (write.existingMode === null) {
    try {
      fs.lstatSync(write.targetPath);
      throw new Error('A mediated write target appeared before commit.');
    } catch (error) {
      if (!error || error.code !== 'ENOENT') {
        throw error;
      }
    }
  }

  // Linking into the directory is a no-replace operation, unlike rename.
  fs.linkSync(write.temporaryPath, write.targetPath);
  const installed = readRegularFileState(write.targetPath);
  if (!sameFileContentState(installed, write.pendingState)
    || installed.digest !== write.contentDigest
    || installed.size !== write.content.length) {
    throw new Error('The mediated pending file could not be installed as a regular file.');
  }
  write.targetState = 'committed';
  fs.unlinkSync(write.temporaryPath);
}

function openDirectoryHandle(directory, expectedIdentity) {
  const fd = fs.openSync(directory, fs.constants.O_RDONLY | fs.constants.O_DIRECTORY | fs.constants.O_NOFOLLOW);
  try {
    const stat = fs.fstatSync(fd);
    if (!stat.isDirectory() || (expectedIdentity && (stat.dev !== expectedIdentity.dev || stat.ino !== expectedIdentity.ino))) {
      throw new Error('The canonical project root changed before the mediated write began.');
    }
    return fd;
  } catch (error) {
    fs.closeSync(fd);
    throw error;
  }
}

function openRelativeDirectoryHandle(handles, relativeDirectory, createdDirectories, transaction, expectedIdentities = []) {
  if (!relativeDirectory) {
    return handles.get('');
  }
  const expectedByPath = new Map(expectedIdentities.map((entry) => [entry.relativePath, entry.identity]));
  const segments = relativeDirectory.split('/');
  let current = '';
  for (const segment of segments) {
    const next = current ? `${current}/${segment}` : segment;
    const expectedIdentity = expectedByPath.get(next) || null;
    if (!handles.has(next)) {
      const parent = handles.get(current);
      if (!parent) {
        throw new Error('A mediated write parent directory could not be anchored.');
      }
      const childPath = handlePath(parent.fd, segment);
      let fd;
      try {
        fd = fs.openSync(childPath, fs.constants.O_RDONLY | fs.constants.O_DIRECTORY | fs.constants.O_NOFOLLOW);
      } catch (error) {
        if (!error || error.code !== 'ENOENT') {
          throw error;
        }
        if (expectedIdentity) {
          throw new Error(`A planned write parent disappeared before it could be opened: ${next}.`);
        }
        fs.mkdirSync(childPath, 0o755);
        createdDirectories.push({ path: childPath, relativePath: next });
        fd = fs.openSync(childPath, fs.constants.O_RDONLY | fs.constants.O_DIRECTORY | fs.constants.O_NOFOLLOW);
      }
      const opened = fs.fstatSync(fd);
      if (!opened.isDirectory() || (expectedIdentity && !sameFileIdentity(fileIdentity(opened), expectedIdentity))) {
        fs.closeSync(fd);
        throw new Error(`A planned write parent changed before it was opened: ${next}.`);
      }
      handles.set(next, { fd, relativePath: next });
    } else if (expectedIdentity) {
      const opened = fs.fstatSync(handles.get(next).fd);
      if (!opened.isDirectory() || !sameFileIdentity(fileIdentity(opened), expectedIdentity)) {
        throw new Error(`A planned write parent changed before it was reused: ${next}.`);
      }
    }
    current = next;
  }
  return handles.get(relativeDirectory);
}

function handlePath(fd, name = '') {
  return path.join('/proc/self/fd', String(fd), name);
}

function verifyDirectoryHandle(handle, projectRoot) {
  const expected = fs.fstatSync(handle.fd);
  const absolutePath = handle.relativePath
    ? path.join(projectRoot, ...handle.relativePath.split('/'))
    : projectRoot;
  const observed = fs.lstatSync(absolutePath);
  if (!observed.isDirectory() || observed.dev !== expected.dev || observed.ino !== expected.ino) {
    throw new Error(`A mediated write parent changed before commit: ${handle.relativePath || '.'}.`);
  }
}

function rollbackCommittedWrites(committed) {
  const errors = [];
  for (const write of [...committed].reverse()) {
    if (write.targetState === 'committed') {
      try {
        const target = fs.lstatSync(write.targetPath);
        if (sameFileIdentity(fileIdentity(target), write.pendingIdentity)) {
          if (write.committedTargetMismatch) {
            const recoveryError = preserveCommittedTarget(write);
            if (recoveryError) {
              errors.push(`${write.relativePath}: ${recoveryError}`);
            }
          }
          fs.unlinkSync(write.targetPath);
        } else {
          const recovery = write.backupState === 'moved'
            ? `; original target backup preserved at ${write.backupRelativePath}`
            : '';
          if (write.backupState === 'moved') {
            write.backupState = 'preserved';
          }
          errors.push(`${write.relativePath}: the committed target changed before rollback${recovery}`);
          continue;
        }
      } catch (error) {
        if (!error || error.code !== 'ENOENT') {
          const recovery = write.backupState === 'moved'
            ? `; original target backup preserved at ${write.backupRelativePath}`
            : '';
          if (write.backupState === 'moved') {
            write.backupState = 'preserved';
          }
          errors.push(`${write.relativePath}: ${error.message}${recovery}`);
          continue;
        }
      }
    }
    if (write.backupState === 'moved') {
      const restoreError = restoreMovedTarget(write);
      if (restoreError) {
        errors.push(`${write.relativePath}: ${restoreError}`);
      }
    }
  }
  return errors;
}

function preserveCommittedTarget(write) {
  if (write.recoveryState === 'preserved') {
    return `installed target recovery preserved at ${write.recoveryRelativePath}`;
  }
  try {
    fs.linkSync(write.targetPath, write.recoveryPath);
    write.recoveryState = 'preserved';
    return `installed target recovery preserved at ${write.recoveryRelativePath}`;
  } catch (error) {
    return `installed target recovery could not be preserved at ${write.recoveryRelativePath}: ${error.message}`;
  }
}

function restoreMovedTarget(write) {
  if (write.backupState !== 'moved') {
    return null;
  }
  try {
    fs.linkSync(write.backupPath, write.targetPath);
    fs.unlinkSync(write.backupPath);
    write.backupState = 'restored';
    write.targetState = 'present';
    return null;
  } catch (error) {
    if (error && error.code === 'EEXIST') {
      write.backupState = 'preserved';
      return `the concurrent target owns the pathname; original target backup preserved at ${write.backupRelativePath}`;
    }
    write.backupState = 'preserved';
    return `the original target could not be restored; backup preserved at ${write.backupRelativePath}: ${error.message}`;
  }
}

function cleanupWriteArtifacts(staged, createdDirectories) {
  for (const write of staged) {
    if (write.pendingFd !== null) {
      try {
        fs.closeSync(write.pendingFd);
      } catch (error) {
        // Descriptor cleanup is best effort after the transaction outcome is fixed.
      }
      write.pendingFd = null;
    }
    const artifacts = [write.temporaryPath];
    if (write.backupState !== 'preserved') {
      artifacts.push(write.backupPath);
    }
    if (write.recoveryState !== 'preserved') {
      artifacts.push(write.recoveryPath);
    }
    for (const artifact of artifacts) {
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
      fs.rmdirSync(directory.path);
    } catch (error) {
      if (!error || !['ENOENT', 'ENOTEMPTY'].includes(error.code)) {
        // Leave a concurrently populated directory intact.
      }
    }
  }
}

function closeDirectoryHandles(handles) {
  for (const handle of handles.values()) {
    try {
      fs.closeSync(handle.fd);
    } catch (error) {
      // The descriptor is best-effort cleanup after the transaction outcome is fixed.
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
