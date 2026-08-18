import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import {
  reminderTextFromHookOutput,
  textFromAgentMessage,
  toClaudeCompatibleCalls,
} from "./adapter.mjs";

const EXTENSION_DIR = path.dirname(fileURLToPath(import.meta.url));
const PLUGIN_ROOT = path.resolve(EXTENSION_DIR, "..");
const SKILL_ROOT = path.join(PLUGIN_ROOT, "skills", "lumin-repo-lens");
const ENGINE_LIB = path.join(SKILL_ROOT, "_engine", "lib");

type UnknownRecord = Record<string, unknown>;

interface PendingMutation {
  auditRoot: string;
  calls: Array<{
    tool_name: string;
    tool_use_id: string;
    tool_input: { file_path: string };
  }>;
  sid: string;
}

function engineModule(name: string): string {
  return pathToFileURL(path.join(ENGINE_LIB, name)).href;
}

function candidateSessionValue(ctx: unknown): string | undefined {
  const manager = (ctx as { sessionManager?: UnknownRecord })?.sessionManager;
  const candidates: unknown[] = [
    process.env.OMP_SESSION_ID,
    process.env.PI_SESSION_ID,
    manager?.sessionId,
    manager?.sessionFile,
  ];

  for (const method of ["getSessionId", "getSessionFile"] as const) {
    const fn = manager?.[method];
    if (typeof fn !== "function") continue;
    try {
      candidates.push(fn.call(manager));
    } catch {
      // A read-only session facade may omit or reject optional accessors.
    }
  }

  return candidates.find((value): value is string =>
    typeof value === "string" && value.length > 0
  );
}

