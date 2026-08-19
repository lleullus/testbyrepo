import {
  createAgentSession,
  createSyntheticSourceInfo,
  DefaultResourceLoader,
  defineTool,
  getAgentDir,
  SessionManager,
  type AgentSession,
  type ExtensionAPI,
  type Skill,
} from "@earendil-works/pi-coding-agent";
import type { Model } from "@earendil-works/pi-ai";
import { Type } from "typebox";
import { readFile, realpath, stat } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import {
  AuditRuntime,
  type AuditRole,
  type AuditRunSpec,
  type AuditRuntimeEvent,
  type AuditSession,
} from "./runtime.ts";
import { markTicketDone } from "../../lib/ticket-transition.mjs";

const IIS_SKILLS_ROOT = process.cwd();
const AGENT_PATHS: Record<AuditRole, string> = {
  implementation: resolve(IIS_SKILLS_ROOT, ".pi/agents/iis-implement-auditor.md"),
  verification: resolve(IIS_SKILLS_ROOT, ".pi/agents/iis-verify-auditor.md"),
};
const DEFAULT_ORACLE_SKILL = "/home/user01/.codex/skills/oracle-browser/SKILL.md";
const TERMINAL = new Set(["COMPLETED", "BLOCKED", "FAILED", "CANCELLED"]);
const THINKING_LEVELS = ["off", "minimal", "low", "medium", "high", "xhigh", "max"] as const;

type ThinkingLevel = (typeof THINKING_LEVELS)[number];

interface PiSessionInput {
  model: Model<any>;
  thinking: ThinkingLevel;
  oracleSkill?: Skill;
}

function bodyAfterFrontmatter(content: string, file: string): string {
  if (!content.startsWith("---\n")) throw new Error(`missing frontmatter: ${file}`);
  const end = content.indexOf("\n---", 4);
  if (end < 0) throw new Error(`missing frontmatter terminator: ${file}`);
  return content.slice(end + 4).replace(/^\n/, "");
}

function lastAssistantText(session: AgentSession): string {
  for (let index = session.messages.length - 1; index >= 0; index -= 1) {
    const message = session.messages[index] as {
      role?: string;
      content?: Array<{ type?: string; text?: string }>;
    };
    if (message.role !== "assistant" || !Array.isArray(message.content)) continue;
    const text = message.content
      .filter((part) => part.type === "text" && typeof part.text === "string")
      .map((part) => part.text)
      .join("\n");
    if (text.trim()) return text;
  }
  return "";
}

function parseModelBinding(value: string): { provider: string; modelId: string } {
  const separator = value.indexOf("/");
  if (separator <= 0 || separator === value.length - 1) {
    throw new Error(`model must be an exact provider/model binding: ${value}`);
  }
  return { provider: value.slice(0, separator), modelId: value.slice(separator + 1) };
}

async function canonicalDirectory(path: string): Promise<string> {
  const canonical = await realpath(path);
  const info = await stat(canonical);
  if (!info.isDirectory()) throw new Error(`audit cwd is not a directory: ${canonical}`);
  return canonical;
}

async function oracleSkill(): Promise<Skill> {
  const configured = process.env.IIS_ORACLE_BROWSER_SKILL || DEFAULT_ORACLE_SKILL;
  const canonical = await realpath(configured);
  const info = await stat(canonical);
  if (!info.isFile()) throw new Error(`Oracle Browser skill is not a file: ${canonical}`);
  return {
    name: "oracle-browser",
    description: "Managed Oracle Browser advisory review",
    filePath: canonical,
    baseDir: dirname(canonical),
    sourceInfo: createSyntheticSourceInfo(canonical, {
      source: "local",
      scope: "user",
      baseDir: dirname(canonical),
    }),
    disableModelInvocation: false,
  };
}


async function configuredVerificationFiles(): Promise<{ ticket: string; validator: string }> {
  if (process.env.IIS_READY_TICKET_MODE !== "VERIFY") throw new Error("guarded Ticket progression is Verify-only");
  const requestedTicket = process.env.IIS_READY_TICKET_PATH;
  const requestedValidator = process.env.IIS_CANONICAL_TICKET_VALIDATOR;
  if (!requestedTicket || !requestedValidator) throw new Error("guarded Ticket progression configuration is incomplete");
  const ticket = await realpath(requestedTicket);
  const validator = await realpath(requestedValidator);
  if (!(await stat(ticket)).isFile()) throw new Error("configured Ticket is not a file");
  if (!(await stat(validator)).isFile()) throw new Error("configured validator is not a file");
  return { ticket, validator };
}

