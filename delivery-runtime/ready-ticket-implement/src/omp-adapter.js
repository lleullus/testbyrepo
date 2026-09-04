import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

import { bindAuthority, checkAuthorityCurrentness, isInsideProject } from "./authority-binding.js";
import {
  MAX_OBSERVATION_OUTPUT_BYTES,
  prepareObservation,
  recordObservationResult,
} from "./observation-ledger.js";
import { parseSimpleReadOnlyCommand, runArgv, validateExecutionRequest, validateInspectRequest, validateMutationRequest } from "./argv-policy.js";
import { inventoryAllowedForPhase, isBroadInventory } from "./inventory-policy.js";
import { ReadyLifecycle } from "./lifecycle.js";
import { classifyError } from "./retry-policy.js";
import { buildProbeBinding, validateProbeHandoff } from "./probe-handoff.js";
import { ManagedServiceRegistry } from "./service-supervisor.js";
import { RuntimeStore, stableDigest } from "./state-store.js";
import { buildExactToolMap, mappedPolicy } from "./tool-map.js";
import { captureVerificationTarget, checkVerificationTarget } from "./verification-target.js";

const INTERNAL_TOOLS = new Set(["ready_guard", "ready_argv", "ready_probe_binding", "ready_service"]);

function sessionId(ctx) {
  const id = ctx?.sessionManager?.getSessionId?.();
  if (!id) throw new Error("Ready runtime requires an explicit OMP session id");
  return id;
}

function resultText(value, details = undefined) {
  return {
    content: [{ type: "text", text: typeof value === "string" ? value : JSON.stringify(value, null, 2) }],
    details,
  };
}

function runtimeView(state) {
  if (!state) return null;
  return {
    execution_id: state.execution_id,
    execution_mode: state.execution_mode,
    purpose: state.purpose ?? "implement",
    phase: state.phase,
    project_root: state.project_root,
    ticket_path: state.ticket_path,
    mutation_revision: state.mutation_revision,
    latest_evidence_revision: state.latest_evidence_revision,
    checkpoint_state: state.checkpoint_state,
    authority_drift: state.authority_drift,
    verification_target: state.verification_target ? {
      digest: state.verification_target.digest,
      target_paths: state.verification_target.target_paths,
      allowed_output_paths: state.verification_target.allowed_output_paths,
    } : null,
    target_drift: state.target_drift ?? null,
    mutation_uncertainty: state.uncertainty
      ? { tool_call_id: state.uncertainty.tool_call_id, detail: state.uncertainty.detail, resolution: state.uncertainty.resolution ?? null }
      : null,
    managed_service: state.managed_service ? { pid: state.managed_service.pid, argv: state.managed_service.argv } : null,
  };
}

function readySkillPurpose(event) {
  if (event?.toolName !== "read") return null;
  const raw = String(event?.input?.path ?? "");
  if (/^skill:\/\/ready-ticket-implement(?=[:/]|$)/.test(raw)) return "implement";
  if (/^skill:\/\/ready-ticket-verify(?=[:/]|$)/.test(raw)) return "verify";
  const normalized = raw.replace(/\\/g, "/").replace(/:[0-9]+(?:-[0-9]+)?$/, "");
  if (normalized.endsWith("/ready-ticket-implement/SKILL.md")) return "implement";
  if (normalized.endsWith("/ready-ticket-verify/SKILL.md")) return "verify";
  return null;
}

function nearestExistingCanonical(absolutePath) {
  let cursor = absolutePath;
  const suffix = [];
  while (!fs.existsSync(cursor)) {
    const parent = path.dirname(cursor);
    if (parent === cursor) return absolutePath;
    suffix.unshift(path.basename(cursor));
    cursor = parent;
  }
  const base = fs.realpathSync(cursor);
  return path.join(base, ...suffix);
}

