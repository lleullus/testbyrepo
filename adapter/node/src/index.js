'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { diagnoseFastProject } = require('./fast-diagnosis');
const { createGatedAdmissionSession, gateProject } = require('./final-gate');

const SOURCE_EXTENSIONS = ['.cts', '.mts', '.tsx', '.jsx', '.ts', '.mjs', '.cjs', '.js'];
const RESOLUTION_EXTENSIONS = [...SOURCE_EXTENSIONS, '.json'];
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
const VERDICT_ORDER = { fail: 0, inconclusive: 1, risk: 2 };

/**
 * Diagnoses a Node or TypeScript project from files already present on disk.
 * The only input accepted as diagnostic evidence is the target directory.
 *
 * @param {string} projectDirectory directory to inspect
 * @returns {object} evidence-grounded diagnosis
 */
function diagnoseProject(projectDirectory) {
  if (typeof projectDirectory !== 'string' || projectDirectory.length === 0) {
    throw new TypeError('diagnoseProject requires a project directory path.');
  }

  const projectRoot = path.resolve(projectDirectory);
  let rootStat;

  try {
    rootStat = fs.statSync(projectRoot);
  } catch (error) {
    return createResult(projectRoot, {
      findings: [
        issue('inconclusive', 'unreadable-project-root', 'The project directory could not be read.', [
          fileEvidence('.', error.message)
        ])
      ]
    });
  }

  if (!rootStat.isDirectory()) {
    return createResult(projectRoot, {
      findings: [
        issue('inconclusive', 'project-root-is-not-directory', 'The diagnosis target is not a directory.', [
          fileEvidence('.')
        ])
      ]
    });
  }

  const packageDocument = readJsonDocument(projectRoot, 'package.json', false);
  const tsconfigDocument = readJsonDocument(projectRoot, 'tsconfig.json', true);
  const scan = scanProject(projectRoot);
  const tsconfigDocuments = collectTsconfigDocuments(projectRoot, scan, tsconfigDocument);

  for (const sourceFile of scan.sourceFiles) {
    const tokens = tokenizeSource(sourceFile.contents);
    sourceFile.imports = collectImports(tokens);
    sourceFile.exports = collectExports(tokens);
  }

  const boundaries = buildBoundaries(scan.sourceFiles);
  const dependencyDirection = analyzeDependencies(
    projectRoot,
    scan,
    tsconfigDocuments,
    packageDocument,
    boundaries
  );
  const packageEntries = collectPackageEntries(packageDocument);
  const tsconfigEntries = collectTsconfigEntries(tsconfigDocument);
  const responsibilities = buildResponsibilities(
    packageDocument,
    tsconfigDocument,
    packageEntries,
    tsconfigEntries,
    boundaries
  );
  const candidates = buildCandidates(
    packageDocument,
    tsconfigDocument,
    packageEntries,
    tsconfigEntries,
    scan.sourceFiles,
    dependencyDirection
  );
  const findings = collectFindings(
    packageDocument,
    tsconfigDocuments,
    scan,
    dependencyDirection
  );
  const repositoryAuthority = assessRepositoryAuthority(packageDocument, scan.sourceFiles);
  findings.push(...repositoryAuthority.findings);

  return createResult(projectRoot, {
    packageDocument,
    tsconfigDocument,
    scan,
    boundaries,
    dependencyDirection,
    responsibilities,
    ssotCandidates: candidates.ssotCandidates,
    reuseCandidates: candidates.reuseCandidates,
    findings,
    repositoryAuthority
  });
}

/**
 * Creates a read-only, one-request admission session with a mediated write gate.
 * Scope is inferred from repository evidence when omitted; an optional scope can only narrow or confirm it.
 * attemptWrite accepts declarative { request, scope?, writes: [{ path, content }] } file writes.
 *
 * @param {{projectDirectory: string, request: string, scope?: string|string[]}} options admission input
 * @returns {object} admission result with mediated writes, final Gate, and session-bound behavior proof;
 * behaviorProof({ mode: 'deep' }) proves the fixed dependency impact closure
 */
function admitChange(options) {
  return createGatedAdmissionSession(options);
}

function scanProject(projectRoot) {
  const scan = {
    directories: new Set(['.']),
    fileByAbsolutePath: new Map(),
    files: [],
    scanErrors: [],
    skippedSymlinks: [],
    sourceFiles: []
  };

  walkDirectory(projectRoot, projectRoot, scan);
  scan.files.sort();
  scan.sourceFiles.sort((left, right) => left.path.localeCompare(right.path));
  return scan;
}

function collectTsconfigDocuments(projectRoot, scan, rootTsconfigDocument) {
  const documents = new Map();

  if (rootTsconfigDocument.status !== 'missing') {
    documents.set(rootTsconfigDocument.path, rootTsconfigDocument);
  }

  for (const filePath of scan.files) {
    if (path.posix.basename(filePath) !== 'tsconfig.json') {
      continue;
    }
    if (filePath === rootTsconfigDocument.path) {
      documents.set(filePath, rootTsconfigDocument);
    } else {
      documents.set(filePath, readJsonDocument(projectRoot, filePath, true));
    }
  }

  const cache = new Map();
  for (const configPath of [...documents.keys()]) {
    const resolved = resolveTsconfigDocument(projectRoot, configPath, documents, cache, new Set());
    const document = documents.get(configPath);
    document.resolutionStatus = resolved.status;
    if (resolved.message) {
      document.resolutionMessage = resolved.message;
    }
    if (resolved.status === 'present') {
      document.resolvedCompilerOptions = resolved.compilerOptions;
      document.compilerOptionOrigins = resolved.compilerOptionOrigins;
    }
  }

  return documents;
}

