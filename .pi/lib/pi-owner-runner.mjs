import { spawn } from "node:child_process";
import { mkdtemp, readFile, realpath, rm, stat, writeFile } from "node:fs/promises";
import { homedir, tmpdir } from "node:os";
import { dirname, isAbsolute, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { assertModelBindings } from "./model-binding-preflight.mjs";

const INPUT_LIMIT = 1024 * 1024;
const TASK_LIMIT = 64 * 1024;
const STDERR_LIMIT = 64 * 1024;
const RUN_ID = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
const THINKING = new Set(["off", "minimal", "low", "medium", "high", "xhigh", "max"]);

export function repositoryRoot(sourceUrl) {
  return resolve(dirname(fileURLToPath(sourceUrl)), "../../..");
}

export function requireRecord(value, field = "input") {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${field} must be an object`);
  }
  return value;
}

export function requireString(value, field, maxLength = 16 * 1024) {
  if (typeof value !== "string" || !value.trim()) throw new Error(`${field} must be a non-empty string`);
  if (value.length > maxLength) throw new Error(`${field} exceeds ${maxLength} characters`);
  return value.trim();
}

export function optionalString(value, field, maxLength = 16 * 1024) {
  if (value === undefined || value === null || value === "") return undefined;
  return requireString(value, field, maxLength);
}

export function requireBoolean(value, field, fallback = false) {
  if (value === undefined) return fallback;
  if (typeof value !== "boolean") throw new Error(`${field} must be boolean`);
  return value;
}

export function requireArray(value, field) {
  if (!Array.isArray(value)) throw new Error(`${field} must be an array`);
  return value;
}

export function requireRunId(value) {
  const runId = requireString(value, "runId", 128);
  if (!RUN_ID.test(runId)) throw new Error("runId contains unsupported characters");
  return runId;
}

export function requireModel(value, field) {
  const model = requireString(value, field, 256);
  const separator = model.indexOf("/");
  if (separator <= 0 || separator === model.length - 1) {
    throw new Error(`${field} must be an exact provider/model binding`);
  }
  return model;
}

export function requireThinking(value, field) {
  const thinking = requireString(value, field, 16);
  if (!THINKING.has(thinking)) throw new Error(`${field} is not a supported thinking level`);
  return thinking;
}

export async function canonicalDirectory(value, field) {
  const requested = requireString(value, field, 4096);
  if (!isAbsolute(requested)) throw new Error(`${field} must be absolute`);
  const canonical = await realpath(requested);
  if (!(await stat(canonical)).isDirectory()) throw new Error(`${field} is not a directory`);
  return canonical;
}

export async function canonicalFile(value, field) {
  const requested = requireString(value, field, 4096);
  if (!isAbsolute(requested)) throw new Error(`${field} must be absolute`);
  const canonical = await realpath(requested);
  if (!(await stat(canonical)).isFile()) throw new Error(`${field} is not a file`);
  return canonical;
}

function parseArguments(argv) {
  if (argv.length !== 2 || argv[0] !== "--input") {
    throw new Error("usage: runner --input <invocation.json|->");
  }
  return argv[1];
}

async function readStdin() {
  let content = "";
  for await (const chunk of process.stdin) {
    content += String(chunk);
    if (content.length > INPUT_LIMIT) throw new Error(`stdin input exceeds ${INPUT_LIMIT} characters`);
  }
  return content;
}

async function readInvocation(path) {
  if (path !== "-") {
    const info = await stat(path);
    if (!info.isFile()) throw new Error("invocation input is not a file");
    if (process.platform !== "win32" && (info.mode & 0o077) !== 0) {
      throw new Error("invocation file must not grant group or other permissions");
    }
  }
  const content = path === "-" ? await readStdin() : await readFile(path, "utf8");
  if (content.length > INPUT_LIMIT) throw new Error(`invocation input exceeds ${INPUT_LIMIT} characters`);
  try {
    return JSON.parse(content);
  } catch (error) {
    throw new Error(`invalid invocation JSON: ${error instanceof Error ? error.message : String(error)}`);
  }
}

function parseAgentSource(content, expectedFile) {
  if (!content.startsWith("---\n")) throw new Error(`missing agent frontmatter: ${expectedFile}`);
  const end = content.indexOf("\n---", 4);
  if (end < 0) throw new Error(`missing agent frontmatter terminator: ${expectedFile}`);
  const metadata = {};
  for (const line of content.slice(4, end).split("\n")) {
    const separator = line.indexOf(":");
    if (separator < 0) continue;
    metadata[line.slice(0, separator).trim()] = line.slice(separator + 1).trim();
  }
  return { metadata, body: content.slice(end + 4).replace(/^\n/, "") };
}

function assertAgentContract(agent, config) {
  const actualTools = (agent.metadata.tools || "").split(",").map((item) => item.trim()).filter(Boolean);
  if (agent.metadata.name !== config.agent) throw new Error(`agent source name drift: ${agent.metadata.name || "missing"}`);
  if (agent.metadata.thinking !== config.defaultThinking) throw new Error(`agent thinking drift: ${agent.metadata.thinking || "missing"}`);
  if (agent.metadata.systemPrompt !== "append") throw new Error("agent systemPrompt must remain append");
  if (agent.metadata.maxDepth !== "0") throw new Error("agent maxDepth must remain 0");
  if (actualTools.join(",") !== config.tools.join(",")) throw new Error("agent tool contract drift");
}

function assistantText(message) {
  if (!message || typeof message !== "object" || message.role !== "assistant" || !Array.isArray(message.content)) return undefined;
  const parts = message.content
    .filter((part) => part && typeof part === "object" && part.type === "text" && typeof part.text === "string")
    .map((part) => part.text);
  return parts.length ? parts.join("\n") : undefined;
}

function appendTail(current, chunk) {
  const joined = current + chunk;
  return joined.length <= STDERR_LIMIT ? joined : joined.slice(joined.length - STDERR_LIMIT);
}

function sanitizeTerminalText(value, values) {
  if (typeof value !== "string" || !value) return value;
  let sanitized = value;
  const exactValues = [values.additionalInstructions, values.implementationReport]
    .filter((candidate) => typeof candidate === "string" && candidate.length >= 8 && candidate !== "None");
  for (const candidate of exactValues) sanitized = sanitized.split(candidate).join("[REDACTED]");
  return sanitized
    .replace(/\bBearer\s+[^\s,;]+/gi, "Bearer [REDACTED]")
    .replace(/\b(?:sk|ghp|github_pat|xox[baprs])[-_][A-Za-z0-9_-]{8,}\b/g, "[REDACTED]")
    .replace(
      /(\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret)\b\s*[:=]\s*)(?:"[^"\n]*"|'[^'\n]*'|[^\s,;]+)/gi,
      "$1[REDACTED]",
    );
}

function terminalEnvelope(config, values) {
  return {
    schema: "iis.pi.ready-ticket-run/v1",
    runId: values.runId || "unknown",
    mode: config.mode,
    agent: config.agent,
    session: "none",
    processStatus: values.processStatus,
    workflow: values.workflow || null,
    ticket: values.ticket || null,
    projectRoot: values.projectRoot || null,
    targetIdentity: values.targetIdentity || null,
    ownerModel: values.ownerModel || null,
    ownerThinking: values.ownerThinking || null,
    preflight: values.preflight || null,
    postcondition: values.postcondition || null,
    startedAt: values.startedAt,
    finishedAt: values.finishedAt,
    durationMs: Date.parse(values.finishedAt) - Date.parse(values.startedAt),
    childExitCode: values.childExitCode ?? null,
    output: sanitizeTerminalText(values.output || "", values),
    error: sanitizeTerminalText(values.error || null, values),
    stderr: sanitizeTerminalText(values.stderr || "", values),
  };
}

function emitTerminal(config, values) {
  process.stdout.write(`${JSON.stringify(terminalEnvelope(config, values))}\n`);
}

async function execute(config, invocation, startedAt) {
  const root = repositoryRoot(config.sourceUrl);
  const agentPath = resolve(root, config.agentRelativePath);
  const extensionPath = resolve(root, ".pi/extensions/iis-ready-audit/index.ts");
  const agent = parseAgentSource(await readFile(agentPath, "utf8"), agentPath);
  assertAgentContract(agent, config);

  const configuredModel = process.env[config.modelEnvironment] || config.defaultModel;
  const normalized = await config.normalize(invocation, configuredModel, config.defaultThinking);
  const preflight = config.preflight ? await config.preflight(normalized, root) : { proceed: true };
  if (!preflight.proceed) {
    const finishedAt = new Date().toISOString();
    return {
      normalized,
      terminal: terminalEnvelope(config, {
        ...normalized,
        startedAt,
        finishedAt,
        processStatus: "COMPLETED",
        workflow: preflight.workflow,
        output: preflight.output,
        preflight: {
          validator: preflight.validator,
          validatorResult: preflight.validatorResult,
          status: preflight.status || null,
        },
      }),
      exitCode: 0,
    };
  }
  const postconditionCapture = config.capturePostcondition
    ? await config.capturePostcondition(normalized, preflight)
    : undefined;
  const task = config.buildTask(normalized, preflight);
  if (task.length > TASK_LIMIT) throw new Error(`generated task exceeds ${TASK_LIMIT} characters`);

  const promptDirectory = await mkdtemp(join(tmpdir(), `${config.agent}-`));
  const promptPath = join(promptDirectory, "system-prompt.md");
  await writeFile(promptPath, agent.body, { encoding: "utf8", mode: 0o600 });

  let child;
  let receivedSignal;
  let stderr = "";
  let stdoutBuffer = "";
  let output = "";

  const forwardSignal = (signal) => {
    receivedSignal = signal;
    if (!child?.pid) return;
    try {
      if (process.platform === "win32") child.kill(signal);
      else process.kill(-child.pid, signal);
    } catch {
      child.kill(signal);
    }
  };
  const onSigInt = () => forwardSignal("SIGINT");
  const onSigTerm = () => forwardSignal("SIGTERM");
  process.once("SIGINT", onSigInt);
  process.once("SIGTERM", onSigTerm);

  try {
    const piBinary = process.env.IIS_PI_BIN || "pi";
    const agentDir = process.env.IIS_PI_AGENT_DIR || resolve(homedir(), ".pi/agent/iis-ready-ticket");
    const args = [
      "--mode", "json",
      "--print",
      "--approve",
      "--no-session",
      "--no-context-files",
      "--no-skills",
      "--no-prompt-templates",
      "--no-extensions",
      "--extension", extensionPath,
      "--model", normalized.ownerModel,
      "--thinking", normalized.ownerThinking,
      "--tools", config.tools.join(","),
      "--append-system-prompt", promptPath,
      "--name", `${config.agent}:${normalized.runId}`,
      task,
    ];
    const env = {};
    for (const key of [
      "HOME",
      "PATH",
      "USER",
      "LOGNAME",
      "SHELL",
      "LANG",
      "LC_ALL",
      "LC_CTYPE",
      "TZ",
      "TMPDIR",
      "XDG_CONFIG_HOME",
      "XDG_CACHE_HOME",
      "XDG_DATA_HOME",
    ]) {
      if (process.env[key]) env[key] = process.env[key];
    }
    if (process.env.NODE_ENV === "test") {
      env.NODE_ENV = "test";
      for (const [key, value] of Object.entries(process.env)) {
        if (key.startsWith("PI_STUB_") && value !== undefined) env[key] = value;
      }
    }
    Object.assign(env, {
      PI_CODING_AGENT_DIR: agentDir,
      PI_SUBAGENT_NAME: config.agent,
      PI_SUBAGENT_SESSION: "none",
      PI_SUBAGENT_DEPTH: "1",
      PI_SUBAGENT_MAX_DEPTH: "0",
      PI_SUBAGENT_ALLOWED: "",
    });

    Object.assign(env, config.childEnvironment ? config.childEnvironment(normalized, preflight) : {});
    preflight.modelBindings = await assertModelBindings({
      agentDir,
      piBinary,
      env,
      bindings: [
        { role: `${config.mode.toLowerCase()} owner`, model: normalized.ownerModel, thinking: normalized.ownerThinking },
        ...normalized.auditors.map((auditor, index) => ({
          role: `${config.mode.toLowerCase()} auditor ${index + 1}`,
          model: auditor.model,
          thinking: auditor.thinking,
        })),
      ],
    });
    child = spawn(piBinary, args, {
      cwd: root,
      env,
      detached: process.platform !== "win32",
      stdio: ["ignore", "pipe", "pipe"],
    });

    const processLine = (line) => {
      if (!line.trim()) return;
      let event;
      try {
        event = JSON.parse(line);
      } catch {
        stderr = appendTail(stderr, `[unparsed stdout] ${line}\n`);
        return;
      }
      if (event.type === "tool_execution_start") {
        process.stderr.write(`[${config.agent}] tool ${String(event.toolName || "unknown")}\n`);
      }
      if (event.type === "message_end") {
        const text = assistantText(event.message);
        if (text !== undefined) output = text;
      }
    };

    child.stdout.on("data", (chunk) => {
      stdoutBuffer += String(chunk);
      const lines = stdoutBuffer.split("\n");
      stdoutBuffer = lines.pop() || "";
      for (const line of lines) processLine(line);
    });
    child.stderr.on("data", (chunk) => {
      stderr = appendTail(stderr, String(chunk));
    });

    const childExitCode = await new Promise((resolveExit, reject) => {
      child.once("error", reject);
      child.once("close", (code) => resolveExit(code ?? 1));
    });
    if (stdoutBuffer.trim()) processLine(stdoutBuffer);

    const finishedAt = new Date().toISOString();
    let postcondition;
    if (config.verifyPostcondition) {
      try {
        postcondition = await config.verifyPostcondition(postconditionCapture, normalized, preflight);
      } catch (error) {
        return {
          normalized,
          terminal: terminalEnvelope(config, {
            ...normalized,
            startedAt,
            finishedAt,
            childExitCode,
            processStatus: "FAILED",
            output,
            stderr,
            postcondition: { status: "FAILED", error: error instanceof Error ? error.message : String(error) },
            preflight,
            error: error instanceof Error ? error.message : String(error),
          }),
          exitCode: 1,
        };
      }
    }
    if (receivedSignal) {
      return {
        normalized,
        terminal: terminalEnvelope(config, {
          ...normalized,
          startedAt,
          finishedAt,
          childExitCode,
          processStatus: "CANCELLED",
          output,
          stderr,
          preflight,
          postcondition,
          error: `runner received ${receivedSignal}`,
        }),
        exitCode: receivedSignal === "SIGINT" ? 130 : 143,
      };
    }
    if (childExitCode !== 0) {
      return {
        normalized,
        terminal: terminalEnvelope(config, {
          ...normalized,
          startedAt,
          finishedAt,
          childExitCode,
          processStatus: "FAILED",
          output,
          stderr,
          preflight,
          postcondition,
          error: `Pi exited with code ${childExitCode}`,
        }),
        exitCode: 1,
      };
    }

    let workflow;
    try {
      workflow = config.parseOutput(output);
      if (config.validateWorkflowPostcondition) config.validateWorkflowPostcondition(workflow, postcondition, preflight);
    } catch (error) {
      return {
        normalized,
        terminal: terminalEnvelope(config, {
          ...normalized,
          startedAt,
          finishedAt,
          childExitCode,
          processStatus: "FAILED",
          output,
          stderr,
          preflight,
          postcondition,
          error: error instanceof Error ? error.message : String(error),
        }),
        exitCode: 1,
      };
    }

    return {
      normalized,
      terminal: terminalEnvelope(config, {
        ...normalized,
        startedAt,
        finishedAt,
        childExitCode,
        processStatus: "COMPLETED",
        workflow,
        output,
        stderr,
        preflight,
        postcondition,
      }),
      exitCode: 0,
    };
  } finally {
    process.removeListener("SIGINT", onSigInt);
    process.removeListener("SIGTERM", onSigTerm);
    await rm(promptDirectory, { recursive: true, force: true });
  }
}

export async function runOwner(config) {
  const startedAt = new Date().toISOString();
  let invocation;
  let runId = "unknown";
  try {
    const inputPath = parseArguments(process.argv.slice(2));
    invocation = await readInvocation(inputPath);
    if (invocation && typeof invocation === "object" && typeof invocation.runId === "string") runId = invocation.runId;
    const result = await execute(config, invocation, startedAt);
    process.stdout.write(`${JSON.stringify(result.terminal)}\n`);
    process.exitCode = result.exitCode;
  } catch (error) {
    const finishedAt = new Date().toISOString();
    emitTerminal(config, {
      runId,
      startedAt,
      finishedAt,
      processStatus: "FAILED",
      error: error instanceof Error ? error.message : String(error),
    });
    process.exitCode = 1;
  }
}