function resolveToolPath(rawPath, cwd) {
  if (typeof rawPath !== "string" || rawPath.length === 0) return null;
  if (/^[a-z][a-z0-9+.-]*:\/\//i.test(rawPath)) return rawPath;
  const absolute = path.isAbsolute(rawPath) ? path.resolve(rawPath) : path.resolve(cwd, rawPath);
  return nearestExistingCanonical(absolute);
}

function pathFromEvent(event, cwd) {
  const raw = event?.input?.path;
  return resolveToolPath(raw, cwd);
}

function protectedMutationReason(state, target) {
  if (!target || /^[a-z][a-z0-9+.-]*:\/\//i.test(target)) return null;
  const protectedArtifact = (state.protected_artifacts || []).find(item => item.path === target);
  return protectedArtifact
    ? `Ready runtime blocks mutation of protected ${protectedArtifact.kind} authority: ${target}`
    : null;
}

function projectConfinementReason(state, target) {
  if (!target) return null;
  if (/^[a-z][a-z0-9+.-]*:\/\//i.test(target)) return `Ready runtime blocks non-project URI access during implementation: ${target}`;
  return isInsideProject(state.project_root, target) ? null : `Ready runtime blocks access outside Project Root: ${target}`;
}

function argvConfinementReason(state, argv) {
  for (const value of argv.slice(1)) {
    if (value.startsWith("-")) continue;
    const looksPathLike = path.isAbsolute(value) || value === ".." || value.startsWith(`..${path.sep}`) || value.startsWith("../") || value.startsWith("./");
    if (!looksPathLike) continue;
    const target = nearestExistingCanonical(path.isAbsolute(value) ? path.resolve(value) : path.resolve(state.project_root, value));
    if (!isInsideProject(state.project_root, target)) return `Ready runtime blocks argv access outside Project Root: ${value}`;
  }
  return null;
}

function hashFileMaybe(file) {
  try {
    return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
  } catch {
    return null;
  }
}

function exactFileObservationToken(toolName, target) {
  if (String(toolName).toLowerCase() !== "read" || !target || /^[a-z][a-z0-9+.-]*:\/\//i.test(target)) return null;
  try {
    if (!fs.statSync(target).isFile()) return null;
    const digest = hashFileMaybe(target);
    return digest ? `file-content:${digest}` : null;
  } catch (error) {
    return error?.code === "ENOENT" ? "file-missing" : null;
  }
}

function mutationSnapshot(event, cwd) {
  const target = pathFromEvent(event, cwd);
  if (!target || /^[a-z][a-z0-9+.-]*:\/\//i.test(target)) return null;
  const beforeHash = hashFileMaybe(target);
  let expectedHash = null;
  if (event.toolName === "write" && typeof event?.input?.content === "string") {
    expectedHash = crypto.createHash("sha256").update(event.input.content).digest("hex");
  }
  return {
    target_path: target,
    before_hash: beforeHash,
    expected_hash: expectedHash,
    tool_name: event.toolName,
  };
}

function resolveSnapshotOutcome(snapshot) {
  if (!snapshot?.target_path) return "inconclusive";
  const currentHash = hashFileMaybe(snapshot.target_path);
  if (snapshot.expected_hash && currentHash === snapshot.expected_hash) return "applied";
  if (currentHash === snapshot.before_hash) return "not_applied";
  return "inconclusive";
}

function contentBytes(content) {
  return Buffer.byteLength(
    (content || [])
      .filter(item => item?.type === "text")
      .map(item => String(item.text ?? ""))
      .join("\n"),
    "utf8",
  );
}

function mutationDigestFor(state, toolName, input) {
  return stableDigest({
    mutation_revision: Number(state.mutation_revision ?? 0),
    tool_name: String(toolName).toLowerCase(),
    input,
  });
}

function repeatedMutationReason(state, mutationDigest) {
  const failed = state.last_failed_mutation;
  if (!failed) return null;
  if (
    Number(failed.mutation_revision) === Number(state.mutation_revision ?? 0)
    && failed.mutation_digest === mutationDigest
  ) {
    return "Ready runtime blocks an unchanged repeat of the same deterministic mutation failure; fix the cause or choose a different bounded action.";
  }
  return null;
}

function ticketReadyToDoneText(text) {
  const matches = [...text.matchAll(/^Status: ([^\r\n]+)$/gm)];
  if (matches.length !== 1 || matches[0][1] !== "ready") throw new Error("exact Ticket is no longer the same single Status: ready contract");
  const match = matches[0];
  return text.slice(0, match.index) + "Status: done" + text.slice(match.index + match[0].length);
}

async function progressReadyTicketToDone(state, signal) {
  if (hashFileMaybe(state.ticket_path) !== state.ticket_sha256) throw new Error("Ticket changed before guarded ready -> done progression");
  const before = fs.readFileSync(state.ticket_path, "utf8");
  const after = ticketReadyToDoneText(before);
  try {
    fs.writeFileSync(state.ticket_path, after, "utf8");
  } catch (error) {
    return { progression: "FAILED", status_after: "ready", detail: String(error?.message ?? error) };
  }
  let validation;
  try {
    validation = await runArgv(["python3", state.validator_path, state.ticket_path], { cwd: state.project_root, signal });
  } catch (error) {
    return { progression: "FAILED", status_after: "done", detail: String(error?.message ?? error) };
  }
  const valid = validation.exitCode === 0 && !validation.timedOut && validation.stdout.trim() === "VALID";
  return {
    progression: valid ? "COMPLETED" : "FAILED",
    status_after: "done",
    detail: valid ? null : (validation.stderr || validation.stdout || `validator exit ${validation.exitCode}`).trim(),
  };
}

function maybeRewritePath(event, target) {
  if (!target || /^[a-z][a-z0-9+.-]*:\/\//i.test(target)) return undefined;
  if (!["read", "write", "grep", "glob"].includes(event.toolName)) return undefined;
  if (typeof event?.input?.path !== "string" || event.input.path === target) return undefined;
  return { ...event.input, path: target };
}

function targetMatchesDrift(state, event, cwd) {
  if (event.toolName !== "read") return false;
  const target = pathFromEvent(event, cwd);
  return Boolean(target && state.authority_drift?.changed?.some(item => item.path === target));
}

async function authorityGate(lifecycle, state, event, cwd) {
  const currentness = await lifecycle.checkAuthorityCurrentness(state);
  if (currentness.current) return { allowed: true, state };
  if (!["AUTHORITY_REVIEW_REQUIRED", "MATERIAL_TURN_REQUIRED"].includes(state.phase)) {
    state = lifecycle.markAuthorityDrift(state.execution_id, currentness.changed);
  }
  if (targetMatchesDrift(state, event, cwd)) return { allowed: true, state, reviewRead: true };
  return {
    allowed: false,
    state,
    reason: state.execution_mode === "SUBAGENT"
      ? "Ready authority changed. Re-read the changed authority and issue MATERIAL_TURN before further guarded work."
      : "Ready authority changed. Re-read the changed authority and call begin_direct again to rebind before further guarded work.",
  };
}

function verificationTargetGate(lifecycle, executionId) {
  const state = lifecycle.status(executionId);
  if (state.purpose !== "verify" || !state.verification_target) return { current: true, changed: [] };
  if (state.phase === "TARGET_DRIFT") return { current: false, changed: state.target_drift?.changed ?? [] };
  const currentness = checkVerificationTarget(state.verification_target);
  if (!currentness.current) lifecycle.markTargetDrift(executionId, currentness.changed);
  return currentness;
}

function requireWorkerExecution(lifecycle, sid) {
  const session = lifecycle.sessionState(sid);
  if (!session?.execution_id) throw new Error("current session has no bound Ready execution");
  if (session.role !== "worker") throw new Error("current session is the SUBAGENT parent and may not perform implementation work");
  const state = lifecycle.status(session.execution_id);
  if (state.session_id !== sid) throw new Error("current session does not own the bound Ready execution");
  return state;
}

function validateExplicitTargets(state, targets) {
  if (!Array.isArray(targets) || targets.length === 0) throw new Error("ready_argv mutate requires explicit target_paths");
  const resolved = targets.map(raw => resolveToolPath(raw, state.project_root));
  for (const target of resolved) {
    const confinement = projectConfinementReason(state, target);
    if (confinement) throw new Error(confinement);
    const protectedReason = protectedMutationReason(state, target);
    if (protectedReason) throw new Error(protectedReason);
  }
  return resolved;
}

export function installReadyRuntime(pi, options = {}) {
  const store = options.store ?? new RuntimeStore(options.dataRoot);
  const lifecycle = options.lifecycle ?? new ReadyLifecycle({
    store,
    bindAuthority: options.bindAuthority ?? bindAuthority,
    checkAuthorityCurrentness: options.checkAuthorityCurrentness ?? checkAuthorityCurrentness,
  });
  const services = options.services ?? new ManagedServiceRegistry({ lifecycle });
  const readySkillDir = options.readySkillDir;
  const operationIndex = new Map();
  let toolMap = { mapped: {}, boundaries: [], customMutationBoundary: [] };
  let toolMapInitialized = false;

  const refreshToolMap = () => {
    toolMap = buildExactToolMap(pi);
    toolMapInitialized = true;
    return toolMap;
  };

  pi.on("resources_discover", async () => {
    refreshToolMap();
    return readySkillDir ? { skillPaths: [readySkillDir] } : {};
  });
  const refreshSessionRuntime = ctx => {
    refreshToolMap();
    lifecycle.recoverInterruptedOperation(sessionId(ctx));
  };
  pi.on("session_start", async (_event, ctx) => {
    refreshSessionRuntime(ctx);
  });
  pi.on("session_switch", async (_event, ctx) => {
    refreshSessionRuntime(ctx);
  });
  pi.on("session_branch", async (_event, ctx) => {
    refreshSessionRuntime(ctx);
  });

  pi.on("tool_call", async (event, ctx) => {
    if (!toolMapInitialized) refreshToolMap();
    const sid = sessionId(ctx);
    const skillPurpose = readySkillPurpose(event);
    if (skillPurpose) {
      lifecycle.armSession(sid, skillPurpose);
      return;
    }
    if (INTERNAL_TOOLS.has(event.toolName)) return;

    const session = lifecycle.sessionState(sid);
    if (!session?.armed) return;
    const policy = mappedPolicy(toolMap, event.toolName);

    let effectivePolicy = policy;
    let normalizedObservationInput = event.input;
    if (policy === "dynamic") {
      const argv = parseSimpleReadOnlyCommand(event?.input?.command);
      if (!argv) {
        return {
          block: true,
          reason: "Ready runtime does not guess Bash mutation semantics. Use ready_argv inspect for read-only argv or ready_argv mutate with explicit target_paths.",
        };
      }
      effectivePolicy = "observation";
      normalizedObservationInput = { argv };
    }

    if (!session.execution_id) {
      if (effectivePolicy === "mutation") {
        const beginAction = session.purpose === "verify" ? "begin_verify" : "begin_direct";
        return { block: true, reason: `Ready ${session.purpose ?? "implement"} is ARMED but ready_guard begin has not bound the exact Ticket yet; use ${beginAction}.` };
      }
      return;
    }

    const state = lifecycle.status(session.execution_id);
    if (state.purpose === "verify") {
      if (!state.verification_target) return { block: true, reason: "Ready verification target is not bound; call ready_guard begin_verify with target_paths before product/runtime work." };
      const targetCurrentness = checkVerificationTarget(state.verification_target);
      if (!targetCurrentness.current) {
        lifecycle.markTargetDrift(state.execution_id, targetCurrentness.changed);
        return { block: true, reason: `Ready verification target drifted: ${targetCurrentness.changed.join(", ")}` };
      }
      if (!policy) {
        operationIndex.set(event.toolCallId, { executionId: state.execution_id, kind: "verification_external", sessionId: sid });
        return;
      }
    } else if (!policy) {
      return;
    }
    if (session.role === "parent") {
      if (effectivePolicy === "mutation") return { block: true, reason: "SUBAGENT parent session may not mutate implementation source." };
      return;
    }
    if (state.session_id !== sid) return { block: true, reason: "Ready execution/session binding mismatch." };

    if (state.phase === "MUTATION_UNCERTAIN") {
      const snapshot = state.uncertainty?.operation?.mutation_snapshot;
      const target = pathFromEvent(event, ctx.cwd);
      if (event.toolName === "read" && snapshot?.target_path === target) {
        operationIndex.set(event.toolCallId, { executionId: state.execution_id, kind: "uncertainty_readback", sessionId: sid });
        return maybeRewritePath(event, target) ? { input: maybeRewritePath(event, target) } : undefined;
      }
      return { block: true, reason: "Ready mutation outcome is uncertain; only exact target readback or terminal BLOCKED is allowed." };
    }

    const authority = await authorityGate(lifecycle, state, event, ctx.cwd);
    if (!authority.allowed) return { block: true, reason: authority.reason };
    if (authority.reviewRead) {
      const target = pathFromEvent(event, ctx.cwd);
      const rewritten = maybeRewritePath(event, target);
      return rewritten ? { input: rewritten } : undefined;
    }

    const current = lifecycle.status(state.execution_id);
    if (current.purpose === "verify" && effectivePolicy === "mutation") {
      return { block: true, reason: "Ready verification keeps Project Root source/config/tests/planning authority immutable; generic mutation tools are blocked." };
    }
    if (effectivePolicy === "mutation" && current.phase !== "ACTIVE") {
      return { block: true, reason: `Ready runtime blocks source mutation in phase ${current.phase}.` };
    }
    if (current.active_operation) {
      return { block: true, reason: `Ready execution already has active guarded operation ${current.active_operation.tool_call_id}.` };
    }

    const target = pathFromEvent(event, ctx.cwd);
    if (target) {
      const confinement = projectConfinementReason(current, target);
      if (confinement) return { block: true, reason: confinement };
      if (effectivePolicy === "mutation") {
        const protectedReason = protectedMutationReason(current, target);
        if (protectedReason) return { block: true, reason: protectedReason };
      }
    }
    if (policy === "dynamic") {
      const argvReason = argvConfinementReason(current, normalizedObservationInput.argv);
      if (argvReason) return { block: true, reason: argvReason };
    }

    if (effectivePolicy === "observation") {
      const broad = isBroadInventory(event.toolName === "bash" ? "bash" : event.toolName, normalizedObservationInput);
      const inventory = inventoryAllowedForPhase(current, broad);
      if (!inventory.allowed) return { block: true, reason: inventory.reason };
      const currentnessIdentity = exactFileObservationToken(event.toolName, target);
      const prepared = prepareObservation(current, event.toolName, normalizedObservationInput, broad, currentnessIdentity);
      if (!prepared.allowed) return { block: true, reason: prepared.reason };
      store.writeExecution(current);
      lifecycle.beginOperation(current.execution_id, {
        toolCallId: event.toolCallId,
        kind: "observation",
        observationDigest: prepared.digest,
      });
      operationIndex.set(event.toolCallId, {
        executionId: current.execution_id,
        kind: "observation",
        observationDigest: prepared.digest,
        sessionId: sid,
      });
    } else {
      const mutationDigest = mutationDigestFor(current, event.toolName, event.input);
      const repeatedReason = repeatedMutationReason(current, mutationDigest);
      if (repeatedReason) return { block: true, reason: repeatedReason };
      const snapshot = mutationSnapshot(event, ctx.cwd);
      lifecycle.beginOperation(current.execution_id, {
        toolCallId: event.toolCallId,
        kind: "mutation",
        mutationSnapshot: snapshot,
        mutationDigest,
      });
      operationIndex.set(event.toolCallId, {
        executionId: current.execution_id,
        kind: "mutation",
        mutationDigest,
        sessionId: sid,
      });
    }

    const rewritten = maybeRewritePath(event, target);
    return rewritten ? { input: rewritten } : undefined;
  });

  pi.on("tool_result", async (event, ctx) => {
    const tracked = operationIndex.get(event.toolCallId);
    if (!tracked) return;
    if (tracked.sessionId && tracked.sessionId !== sessionId(ctx)) return;
    operationIndex.delete(event.toolCallId);

    if (tracked.kind === "uncertainty_readback") {
      const state = lifecycle.status(tracked.executionId);
      const snapshot = state.uncertainty?.operation?.mutation_snapshot;
      const outcome = event.isError ? "inconclusive" : resolveSnapshotOutcome(snapshot);
      lifecycle.resolveMutationUncertainty(tracked.executionId, outcome);
      return;
    }

    if (tracked.kind === "verification_external") {
      verificationTargetGate(lifecycle, tracked.executionId);
      return;
    }

    if (tracked.kind === "observation") {
      const state = lifecycle.status(tracked.executionId);
      const bytes = contentBytes(event.content);
      const classification = event.isError ? classifyError(event.content) : null;
      recordObservationResult(state, tracked.observationDigest, {
        success: !event.isError,
        outputBytes: bytes,
        errorClassification: classification,
        incomplete: bytes > MAX_OBSERVATION_OUTPUT_BYTES,
      });
      store.writeExecution(state);
      lifecycle.finishOperation(tracked.executionId, event.toolCallId, { mutationApplied: false });
      verificationTargetGate(lifecycle, tracked.executionId);
      return;
    }

    const state = lifecycle.status(tracked.executionId);
    if (!event.isError) {
      lifecycle.finishOperation(tracked.executionId, event.toolCallId, { mutationApplied: true });
      return;
    }
    const classification = classifyError(event.content);
    if (classification === "TRANSPORT_NETWORK") {
      const uncertain = lifecycle.markMutationUncertain(tracked.executionId, event.toolCallId, "mutation-capable tool returned transport/network failure");
      const snapshot = uncertain.uncertainty?.operation?.mutation_snapshot;
      const outcome = resolveSnapshotOutcome(snapshot);
      if (outcome !== "inconclusive") lifecycle.resolveMutationUncertainty(tracked.executionId, outcome);
      return;
    }
    lifecycle.finishOperation(tracked.executionId, event.toolCallId, {
      mutationApplied: false,
      failureClassification: classification,
      failureDetail: JSON.stringify(event.content),
    });
  });

  pi.on("session_shutdown", async (_event, ctx) => {
    const sid = sessionId(ctx);
    await services.cleanupSession(sid);
    const session = lifecycle.sessionState(sid);
    if (session?.assignment_id && !session.execution_id) {
      const assignment = store.readAssignment(session.assignment_id);
      if (assignment?.status === "issued" && assignment.parent_session_id === sid) {
        lifecycle.blockAssignment(assignment.assignment_id, sid, "parent session shutdown before delegated execution began");
      }
      return;
    }
    if (!session?.execution_id) return;
    const state = store.readExecution(session.execution_id);
    if (!state?.active_operation || state.session_id !== sid) return;
    if (state.active_operation.kind === "mutation") {
      lifecycle.markMutationUncertain(
        state.execution_id,
        state.active_operation.tool_call_id,
        "session shutdown interrupted an active mutation",
      );
    } else {
      const digest = state.active_operation.observation_digest;
      if (digest) {
        recordObservationResult(state, digest, {
          success: false,
          outputBytes: 0,
          incomplete: true,
        });
        store.writeExecution(state);
      }
      lifecycle.finishOperation(state.execution_id, state.active_operation.tool_call_id, { mutationApplied: false });
    }
  });

  const z = pi.zod;
  pi.registerTool({
    name: "ready_probe_binding",
    label: "Ready Probe Binding",
    description: "Create one machine-checkable current heuristic-probe handoff outside Project Root. This does not issue verifier verdicts.",
    parameters: z.object({
      ticket_path: z.string(),
      project_root: z.string(),
      output_path: z.string(),
      target_paths: z.array(z.string()).optional(),
      allowed_output_paths: z.array(z.string()).optional(),
      lanes: z.array(z.string()).optional(),
    }),
    async execute(_toolCallId, params) {
      const root = fs.realpathSync(params.project_root);
      const output = path.resolve(params.output_path);
      if (isInsideProject(root, output)) throw new Error("Probe machine binding must be written outside Project Root");
      if (fs.existsSync(output)) throw new Error(`Probe machine binding output already exists: ${output}`);
      const laneTerminals = (params.lanes ?? []).map(raw => {
        const separator = raw.lastIndexOf("=");
        if (separator <= 0) throw new Error(`Probe lane must be NAME=FINDING|NO_FINDING|EVIDENCE_LIMIT: ${raw}`);
        const lane = raw.slice(0, separator).trim();
        const status = raw.slice(separator + 1).trim();
        if (!lane || !new Set(["FINDING", "NO_FINDING", "EVIDENCE_LIMIT"]).has(status)) {
          throw new Error(`invalid Probe lane terminal: ${raw}`);
        }
        return { lane, status };
      });
      const binding = await buildProbeBinding({
        projectRoot: root,
        ticketPath: params.ticket_path,
        targetPaths: params.target_paths ?? [],
        allowedOutputPaths: params.allowed_output_paths ?? [],
        admittedLanes: laneTerminals.map(item => item.lane),
        laneTerminals,
        bindAuthorityFn: request => lifecycle.bindAuthority(request),
        captureTargetFn: captureVerificationTarget,
      });
      fs.mkdirSync(path.dirname(output), { recursive: true });
      const temporary = `${output}.${crypto.randomUUID()}.tmp`;
      try {
        fs.writeFileSync(temporary, JSON.stringify(binding, null, 2) + "\n", { flag: "wx" });
        fs.renameSync(temporary, output);
      } finally {
        if (fs.existsSync(temporary)) fs.rmSync(temporary, { force: true });
      }
      return resultText({
        probe_binding_path: output,
        schema: binding.schema,
        binding_digest: stableDigest(binding),
        admitted_lanes: binding.admitted_lanes,
      });
    },
  });

  pi.registerTool({
    name: "ready_guard",
    label: "Ready Guard",
    description: "Bind and advance the internal ready-ticket-implement runtime without changing its external delivery contract.",
    parameters: z.object({
      action: z.enum([
        "begin_direct", "begin_verify", "assign_subagent", "begin_delegated", "checkpoint_pre_action", "checkpoint_material_turn",
        "release_checkpoint", "complete", "finalize_verification", "block", "status",
      ]),
      ticket_path: z.string().optional(),
      project_root: z.string().optional(),
      assignment_id: z.string().optional(),
      execution_id: z.string().optional(),
      probe_binding_path: z.string().optional(),
      target_paths: z.array(z.string()).optional(),
      allowed_output_paths: z.array(z.string()).optional(),
      verdict: z.enum(["VERIFIED", "FAILED", "INCONCLUSIVE"]).optional(),
      decision: z.enum(["CONTINUE", "STEER", "STOP"]).optional(),
      summary: z.string().optional(),
      reason: z.string().optional(),
    }),
    async execute(_toolCallId, params, _signal, _onUpdate, ctx) {
      const sid = sessionId(ctx);
      let value;
      switch (params.action) {
        case "begin_direct":
          value = await lifecycle.beginDirect({ sessionId: sid, projectRoot: params.project_root, ticketPath: params.ticket_path, purpose: "implement" });
          return resultText(runtimeView(value));
        case "begin_verify": {
          const preflight = await lifecycle.bindAuthority({
            projectRoot: params.project_root,
            ticketPath: params.ticket_path,
            allowedStatuses: ["ready", "done"],
          });
          if (preflight.ticket_status_at_start === "ready") {
            if (!params.probe_binding_path) throw new Error("Ready verification requires one current canonical Probe machine binding before begin_verify");
            await validateProbeHandoff({
              probeBindingPath: params.probe_binding_path,
              projectRoot: preflight.project_root,
              ticketPath: preflight.ticket_path,
              targetPaths: params.target_paths ?? [],
              allowedOutputPaths: params.allowed_output_paths ?? [],
              bindAuthorityFn: request => lifecycle.bindAuthority(request),
              captureTargetFn: captureVerificationTarget,
            });
          }
          value = await lifecycle.beginDirect({ sessionId: sid, projectRoot: params.project_root, ticketPath: params.ticket_path, purpose: "verify" });
          const targetBinding = captureVerificationTarget({
            projectRoot: value.project_root,
            targetPaths: params.target_paths ?? [],
            allowedOutputPaths: params.allowed_output_paths ?? [],
          });
          value = lifecycle.bindVerificationTarget(value.execution_id, sid, targetBinding);
          return resultText(runtimeView(value));
        }
        case "assign_subagent":
          value = await lifecycle.assignSubagent({ parentSessionId: sid, projectRoot: params.project_root, ticketPath: params.ticket_path });
          return resultText({
            assignment_id: value.assignment_id,
            ticket_path: value.ticket_path,
            project_root: value.project_root,
            status: value.status,
          });
        case "begin_delegated": {
          const assignment = store.readAssignment(params.assignment_id);
          if (!assignment) throw new Error(`unknown assignment: ${params.assignment_id}`);
          if ((assignment.purpose ?? "implement") === "verify") {
            const preflight = await lifecycle.bindAuthority({
              projectRoot: assignment.project_root,
              ticketPath: assignment.ticket_path,
              allowedStatuses: ["ready", "done"],
            });
            if (preflight.ticket_status_at_start === "ready") {
              if (!params.probe_binding_path) throw new Error("Ready delegated verification requires one current canonical Probe machine binding before begin_delegated");
              await validateProbeHandoff({
                probeBindingPath: params.probe_binding_path,
                projectRoot: preflight.project_root,
                ticketPath: preflight.ticket_path,
                targetPaths: params.target_paths ?? [],
                allowedOutputPaths: params.allowed_output_paths ?? [],
                bindAuthorityFn: request => lifecycle.bindAuthority(request),
                captureTargetFn: captureVerificationTarget,
              });
            }
          }
          value = await lifecycle.beginDelegated({ childSessionId: sid, assignmentId: params.assignment_id });
          if (value.purpose === "verify") {
            const targetBinding = captureVerificationTarget({
              projectRoot: value.project_root,
              targetPaths: params.target_paths ?? [],
              allowedOutputPaths: params.allowed_output_paths ?? [],
            });
            value = lifecycle.bindVerificationTarget(value.execution_id, sid, targetBinding);
          }
          return resultText(runtimeView(value));
        }
        case "checkpoint_pre_action":
          value = lifecycle.checkpointPreAction(params.execution_id, sid, params.summary ?? null);
          return resultText(runtimeView(value));
        case "checkpoint_material_turn": {
          const before = lifecycle.status(params.execution_id);
          if (before.phase === "MATERIAL_TURN_REQUIRED") await lifecycle.refreshDelegatedAuthority(params.execution_id, sid);
          value = lifecycle.checkpointMaterialTurn(params.execution_id, sid, params.summary ?? null);
          return resultText(runtimeView(value));
        }
        case "release_checkpoint":
          value = lifecycle.releaseCheckpoint(params.execution_id, sid, params.decision);
          return resultText(runtimeView(value));
        case "complete": {
          const execution = lifecycle.status(params.execution_id);
          if (execution.purpose === "verify") throw new Error("Ready verification must close through finalize_verification, not complete");
          if (execution.managed_service) await services.stop(execution.execution_id, sid);
          value = await lifecycle.complete(params.execution_id, sid);
          return resultText(runtimeView(value));
        }
        case "finalize_verification": {
          const execution = lifecycle.status(params.execution_id);
          if (execution.purpose !== "verify") throw new Error("finalize_verification requires a verify execution");
          if (!params.verdict) throw new Error("finalize_verification requires verdict");
          let progression = {
            progression: "NOT APPLICABLE",
            status_after: execution.ticket_status_at_start,
            detail: null,
          };
          if (params.verdict === "VERIFIED") {
            const targetCurrentness = verificationTargetGate(lifecycle, execution.execution_id);
            if (!targetCurrentness.current) throw new Error(`VERIFIED blocked by target drift: ${targetCurrentness.changed.join(", ")}`);
            const authority = await lifecycle.checkAuthorityCurrentness(lifecycle.status(execution.execution_id));
            if (!authority.current) {
              lifecycle.markAuthorityDrift(execution.execution_id, authority.changed);
              throw new Error("VERIFIED blocked by authority drift");
            }
            if (execution.ticket_status_at_start === "ready") {
              progression = await progressReadyTicketToDone(lifecycle.status(execution.execution_id), _signal);
            }
          }
          value = lifecycle.finalizeVerification(execution.execution_id, sid, {
            verdict: params.verdict,
            progression: progression.progression,
          });
          return resultText({
            execution: runtimeView(value),
            verification_verdict: params.verdict,
            ticket_progression: progression.progression,
            ticket_status_after: progression.status_after,
            progression_detail: progression.detail,
          });
        }
        case "block": {
          if (!params.execution_id && params.assignment_id) {
            value = lifecycle.blockAssignment(params.assignment_id, sid, params.reason ?? "Ready implementation assignment blocked");
            return resultText({ assignment_id: value.assignment_id, status: value.status, block_reason: value.block_reason });
          }
          const execution = lifecycle.status(params.execution_id);
          if (execution.managed_service) await services.stop(execution.execution_id, sid);
          value = lifecycle.block(params.execution_id, sid, params.reason ?? "Ready implementation blocked");
          return resultText(runtimeView(value));
        }
        case "status": {
          const session = lifecycle.sessionState(sid);
          const executionId = params.execution_id ?? session?.execution_id;
          return resultText({
            session: session ? { armed: session.armed, purpose: session.purpose ?? null, role: session.role, execution_id: session.execution_id, assignment_id: session.assignment_id } : null,
            execution: executionId ? runtimeView(lifecycle.status(executionId)) : null,
            tool_map: { mapped: toolMap.mapped, boundaries: toolMap.boundaries, custom_mutation_boundary: toolMap.customMutationBoundary },
          });
        }
        default:
          throw new Error(`unsupported ready_guard action: ${params.action}`);
      }
    },
  });

  pi.registerTool({
    name: "ready_argv",
    label: "Ready Argv",
    description: "Run explicit structured argv for Ready inspection, verification execution, or implementation mutation. Shell strings are not accepted.",
    parameters: z.object({
      action: z.enum(["inspect", "execute", "mutate"]),
      version: z.literal(1),
      commands: z.array(z.array(z.string())).optional(),
      argv: z.array(z.string()).optional(),
      target_paths: z.array(z.string()).optional(),
    }),
    async execute(_toolCallId, params, signal, _onUpdate, ctx) {
      const sid = sessionId(ctx);
      let state = requireWorkerExecution(lifecycle, sid);
      const authority = await lifecycle.checkAuthorityCurrentness(state);
      if (!authority.current) {
        lifecycle.markAuthorityDrift(state.execution_id, authority.changed);
        throw new Error("Ready authority changed; re-confirm authority before ready_argv execution");
      }

      if (params.action === "inspect") {
        const request = validateInspectRequest({ version: params.version, commands: params.commands });
        const outputs = [];
        for (const argv of request.commands) {
          state = lifecycle.status(state.execution_id);
          if (["COMPLETE", "BLOCKED", "MUTATION_UNCERTAIN"].includes(state.phase)) throw new Error(`ready_argv inspect is unavailable in phase ${state.phase}`);
          const confinement = argvConfinementReason(state, argv);
          if (confinement) throw new Error(confinement);
          const broad = isBroadInventory("bash", { argv });
          const inventory = inventoryAllowedForPhase(state, broad);
          if (!inventory.allowed) throw new Error(inventory.reason);
          const prepared = prepareObservation(state, "ready_argv.inspect", { argv }, broad);
          if (!prepared.allowed) throw new Error(prepared.reason);
          store.writeExecution(state);
          const syntheticId = `ready-argv-${crypto.randomUUID()}`;
          lifecycle.beginOperation(state.execution_id, { toolCallId: syntheticId, kind: "observation", observationDigest: prepared.digest });
          let result;
          try {
            result = await runArgv(argv, { cwd: state.project_root, signal });
          } catch (error) {
            const current = lifecycle.status(state.execution_id);
            recordObservationResult(current, prepared.digest, {
              success: false,
              outputBytes: 0,
              errorClassification: classifyError(error?.message ?? error),
            });
            store.writeExecution(current);
            lifecycle.finishOperation(state.execution_id, syntheticId, { mutationApplied: false });
            throw error;
          }
          const combined = `${result.stdout}${result.stderr}`;
          const bytes = Buffer.byteLength(combined, "utf8");
          const success = result.exitCode === 0 && !result.timedOut;
          const current = lifecycle.status(state.execution_id);
          recordObservationResult(current, prepared.digest, {
            success,
            outputBytes: bytes,
            errorClassification: success ? null : classifyError(result.timedOut ? "timeout" : result.stderr || `exit ${result.exitCode}`),
            incomplete: bytes > MAX_OBSERVATION_OUTPUT_BYTES,
          });
          store.writeExecution(current);
          lifecycle.finishOperation(state.execution_id, syntheticId, { mutationApplied: false });
          outputs.push({
            argv,
            exit_code: result.exitCode,
            timed_out: result.timedOut,
            stdout: result.stdout.slice(0, MAX_OBSERVATION_OUTPUT_BYTES),
            stderr: result.stderr.slice(0, MAX_OBSERVATION_OUTPUT_BYTES),
          });
        }
        return resultText({ action: "inspect", results: outputs });
      }

      if (params.action === "execute") {
        state = lifecycle.status(state.execution_id);
        if (state.purpose !== "verify") throw new Error("ready_argv execute is reserved for Ready verification");
        if (state.phase !== "ACTIVE") throw new Error(`ready_argv execute requires ACTIVE verification; found ${state.phase}`);
        const beforeTarget = verificationTargetGate(lifecycle, state.execution_id);
        if (!beforeTarget.current) throw new Error(`ready_argv execute blocked by target drift: ${beforeTarget.changed.join(", ")}`);
        const request = validateExecutionRequest({ version: params.version, argv: params.argv });
        const confinement = argvConfinementReason(state, request.argv);
        if (confinement) throw new Error(confinement);
        const prepared = prepareObservation(state, "ready_argv.execute", { argv: request.argv }, false);
        if (!prepared.allowed) throw new Error(prepared.reason);
        store.writeExecution(state);
        const syntheticId = `ready-argv-${crypto.randomUUID()}`;
        lifecycle.beginOperation(state.execution_id, { toolCallId: syntheticId, kind: "observation", observationDigest: prepared.digest });
        let result;
        try {
          result = await runArgv(request.argv, { cwd: state.project_root, signal });
        } catch (error) {
          const current = lifecycle.status(state.execution_id);
          recordObservationResult(current, prepared.digest, {
            success: false,
            outputBytes: 0,
            errorClassification: classifyError(error?.message ?? error),
          });
          store.writeExecution(current);
          lifecycle.finishOperation(state.execution_id, syntheticId, { mutationApplied: false });
          verificationTargetGate(lifecycle, state.execution_id);
          throw error;
        }
        const combined = `${result.stdout}${result.stderr}`;
        const bytes = Buffer.byteLength(combined, "utf8");
        const success = result.exitCode === 0 && !result.timedOut;
        const current = lifecycle.status(state.execution_id);
        recordObservationResult(current, prepared.digest, {
          success,
          outputBytes: bytes,
          errorClassification: success ? null : classifyError(result.timedOut ? "timeout" : result.stderr || `exit ${result.exitCode}`),
          incomplete: bytes > MAX_OBSERVATION_OUTPUT_BYTES,
        });
        store.writeExecution(current);
        lifecycle.finishOperation(state.execution_id, syntheticId, { mutationApplied: false });
        const afterTarget = verificationTargetGate(lifecycle, state.execution_id);
        return resultText({
          action: "execute",
          argv: request.argv,
          exit_code: result.exitCode,
          timed_out: result.timedOut,
          stdout: result.stdout.slice(0, MAX_OBSERVATION_OUTPUT_BYTES),
          stderr: result.stderr.slice(0, MAX_OBSERVATION_OUTPUT_BYTES),
          target_current: afterTarget.current,
          target_drift: afterTarget.changed,
          execution: runtimeView(lifecycle.status(state.execution_id)),
        });
      }

      if (state.purpose === "verify") throw new Error("ready_argv mutate is unavailable during Ready verification");
      if (state.phase !== "ACTIVE") throw new Error(`ready_argv mutate requires ACTIVE execution; found ${state.phase}`);
      const request = validateMutationRequest({ version: params.version, argv: params.argv });
      const targetPaths = validateExplicitTargets(state, params.target_paths);
      const confinement = argvConfinementReason(state, request.argv);
      if (confinement) throw new Error(confinement);
      const mutationDigest = mutationDigestFor(state, "ready_argv.mutate", {
        argv: request.argv,
        target_paths: targetPaths,
      });
      const repeatedReason = repeatedMutationReason(state, mutationDigest);
      if (repeatedReason) throw new Error(repeatedReason);
      const syntheticId = `ready-argv-${crypto.randomUUID()}`;
      lifecycle.beginOperation(state.execution_id, {
        toolCallId: syntheticId,
        kind: "mutation",
        mutationDigest,
      });
      let result;
      try {
        result = await runArgv(request.argv, { cwd: state.project_root, signal });
      } catch (error) {
        const classification = classifyError(error?.message ?? error);
        if (classification === "TRANSPORT_NETWORK") {
          lifecycle.markMutationUncertain(
            state.execution_id,
            syntheticId,
            "structured mutation argv ended with transport/network uncertainty; automatic replay is forbidden",
          );
        } else {
          lifecycle.finishOperation(state.execution_id, syntheticId, {
            mutationApplied: false,
            failureClassification: classification,
            failureDetail: String(error?.message ?? error),
          });
        }
        throw error;
      }
      if (result.timedOut) {
        lifecycle.markMutationUncertain(state.execution_id, syntheticId, "structured mutation argv timed out; automatic replay is forbidden");
      } else if (result.exitCode === 0) {
        lifecycle.finishOperation(state.execution_id, syntheticId, { mutationApplied: true });
      } else {
        const classification = classifyError(result.stderr || `exit ${result.exitCode}`);
        if (classification === "TRANSPORT_NETWORK") {
          lifecycle.markMutationUncertain(
            state.execution_id,
            syntheticId,
            "structured mutation argv returned a transport/network failure; automatic replay is forbidden",
          );
        } else {
          lifecycle.finishOperation(state.execution_id, syntheticId, {
            mutationApplied: false,
            failureClassification: classification,
            failureDetail: result.stderr || `exit ${result.exitCode}`,
          });
        }
      }
      return resultText({
        action: "mutate",
        argv: request.argv,
        exit_code: result.exitCode,
        timed_out: result.timedOut,
        stdout: result.stdout.slice(0, MAX_OBSERVATION_OUTPUT_BYTES),
        stderr: result.stderr.slice(0, MAX_OBSERVATION_OUTPUT_BYTES),
        execution: runtimeView(lifecycle.status(state.execution_id)),
      });
    },
  });

  pi.registerTool({
    name: "ready_service",
    label: "Ready Service",
    description: "Start, stop, or inspect one execution-owned local service required for implementation self-checks.",
    parameters: z.object({
      action: z.enum(["start", "stop", "status"]),
      execution_id: z.string(),
      version: z.literal(1).optional(),
      argv: z.array(z.string()).optional(),
    }),
    async execute(_toolCallId, params, _signal, _onUpdate, ctx) {
      const sid = sessionId(ctx);
      if (params.action === "start") return resultText(services.start(params.execution_id, sid, { version: params.version, argv: params.argv }));
      if (params.action === "stop") return resultText(await services.stop(params.execution_id, sid));
      return resultText(services.status(params.execution_id));
    },
  });

  return { store, lifecycle, services, getToolMap: () => toolMap };
}