function resolveTsconfigDocument(projectRoot, configPath, documents, cache, stack) {
  const normalizedPath = displayPath(projectRoot, path.resolve(projectRoot, configPath));
  if (cache.has(normalizedPath)) {
    return cache.get(normalizedPath);
  }
  if (stack.has(normalizedPath)) {
    return { message: 'A tsconfig extends cycle was observed.', status: 'invalid' };
  }

  let document = documents.get(normalizedPath);
  if (!document) {
    document = readJsonDocument(projectRoot, normalizedPath, true);
    documents.set(normalizedPath, document);
  }
  if (document.status !== 'present') {
    const result = { message: document.message, status: document.status };
    cache.set(normalizedPath, result);
    return result;
  }

  stack.add(normalizedPath);
  const configDirectory = path.dirname(path.join(projectRoot, normalizedPath));
  const value = document.value;
  let inherited = { compilerOptions: {}, compilerOptionOrigins: {} };

  if (value.extends !== undefined) {
    if (
      typeof value.extends !== 'string' ||
      !(
        ['.', '..'].includes(value.extends) ||
        value.extends.startsWith('./') ||
        value.extends.startsWith('../')
      ) ||
      path.isAbsolute(value.extends) ||
      path.win32.isAbsolute(value.extends)
    ) {
      const result = { message: 'Only local relative tsconfig extends values are supported.', status: 'unsupported' };
      cache.set(normalizedPath, result);
      stack.delete(normalizedPath);
      return result;
    }

    const inheritedPath = resolveTsconfigExtendsPath(projectRoot, configDirectory, value.extends);
    if (!inheritedPath || !isWithin(projectRoot, inheritedPath)) {
      const result = { message: 'The tsconfig extends target is missing or outside the target tree.', status: 'unsupported' };
      cache.set(normalizedPath, result);
      stack.delete(normalizedPath);
      return result;
    }

    inherited = resolveTsconfigDocument(
      projectRoot,
      displayPath(projectRoot, inheritedPath),
      documents,
      cache,
      stack
    );
    if (inherited.status !== 'present') {
      cache.set(normalizedPath, inherited);
      stack.delete(normalizedPath);
      return inherited;
    }
  }

  if (value.compilerOptions !== undefined && !isPlainObject(value.compilerOptions)) {
    const result = { message: 'tsconfig compilerOptions must be an object.', status: 'invalid' };
    cache.set(normalizedPath, result);
    stack.delete(normalizedPath);
    return result;
  }

  const compilerOptionError = validateTypeScriptCompilerOptions(value.compilerOptions || {});
  if (compilerOptionError) {
    const result = { message: compilerOptionError, status: 'invalid' };
    cache.set(normalizedPath, result);
    stack.delete(normalizedPath);
    return result;
  }

  const compilerOptions = {
    ...inherited.compilerOptions,
    ...(value.compilerOptions || {})
  };
  const compilerOptionOrigins = { ...inherited.compilerOptionOrigins };
  for (const key of Object.keys(value.compilerOptions || {})) {
    compilerOptionOrigins[key] = configDirectory;
  }
  const result = { compilerOptionOrigins, compilerOptions, status: 'present' };
  cache.set(normalizedPath, result);
  stack.delete(normalizedPath);
  return result;
}

function validateTypeScriptCompilerOptions(compilerOptions) {
  if (Object.hasOwn(compilerOptions, 'baseUrl') && typeof compilerOptions.baseUrl !== 'string') {
    return 'tsconfig compilerOptions.baseUrl must be a string.';
  }
  if (!Object.hasOwn(compilerOptions, 'paths')) {
    return null;
  }
  if (!isPlainObject(compilerOptions.paths)) {
    return 'tsconfig compilerOptions.paths must be an object.';
  }
  for (const [pattern, substitutions] of Object.entries(compilerOptions.paths)) {
    if (!Array.isArray(substitutions) || substitutions.some((substitution) => typeof substitution !== 'string')) {
      return `tsconfig compilerOptions.paths.${pattern} must be an array of strings.`;
    }
  }
  return null;
}

function resolveTsconfigExtendsPath(projectRoot, configDirectory, extendsValue) {
  const base = path.resolve(configDirectory, extendsValue);
  if (!isWithin(projectRoot, base)) {
    return null;
  }
  const candidates = path.extname(base) ? [base] : [base, `${base}.json`];
  return candidates.find((candidate) => isSafeTsconfigTarget(projectRoot, candidate)) || null;
}

function isSafeTsconfigTarget(projectRoot, candidate) {
  if (!isWithin(projectRoot, candidate) || containsSymlinkComponent(projectRoot, candidate)) {
    return false;
  }

  let candidateStat;
  let projectRealPath;
  let candidateRealPath;
  try {
    candidateStat = fs.lstatSync(candidate);
    if (!candidateStat.isFile() || candidateStat.isSymbolicLink()) {
      return false;
    }
    projectRealPath = fs.realpathSync(projectRoot);
    candidateRealPath = fs.realpathSync(candidate);
  } catch (error) {
    return false;
  }
  return isWithin(projectRealPath, candidateRealPath);
}

function containsSymlinkComponent(projectRoot, candidate) {
  const relativePath = path.relative(path.resolve(projectRoot), path.resolve(candidate));
  if (!relativePath || relativePath.startsWith(`..${path.sep}`) || relativePath === '..' || path.isAbsolute(relativePath)) {
    return false;
  }

  let currentPath = path.resolve(projectRoot);
  for (const segment of relativePath.split(path.sep)) {
    currentPath = path.join(currentPath, segment);
    try {
      if (fs.lstatSync(currentPath).isSymbolicLink()) {
        return true;
      }
    } catch (error) {
      return true;
    }
  }
  return false;
}

function walkDirectory(projectRoot, directory, scan) {
  let entries;

  try {
    entries = fs.readdirSync(directory, { withFileTypes: true });
  } catch (error) {
    scan.scanErrors.push({
      path: displayPath(projectRoot, directory),
      message: error.message,
      type: 'directory'
    });
    return;
  }

  for (const entry of entries) {
    const absolutePath = path.join(directory, entry.name);
    const relativePath = displayPath(projectRoot, absolutePath);

    if (entry.isSymbolicLink()) {
      scan.skippedSymlinks.push(relativePath);
      continue;
    }

    if (entry.isDirectory()) {
      if (!IGNORED_DIRECTORIES.has(entry.name)) {
        scan.directories.add(relativePath);
        walkDirectory(projectRoot, absolutePath, scan);
      }
      continue;
    }

    if (!entry.isFile()) {
      continue;
    }

    const record = { absolutePath: path.resolve(absolutePath), path: relativePath };
    scan.fileByAbsolutePath.set(record.absolutePath, record);
    scan.files.push(relativePath);

    if (!isSourceFile(relativePath)) {
      continue;
    }

    try {
      const sourceFile = {
        ...record,
        contents: fs.readFileSync(absolutePath, 'utf8'),
        exports: [],
        imports: []
      };
      record.sourceFile = sourceFile;
      scan.sourceFiles.push(sourceFile);
    } catch (error) {
      scan.scanErrors.push({ path: relativePath, message: error.message, type: 'source-file' });
    }
  }
}

function readJsonDocument(projectRoot, relativePath, allowComments) {
  const absolutePath = path.join(projectRoot, relativePath);
  let contents;

  try {
    contents = fs.readFileSync(absolutePath, 'utf8');
  } catch (error) {
    if (error && error.code === 'ENOENT') {
      return { path: relativePath, status: 'missing' };
    }

    return { path: relativePath, status: 'unreadable', message: error.message };
  }

  try {
    const value = JSON.parse(allowComments ? parseJsonc(contents) : contents.replace(/^\uFEFF/, ''));
    if (!isPlainObject(value)) {
      return {
        path: relativePath,
        status: 'invalid',
        message: 'The configuration root must be a JSON object.'
      };
    }
    return { path: relativePath, status: 'present', value };
  } catch (error) {
    return { path: relativePath, status: 'invalid', message: error.message };
  }
}