function eventMessage(event: AuditRuntimeEvent): string {
  if (event.type === "HANDOFF") {
    return [
      "PI AUDITOR HANDOFF",
      `Run ID: ${event.run.runId}`,
      `Role: ${event.run.role}`,
      `Assignment: ${event.run.assignment}`,
      `Handoff Sequence: ${event.sequence}`,
      `Status: ${event.run.status}`,
      "",
      event.body,
      "",
      "Inspect the cited evidence, then call iis_audit_reply for this exact run ID and sequence.",
    ].join("\n");
  }
  return [
    "PI AUDITOR TERMINAL RESULT",
    `Run ID: ${event.run.runId}`,
    `Role: ${event.run.role}`,
    `Assignment: ${event.run.assignment}`,
    `Status: ${event.run.status}`,
    ...(event.run.error ? [`Error: ${event.run.error}`] : []),
    "",
    event.run.finalOutput || "(no terminal output)",
    "",
    "This terminal event is evidence, not automatic acceptance. Fan in every required run before completion.",
  ].join("\n");
}

export default function iisReadyAuditExtension(pi: ExtensionAPI): void {
  let shuttingDown = false;
  const runtime = new AuditRuntime<PiSessionInput>(
    async (_runId, spec, input, handoff): Promise<AuditSession> => {
      const agentFile = AGENT_PATHS[spec.role];
      const prompt = bodyAfterFrontmatter(await readFile(agentFile, "utf8"), agentFile);
      const handoffTool = defineTool({
        name: "iis_audit_handoff",
        label: "IIS Audit Handoff",
        description: "Send one evidence-bearing handoff to the direct owner and wait for its reply.",
        parameters: Type.Object({
          body: Type.String({ minLength: 1, description: "Concise evidence, inference, uncertainty, and requested owner direction" }),
        }),
        execute: async (_toolCallId, params) => {
          const reply = await handoff(params.body);
          return {
            content: [{ type: "text" as const, text: `OWNER REPLY\n${reply}` }],
            details: { reply },
          };
        },
      });

      const loader = new DefaultResourceLoader({
        cwd: spec.cwd,
        agentDir: getAgentDir(),
        systemPromptOverride: () => prompt,
        ...(input.oracleSkill
          ? {
              skillsOverride: (current) => ({
                skills: current.skills.some((skill) => skill.name === input.oracleSkill?.name)
                  ? current.skills
                  : [...current.skills, input.oracleSkill as Skill],
                diagnostics: current.diagnostics,
              }),
            }
          : {}),
      });
      await loader.reload();

      const enabledTools = ["read", "grep", "find", "ls", "iis_audit_handoff"];
      if (input.oracleSkill) enabledTools.push("bash");
      const { session } = await createAgentSession({
        cwd: spec.cwd,
        model: input.model,
        thinkingLevel: input.thinking,
        tools: enabledTools,
        customTools: [handoffTool],
        resourceLoader: loader,
        sessionManager: SessionManager.inMemory(spec.cwd),
      });

      return {
        prompt: (task) =>
          session.prompt(
            `${task}\n\nOracle Browser: ${input.oracleSkill ? "ALLOWED" : "NOT REQUESTED"}\n` +
              "Use iis_audit_handoff for intermediate collaboration. Return completion only in the terminal assistant result.",
          ),
        abort: () => session.abort(),
        dispose: () => session.dispose(),
        finalText: () => lastAssistantText(session),
      };
    },
    (event) => {
      if (shuttingDown) return;
      pi.sendMessage(
        {
          customType: event.type === "HANDOFF" ? "iis-audit-handoff" : "iis-audit-terminal",
          content: eventMessage(event),
          display: true,
          details: event,
        },
        { deliverAs: "steer", triggerTurn: true },
      );
    },
  );

  if (process.env.IIS_READY_TICKET_MODE === "VERIFY") {
    pi.registerTool({
      name: "iis_ticket_mark_done",
      label: "Guarded IIS Ticket Done Transition",
      description: "Atomically target only the configured Ticket's exact Status: ready line after validator and content-hash checks.",
      parameters: Type.Object({
        expectedSha256: Type.String({ pattern: "^[0-9a-f]{64}$" }),
      }),
      async execute(_toolCallId, params, signal) {
        const { ticket, validator } = await configuredVerificationFiles();
        const details = await markTicketDone({
          ticket,
          validator,
          expectedSha256: params.expectedSha256,
          signal,
        });
        return {
          content: [
            {
              type: "text",
              text: `Ticket progression completed: ${details.beforeSha256} -> ${details.afterSha256}`,
            },
          ],
          details,
        };
      },
    });
  }

  pi.registerTool({
    name: "iis_audit_start",
    label: "Start IIS Auditor",
    description: "Start one fresh isolated IIS auditor in the background and return its unique run ID immediately.",
    parameters: Type.Object({
      role: Type.Union([Type.Literal("implementation"), Type.Literal("verification")]),
      assignment: Type.String({ minLength: 1 }),
      task: Type.String({ minLength: 1 }),
      cwd: Type.String({ minLength: 1, description: "Exact target Project Root" }),
      model: Type.String({ minLength: 3, description: "Exact provider/model binding" }),
      thinking: Type.Union(THINKING_LEVELS.map((level) => Type.Literal(level))),
      oracleBrowser: Type.Optional(Type.Boolean({ default: false })),
    }),
    async execute(_toolCallId, params, signal, _onUpdate, ctx) {
      signal?.throwIfAborted();
      const cwd = await canonicalDirectory(params.cwd);
      const binding = parseModelBinding(params.model);
      const model = ctx.modelRegistry.find(binding.provider, binding.modelId);
      if (!model) throw new Error(`requested model binding is unavailable: ${params.model}`);
      const selectedOracleSkill = params.oracleBrowser ? await oracleSkill() : undefined;
      const spec: AuditRunSpec = {
        role: params.role,
        assignment: params.assignment,
        task: params.task,
        cwd,
        model: params.model,
        thinking: params.thinking,
        oracleBrowser: Boolean(params.oracleBrowser),
      };
      const run = runtime.start(spec, {
        model,
        thinking: params.thinking,
        oracleSkill: selectedOracleSkill,
      });
      return {
        content: [{ type: "text", text: JSON.stringify(run, null, 2) }],
        details: run,
      };
    },
  });

  pi.registerTool({
    name: "iis_audit_reply",
    label: "Reply To IIS Auditor",
    description: "Reply to one exact waiting auditor handoff after checking its cited evidence.",
    parameters: Type.Object({
      runId: Type.String({ minLength: 1 }),
      sequence: Type.Integer({ minimum: 1 }),
      body: Type.String({ minLength: 1 }),
    }),
    async execute(_toolCallId, params) {
      const run = runtime.reply(params.runId, params.sequence, params.body);
      return { content: [{ type: "text", text: JSON.stringify(run, null, 2) }], details: run };
    },
  });

  pi.registerTool({
    name: "iis_audit_cancel",
    label: "Cancel IIS Auditor",
    description: "Cancel and contain one exact nonterminal auditor run.",
    parameters: Type.Object({
      runId: Type.String({ minLength: 1 }),
      reason: Type.String({ minLength: 1 }),
    }),
    async execute(_toolCallId, params) {
      const run = await runtime.cancel(params.runId, params.reason);
      return { content: [{ type: "text", text: JSON.stringify(run, null, 2) }], details: run };
    },
  });

  pi.registerTool({
    name: "iis_audit_fan_in",
    label: "Fan In IIS Auditors",
    description: "Return attributable terminal results only when every exact required auditor run is terminal.",
    parameters: Type.Object({ runIds: Type.Array(Type.String({ minLength: 1 }), { minItems: 1 }) }),
    async execute(_toolCallId, params) {
      const runs = runtime.fanIn(params.runIds);
      const accepted = runs.every((run) => TERMINAL.has(run.status));
      if (!accepted) throw new Error("fan-in contained a nonterminal run");
      return { content: [{ type: "text", text: JSON.stringify(runs, null, 2) }], details: runs };
    },
  });

  pi.on("session_shutdown", async () => {
    shuttingDown = true;
    await runtime.shutdown();
  });
}
