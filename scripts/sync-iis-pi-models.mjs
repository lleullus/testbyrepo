#!/usr/bin/env node
import { execFile } from "node:child_process";
import { createHash, randomUUID } from "node:crypto";
import { open, readFile, realpath, rename, rm, stat } from "node:fs/promises";
import { homedir, tmpdir } from "node:os";
import { basename, dirname, isAbsolute, join, resolve } from "node:path";
import { createRequire } from "node:module";

const PROVIDER = "opencodex";
const REQUIRED_DEFAULTS = ["gpt-5.6-luna"];
const THINKING_LEVELS = ["minimal", "low", "medium", "high", "xhigh", "max"];
const SUPPORTED_APIS = new Set(["openai-completions", "openai-responses"]);
const SMOKE_TEXT = "IIS_PI_MODEL_SYNC_SMOKE_OK";

function execute(command, args, options = {}) {
  const { promise, resolve: resolveExecution, reject } = Promise.withResolvers();
  const child = execFile(
    command,
    args,
    { encoding: "utf8", maxBuffer: 16 * 1024 * 1024, timeout: 300_000, ...options },
    (error, stdout, stderr) => {
      if (error) {
        error.stdout = stdout;
        error.stderr = stderr;
        reject(error);
      } else {
        resolveExecution({ stdout, stderr });
      }
    },
  );
  child.stdin?.end();
  return promise;
}

function sha256(content) {
  return createHash("sha256").update(content).digest("hex");
}

function safeError(error) {
  const message = error instanceof Error ? error.message : String(error);
  return message
    .replace(/\bBearer\s+[^\s,;]+/gi, "Bearer [REDACTED]")
    .replace(/\b(?:sk|ghp|github_pat|xox[baprs])[-_][A-Za-z0-9_-]{8,}\b/g, "[REDACTED]")
    .replace(
      /(\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret)\b\s*[:=]\s*)(?:"[^"\n]*"|'[^'\n]*'|[^\s,;]+)/gi,
      "$1[REDACTED]",
    );
}

async function resolveExecutable(command) {
  if (isAbsolute(command) || command.includes("/")) return realpath(resolve(command));
  const result = await execute("which", [command], { timeout: 30_000 });
  const resolved = result.stdout.trim();
  if (!resolved) throw new Error(`executable not found: ${command}`);
  return realpath(resolved);
}

async function loadYamlParser(piExecutable) {
  const requireFromPi = createRequire(piExecutable);
  const yaml = requireFromPi("yaml");
  if (typeof yaml.parse !== "function") throw new Error("Pi runtime YAML parser is unavailable");
  return yaml.parse;
}

async function snapshot(path, required) {
  try {
    const content = await readFile(path);
    return { exists: true, content, hash: sha256(content) };
  } catch (error) {
    if (!required && error?.code === "ENOENT") return { exists: false, content: Buffer.alloc(0), hash: null };
    throw error;
  }
}

function sameSnapshot(left, right) {
  return left.exists === right.exists && left.hash === right.hash;
}

function requireRecord(value, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error(`${label} must be an object`);
  return value;
}

function requireString(value, label) {
  if (typeof value !== "string" || !value.trim()) throw new Error(`${label} must be a non-empty string`);
  return value.trim();
}

function requirePositiveInteger(value, label) {
  if (!Number.isInteger(value) || value <= 0) throw new Error(`${label} must be a positive integer`);
  return value;
}

function normalizeInput(value, label) {
  if (!Array.isArray(value) || !value.length || value.some((entry) => entry !== "text" && entry !== "image")) {
    throw new Error(`${label} must contain supported modalities`);
  }
  return [...value];
}

function convertThinking(source, effective, label) {
  const authored = source.thinking === undefined ? undefined : requireRecord(source.thinking, `${label}.thinking`);
  if (authored?.mode !== undefined && authored.mode !== "effort") throw new Error(`${label}.thinking.mode must be effort`);
  const efforts = authored?.efforts ?? effective.thinking ?? [];
  if (!Array.isArray(efforts) || efforts.some((level) => !THINKING_LEVELS.includes(level))) {
    throw new Error(`${label}.thinking efforts are invalid`);
  }
  const supported = new Set(efforts);
  return Object.fromEntries(THINKING_LEVELS.map((level) => [level, supported.has(level) ? level : null]));
}