function parseJsonc(contents) {
  const withoutComments = removeJsonComments(contents.replace(/^\uFEFF/, ''));
  return removeTrailingJsonCommas(withoutComments);
}

function removeJsonComments(contents) {
  let result = '';
  let quote = null;

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
        const commentCharacter = contents[index];
        const commentNext = contents[index + 1];
        if (commentCharacter === '*' && commentNext === '/') {
          result += '  ';
          index += 1;
          break;
        }
        result += commentCharacter === '\n' || commentCharacter === '\r' ? commentCharacter : ' ';
        index += 1;
      }
      continue;
    }

    result += character;
  }

  return result;
}

function removeTrailingJsonCommas(contents) {
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

function tokenizeSource(contents) {
  const tokens = [];
  let index = 0;
  let line = 1;

  while (index < contents.length) {
    const character = contents[index];
    const next = contents[index + 1];

    if (/\s/.test(character)) {
      if (character === '\n') {
        line += 1;
      }
      index += 1;
      continue;
    }

    if (character === '/' && next === '/') {
      index += 2;
      while (index < contents.length && contents[index] !== '\n') {
        index += 1;
      }
      continue;
    }

    if (character === '/' && next === '*') {
      index += 2;
      while (index < contents.length) {
        if (contents[index] === '\n') {
          line += 1;
        }
        if (contents[index] === '*' && contents[index + 1] === '/') {
          index += 2;
          break;
        }
        index += 1;
      }
      continue;
    }

    if (character === '"' || character === "'") {
      const tokenLine = line;
      const quote = character;
      let value = '';
      index += 1;

      while (index < contents.length) {
        const stringCharacter = contents[index];
        if (stringCharacter === '\\') {
          const escaped = contents[index + 1];
          if (escaped === '\n') {
            line += 1;
          }
          value += escaped || '';
          index += 2;
          continue;
        }
        if (stringCharacter === quote) {
          index += 1;
          break;
        }
        if (stringCharacter === '\n') {
          line += 1;
        }
        value += stringCharacter;
        index += 1;
      }

      tokens.push({ line: tokenLine, type: 'string', value });
      continue;
    }

    if (character === '`') {
      index += 1;
      while (index < contents.length) {
        if (contents[index] === '\\') {
          index += 2;
          continue;
        }
        if (contents[index] === '`') {
          index += 1;
          break;
        }
        if (contents[index] === '\n') {
          line += 1;
        }
        index += 1;
      }
      continue;
    }

    if (isIdentifierStart(character)) {
      const tokenLine = line;
      let value = character;
      index += 1;
      while (index < contents.length && isIdentifierPart(contents[index])) {
        value += contents[index];
        index += 1;
      }
      tokens.push({ line: tokenLine, type: 'identifier', value });
      continue;
    }

    tokens.push({ line, type: 'punctuation', value: character });
    index += 1;
  }

  return tokens;
}

function isIdentifierStart(character) {
  return /[A-Za-z_$]/.test(character);
}

function isIdentifierPart(character) {
  return /[A-Za-z0-9_$]/.test(character);
}

function collectImports(tokens) {
  const imports = [];
  const seen = new Set();

  function add(kind, token, specifier) {
    if (!specifier) {
      return;
    }
    const key = `${kind}:${token.line}:${specifier}`;
    if (!seen.has(key)) {
      seen.add(key);
      imports.push({ kind, line: token.line, specifier });
    }
  }

  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];
    const previous = tokens[index - 1];
    if (previous && previous.value === '.') {
      continue;
    }

    if (token.type !== 'identifier') {
      continue;
    }

    if (token.value === 'import') {
      const next = tokens[index + 1];
      if (next && next.type === 'string') {
        add('import', token, next.value);
      } else if (next && next.value === '(' && tokens[index + 2] && tokens[index + 2].type === 'string') {
        add('dynamic-import', token, tokens[index + 2].value);
      } else {
        const specifier = findFromSpecifier(tokens, index + 1, token.line);
        if (specifier) {
          add('import', token, specifier.value);
        }
      }
      continue;
    }

    if (token.value === 'export') {
      const specifier = findFromSpecifier(tokens, index + 1, token.line);
      if (specifier) {
        add('export-from', token, specifier.value);
      }
      continue;
    }

    if (
      token.value === 'require' &&
      tokens[index + 1] &&
      tokens[index + 1].value === '(' &&
      tokens[index + 2] &&
      tokens[index + 2].type === 'string'
    ) {
      add('require', token, tokens[index + 2].value);
    }
  }

  return imports;
}

function findFromSpecifier(tokens, start, startingLine) {
  for (let index = start; index < tokens.length; index += 1) {
    const token = tokens[index];
    if (token.line > startingLine + 20 || token.value === ';') {
      return null;
    }
    if (token.type === 'identifier' && (token.value === 'import' || token.value === 'export')) {
      return null;
    }
    if (token.type === 'identifier' && token.value === 'from') {
      const next = tokens[index + 1];
      return next && next.type === 'string' ? next : null;
    }
  }
  return null;
}

function collectExports(tokens) {
  const exports = [];
  const seen = new Set();

  function add(symbol, token) {
    const key = `${symbol}:${token.line}`;
    if (!seen.has(key)) {
      seen.add(key);
      exports.push({ line: token.line, symbol });
    }
  }

  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];
    const previous = tokens[index - 1];
    if (token.type !== 'identifier' || (previous && previous.value === '.')) {
      continue;
    }

    if (token.value === 'export') {
      let cursor = index + 1;
      if (tokens[cursor] && tokens[cursor].value === 'default') {
        add('default', tokens[cursor]);
        continue;
      }
      if (tokens[cursor] && (tokens[cursor].value === 'declare' || tokens[cursor].value === 'async')) {
        cursor += 1;
      }
      if (
        tokens[cursor] &&
        ['class', 'const', 'enum', 'function', 'interface', 'let', 'type', 'var'].includes(tokens[cursor].value) &&
        tokens[cursor + 1] &&
        tokens[cursor + 1].type === 'identifier'
      ) {
        add(tokens[cursor + 1].value, tokens[cursor + 1]);
        continue;
      }
      if (tokens[cursor] && tokens[cursor].value === '{') {
        collectNamedExports(tokens, cursor + 1, add);
      }
      continue;
    }

    if (
      token.value === 'module' &&
      tokens[index + 1] && tokens[index + 1].value === '.' &&
      tokens[index + 2] && tokens[index + 2].value === 'exports'
    ) {
      if (tokens[index + 3] && tokens[index + 3].value === '=') {
        add('module.exports', token);
      }
      if (
        tokens[index + 3] && tokens[index + 3].value === '.' &&
        tokens[index + 4] && tokens[index + 4].type === 'identifier' &&
        tokens[index + 5] && tokens[index + 5].value === '='
      ) {
        add(tokens[index + 4].value, tokens[index + 4]);
      }
      continue;
    }

    if (
      token.value === 'exports' &&
      tokens[index + 1] && tokens[index + 1].value === '.' &&
      tokens[index + 2] && tokens[index + 2].type === 'identifier' &&
      tokens[index + 3] && tokens[index + 3].value === '='
    ) {
      add(tokens[index + 2].value, tokens[index + 2]);
    }
  }

  return exports;
}

