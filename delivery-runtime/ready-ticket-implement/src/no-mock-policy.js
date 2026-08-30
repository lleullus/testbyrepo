import { analyzeJavaScriptStructure, identifierBindingScope, isIdentifierLexicallyBound } from "./import-structure.js";
import { isReadOnlyArgv, runArgv } from "./argv-policy.js";
import { spawnSync } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
const SOURCE_EXTENSIONS = new Set([".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"]);
const CONFIG_EXTENSIONS = new Set([".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".env"]);
const JS_EXTENSIONS = [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".json"];
const CLEAN_PROVENANCE_KINDS = new Set(["LOCAL_PATH", "LOCAL_SQLITE"]);
const PY_EXTENSIONS = [".py"];

const TAINT_RULES = [
  ["PY_UNITTEST_MOCK", /(?:from\s+unittest(?:\.mock)?\s+import\s+[^\n]*(?:\bmock\b|\bMock\b|\bMagicMock\b|\bAsyncMock\b|\bpatch\b|\bcreate_autospec\b)|import\s+unittest\.mock\b)/m],
  ["PY_PATCH_API", /\b(?:Mock|MagicMock|AsyncMock|PropertyMock|create_autospec|patch)(?:\.object)?\s*\(/],
  ["PY_PYTEST_PATCH", /\b(?:monkeypatch|mocker)(?:\.|\b)/],
  ["PY_PYTEST_MONKEYPATCH_CLASS", /(?:from\s+pytest\s+import\s+[^\n]*\bMonkeyPatch\b|\bpytest\.MonkeyPatch\b)/],
  ["PY_INTERCEPT_LIBRARY", /(?:^|\n)\s*(?:from|import)\s+(?:mock|responses|requests_mock|respx|httpretty|vcr|moto|aioresponses|mongomock|fakeredis|botocore\.stub)\b/m],
  ["FAKE_IMPLEMENTATION", /\b(?:class|function)\s+[A-Za-z0-9_]*(?:Mock|Fake|Stub|InMemory|Memory)[A-Za-z0-9_]*(?:Repository|Provider|Client|Database|Db|DB|Http|HTTP|Transport|Service|Store)\b|\b(?:class|function)\s+[A-Za-z0-9_]*(?:Repository|Provider|Client|Database|Db|DB|Http|HTTP|Transport|Service|Store)[A-Za-z0-9_]*(?:Mock|Fake|Stub|InMemory|Memory)\b/],
  ["IN_MEMORY_PERSISTENCE", /(?:["']:\s*memory:["']|["']:memory:["']|mode=memory\b|\bpg-mem\b|\bmongomock\b|\bfakeredis\b)/i],
  ["MOCK_MODE_ENV", /\b(?:process\.env\.|os\.getenv\(\s*["']|os\.environ\[\s*["']|getenv\(\s*["']|env\[\s*["'])(?:[A-Z0-9_]*(?:MOCK|FAKE|STUB)[A-Z0-9_]*)/i],
  ["MOCK_ENV_ASSIGNMENT", /(?:^|\s)[A-Z0-9_]*(?:MOCK|FAKE|STUB)[A-Z0-9_]*\s*=/i],
  ["MOCK_MODE_CONFIG", /(?:^|[\s,{])["']?(?:use[_-]?mock|mock[_-]?mode|fake[_-]?(?:provider|db|database|repository)|stub[_-]?(?:provider|client))["']?\s*[:=]/im],
];

const JS_FILE_EXTENSIONS = new Set([".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"]);
const JS_INTERCEPT_SOURCES = new Set([
  "nock", "msw", "fetch-mock", "axios-mock-adapter", "proxyquire", "mock-require",
  "aws-sdk-client-mock", "pg-mem", "sequelize-mock", "mock-knex",
]);

function realpathExisting(raw, label) {
  const resolved = fs.realpathSync(raw);
  if (!fs.statSync(resolved).isFile()) throw new Error(`${label} is not a file: ${resolved}`);
  return resolved;
}

export function fileDigest(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function isJavaScriptInput(text, file) {
  if (JS_FILE_EXTENSIONS.has(path.extname(file).toLowerCase())) return true;
  if (!(file.startsWith("<") && file.endsWith(">"))) return false;
  return /(?:\b(?:const|let|var|export)\b|=>|\brequire\s*\(|\bimport\s*\(|\bimport\s*(?:["'{*]|[A-Za-z_$][A-Za-z0-9_$]*\s+from\b)|\b(?:vi|jest|sinon)\s*(?:[.(]|\[)|\b(?:globalThis|window|self|global)\s*(?:\.|\[)|\b(?:MockAgent|MockPool|MockClient)\b)/.test(text);
}

const JS_MOCK_OBJECT_METHODS = new Set(["mock", "doMock", "fn", "spyOn"]);
const JS_SINON_METHODS = new Set(["stub", "mock", "spy", "replace"]);
const JS_GLOBAL_HOSTS = new Set(["globalThis", "window", "self", "global"]);
const JS_MOCK_GLOBALS = new Set(["vi", "jest", "sinon"]);
const JS_MOCK_SOURCES = new Set(["vitest", "@jest/globals", "sinon"]);
const MAX_JS_MOCK_FLOW_PASSES = 64;

function matchingOpen(tokens, closeIndex, openValue, closeValue) {
  let depth = 0;
  for (let index = closeIndex; index >= 0; index -= 1) {
    if (tokens[index].value === closeValue) depth += 1;
    else if (tokens[index].value === openValue) {
      depth -= 1;
      if (depth === 0) return index;
    }
  }
  return -1;
}

function matchingClose(tokens, openIndex, openValue, closeValue) {
  let depth = 0;
  for (let index = openIndex; index < tokens.length; index += 1) {
    if (tokens[index].value === openValue) depth += 1;
    else if (tokens[index].value === closeValue) {
      depth -= 1;
      if (depth === 0) return index;
    }
  }
  return -1;
}

function isDefinitionBoundary(token) {
  return !token || ["{", "}", ",", ";"].includes(token.value);
}

function isMethodDefinitionName(tokens, index) {
  if (tokens[index]?.type !== "identifier" || tokens[index + 1]?.value !== "(") return false;
  const close = matchingClose(tokens, index + 1, "(", ")");
  if (close < 0 || tokens[close + 1]?.value !== "{") return false;

  let start = index;
  if (tokens[start - 1]?.value === "*") start -= 1;
  if (["async", "get", "set"].includes(tokens[start - 1]?.value)) start -= 1;
  if (tokens[start - 1]?.value === "static") start -= 1;
  return isDefinitionBoundary(tokens[start - 1]);
}

function enclosingBrace(tokens, index) {
  let depth = 0;
  for (let cursor = index - 1; cursor >= 0; cursor -= 1) {
    if (tokens[cursor].value === "}") depth += 1;
    else if (tokens[cursor].value === "{") {
      if (depth === 0) return cursor;
      depth -= 1;
    }
  }
  return -1;
}

function isClassBodyOpen(tokens, open) {
  let parentheses = 0;
  let brackets = 0;
  let braces = 0;
  for (let index = open - 1; index >= 0; index -= 1) {
    const value = tokens[index].value;
    if (value === ")") parentheses += 1;
    else if (value === "(" && parentheses > 0) parentheses -= 1;
    else if (value === "]") brackets += 1;
    else if (value === "[" && brackets > 0) brackets -= 1;
    else if (value === "}") braces += 1;
    else if (value === "{" && braces > 0) braces -= 1;
    if (parentheses || brackets || braces) continue;
    if (value === "class") return true;
    if ([";", "{", "}"].includes(value)) return false;
  }
  return false;
}

function isClassFieldDefinitionName(tokens, index) {
  if (tokens[index]?.type !== "identifier") return false;
  const next = tokens[index + 1]?.value;
  if (!["=", ";", ":", "}"].includes(next)) return false;

  let start = index;
  if (tokens[start - 1]?.value === "static") start -= 1;
  if (!isDefinitionBoundary(tokens[start - 1])) return false;
  const open = enclosingBrace(tokens, start);
  return open >= 0 && isClassBodyOpen(tokens, open);
}

function isStaticPropertyDefinitionName(tokens, index) {
  return isMethodDefinitionName(tokens, index) || isClassFieldDefinitionName(tokens, index);
}

function staticMemberAt(tokens, index) {
  if ([".", "?."].includes(tokens[index]?.value) && tokens[index + 1]?.type === "identifier") {
    return { name: tokens[index + 1].value, next: index + 2 };
  }
  if (tokens[index]?.value === "[" && tokens[index + 1]?.type === "string" && tokens[index + 2]?.value === "]") {
    return { name: tokens[index + 1].value, next: index + 3 };
  }
  return null;
}
function destructuredPropertyAt(tokens, cursor, close) {
  const token = tokens[cursor];
  if (token?.type === "identifier" || token?.type === "string") {
    return { property: token.value, next: cursor + 1, dynamic: false };
  }
  if (token?.value !== "[") return null;
  const bracketClose = matchingClose(tokens, cursor, "[", "]");
  if (bracketClose < 0 || bracketClose >= close) return null;
  const staticString = bracketClose === cursor + 2 && tokens[cursor + 1]?.type === "string";
  return {
    property: staticString ? tokens[cursor + 1].value : null,
    next: bracketClose + 1,
    dynamic: !staticString,
  };
}


function destructuredEntries(tokens, open, close) {
  const entries = [];
  let cursor = open + 1;
  while (cursor < close) {
    while (tokens[cursor]?.value === ",") cursor += 1;
    const property = destructuredPropertyAt(tokens, cursor, close);
    if (!property) {
      cursor += 1;
      continue;
    }
    let target = tokens[cursor]?.type === "identifier" ? tokens[cursor].value : null;
    let targetIndex = cursor;
    cursor = property.next;
    if (tokens[cursor]?.value === ":" && tokens[cursor + 1]?.type === "identifier") {
      target = tokens[cursor + 1].value;
      targetIndex = cursor + 1;
      cursor += 2;
    }
    if (target) entries.push({ property: property.property, target, targetIndex, dynamic: property.dynamic });
    let depth = 0;
    while (cursor < close) {
      const value = tokens[cursor].value;
      if (["(", "[", "{"].includes(value)) depth += 1;
      else if ([")", "]", "}"].includes(value)) depth -= 1;
      if (value === "," && depth === 0) break;
      cursor += 1;
    }
  }
  return entries;
}


function isRuntimeGlobalReference(structure, index) {
  const { tokens } = structure;
  const token = tokens[index];
  if (token.type !== "identifier" || !JS_MOCK_GLOBALS.has(token.value)
    || isIdentifierLexicallyBound(structure, index, token.value)) return false;
  if ([".", "?."].includes(tokens[index - 1]?.value)) return false;
  if (isStaticPropertyDefinitionName(tokens, index)) return false;
  if (tokens[index + 1]?.value === ":" && ["{", ","].includes(tokens[index - 1]?.value)) return false;
  if (tokens[index + 1]?.value === "as") return false;
  if (["const", "let", "var", "class", "function", "import", "export", "as"].includes(tokens[index - 1]?.value)) return false;
  return true;
}

function memberAuthority(authority, member) {
  if (authority === "global-host") {
    if (["vi", "jest"].includes(member)) return "mock-object";
    if (member === "sinon") return "sinon-object";
  }
  if (authority === "mock-namespace") {
    if (["vi", "jest"].includes(member)) return "mock-object";
    if (JS_MOCK_OBJECT_METHODS.has(member)) return "mock-function";
  }
  if (authority === "mock-object" && JS_MOCK_OBJECT_METHODS.has(member)) return "mock-function";
  if (authority === "sinon-object" && JS_SINON_METHODS.has(member)) return "mock-function";
  return null;
}

function mockBindingFacts(structure) {
  const tokens = structure.tokens;
  const bindings = new Map();
  const occurrences = [];
  const candidates = [];
  const bindingKey = (name, index) => `${identifierBindingScope(structure, index, name)}:${name}`;
  const recordOccurrence = (authority, source, token) => {
    occurrences.push({ authority, source, line: token.line });
  };

  for (const imported of structure.imports) {
    if (!JS_MOCK_SOURCES.has(imported.specifier)) continue;
    for (const binding of imported.bindings) {
      let authority = null;
      if (imported.specifier === "sinon") {
        authority = ["default", "*"].includes(binding.imported) ? "sinon-object"
          : JS_SINON_METHODS.has(binding.imported) ? "mock-function" : null;
      } else if (["default", "*"].includes(binding.imported)) authority = "mock-namespace";
      else if (["vi", "jest"].includes(binding.imported)) authority = "mock-object";
      else if (JS_MOCK_OBJECT_METHODS.has(binding.imported)) authority = "mock-function";
      if (authority) bindings.set(`0:${binding.local}`, authority);
    }
  }

  const resolveExpression = start => {
    let cursor = start;
    let authority = null;
    const base = tokens[cursor];
    if (base?.type === "identifier" && JS_GLOBAL_HOSTS.has(base.value)) {
      authority = "global-host";
      cursor += 1;
    } else if (base?.type === "identifier" && bindings.has(bindingKey(base.value, cursor))) {
      authority = bindings.get(bindingKey(base.value, cursor));
      cursor += 1;
    } else if (base?.type === "identifier" && isRuntimeGlobalReference(structure, cursor)) {
      authority = base.value === "sinon" ? "sinon-object" : "mock-object";
      cursor += 1;
    } else if (base?.value === "require" && tokens[cursor + 1]?.value === "("
      && tokens[cursor + 2]?.type === "string" && tokens[cursor + 3]?.value === ")") {
      const source = tokens[cursor + 2].value;
      authority = source === "sinon" ? "sinon-object"
        : ["vitest", "@jest/globals"].includes(source) ? "mock-namespace" : null;
      cursor += 4;
    }
    if (!authority) return null;
    while (true) {
      const member = staticMemberAt(tokens, cursor);
      if (!member) break;
      authority = memberAuthority(authority, member.name);
      if (!authority) return null;
      cursor = member.next;
    }
    return authority;
  };

  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];
    if (isRuntimeGlobalReference(structure, index)) {
      recordOccurrence(token.value === "sinon" ? "sinon-object" : "mock-object", token.value, token);
    }
    if (token.type === "identifier" && JS_GLOBAL_HOSTS.has(token.value)) {
      const member = staticMemberAt(tokens, index + 1);
      const authority = member && memberAuthority("global-host", member.name);
      if (authority) recordOccurrence(authority, `${token.value}.${member.name}`, token);
    }
    if (token.value !== "=") continue;
    if (tokens[index - 1]?.type === "identifier"
      && ![".", "?.", ":"].includes(tokens[index - 2]?.value)
      && !isClassFieldDefinitionName(tokens, index - 1)) {
      candidates.push({ targets: [{ target: tokens[index - 1].value, targetIndex: index - 1, property: null }], source: index + 1 });
    } else if (tokens[index - 1]?.value === "}") {
      const open = matchingOpen(tokens, index - 1, "{", "}");
      if (open >= 0) candidates.push({ targets: destructuredEntries(tokens, open, index - 1), source: index + 1 });
    }
  }

  const limit = Math.min(MAX_JS_MOCK_FLOW_PASSES, candidates.length + 1);
  for (let pass = 0; pass < limit; pass += 1) {
    let changed = false;
    for (const candidate of candidates) {
      const sourceAuthority = resolveExpression(candidate.source);
      if (!sourceAuthority) continue;
      for (const { target, targetIndex, property, dynamic } of candidate.targets) {
        const authority = dynamic ? "mock-function"
          : property !== null ? memberAuthority(sourceAuthority, property) : sourceAuthority;
        const key = bindingKey(target, targetIndex);
        if (authority && !bindings.has(key)) {
          bindings.set(key, authority);
          changed = true;
        }
      }
    }
    if (!changed) break;
  }
  return { bindings, occurrences };
}

function javascriptTaint(structure, file) {
  const violations = [];
  const add = (code, detail = `Zero-Mock policy matched ${code}`) => {
    if (!violations.some(item => item.code === code)) violations.push({ code, path: file, detail });
  };

  if (structure.errors.length > 0) {
    const details = structure.errors.map(error => `line ${error.line}: ${error.message}`).join("; ");
    add("JS_STRUCTURE_PARSE_ERROR", `JavaScript/TypeScript structure parse failed closed: ${details}`);
  }

  for (const imported of structure.imports) {
    if (imported.specifier === "vitest" || imported.specifier === "@jest/globals") add("JS_MOCK_OBJECT_IMPORT");
    else if (imported.specifier === "sinon") add("JS_SINON");
    else if (JS_INTERCEPT_SOURCES.has(imported.specifier)) add("JS_INTERCEPT_LIBRARY");
  }

  const facts = mockBindingFacts(structure);
  if (facts.occurrences.some(item => ["mock-object", "mock-function"].includes(item.authority))) add("JS_MOCK_API");
  if (facts.occurrences.some(item => item.authority === "sinon-object")) add("JS_SINON");
  if (facts.bindings.size > 0) add("JS_MOCK_ALIAS");

  for (const current of structure.tokens) {
    if (["MockAgent", "MockPool", "MockClient"].includes(current.value)) add("JS_UNDICI_MOCK");
  }
  return violations;
}

export function directTaint(text, file = "<memory>", structure = null) {
  const violations = [];
  for (const [code, pattern] of TAINT_RULES) {
    if (pattern.test(text)) violations.push({ code, path: file, detail: `Zero-Mock policy matched ${code}` });
  }
  if (isJavaScriptInput(text, file)) {
    violations.push(...javascriptTaint(structure || analyzeJavaScriptStructure(text), file));
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

const PYTHON_AST_PARSER_SCRIPT = `import ast, json, os, sys
try:
    source = sys.stdin.read()
    tree = ast.parse(source)
except Exception as exc:
    sys.stderr.write(f"Python AST parse error: {exc}\\n")
    sys.exit(1)

source_file = os.path.abspath(sys.argv[1])
imports = []
references = []
assignments = {}
for candidate_node in tree.body:
    if isinstance(candidate_node, (ast.Assign, ast.AnnAssign)):
        targets = candidate_node.targets if isinstance(candidate_node, ast.Assign) else [candidate_node.target]
        value = candidate_node.value
        for target in targets:
            if isinstance(target, ast.Name):
                assignments[target.id] = value
resolving_names = set()


def literal(node):
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None

def dotted_name(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None

def static_path(node):
    value = literal(node)
    if value is not None:
        return value
    if isinstance(node, ast.Name):
        if node.id == "__file__":
            return source_file
        assigned = assignments.get(node.id)
        if assigned is None or node.id in resolving_names:
            return None
        resolving_names.add(node.id)
        try:
            return static_path(assigned)
        finally:
            resolving_names.remove(node.id)
    if isinstance(node, ast.Attribute) and node.attr == "parent":
        base = static_path(node.value)
        return os.path.dirname(base) if base is not None else None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left, right = static_path(node.left), literal(node.right)
        return os.path.join(left, right) if left is not None and right is not None else None
    if not isinstance(node, ast.Call):
        return None
    name = dotted_name(node.func)
    if name in ("Path", "pathlib.Path", "PurePath", "pathlib.PurePath"):
        parts = [static_path(arg) for arg in node.args]
        return os.path.join(*parts) if parts and all(part is not None for part in parts) else None
    if isinstance(node.func, ast.Attribute):
        base = static_path(node.func.value)
        args = [literal(arg) for arg in node.args]
        if base is not None and node.func.attr == "with_name" and len(args) == 1 and args[0] is not None:
            return os.path.join(os.path.dirname(base), args[0])
        if base is not None and node.func.attr == "joinpath" and args and all(arg is not None for arg in args):
            return os.path.join(base, *args)
    return None

for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        names = [alias.name for alias in node.names if getattr(alias, "name", None)]
        if names:
            imports.append({"type": "import", "names": names})
    elif isinstance(node, ast.ImportFrom):
        names = [alias.name for alias in node.names if getattr(alias, "name", None)]
        imports.append({"type": "import_from", "module": node.module, "level": int(node.level or 0), "names": names})
    elif isinstance(node, ast.Call):
        name = dotted_name(node.func)
        candidate = None
        if name in ("open", "io.open", "sqlite3.connect", "Path", "pathlib.Path", "PurePath", "pathlib.PurePath") and node.args:
            candidate = static_path(node.args[0])
        elif isinstance(node.func, ast.Attribute) and node.func.attr in ("with_name", "joinpath", "read_text", "write_text", "read_bytes", "write_bytes"):
            candidate = static_path(node)
            if candidate is None and node.func.attr in ("read_text", "write_text", "read_bytes", "write_bytes"):
                candidate = static_path(node.func.value)
        if candidate is not None:
            references.append(candidate)

sys.stdout.write(json.dumps({"imports": imports, "path_references": references}))
`;

function isInsideRoot(candidatePath, canonicalRoot) {
  const relative = path.relative(canonicalRoot, candidatePath);
  return relative === "" || (!relative.startsWith(`..${path.sep}`) && relative !== ".." && !path.isAbsolute(relative));
}

function pythonImports(file, text, projectRoot) {
  let canonicalRoot;
  try {
    canonicalRoot = fs.realpathSync(projectRoot);
  } catch {
    canonicalRoot = path.resolve(projectRoot);
  }

  const result = spawnSync("python3", ["-c", PYTHON_AST_PARSER_SCRIPT, file], {
    input: text,
    encoding: "utf8",
    maxBuffer: 10 * 1024 * 1024,
  });

  if (result.error) {
    throw new Error(`Failed to execute python3 for ${file}: ${result.error.message}`);
  }
  if (result.status !== 0) {
    const stderr = result.stderr ? result.stderr.trim() : "";
    throw new Error(`Failed to parse Python AST for ${file} (exit ${result.status}): ${stderr}`);
  }

  let astResult;
  try {
    astResult = JSON.parse(result.stdout || "{}");
  } catch (error) {
    throw new Error(`Failed to parse Python AST JSON output for ${file}: ${error.message}`);
  }

  const found = new Set();

  const addCandidate = (basePath) => {
    const candidate = candidateFile(basePath);
    if (candidate && isInsideRoot(candidate, canonicalRoot)) {
      found.add(candidate);
    }
  };

  for (const item of astResult.imports || []) {
    if (item.type === "import") {
      for (const name of item.names || []) {
        if (!name) continue;
        const parts = name.split(".");
        for (let i = 1; i <= parts.length; i += 1) {
          const subpath = parts.slice(0, i).join(path.sep);
          addCandidate(path.join(canonicalRoot, subpath));
        }
      }
    } else if (item.type === "import_from") {
      let baseDir = canonicalRoot;
      const level = item.level || 0;
      if (level > 0) {
        baseDir = path.dirname(file);
        for (let i = 1; i < level; i += 1) {
          baseDir = path.dirname(baseDir);
        }
      }

      let targetBase = baseDir;
      if (item.module) {
        const moduleParts = item.module.split(".");
        for (let i = 1; i <= moduleParts.length; i += 1) {
          addCandidate(path.join(baseDir, ...moduleParts.slice(0, i)));
        }
        targetBase = path.join(baseDir, ...moduleParts);
      } else {
        addCandidate(targetBase);
      }

      for (const name of item.names || []) {
        if (!name || name === "*") continue;
        const nameParts = name.split(".");
        addCandidate(path.join(targetBase, ...nameParts));
      }
    }
  }

  return { imports: Array.from(found), pathReferences: astResult.path_references || [] };
}

function javascriptImports(file, structure) {
  const found = new Set();
  for (const imported of structure.imports) {
    const specifier = imported.specifier;
    if (!(specifier?.startsWith("./") || specifier?.startsWith("../"))) continue;
    const candidate = candidateFile(path.resolve(path.dirname(file), specifier));
    if (candidate) found.add(candidate);
  }
  return Array.from(found);
}

function localStructure(file, text, projectRoot, structure = null) {
  const extension = path.extname(file).toLowerCase();
  if (extension === ".py") return pythonImports(file, text, projectRoot);
  if (JS_FILE_EXTENSIONS.has(extension)) {
    const analyzed = structure || analyzeJavaScriptStructure(text);
    return { imports: javascriptImports(file, analyzed), pathReferences: analyzed.pathReferences || [] };
  }
  return { imports: [], pathReferences: [] };
}

function canonicalReferenceCandidates(raw, sourceFile, canonicalRoot) {
  if (typeof raw !== "string" || raw.length === 0 || raw.includes("\0") || /^[a-z][a-z0-9+.-]*:/i.test(raw)) return [];
  const candidates = path.isAbsolute(raw)
    ? [path.resolve(raw)]
    : [path.resolve(path.dirname(sourceFile), raw), path.resolve(canonicalRoot, raw)];
  const resolved = new Set();
  for (const candidate of candidates) {
    let existing = candidate;
    const suffix = [];
    while (!fs.existsSync(existing)) {
      const parent = path.dirname(existing);
      if (parent === existing) break;
      suffix.unshift(path.basename(existing));
      existing = parent;
    }
    if (!fs.existsSync(existing)) continue;
    const canonical = path.resolve(fs.realpathSync(existing), ...suffix);
    if (isInsideRoot(canonical, canonicalRoot)) resolved.add(canonical);
  }
  return Array.from(resolved);
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
  const referencedPaths = new Set();

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
    const structure = JS_FILE_EXTENSIONS.has(extension) ? analyzeJavaScriptStructure(text) : null;
    for (const violation of directTaint(text, file, structure)) {
      const chain = [file];
      let cursor = file;
      while (parents.has(cursor)) {
        cursor = parents.get(cursor);
        chain.unshift(cursor);
      }
      violations.push({ ...violation, import_chain: chain });
    }
    const local = localStructure(file, text, canonicalRoot, structure);
    for (const dependency of local.imports) {
      if (!visited.has(dependency)) queue.push({ file: dependency, via: file });
    }
    if (SOURCE_EXTENSIONS.has(extension)) {
      for (const reference of local.pathReferences) {
        for (const candidate of canonicalReferenceCandidates(reference, file, canonicalRoot)) {
          referencedPaths.add(candidate);
        }
      }
    }
  }
  return {
    mock_taint: violations.length > 0,
    violations,
    scanned_paths: scannedPaths,
    referenced_paths: Array.from(referencedPaths),
  };
}

function isPlainFingerprintRecord(value) {
  if (Object.prototype.toString.call(value) !== "[object Object]") return false;
  const prototype = Object.getPrototypeOf(value);
  if (prototype === null) return true;
  if (Object.getPrototypeOf(prototype) !== null) return false;
  const constructor = Object.getOwnPropertyDescriptor(prototype, "constructor")?.value;
  return (
    typeof constructor === "function" &&
    constructor.prototype === prototype &&
    Function.prototype.toString.call(constructor) === Function.prototype.toString.call(Object)
  );
}

function canonicalFingerprintValue(value, logicalPath = "$") {
  if (value === null || typeof value === "string" || typeof value === "boolean") return value;
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (Array.isArray(value)) return value.map((item, index) => canonicalFingerprintValue(item, `${logicalPath}[${index}]`));
  if (value && typeof value === "object" && isPlainFingerprintRecord(value)) {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map(key => {
          const childPath = `${logicalPath}[${JSON.stringify(key)}]`;
          const childValue = value[key];
          if (childValue === undefined) throw new Error(`fingerprint payload contains undefined at ${childPath}`);
          return [key, canonicalFingerprintValue(childValue, childPath)];
        }),
    );
  }
  const kind = value && typeof value === "object" ? Object.prototype.toString.call(value) : typeof value;
  throw new Error(`fingerprint payload contains an unsupported value at ${logicalPath}: ${kind}`);
}

export function serializeEvidenceFingerprintPayload(payload) {
  return JSON.stringify(canonicalFingerprintValue(payload));
}

function fingerprintPathEntries(paths, label) {
  return [...new Set(paths)].sort().map(file => {
    let stat;
    try {
      stat = fs.statSync(file);
    } catch (error) {
      throw new Error(`${label} is unavailable while building fingerprint: ${file}: ${error.message}`);
    }
    if (!stat.isFile()) throw new Error(`${label} is not a file while building fingerprint: ${file}`);
    try {
      return { path: file, sha256: fileDigest(file) };
    } catch (error) {
      throw new Error(`${label} cannot be digested while building fingerprint: ${file}: ${error.message}`);
    }
  });
}

function fingerprintClosure(projectRoot, roots, label) {
  const graph = scanFileGraph(projectRoot, roots);
  const missing = graph.violations.filter(item => item.code === "EVIDENCE_PATH_MISSING");
  if (missing.length > 0) {
    throw new Error(`${label} closure is incomplete: ${missing.map(item => item.path).join(", ")}`);
  }
  const files = fingerprintPathEntries(graph.scanned_paths, `${label} closure member`);
  const scanned = new Set(files.map(item => item.path));
  for (const root of roots) {
    if (!scanned.has(root)) throw new Error(`${label} closure omitted root: ${root}`);
  }
  return files;
}

function fingerprintReadback(projectRoot, descriptor) {
  if (!descriptor || descriptor.available !== true) throw new Error("fingerprint requires an available authoritative readback");
  if (descriptor.kind === "path") {
    const readbackPath = resolveEvidencePath(projectRoot, descriptor.path, "authoritative readback path");
    const currentSha256 = fingerprintPathEntries([readbackPath], "authoritative readback")[0].sha256;
    if (descriptor.sha256 !== undefined && descriptor.sha256 !== currentSha256) {
      throw new Error(`authoritative readback changed before fingerprinting: ${readbackPath}`);
    }
    return { kind: "path", path: readbackPath, sha256: currentSha256 };
  }
  if (descriptor.kind === "argv") {
    if (!Array.isArray(descriptor.argv) || descriptor.argv.length === 0 || descriptor.argv.some(value => typeof value !== "string" || !value)) {
      throw new Error("fingerprint authoritative readback argv must be a non-empty string array");
    }
    if (!Number.isInteger(descriptor.exit_code) || typeof descriptor.stdout_sha256 !== "string" || !/^[a-f0-9]{64}$/.test(descriptor.stdout_sha256)) {
      throw new Error("fingerprint authoritative readback argv lacks exit/stdout identity");
    }
    return {
      kind: "argv",
      argv: descriptor.argv.slice(),
      exit_code: descriptor.exit_code,
      timed_out: descriptor.timed_out === true,
      stdout_sha256: descriptor.stdout_sha256,
    };
  }
  throw new Error(`unsupported authoritative readback kind: ${descriptor.kind}`);
}

const DIRECT_INSPECTION_RUNNER_KEYS = ["command_argv", "package_json", "package_script", "resolved_argv", "runner"];

function isExactDirectInspectionRunner(descriptor) {
  return descriptor?.runner === "direct-inspection"
    && Object.keys(descriptor).sort().join("\0") === DIRECT_INSPECTION_RUNNER_KEYS.join("\0")
    && Array.isArray(descriptor.command_argv)
    && descriptor.command_argv.length === 0
    && Array.isArray(descriptor.resolved_argv)
    && descriptor.resolved_argv.length === 0
    && descriptor.package_script === null
    && descriptor.package_json === null;
}

function fingerprintRunner(projectRoot, descriptor) {
  if (!descriptor || typeof descriptor.runner !== "string" || !descriptor.runner) throw new Error("fingerprint requires a resolved runner descriptor");
  if (descriptor.runner === "direct-inspection") {
    if (!isExactDirectInspectionRunner(descriptor)) {
      throw new Error("fingerprint direct-inspection runner must have exact empty command and no-package identity");
    }
    return {
      command_argv: [],
      resolved_argv: [],
      runner: "direct-inspection",
      package_script: null,
      package_json: null,
    };
  }
  for (const field of ["command_argv", "resolved_argv"]) {
    if (!Array.isArray(descriptor[field]) || descriptor[field].length === 0 || descriptor[field].some(value => typeof value !== "string" || !value)) {
      throw new Error(`fingerprint runner ${field} must be a non-empty string array`);
    }
  }
  const runner = {
    command_argv: descriptor.command_argv.slice(),
    resolved_argv: descriptor.resolved_argv.slice(),
    runner: descriptor.runner,
    package_script: descriptor.package_script ?? null,
    package_json: null,
  };
  if (descriptor.package_json) {
    const packageJson = resolveEvidencePath(projectRoot, descriptor.package_json, "runner package.json");
    runner.package_json = fingerprintPathEntries([packageJson], "runner package.json")[0];
  }
  return runner;
}

export function buildEvidenceFingerprint({
  projectRoot,
  mutationRevision,
  provenanceKind,
  productionEntrypoint,
  evidenceRootPaths,
  dependencyPaths,
  authoritativeReadback,
  resolvedRunner,
}) {
  const canonicalRoot = fs.realpathSync(projectRoot);
  if (!fs.statSync(canonicalRoot).isDirectory()) throw new Error(`Project Root is not a directory: ${canonicalRoot}`);
  if (!Number.isInteger(mutationRevision) || mutationRevision < 0) throw new Error("fingerprint mutation revision must be a non-negative integer");
  if (!CLEAN_PROVENANCE_KINDS.has(provenanceKind)) throw new Error(`fingerprint provenance kind is unsupported: ${provenanceKind}`);
  const production = resolveEvidencePath(canonicalRoot, productionEntrypoint, "production entrypoint");
  const evidenceRoots = [...new Set((evidenceRootPaths || []).map(raw => resolveEvidencePath(canonicalRoot, raw, "evidence root path")))].sort();
  if (evidenceRoots.length === 0) throw new Error("fingerprint requires at least one evidence root path");
  const dependencies = [...new Set((dependencyPaths || []).map(raw => resolveEvidencePath(canonicalRoot, raw, "dependency/config path")))].sort();
  const productionDigest = fingerprintPathEntries([production], "production entrypoint")[0].sha256;
  const payload = {
    schema: "iis.ready_evidence_fingerprint",
    version: 1,
    project_root: canonicalRoot,
    mutation_revision: mutationRevision,
    provenance_kind: provenanceKind,
    production: {
      entrypoint: { path: production, sha256: productionDigest },
      local_import_closure: fingerprintClosure(canonicalRoot, [production], "production"),
    },
    evidence: {
      roots: evidenceRoots,
      local_import_closure: fingerprintClosure(canonicalRoot, evidenceRoots, "evidence"),
    },
    dependencies: fingerprintPathEntries(dependencies, "dependency/config path"),
    authoritative_readback: fingerprintReadback(canonicalRoot, authoritativeReadback),
    runner: fingerprintRunner(canonicalRoot, resolvedRunner),
  };
  const canonicalPayload = canonicalFingerprintValue(payload);
  const serialized = serializeEvidenceFingerprintPayload(canonicalPayload);
  return {
    payload: canonicalPayload,
    sha256: crypto.createHash("sha256").update(serialized).digest("hex"),
  };
}

function evidenceStale(message, cause = undefined) {
  return new Error(`EVIDENCE_STALE: ${message}`, cause === undefined ? undefined : { cause });
}

function requireFingerprintRecord(value, label) {
  if (!isPlainFingerprintRecord(value)) throw evidenceStale(`${label} is missing or malformed`);
  return value;
}

function requireFingerprintPath(value, label) {
  if (typeof value !== "string" || value.length === 0) throw evidenceStale(`${label} is missing or malformed`);
  return value;
}

export async function revalidateEvidenceFingerprint({
  projectRoot,
  mutationRevision,
  provenance,
  signal,
}) {
  try {
    const fingerprint = requireFingerprintRecord(provenance?.fingerprint, "stored evidence fingerprint");
    const payload = requireFingerprintRecord(fingerprint.payload, "stored evidence fingerprint payload");
    if (typeof fingerprint.sha256 !== "string" || !/^[a-f0-9]{64}$/.test(fingerprint.sha256)) {
      throw evidenceStale("stored evidence fingerprint SHA-256 is missing or malformed");
    }
    const storedPayloadSha256 = crypto
      .createHash("sha256")
      .update(serializeEvidenceFingerprintPayload(payload))
      .digest("hex");
    if (storedPayloadSha256 !== fingerprint.sha256) {
      throw evidenceStale("stored evidence fingerprint payload does not match its SHA-256");
    }

    if (payload.schema !== "iis.ready_evidence_fingerprint" || payload.version !== 1) {
      throw evidenceStale("stored evidence fingerprint schema or version is unsupported");
    }
    const canonicalRoot = fs.realpathSync(projectRoot);
    if (payload.project_root !== canonicalRoot) throw evidenceStale("stored evidence fingerprint Project Root changed");
    if (!Number.isInteger(mutationRevision) || mutationRevision < 0) {
      throw evidenceStale("current execution mutation revision is invalid");
    }
    if (provenance?.mutation_revision !== mutationRevision || payload.mutation_revision !== mutationRevision) {
      throw evidenceStale("stored evidence fingerprint mutation revision is not current");
    }
    if (!CLEAN_PROVENANCE_KINDS.has(payload.provenance_kind)) {
      throw evidenceStale(`stored evidence fingerprint provenance kind is unsupported: ${payload.provenance_kind}`);
    }
    if (provenance?.provenance_kind !== payload.provenance_kind) {
      throw evidenceStale("stored evidence provenance kind does not match its fingerprint");
    }

    const production = requireFingerprintRecord(payload.production, "stored production identity");
    const productionEntrypoint = requireFingerprintPath(
      requireFingerprintRecord(production.entrypoint, "stored production entrypoint").path,
      "stored production entrypoint path",
    );
    const evidence = requireFingerprintRecord(payload.evidence, "stored evidence identity");
    if (!Array.isArray(evidence.roots) || evidence.roots.length === 0) {
      throw evidenceStale("stored evidence root identity is missing or malformed");
    }
    const evidenceRootPaths = evidence.roots.map((item, index) => requireFingerprintPath(item, `stored evidence root ${index}`));
    if (!Array.isArray(payload.dependencies)) throw evidenceStale("stored dependency identity is missing or malformed");
    const dependencyPaths = payload.dependencies.map((item, index) => requireFingerprintPath(
      requireFingerprintRecord(item, `stored dependency ${index}`).path,
      `stored dependency path ${index}`,
    ));

    const storedReadback = requireFingerprintRecord(payload.authoritative_readback, "stored authoritative readback identity");
    let authoritativeReadback;
    if (storedReadback.kind === "path") {
      authoritativeReadback = {
        available: true,
        kind: "path",
        path: requireFingerprintPath(storedReadback.path, "stored authoritative readback path"),
      };
    } else if (storedReadback.kind === "argv") {
      if (!Array.isArray(storedReadback.argv) || storedReadback.argv.length === 0 || !isReadOnlyArgv(storedReadback.argv)) {
        throw evidenceStale("stored authoritative readback argv is not on the current read-only allowlist");
      }
      const readbackResult = await runArgv(storedReadback.argv, { cwd: canonicalRoot, signal });
      authoritativeReadback = {
        available: readbackResult.exitCode === 0 && !readbackResult.timedOut,
        kind: "argv",
        argv: storedReadback.argv.slice(),
        exit_code: readbackResult.exitCode,
        timed_out: readbackResult.timedOut,
        stdout_sha256: crypto.createHash("sha256").update(readbackResult.stdout).digest("hex"),
      };
    } else {
      throw evidenceStale(`stored authoritative readback kind is unsupported: ${storedReadback.kind}`);
    }

    const storedRunner = requireFingerprintRecord(payload.runner, "stored runner identity");
    let currentRunner;
    if (storedRunner.runner === "direct-inspection") {
      if (!isExactDirectInspectionRunner(storedRunner)) {
        throw evidenceStale("stored direct-inspection runner must have exact empty command and no-package identity");
      }
      currentRunner = {
        runner: "direct-inspection",
        command_argv: [],
        resolved_argv: [],
        package_script: null,
        package_json: null,
      };
    } else {
      for (const field of ["command_argv", "resolved_argv"]) {
        if (!Array.isArray(storedRunner[field]) || storedRunner[field].length === 0) {
          throw evidenceStale(`stored runner ${field} identity is missing or malformed`);
        }
      }
      const resolvedRunner = {
        runner: storedRunner.runner,
        command_argv: storedRunner.command_argv.slice(),
        resolved_argv: storedRunner.resolved_argv.slice(),
        argv: storedRunner.resolved_argv.slice(),
        package_script: storedRunner.package_script,
        package_json: storedRunner.package_json === null
          ? null
          : requireFingerprintPath(
            requireFingerprintRecord(storedRunner.package_json, "stored runner package.json identity").path,
            "stored runner package.json path",
          ),
      };
      try {
        currentRunner = resolveAcceptanceRunner(resolvedRunner.command_argv, canonicalRoot);
      } catch (error) {
        throw evidenceStale(`stored acceptance command no longer resolves: ${error.message}`, error);
      }
      if (
        currentRunner.runner !== resolvedRunner.runner
        || JSON.stringify(currentRunner.resolved_argv) !== JSON.stringify(resolvedRunner.resolved_argv)
        || (currentRunner.package_script ?? null) !== (resolvedRunner.package_script ?? null)
        || (currentRunner.package_json ?? null) !== (resolvedRunner.package_json ?? null)
      ) {
        throw evidenceStale("current acceptance command resolution does not match stored runner identity");
      }
    }
    const rebuilt = buildEvidenceFingerprint({
      projectRoot: canonicalRoot,
      mutationRevision,
      provenanceKind: payload.provenance_kind,
      productionEntrypoint,
      evidenceRootPaths,
      dependencyPaths,
      authoritativeReadback,
      resolvedRunner: currentRunner,
    });
    if (rebuilt.sha256 !== fingerprint.sha256) {
      throw evidenceStale("current evidence fingerprint does not match stored clean evidence");
    }
    return rebuilt;
  } catch (error) {
    if (String(error?.message ?? error).startsWith("EVIDENCE_STALE:")) throw error;
    throw evidenceStale(String(error?.message ?? error), error);
  }
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

function packageInvocation(argv) {
  const manager = path.basename(argv[0]).toLowerCase();
  if (!["npm", "pnpm", "yarn"].includes(manager)) return null;
  let scriptName;
  let forwarded;
  if (manager === "npm" || manager === "pnpm") {
    if (argv[1] === "test") {
      scriptName = "test";
      forwarded = argv.slice(2);
    } else if (argv[1] === "run" && argv[2] && !argv[2].startsWith("-")) {
      scriptName = argv[2];
      forwarded = argv.slice(3);
    } else {
      throw new Error(`unverifiable package acceptance command: ${argv.join(" ")}`);
    }
    if (forwarded.length > 0) {
      if (forwarded[0] !== "--" || forwarded.slice(1).includes("--")) {
        throw new Error(`ambiguous package acceptance option placement: ${argv.join(" ")}`);
      }
      forwarded = forwarded.slice(1);
    }
  } else {
    if (argv[1] === "run") {
      if (!argv[2] || argv[2].startsWith("-")) throw new Error(`unverifiable package acceptance command: ${argv.join(" ")}`);
      scriptName = argv[2];
      forwarded = argv.slice(3);
    } else {
      if (!argv[1] || argv[1].startsWith("-")) throw new Error(`unverifiable package acceptance command: ${argv.join(" ")}`);
      scriptName = argv[1];
      forwarded = argv.slice(2);
    }
    if (forwarded[0] === "--") forwarded = forwarded.slice(1);
    if (forwarded.includes("--")) throw new Error(`ambiguous package acceptance option placement: ${argv.join(" ")}`);
  }
  return { manager, scriptName, forwarded };
}

export function resolveAcceptanceRunner(argv, projectRoot) {
  if (!Array.isArray(argv) || argv.length === 0 || argv.some(value => typeof value !== "string" || !value)) throw new Error("acceptance argv must be a non-empty string array");
  const direct = standardRunner(argv);
  if (direct) {
    return { runner: direct, argv: argv.slice(), command_argv: argv.slice(), resolved_argv: argv.slice() };
  }
  const invocation = packageInvocation(argv);
  if (!invocation) throw new Error(`unverifiable custom acceptance runner: ${argv[0]}`);
  const packageJson = resolveEvidencePath(projectRoot, "package.json", "package.json");
  const payload = JSON.parse(fs.readFileSync(packageJson, "utf8"));
  const scripts = payload?.scripts;
  const script = scripts?.[invocation.scriptName];
  if (typeof script !== "string") throw new Error(`package script is unavailable: ${invocation.scriptName}`);
  const lifecycleHooks = [`pre${invocation.scriptName}`, `post${invocation.scriptName}`];
  const configuredHook = lifecycleHooks.find(hook => Object.hasOwn(scripts, hook));
  if (configuredHook) {
    throw new Error(`PACKAGE_ACCEPTANCE_LIFECYCLE_HOOK_UNSUPPORTED: package script ${invocation.scriptName} has adjacent lifecycle hook ${configuredHook}`);
  }
  const scriptArgv = simpleTokens(script);
  const runner = standardRunner(scriptArgv);
  if (!runner) throw new Error(`package script must resolve directly to one standard acceptance runner: ${invocation.scriptName}`);
  const resolvedArgv = [...scriptArgv, ...invocation.forwarded];
  if (standardRunner(resolvedArgv) !== runner) throw new Error(`forwarded arguments changed the package acceptance runner: ${invocation.scriptName}`);
  return {
    runner,
    argv: resolvedArgv.slice(),
    command_argv: argv.slice(),
    resolved_argv: resolvedArgv,
    package_script: invocation.scriptName,
    package_json: packageJson,
  };
}

function canonicalSelectedFile(projectRoot, raw, extensions) {
  if (!raw || raw.startsWith("-") || /[*?\[\]{}]/.test(raw)) throw new Error(`unsupported or non-explicit acceptance selector: ${raw}`);
  const selectorPath = raw.split("::", 1)[0];
  const file = resolveEvidencePath(projectRoot, selectorPath, "selected acceptance test");
  if (!fs.statSync(file).isFile() || !extensions.has(path.extname(file).toLowerCase())) {
    throw new Error(`selected acceptance target is not a supported test file: ${raw}`);
  }
  return file;
}

function globPatternRegex(pattern) {
  if (!pattern || pattern.includes("/") || pattern.includes("\\") || /[\[\]{}]/.test(pattern)) {
    throw new Error(`unsupported unittest discovery pattern: ${pattern}`);
  }
  let source = "^";
  for (const character of pattern) {
    if (character === "*") source += ".*";
    else if (character === "?") source += ".";
    else source += character.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }
  return new RegExp(`${source}$`);
}

function canonicalProjectDirectory(projectRoot, raw, label) {
  const canonicalRoot = fs.realpathSync(projectRoot);
  const absolute = path.isAbsolute(raw) ? path.resolve(raw) : path.resolve(canonicalRoot, raw);
  const resolved = fs.realpathSync(absolute);
  const relative = path.relative(canonicalRoot, resolved);
  if (relative === ".." || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
    throw new Error(`${label} is outside Project Root: ${resolved}`);
  }
  if (!fs.statSync(resolved).isDirectory()) throw new Error(`${label} is not a directory: ${resolved}`);
  return resolved;
}

function discoverPythonFiles(projectRoot, startDirectory, pattern) {
  const start = canonicalProjectDirectory(projectRoot, startDirectory, "unittest discovery start directory");
  const matcher = globPatternRegex(pattern);
  const selected = [];
  const visit = directory => {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name))) {
      const candidate = path.join(directory, entry.name);
      if (entry.isSymbolicLink()) throw new Error(`unittest discovery cannot attribute symlinked targets: ${candidate}`);
      if (entry.isDirectory()) {
        if (fs.existsSync(path.join(candidate, "__init__.py"))) visit(candidate);
      } else if (
        entry.isFile() &&
        /^[_a-z]\w*\.py$/i.test(entry.name) &&
        matcher.test(entry.name)
      ) {
        selected.push(resolveEvidencePath(projectRoot, candidate, "selected unittest discovery test"));
      }
    }
  };
  visit(start);
  if (selected.length === 0) throw new Error("unittest discovery selected no attributable test files");
  return selected;
}

function unittestModuleFile(projectRoot, selector) {
  const pathSelector = selector.split("::", 1)[0];
  if (pathSelector.includes("/") || pathSelector.includes("\\") || pathSelector.endsWith(".py")) {
    return canonicalSelectedFile(projectRoot, pathSelector, new Set([".py"]));
  }
  const parts = pathSelector.split(".");
  for (let length = parts.length; length > 0; length -= 1) {
    const candidate = `${parts.slice(0, length).join(path.sep)}.py`;
    try {
      return canonicalSelectedFile(projectRoot, candidate, new Set([".py"]));
    } catch (error) {
      if (length === 1) throw new Error(`unittest module selector does not resolve to a project-local test file: ${selector}`, { cause: error });
    }
  }
  throw new Error(`unittest module selector is unsupported: ${selector}`);
}

function parseUnittestRoots(argv, projectRoot) {
  const args = argv.slice(3);
  if (args[0] === "discover") {
    let start = null;
    let pattern = null;
    for (let index = 1; index < args.length; index += 1) {
      const option = args[index];
      if (option !== "-s" && option !== "--start-directory" && option !== "-p" && option !== "--pattern") {
        throw new Error(`unsupported unittest discover flag or operand: ${option}`);
      }
      const value = args[++index];
      if (!value || value.startsWith("-")) throw new Error(`unittest discover option requires a value: ${option}`);
      if (option === "-s" || option === "--start-directory") {
        if (start !== null) throw new Error("duplicate unittest discover start directory");
        start = value;
      } else {
        if (pattern !== null) throw new Error("duplicate unittest discover pattern");
        pattern = value;
      }
    }
    if (start === null || pattern === null) throw new Error("unittest discover requires explicit -s and -p selectors");
    return discoverPythonFiles(projectRoot, start, pattern);
  }
  const targets = [];
  const valueOptions = new Set(["-k"]);
  const flagOptions = new Set(["-v", "--verbose", "-q", "--quiet", "-f", "--failfast", "-c", "--catch", "-b", "--buffer"]);
  for (let index = 0; index < args.length; index += 1) {
    const token = args[index];
    if (flagOptions.has(token)) continue;
    if (valueOptions.has(token)) {
      if (!args[++index] || args[index].startsWith("-")) throw new Error(`unittest option requires a value: ${token}`);
      continue;
    }
    if (token.startsWith("-")) throw new Error(`unsupported unittest option: ${token}`);
    targets.push(unittestModuleFile(projectRoot, token));
  }
  if (targets.length === 0) throw new Error("unittest requires explicit project-local module or path selectors");
  return targets;
}

function explicitFileRoots(args, projectRoot, extensions, grammar) {
  const roots = [];
  let positionalOnly = false;
  for (let index = 0; index < args.length; index += 1) {
    const token = args[index];
    if (!positionalOnly && token === "--") {
      positionalOnly = true;
      continue;
    }
    if (!positionalOnly && token.startsWith("-")) {
      const equals = token.indexOf("=");
      const option = equals === -1 ? token : token.slice(0, equals);
      if (grammar.flags.has(option)) continue;
      if (grammar.values.has(option)) {
        if (equals !== -1) {
          if (equals === token.length - 1) throw new Error(`acceptance runner option requires a value: ${option}`);
        } else if (!args[++index] || args[index].startsWith("-")) {
          throw new Error(`acceptance runner option requires a value: ${option}`);
        }
        continue;
      }
      throw new Error(`unsupported acceptance runner option: ${token}`);
    }
    roots.push(canonicalSelectedFile(projectRoot, token, extensions));
  }
  if (roots.length === 0) throw new Error("acceptance runner requires explicit project-local test file operands");
  return roots;
}

export function deriveAcceptanceTestRoots(resolvedRunner, projectRoot) {
  const argv = resolvedRunner?.resolved_argv;
  if (!Array.isArray(argv) || argv.length === 0) throw new Error("resolved acceptance argv is unavailable");
  if (resolvedRunner.runner === "python -m unittest") return [...new Set(parseUnittestRoots(argv, projectRoot))].sort();
  const pyExtensions = new Set([".py"]);
  const jsExtensions = new Set([".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"]);
  if (["pytest", "py.test", "python -m pytest"].includes(resolvedRunner.runner)) {
    const offset = resolvedRunner.runner === "python -m pytest" ? 3 : 1;
    return [...new Set(explicitFileRoots(argv.slice(offset), projectRoot, pyExtensions, {
      flags: new Set(["-q", "--quiet", "-v", "--verbose", "-s", "-x", "--exitfirst", "--disable-warnings", "--strict-markers"]),
      values: new Set(["-k", "-m", "--maxfail", "--rootdir", "--confcutdir", "--basetemp", "--override-ini", "-o", "--import-mode"]),
    }))].sort();
  }
  if (resolvedRunner.runner === "node --test") {
    if (argv[1] !== "--test") throw new Error("node acceptance grammar requires --test immediately after node");
    return [...new Set(explicitFileRoots(argv.slice(2), projectRoot, jsExtensions, {
      flags: new Set(["--test-only", "--test-force-exit"]),
      values: new Set(["--test-name-pattern", "--test-skip-pattern", "--test-reporter", "--test-concurrency"]),
    }))].sort();
  }
  if (resolvedRunner.runner === "bun test") {
    return [...new Set(explicitFileRoots(argv.slice(2), projectRoot, jsExtensions, {
      flags: new Set(["--bail", "--coverage", "--watch"]),
      values: new Set(["-t", "--test-name-pattern", "--timeout", "--preload"]),
    }))].sort();
  }
  if (["jest", "vitest"].includes(resolvedRunner.runner)) {
    const offset = resolvedRunner.runner === "vitest" && argv[1] === "run" ? 2 : 1;
    return [...new Set(explicitFileRoots(argv.slice(offset), projectRoot, jsExtensions, {
      flags: new Set(["--runInBand", "--runTestsByPath", "--passWithNoTests", "--silent", "--verbose", "--run"]),
      values: new Set(["-t", "--testNamePattern", "--config", "--project", "--testTimeout", "--maxWorkers"]),
    }))].sort();
  }
  throw new Error(`unsupported acceptance runner selection grammar: ${resolvedRunner.runner}`);
}

export function assertAcceptanceEvidenceBinding(projectRoot, resolvedRunner, evidencePaths) {
  const selected = deriveAcceptanceTestRoots(resolvedRunner, projectRoot);
  const evidence = [...new Set(evidencePaths.map(raw => resolveEvidencePath(projectRoot, raw, "acceptance evidence path")))].sort();
  if (selected.length !== evidence.length || selected.some((file, index) => file !== evidence[index])) {
    const selectedSet = new Set(selected);
    const evidenceSet = new Set(evidence);
    const missing = selected.filter(file => !evidenceSet.has(file));
    const extra = evidence.filter(file => !selectedSet.has(file));
    throw new Error(`ACCEPTANCE_EVIDENCE_BINDING_MISMATCH: selected test roots and evidence_paths differ; missing evidence: ${missing.join(", ") || "none"}; extra evidence: ${extra.join(", ") || "none"}`);
  }
  return selected;
}

export function productionPathProvenance(projectRoot, evidencePaths, productionEntrypoint) {
  const production = resolveEvidencePath(projectRoot, productionEntrypoint, "production entrypoint");
  const normalized = production.replace(/\\/g, "/");
  if (/(^|\/)(?:test|tests|__tests__|fixtures?|mocks?|stubs?|fakes?)(\/|$)/i.test(normalized)) {
    throw new Error(`production entrypoint points to a test/fake surface: ${production}`);
  }
  const graph = scanFileGraph(projectRoot, evidencePaths);
  const referenced = graph.scanned_paths.includes(production);
  if (!referenced) {
    graph.violations.push({
      code: "PRODUCTION_PATH_UNPROVEN",
      path: production,
      detail: "acceptance evidence import closure does not include the declared production entrypoint",
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
