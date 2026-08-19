import { execFile } from "node:child_process";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

const STANDARD_THINKING_LEVELS = new Set(["minimal", "low", "medium", "high"]);

function execute(command, args, options) {
  const { promise, resolve, reject } = Promise.withResolvers();
  const child = execFile(
    command,
    args,
    { encoding: "utf8", maxBuffer: 4 * 1024 * 1024, timeout: 30_000, ...options },
    (error, stdout) => {
      if (error) reject(new Error(`Pi model availability check failed for ${args.at(-1)}`));
      else resolve(stdout);
    },
  );
  child.stdin?.end();
  return promise;
}

function parseBinding(raw, role) {
  if (typeof raw !== "string") throw new Error(`${role} model binding must be a string`);
  const separator = raw.indexOf("/");
  if (separator <= 0 || separator === raw.length - 1) throw new Error(`${role} model binding must be provider/model`);
  return { provider: raw.slice(0, separator), id: raw.slice(separator + 1) };
}

function parseAvailableModels(stdout) {
  const available = new Set();
  for (const line of stdout.split("\n").slice(1)) {
    const [provider, id] = line.trim().split(/\s+/);
    if (provider && id) available.add(`${provider}/${id}`);
  }
  return available;
}

function assertThinking(model, requested, role) {
  if (requested === "off") return;
  if (!model.reasoning) throw new Error(`${role} requests thinking=${requested} from non-reasoning model`);
  const map = model.thinkingLevelMap;
  if (map !== undefined) {
    if (!map || typeof map !== "object" || Array.isArray(map) || !(requested in map) || map[requested] === null) {
      throw new Error(`${role} requests unsupported thinking=${requested}`);
    }
    return;
  }
  if (!STANDARD_THINKING_LEVELS.has(requested)) throw new Error(`${role} requests unsupported thinking=${requested}`);
}

export async function assertModelBindings({ agentDir, piBinary, bindings, env }) {
  if (!Array.isArray(bindings) || bindings.length === 0) throw new Error("at least one exact Pi model binding is required");
  const config = JSON.parse(await readFile(join(agentDir, "models.json"), "utf8"));
  if (!config?.providers || typeof config.providers !== "object" || Array.isArray(config.providers)) {
    throw new Error("Pi models.json providers are invalid");
  }

  const checked = [];
  for (const binding of bindings) {
    const role = binding.role || "runtime";
    const parsed = parseBinding(binding.model, role);
    const provider = config.providers[parsed.provider];
    if (!provider || typeof provider !== "object" || Array.isArray(provider)) {
      throw new Error(`${role} provider is absent from Pi models.json: ${parsed.provider}`);
    }
    const model = Array.isArray(provider.models) ? provider.models.find((candidate) => candidate?.id === parsed.id) : undefined;
    if (!model) throw new Error(`${role} model is absent from Pi models.json: ${binding.model}`);
    const api = model.api ?? provider.api;
    if (typeof api !== "string" || !api) throw new Error(`${role} model has no provider API route: ${binding.model}`);
    assertThinking(model, binding.thinking, role);
    checked.push({ ...binding, ...parsed, api });
  }

  const availableByProvider = new Map();
  for (const provider of new Set(checked.map((binding) => binding.provider))) {
    const stdout = await execute(piBinary, ["--list-models", provider], {
      env: { ...env, PI_CODING_AGENT_DIR: agentDir },
    });
    availableByProvider.set(provider, parseAvailableModels(stdout));
  }
  for (const binding of checked) {
    if (!availableByProvider.get(binding.provider).has(binding.model)) {
      throw new Error(`${binding.role || "runtime"} model/API/auth is unavailable to Pi: ${binding.model}`);
    }
  }

  return checked.map(({ role, model, thinking, api }) => ({ role, model, thinking, api }));
}