function collectNamedExports(tokens, start, add) {
  let segment = [];

  function finishSegment() {
    const identifiers = segment.filter((token) => token.type === 'identifier' && token.value !== 'type');
    const asIndex = identifiers.findIndex((token) => token.value === 'as');
    const exported = asIndex === -1 ? identifiers[0] : identifiers[asIndex + 1];
    if (exported) {
      add(exported.value, exported);
    }
    segment = [];
  }

  for (let index = start; index < tokens.length; index += 1) {
    const token = tokens[index];
    if (token.value === '}') {
      finishSegment();
      return;
    }
    if (token.value === ',') {
      finishSegment();
    } else {
      segment.push(token);
    }
  }
}

function buildBoundaries(sourceFiles) {
  const byPath = new Map();

  for (const sourceFile of sourceFiles) {
    const boundaryPath = boundaryPathFor(sourceFile.path);
    let boundary = byPath.get(boundaryPath);
    if (!boundary) {
      const role = roleForBoundary(boundaryPath);
      boundary = {
        evidence: [directoryEvidence(boundaryPath)],
        fileCount: 0,
        files: [],
        path: boundaryPath,
        responsibility: responsibilityForRole(role),
        role
      };
      byPath.set(boundaryPath, boundary);
    }
    boundary.fileCount += 1;
    boundary.files.push(sourceFile.path);
  }

  return [...byPath.values()]
    .sort((left, right) => left.path.localeCompare(right.path))
    .map((boundary) => ({
      ...boundary,
      evidence: [
        ...boundary.evidence,
        ...boundary.files.slice(0, 10).map((filePath) => fileEvidence(filePath))
      ]
    }));
}

