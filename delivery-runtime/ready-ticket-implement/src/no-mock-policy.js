import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const SOURCE_EXTENSIONS = new Set([".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"]);
const CONFIG_EXTENSIONS = new Set([".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".env"]);
const JS_EXTENSIONS = [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".json"];
const PY_EXTENSIONS = [".py"];

const TAINT_RULES = [
  ["PY_UNITTEST_MOCK", /(?:from\s+unittest(?:\.mock)?\s+import\s+[^\n]*(?:\bmock\b|\bMock\b|\bMagicMock\b|\bAsyncMock\b|\bpatch\b|\bcreate_autospec\b)|import\s+unittest\.mock\b)/m],
  ["PY_PATCH_API", /\b(?:Mock|MagicMock|AsyncMock|PropertyMock|create_autospec|patch)(?:\.object)?\s*\(/],
  ["PY_PYTEST_PATCH", /\b(?:monkeypatch|mocker)(?:\.|\b)/],
  ["PY_PYTEST_MONKEYPATCH_CLASS", /(?:from\s+pytest\s+import\s+[^\n]*\bMonkeyPatch\b|\bpytest\.MonkeyPatch\b)/],
  ["PY_INTERCEPT_LIBRARY", /(?:^|\n)\s*(?:from|import)\s+(?:mock|responses|requests_mock|respx|httpretty|vcr|moto|aioresponses|mongomock|fakeredis|botocore\.stub)\b/m],
  ["JS_MOCK_API", /\b(?:jest|vi)\.(?:mock|doMock|fn|spyOn)\s*\(/],
  ["JS_MOCK_OBJECT_IMPORT", /import\s*\{[^}]*\b(?:vi|jest)\b[^}]*\}\s*from\s*["'](?:vitest|@jest\/globals)["']/],
  ["JS_MOCK_ALIAS", /\b(?:const|let|var)\s+[A-Za-z_$][A-Za-z0-9_$]*\s*=\s*(?:vi|jest|sinon)\b/],
  ["JS_SINON", /(?:from\s+["']sinon["']|require\(\s*["']sinon["']\s*\)|\bsinon\.(?:stub|mock|spy|replace)\s*\()/],
  ["JS_INTERCEPT_LIBRARY", /(?:from\s+["'](?:nock|msw|fetch-mock|axios-mock-adapter|proxyquire|mock-require|aws-sdk-client-mock|pg-mem|sequelize-mock|mock-knex)["']|require\(\s*["'](?:nock|msw|fetch-mock|axios-mock-adapter|proxyquire|mock-require|aws-sdk-client-mock|pg-mem|sequelize-mock|mock-knex)["']\s*\))/],
  ["JS_UNDICI_MOCK", /\b(?:MockAgent|MockPool|MockClient)\b/],
  ["FAKE_IMPLEMENTATION", /\b(?:class|function)\s+[A-Za-z0-9_]*(?:Mock|Fake|Stub|InMemory|Memory)[A-Za-z0-9_]*(?:Repository|Provider|Client|Database|Db|DB|Http|HTTP|Transport|Service|Store)\b|\b(?:class|function)\s+[A-Za-z0-9_]*(?:Repository|Provider|Client|Database|Db|DB|Http|HTTP|Transport|Service|Store)[A-Za-z0-9_]*(?:Mock|Fake|Stub|InMemory|Memory)\b/],
  ["IN_MEMORY_PERSISTENCE", /(?:["']:\s*memory:["']|["']:memory:["']|mode=memory\b|\bpg-mem\b|\bmongomock\b|\bfakeredis\b)/i],
  ["MOCK_MODE_ENV", /\b(?:process\.env\.|os\.getenv\(\s*["']|os\.environ\[\s*["']|getenv\(\s*["']|env\[\s*["'])(?:[A-Z0-9_]*(?:MOCK|FAKE|STUB)[A-Z0-9_]*)/i],
  ["MOCK_ENV_ASSIGNMENT", /(?:^|\s)[A-Z0-9_]*(?:MOCK|FAKE|STUB)[A-Z0-9_]*\s*=/i],
  ["MOCK_MODE_CONFIG", /(?:^|[\s,{])["']?(?:use[_-]?mock|mock[_-]?mode|fake[_-]?(?:provider|db|database|repository)|stub[_-]?(?:provider|client))["']?\s*[:=]/im],
];

function realpathExisting(raw, label) {
  const resolved = fs.realpathSync(raw);
  if (!fs.statSync(resolved).isFile()) throw new Error(`${label} is not a file: ${resolved}`);
  return resolved;
}

export function fileDigest(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

export function directTaint(text, file = "<memory>") {
  const violations = [];
  for (const [code, pattern] of TAINT_RULES) {
    if (pattern.test(text)) violations.push({ code, path: file, detail: `Zero-Mock policy matched ${code}` });
  }
  return violations;
}

export function environmentTaint(env = process.env) {
  return Object.entries(env)
    .filter(([key, value]) => /(?:MOCK|FAKE|STUB)/i.test(key) && value != null && String(value) !== "" && !/^(0|false|off|no)$/i.test(String(value)))
    .map(([key]) => ({ code: "MOCK_MODE_ENV_ACTIVE", path: "<environment>", detail: `active mock/fake/stub environment flag: ${key}` }));
}

function candidateFile(base) {
  for (const suffix of ["", ...JS_EXTENSIONS, ...PY_EXTENSIONS]) {
    const direct = suffix ? `${base}${suffix}` : base;
    if (fs.existsSync(direct) && fs.statSync(direct).isFile()) return fs.realpathSync(direct);
  }
  for (const name of ["index.js", "index.ts", "index.tsx", "__init__.py"]) {
    const nested = path.join(base, name);
    if (fs.existsSync(nested) && fs.statSync(nested).isFile()) return fs.realpathSync(nested);
  }
  return null;
}

function pythonImports(file, text, projectRoot) {
  const found = [];
  for (const match of text.matchAll(/^\s*(?:from\s+([.A-Za-z0-9_]+)\s+import\s+[^\n]+|import\s+([A-Za-z0-9_.]+))/gm)) {
    const specifier = match[1] || match[2];
    if (!specifier) continue;
    if (specifier.startsWith(".")) {
      const dots = specifier.match(/^\.+/)?.[0]?.length ?? 0;
      const rest = specifier.slice(dots).replaceAll(".", path.sep);
      let base = path.dirname(file);
      for (let index = 1; index < dots; index += 1) base = path.dirname(base);
      const candidate = candidateFile(path.join(base, rest));
      if (candidate) found.push(candidate);
      continue;
    }
    const candidate = candidateFile(path.join(projectRoot, specifier.replaceAll(".", path.sep)));
    if (candidate) found.push(candidate);
  }
  return found;
}

function javascriptImports(file, text) {
  const found = [];
  const pattern = /(?:import[\s\S]*?from\s*|export[\s\S]*?from\s*|import\s*\(|require\s*\()\s*["']([^"']+)["']/g;
  for (const match of text.matchAll(pattern)) {
    const specifier = match[1];
    if (!specifier?.startsWith(".")) continue;
    const candidate = candidateFile(path.resolve(path.dirname(file), specifier));
    if (candidate) found.push(candidate);
  }
  return found;
}

function localImports(file, text, projectRoot) {
  const extension = path.extname(file).toLowerCase();
  if (extension === ".py") return pythonImports(file, text, projectRoot);
  if ([".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"].includes(extension)) return javascriptImports(file, text);
  return [];
}

export function scanFileGraph(projectRoot, roots) {
  const canonicalRoot = fs.realpathSync(projectRoot);
  const queue = [];
  for (const raw of roots || []) {
    const absolute = path.isAbsolute(raw) ? raw : path.resolve(canonicalRoot, raw);
    if (!fs.existsSync(absolute) || !fs.statSync(absolute).isFile()) {
      queue.push({ missing: absolute });
      continue;
    }
    queue.push({ file: fs.realpathSync(absolute), via: null });
  }
  const visited = new Set();
  const violations = [];
  const scannedPaths = [];
  const parents = new Map();

  while (queue.length > 0) {
    const item = queue.shift();
    if (item.missing) {
      violations.push({ code: "EVIDENCE_PATH_MISSING", path: item.missing, detail: "required Zero-Mock evidence path is missing" });
      continue;
    }
    const file = item.file;
    if (visited.has(file)) continue;
    visited.add(file);
    scannedPaths.push(file);
    if (item.via) parents.set(file, item.via);
    const extension = path.extname(file).toLowerCase();
    const base = path.basename(file);
    if (!SOURCE_EXTENSIONS.has(extension) && !CONFIG_EXTENSIONS.has(extension) && !base.startsWith(".env")) continue;
    const text = fs.readFileSync(file, "utf8");
    for (const violation of directTaint(text, file)) {
      const chain = [file];
      let cursor = file;
      while (parents.has(cursor)) {
        cursor = parents.get(cursor);
        chain.unshift(cursor);
      }
      violations.push({ ...violation, import_chain: chain });
    }
    for (const dependency of localImports(file, text, canonicalRoot)) {
      if (!visited.has(dependency)) queue.push({ file: dependency, via: file });
    }
  }
  return { mock_taint: violations.length > 0, violations, scanned_paths: scannedPaths };
}

export function scanProspectiveMutation(input, targetPath) {
  const strings = [];
  const walk = value => {
    if (typeof value === "string") strings.push(value);
    else if (Array.isArray(value)) value.forEach(walk);
    else if (value && typeof value === "object") Object.values(value).forEach(walk);
  };
  walk(input);
  return strings.flatMap(text => directTaint(text, targetPath || "<mutation-input>"));
}

export function resolveEvidencePath(projectRoot, raw, label = "evidence path") {
  const canonicalRoot = fs.realpathSync(projectRoot);
  const absolute = path.isAbsolute(raw) ? path.resolve(raw) : path.resolve(canonicalRoot, raw);
  const resolved = realpathExisting(absolute, label);
  const relative = path.relative(canonicalRoot, resolved);
  if (relative === ".." || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
    throw new Error(`${label} is outside Project Root: ${resolved}`);
  }
  return resolved;
}

function simpleTokens(text) {
  if (/[|&;<>()$`\n\r]/.test(text)) throw new Error("acceptance package script contains shell control syntax");
  const tokens = text.trim().split(/\s+/).filter(Boolean);
  if (tokens.length === 0) throw new Error("empty acceptance runner");
  return tokens;
}

function standardRunner(argv) {
  const executable = path.basename(argv[0]).toLowerCase();
  if (["pytest", "py.test", "jest", "vitest"].includes(executable)) return executable;
  if (/^python(?:3(?:\.\d+)?)?$/.test(executable) && argv[1] === "-m" && ["pytest", "unittest"].includes(argv[2])) return `python -m ${argv[2]}`;
  if (executable === "node" && argv.includes("--test")) return "node --test";
  if (executable === "bun" && argv[1] === "test") return "bun test";
  return null;
}

export function resolveAcceptanceRunner(argv, projectRoot, depth = 0) {
  if (!Array.isArray(argv) || argv.length === 0 || argv.some(value => typeof value !== "string" || !value)) throw new Error("acceptance argv must be a non-empty string array");
  if (depth > 2) throw new Error("acceptance package script indirection is too deep");
  const direct = standardRunner(argv);
  if (direct) return { runner: direct, argv: argv.slice() };
  const executable = path.basename(argv[0]).toLowerCase();
  if (!["npm", "pnpm", "yarn"].includes(executable)) throw new Error(`unverifiable custom acceptance runner: ${argv[0]}`);
  let scriptName = null;
  if (argv[1] === "test") scriptName = "test";
  else if (argv[1] === "run" && argv[2]) scriptName = argv[2];
  else if (executable === "yarn" && argv[1]) scriptName = argv[1];
  if (!scriptName) throw new Error(`unverifiable package acceptance command: ${argv.join(" ")}`);
  const packageJson = resolveEvidencePath(projectRoot, "package.json", "package.json");
  const payload = JSON.parse(fs.readFileSync(packageJson, "utf8"));
  const script = payload?.scripts?.[scriptName];
  if (typeof script !== "string") throw new Error(`package script is unavailable: ${scriptName}`);
  const nested = resolveAcceptanceRunner(simpleTokens(script), projectRoot, depth + 1);
  return { ...nested, package_script: scriptName, package_json: packageJson };
}

export function productionPathProvenance(projectRoot, evidencePaths, productionEntrypoint) {
  const production = resolveEvidencePath(projectRoot, productionEntrypoint, "production entrypoint");
  const normalized = production.replace(/\\/g, "/");
  if (/(^|\/)(?:test|tests|__tests__|fixtures?|mocks?|stubs?|fakes?)(\/|$)/i.test(normalized)) {
    throw new Error(`production entrypoint points to a test/fake surface: ${production}`);
  }
  const graph = scanFileGraph(projectRoot, evidencePaths);
  const basename = path.basename(production);
  const referenced = graph.scanned_paths.includes(production) || (evidencePaths || []).some(raw => {
    const file = resolveEvidencePath(projectRoot, raw);
    const text = fs.readFileSync(file, "utf8");
    return text.includes(productionEntrypoint) || text.includes(basename);
  });
  if (!referenced) {
    graph.violations.push({
      code: "PRODUCTION_PATH_UNPROVEN",
      path: production,
      detail: "acceptance evidence does not import or reference the declared production entrypoint",
    });
    graph.mock_taint = true;
  }
  return { production_entrypoint: production, ...graph };
}

export function dependencyProvenance(projectRoot, dependencyPaths) {
  if (!Array.isArray(dependencyPaths) || dependencyPaths.length === 0) throw new Error("acceptance provenance requires at least one actual dependency/config path");
  return dependencyPaths.map(raw => {
    const resolved = resolveEvidencePath(projectRoot, raw, "dependency/config path");
    return { path: resolved, sha256: fileDigest(resolved) };
  });
}