function convertCatalog(ompConfig, effectiveCatalog, currentPiConfig) {
  const providers = requireRecord(ompConfig.providers, "OMP providers");
  const sourceProvider = requireRecord(providers[PROVIDER], `OMP provider ${PROVIDER}`);
  const sourceModels = sourceProvider.models;
  if (!Array.isArray(sourceModels) || !sourceModels.length) throw new Error(`OMP provider ${PROVIDER} has no models`);

  const effectiveById = new Map();
  for (const model of effectiveCatalog) {
    const record = requireRecord(model, "effective OMP model");
    if (record.provider !== PROVIDER) throw new Error(`unexpected effective provider: ${record.provider}`);
    const id = requireString(record.id, "effective model id");
    if (effectiveById.has(id)) throw new Error(`duplicate effective OMP model: ${id}`);
    effectiveById.set(id, record);
  }

  const sourceIds = new Set(sourceModels.map((model, index) => requireString(requireRecord(model, `OMP model ${index}`).id, `OMP model ${index}.id`)));
  const effectiveIds = new Set(effectiveById.keys());
  const unavailable = [...sourceIds].filter((id) => !effectiveIds.has(id));
  const unauthored = [...effectiveIds].filter((id) => !sourceIds.has(id));
  if (unavailable.length || unauthored.length) {
    throw new Error(`OMP catalog authority mismatch: unavailable=${unavailable.join(",") || "none"}; unauthored=${unauthored.join(",") || "none"}`);
  }

  const providerApi = requireString(sourceProvider.api, `OMP ${PROVIDER}.api`);
  if (!SUPPORTED_APIS.has(providerApi)) throw new Error(`unsupported provider API family: ${providerApi}`);
  const convertedModels = sourceModels.map((rawModel, index) => {
    const source = requireRecord(rawModel, `OMP model ${index}`);
    const id = requireString(source.id, `OMP model ${index}.id`);
    const effective = effectiveById.get(id);
    const api = source.api === undefined ? providerApi : requireString(source.api, `${id}.api`);
    if (!SUPPORTED_APIS.has(api)) throw new Error(`unsupported API family for ${id}: ${api}`);
    const reasoning = source.reasoning === undefined ? Boolean(effective.reasoning) : source.reasoning;
    if (typeof reasoning !== "boolean") throw new Error(`${id}.reasoning must be boolean`);
    const cost = requireRecord(effective.cost, `${id}.cost`);
    return {
      id,
      name: requireString(source.name ?? effective.name ?? id, `${id}.name`),
      api,
      reasoning,
      input: normalizeInput(source.input ?? effective.input, `${id}.input`),
      contextWindow: requirePositiveInteger(source.contextWindow ?? effective.contextWindow, `${id}.contextWindow`),
      maxTokens: requirePositiveInteger(source.maxTokens ?? effective.maxTokens, `${id}.maxTokens`),
      thinkingLevelMap: convertThinking(source, effective, id),
      cost: {
        input: Number(cost.input ?? 0),
        output: Number(cost.output ?? 0),
        cacheRead: Number(cost.cacheRead ?? 0),
        cacheWrite: Number(cost.cacheWrite ?? 0),
      },
    };
  });

  for (const required of REQUIRED_DEFAULTS) {
    if (!convertedModels.some((model) => model.id === required)) throw new Error(`required Ready Ticket default is absent: ${PROVIDER}/${required}`);
  }

  const current = currentPiConfig === undefined ? { providers: {} } : requireRecord(currentPiConfig, "Pi models config");
  const currentProviders = current.providers === undefined ? {} : requireRecord(current.providers, "Pi providers");
  const currentProvider = currentProviders[PROVIDER] === undefined ? {} : requireRecord(currentProviders[PROVIDER], `Pi provider ${PROVIDER}`);
  const preservedProvider = { ...currentProvider };
  delete preservedProvider.baseUrl;
  delete preservedProvider.api;
  delete preservedProvider.models;
  delete preservedProvider.modelOverrides;

  return {
    ...current,
    providers: {
      ...currentProviders,
      [PROVIDER]: {
        ...preservedProvider,
        baseUrl: requireString(sourceProvider.baseUrl, `OMP ${PROVIDER}.baseUrl`),
        api: providerApi,
        models: convertedModels,
      },
    },
  };
}

function modelMap(config) {
  const models = config?.providers?.[PROVIDER]?.models;
  if (!Array.isArray(models)) return new Map();
  return new Map(models.map((model) => [model.id, model]));
}