function boundaryPathFor(filePath) {
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

function roleForBoundary(boundaryPath) {
  const segment = boundaryPath.split('/').at(-1).toLowerCase();
  if (['api', 'controllers', 'http', 'routes'].includes(segment)) {
    return 'api';
  }
  if (['cli', 'command', 'commands'].includes(segment)) {
    return 'cli';
  }
  if (['application', 'service', 'services', 'use-cases', 'usecases'].includes(segment)) {
    return 'application';
  }
  if (['core', 'domain', 'entities', 'models'].includes(segment)) {
    return 'domain';
  }
  if (['adapter', 'adapters', 'data', 'infra', 'infrastructure', 'repositories', 'repository'].includes(segment)) {
    return 'infrastructure';
  }
  if (['config', 'configuration', 'settings'].includes(segment)) {
    return 'configuration';
  }
  if (['__tests__', 'test', 'tests'].includes(segment)) {
    return 'test';
  }
  return 'module';
}

function responsibilityForRole(role) {
  if (role === 'module') {
    return 'Source module boundary';
  }
  return `${role[0].toUpperCase()}${role.slice(1)} boundary inferred from the directory name`;
}

function analyzeDependencies(projectRoot, scan, tsconfigDocuments, packageDocument, boundaries) {
  const boundaryBySourcePath = new Map();
  for (const sourceFile of scan.sourceFiles) {
    boundaryBySourcePath.set(sourceFile.path, boundaryPathFor(sourceFile.path));
  }

  const internalReferences = [];
  const externalImports = [];
  const outsideTargetImports = [];
  const resolvedArtifacts = [];
  const unresolvedAliases = [];
  const unresolvedRelativeImports = [];

  for (const sourceFile of scan.sourceFiles) {
    for (const imported of sourceFile.imports) {
      const importEvidence = {
        kind: 'import',
        line: imported.line,
        path: sourceFile.path,
        specifier: imported.specifier,
        syntax: imported.kind
      };

      let resolution;
      if (isRelativeSpecifier(imported.specifier)) {
        resolution = resolveSpecifier(
          projectRoot,
          path.dirname(sourceFile.absolutePath),
          imported.specifier,
          scan.fileByAbsolutePath,
          packageDocument
        );
      } else {
        const tsconfigDocument = findContainingTsconfig(sourceFile.path, tsconfigDocuments) || { status: 'missing' };
        resolution = resolveTsPathAlias(
          projectRoot,
          imported.specifier,
          tsconfigDocument,
          scan.fileByAbsolutePath
        );
      }

      if (resolution.status === 'source') {
        internalReferences.push({
          ...importEvidence,
          target: resolution.target.path,
          targetBoundary: boundaryBySourcePath.get(resolution.target.path)
        });
      } else if (resolution.status === 'file') {
        resolvedArtifacts.push({ ...importEvidence, target: resolution.target.path });
      } else if (resolution.status === 'outside') {
        outsideTargetImports.push({ ...importEvidence, attemptedPath: resolution.attemptedPath });
      } else if (resolution.status === 'alias-missing') {
        unresolvedAliases.push({
          ...importEvidence,
          expectedPaths: resolution.expectedPaths,
          pattern: resolution.pattern
        });
      } else if (isRelativeSpecifier(imported.specifier)) {
        unresolvedRelativeImports.push({
          ...importEvidence,
          expectedPaths: resolution.expectedPaths
        });
      } else {
        externalImports.push(importEvidence);
      }
    }
  }

  const edgeByDirection = new Map();
  for (const reference of internalReferences) {
    const from = boundaryBySourcePath.get(reference.path);
    const to = reference.targetBoundary;
    const key = `${from}\u0000${to}`;
    let edge = edgeByDirection.get(key);
    if (!edge) {
      edge = { from, imports: [], to };
      edgeByDirection.set(key, edge);
    }
    edge.imports.push(reference);
  }

  const internalEdges = [...edgeByDirection.values()].sort((left, right) => {
    return `${left.from}:${left.to}`.localeCompare(`${right.from}:${right.to}`);
  });

  return {
    cycles: findCycles(internalReferences),
    externalImports,
    internalEdges,
    internalReferences,
    outsideTargetImports,
    resolvedArtifacts,
    unresolvedAliases,
    unresolvedRelativeImports
  };
}

function isRelativeSpecifier(specifier) {
  return specifier === '.' || specifier === '..' || specifier.startsWith('./') || specifier.startsWith('../');
}

function resolveSpecifier(projectRoot, sourceDirectory, specifier, fileByAbsolutePath, packageDocument) {
  const basePath = path.resolve(sourceDirectory, specifier);
  if (path.resolve(basePath) === path.resolve(projectRoot)) {
    const packageEntry = resolvePackageEntry(projectRoot, packageDocument, fileByAbsolutePath);
    if (packageEntry) {
      return packageEntry;
    }
  }

  return resolveCandidatePath(
    projectRoot,
    basePath,
    fileByAbsolutePath
  );
}

function resolvePackageEntry(projectRoot, packageDocument, fileByAbsolutePath) {
  if (packageDocument.status !== 'present') {
    return null;
  }
  const entry = simplePackageExportTarget(packageDocument.value.exports) || packageDocument.value.main;
  if (typeof entry !== 'string') {
    return null;
  }

  return resolveCandidatePath(
    projectRoot,
    path.resolve(projectRoot, entry),
    fileByAbsolutePath
  );
}

function simplePackageExportTarget(value) {
  if (typeof value === 'string') {
    return value;
  }
  if (!isPlainObject(value)) {
    return null;
  }
  const root = Object.hasOwn(value, '.') ? value['.'] : value;
  if (typeof root === 'string') {
    return root;
  }
  if (!isPlainObject(root)) {
    return null;
  }
  for (const key of ['require', 'import', 'default', 'node']) {
    if (typeof root[key] === 'string') {
      return root[key];
    }
  }
  return null;
}

function resolveTsPathAlias(projectRoot, specifier, tsconfigDocument, fileByAbsolutePath) {
  const configurationStatus = tsconfigDocument.resolutionStatus || tsconfigDocument.status;
  if (configurationStatus !== 'present') {
    return { status: 'external' };
  }

  const compilerOptions = tsconfigDocument.resolvedCompilerOptions || tsconfigDocument.value.compilerOptions;
  if (!isPlainObject(compilerOptions)) {
    return { status: 'external' };
  }

  const configDirectory = path.dirname(path.join(projectRoot, tsconfigDocument.path));
  const compilerOptionOrigins = tsconfigDocument.compilerOptionOrigins || {};
  const baseUrl = typeof compilerOptions.baseUrl === 'string'
    ? path.resolve(compilerOptionOrigins.baseUrl || configDirectory, compilerOptions.baseUrl)
    : null;
  const paths = isPlainObject(compilerOptions.paths) ? compilerOptions.paths : null;
  if (Object.hasOwn(compilerOptions, 'paths') && !paths) {
    return { expectedPaths: [], pattern: '<paths>', status: 'alias-missing' };
  }

  const matches = paths
    ? Object.entries(paths)
      .map(([pattern, substitutions], declarationOrder) => ({
        declarationOrder,
        pattern,
        substitutions,
        wildcard: matchPathPattern(pattern, specifier)
      }))
      .filter((match) => match.wildcard !== null)
      .sort(comparePathMatches)
    : [];

  for (const match of matches) {
    const { pattern, substitutions, wildcard } = match;
    if (!Array.isArray(substitutions)) {
      return { expectedPaths: [], pattern, status: 'alias-missing' };
    }

    const expectedPaths = [];
    const resolutionBase = baseUrl || path.resolve(compilerOptionOrigins.paths || configDirectory);
    for (const substitution of substitutions) {
      if (typeof substitution !== 'string') {
        continue;
      }
      const candidate = substitution.replaceAll('*', wildcard);
      const resolution = resolveCandidatePath(
        projectRoot,
        path.resolve(resolutionBase, candidate),
        fileByAbsolutePath
      );
      if (resolution.status === 'source' || resolution.status === 'file' || resolution.status === 'outside') {
        return resolution;
      }
      expectedPaths.push(...resolution.expectedPaths);
    }

    return { expectedPaths: unique(expectedPaths), pattern, status: 'alias-missing' };
  }

  if (typeof compilerOptions.baseUrl === 'string') {
    const resolution = resolveCandidatePath(projectRoot, path.resolve(baseUrl, specifier), fileByAbsolutePath);
    if (resolution.status === 'source' || resolution.status === 'file' || resolution.status === 'outside') {
      return resolution;
    }
    return { status: 'external' };
  }
  return { status: 'external' };
}

function comparePathMatches(left, right) {
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

function matchPathPattern(pattern, specifier) {
  const wildcardIndex = pattern.indexOf('*');
  if (wildcardIndex === -1) {
    return pattern === specifier ? '' : null;
  }

  const prefix = pattern.slice(0, wildcardIndex);
  const suffix = pattern.slice(wildcardIndex + 1);
  if (!specifier.startsWith(prefix) || !specifier.endsWith(suffix)) {
    return null;
  }
  return specifier.slice(prefix.length, specifier.length - suffix.length || undefined);
}

function resolveCandidatePath(projectRoot, basePath, fileByAbsolutePath) {
  if (!isWithin(projectRoot, basePath)) {
    return { attemptedPath: displayPath(path.dirname(projectRoot), basePath), status: 'outside' };
  }

  const candidates = candidatePaths(basePath);
  const expectedPaths = [];

  for (const candidate of candidates) {
    if (!isWithin(projectRoot, candidate)) {
      continue;
    }
    const normalizedCandidate = path.resolve(candidate);
    expectedPaths.push(displayPath(projectRoot, normalizedCandidate));
    const record = fileByAbsolutePath.get(normalizedCandidate);
    if (record) {
      return { status: record.sourceFile ? 'source' : 'file', target: record };
    }
  }

  return { expectedPaths: unique(expectedPaths), status: 'missing' };
}

function candidatePaths(basePath) {
  const extension = path.extname(basePath);
  const candidates = [basePath];

  if (extension) {
    if (['.cjs', '.js', '.mjs'].includes(extension)) {
      const withoutExtension = basePath.slice(0, -extension.length);
      for (const sourceExtension of SOURCE_EXTENSIONS) {
        candidates.push(`${withoutExtension}${sourceExtension}`);
      }
    }
    return unique(candidates);
  }

  for (const resolutionExtension of RESOLUTION_EXTENSIONS) {
    candidates.push(`${basePath}${resolutionExtension}`);
    candidates.push(path.join(basePath, `index${resolutionExtension}`));
  }
  return unique(candidates);
}

function isWithin(projectRoot, candidate) {
  const relative = path.relative(path.resolve(projectRoot), path.resolve(candidate));
  return relative === '' || (!relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative));
}

function findCycles(internalReferences) {
  const dependencies = new Map();
  for (const reference of internalReferences) {
    if (!dependencies.has(reference.path)) {
      dependencies.set(reference.path, new Set());
    }
    dependencies.get(reference.path).add(reference.target);
  }

  const cycles = [];
  const seenCycles = new Set();
  const visiting = new Set();
  const visited = new Set();
  const stack = [];

  function visit(sourcePath) {
    visiting.add(sourcePath);
    stack.push(sourcePath);

    for (const targetPath of dependencies.get(sourcePath) || []) {
      if (visiting.has(targetPath)) {
        const cycle = [...stack.slice(stack.indexOf(targetPath)), targetPath];
        const key = [...new Set(cycle.slice(0, -1))].sort().join('\u0000');
        if (!seenCycles.has(key)) {
          seenCycles.add(key);
          cycles.push(cycle);
        }
      } else if (!visited.has(targetPath)) {
        visit(targetPath);
      }
    }

    stack.pop();
    visiting.delete(sourcePath);
    visited.add(sourcePath);
  }

  for (const sourcePath of dependencies.keys()) {
    if (!visited.has(sourcePath)) {
      visit(sourcePath);
    }
  }

  return cycles;
}

function collectPackageEntries(document) {
  if (document.status !== 'present') {
    return [];
  }

  const entries = [];
  for (const key of ['bin', 'exports', 'main', 'module', 'name', 'scripts', 'type', 'types']) {
    if (Object.hasOwn(document.value, key)) {
      entries.push(configEvidence('package.json', key, document.value[key]));
    }
  }
  return entries;
}

function collectTsconfigEntries(document) {
  if (document.status !== 'present') {
    return [];
  }

  const entries = [];
  for (const key of ['extends', 'files', 'include', 'exclude']) {
    if (Object.hasOwn(document.value, key)) {
      entries.push(configEvidence('tsconfig.json', key, document.value[key]));
    }
  }

  if (isPlainObject(document.value.compilerOptions)) {
    for (const key of ['baseUrl', 'outDir', 'paths', 'rootDir']) {
      if (Object.hasOwn(document.value.compilerOptions, key)) {
        entries.push(configEvidence('tsconfig.json', `compilerOptions.${key}`, document.value.compilerOptions[key]));
      }
    }
  }
  return entries;
}

function buildResponsibilities(packageDocument, tsconfigDocument, packageEntries, tsconfigEntries, boundaries) {
  const responsibilities = [];

  if (packageDocument.status === 'present') {
    responsibilities.push({
      evidence: packageEntries.length > 0 ? packageEntries : [fileEvidence('package.json')],
      ownerPath: 'package.json',
      responsibility: 'Package entry and runtime configuration'
    });
  }
  if (tsconfigDocument.status === 'present') {
    responsibilities.push({
      evidence: tsconfigEntries.length > 0 ? tsconfigEntries : [fileEvidence('tsconfig.json')],
      ownerPath: 'tsconfig.json',
      responsibility: 'TypeScript compiler configuration'
    });
  }
  for (const boundary of boundaries) {
    responsibilities.push({
      evidence: boundary.evidence,
      ownerPath: boundary.path,
      responsibility: boundary.responsibility
    });
  }
  return responsibilities;
}

function buildCandidates(
  packageDocument,
  tsconfigDocument,
  packageEntries,
  tsconfigEntries,
  sourceFiles,
  dependencyDirection
) {
  const ssotCandidates = [];
  const reuseCandidates = [];

  if (packageDocument.status === 'present') {
    ssotCandidates.push({
      candidate: 'Package configuration candidate',
      evidence: packageEntries.length > 0 ? packageEntries : [fileEvidence('package.json')],
      path: 'package.json'
    });
  }
  if (tsconfigDocument.status === 'present') {
    ssotCandidates.push({
      candidate: 'TypeScript compiler configuration candidate',
      evidence: tsconfigEntries.length > 0 ? tsconfigEntries : [fileEvidence('tsconfig.json')],
      path: 'tsconfig.json'
    });
  }

  const inboundReferences = new Map();
  for (const reference of dependencyDirection.internalReferences) {
    if (!inboundReferences.has(reference.target)) {
      inboundReferences.set(reference.target, []);
    }
    inboundReferences.get(reference.target).push(reference);
  }

  for (const sourceFile of sourceFiles) {
    const inbound = inboundReferences.get(sourceFile.path) || [];
    if (inbound.length === 0) {
      continue;
    }
    const symbolEvidence = sourceFile.exports.map((exported) => symbolEvidenceFor(sourceFile.path, exported));
    const evidence = [...inbound, ...symbolEvidence];
    const candidate = {
      evidence,
      importedBy: inbound.map((reference) => reference.path),
      observedImportCount: inbound.length,
      path: sourceFile.path,
      symbols: sourceFile.exports.map((exported) => exported.symbol)
    };
    reuseCandidates.push(candidate);
    if (inbound.length >= 2) {
      ssotCandidates.push({
        candidate: 'Internally reused source module candidate',
        ...candidate
      });
    }
  }

  return { reuseCandidates, ssotCandidates };
}

function assessRepositoryAuthority(packageDocument, sourceFiles) {
  const findings = [];
  const configuredEvidence = collectPackageExecutionEntries(packageDocument);
  const hasExports = Boolean(
    packageDocument &&
    packageDocument.status === 'present' &&
    Object.hasOwn(packageDocument.value, 'exports')
  );
  const exportEntries = configuredEvidence.filter((entry) => entry.key === 'exports');
  const exportPaths = [...new Set(exportEntries
    .map((entry) => resolvePackageExecutionPath(entry.value, sourceFiles))
    .filter(Boolean))];
  const unresolvedExports = exportEntries.filter((entry) => !resolvePackageExecutionPath(entry.value, sourceFiles));
  const defaultEvidence = configuredEvidence.length === 0 && canUseNodeDefaultEntry(packageDocument, sourceFiles)
    ? [fileEvidence('index.js')]
    : [];
  const evidence = [...configuredEvidence, ...defaultEvidence];
  const executionPaths = [...new Set(configuredEvidence
    .map((entry) => resolvePackageExecutionPath(entry.value, sourceFiles))
    .filter(Boolean))];
  if (defaultEvidence.length > 0) {
    executionPaths.push('index.js');
  }
  const hasUnambiguousRootExport = exportPaths.length === 1 && unresolvedExports.length === 0;
  const unresolved = configuredEvidence.filter((entry) => {
    if (hasUnambiguousRootExport && entry.key === 'main') {
      return false;
    }
    return !resolvePackageExecutionPath(entry.value, sourceFiles);
  });
  if (configuredEvidence.length > 0 && unresolved.length > 0) {
    findings.push(issue(
      'inconclusive',
      'execution-entry-unresolved',
      'At least one configured package execution entry is missing, unsafe, or cannot be resolved to observed source.',
      unresolved
    ));
  }
  let canonicalSsot = null;
  const mainEntries = configuredEvidence.filter((entry) => entry.key === 'main');
  const mainPath = mainEntries.length === 1
    ? resolvePackageExecutionPath(mainEntries[0].value, sourceFiles)
    : null;
  if (defaultEvidence.length > 0) {
    canonicalSsot = {
      evidence,
      path: 'index.js',
      source: 'node-default-entry'
    };
  } else if (exportPaths.length === 1 && unresolvedExports.length === 0) {
    canonicalSsot = {
      evidence,
      path: exportPaths[0],
      source: 'configured-exports-root-entry'
    };
  } else if (!hasExports && mainPath && unresolved.length === 0) {
    canonicalSsot = {
      evidence,
      path: mainPath,
      source: 'configured-main-entry'
    };
  } else if (!hasExports && executionPaths.length === 1 && unresolved.length === 0) {
    canonicalSsot = {
      evidence,
      path: executionPaths[0],
      source: 'configured-package-entry'
    };
  } else if (!hasExports && executionPaths.length > 1 && unresolved.length === 0) {
    findings.push(issue(
      'inconclusive',
      'canonical-ssot-unresolved',
      'Multiple distinct package execution paths were observed and no unambiguous canonical source was established.',
      evidence
    ));
  } else if (hasExports && exportPaths.length > 1 && unresolvedExports.length === 0) {
    findings.push(issue(
      'inconclusive',
      'canonical-ssot-unresolved',
      'Multiple distinct package-root export targets were observed and no unambiguous canonical source was established.',
      exportEntries
    ));
  }
  return {
    canonicalSsot,
    executionPaths: [...new Set(executionPaths)].sort(),
    findings
  };
}

function collectPackageExecutionEntries(document) {
  if (!document || document.status !== 'present') {
    return [];
  }

  const entries = [];
  if (Object.hasOwn(document.value, 'bin')) {
    const bin = document.value.bin;
    if (typeof bin === 'string') {
      addPackageExecutionEntry(entries, 'bin', bin);
    } else if (isPlainObject(bin)) {
      for (const value of Object.values(bin)) {
        addPackageExecutionEntry(entries, 'bin', value);
      }
    }
  }
  if (Object.hasOwn(document.value, 'exports')) {
    for (const value of collectPackageRootExportTargets(document.value.exports)) {
      addPackageExecutionEntry(entries, 'exports', value);
    }
  }
  for (const key of ['main', 'module']) {
    if (Object.hasOwn(document.value, key)) {
      addPackageExecutionEntry(entries, key, document.value[key]);
    }
  }
  return entries;
}

function addPackageExecutionEntry(entries, key, value) {
  if (typeof value === 'string' && value.length > 0 && !value.includes('*')) {
    entries.push(configEvidence('package.json', key, value));
  }
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

function canUseNodeDefaultEntry(document, sourceFiles) {
  if (!sourceFiles.some((sourceFile) => (typeof sourceFile === 'string' ? sourceFile : sourceFile.path) === 'index.js')) {
    return false;
  }
  if (!document || document.status !== 'present') {
    return true;
  }
  return !['bin', 'exports', 'main', 'module'].some((key) => Object.hasOwn(document.value, key));
}

function resolvePackageExecutionPath(value, sourceFiles) {
  if (typeof value !== 'string' || value.length === 0 || value.includes('\\') || path.posix.isAbsolute(value) || path.win32.isAbsolute(value) || /^[A-Za-z]:/.test(value)) {
    return null;
  }
  const normalized = value.replace(/^\.\//, '');
  if (normalized.split('/').some((segment) => !segment || segment === '.' || segment === '..')) {
    return null;
  }
  const observedPaths = sourceFiles.map((sourceFile) => typeof sourceFile === 'string' ? sourceFile : sourceFile.path);
  if (observedPaths.includes(normalized)) {
    return normalized;
  }
  const extension = path.posix.extname(normalized);
  const base = extension ? normalized.slice(0, -extension.length) : normalized;
  return observedPaths.find((sourceFile) => {
    const sourceExtension = path.posix.extname(sourceFile);
    const sourceBase = sourceFile.slice(0, -sourceExtension.length);
    return sourceBase === base || sourceBase === `${normalized}/index`;
  }) || null;
}

function collectFindings(packageDocument, tsconfigDocuments, scan, dependencyDirection) {
  const findings = [];

  addConfigurationFinding(findings, packageDocument, 'package.json', true);
  addTypeScriptConfigurationFindings(findings, scan.sourceFiles, tsconfigDocuments);

  const productSourceFiles = scan.sourceFiles.filter((sourceFile) => !isTestFile(sourceFile.path));
  if (productSourceFiles.length === 0) {
    findings.push(
      issue('inconclusive', 'no-product-source-files', 'No non-test Node or TypeScript source file was observed.', [
        directoryEvidence('.')
      ])
    );
  }

  for (const scanError of scan.scanErrors) {
    findings.push(
      issue(
        'inconclusive',
        scanError.type === 'source-file' ? 'unreadable-source-file' : 'unreadable-directory',
        `Required repository evidence could not be read at ${scanError.path}.`,
        [fileEvidence(scanError.path, scanError.message)]
      )
    );
  }

  for (const unresolved of dependencyDirection.unresolvedRelativeImports) {
    findings.push(
      issue('fail', 'unresolved-relative-import', `A relative import does not resolve in the target tree: ${unresolved.specifier}.`, [
        importEvidence(unresolved),
        ...unresolved.expectedPaths.map((expectedPath) => fileEvidence(expectedPath))
      ])
    );
  }

  for (const unresolved of dependencyDirection.unresolvedAliases) {
    findings.push(
      issue('fail', 'unresolved-path-alias', `The configured path alias ${unresolved.pattern} does not resolve: ${unresolved.specifier}.`, [
        importEvidence(unresolved),
        ...unresolved.expectedPaths.map((expectedPath) => fileEvidence(expectedPath))
      ])
    );
  }

  for (const outside of dependencyDirection.outsideTargetImports) {
    findings.push(
      issue(
        'inconclusive',
        'dependency-outside-target',
        `A relative import leaves the diagnosed target tree: ${outside.specifier}.`,
        [importEvidence(outside), fileEvidence(outside.attemptedPath)]
      )
    );
  }

  for (const cycle of dependencyDirection.cycles) {
    findings.push(
      issue('risk', 'circular-internal-dependency', 'An internal source dependency cycle was observed.', cycle.map((cyclePath) => fileEvidence(cyclePath)))
    );
  }

  for (const symlinkPath of scan.skippedSymlinks) {
    findings.push(
      issue('inconclusive', 'skipped-symbolic-link', 'A symbolic link prevents complete structural evidence for the target tree.', [
        fileEvidence(symlinkPath)
      ])
    );
  }

  return findings;
}

function addTypeScriptConfigurationFindings(findings, sourceFiles, tsconfigDocuments) {
  const reportedConfigurations = new Set();

  for (const sourceFile of sourceFiles) {
    if (!/\.(cts|mts|tsx|ts)$/.test(sourceFile.path)) {
      continue;
    }

    const tsconfigDocument = findContainingTsconfig(sourceFile.path, tsconfigDocuments);
    if (!tsconfigDocument) {
      findings.push(
        issue(
          'inconclusive',
          'required-missing-tsconfig.json',
          `No containing tsconfig.json was found for TypeScript source ${sourceFile.path}.`,
          [fileEvidence(sourceFile.path)]
        )
      );
      continue;
    }

    const configurationStatus = tsconfigDocument.resolutionStatus || tsconfigDocument.status;
    if (configurationStatus !== 'present' && !reportedConfigurations.has(tsconfigDocument.path)) {
      reportedConfigurations.add(tsconfigDocument.path);
      const configuration = {
        ...tsconfigDocument,
        message: tsconfigDocument.resolutionMessage || tsconfigDocument.message,
        status: configurationStatus
      };
      addConfigurationFinding(findings, configuration, 'tsconfig.json', true, [fileEvidence(sourceFile.path)]);
    }
  }
}

function findContainingTsconfig(sourcePath, tsconfigDocuments) {
  let directoryPath = path.posix.dirname(sourcePath);

  while (true) {
    const tsconfigPath = directoryPath === '.' ? 'tsconfig.json' : `${directoryPath}/tsconfig.json`;
    const document = tsconfigDocuments.get(tsconfigPath);
    if (document) {
      return document;
    }
    if (directoryPath === '.') {
      return null;
    }
    directoryPath = path.posix.dirname(directoryPath);
  }
}

function addConfigurationFinding(findings, document, name, required, additionalEvidence = []) {
  if (document.status === 'present' || !required) {
    return;
  }
  const configurationPath = document.path || name;
  const messageByStatus = {
    invalid: `${configurationPath} could not be parsed as its required configuration format.`,
    missing: `${configurationPath} is required to establish the project structure but was not found.`,
    unreadable: `${configurationPath} is required to establish the project structure but could not be read.`,
    unsupported: `${configurationPath} could not be safely resolved as its required configuration format.`
  };
  findings.push(
    issue('inconclusive', `required-${document.status}-${name}`, messageByStatus[document.status] || `${configurationPath} could not be resolved.`, [
      fileEvidence(configurationPath, document.message),
      ...additionalEvidence
    ])
  );
}

function isTestFile(filePath) {
  const segments = filePath.split('/');
  return (
    segments.some((segment) => ['__tests__', 'test', 'tests'].includes(segment)) ||
    /\.(spec|test)\.[cm]?[jt]sx?$/.test(filePath)
  );
}

function createResult(projectRoot, input) {
  const findings = [...(input.findings || [])].sort((left, right) => {
    const order = VERDICT_ORDER[left.severity] - VERDICT_ORDER[right.severity];
    return order !== 0 ? order : left.code.localeCompare(right.code);
  });
  const verdict = findings.some((finding) => finding.severity === 'fail')
    ? 'FAIL'
    : findings.some((finding) => finding.severity === 'inconclusive')
      ? 'INCONCLUSIVE'
      : 'PASS';
  const responsibilities = input.responsibilities || [];
  const observedResponsibility = describeObservedResponsibility(responsibilities);
  const risks = findings.map((finding) => ({
    code: finding.code,
    evidence: finding.evidence,
    message: finding.message,
    severity: finding.severity
  }));
  const mainRisks = risks.slice(0, 3);
  const summary = { verdict, observedResponsibility, mainRisks };

  return {
    verdict,
    responsibility: observedResponsibility,
    risks,
    summary,
    details: {
      verdict,
      observedResponsibility,
      mainRisks,
      risks,
      project: {
        root: projectRoot,
        packageConfiguration: documentDetail(input.packageDocument),
        tsconfig: documentDetail(input.tsconfigDocument)
      },
      structure: {
        directories: input.scan ? [...input.scan.directories].sort() : [],
        sourceFiles: input.scan ? input.scan.sourceFiles.map((sourceFile) => sourceFile.path) : [],
        boundaries: input.boundaries || []
      },
      responsibilities,
      repositoryAuthority: input.repositoryAuthority || { canonicalSsot: null, executionPaths: [] },
      ssotCandidates: input.ssotCandidates || [],
      reuseCandidates: input.reuseCandidates || [],
      dependencyDirection: input.dependencyDirection || emptyDependencyDirection()
    }
  };
}

function documentDetail(document) {
  if (!document) {
    return null;
  }
  return {
    path: document.path,
    status: document.status,
    ...(document.status === 'present' ? {} : { message: document.message })
  };
}

function emptyDependencyDirection() {
  return {
    cycles: [],
    externalImports: [],
    internalEdges: [],
    internalReferences: [],
    outsideTargetImports: [],
    resolvedArtifacts: [],
    unresolvedAliases: [],
    unresolvedRelativeImports: []
  };
}

function describeObservedResponsibility(responsibilities) {
  const sourceResponsibilities = responsibilities.filter((responsibility) => {
    return !['package.json', 'tsconfig.json'].includes(responsibility.ownerPath);
  });
  const labels = sourceResponsibilities.slice(0, 3).map((responsibility) => {
    return `${responsibility.ownerPath} (${responsibility.responsibility})`;
  });

  if (labels.length > 0) {
    const remaining = sourceResponsibilities.length - labels.length;
    const suffix = remaining > 0 ? `; ${remaining} additional source boundary/boundaries observed` : '';
    return `Observed source responsibility: ${labels.join(', ')}${suffix}.`;
  }
  if (responsibilities.some((responsibility) => responsibility.ownerPath === 'package.json')) {
    return 'Observed responsibility: package entry and runtime configuration in package.json; no product source boundary was established.';
  }
  return 'Observed responsibility: insufficient repository evidence to establish a source responsibility.';
}

function issue(severity, code, message, evidence) {
  return { code, evidence, message, severity };
}

function fileEvidence(filePath, error) {
  return error ? { error, kind: 'file', path: filePath } : { kind: 'file', path: filePath };
}

function directoryEvidence(directoryPath) {
  return { kind: 'directory', path: directoryPath };
}

function configEvidence(filePath, key, value) {
  return { key, kind: 'config', path: filePath, value };
}

function importEvidence(reference) {
  return {
    kind: 'import',
    line: reference.line,
    path: reference.path,
    specifier: reference.specifier,
    syntax: reference.syntax
  };
}

function symbolEvidenceFor(filePath, exported) {
  return { kind: 'symbol', line: exported.line, path: filePath, symbol: exported.symbol };
}

function displayPath(projectRoot, absolutePath) {
  const relativePath = path.relative(projectRoot, absolutePath);
  return relativePath ? relativePath.split(path.sep).join('/') : '.';
}

function isSourceFile(filePath) {
  return SOURCE_EXTENSIONS.some((extension) => filePath.endsWith(extension));
}

function unique(values) {
  return [...new Set(values)];
}

function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

module.exports = Object.freeze({
  admitChange,
  diagnoseFastProject,
  diagnoseProject,
  gateProject
});
