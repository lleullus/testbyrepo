import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { spawnSync } from "node:child_process";

import { bindAuthority, checkAuthorityCurrentness, isInsideProject, resolveCanonicalValidator } from "./authority-binding.js";
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
const FINAL_VALIDATOR_TIMEOUT_MS = 10_000;

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
  if (rawPath.startsWith("~/")) rawPath = path.join(os.homedir(), rawPath.slice(2));
  const absolute = path.isAbsolute(rawPath) ? path.resolve(rawPath) : path.resolve(cwd, rawPath);
  return nearestExistingCanonical(absolute);
}

function pathFromEvent(event, cwd) {
  const raw = event?.input?.path;
  const base = event.toolName === "read" && typeof raw === "string"
    ? raw.replace(/(?::(?:raw|-?\d+(?:[-+]\d*)?(?:,\d+(?:[-+]\d*)?)*))+$/, "") : raw;
  return resolveToolPath(base, cwd);
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

function pathIdentity(target) {
  let stat;
  try { stat = fs.lstatSync(target); } catch (error) {
    if (error.code === "ENOENT") return "missing";
    throw error;
  }
  if (stat.isSymbolicLink()) return `link:${fs.readlinkSync(target)}`;
  if (stat.isFile()) return `file:${stat.mode}:${crypto.createHash("sha256").update(fs.readFileSync(target)).digest("hex")}`;
  if (stat.isDirectory()) return `dir:${stableDigest(fs.readdirSync(target).sort().map(name => [name, pathIdentity(path.join(target, name))]))}`;
  throw new Error(`cannot attribute mutation effects for special file: ${target}`);
}

function snapshotPaths(targets) {
  return { targets: targets.map(target => ({ path: target, before: pathIdentity(target) })) };
}

function mutationTargets(event, cwd) {
  if (event.toolName !== "edit" || typeof event.input?.input !== "string") {
    const target = pathFromEvent(event, cwd);
    if (!target) throw new Error("mutation tool requires attributable target paths");
    return [target];
  }
  const targets = [];
  for (const line of event.input.input.split(/\r?\n/)) {
    if (!line.trim() || line.startsWith("+")) continue;
    const header = /^\[(.+)#[a-fA-F0-9]{4}\]$/.exec(line);
    if (header) targets.push(resolveToolPath(header[1], cwd));
    else if (line.startsWith("MV ")) {
      const destination = line.slice(3).trim();
      targets.push(resolveToolPath(destination.startsWith('"') ? JSON.parse(destination) : destination, cwd));
    } else if (!/^(?:PUT |CUT |REM$)/.test(line)) throw new Error("Ready supports attributable hashline edit input only");
  }
  if (!targets.length || targets.some(target => !target)) throw new Error("edit has no attributable target paths");
  return [...new Set(targets)];
}


function resolveSnapshotOutcome(snapshot) {
  if (!snapshot?.targets?.length) return "inconclusive";
  try {
    let changed = false;
    for (const target of snapshot.targets) if (pathIdentity(target.path) !== target.before) changed = true;
    return changed ? "applied" : "not_applied";
  } catch { return "inconclusive"; }
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

function mutationDigestFor(toolName, input) {
  return stableDigest({
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

function runValidatorSync(state) {
  const validation = spawnSync("python3", [state.validator_path, state.ticket_path], {
    cwd: state.project_root,
    shell: false,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
    timeout: FINAL_VALIDATOR_TIMEOUT_MS,
  });
  const timedOut = validation.error?.code === "ETIMEDOUT";
  if (validation.error && !timedOut) throw validation.error;
  return {
    exitCode: validation.status,
    timedOut,
    stdout: validation.stdout ?? "",
    stderr: validation.stderr ?? "",
  };
}

function progressReadyTicketToDone(state, signal) {
  if (signal?.aborted) throw new Error("verification finalization was aborted before guarded progression");
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
    validation = runValidatorSync(state);
  } catch (error) {
    return { progression: "FAILED", status_after: "done", detail: String(error?.message ?? error) };
  }
  const valid = validation.exitCode === 0 && !validation.timedOut && validation.stdout.trim() === "VALID";
  return {
    progression: valid ? "COMPLETED" : "FAILED",
    status_after: "done",
    detail: valid ? null : (validation.stderr || validation.stdout || (validation.timedOut ? "validator timed out" : `validator exit ${validation.exitCode}`)).trim(),
  };
}

function maybeRewritePath(event, target) {
  if (!target || /^[a-z][a-z0-9+.-]*:\/\//i.test(target)) return undefined;
  if (!["read", "write", "grep", "glob"].includes(event.toolName)) return undefined;
  if (typeof event?.input?.path !== "string" || event.input.path === target) return undefined;
  const selector = event.toolName === "read" ? event.input.path.match(/(?::(?:raw|-?\d+(?:[-+]\d*)?(?:,\d+(?:[-+]\d*)?)*))+$/)?.[0] ?? "" : "";
  return { ...event.input, path: target + selector };
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
  if (state.worker_inactive) throw new Error("Ready worker is suspended");
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

function boundAuthorityRead(state, event, cwd) {
  if (state.purpose !== "verify" || event.toolName !== "read" || typeof event.input?.path !== "string") return null;
  const raw = event.input.path;
  const selector = raw.match(/(?::(?:raw|-?\d+(?:[-+]\d*)?(?:,\d+(?:[-+]\d*)?)*))+$/)?.[0] ?? "";
  const base = selector ? raw.slice(0, -selector.length) : raw;
  const resolved = resolveToolPath(base, cwd);
  for (const artifact of state.protected_artifacts ?? []) {
    const workflow = artifact.kind === "workflow" && /^(?:skill:\/\/iis-workflow)(?:\/SKILL\.md)?$/.test(base);
    const toTickets = artifact.kind === "to_tickets" && /^(?:skill:\/\/to-tickets)(?:\/SKILL\.md)?$/.test(base);
    if (resolved === artifact.path || workflow || toTickets) {
      return { target: artifact.path, input: { ...event.input, path: artifact.path + selector } };
    }
  }
  return null;
}

function canonicalValidatorInspection(params, cwd, state = null) {
  if (params.action !== "inspect" || params.version !== 1 || !Array.isArray(params.commands) || params.commands.length !== 1) return null;
  const argv = params.commands[0];
  if (!Array.isArray(argv) || argv.some(value => typeof value !== "string" || !value) || argv[0] !== "python3") return null;
  const scriptIndex = argv[1] === "-B" ? 2 : 1;
  if (argv.length !== scriptIndex + 2 || path.basename(argv[scriptIndex]) !== "validate_ticket.py") return null;
  const validator = state ? state.protected_artifacts?.find(artifact => artifact.kind === "validator")?.path : resolveCanonicalValidator().validator;
  if (!validator || (state && validator !== state.validator_path)) return null;
  if (fs.realpathSync(path.resolve(cwd, argv[scriptIndex])) !== validator) return null;
  const ticket = fs.realpathSync(path.resolve(cwd, argv[scriptIndex + 1]));
  if (!fs.statSync(ticket).isFile()) return null;
  if (state && ticket !== state.ticket_path) return null;
  return ["python3", "-B", validator, ticket];
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
  const liveOperations = new Set();
  let toolMap = { mapped: {}, boundaries: [], customMutationBoundary: [] };
  const runningCommands = new Map();
  const runOwnedArgv = async (executionId, argv, options) => {
    const id = lifecycle.status(executionId).active_operation.tool_call_id;
    const controller = new AbortController();
    const abort = () => controller.abort();
    options.signal?.addEventListener("abort", abort, { once: true });
    if (options.signal?.aborted) abort();
    const promise = runArgv(argv, { ...options, signal: controller.signal });
    liveOperations.add(id);
    runningCommands.set(id, { executionId, controller, promise });
    try { return await promise; } finally {
      options.signal?.removeEventListener("abort", abort);
      liveOperations.delete(id);
      runningCommands.delete(id);
    }
  };
  let toolMapInitialized = false;

  const refreshToolMap = () => {
    toolMap = buildExactToolMap(pi);
    toolMapInitialized = true;
    return toolMap;
  };

  const prepareVerification = params => async binding => {
    const target = captureVerificationTarget({
      projectRoot: binding.project_root,
      targetPaths: params.target_paths ?? [],
      allowedOutputPaths: params.allowed_output_paths ?? [],
    });
    if (binding.ticket_status_at_start === "ready") {
      if (!params.probe_binding_path) throw new Error("Ready verification requires one current canonical Probe machine binding before begin_verify");
      await validateProbeHandoff({
        probeBindingPath: params.probe_binding_path,
        projectRoot: binding.project_root,
        ticketPath: binding.ticket_path,
        targetPaths: params.target_paths ?? [],
        allowedOutputPaths: params.allowed_output_paths ?? [],
        bindAuthorityFn: async () => binding,
        captureTargetFn: () => target,
      });
    }
    return { ...binding, verification_target: target, target_drift: null };
  };

  pi.on("resources_discover", async () => {
    refreshToolMap();
    return readySkillDir ? { skillPaths: [readySkillDir] } : {};
  });
  const refreshSessionRuntime = ctx => {
    refreshToolMap();
    lifecycle.recoverInterruptedOperation(sessionId(ctx), new Set([...operationIndex.keys(), ...liveOperations]));
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
    // Device docs are control metadata, not product observations. Internal writes
    // still defer to their registered tool's validation.
    if (INTERNAL_TOOLS.has(event.toolName)) return;
    if ((event.toolName === "read" || event.toolName === "write") && typeof event.input?.path === "string") {
      const device = /^xd:\/\/([^/:?#]+)$/.exec(event.input.path)?.[1];
      if (INTERNAL_TOOLS.has(device) || (event.toolName === "write" && device === "report_issue")) return;
    }

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
      if (state.active_operation) {
        return { block: true, reason: `Ready execution already has active guarded operation ${state.active_operation.tool_call_id}.` };
      }
      if (!policy) {
        if (session.role === "parent") {
          return { block: true, reason: "SUBAGENT parent session may not perform verifier-owned product/runtime actions." };
        }
        if (state.session_id !== sid) return { block: true, reason: "Ready execution/session binding mismatch." };
        if (state.phase !== "ACTIVE") {
          return { block: true, reason: `Ready verification external product/runtime actions require ACTIVE verification; delegated verification waits for Parent CONTINUE. Found ${state.phase}.` };
        }
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
    if (state.worker_inactive) return { block: true, reason: "Ready worker is suspended; only the parent may issue replacement continuation." };

    if (state.phase === "MUTATION_UNCERTAIN") {
      const snapshot = state.uncertainty?.operation?.mutation_snapshot;
      const target = pathFromEvent(event, ctx.cwd);
      if (event.toolName === "read" && snapshot?.targets?.some(item => item.path === target)) {
        operationIndex.set(event.toolCallId, { executionId: state.execution_id, kind: "uncertainty_readback", sessionId: sid });
        return;
      }
      return { block: true, reason: "Ready mutation outcome is uncertain; only exact target readback or terminal BLOCKED is allowed." };
    }

    const authorityRead = boundAuthorityRead(state, event, ctx.cwd);
    const authorityEvent = authorityRead ? { ...event, input: { ...event.input, path: authorityRead.target } } : event;
    const authority = await authorityGate(lifecycle, state, authorityEvent, ctx.cwd);
    if (!authority.allowed) return { block: true, reason: authority.reason };
    if (authority.reviewRead) {
      const target = pathFromEvent(authorityEvent, ctx.cwd);
      const rewritten = authorityRead?.input ?? maybeRewritePath(event, target);
      return rewritten ? { input: rewritten } : undefined;
    }

    const current = lifecycle.status(state.execution_id);
    if (authorityRead && current.phase !== "ACTIVE") return { block: true, reason: `Ready authority revalidation requires ACTIVE verification; found ${current.phase}.` };
    if (current.purpose === "verify" && effectivePolicy === "mutation") {
      return { block: true, reason: "Ready verification keeps Project Root source/config/tests/planning authority immutable; generic mutation tools are blocked." };
    }
    if (effectivePolicy === "mutation" && current.phase !== "ACTIVE") {
      return { block: true, reason: `Ready runtime blocks source mutation in phase ${current.phase}.` };
    }
    if (current.active_operation) {
      return { block: true, reason: `Ready execution already has active guarded operation ${current.active_operation.tool_call_id}.` };
    }

    const target = authorityRead?.target ?? pathFromEvent(event, ctx.cwd);
    if (target) {
      const confinement = authorityRead ? null : projectConfinementReason(current, target);
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
      const prepared = prepareObservation(current, event.toolName, authorityRead?.input ?? normalizedObservationInput, broad, currentnessIdentity, authorityRead ? "REFRESH" : "BLOCK");
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
      let targets;
      try { targets = mutationTargets(event, ctx.cwd); } catch (error) { return { block: true, reason: error.message }; }
      for (const mutationTarget of targets) {
        const reason = projectConfinementReason(current, mutationTarget) || protectedMutationReason(current, mutationTarget);
        if (reason) return { block: true, reason };
      }
      const mutationDigest = mutationDigestFor(event.toolName, event.input);
      const repeatedReason = repeatedMutationReason(current, mutationDigest);
      if (repeatedReason) return { block: true, reason: repeatedReason };
      const snapshot = snapshotPaths(targets);
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

    const rewritten = authorityRead?.input ?? maybeRewritePath(event, target);
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
      lifecycle.resolveMutationUncertainty(tracked.executionId, tracked.sessionId, outcome);
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
    const outcome = resolveSnapshotOutcome(state.active_operation?.mutation_snapshot);
    if (event.isError && outcome === "inconclusive") {
      lifecycle.markMutationUncertain(tracked.executionId, event.toolCallId, "mutation tool failed without attributable target readback");
      return;
    }
    lifecycle.finishOperation(tracked.executionId, event.toolCallId, {
      mutationApplied: !event.isError || outcome === "applied",
      failureClassification: event.isError ? classifyError(event.content) : null,
      failureDetail: event.isError ? JSON.stringify(event.content) : null,
    });
  });

  pi.on("session_shutdown", async (_event, ctx) => {
    const sid = sessionId(ctx);
    await services.cleanupSession(sid);
    const ownedCommands = [...runningCommands.values()].filter(item => lifecycle.status(item.executionId).session_id === sid);
    for (const command of ownedCommands) command.controller.abort();
    await Promise.allSettled(ownedCommands.map(command => command.promise));
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
    for (const [id, operation] of operationIndex) if (operation.sessionId === sid) operationIndex.delete(id);
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
    loadMode: "essential",
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
    loadMode: "essential",
    label: "Ready Guard",
    description: "Bind and advance the internal ready-ticket-implement runtime without changing its external delivery contract.",
    parameters: z.object({
      action: z.enum([
        "cancel_admission", "begin_direct", "begin_verify", "assign_subagent", "begin_delegated", "checkpoint_pre_action", "checkpoint_material_turn",
        "release_checkpoint", "complete", "finalize_verification", "block", "status", "resolve_mutation", "suspend_worker", "replace_worker",
      ]),
      ticket_path: z.string().optional(),
      project_root: z.string().optional(),
      purpose: z.enum(["implement", "verify"]).optional(),
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
        case "cancel_admission": {
          if ([params.ticket_path, params.project_root, params.execution_id, params.assignment_id, params.probe_binding_path].some(Boolean)
            || params.target_paths?.length || params.allowed_output_paths?.length) {
            throw new Error("cancel_admission accepts no Ticket, execution, assignment, or other identifier; it targets only the current session");
          }
          const session = lifecycle.cancelAdmission(sid);
          return resultText({
            session: {
              armed: session.armed,
              purpose: session.purpose ?? null,
              role: session.role ?? null,
              execution_id: session.execution_id ?? null,
              assignment_id: session.assignment_id ?? null,
            },
            execution: null,
          });
        }
        case "begin_direct":
          value = await lifecycle.admit(sid, "implement", admissionToken => lifecycle.beginDirect({
            sessionId: sid, projectRoot: params.project_root, ticketPath: params.ticket_path, purpose: "implement", admissionToken,
          }));
          return resultText(runtimeView(value));
        case "begin_verify":
          value = await lifecycle.admit(sid, "verify", admissionToken => lifecycle.beginDirect({
            sessionId: sid, projectRoot: params.project_root, ticketPath: params.ticket_path, purpose: "verify", admissionToken,
            prepareBinding: prepareVerification(params),
          }));
          return resultText(runtimeView(value));
        case "assign_subagent":
          value = await lifecycle.admit(sid, params.purpose ?? "implement", () => lifecycle.assignSubagent({ parentSessionId: sid, projectRoot: params.project_root, ticketPath: params.ticket_path }));
          return resultText({
            assignment_id: value.assignment_id,
            ticket_path: value.ticket_path,
            project_root: value.project_root,
            status: value.status,
          });
        case "begin_delegated": {
          const assignment = store.readAssignment(params.assignment_id);
          if (!assignment) throw new Error(`unknown assignment: ${params.assignment_id}`);
          value = await lifecycle.admit(sid, assignment.purpose ?? "implement", admissionToken => lifecycle.beginDelegated({
            childSessionId: sid, assignmentId: params.assignment_id, admissionToken,
            prepareBinding: async binding => {
              if (assignment.resume_execution_id) {
                const previous = lifecycle.status(assignment.resume_execution_id);
                if (!previous.continuation_target || !checkVerificationTarget(previous.continuation_target).current) throw new Error("replacement continuation working-tree target changed or was not bound");
              }
              return assignment.purpose === "verify" ? prepareVerification(params)(binding) : binding;
            },
          }));
          return resultText(runtimeView(value));
        }
        case "resolve_mutation": {
          const execution = requireWorkerExecution(lifecycle, sid);
          if (execution.execution_id !== params.execution_id) throw new Error("Ready recovery execution binding mismatch");
          const outcome = resolveSnapshotOutcome(execution.uncertainty?.operation?.mutation_snapshot);
          value = lifecycle.resolveMutationUncertainty(execution.execution_id, sid, outcome);
          return resultText(runtimeView(value));
        }
        case "suspend_worker": {
          const execution = requireWorkerExecution(lifecycle, sid);
          if (execution.execution_id !== params.execution_id) throw new Error("Ready suspension execution binding mismatch");
          if (execution.managed_service) await services.stop(execution.execution_id, sid);
          const target = captureVerificationTarget({ projectRoot: execution.project_root });
          value = lifecycle.suspendWorker(execution.execution_id, sid, target);
          return resultText(runtimeView(value));
        }
        case "replace_worker":
          return resultText(lifecycle.replaceWorker(params.execution_id, sid));
        case "checkpoint_pre_action":
          value = lifecycle.checkpointPreAction(params.execution_id, sid, params.summary ?? null);
          return resultText(runtimeView(value));
        case "checkpoint_material_turn": {
          const before = lifecycle.status(params.execution_id);
          if (before.phase === "MATERIAL_TURN_REQUIRED") await lifecycle.refreshDelegatedAuthority(params.execution_id, sid);
          value = lifecycle.checkpointMaterialTurn(params.execution_id, sid, params.summary ?? null);
          return resultText(runtimeView(value));
        }
        case "release_checkpoint": {
          const execution = lifecycle.status(params.execution_id);
          if (execution.parent_session_id !== sid) throw new Error("only the bound parent may release a checkpoint");
          if (params.decision === "STOP" && execution.managed_service) await services.stop(execution.execution_id, sid);
          value = lifecycle.releaseCheckpoint(params.execution_id, sid, params.decision);
          return resultText(runtimeView(value));
        }
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
          const finalizationId = `ready-finalize-${crypto.randomUUID()}`;
          let reservationActive = false;
          try {
            lifecycle.beginVerificationFinalization(execution.execution_id, sid, params.verdict, finalizationId);
            reservationActive = true;
            liveOperations.add(finalizationId);
            if (execution.managed_service) await services.stop(execution.execution_id, sid);
            if (params.verdict === "VERIFIED") {
              const targetCurrentness = verificationTargetGate(lifecycle, execution.execution_id);
              if (!targetCurrentness.current) throw new Error(`VERIFIED blocked by target drift: ${targetCurrentness.changed.join(", ")}`);
              const authority = await lifecycle.checkAuthorityCurrentness(lifecycle.status(execution.execution_id));
              if (!authority.current) {
                lifecycle.cancelVerificationFinalization(execution.execution_id, sid, finalizationId);
                reservationActive = false;
                lifecycle.markAuthorityDrift(execution.execution_id, authority.changed);
                throw new Error("VERIFIED blocked by authority drift");
              }
              const finalTargetCurrentness = verificationTargetGate(lifecycle, execution.execution_id);
              if (!finalTargetCurrentness.current) throw new Error(`VERIFIED blocked by target drift: ${finalTargetCurrentness.changed.join(", ")}`);
            }
            const finalizationState = lifecycle.verificationFinalizationState(
              execution.execution_id,
              sid,
              params.verdict,
              finalizationId,
            );
            const progression = params.verdict === "VERIFIED" && finalizationState.ticket_status_at_start === "ready"
              ? progressReadyTicketToDone(finalizationState, _signal)
              : {
                progression: "NOT APPLICABLE",
                status_after: finalizationState.ticket_status_at_start,
                detail: null,
              };
            value = lifecycle.finalizeVerification(execution.execution_id, sid, {
              verdict: params.verdict,
              progression,
              finalizationId,
            });
            reservationActive = false;
            return resultText({
              execution: runtimeView(value),
              verification_verdict: params.verdict,
              ticket_progression: progression.progression,
              ticket_status_after: progression.status_after,
              progression_detail: progression.detail,
            });
          } catch (error) {
            if (reservationActive) lifecycle.cancelVerificationFinalization(execution.execution_id, sid, finalizationId);
            throw error;
          } finally {
            liveOperations.delete(finalizationId);
          }
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
    loadMode: "essential",
    label: "Ready Argv",
    description: "Run explicit structured argv. inspect uses commands: [[executable, ...args]]; the canonical python3 validate_ticket.py command is allowed for admission and exact bound ACTIVE verification revalidation. execute/mutate use argv. Shell strings are not accepted.",
    parameters: z.object({
      action: z.enum(["inspect", "execute", "mutate"]),
      version: z.literal(1),
      commands: z.array(z.array(z.string())).optional(),
      argv: z.array(z.string()).optional(),
      target_paths: z.array(z.string()).optional(),
    }),
    async execute(_toolCallId, params, signal, _onUpdate, ctx) {
      const sid = sessionId(ctx);
      const session = lifecycle.sessionState(sid);
      const admissionArgv = !session?.execution_id ? canonicalValidatorInspection(params, ctx.cwd) : null;
      if (!session?.execution_id && admissionArgv) {
        const result = await runArgv(admissionArgv, { cwd: ctx.cwd, timeoutMs: FINAL_VALIDATOR_TIMEOUT_MS, signal });
        return resultText({ action: "inspect", phase: "PRE_ADMISSION", results: [{
          argv: admissionArgv, exit_code: result.exitCode, timed_out: result.timedOut,
          stdout: result.stdout.slice(0, MAX_OBSERVATION_OUTPUT_BYTES),
          stderr: result.stderr.slice(0, MAX_OBSERVATION_OUTPUT_BYTES),
        }] });
      }
      let state = requireWorkerExecution(lifecycle, sid);
      const authority = await lifecycle.checkAuthorityCurrentness(state);
      if (!authority.current) {
        lifecycle.markAuthorityDrift(state.execution_id, authority.changed);
        throw new Error("Ready authority changed; re-confirm authority before ready_argv execution");
      }

      if (params.action === "inspect") {
        const canonicalArgv = state.purpose === "verify" ? canonicalValidatorInspection(params, state.project_root, state) : null;
        if (canonicalArgv) {
          if (state.active_operation) throw new Error(`Ready execution already has active guarded operation ${state.active_operation.tool_call_id}.`);
          if (state.phase !== "ACTIVE") throw new Error(`Canonical revalidation requires ACTIVE verification; found ${state.phase}`);
          const target = verificationTargetGate(lifecycle, state.execution_id);
          if (!target.current) throw new Error(`Canonical revalidation blocked by target drift: ${target.changed.join(", ")}`);
        }
        const request = canonicalArgv ? { commands: [canonicalArgv] } : validateInspectRequest({ version: params.version, commands: params.commands });
        const outputs = [];
        for (const argv of request.commands) {
          state = lifecycle.status(state.execution_id);
          if (state.active_operation) throw new Error(`Ready execution already has active guarded operation ${state.active_operation.tool_call_id}.`);
          if (["COMPLETE", "BLOCKED", "MUTATION_UNCERTAIN"].includes(state.phase)) throw new Error(`ready_argv inspect is unavailable in phase ${state.phase}`);
          const confinement = canonicalArgv ? null : argvConfinementReason(state, argv);
          if (confinement) throw new Error(confinement);
          const broad = isBroadInventory("bash", { argv });
          const inventory = inventoryAllowedForPhase(state, broad);
          if (!inventory.allowed) throw new Error(inventory.reason);
          const prepared = prepareObservation(state, "ready_argv.inspect", { argv }, broad, null, canonicalArgv ? "REFRESH" : "BLOCK");
          if (!prepared.allowed) throw new Error(prepared.reason);
          store.writeExecution(state);
          const syntheticId = `ready-argv-${crypto.randomUUID()}`;
          lifecycle.beginOperation(state.execution_id, { toolCallId: syntheticId, kind: "observation", observationDigest: prepared.digest });
          let result;
          try {
            result = await runOwnedArgv(state.execution_id, argv, { cwd: state.project_root, signal, timeoutMs: canonicalArgv ? FINAL_VALIDATOR_TIMEOUT_MS : undefined });
          } catch (error) {
            const current = lifecycle.status(state.execution_id);
            recordObservationResult(current, prepared.digest, {
              success: false,
              outputBytes: 0,
              errorClassification: classifyError(error?.message ?? error),
            });
            store.writeExecution(current);
            lifecycle.finishOperation(state.execution_id, syntheticId, { mutationApplied: false });
            if (canonicalArgv) verificationTargetGate(lifecycle, state.execution_id);
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
          if (canonicalArgv) {
            const target = verificationTargetGate(lifecycle, state.execution_id);
            if (!target.current) throw new Error(`Canonical revalidation detected target drift: ${target.changed.join(", ")}`);
            const currentAuthority = await lifecycle.checkAuthorityCurrentness(lifecycle.status(state.execution_id));
            if (!currentAuthority.current) {
              lifecycle.markAuthorityDrift(state.execution_id, currentAuthority.changed);
              throw new Error("Ready authority changed during canonical revalidation");
            }
          }
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
        if (state.active_operation) throw new Error(`Ready execution already has active guarded operation ${state.active_operation.tool_call_id}.`);
        const beforeTarget = verificationTargetGate(lifecycle, state.execution_id);
        if (!beforeTarget.current) throw new Error(`ready_argv execute blocked by target drift: ${beforeTarget.changed.join(", ")}`);
        const request = validateExecutionRequest({ version: params.version, argv: params.argv });
        const confinement = argvConfinementReason(state, request.argv);
        if (confinement) throw new Error(confinement);
        const prepared = prepareObservation(state, "ready_argv.execute", { argv: request.argv }, false, null, "REFRESH");
        if (!prepared.allowed) throw new Error(prepared.reason);
        store.writeExecution(state);
        const syntheticId = `ready-argv-${crypto.randomUUID()}`;
        lifecycle.beginOperation(state.execution_id, { toolCallId: syntheticId, kind: "observation", observationDigest: prepared.digest });
        let result;
        try {
          result = await runOwnedArgv(state.execution_id, request.argv, { cwd: state.project_root, signal });
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
      const mutationDigest = mutationDigestFor("ready_argv.mutate", {
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
        mutationSnapshot: snapshotPaths(targetPaths),
      });
      liveOperations.add(syntheticId);
      let result;
      try {
        result = await runOwnedArgv(state.execution_id, request.argv, { cwd: state.project_root, signal });
      } catch (error) {
        const outcome = signal?.aborted ? "inconclusive" : resolveSnapshotOutcome(lifecycle.status(state.execution_id).active_operation?.mutation_snapshot);
        if (outcome === "inconclusive") lifecycle.markMutationUncertain(state.execution_id, syntheticId, "structured mutation interrupted or failed without attributable target readback; automatic replay is forbidden");
        else lifecycle.finishOperation(state.execution_id, syntheticId, {
          mutationApplied: outcome === "applied", failureClassification: classifyError(error?.message ?? error), failureDetail: String(error?.message ?? error),
        });
        throw error;
      } finally {
        liveOperations.delete(syntheticId);
      }
      if (result.timedOut) {
        lifecycle.markMutationUncertain(state.execution_id, syntheticId, "structured mutation argv timed out; automatic replay is forbidden");
      } else if (result.exitCode === 0) {
        lifecycle.finishOperation(state.execution_id, syntheticId, {
          mutationApplied: true,
          commandOutputBytes: Buffer.byteLength(result.stdout, "utf8") + Buffer.byteLength(result.stderr, "utf8"),
        });
      } else {
        const outcome = resolveSnapshotOutcome(lifecycle.status(state.execution_id).active_operation?.mutation_snapshot);
        if (outcome === "inconclusive") lifecycle.markMutationUncertain(state.execution_id, syntheticId, "structured mutation failed without attributable target readback");
        else lifecycle.finishOperation(state.execution_id, syntheticId, {
          mutationApplied: outcome === "applied",
          failureClassification: classifyError(result.stderr || `exit ${result.exitCode}`),
          failureDetail: result.stderr || `exit ${result.exitCode}`,
        });
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
    loadMode: "essential",
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