function catalogDrift(current, desired) {
  const currentModels = modelMap(current);
  const desiredModels = modelMap(desired);
  const missing = [...desiredModels.keys()].filter((id) => !currentModels.has(id));
  const extra = [...currentModels.keys()].filter((id) => !desiredModels.has(id));
  const changed = [...desiredModels.keys()].filter(
    (id) => currentModels.has(id) && JSON.stringify(currentModels.get(id)) !== JSON.stringify(desiredModels.get(id)),
  );
  const providerChanged =
    current?.providers?.[PROVIDER]?.baseUrl !== desired.providers[PROVIDER].baseUrl ||
    current?.providers?.[PROVIDER]?.api !== desired.providers[PROVIDER].api;
  return { missing, extra, changed, providerChanged, drift: missing.length > 0 || extra.length > 0 || changed.length > 0 || providerChanged };
}

function parseEffectiveCatalog(stdout) {
  const parsed = JSON.parse(stdout);
  if (!parsed || !Array.isArray(parsed.models)) throw new Error("OMP effective model output is invalid");
  return parsed.models;
}

function parseModelList(stdout) {
  const lines = stdout.split("\n").map((line) => line.trim()).filter(Boolean).slice(1);
  return new Set(lines.map((line) => line.split(/\s+/)[1]).filter(Boolean));
}

async function validateStagedConfig(stageDir, piExecutable, desired) {
  const listed = await execute(piExecutable, ["--list-models", PROVIDER], {
    env: { ...process.env, PI_CODING_AGENT_DIR: stageDir },
  });
  const available = parseModelList(listed.stdout);
  for (const id of modelMap(desired).keys()) {
    if (!available.has(id)) throw new Error(`staged Pi catalog did not expose ${PROVIDER}/${id}`);
  }
}

function assistantSmokeResult(stdout, expectedApi, expectedModel) {
  let observed;
  for (const line of stdout.split("\n")) {
    if (!line.trim()) continue;
    const event = JSON.parse(line);
    if (event.type !== "message_end" || event.message?.role !== "assistant") continue;
    const text = Array.isArray(event.message.content)
      ? event.message.content.filter((part) => part.type === "text").map((part) => part.text).join("\n")
      : "";
    observed = { text, api: event.message.api, model: event.message.model };
  }
  if (!observed || observed.text.trim() !== SMOKE_TEXT || observed.api !== expectedApi || observed.model !== expectedModel) {
    throw new Error(`inference smoke failed for ${PROVIDER}/${expectedModel} using ${expectedApi}`);
  }
}

function smokeRepresentatives(desired) {
  const byApi = new Map();
  for (const model of modelMap(desired).values()) {
    if (!byApi.has(model.api)) byApi.set(model.api, model);
  }
  const sol = modelMap(desired).get("gpt-5.6-sol");
  if (sol) byApi.set(sol.api, sol);
  const gemini = modelMap(desired).get("google-antigravity/gemini-3.7-flash");
  if (gemini) byApi.set(gemini.api, gemini);
  return [...byApi.values()];
}

async function smokeApiFamilies(stageDir, piExecutable, desired) {
  for (const model of smokeRepresentatives(desired)) {
    const supportedThinking = THINKING_LEVELS.find((level) => model.thinkingLevelMap[level] !== null);
    const args = [
      "--mode", "json",
      "--print",
      "--no-session",
      "--no-context-files",
      "--no-skills",
      "--no-prompt-templates",
      "--no-extensions",
      "--no-tools",
      "--model", `${PROVIDER}/${model.id}`,
    ];
    if (model.reasoning && supportedThinking) args.push("--thinking", supportedThinking);
    args.push(`Reply with exactly ${SMOKE_TEXT} and nothing else.`);
    const result = await execute(piExecutable, args, {
      cwd: stageDir,
      env: { ...process.env, PI_CODING_AGENT_DIR: stageDir },
      timeout: 120_000,
    });
    assistantSmokeResult(result.stdout, model.api, model.id);
  }
}

async function writePrivate(path, payload) {
  const handle = await open(path, "wx", 0o600);
  try {
    await handle.writeFile(payload, "utf8");
    await handle.sync();
  } finally {
    await handle.close();
  }
}