function formatError(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export default function luminRepoLensOmp(pi: ExtensionAPI) {
  pi.setLabel("Lumin Repo Lens");

  const fallbackSid = `omp_${process.pid}_${Date.now().toString(36)}`;
  let sid = fallbackSid;
  const pending = new Map<string, PendingMutation>();
  let lightModulesPromise: Promise<{
    drainDueEventReminders: (...args: any[]) => any;
    observeStopAcknowledgements: (...args: any[]) => any;
    resolveAuditRoot: (cwd?: string) => string | null;
    safeRepoPathForToolInput: (...args: any[]) => any;
    safeSessionId: (payload?: UnknownRecord) => string;
    safeToolUseId: (payload?: UnknownRecord) => string;
  }> | null = null;
  let writeModulesPromise: Promise<{
    capturePreimage: (...args: any[]) => any;
    cleanupPreimage: (...args: any[]) => any;
    processPostWriteLite: (...args: any[]) => any;
  }> | null = null;

  function warn(scope: string, error: unknown) {
    pi.logger.warn(`[lumin-repo-lens] ${scope}`, {
      error: formatError(error),
    });
  }

  async function loadLightModules() {
    if (!lightModulesPromise) {
      lightModulesPromise = Promise.all([
        import(engineModule("hook-event-drain.mjs")),
        import(engineModule("hook-ack-observer.mjs")),
        import(engineModule("hook-path-safety.mjs")),
        import(engineModule("hook-id-safety.mjs")),
      ]).then(([drain, ack, pathSafety, idSafety]) => ({
        drainDueEventReminders: drain.drainDueEventReminders,
        observeStopAcknowledgements: ack.observeStopAcknowledgements,
        resolveAuditRoot: pathSafety.resolveAuditRoot,
        safeRepoPathForToolInput: pathSafety.safeRepoPathForToolInput,
        safeSessionId: idSafety.safeSessionId,
        safeToolUseId: idSafety.safeToolUseId,
      }));
    }
    return lightModulesPromise;
  }

  async function loadWriteModules() {
    if (!writeModulesPromise) {
      writeModulesPromise = (async () => {
        const dependencyGuard = await import(engineModule("dependency-guard.mjs"));
        await dependencyGuard.assertRuntimeSetup({
          startDir: SKILL_ROOT,
          commandName: "lumin-repo-lens-omp",
        });
        const [preimage, postWrite] = await Promise.all([
          import(engineModule("hook-preimage-store.mjs")),
          import(engineModule("hook-post-write-lite.mjs")),
        ]);
        return {
          capturePreimage: preimage.capturePreimage,
          cleanupPreimage: preimage.cleanupPreimage,
          processPostWriteLite: postWrite.processPostWriteLite,
        };
      })();
    }
    return writeModulesPromise;
  }

  async function refreshSessionId(ctx: unknown) {
    try {
      const { safeSessionId } = await loadLightModules();
      const candidate = candidateSessionValue(ctx);
      sid = candidate
        ? safeSessionId({ transcript_path: candidate })
        : safeSessionId({ session_id: fallbackSid });
    } catch (error) {
      sid = fallbackSid;
      warn("could not derive session id", error);
    }
  }

  async function clearPending() {
    if (pending.size === 0) return;
    try {
      const { cleanupPreimage } = await loadWriteModules();
      for (const item of pending.values()) {
        for (const call of item.calls) {
          cleanupPreimage(item.auditRoot, item.sid, call.tool_use_id);
        }
      }
    } catch (error) {
      warn("could not clean pending preimages", error);
    } finally {
      pending.clear();
    }
  }

  pi.on("session_start", async (_event, ctx) => {
    await refreshSessionId(ctx);
  });

  pi.on("session_switch", async (_event, ctx) => {
    await clearPending();
    await refreshSessionId(ctx);
  });

  pi.on("session_branch", async (_event, ctx) => {
    await clearPending();
    await refreshSessionId(ctx);
  });

  pi.on("before_agent_start", async (event, ctx) => {
    try {
      const { drainDueEventReminders, resolveAuditRoot } = await loadLightModules();
      const auditRoot = resolveAuditRoot(ctx.cwd);
      if (!auditRoot) return;

      const drain = drainDueEventReminders(auditRoot, sid, {
        hookEventName: "before_agent_start",
      });
      const reminder = reminderTextFromHookOutput(drain.output);
      if (!reminder) return;

      return {
        systemPrompt: [
          ...event.systemPrompt,
          `Lumin Repo Lens repository evidence reminder:\n${reminder}`,
        ],
      };
    } catch (error) {
      warn("before_agent_start adapter failed", error);
    }
  });

  // OMP emits this after tool-call input revision and immediately before actual
  // execution, which is the closest native equivalent to Claude PreToolUse.
  pi.on("tool_execution_start", async (event, ctx) => {
    if (event.toolName !== "write" && event.toolName !== "edit") return;

    try {
      const calls = toClaudeCompatibleCalls(
        event.toolCallId,
        event.toolName,
        event.args as UnknownRecord,
      );
      if (calls.length === 0) return;

      const light = await loadLightModules();
      const write = await loadWriteModules();
      const auditRoot = light.resolveAuditRoot(ctx.cwd);
      if (!auditRoot) return;

      const captured = [];
      for (const call of calls) {
        const target = call.tool_input.file_path;
        const safe = light.safeRepoPathForToolInput(ctx.cwd, target);
        if (!safe.ok) continue;
        const tid = light.safeToolUseId(call);
        write.capturePreimage({
          auditRoot,
          sid,
          tid,
          safe,
        });
        captured.push({
          ...call,
          tool_use_id: tid,
        });
      }

      if (captured.length > 0) {
        pending.set(event.toolCallId, {
          auditRoot,
          calls: captured,
          sid,
        });
      }
    } catch (error) {
      warn("pre-write adapter failed", error);
    }
  });

  pi.on("tool_result", async (event, ctx) => {
    if (event.toolName !== "write" && event.toolName !== "edit") return;

    const item = pending.get(event.toolCallId);
    pending.delete(event.toolCallId);
    if (!item) return;

    try {
      const { processPostWriteLite } = await loadWriteModules();
      const result = processPostWriteLite(
        {
          cwd: ctx.cwd,
          session_id: item.sid,
          tool_calls: item.calls,
        },
        {
          auditRoot: item.auditRoot,
          sid: item.sid,
        },
      );
      const reminder = reminderTextFromHookOutput(result.output);
      if (!reminder) return;

      return {
        content: [
          ...event.content,
          {
            type: "text",
            text: `Lumin Repo Lens repository evidence reminder:\n${reminder}`,
          },
        ],
      };
    } catch (error) {
      warn("post-write adapter failed", error);
      try {
        const { cleanupPreimage } = await loadWriteModules();
        for (const call of item.calls) {
          cleanupPreimage(item.auditRoot, item.sid, call.tool_use_id);
        }
      } catch {
        // Advisory cleanup only.
      }
    }
  });

  pi.on("session_stop", async (event, ctx) => {
    try {
      const {
        observeStopAcknowledgements,
        resolveAuditRoot,
      } = await loadLightModules();
      const auditRoot = resolveAuditRoot(ctx.cwd);
      if (!auditRoot) return;

      observeStopAcknowledgements(
        auditRoot,
        sid,
        {
          last_assistant_message: textFromAgentMessage(
            event.last_assistant_message,
          ),
        },
      );
    } catch (error) {
      warn("session_stop adapter failed", error);
    }
  });

  pi.on("session_shutdown", async () => {
    await clearPending();
  });
}
