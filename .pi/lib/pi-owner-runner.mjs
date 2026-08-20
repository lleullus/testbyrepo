import { spawn } from "node:child_process";
import { constants as fsConstants } from "node:fs";
import { access, mkdtemp, readFile, realpath, rm, stat, writeFile } from "node:fs/promises";
import { homedir, tmpdir } from "node:os";
import { delimiter, dirname, isAbsolute, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { assertModelBindings } from "./model-binding-preflight.mjs";

const INPUT_LIMIT = 1024 * 1024;
const TASK_LIMIT = 64 * 1024;
const STDERR_LIMIT = 64 * 1024;
const RUN_ID = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
const THINKING = new Set(["off", "minimal", "low", "medium", "high", "xhigh", "max"]);
const PROGRESS_SCHEMA = "iis.pi.progress/v1";
const AUDIT_PROGRESS_PREFIX = "IIS_PI_AUDIT_EVENT ";
const AUDIT_RUN_ID = /^iis-audit-[0-9a-f-]+$/;
const AUDIT_ROLES = new Set(["implementation", "verification"]);
const AUDIT_TERMINAL = new Set(["COMPLETED", "BLOCKED", "FAILED", "CANCELLED"]);
const AUDIT_EVENTS = new Set([
  "AUDITOR_STARTING",
  "AUDITOR_RUNNING",
  "AUDITOR_WAITING_REPLY",
  "AUDITOR_RESUMED",
  "AUDITOR_TERMINAL",
  "FAN_IN_COMPLETE",
]);
const DEFAULT_HEARTBEAT_MS = 60_000;
const TOOL_NAME = /^[A-Za-z0-9_-]{1,128}$/;

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

async function isExecutable(path) {
  try {
    await access(path, process.platform === "win32" ? fsConstants.F_OK : fsConstants.X_OK);
    return true;
  } catch {
    return false;
  }
}

export async function resolvePiBinary(configured = process.env.IIS_PI_BIN) {
  const requested = typeof configured === "string" ? configured.trim() : "";
  if (requested && (isAbsolute(requested) || requested.includes("/") || requested.includes("\\"))) {
    const candidate = isAbsolute(requested) ? requested : resolve(requested);
    if (await isExecutable(candidate)) return candidate;
    throw new Error(`configured IIS_PI_BIN is not executable: ${requested}`);
  }

  const command = requested || "pi";
  const names = process.platform === "win32" && !/\.(?:bat|cmd|exe)$/i.test(command)
    ? [command, `${command}.cmd`, `${command}.exe`, `${command}.bat`]
    : [command];
  const directories = [
    ...(process.env.PATH || "").split(delimiter).filter(Boolean),
    join(homedir(), ".local", "bin"),
    join(homedir(), ".bun", "bin"),
  ];
  for (const directory of new Set(directories)) {
    for (const name of names) {
      const candidate = join(directory, name);
      if (await isExecutable(candidate)) return candidate;
    }
  }
  throw new Error("Pi executable is unavailable; set IIS_PI_BIN or install pi in PATH, ~/.local/bin, or ~/.bun/bin");
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

function progressHeartbeatMs() {
  if (process.env.NODE_ENV !== "test") return DEFAULT_HEARTBEAT_MS;
  const configured = Number(process.env.PI_STUB_PROGRESS_HEARTBEAT_MS);
  return Number.isFinite(configured) && configured >= 10 ? configured : DEFAULT_HEARTBEAT_MS;
}

function progressSummary(mode, event, fields = {}) {
  const modeLabel = mode === "VERIFY" ? "Verify" : "Implement";
  const auditorLabel = mode === "VERIFY" ? "AC auditors" : "Implementation auditors";
  const configuredAuditors = Number.isInteger(fields.configuredAuditors) ? fields.configuredAuditors : 0;
  const terminalAuditors = Number.isInteger(fields.terminalAuditors) ? fields.terminalAuditors : 0;
  const failedAuditors = Number.isInteger(fields.failedAuditors) ? fields.failedAuditors : 0;
  const blockedAuditors = Number.isInteger(fields.blockedAuditors) ? fields.blockedAuditors : 0;
  const cancelledAuditors = Number.isInteger(fields.cancelledAuditors) ? fields.cancelledAuditors : 0;

  switch (event) {
    case "RUN_STARTED":
      return `${mode === "VERIFY" ? "🔎" : "🚀"} ${modeLabel} started`;
    case "PREFLIGHT_PASSED":
      return configuredAuditors > 0
        ? `✓ Preflight passed · ${configuredAuditors} ${mode === "VERIFY" ? "AC auditors" : "auditors"} configured`
        : "✓ Preflight passed · no auditors configured";
    case "PREFLIGHT_FAILED":
      return `! Preflight failed${fields.failureStage ? ` · ${fields.failureStage}` : ""}`;
    case "OWNER_PROCESS_STARTED":
      return "● Owner process started";
    case "OWNER_STATUS":
      if (fields.status === "INSPECTING") {
        return mode === "VERIFY" ? "● Inspecting verification target" : "● Inspecting ticket and repository";
      }
      if (fields.status === "UPDATING") return "● Updating implementation";
      if (fields.status === "RUNNING_COMMAND") return "● Running repository command";
      if (fields.status === "FINALIZING_TICKET") return "● Finalizing Ticket status";
      return "● Owner working";
    case "AUDITOR_STATUS": {
      const suffix = `${terminalAuditors}/${configuredAuditors} terminal`;
      const issues = [
        failedAuditors > 0 ? `${failedAuditors} failed` : null,
        blockedAuditors > 0 ? `${blockedAuditors} blocked` : null,
        cancelledAuditors > 0 ? `${cancelledAuditors} cancelled` : null,
      ].filter(Boolean);
      if (issues.length > 0) return `! ${auditorLabel} · ${issues.join(", ")} · ${suffix}`;
      if (fields.fanInComplete) return `✓ ${auditorLabel} · ${terminalAuditors}/${configuredAuditors} fan-in complete`;
      return `◐ ${auditorLabel} · ${suffix}`;
    }
    case "POSTCONDITION_STARTED":
      return "● Checking final Ticket state";
    case "POSTCONDITION_PASSED":
      return "✓ Final Ticket state passed";
    case "POSTCONDITION_FAILED":
      return "! Final Ticket state failed";
    case "RUN_ALIVE":
      return `● Still running · no new observable activity for ${Math.floor((fields.inactiveMs || 0) / 1000)}s`;
    case "RUN_COMPLETED":
      return "● Pi run finished · reading final result";
    case "RUN_CANCELLED":
      return "! Pi run cancelled";
    case "RUN_FAILED":
      return "! Pi run failed";
    default:
      return `${modeLabel} · ${event}`;
  }
}

function createProgressReporter(runId, startedAt, mode) {
  const startedMs = Date.parse(startedAt);
  const heartbeatMs = progressHeartbeatMs();
  let sequence = 0;
  let lastObservedAt = Date.now();
  let lastHeartbeatAt = 0;
  let stopped = false;

  const emit = (event, fields = {}, observed = true) => {
    if (stopped) return;
    const now = Date.now();
    if (observed) lastObservedAt = now;
    sequence += 1;
    process.stderr.write(`${JSON.stringify({
      summary: progressSummary(mode, event, fields),
      event,
      schema: PROGRESS_SCHEMA,
      runId,
      sequence,
      timestamp: new Date(now).toISOString(),
      elapsedMs: Math.max(0, now - startedMs),
      ...fields,
    })}\n`);
  };

  const timer = setInterval(() => {
    const now = Date.now();
    const inactiveMs = now - lastObservedAt;
    if (inactiveMs < heartbeatMs || now - lastHeartbeatAt < heartbeatMs) return;
    lastHeartbeatAt = now;
    emit("RUN_ALIVE", { inactiveMs }, false);
  }, Math.max(10, Math.min(heartbeatMs, 15_000)));
  timer.unref();

  return {
    emit,
    observe() {
      lastObservedAt = Date.now();
    },
    stop() {
      if (stopped) return;
      stopped = true;
      clearInterval(timer);
    },
  };
}

function safeToolName(value) {
  return typeof value === "string" && TOOL_NAME.test(value) ? value : "unknown";
}

function ownerStatusForTool(mode, value) {
  const toolName = safeToolName(value);
  if (["read", "grep", "find", "ls"].includes(toolName)) return "INSPECTING";
  if (toolName === "bash") return "RUNNING_COMMAND";
  if (mode === "IMPLEMENT" && ["edit", "write"].includes(toolName)) return "UPDATING";
  if (mode === "VERIFY" && toolName === "iis_ticket_mark_done") return "FINALIZING_TICKET";
  if (toolName.startsWith("iis_audit_")) return undefined;
  return "WORKING";
}

function parseAuditProgress(line) {
  if (!line.startsWith(AUDIT_PROGRESS_PREFIX)) return undefined;
  let event;
  try {
    event = JSON.parse(line.slice(AUDIT_PROGRESS_PREFIX.length));
  } catch {
    throw new Error("invalid child audit progress JSON");
  }
  if (!event || typeof event !== "object" || Array.isArray(event) || !AUDIT_EVENTS.has(event.event)) {
    throw new Error("invalid child audit progress event");
  }
  if (event.event === "FAN_IN_COMPLETE") {
    if (!Array.isArray(event.auditRunIds) || event.auditRunIds.some((runId) => !AUDIT_RUN_ID.test(runId))) {
      throw new Error("invalid child audit fan-in identity");
    }
    if (!Number.isInteger(event.terminalAuditors) || event.terminalAuditors !== event.auditRunIds.length) {
      throw new Error("invalid child audit fan-in count");
    }
    return {
      event: event.event,
      fields: { auditRunIds: event.auditRunIds, terminalAuditors: event.terminalAuditors },
    };
  }
  if (!AUDIT_RUN_ID.test(event.auditRunId) || !AUDIT_ROLES.has(event.role)) {
    throw new Error("invalid child auditor identity");
  }
  if (!Number.isInteger(event.handoffSequence) || event.handoffSequence < 0) {
    throw new Error("invalid child auditor handoff sequence");
  }
  const fields = {
    auditRunId: event.auditRunId,
    role: event.role,
    handoffSequence: event.handoffSequence,
  };
  if (event.event === "AUDITOR_TERMINAL") {
    if (!AUDIT_TERMINAL.has(event.terminalStatus)) throw new Error("invalid child auditor terminal status");
    fields.terminalStatus = event.terminalStatus;
  }
  return { event: event.event, fields };
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

async function execute(config, invocation, startedAt, progress) {
  const root = repositoryRoot(config.sourceUrl);
  const agentPath = resolve(root, config.agentRelativePath);
  const extensionPath = resolve(root, ".pi/extensions/iis-ready-audit/index.ts");
  let agent;
  let normalized;
  let preflight;
  let postconditionCapture;
  let task;
  try {
    agent = parseAgentSource(await readFile(agentPath, "utf8"), agentPath);
    assertAgentContract(agent, config);

    const configuredModel = process.env[config.modelEnvironment] || config.defaultModel;
    normalized = await config.normalize(invocation, configuredModel, config.defaultThinking);
    preflight = config.preflight ? await config.preflight(normalized, root) : { proceed: true };
    if (!preflight.proceed) {
      progress.emit("PREFLIGHT_FAILED", {
        failureStage: "ADMISSION",
        configuredAuditors: normalized.auditors.length,
      });
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
    postconditionCapture = config.capturePostcondition
      ? await config.capturePostcondition(normalized, preflight)
      : undefined;
    task = config.buildTask(normalized, preflight);
    if (task.length > TASK_LIMIT) throw new Error(`generated task exceeds ${TASK_LIMIT} characters`);
  } catch (error) {
    progress.emit("PREFLIGHT_FAILED", { failureStage: "ADMISSION" });
    throw error;
  }

  const promptDirectory = await mkdtemp(join(tmpdir(), `${config.agent}-`));
  const promptPath = join(promptDirectory, "system-prompt.md");
  await writeFile(promptPath, agent.body, { encoding: "utf8", mode: 0o600 });

  let child;
  let receivedSignal;
  let stderr = "";
  let stdoutBuffer = "";
  let childStderrBuffer = "";
  let output = "";
  let progressError = false;
  let lastOwnerStatus;
  const startedAuditors = new Set();
  const terminalAuditors = new Set();
  const auditorTerminalStatuses = new Map();

  const auditorAggregate = (fanInComplete = false) => {
    const statuses = [...auditorTerminalStatuses.values()];
    return {
      configuredAuditors: normalized.auditors.length,
      startedAuditors: startedAuditors.size,
      terminalAuditors: terminalAuditors.size,
      completedAuditors: statuses.filter((status) => status === "COMPLETED").length,
      blockedAuditors: statuses.filter((status) => status === "BLOCKED").length,
      failedAuditors: statuses.filter((status) => status === "FAILED").length,
      cancelledAuditors: statuses.filter((status) => status === "CANCELLED").length,
      fanInComplete,
    };
  };

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
    const piBinary = await resolvePiBinary();
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
      IIS_PI_PROGRESS_PROTOCOL: PROGRESS_SCHEMA,
    });

    Object.assign(env, config.childEnvironment ? config.childEnvironment(normalized, preflight) : {});
    try {
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
    } catch (error) {
      progress.emit("PREFLIGHT_FAILED", {
        failureStage: "MODEL_BINDING",
        configuredAuditors: normalized.auditors.length,
      });
      throw error;
    }
    progress.emit("PREFLIGHT_PASSED", {
      configuredAuditors: normalized.auditors.length,
      ownerModel: normalized.ownerModel,
      ownerThinking: normalized.ownerThinking,
    });
    child = spawn(piBinary, args, {
      cwd: root,
      env,
      detached: process.platform !== "win32",
      stdio: ["ignore", "pipe", "pipe"],
    });
    child.once("spawn", () => {
      progress.emit("OWNER_PROCESS_STARTED", {
        ownerModel: normalized.ownerModel,
        ownerThinking: normalized.ownerThinking,
      });
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
      progress.observe();
      if (event.type === "tool_execution_start") {
        const status = ownerStatusForTool(config.mode, event.toolName);
        if (status && status !== lastOwnerStatus) {
          lastOwnerStatus = status;
          progress.emit("OWNER_STATUS", { status });
        }
      }
      if (event.type === "message_end") {
        const text = assistantText(event.message);
        if (text !== undefined) output = text;
      }
    };

    const processChildStderrLine = (line) => {
      if (!line.startsWith(AUDIT_PROGRESS_PREFIX)) {
        stderr = appendTail(stderr, `${line}\n`);
        return;
      }
      try {
        const auditProgress = parseAuditProgress(line);
        if (!auditProgress) return;
        if (auditProgress.fields.auditRunId) startedAuditors.add(auditProgress.fields.auditRunId);
        if (auditProgress.event === "AUDITOR_TERMINAL") {
          const auditRunId = auditProgress.fields.auditRunId;
          const isNewTerminal = !terminalAuditors.has(auditRunId);
          terminalAuditors.add(auditRunId);
          auditorTerminalStatuses.set(auditRunId, auditProgress.fields.terminalStatus);
          if (isNewTerminal) progress.emit("AUDITOR_STATUS", auditorAggregate(false));
        } else if (auditProgress.event === "FAN_IN_COMPLETE") {
          progress.emit("AUDITOR_STATUS", auditorAggregate(true));
        }
      } catch {
        progressError = true;
        stderr = appendTail(stderr, "[invalid child audit progress event]\n");
      }
    };

    child.stdout.on("data", (chunk) => {
      progress.observe();
      stdoutBuffer += String(chunk);
      const lines = stdoutBuffer.split("\n");
      stdoutBuffer = lines.pop() || "";
      for (const line of lines) processLine(line);
    });
    child.stderr.on("data", (chunk) => {
      progress.observe();
      childStderrBuffer += String(chunk);
      const lines = childStderrBuffer.split("\n");
      childStderrBuffer = lines.pop() || "";
      for (const line of lines) processChildStderrLine(line);
    });

    const childExitCode = await new Promise((resolveExit, reject) => {
      child.once("error", reject);
      child.once("close", (code) => resolveExit(code ?? 1));
    });
    if (stdoutBuffer.trim()) processLine(stdoutBuffer);
    if (childStderrBuffer) processChildStderrLine(childStderrBuffer);

    let postcondition;
    if (config.verifyPostcondition) {
      progress.emit("POSTCONDITION_STARTED");
      try {
        postcondition = await config.verifyPostcondition(postconditionCapture, normalized, preflight);
        progress.emit("POSTCONDITION_PASSED");
      } catch (error) {
        progress.emit("POSTCONDITION_FAILED");
        const finishedAt = new Date().toISOString();
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
    const finishedAt = new Date().toISOString();
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
    if (progressError) {
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
          error: "invalid child audit progress event",
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
  let progress;
  try {
    const inputPath = parseArguments(process.argv.slice(2));
    invocation = await readInvocation(inputPath);
    runId = requireRunId(invocation?.runId);
    progress = createProgressReporter(runId, startedAt, config.mode);
    progress.emit("RUN_STARTED", { mode: config.mode, agent: config.agent });
    const result = await execute(config, invocation, startedAt, progress);
    const terminalEvent = result.terminal.processStatus === "COMPLETED"
      ? "RUN_COMPLETED"
      : result.terminal.processStatus === "CANCELLED"
        ? "RUN_CANCELLED"
        : "RUN_FAILED";
    progress.emit(terminalEvent);
    progress.stop();
    process.stdout.write(`${JSON.stringify(result.terminal)}\n`);
    process.exitCode = result.exitCode;
  } catch (error) {
    progress?.emit("RUN_FAILED");
    progress?.stop();
    const finishedAt = new Date().toISOString();
    emitTerminal(config, {
      runId,
      startedAt,
      finishedAt,
      processStatus: "FAILED",
      error: error instanceof Error ? error.message : String(error),
    });
    process.exitCode = 1;
  } finally {
    progress?.stop();
  }
}