async function atomicReplace(target, payload) {
  const parent = dirname(target);
  await stat(parent);
  const temporary = join(parent, `.${basename(target)}.${process.pid}.${randomUUID()}.tmp`);
  try {
    await writePrivate(temporary, payload);
    await rename(temporary, target);
    const directory = await open(parent, "r");
    try {
      await directory.sync();
    } finally {
      await directory.close();
    }
  } finally {
    await rm(temporary, { force: true });
  }
}

function outputDrift(drift, currentCount, desiredCount) {
  console.log(drift.drift ? "DRIFT" : "SYNCED");
  console.log(`Provider: ${PROVIDER}`);
  console.log(`OMP models: ${desiredCount}`);
  console.log(`Pi models: ${currentCount}`);
  console.log(`Missing in Pi: ${drift.missing.join(", ") || "None"}`);
  console.log(`Extra in Pi: ${drift.extra.join(", ") || "None"}`);
  console.log(`Changed in Pi: ${drift.changed.join(", ") || "None"}`);
  console.log(`Provider route drift: ${drift.providerChanged ? "yes" : "no"}`);
}

function parseMode(argv) {
  if (argv.length !== 1 || (argv[0] !== "--check" && argv[0] !== "--apply")) {
    throw new Error("usage: sync-iis-pi-models.mjs --check | --apply");
  }
  return argv[0].slice(2).toUpperCase();
}

async function main() {
  const mode = parseMode(process.argv.slice(2));
  const ompModelsPath = resolve(process.env.IIS_OMP_MODELS_PATH || join(homedir(), ".omp/agent/models.yml"));
  const piAgentDir = resolve(process.env.IIS_PI_AGENT_DIR || join(homedir(), ".pi/agent/iis-ready-ticket"));
  const piModelsPath = join(piAgentDir, "models.json");
  const ompExecutable = await resolveExecutable(process.env.OMP_BIN || "omp");
  const piExecutable = await resolveExecutable(process.env.IIS_PI_BIN || "pi");
  const yamlRuntime = process.env.IIS_PI_YAML_RUNTIME
    ? await resolveExecutable(process.env.IIS_PI_YAML_RUNTIME)
    : piExecutable;
  const parseYaml = await loadYamlParser(yamlRuntime);

  const ompStart = await snapshot(ompModelsPath, true);
  const piStart = await snapshot(piModelsPath, false);
  const ompConfig = parseYaml(ompStart.content.toString("utf8"));
  const currentPiConfig = piStart.exists ? JSON.parse(piStart.content.toString("utf8")) : undefined;
  const effectiveResult = await execute(ompExecutable, ["models", PROVIDER, "--json"], { timeout: 60_000 });
  const desired = convertCatalog(ompConfig, parseEffectiveCatalog(effectiveResult.stdout), currentPiConfig);
  const drift = catalogDrift(currentPiConfig, desired);
  outputDrift(drift, modelMap(currentPiConfig).size, modelMap(desired).size);

  if (mode === "CHECK") return drift.drift ? 1 : 0;

  const stageDir = await import("node:fs/promises").then(({ mkdtemp }) => mkdtemp(join(tmpdir(), "iis-pi-model-sync-")));
  try {
    const payload = `${JSON.stringify(desired, null, 2)}\n`;
    await writePrivate(join(stageDir, "models.json"), payload);
    await validateStagedConfig(stageDir, piExecutable, desired);
    await smokeApiFamilies(stageDir, piExecutable, desired);

    const ompFinal = await snapshot(ompModelsPath, true);
    const piFinal = await snapshot(piModelsPath, false);
    if (!sameSnapshot(ompStart, ompFinal) || !sameSnapshot(piStart, piFinal)) {
      throw new Error("STALE INPUT: OMP or Pi model configuration changed during validation");
    }

    await atomicReplace(piModelsPath, payload);
    const applied = JSON.parse((await readFile(piModelsPath)).toString("utf8"));
    if (catalogDrift(applied, desired).drift) throw new Error("applied Pi catalog does not match the validated payload");
    if ((await stat(piModelsPath)).mode & 0o077) throw new Error("applied Pi model config is not private");
    console.log(`APPLIED: ${piModelsPath}`);
    console.log(`API families smoked: ${[...new Set([...modelMap(desired).values()].map((model) => model.api))].join(", ")}`);
    return 0;
  } finally {
    await rm(stageDir, { recursive: true, force: true });
  }
}

try {
  process.exitCode = await main();
} catch (error) {
  console.error(`ERROR: ${safeError(error)}`);
  process.exitCode = 2;
}
