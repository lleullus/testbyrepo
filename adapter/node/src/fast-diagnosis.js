'use strict';

const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const SOURCE_EXTENSIONS = ['.cts', '.mts', '.tsx', '.jsx', '.ts', '.mjs', '.cjs', '.js'];
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
const DEFAULT_THRESHOLDS = Object.freeze({
  maxComplexity: 10,
  maxDepth: 2,
  maxFanIn: 10,
  maxFanOut: 10,
  maxFileLines: 300,
  maxFunctionLines: 50,
  maxReexports: 10
});
const CHECK_IDS = Object.freeze([
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
const THRESHOLD_FOR_CHECK = Object.freeze({
  'complexity': 'maxComplexity',
  'fan-in-concentration': 'maxFanIn',
  'fan-out-concentration': 'maxFanOut',
  'file-size': 'maxFileLines',
  'function-size': 'maxFunctionLines',
  'max-depth': 'maxDepth',
  're-export-concentration': 'maxReexports'
});
const FUNCTION_NODE_TYPES = new Set([
  'ArrowFunctionExpression',
  'ClassMethod',
  'ClassPrivateMethod',
  'FunctionDeclaration',
  'FunctionExpression',
  'ObjectMethod'
]);
const CONTROL_NODE_TYPES = new Set([
  'CatchClause',
  'ConditionalExpression',
  'DoWhileStatement',
  'ForInStatement',
  'ForOfStatement',
  'ForStatement',
  'IfStatement',
  'SwitchStatement',
  'TryStatement',
  'WhileStatement',
  'WithStatement'
]);
const ESLINT_RULE_THRESHOLDS = Object.freeze({
  'complexity': 'maxComplexity',
  'max-depth': 'maxDepth',
  'max-lines': 'maxFileLines',
  'max-lines-per-function': 'maxFunctionLines'
});
const UNSUPPORTED_LINT_CONFIGS = [
  '.eslintrc.cjs',
  '.eslintrc.js',
  '.eslintrc.yaml',
  '.eslintrc.yml',
  'eslint.config.cjs',
  'eslint.config.js',
  'eslint.config.mjs',
  'eslint.config.ts'
];
const CHILDLESS_KEYS = new Set([
  'comments',
  'end',
  'extra',
  'innerComments',
  'leadingComments',
  'loc',
  'start',
  'tokens',
  'trailingComments'
]);

/**
 * Runs the limited, read-only fast diagnosis for mechanically decidable source rules.
 * It intentionally never grants final completion approval.
 *
 * @param {string} projectDirectory directory to inspect
 * @param {{boundaryEvidence?: object, fixedThresholds?: object}} [options] fixed policy evidence captured before the diagnosis
 * @returns {object} a limited fast-diagnosis result
 */
function diagnoseFastProject(projectDirectory, options = {}) {
  if (typeof projectDirectory !== 'string' || projectDirectory.length === 0) {
    throw new TypeError('diagnoseFastProject requires a project directory path.');
  }

  const projectRoot = path.resolve(projectDirectory);
  const normalizedOptions = isPlainObject(options) ? options : {};
  const beforeScan = scanSourceFiles(projectRoot);
  const beforeState = sourceState(beforeScan);
  const thresholdState = resolveThresholds(projectRoot, normalizedOptions.fixedThresholds);
  const productFiles = beforeScan.files.filter((file) => !isTestFile(file.path));
  const parser = loadParser();
  let checks;
  let graph = null;
  let parsedFiles = [];
  let analysisFailure = null;

  if (beforeScan.errors.length > 0) {
    analysisFailure = {
      evidence: beforeScan.errors.map(scanErrorEvidence),
      message: 'The target source tree could not be read completely.'
    };
  } else if (!parser.parse) {
    analysisFailure = {
      evidence: [capabilityEvidence(parser.error)],
      message: 'The required JavaScript and TypeScript AST parser is unavailable.'
    };
  } else if (productFiles.length === 0) {
    analysisFailure = {
      evidence: [directoryEvidence('.')],
      message: 'No non-test JavaScript or TypeScript source file was observed.'
    };
  } else {
    const parsed = parseSourceFiles(productFiles, parser.parse);
    parsedFiles = parsed.files;
    if (parsed.errors.length > 0) {
      analysisFailure = {
        evidence: parsed.errors.map(parseErrorEvidence),
        message: 'At least one target source file could not be parsed into an AST.'
      };
    }
  }

  if (analysisFailure) {
    checks = unavailableChecks(analysisFailure.message, analysisFailure.evidence, thresholdState);
  } else {
    const typeScriptConfiguration = assessTypeScriptConfiguration(projectRoot, parsedFiles);
    graph = buildDependencyGraph(projectRoot, parsedFiles, typeScriptConfiguration);
    checks = collectChecks({
      files: parsedFiles,
      graph,
      options: normalizedOptions,
      projectRoot,
      thresholdState,
      typeScriptConfiguration,
      parser: parser.parse
    });
  }

  const afterState = sourceState(scanSourceFiles(projectRoot));
  checks.push(sourceStabilityCheck(beforeState, afterState));

  return createResult(projectRoot, checks, thresholdState, beforeState, afterState, parser.name, graph);
}

function collectChecks(context) {
  const functionDescriptors = context.files.flatMap(collectFunctionDescriptors);
  return [
    emptyCatchCheck(context.files),
    maxDepthCheck(context.files, functionDescriptors, context.thresholdState),
    functionSizeCheck(functionDescriptors, context.thresholdState),
    fileSizeCheck(context.files, context.thresholdState),
    complexityCheck(functionDescriptors, context.thresholdState),
    unreachableCodeCheck(context.files),
    deadCodeCheck(context.files),
    commentedOutCodeCheck(context.files, context.parser),
    reexportConcentrationCheck(context.files, context.thresholdState),
    fanInCheck(context.graph, context.thresholdState),
    fanOutCheck(context.graph, context.thresholdState),
    typeScriptStrictCheck(context.typeScriptConfiguration),
    asAnyCheck(context.files),
    asUnknownAsCheck(context.files),
    javaScriptJsdocCheck(context.files, functionDescriptors),
    circularDependencyCheck(context.graph),
    fixedBoundaryCheck(
      context.graph,
      context.options.boundaryEvidence,
      context.projectRoot,
      context.options.boundaryEvidenceError
    )
  ];
}

function emptyCatchCheck(files) {
  const violations = [];
  for (const file of files) {
    visitNode(file.ast, (node) => {
      if (node.type === 'CatchClause' && node.body && Array.isArray(node.body.body) && node.body.body.length === 0) {
        violations.push(sourceEvidence(file.path, node));
      }
    });
  }
  return violations.length > 0
    ? check('empty-catch', 'FAIL', 'Empty catch clauses discard an error without handling it.', violations)
    : check('empty-catch', 'PASS', 'No empty catch clause was observed.');
}

function maxDepthCheck(files, functionDescriptors, thresholdState) {
  const threshold = thresholdFor('max-depth', thresholdState);
  const violations = [];

  for (const file of files) {
    const moduleDepth = calculateMaxDepth(file.ast);
    if (moduleDepth.depth > threshold.effective) {
      violations.push({
        ...sourceEvidence(file.path, moduleDepth.node || file.ast),
        depth: moduleDepth.depth,
        subject: 'module'
      });
    }
  }
  for (const descriptor of functionDescriptors) {
    const depth = calculateMaxDepth(descriptor.node);
    if (depth.depth > threshold.effective) {
      violations.push({
        ...sourceEvidence(descriptor.file.path, depth.node || descriptor.node),
        depth: depth.depth,
        subject: descriptor.name
      });
    }
  }

  return thresholdCheck(
    'max-depth',
    violations,
    threshold,
    thresholdState,
    'No control-flow nesting exceeds the effective maximum depth.'
  );
}

function functionSizeCheck(functionDescriptors, thresholdState) {
  const threshold = thresholdFor('function-size', thresholdState);
  const violations = functionDescriptors
    .map((descriptor) => ({
      descriptor,
      lines: lineSpan(descriptor.node)
    }))
    .filter((item) => item.lines > threshold.effective)
    .map((item) => ({
      ...sourceEvidence(item.descriptor.file.path, item.descriptor.node),
      lines: item.lines,
      subject: item.descriptor.name
    }));

  return thresholdCheck(
    'function-size',
    violations,
    threshold,
    thresholdState,
    'No function exceeds the effective line limit.'
  );
}

function fileSizeCheck(files, thresholdState) {
  const threshold = thresholdFor('file-size', thresholdState);
  const violations = files
    .filter((file) => file.lineCount > threshold.effective)
    .map((file) => ({
      ...sourceEvidence(file.path, { loc: { start: { column: 0, line: Math.min(file.lineCount, threshold.effective + 1) } } }),
      lines: file.lineCount
    }));

  return thresholdCheck(
    'file-size',
    violations,
    threshold,
    thresholdState,
    'No source file exceeds the effective line limit.'
  );
}

function complexityCheck(functionDescriptors, thresholdState) {
  const threshold = thresholdFor('complexity', thresholdState);
  const violations = functionDescriptors
    .map((descriptor) => ({ descriptor, complexity: calculateComplexity(descriptor.node) }))
    .filter((item) => item.complexity.value > threshold.effective)
    .map((item) => ({
      ...sourceEvidence(item.descriptor.file.path, item.complexity.node || item.descriptor.node),
      complexity: item.complexity.value,
      subject: item.descriptor.name
    }));

  return thresholdCheck(
    'complexity',
    violations,
    threshold,
    thresholdState,
    'No function exceeds the effective cyclomatic-complexity limit.'
  );
}

function unreachableCodeCheck(files) {
  const violations = files.flatMap((file) => findUnreachableStatements(file).map((node) => sourceEvidence(file.path, node)));
  return violations.length > 0
    ? check('unreachable-code', 'FAIL', 'Statements after a terminating control-flow statement were observed.', violations)
    : check('unreachable-code', 'PASS', 'No mechanically unreachable statement was observed.');
}

function deadCodeCheck(files) {
  const violations = files.flatMap((file) => findUnusedTopLevelDeclarations(file).map((node) => sourceEvidence(file.path, node)));
  return violations.length > 0
    ? check('dead-code', 'FAIL', 'Unused private top-level declarations were observed.', violations)
    : check('dead-code', 'PASS', 'No mechanically unused private top-level declaration was observed.');
}

function commentedOutCodeCheck(files, parse) {
  const violations = [];
  for (const file of files) {
    for (const comment of file.comments) {
      if (commentedCode(comment, file, parse)) {
        violations.push(commentEvidence(file.path, comment));
      }
    }
  }
  return violations.length > 0
    ? check('commented-out-code', 'FAIL', 'Comments containing parseable source statements were observed.', violations)
    : check('commented-out-code', 'PASS', 'No mechanically detectable commented-out source statement was observed.');
}

function reexportConcentrationCheck(files, thresholdState) {
  const threshold = thresholdFor('re-export-concentration', thresholdState);
  const violations = [];
  for (const file of files) {
    const reexports = [];
    let hasExportAll = false;
    let reexportCount = 0;
    visitNode(file.ast, (node) => {
      if (!node.source || typeof node.source.value !== 'string') {
        return;
      }
      if (node.type === 'ExportAllDeclaration') {
        hasExportAll = true;
        reexports.push(node);
      } else if (node.type === 'ExportNamedDeclaration') {
        reexportCount += node.specifiers.length;
        reexports.push(...node.specifiers);
      }
    });
    if (hasExportAll || reexportCount > threshold.effective) {
      const observedCount = hasExportAll ? 'unbounded' : reexportCount;
      violations.push(...reexports.map((node) => ({
        ...sourceEvidence(file.path, node),
        reexports: observedCount
      })));
    }
  }
  return thresholdCheck(
    're-export-concentration',
    violations,
    threshold,
    thresholdState,
    'No module exceeds the effective re-export concentration limit.'
  );
}

function fanInCheck(graph, thresholdState) {
  const threshold = thresholdFor('fan-in-concentration', thresholdState);
  const incoming = new Map();
  for (const edge of graph.edges) {
    let sources = incoming.get(edge.to);
    if (!sources) {
      sources = new Map();
      incoming.set(edge.to, sources);
    }
    if (!sources.has(edge.from)) {
      sources.set(edge.from, edge);
    }
  }

  const violations = [];
  for (const sources of incoming.values()) {
    if (sources.size > threshold.effective) {
      violations.push(...[...sources.values()].map((edge) => ({
        ...edgeEvidence(edge),
        fanIn: sources.size
      })));
    }
  }
  return graphThresholdCheck(
    'fan-in-concentration',
    violations,
    threshold,
    thresholdState,
    graph,
    'No source module exceeds the effective fan-in concentration limit.'
  );
}

function fanOutCheck(graph, thresholdState) {
  const threshold = thresholdFor('fan-out-concentration', thresholdState);
  const outgoing = new Map();
  for (const edge of graph.edges) {
    let targets = outgoing.get(edge.from);
    if (!targets) {
      targets = new Map();
      outgoing.set(edge.from, targets);
    }
    if (!targets.has(edge.to)) {
      targets.set(edge.to, edge);
    }
  }

  const violations = [];
  for (const targets of outgoing.values()) {
    if (targets.size > threshold.effective) {
      violations.push(...[...targets.values()].map((edge) => ({
        ...edgeEvidence(edge),
        fanOut: targets.size
      })));
    }
  }
  return graphThresholdCheck(
    'fan-out-concentration',
    violations,
    threshold,
    thresholdState,
    graph,
    'No source module exceeds the effective fan-out concentration limit.'
  );
}

function typeScriptStrictCheck(configuration) {
  if (configuration.sources.length === 0) {
    return check('typescript-strict', 'PASS', 'No TypeScript source was observed.', [], { applicable: false });
  }

  const failures = [];
  const unknown = [];
  for (const source of configuration.sources) {
    if (source.status !== 'present') {
      unknown.push(configProblemEvidence(source));
    } else if (source.compilerOptions.strict !== true) {
      failures.push({
        ...configEvidence(source.configPath),
        sourceFile: source.path,
        value: Object.hasOwn(source.compilerOptions, 'strict') ? source.compilerOptions.strict : null
      });
    }
  }

  if (failures.length > 0) {
    return check('typescript-strict', 'FAIL', 'TypeScript source is not covered by strict: true.', failures);
  }
  if (unknown.length > 0) {
    return check('typescript-strict', 'INCONCLUSIVE', 'TypeScript strictness could not be established from required configuration.', unknown);
  }
  return check('typescript-strict', 'PASS', 'All observed TypeScript source is covered by strict: true.');
}

function asAnyCheck(files) {
  const violations = [];
  for (const file of files.filter((file) => isTypeScriptFile(file.path))) {
    visitNode(file.ast, (node) => {
      if (node.type === 'TSAsExpression' && node.typeAnnotation && node.typeAnnotation.type === 'TSAnyKeyword') {
        violations.push(sourceEvidence(file.path, node));
      }
    });
  }
  return violations.length > 0
    ? check('no-as-any', 'FAIL', 'Type assertions using as any were observed.', violations)
    : check('no-as-any', 'PASS', 'No as any assertion was observed.');
}

function asUnknownAsCheck(files) {
  const violations = [];
  for (const file of files.filter((file) => isTypeScriptFile(file.path))) {
    visitNode(file.ast, (node) => {
      if (
        node.type === 'TSAsExpression' &&
        node.expression &&
        node.expression.type === 'TSAsExpression' &&
        node.expression.typeAnnotation &&
        node.expression.typeAnnotation.type === 'TSUnknownKeyword'
      ) {
        violations.push(sourceEvidence(file.path, node));
      }
    });
  }
  return violations.length > 0
    ? check('no-as-unknown-as', 'FAIL', 'Double assertions using as unknown as were observed.', violations)
    : check('no-as-unknown-as', 'PASS', 'No as unknown as assertion was observed.');
}

function javaScriptJsdocCheck(files, functionDescriptors) {
  const javaScriptFiles = files.filter((file) => isJavaScriptFile(file.path));
  if (javaScriptFiles.length === 0) {
    return check('javascript-jsdoc', 'PASS', 'No JavaScript source was observed.', [], { applicable: false });
  }

  const violations = [];
  const unknown = [];
  for (const descriptor of functionDescriptors) {
    if (!isJavaScriptFile(descriptor.file.path) || !descriptor.public) {
      continue;
    }
    const contract = jsdocContract(descriptor);
    if (contract.status === 'inconclusive') {
      unknown.push(jsdocEvidence(descriptor, contract));
    } else if (contract.status === 'fail') {
      violations.push(jsdocEvidence(descriptor, contract));
    }
  }
  if (violations.length > 0) {
    return check(
      'javascript-jsdoc',
      'FAIL',
      'Public JavaScript functions require typed JSDoc entries for declared parameters and returned values.',
      violations
    );
  }
  if (unknown.length > 0) {
    return check(
      'javascript-jsdoc',
      'INCONCLUSIVE',
      'A public JavaScript function uses a parameter pattern that cannot be matched to JSDoc without inventing a name.',
      unknown
    );
  }
  return check('javascript-jsdoc', 'PASS', 'All observed public JavaScript functions expose their parameter and return contracts through JSDoc.');
}

function circularDependencyCheck(graph) {
  const cycles = findCycles(graph.files, graph.edges);
  const violations = cycles.flatMap((cycle) => cycle.edges.map(edgeEvidence));
  if (violations.length > 0) {
    return check('circular-dependencies', 'FAIL', 'Circular internal source dependencies were observed.', violations);
  }
  if (graph.unknown.length > 0) {
    return check(
      'circular-dependencies',
      'INCONCLUSIVE',
      'Internal dependency cycles could not be ruled out because some source dependencies could not be resolved.',
      graph.unknown.map(graphProblemEvidence)
    );
  }
  return check('circular-dependencies', 'PASS', 'No circular internal source dependency was observed.');
}

function fixedBoundaryCheck(graph, boundaryEvidence, projectRoot, boundaryEvidenceError) {
  if (boundaryEvidenceError) {
    return check(
      'fixed-boundaries',
      'INCONCLUSIVE',
      'Fixed boundary evidence could not be read or parsed.',
      [{
        kind: 'boundary-evidence',
        path: boundaryEvidenceError.path || 'boundaryEvidence',
        error: boundaryEvidenceError.message || 'Boundary evidence is unavailable.'
      }]
    );
  }
  const policy = validateBoundaryEvidence(boundaryEvidence, projectRoot);
  if (!policy.provided) {
    return check(
      'fixed-boundaries',
      'INCONCLUSIVE',
      'Fixed observed-boundary evidence was not supplied, so this required check could not be executed.',
      [{
        kind: 'boundary-evidence',
        path: 'boundaryEvidence',
        error: 'Fixed observed-boundary evidence was not supplied.'
      }]
    );
  }
  if (policy.error) {
    return check('fixed-boundaries', 'INCONCLUSIVE', policy.error.message, [policy.error.evidence]);
  }

  const violations = [];
  const uncovered = [];
  for (const edge of graph.edges) {
    const from = boundaryForFile(edge.from);
    const to = boundaryForFile(edge.to);
    const allowed = policy.allowed.get(from);
    if (!allowed) {
      uncovered.push(edge);
    } else if (!allowed.has(to)) {
      violations.push(edge);
    }
  }

  if (violations.length > 0) {
    return check(
      'fixed-boundaries',
      'FAIL',
      'An internal dependency violates the supplied fixed observed-boundary evidence.',
      violations.map((edge) => ({ ...edgeEvidence(edge), fromBoundary: boundaryForFile(edge.from), toBoundary: boundaryForFile(edge.to) })),
      { boundaryEvidenceSource: policy.source }
    );
  }
  if (uncovered.length > 0 || graph.unknown.length > 0) {
    return check(
      'fixed-boundaries',
      'INCONCLUSIVE',
      'The supplied fixed observed-boundary evidence does not cover every resolvable dependency.',
      [
        ...uncovered.map((edge) => edgeEvidence(edge)),
        ...graph.unknown.map(graphProblemEvidence)
      ],
      { boundaryEvidenceSource: policy.source }
    );
  }
  return check(
    'fixed-boundaries',
    'PASS',
    'All resolved internal dependencies conform to the supplied fixed observed-boundary evidence.',
    [],
    { boundaryEvidenceSource: policy.source }
  );
}

function sourceStabilityCheck(before, after) {
  if (before.digest && after.digest && before.digest === after.digest) {
    return check('target-source-stability', 'PASS', 'Target source bytes were identical before and after diagnosis.', [
      sourceStateEvidence(before)
    ]);
  }
  return check(
    'target-source-stability',
    'INCONCLUSIVE',
    'Target source bytes could not be confirmed identical before and after diagnosis.',
    [sourceStateEvidence(before), sourceStateEvidence(after)]
  );
}

function thresholdCheck(id, violations, threshold, thresholdState, passMessage) {
  if (violations.length > 0) {
    return check(id, 'FAIL', `${id} exceeds its effective safety threshold.`, violations, { threshold });
  }
  if (thresholdState.errors.length > 0) {
    return check(
      id,
      'INCONCLUSIVE',
      `${id} could not be fully evaluated because repository threshold configuration is unsupported or unreadable.`,
      thresholdState.errors.map(configProblemEvidence),
      { threshold }
    );
  }
  return check(id, 'PASS', passMessage, [], { threshold });
}

function graphThresholdCheck(id, violations, threshold, thresholdState, graph, passMessage) {
  const base = thresholdCheck(id, violations, threshold, thresholdState, passMessage);
  if (base.verdict === 'FAIL' || base.verdict === 'INCONCLUSIVE') {
    return base;
  }
  if (graph.unknown.length > 0) {
    return check(
      id,
      'INCONCLUSIVE',
      `${id} could not be fully evaluated because some source dependencies could not be resolved.`,
      graph.unknown.map(graphProblemEvidence),
      { threshold }
    );
  }
  return base;
}

function unavailableChecks(message, evidence, thresholdState) {
  return CHECK_IDS.map((id) => check(id, 'INCONCLUSIVE', message, evidence, thresholdMetadata(id, thresholdState)));
}

function check(id, verdict, message, evidence = [], extra = {}) {
  return { id, verdict, message, evidence, ...extra };
}

function createResult(projectRoot, checks, thresholdState, before, after, parserName, graph) {
  const verdict = aggregateVerdict(checks);
  const counts = { FAIL: 0, INCONCLUSIVE: 0, PASS: 0 };
  for (const item of checks) {
    counts[item.verdict] += 1;
  }
  const finalCompletion = {
    approved: false,
    status: 'NOT_FINAL',
    reason: 'Fast definitive-rule diagnosis is limited evidence and cannot approve final completion.'
  };
  const summary = {
    verdict,
    kind: 'limited-fast-definitive-rule-diagnosis',
    scope: 'mechanically-decidable-rules-only',
    completionApproval: false,
    checkCounts: counts,
    mainFindings: checks.filter((item) => item.verdict !== 'PASS').slice(0, 3)
  };

  return {
    kind: summary.kind,
    scope: summary.scope,
    completionApproval: false,
    finalCompletion,
    verdict,
    checks,
    summary,
    details: {
      ...summary,
      finalCompletion,
      projectRoot,
      checks,
      thresholds: thresholdState.values,
      thresholdConfiguration: {
        errors: thresholdState.errors,
        sources: thresholdState.sources
      },
      dependencyGraph: graph ? {
        edges: graph.edges,
        files: graph.files,
        unknown: graph.unknown
      } : null,
      parser: parserName,
      sourceReadback: {
        before: sourceStateEvidence(before),
        after: sourceStateEvidence(after),
        unchanged: Boolean(before.digest && after.digest && before.digest === after.digest)
      }
    }
  };
}

function aggregateVerdict(checks) {
  if (checks.some((item) => item.verdict === 'FAIL')) {
    return 'FAIL';
  }
  if (checks.some((item) => item.verdict === 'INCONCLUSIVE')) {
    return 'INCONCLUSIVE';
  }
  return 'PASS';
}

function loadParser() {
  try {
    const parser = require('@babel/parser');
    if (typeof parser.parse !== 'function') {
      throw new TypeError('@babel/parser does not expose parse.');
    }
    return { name: '@babel/parser', parse: parser.parse };
  } catch (error) {
    return { name: null, parse: null, error };
  }
}

function parseSourceFiles(files, parse) {
  const parsedFiles = [];
  const errors = [];
  for (const file of files) {
    try {
      const parsed = parse(file.contents, {
        attachComment: true,
        plugins: parserPlugins(file.path),
        ranges: true,
        sourceType: 'unambiguous'
      });
      parsedFiles.push({ ...file, ast: parsed.program, comments: parsed.comments || [] });
    } catch (error) {
      errors.push({
        column: error.loc && Number.isInteger(error.loc.column) ? error.loc.column + 1 : 1,
        line: error.loc && Number.isInteger(error.loc.line) ? error.loc.line : 1,
        message: error.message,
        path: file.path
      });
    }
  }
  return { errors, files: parsedFiles };
}

function parserPlugins(filePath) {
  const plugins = [];
  if (isTypeScriptFile(filePath)) {
    plugins.push('typescript');
  }
  if (/\.(jsx|tsx)$/.test(filePath)) {
    plugins.push('jsx');
  }
  return plugins;
}

function scanSourceFiles(projectRoot) {
  const files = [];
  const errors = [];
  let root;

  try {
    root = fs.statSync(projectRoot);
  } catch (error) {
    return { errors: [{ message: error.message, path: '.', type: 'project-root' }], files };
  }
  if (!root.isDirectory()) {
    return { errors: [{ message: 'The diagnosis target is not a directory.', path: '.', type: 'project-root' }], files };
  }

  function visit(directory) {
    let entries;
    try {
      entries = fs.readdirSync(directory, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name));
    } catch (error) {
      errors.push({ message: error.message, path: displayPath(projectRoot, directory), type: 'directory' });
      return;
    }

    for (const entry of entries) {
      const absolutePath = path.join(directory, entry.name);
      const relativePath = displayPath(projectRoot, absolutePath);
      if (entry.isSymbolicLink()) {
        errors.push({
          message: 'Symbolic links cannot be safely included in a complete source diagnosis.',
          path: relativePath,
          type: 'symbolic-link'
        });
        continue;
      }
      if (entry.isDirectory()) {
        if (!IGNORED_DIRECTORIES.has(entry.name)) {
          visit(absolutePath);
        }
        continue;
      }
      if (!entry.isFile() || !isSourceFile(relativePath)) {
        continue;
      }
      try {
        const contents = fs.readFileSync(absolutePath);
        files.push({
          absolutePath: path.resolve(absolutePath),
          contents: contents.toString('utf8'),
          path: relativePath,
          rawContents: contents,
          lineCount: physicalLineCount(contents.toString('utf8'))
        });
      } catch (error) {
        errors.push({ message: error.message, path: relativePath, type: 'source-file' });
      }
    }
  }

  visit(projectRoot);
  files.sort((left, right) => left.path.localeCompare(right.path));
  return { errors, files };
}

function sourceState(scan) {
  if (scan.errors.length > 0) {
    return { error: scan.errors.map((item) => `${item.path}: ${item.message}`).join('; '), fileCount: scan.files.length };
  }
  const hash = crypto.createHash('sha256');
  for (const file of scan.files) {
    hash.update(file.path);
    hash.update('\u0000');
    hash.update(String(file.rawContents.length));
    hash.update('\u0000');
    hash.update(file.rawContents);
    hash.update('\u0000');
  }
  return { digest: hash.digest('hex'), fileCount: scan.files.length };
}

function captureSourceState(projectDirectory) {
  return sourceState(scanSourceFiles(path.resolve(projectDirectory)));
}

function resolveThresholds(projectRoot, fixedThresholds) {
  const candidates = Object.fromEntries(Object.entries(DEFAULT_THRESHOLDS).map(([name, value]) => [name, []]));
  const errors = [];
  const sources = [];
  const packagePath = path.join(projectRoot, 'package.json');
  const packageDocument = readJsonFile(packagePath, false);

  if (packageDocument.status === 'invalid' || packageDocument.status === 'unreadable') {
    errors.push({ message: packageDocument.message, path: 'package.json', status: packageDocument.status });
  } else if (packageDocument.status === 'present') {
    sources.push({ path: 'package.json', status: 'read' });
    const packageValue = packageDocument.value;
    if (Object.hasOwn(packageValue, 'eslintConfig')) {
      collectEslintThresholds(packageValue.eslintConfig, 'package.json#eslintConfig', candidates, errors);
    }
    const checkerConfiguration = packageValue.nodePolicyChecker;
    if (checkerConfiguration !== undefined) {
      collectCheckerThresholds(checkerConfiguration, 'package.json#nodePolicyChecker', candidates, errors);
    }
  }

  for (const fileName of ['.eslintrc', '.eslintrc.json']) {
    const configPath = path.join(projectRoot, fileName);
    if (!fs.existsSync(configPath)) {
      continue;
    }
    const document = readJsonFile(configPath, true);
    if (document.status !== 'present') {
      errors.push({ message: document.message, path: fileName, status: document.status });
      continue;
    }
    sources.push({ path: fileName, status: 'read' });
    collectEslintThresholds(document.value, fileName, candidates, errors);
  }

  for (const fileName of UNSUPPORTED_LINT_CONFIGS) {
    if (fs.existsSync(path.join(projectRoot, fileName))) {
      errors.push({
        message: 'JavaScript or YAML ESLint configuration cannot be safely interpreted without executing project code.',
        path: fileName,
        status: 'unsupported'
      });
    }
  }

  collectFixedThresholds(fixedThresholds, candidates, errors);

  const values = {};
  for (const [name, defaultValue] of Object.entries(DEFAULT_THRESHOLDS)) {
    const configured = candidates[name];
    const stricter = configured.filter((candidate) => candidate.value < defaultValue);
    const effective = stricter.length === 0 ? defaultValue : Math.min(...stricter.map((candidate) => candidate.value));
    const source = stricter.length === 0
      ? 'checker-default'
      : stricter.find((candidate) => candidate.value === effective).source;
    values[name] = {
      default: defaultValue,
      effective,
      source,
      observed: configured.map((candidate) => ({
        ...candidate,
        applied: candidate.value === effective && candidate.value < defaultValue,
        ignored: candidate.value >= defaultValue
      }))
    };
  }
  return { errors, sources, values };
}

function collectFixedThresholds(configuration, candidates, errors) {
  if (configuration === undefined) {
    return;
  }
  if (!isPlainObject(configuration)) {
    errors.push({
      message: 'Fixed policy thresholds must be an object when supplied.',
      path: 'fixedThresholds',
      status: 'invalid'
    });
    return;
  }
  for (const thresholdName of Object.keys(DEFAULT_THRESHOLDS)) {
    if (!Object.hasOwn(configuration, thresholdName)) {
      continue;
    }
    const value = configuration[thresholdName];
    if (!Number.isSafeInteger(value) || value <= 0) {
      errors.push({
        message: `Fixed policy ${thresholdName} must be a positive integer.`,
        path: `fixedThresholds.${thresholdName}`,
        status: 'invalid'
      });
      continue;
    }
    candidates[thresholdName].push({ source: `fixed-policy.thresholds.${thresholdName}`, value });
  }
}

function collectEslintThresholds(configuration, source, candidates, errors) {
  if (!isPlainObject(configuration)) {
    errors.push({ message: 'ESLint configuration must be an object.', path: source, status: 'invalid' });
    return;
  }
  if (configuration.extends !== undefined) {
    errors.push({
      message: 'ESLint extends cannot be safely resolved by the fast diagnosis.',
      path: source,
      status: 'unsupported'
    });
  }
  if (Array.isArray(configuration.overrides) && configuration.overrides.length > 0) {
    errors.push({
      message: 'ESLint overrides cannot be safely applied without file-pattern evaluation.',
      path: source,
      status: 'unsupported'
    });
  }
  if (configuration.rules === undefined) {
    return;
  }
  if (!isPlainObject(configuration.rules)) {
    errors.push({ message: 'ESLint rules must be an object.', path: source, status: 'invalid' });
    return;
  }
  for (const [ruleName, thresholdName] of Object.entries(ESLINT_RULE_THRESHOLDS)) {
    if (!Object.hasOwn(configuration.rules, ruleName)) {
      continue;
    }
    const result = eslintLimit(configuration.rules[ruleName]);
    if (result.status === 'disabled') {
      continue;
    }
    if (result.status !== 'present') {
      errors.push({
        message: `The ${ruleName} rule must use a positive numeric limit or { max: number }.`,
        path: `${source}.rules.${ruleName}`,
        status: 'unsupported'
      });
      continue;
    }
    candidates[thresholdName].push({ source: `${source}.rules.${ruleName}`, value: result.value });
  }
}

function collectCheckerThresholds(configuration, source, candidates, errors) {
  if (!isPlainObject(configuration)) {
    errors.push({
      message: 'nodePolicyChecker must be an object when supplied.',
      path: source,
      status: 'invalid'
    });
    return;
  }
  if (configuration.fastDiagnosis === undefined) {
    return;
  }
  if (!isPlainObject(configuration.fastDiagnosis)) {
    errors.push({
      message: 'nodePolicyChecker.fastDiagnosis must be an object when supplied.',
      path: source,
      status: 'invalid'
    });
    return;
  }
  for (const thresholdName of Object.keys(DEFAULT_THRESHOLDS)) {
    if (!Object.hasOwn(configuration.fastDiagnosis, thresholdName)) {
      continue;
    }
    const value = configuration.fastDiagnosis[thresholdName];
    if (!Number.isSafeInteger(value) || value <= 0) {
      errors.push({
        message: `${thresholdName} must be a positive integer.`,
        path: `${source}.fastDiagnosis.${thresholdName}`,
        status: 'invalid'
      });
      continue;
    }
    candidates[thresholdName].push({ source: `${source}.fastDiagnosis.${thresholdName}`, value });
  }
}

function eslintLimit(value) {
  if (!Array.isArray(value) || value.length < 2) {
    return { status: 'invalid' };
  }
  const severity = value[0];
  if (severity === 0 || severity === 'off') {
    return { status: 'disabled' };
  }
  if (![1, 2, 'warn', 'warning', 'error'].includes(severity)) {
    return { status: 'invalid' };
  }
  const option = value[1];
  const limit = Number.isSafeInteger(option)
    ? option
    : isPlainObject(option) && Number.isSafeInteger(option.max)
      ? option.max
      : null;
  return limit && limit > 0 ? { status: 'present', value: limit } : { status: 'invalid' };
}

function assessTypeScriptConfiguration(projectRoot, files) {
  const sources = [];
  const cache = new Map();
  for (const file of files.filter((candidate) => isTypeScriptFile(candidate.path))) {
    const configPath = nearestTsconfig(projectRoot, file.absolutePath);
    if (!configPath) {
      sources.push({
        message: 'No containing tsconfig.json was found.',
        path: file.path,
        status: 'missing'
      });
      continue;
    }
    const resolved = resolveTsconfig(projectRoot, configPath, cache, new Set());
    if (resolved.status !== 'present') {
      sources.push({ ...resolved, configPath: displayPath(projectRoot, configPath), path: file.path });
      continue;
    }
    sources.push({
      compilerOptions: resolved.compilerOptions,
      configPath: displayPath(projectRoot, configPath),
      path: file.path,
      status: 'present'
    });
  }
  return { sources };
}

function nearestTsconfig(projectRoot, sourcePath) {
  let directory = path.dirname(sourcePath);
  const root = path.resolve(projectRoot);
  while (isWithin(root, directory)) {
    const candidate = path.join(directory, 'tsconfig.json');
    if (fs.existsSync(candidate)) {
      return candidate;
    }
    if (directory === root) {
      return null;
    }
    directory = path.dirname(directory);
  }
  return null;
}

function resolveTsconfig(projectRoot, configPath, cache, stack) {
  const normalized = path.resolve(configPath);
  if (cache.has(normalized)) {
    return cache.get(normalized);
  }
  if (stack.has(normalized)) {
    return { message: 'A tsconfig extends cycle was observed.', status: 'invalid' };
  }
  stack.add(normalized);
  const document = readJsonFile(normalized, true);
  if (document.status !== 'present') {
    const result = { message: document.message, status: document.status };
    cache.set(normalized, result);
    stack.delete(normalized);
    return result;
  }
  const value = document.value;
  let inherited = {};
  if (value.extends !== undefined) {
    if (typeof value.extends !== 'string' || !value.extends.startsWith('.')) {
      const result = { message: 'Only local relative tsconfig extends values are supported.', status: 'unsupported' };
      cache.set(normalized, result);
      stack.delete(normalized);
      return result;
    }
    const inheritedPath = resolveLocalConfig(path.dirname(normalized), value.extends);
    if (!inheritedPath || !isWithin(projectRoot, inheritedPath)) {
      const result = { message: 'The tsconfig extends target is missing or outside the target tree.', status: 'unsupported' };
      cache.set(normalized, result);
      stack.delete(normalized);
      return result;
    }
    const parent = resolveTsconfig(projectRoot, inheritedPath, cache, stack);
    if (parent.status !== 'present') {
      cache.set(normalized, parent);
      stack.delete(normalized);
      return parent;
    }
    inherited = parent.compilerOptions;
  }
  const compilerOptions = isPlainObject(value.compilerOptions) ? value.compilerOptions : {};
  const result = { compilerOptions: { ...inherited, ...compilerOptions }, status: 'present' };
  cache.set(normalized, result);
  stack.delete(normalized);
  return result;
}

function resolveLocalConfig(directory, extendsValue) {
  const base = path.resolve(directory, extendsValue);
  const candidates = path.extname(base) ? [base] : [base, `${base}.json`];
  return candidates.find((candidate) => fs.existsSync(candidate)) || null;
}

function buildDependencyGraph(projectRoot, files, typeScriptConfiguration) {
  const fileByAbsolutePath = new Map(files.map((file) => [file.absolutePath, file]));
  const configurationBySource = new Map(typeScriptConfiguration.sources.map((source) => [source.path, source]));
  const edges = [];
  const unknown = [];
  const edgeKeys = new Set();

  for (const file of files) {
    for (const reference of collectReferences(file)) {
      if (!reference.specifier) {
        unknown.push({ ...reference, message: 'A dynamic source dependency cannot be resolved mechanically.' });
        continue;
      }
      if (!isRelativeSpecifier(reference.specifier)) {
        const configuration = configurationBySource.get(file.path);
        if (
          configuration &&
          configuration.status === 'present' &&
          configuration.compilerOptions &&
          (typeof configuration.compilerOptions.baseUrl === 'string' || isPlainObject(configuration.compilerOptions.paths))
        ) {
          unknown.push({ ...reference, message: 'A TypeScript path-alias dependency cannot be resolved mechanically.' });
        }
        continue;
      }
      const resolution = resolveRelativeSource(projectRoot, file, reference.specifier, fileByAbsolutePath);
      if (resolution.status === 'source') {
        const key = `${file.path}\u0000${resolution.file.path}\u0000${reference.line}\u0000${reference.specifier}`;
        if (!edgeKeys.has(key)) {
          edgeKeys.add(key);
          edges.push({
            column: reference.column,
            from: file.path,
            kind: reference.kind,
            line: reference.line,
            specifier: reference.specifier,
            to: resolution.file.path
          });
        }
      } else if (resolution.status === 'missing' || resolution.status === 'outside') {
        unknown.push({ ...reference, message: 'A relative source dependency could not be resolved.' });
      }
    }
  }
  return { edges, files: files.map((file) => file.path), unknown };
}

function collectReferences(file) {
  const references = [];
  const seen = new Set();
  function add(node, specifier, kind) {
    const location = node.loc && node.loc.start;
    const reference = {
      column: location ? location.column + 1 : 1,
      kind,
      line: location ? location.line : 1,
      path: file.path,
      specifier
    };
    const key = `${reference.kind}\u0000${reference.line}\u0000${reference.column}\u0000${specifier || ''}`;
    if (!seen.has(key)) {
      seen.add(key);
      references.push(reference);
    }
  }

  visitNode(file.ast, (node) => {
    if (node.type === 'ImportDeclaration') {
      add(node.source || node, stringValue(node.source), 'import');
    } else if (node.type === 'ExportAllDeclaration' || (node.type === 'ExportNamedDeclaration' && node.source)) {
      add(node.source || node, stringValue(node.source), 'export-from');
    } else if (node.type === 'ImportExpression') {
      add(node.source || node, stringValue(node.source), 'dynamic-import');
    } else if (node.type === 'CallExpression' && node.callee && node.callee.type === 'Import') {
      add(node.arguments && node.arguments[0] ? node.arguments[0] : node, stringValue(node.arguments && node.arguments[0]), 'dynamic-import');
    } else if (
      node.type === 'CallExpression' &&
      node.callee &&
      node.callee.type === 'Identifier' &&
      node.callee.name === 'require'
    ) {
      add(node.arguments && node.arguments[0] ? node.arguments[0] : node, stringValue(node.arguments && node.arguments[0]), 'require');
    }
  });
  return references;
}

function resolveRelativeSource(projectRoot, file, specifier, fileByAbsolutePath) {
  const base = path.resolve(path.dirname(file.absolutePath), specifier);
  if (!isWithin(projectRoot, base)) {
    return { status: 'outside' };
  }
  for (const candidate of sourceCandidates(base)) {
    const source = fileByAbsolutePath.get(candidate);
    if (source) {
      return { file: source, status: 'source' };
    }
  }
  for (const candidate of artifactCandidates(base)) {
    try {
      if (fs.statSync(candidate).isFile()) {
        return { status: 'artifact' };
      }
    } catch (error) {
      // A missing candidate is handled after every supported resolution form is checked.
    }
  }
  return { status: 'missing' };
}

function sourceCandidates(basePath) {
  const extension = path.extname(basePath);
  const candidates = [path.resolve(basePath)];
  if (extension) {
    if (['.cjs', '.js', '.mjs'].includes(extension)) {
      const withoutExtension = basePath.slice(0, -extension.length);
      for (const sourceExtension of SOURCE_EXTENSIONS) {
        candidates.push(path.resolve(`${withoutExtension}${sourceExtension}`));
      }
    }
    return unique(candidates);
  }
  for (const sourceExtension of SOURCE_EXTENSIONS) {
    candidates.push(path.resolve(`${basePath}${sourceExtension}`));
    candidates.push(path.resolve(path.join(basePath, `index${sourceExtension}`)));
  }
  return unique(candidates);
}

function artifactCandidates(basePath) {
  const extension = path.extname(basePath);
  if (extension) {
    return [path.resolve(basePath)];
  }
  return [
    path.resolve(basePath),
    path.resolve(`${basePath}.json`),
    path.resolve(path.join(basePath, 'index.json'))
  ];
}

function findCycles(files, edges) {
  const adjacency = new Map(files.map((file) => [file, new Set()]));
  for (const edge of edges) {
    adjacency.get(edge.from).add(edge.to);
  }
  const indexes = new Map();
  const lowlinks = new Map();
  const stack = [];
  const onStack = new Set();
  const components = [];
  let index = 0;

  function visit(file) {
    indexes.set(file, index);
    lowlinks.set(file, index);
    index += 1;
    stack.push(file);
    onStack.add(file);
    for (const target of adjacency.get(file) || []) {
      if (!indexes.has(target)) {
        visit(target);
        lowlinks.set(file, Math.min(lowlinks.get(file), lowlinks.get(target)));
      } else if (onStack.has(target)) {
        lowlinks.set(file, Math.min(lowlinks.get(file), indexes.get(target)));
      }
    }
    if (lowlinks.get(file) !== indexes.get(file)) {
      return;
    }
    const members = [];
    let member;
    do {
      member = stack.pop();
      onStack.delete(member);
      members.push(member);
    } while (member !== file);
    const memberSet = new Set(members);
    const selfReference = members.length === 1 && (adjacency.get(members[0]) || new Set()).has(members[0]);
    if (members.length > 1 || selfReference) {
      components.push({
        edges: edges.filter((edge) => memberSet.has(edge.from) && memberSet.has(edge.to)),
        members: members.sort()
      });
    }
  }

  for (const file of files) {
    if (!indexes.has(file)) {
      visit(file);
    }
  }
  return components;
}

function validateBoundaryEvidence(value, projectRoot) {
  if (value === undefined) {
    return { provided: false };
  }
  if (!isPlainObject(value)) {
    return boundaryEvidenceError('Fixed boundary evidence must be an object.');
  }
  if (value.kind !== 'fixed-observed-boundaries') {
    return boundaryEvidenceError('Fixed boundary evidence must use kind: fixed-observed-boundaries.');
  }
  if (typeof value.source !== 'string' || value.source.trim().length === 0) {
    return boundaryEvidenceError('Fixed boundary evidence must identify its observed source.');
  }
  if (typeof value.projectRoot !== 'string' || path.resolve(value.projectRoot) !== path.resolve(projectRoot)) {
    return boundaryEvidenceError('Fixed boundary evidence must be bound to this project root.');
  }
  if (!Array.isArray(value.allowedDependencies)) {
    return boundaryEvidenceError('Fixed boundary evidence must provide allowedDependencies.');
  }
  const allowed = new Map();
  for (const item of value.allowedDependencies) {
    if (!isPlainObject(item) || !validBoundaryPath(item.from) || !validBoundaryPath(item.to)) {
      return boundaryEvidenceError('Each allowed dependency must provide safe relative from and to boundary paths.');
    }
    let targets = allowed.get(item.from);
    if (!targets) {
      targets = new Set();
      allowed.set(item.from, targets);
    }
    targets.add(item.to);
  }
  return { allowed, provided: true, source: value.source };
}

function boundaryEvidenceError(message) {
  return {
    error: { evidence: { kind: 'boundary-evidence', path: 'boundaryEvidence', source: null }, message },
    provided: true
  };
}

function validBoundaryPath(value) {
  return value === '.' || (typeof value === 'string' && value.length > 0 && !path.isAbsolute(value) && !value.split('/').some((part) => !part || part === '.' || part === '..'));
}

function boundaryForFile(filePath) {
  const segments = filePath.split('/');
  if (segments.length === 1) {
    return '.';
  }
  const [first, second, third] = segments;
  if (['src', 'lib', 'app', 'server'].includes(first)) {
    return segments.length > 2 ? `${first}/${second}` : first;
  }
  if (first === 'packages' && second) {
    return segments.length > 3 ? `packages/${second}/${third}` : `packages/${second}`;
  }
  return first;
}

function collectFunctionDescriptors(file) {
  const descriptors = [];
  visitNode(file.ast, (node, ancestors) => {
    if (!isFunctionNode(node) || !node.body) {
      return;
    }
    const anchorStart = documentationAnchorStart(node, ancestors);
    descriptors.push({
      anchorStart,
      file,
      name: functionName(node, ancestors),
      node,
      public: isPublicJavaScriptFunction(file, node, ancestors)
    });
  });
  return descriptors;
}

function documentationAnchorStart(node, ancestors) {
  const starts = [node.start];
  for (const ancestor of ancestors) {
    if (
      [
        'ClassMethod',
        'ClassPrivateMethod',
        'AssignmentExpression',
        'ExportDefaultDeclaration',
        'ExportNamedDeclaration',
        'ObjectMethod',
        'VariableDeclaration'
      ].includes(ancestor.type) && Number.isInteger(ancestor.start)
    ) {
      starts.push(ancestor.start);
    }
  }
  return Math.min(...starts);
}

function functionName(node, ancestors) {
  if (node.id && node.id.type === 'Identifier') {
    return node.id.name;
  }
  for (const ancestor of [...ancestors].reverse()) {
    if (ancestor.type === 'VariableDeclarator' && ancestor.id && ancestor.id.type === 'Identifier') {
      return ancestor.id.name;
    }
    if (
      ['ClassMethod', 'ClassPrivateMethod', 'ObjectMethod'].includes(ancestor.type) &&
      ancestor.key &&
      ancestor.key.type === 'Identifier'
    ) {
      return ancestor.key.name;
    }
  }
  return 'anonymous function';
}

function isPublicJavaScriptFunction(file, node, ancestors) {
  if (!isJavaScriptFile(file.path) || ancestors.some(isFunctionNode)) {
    return false;
  }
  if (ancestors.some((ancestor) => ['ExportDefaultDeclaration', 'ExportNamedDeclaration'].includes(ancestor.type))) {
    return true;
  }
  if (ancestors.some((ancestor) => ancestor.type === 'AssignmentExpression' && isCommonJsExportTarget(ancestor.left))) {
    return true;
  }
  const isTopLevel = ancestors[0] && ancestors[0].type === 'Program';
  return Boolean(
    isTopLevel &&
    (
      node.type === 'FunctionDeclaration' ||
      ancestors.some((ancestor) => ['ClassMethod', 'ClassPrivateMethod', 'VariableDeclarator'].includes(ancestor.type))
    )
  );
}

function isCommonJsExportTarget(node) {
  if (!node || node.type !== 'MemberExpression') {
    return false;
  }
  if (node.object && node.object.type === 'Identifier' && node.object.name === 'exports') {
    return true;
  }
  return (
    node.object &&
    node.object.type === 'MemberExpression' &&
    node.object.object &&
    node.object.object.type === 'Identifier' &&
    node.object.object.name === 'module' &&
    propertyName(node.object.property) === 'exports'
  );
}

function jsdocContract(descriptor) {
  const parameters = declaredParameters(descriptor.node.params);
  const requiresReturn = functionReturnsValue(descriptor.node);
  const comment = immediateJsdocComment(descriptor);
  if (!comment) {
    return {
      evidenceNode: descriptor.node,
      missingParameters: parameters.names,
      missingReturn: requiresReturn,
      status: 'fail'
    };
  }
  const tags = jsdocTags(comment);
  const missingParameters = parameters.names.filter((name) => !tags.parameters.has(name));
  if (missingParameters.length > 0 || (requiresReturn && !tags.hasReturn)) {
    return {
      evidenceNode: comment,
      missingParameters,
      missingReturn: requiresReturn && !tags.hasReturn,
      status: 'fail'
    };
  }
  if (parameters.unsupported) {
    return {
      evidenceNode: comment,
      missingParameters,
      missingReturn: requiresReturn && !tags.hasReturn,
      status: 'inconclusive'
    };
  }
  return { status: 'pass' };
}

function jsdocEvidence(descriptor, contract) {
  return {
    ...sourceEvidence(descriptor.file.path, contract.evidenceNode || descriptor.node),
    subject: descriptor.name,
    ...(contract.missingParameters && contract.missingParameters.length > 0
      ? { missingParameters: contract.missingParameters }
      : {}),
    ...(contract.missingReturn ? { missingReturn: true } : {})
  };
}

function immediateJsdocComment(descriptor) {
  const matching = descriptor.file.comments
    .filter((comment) => {
      return comment.type === 'CommentBlock' &&
        typeof comment.value === 'string' &&
        comment.value.trimStart().startsWith('*') &&
        comment.end <= descriptor.anchorStart;
    })
    .sort((left, right) => right.end - left.end)[0];
  if (!matching) {
    return null;
  }
  const between = descriptor.file.contents.slice(matching.end, descriptor.anchorStart);
  return /^\s*$/.test(between) && matching.value.replace(/^\s*\*/, '').trim().length > 0
    ? matching
    : null;
}

function declaredParameters(parameters) {
  const names = [];
  let unsupported = false;
  for (const parameter of parameters) {
    const name = declaredParameterName(parameter);
    if (name === null) {
      unsupported = true;
    } else {
      names.push(name);
    }
  }
  return { names, unsupported };
}

function declaredParameterName(parameter) {
  if (parameter.type === 'Identifier') {
    return parameter.name;
  }
  if (parameter.type === 'AssignmentPattern') {
    return declaredParameterName(parameter.left);
  }
  if (parameter.type === 'RestElement') {
    return declaredParameterName(parameter.argument);
  }
  return null;
}

function functionReturnsValue(node) {
  if (node.type === 'ArrowFunctionExpression' && node.body.type !== 'BlockStatement') {
    return true;
  }
  let returnsValue = false;
  function inspect(current) {
    if (!isAstNode(current) || (current !== node.body && isFunctionNode(current))) {
      return;
    }
    if (current.type === 'ReturnStatement' && current.argument !== null) {
      returnsValue = true;
    }
    forEachChild(current, inspect);
  }
  inspect(node.body);
  return returnsValue;
}

function jsdocTags(comment) {
  const text = comment.value
    .split(/\r?\n/)
    .map((line) => line.replace(/^\s*\*\s?/, ''))
    .join('\n');
  const matches = [...text.matchAll(/@([A-Za-z]+)\b/g)];
  const parameters = new Set();
  let hasReturn = false;
  for (let index = 0; index < matches.length; index += 1) {
    const match = matches[index];
    const tag = match[1].toLowerCase();
    const start = match.index + match[0].length;
    const end = index + 1 < matches.length ? matches[index + 1].index : text.length;
    const details = typedJsdocTag(text.slice(start, end));
    if (tag === 'param' && details.type && details.name) {
      parameters.add(details.name);
    } else if ((tag === 'return' || tag === 'returns') && details.type) {
      hasReturn = true;
    }
  }
  return { hasReturn, parameters };
}

function typedJsdocTag(value) {
  const text = value.trimStart();
  if (!text.startsWith('{')) {
    return { name: null, type: null };
  }
  let depth = 0;
  for (let index = 0; index < text.length; index += 1) {
    if (text[index] === '{') {
      depth += 1;
    } else if (text[index] === '}') {
      depth -= 1;
      if (depth === 0) {
        const type = text.slice(1, index).trim();
        const remainder = text.slice(index + 1).trimStart();
        return { name: jsdocParameterName(remainder), type: type || null };
      }
    }
  }
  return { name: null, type: null };
}

function jsdocParameterName(value) {
  const token = value.split(/\s+/)[0];
  if (!token) {
    return null;
  }
  const optional = token.startsWith('[') && token.endsWith(']') ? token.slice(1, -1) : token;
  return optional.replace(/^\.\.\./, '').split('=')[0] || null;
}

function calculateMaxDepth(root) {
  let depth = 0;
  let nodeAtDepth = null;
  walkMetric(root, root, 0, (node, currentDepth) => {
    if (isControlNode(node) && currentDepth > depth) {
      depth = currentDepth;
      nodeAtDepth = node;
    }
  });
  return { depth, node: nodeAtDepth };
}

function calculateComplexity(root) {
  let value = 1;
  let decisionNode = null;
  walkMetric(root, root, 0, (node) => {
    if (isComplexityDecision(node)) {
      value += 1;
      decisionNode = node;
    }
  });
  return { node: decisionNode, value };
}

function walkMetric(node, root, depth, visitor) {
  if (!isAstNode(node) || (node !== root && isFunctionNode(node))) {
    return;
  }
  const currentDepth = isControlNode(node) ? depth + 1 : depth;
  visitor(node, currentDepth);
  forEachChild(node, (child) => walkMetric(child, root, currentDepth, visitor));
}

function isControlNode(node) {
  return CONTROL_NODE_TYPES.has(node.type);
}

function isComplexityDecision(node) {
  return (
    ['CatchClause', 'ConditionalExpression', 'DoWhileStatement', 'ForInStatement', 'ForOfStatement', 'ForStatement', 'IfStatement', 'WhileStatement'].includes(node.type) ||
    (node.type === 'SwitchCase' && node.test !== null) ||
    (node.type === 'LogicalExpression' && ['&&', '||', '??'].includes(node.operator))
  );
}

function findUnreachableStatements(file) {
  const unreachable = [];
  visitNode(file.ast, (node) => {
    const statements = node.type === 'BlockStatement'
      ? node.body
      : node.type === 'SwitchCase'
        ? node.consequent
        : null;
    if (!Array.isArray(statements)) {
      return;
    }
    let terminated = false;
    for (const statement of statements) {
      if (terminated && statement.type !== 'FunctionDeclaration') {
        unreachable.push(statement);
      }
      if (statementTerminates(statement)) {
        terminated = true;
      }
    }
  });
  return unreachable;
}

function statementTerminates(node) {
  if (!node) {
    return false;
  }
  if (['BreakStatement', 'ContinueStatement', 'ReturnStatement', 'ThrowStatement'].includes(node.type)) {
    return true;
  }
  if (node.type === 'BlockStatement') {
    return statementTerminates(node.body[node.body.length - 1]);
  }
  if (node.type === 'IfStatement') {
    return Boolean(node.alternate && statementTerminates(node.consequent) && statementTerminates(node.alternate));
  }
  if (node.type === 'TryStatement' && node.finalizer) {
    return statementTerminates(node.finalizer);
  }
  return false;
}

function findUnusedTopLevelDeclarations(file) {
  const candidates = [];
  for (const statement of file.ast.body) {
    const exported = statement.type === 'ExportNamedDeclaration' || statement.type === 'ExportDefaultDeclaration';
    const declaration = exported ? statement.declaration : statement;
    if (!declaration || exported) {
      continue;
    }
    if (['ClassDeclaration', 'FunctionDeclaration'].includes(declaration.type) && declaration.id && declaration.id.type === 'Identifier') {
      candidates.push({ identifier: declaration.id, name: declaration.id.name });
    } else if (declaration.type === 'VariableDeclaration') {
      for (const declarator of declaration.declarations) {
        if (declarator.id && declarator.id.type === 'Identifier') {
          candidates.push({ identifier: declarator.id, name: declarator.id.name });
        }
      }
    }
  }
  if (candidates.length === 0) {
    return [];
  }
  const declarationStarts = new Set(candidates.map((candidate) => candidate.identifier.start));
  const usages = new Map(candidates.map((candidate) => [candidate.name, 0]));
  visitNode(file.ast, (node) => {
    if (node.type === 'Identifier' && usages.has(node.name) && !declarationStarts.has(node.start)) {
      usages.set(node.name, usages.get(node.name) + 1);
    }
  });
  return candidates.filter((candidate) => usages.get(candidate.name) === 0).map((candidate) => candidate.identifier);
}

function commentedCode(comment, file, parse) {
  if (comment.type === 'CommentBlock' && comment.value.trimStart().startsWith('*')) {
    return false;
  }
  const text = comment.value
    .split(/\r?\n/)
    .map((line) => line.replace(/^\s*\*\s?/, ''))
    .join('\n')
    .trim();
  if (!text) {
    return false;
  }
  try {
    const parsed = parse(text, {
      plugins: parserPlugins(file.path),
      sourceType: 'unambiguous'
    });
    return parsed.program.body.some(isLikelyCommentedCodeStatement);
  } catch (error) {
    return false;
  }
}

function isLikelyCommentedCodeStatement(statement) {
  if (
    [
      'BreakStatement',
      'ClassDeclaration',
      'ContinueStatement',
      'DoWhileStatement',
      'ExportAllDeclaration',
      'ExportDefaultDeclaration',
      'ExportNamedDeclaration',
      'ForInStatement',
      'ForOfStatement',
      'ForStatement',
      'FunctionDeclaration',
      'IfStatement',
      'ImportDeclaration',
      'ReturnStatement',
      'SwitchStatement',
      'ThrowStatement',
      'TryStatement',
      'VariableDeclaration',
      'WhileStatement'
    ].includes(statement.type)
  ) {
    return true;
  }
  return Boolean(
    statement.type === 'ExpressionStatement' &&
    statement.expression &&
    ['AssignmentExpression', 'AwaitExpression', 'CallExpression', 'NewExpression', 'UpdateExpression'].includes(statement.expression.type)
  );
}

function thresholdFor(checkId, thresholdState) {
  return thresholdState.values[THRESHOLD_FOR_CHECK[checkId]];
}

function thresholdMetadata(checkId, thresholdState) {
  const threshold = THRESHOLD_FOR_CHECK[checkId];
  return threshold ? { threshold: thresholdState.values[threshold] } : {};
}

function visitNode(node, visitor, ancestors = []) {
  if (!isAstNode(node)) {
    return;
  }
  visitor(node, ancestors);
  forEachChild(node, (child) => visitNode(child, visitor, [...ancestors, node]));
}

function forEachChild(node, visit) {
  for (const [key, value] of Object.entries(node)) {
    if (CHILDLESS_KEYS.has(key)) {
      continue;
    }
    if (isAstNode(value)) {
      visit(value);
    } else if (Array.isArray(value)) {
      for (const entry of value) {
        if (isAstNode(entry)) {
          visit(entry);
        }
      }
    }
  }
}

function isAstNode(value) {
  return Boolean(
    value &&
    typeof value === 'object' &&
    typeof value.type === 'string' &&
    !value.type.startsWith('Comment')
  );
}

function isFunctionNode(node) {
  return FUNCTION_NODE_TYPES.has(node.type);
}

function readJsonFile(filePath, allowComments) {
  let contents;
  try {
    contents = fs.readFileSync(filePath, 'utf8');
  } catch (error) {
    if (error && error.code === 'ENOENT') {
      return { status: 'missing' };
    }
    return { message: error.message, status: 'unreadable' };
  }
  try {
    const value = JSON.parse(allowComments ? parseJsonc(contents) : contents.replace(/^\uFEFF/, ''));
    if (!isPlainObject(value)) {
      return { message: 'The configuration root must be an object.', status: 'invalid' };
    }
    return { status: 'present', value };
  } catch (error) {
    return { message: error.message, status: 'invalid' };
  }
}

function parseJsonc(contents) {
  return removeTrailingCommas(removeJsonComments(contents.replace(/^\uFEFF/, '')));
}

function removeJsonComments(contents) {
  let quote = null;
  let result = '';
  for (let index = 0; index < contents.length; index += 1) {
    const character = contents[index];
    const next = contents[index + 1];
    if (quote) {
      result += character;
      if (character === '\\') {
        result += next || '';
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
    if (character === '/' && next === '/') {
      result += '  ';
      index += 2;
      while (index < contents.length && contents[index] !== '\n' && contents[index] !== '\r') {
        result += ' ';
        index += 1;
      }
      index -= 1;
      continue;
    }
    if (character === '/' && next === '*') {
      result += '  ';
      index += 2;
      while (index < contents.length) {
        const current = contents[index];
        const following = contents[index + 1];
        if (current === '*' && following === '/') {
          result += '  ';
          index += 1;
          break;
        }
        result += current === '\n' || current === '\r' ? current : ' ';
        index += 1;
      }
      continue;
    }
    result += character;
  }
  return result;
}

function removeTrailingCommas(contents) {
  let quote = null;
  let result = '';
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

function sourceEvidence(filePath, node, extra = {}) {
  const location = node && node.loc && node.loc.start ? node.loc.start : { column: 0, line: 1 };
  return {
    kind: 'source',
    path: filePath,
    line: location.line,
    column: location.column + 1,
    ...extra
  };
}

function commentEvidence(filePath, comment) {
  return {
    kind: 'comment',
    path: filePath,
    line: comment.loc.start.line,
    column: comment.loc.start.column + 1
  };
}

function edgeEvidence(edge) {
  return {
    kind: 'import',
    path: edge.from,
    line: edge.line,
    column: edge.column,
    specifier: edge.specifier,
    target: edge.to,
    syntax: edge.kind
  };
}

function graphProblemEvidence(problem) {
  return {
    kind: 'import',
    path: problem.path,
    line: problem.line,
    column: problem.column,
    specifier: problem.specifier || null,
    syntax: problem.kind,
    error: problem.message
  };
}

function configEvidence(filePath) {
  return { kind: 'configuration', path: filePath, line: 1, column: 1 };
}

function configProblemEvidence(problem) {
  return {
    kind: 'configuration',
    path: problem.configPath || problem.path,
    line: 1,
    column: 1,
    error: problem.message,
    status: problem.status
  };
}

function scanErrorEvidence(error) {
  return { kind: 'source', path: error.path, line: 1, column: 1, error: error.message };
}

function parseErrorEvidence(error) {
  return { kind: 'source', path: error.path, line: error.line, column: error.column, error: error.message };
}

function capabilityEvidence(error) {
  return {
    kind: 'capability',
    path: '@babel/parser',
    error: error && error.message ? error.message : 'The parser module could not be loaded.'
  };
}

function sourceStateEvidence(state) {
  return {
    kind: 'source-state',
    digest: state.digest || null,
    fileCount: state.fileCount || 0,
    ...(state.error ? { error: state.error } : {})
  };
}

function directoryEvidence(directoryPath) {
  return { kind: 'directory', path: directoryPath };
}

function physicalLineCount(contents) {
  if (!contents) {
    return 0;
  }
  const lineBreaks = contents.match(/\r\n|\r|\n/g) || [];
  const endsWithLineBreak = /(?:\r\n|\r|\n)$/.test(contents);
  return lineBreaks.length + (endsWithLineBreak ? 0 : 1);
}

function lineSpan(node) {
  if (!node || !node.loc || !node.loc.start || !node.loc.end) {
    return 0;
  }
  return node.loc.end.line - node.loc.start.line + 1;
}

function stringValue(node) {
  return node && (node.type === 'StringLiteral' || node.type === 'Literal') && typeof node.value === 'string'
    ? node.value
    : null;
}

function propertyName(node) {
  return node && node.type === 'Identifier'
    ? node.name
    : node && (node.type === 'StringLiteral' || node.type === 'Literal') && typeof node.value === 'string'
      ? node.value
      : null;
}

function isRelativeSpecifier(specifier) {
  return specifier === '.' || specifier === '..' || specifier.startsWith('./') || specifier.startsWith('../');
}

function isSourceFile(filePath) {
  return SOURCE_EXTENSIONS.some((extension) => filePath.endsWith(extension));
}

function isTypeScriptFile(filePath) {
  return /\.(cts|mts|tsx|ts)$/.test(filePath);
}

function isJavaScriptFile(filePath) {
  return /\.(cjs|mjs|jsx|js)$/.test(filePath);
}

function isTestFile(filePath) {
  const segments = filePath.split('/');
  return segments.some((segment) => ['__tests__', 'test', 'tests'].includes(segment)) || /\.(spec|test)\.[cm]?[jt]sx?$/.test(filePath);
}

function isWithin(projectRoot, candidate) {
  const relative = path.relative(path.resolve(projectRoot), path.resolve(candidate));
  return relative === '' || (!relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative));
}

function displayPath(projectRoot, absolutePath) {
  const relative = path.relative(projectRoot, absolutePath);
  return relative ? relative.split(path.sep).join('/') : '.';
}

function unique(values) {
  return [...new Set(values)];
}

function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

module.exports = { captureSourceState, diagnoseFastProject };
