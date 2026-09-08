import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { ReadyLifecycle } from "./lifecycle.js";
import { RuntimeStore, stableDigest } from "./state-store.js";
import { isInsideProject, resolveCanonicalValidator } from "./authority-binding.js";
import { canonicalPath, fileIdentity } from "./verification-target.js";
import { validateExecutionRequest, validateInspectRequest, validateMutationRequest } from "./argv-policy.js";
import { buildExactToolMap, mappedPolicy } from "./tool-map.js";
import { finalizeVerification } from "./finalization.js";

const internal = new Set(["ready_guard", "ready_argv"]);
const sid = ctx => ctx?.sessionManager?.getSessionId?.() ?? (() => { throw new Error("CAPABILITY_UNAVAILABLE: host session identity missing"); })();
const resultText = value => ({ content: [{ type: "text", text: JSON.stringify(value, null, 2) }], details: value });
const fail = message => { throw new Error(message); };

function mutationTargets(event, cwd) {
  if (event.toolName !== "edit" || typeof event.input?.input !== "string") {
    if (!event.input?.path || /^[a-z][a-z0-9+.-]*:\/\//i.test(event.input.path)) fail("CAPABILITY_UNAVAILABLE: mutation requires a local file");
    return [canonicalPath(event.input.path, cwd)];
  }
  const targets = [];
  for (const line of event.input.input.split(/\r?\n/)) {
    if (!line.trim() || line.startsWith("+")) continue;
    const header = /^\[(.+)#[a-fA-F0-9]{4}\]$/.exec(line);
    if (header) targets.push(canonicalPath(header[1], cwd));
    else if (line.startsWith("MV ")) {
      const raw = line.slice(3).trim(); targets.push(canonicalPath(raw.startsWith('"') ? JSON.parse(raw) : raw, cwd));
    } else if (!/^(?:PUT |CUT |REM$)/.test(line)) fail("CAPABILITY_UNAVAILABLE: only attributable hashline edits supported");
  }
  if (!targets.length) fail("mutation has no attributable paths");
  return [...new Set(targets)];
}
function validateMutationPaths(state, targets) {
  const protectedPaths = [...state.protected_artifacts.map(item => item.path), ...(state.plan_binding?.plans ?? []).map(item => item.path), state.plan_binding?.review_path, ...(state.navigation_binding?.plans ?? []).map(item => item.path), state.navigation_binding?.review_path].filter(Boolean);
  for (const target of targets) {
    if (protectedPaths.some(file => isInsideProject(target, file) || target === file)) fail(`protected authority/method path: ${target}`);
    const output = state.allowed_output_paths.includes(target);
    if (!output && (!isInsideProject(state.project_root, target) || state.purpose === "verify")) fail(`mutation outside admitted source/output surface: ${target}`);
    if (fs.existsSync(target) && !fs.lstatSync(target).isFile()) fail("CAPABILITY_UNAVAILABLE: native directory/archive/database mutation is not a file operation");
  }
}
function normalizeDevice(event) {
  if (!["read", "write"].includes(event.toolName)) return event;
  const device = /^xd:\/\/([^/:?#]+)$/.exec(event.input?.path ?? "")?.[1];
  if (!device) return event;
  if (event.toolName === "read") return { ...event, controlRead: true };
  if (internal.has(device) || device === "hub" || device === "todo") return { ...event, toolName: device, input: JSON.parse(event.input.content), device: true };
  return { ...event, unknownDevice: true };
}

export function installReadyRuntime(pi, options = {}) {
  const z = pi.zod;
  const store = options.store ?? new RuntimeStore(options.dataRoot);
  const executeArgv = options.executeArgv ?? (async (argv, request = {}) => {
    if (!pi.exec) fail("CAPABILITY_UNAVAILABLE: host structured exec missing");
    const raw = await pi.exec(argv[0], argv.slice(1), { cwd: request.cwd, signal: request.signal, timeout: request.timeout ?? 120000 });
    const interrupted = Boolean(raw.killed || request.signal?.aborted);
    return { exitCode: raw.code, interrupted, terminationState: interrupted ? "unknown" : "settled", stdout: raw.stdout, stderr: raw.stderr };
  });
  const bundleRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
  let bundleIdentity = options.bundleIdentity ?? process.env.IIS_READY_BUNDLE_ID;
  if (!bundleIdentity && fs.existsSync(path.join(bundleRoot, "bundle.json"))) bundleIdentity = JSON.parse(fs.readFileSync(path.join(bundleRoot, "bundle.json"), "utf8")).bundle_id;
  const lifecycle = options.lifecycle ?? new ReadyLifecycle({ store, executeArgv, validatorPath: options.validatorPath ?? process.env.IIS_READY_VALIDATOR_PATH, bundleIdentity: bundleIdentity ?? "source", recoveryOwner: options.recoveryOwner });
  const pending = new Map();
  const commands = new Map();
  // Host action APIs become available only after extension registration finishes.
  let toolMap = null;
  const currentExecution = actor => {
    const session = lifecycle.sessionState(actor);
    if (!session?.execution_id) fail("explicit Ready begin is required");
    return lifecycle.assertOwner(lifecycle.status(session.execution_id), actor);
  };
  const evidenceOutput = (state, operationId, value) => {
    const directory = path.join(store.root, "outputs", state.execution_id);
    fs.mkdirSync(directory, { recursive: true, mode: 0o700 });
    const file = path.join(directory, `${operationId}.json`);
    fs.writeFileSync(file, JSON.stringify(value), { mode: 0o600 });
    return file;
  };
  pi.on("resources_discover", async () => {
    toolMap = buildExactToolMap(pi);
    return options.readySkillDir ? { skillPaths: [options.readySkillDir] } : {};
  });
  for (const name of ["session_start", "session_switch", "session_branch"]) pi.on(name, async (_event, ctx) => {
    toolMap = buildExactToolMap(pi);
    lifecycle.recoverInterruptedOperation(sid(ctx), new Set([...pending.values()].map(item => item.operationId).concat([...commands.keys()])));
  });
  pi.on("session_shutdown", async () => {
    // Explicit native hub stop is required before terminal. Shutdown is not settlement proof.
    for (const command of commands.values()) command.controller.abort();
    await Promise.allSettled([...commands.values()].map(command => command.promise));
  });

  pi.on("tool_call", async (raw, ctx) => {
    try {
      const actor = sid(ctx), event = normalizeDevice(raw), session = lifecycle.sessionState(actor);
      if (internal.has(event.toolName)) return; // Each internal action checks its exact controlling owner.
      if (!session?.execution_id) {
        if (session?.role === "parent" && !["read", "grep", "glob", "hub", "task"].includes(event.toolName)) fail("assigned parent cannot perform worker mutations");
        return; // Reading skills and authoring preparation never arms a session.
      }
      const bound = lifecycle.status(session.execution_id);
      // A terminal owner may close its own host checklist, never issue product work.
      // Superseded/inactive workers remain fenced even for session bookkeeping.
      const controlOwner = session.role === "parent" ? bound.parent_session_id : bound.session_id;
      if ((bound.phase === "COMPLETE" || bound.phase === "BLOCKED") && !bound.worker_inactive && controlOwner === actor && mappedPolicy(toolMap, event.toolName) === "session_control" && !event.unknownDevice) return;
      if (session.role === "parent") {
        lifecycle.assertOwner(bound, actor, { controller: true, inactive: true });
        if (mappedPolicy(toolMap, event.toolName) === "session_control" || ["read", "grep", "glob"].includes(event.toolName) || event.toolName === "hub" && !event.input?.name && event.input?.op !== "start") return;
        if (mappedPolicy(toolMap, event.toolName) === "mutation" && !event.unknownDevice) {
          const targets = mutationTargets(event, ctx.cwd);
          validateMutationPaths(bound, targets);
          if (targets.every(target => bound.allowed_output_paths.includes(target))) return;
        }
        fail("bound parent cannot dispatch worker-owned product effects");
      }
      const state = lifecycle.assertOwner(bound, actor);
      // Owner fence intentionally precedes mapping, including unknown/device paths.
      if (event.controlRead) return;
      const policy = mappedPolicy(toolMap, event.toolName);
      if (!policy || policy === "unsupported" || event.unknownDevice) fail(`CAPABILITY_UNAVAILABLE: ${event.toolName}; use reviewed native file/structured argv/hub surfaces`);
      if (policy === "session_control") return;
      // OMP's device dispatcher invokes the canonical tool wrapper with the same
      // call ID. Bind that inner dispatch to the already reserved outer action.
      const nested = pending.get(raw.toolCallId);
      if (nested?.device && !event.device && event.toolName === "hub") {
        if (nested.nestedDispatched || nested.actor !== actor || nested.executionId !== state.execution_id || state.active_operation?.operation_id !== nested.operationId || stableDigest(event.input) !== stableDigest(nested.service)) fail("mismatched or repeated nested device dispatch");
        nested.nestedDispatched = true;
        return;
      }
      if (policy === "observation") { await lifecycle.ensureCurrent(state.execution_id, actor); return; }
      if (policy === "hub") {
        const request = event.input ?? {};
        if (!request.name && request.op !== "start") return; // Coordination is not a product operation.
        if (!["start", "logs", "wait", "stop", "describe"].includes(request.op)) fail("Ready-owned services forbid restart/send/adoption");
        const owned = state.owned_service;
        if (request.op === "start") {
          await lifecycle.ensureCurrent(state.execution_id, actor, { effect: true });
          if (owned) fail("one execution-owned service at a time");
          if (request.name !== `ready-${state.execution_id}` || request.persist || request.detached || request.restart && request.restart !== "no") fail(`ephemeral owned service requires unique name ready-${state.execution_id}, persist:false, detached:false, restart:no`);
          if (!request.ready || !request.ready.log && !request.ready.port) fail("service requires observable readiness conditions");
          if (canonicalPath(request.cwd ?? ctx.cwd, ctx.cwd) !== state.project_root) fail("service cwd must equal bound Project Root");
        } else {
          if (!owned || owned.name !== request.name) fail("cannot control a shared/preexisting or different service");
          if (["logs", "describe"].includes(request.op)) return;
          // Cleanup is permitted while paused; never invent stop/reap behind the host tool.
          if (state.active_operation || state.uncertainty) fail("settle uncertain activity before service operation");
        }
        const operationId = crypto.randomUUID();
        if (["stop", "wait"].includes(request.op) && state.phase !== "ACTIVE") {
          lifecycle.update(state.execution_id, current => { lifecycle.assertOwner(current, actor); current.active_operation = { operation_id: operationId, kind: "service", effect_surface: request.name, owner: actor }; });
        } else lifecycle.beginOperation(state.execution_id, actor, { operation_id: operationId, kind: "service", effect_surface: request.name });
        pending.set(raw.toolCallId, { actor, executionId: state.execution_id, operationId, service: request, beforeService: owned, device: event.device === true });
        return;
      }
      const targets = mutationTargets(event, ctx.cwd);
      validateMutationPaths(state, targets);
      // Declared outside-root reports/readback records are not product replay.
      // Writing one neither clears uncertainty nor releases a paused execution.
      if (targets.every(target => state.allowed_output_paths.includes(target))) return;
      await lifecycle.ensureCurrent(state.execution_id, actor, { effect: true });
      const operation = lifecycle.beginOperation(state.execution_id, actor, { kind: "local_file", effect_surface: targets.join("\n"), snapshot: targets.map(file => ({ path: file, before: fileIdentity(file) })) });
      pending.set(raw.toolCallId, { actor, executionId: state.execution_id, operationId: operation.operation_id, targets });
    } catch (error) { return { block: true, reason: error.message }; }
  });
  pi.on("tool_result", async event => {
    const operation = pending.get(event.toolCallId);
    if (!operation) return;
    pending.delete(event.toolCallId);
    const { actor, executionId, operationId } = operation;
    let uncertain = Boolean(event.isError), detail = event.isError ? "host tool returned an error; inspect exact effect" : null;
    try {
      if (operation.service) {
        const daemon = event.details?.daemon ?? (event.details?.xdev?.tool === "hub" ? event.details.xdev.inner?.daemon : null);
        if (!daemon?.id || !Number.isFinite(daemon.startedAt) || !daemon.owner || daemon.name !== operation.service.name || daemon.persist || daemon.detached || daemon.restartCount !== 0) fail("host did not return an attributable ephemeral service generation");
        const previous = operation.beforeService;
        if (previous && (previous.resourceId !== daemon.id || previous.generation !== `${daemon.startedAt}:${daemon.restartCount}` || previous.owner !== daemon.owner)) fail("service generation/owner changed; result is not owned settlement");
        const handle = { host: "omp", projectScope: lifecycle.status(executionId).project_root, resourceId: daemon.id, name: daemon.name, owner: daemon.owner, generation: `${daemon.startedAt}:${daemon.restartCount}`, readiness: daemon.readyAt ? "observed" : "pending", terminalState: daemon.state, evidenceReference: `host-tool:${event.toolCallId}`, settlement_scope: "host-reported process tree; escaped descendants/external effects require authoritative readback" };
        lifecycle.recordService(executionId, actor, handle, operationId);
        // A readiness timeout is a live owned handle, not a failed non-start.
        uncertain = false;
      } else if (event.isError) {
        const state = lifecycle.status(executionId), snapshot = state.active_operation?.snapshot;
        if (snapshot?.every(item => JSON.stringify(item.before) === JSON.stringify(fileIdentity(item.path)))) { uncertain = false; detail = "exact local native file identities unchanged"; }
      }
      lifecycle.finishOperation(executionId, actor, operationId, { uncertain, detail });
    } catch (error) {
      const hostError = event.isError ? (event.content ?? []).filter(part => part.type === "text").map(part => part.text).join("\n") : "";
      const detail = hostError ? `${error.message}; host error: ${hostError}` : error.message;
      try { lifecycle.finishOperation(executionId, actor, operationId, { uncertain: true, detail }); } catch { /* A superseded result cannot mutate the new owner. */ }
      return { content: [...(event.content ?? []), { type: "text", text: `Ready effect recovery required: ${error.message}` }], isError: true };
    }
  });

  pi.registerTool({
    name: "ready_guard", loadMode: "essential", label: "Ready Guard",
    description: "Inspect authority without arming; bind current review and exact owner; manage checkpoints, effect recovery and guarded status-only progression.",
    parameters: z.object({
      action: z.enum(["inspect_authority", "cancel_admission", "recover_admission", "begin_direct", "begin_verify", "assign_subagent", "begin_delegated", "checkpoint", "release_checkpoint", "complete", "finalize_verification", "block", "status", "resolve_mutation", "suspend_worker", "replace_worker"]),
      ticket_path: z.string().optional(), project_root: z.string().optional(), purpose: z.enum(["implement", "verify"]).optional(), assignment_id: z.string().optional(), execution_id: z.string().optional(), plan_review_path: z.string().optional(),
      target_paths: z.array(z.string()).optional(), allowed_output_paths: z.array(z.string()).optional(),
      kind: z.enum(["PRE_RUNTIME", "MATERIAL_TURN", "PRE_PROGRESSION"]).optional(), verdict: z.enum(["VERIFIED", "FAILED", "INCONCLUSIVE"]).optional(), decision: z.enum(["CONTINUE", "STEER", "STOP"]).optional(), summary: z.string().optional(), reason: z.string().optional(),
      reservation_id: z.string().optional(), recovery_evidence_reference: z.string().optional(), operation_id: z.string().optional(), effect_surface: z.string().optional(), evidence_reference: z.string().optional(), outcome: z.enum(["applied", "not_applied", "inconclusive"]).optional(),
    }),
    async execute(_callId, params, _signal, _onUpdate, ctx) {
      const actor = sid(ctx);
      const input = { projectRoot: params.project_root, ticketPath: params.ticket_path, purpose: params.purpose ?? "implement", planReviewPath: params.plan_review_path, targetPaths: params.target_paths, allowedOutputPaths: params.allowed_output_paths };
      let value;
      switch (params.action) {
        case "inspect_authority": value = await lifecycle.bindAuthority({ projectRoot: params.project_root, ticketPath: params.ticket_path, allowedStatuses: ["ready", "done"] }); break;
        case "begin_direct": value = await lifecycle.beginDirect({ sessionId: actor, ...input }); break;
        case "begin_verify": value = await lifecycle.beginDirect({ sessionId: actor, ...input, purpose: "verify" }); break;
        case "assign_subagent": value = await lifecycle.assignSubagent({ parentSessionId: actor, ...input }); break;
        case "begin_delegated": value = await lifecycle.beginDelegated({ childSessionId: actor, assignmentId: params.assignment_id, planReviewPath: params.plan_review_path }); break;
        case "checkpoint": value = lifecycle.checkpoint(params.execution_id, actor, params.kind, params.summary); break;
        case "release_checkpoint": value = await lifecycle.releaseCheckpoint(params.execution_id, actor, params.decision, { planReviewPath: params.plan_review_path }); break;
        case "complete": value = await lifecycle.complete(params.execution_id, actor); break;
        case "finalize_verification": value = await finalizeVerification(lifecycle, params.execution_id, actor, params.verdict); break;
        case "block": value = params.execution_id ? lifecycle.block(params.execution_id, actor, params.reason) : lifecycle.cancelAdmission(actor, params.assignment_id); break;
        case "cancel_admission": value = lifecycle.cancelAdmission(actor, params.assignment_id); break;
        case "recover_admission": value = lifecycle.recoverAdmission({ actor, projectRoot: params.project_root, ticketPath: params.ticket_path, reservationId: params.reservation_id, recoveryEvidenceReference: params.recovery_evidence_reference }); break;
        case "resolve_mutation": value = lifecycle.resolveMutationUncertainty(params.execution_id, actor, { operationId: params.operation_id, effectSurface: params.effect_surface, evidenceReference: params.evidence_reference, outcome: params.outcome }); break;
        case "suspend_worker": value = lifecycle.suspendWorker(params.execution_id, actor); break;
        case "replace_worker": value = await lifecycle.replaceWorker(params.execution_id, actor, { planReviewPath: params.plan_review_path }); break;
        case "status": value = { session: lifecycle.sessionState(actor), execution: params.execution_id ? lifecycle.status(params.execution_id) : null, active_ticket: params.project_root && params.ticket_path ? store.readActiveTicket(fs.realpathSync(params.project_root), fs.realpathSync(params.ticket_path)) : null, runtime_protocol: "iis-ready/v2", bundle_identity: lifecycle.authorityOptions.bundleIdentity, loaded_module: fileURLToPath(import.meta.url), tool_map: toolMap }; break;
        default: fail("unknown action");
      }
      return resultText(value);
    },
  });
  pi.registerTool({
    name: "ready_argv", loadMode: "essential", label: "Ready Argv",
    description: "Native host structured argv. inspect is read-only; execute/mutate reserve opaque effects. Arbitrary programs are not OS-sandboxed. Interrupted/nonzero effects require authoritative owner readback, never local-hash replay.",
    parameters: z.object({ action: z.enum(["inspect", "execute", "mutate"]), version: z.literal(1), commands: z.array(z.array(z.string())).optional(), argv: z.array(z.string()).optional(), target_paths: z.array(z.string()).optional() }),
    async execute(_callId, params, signal, _onUpdate, ctx) {
      const actor = sid(ctx);
      if (!lifecycle.sessionState(actor)?.execution_id && params.action === "inspect") {
        const original = params.commands?.[0];
        const argv = original?.[1] === "-B" ? [original[0], ...original.slice(2)] : original;
        if (params.version === 1 && params.commands?.length === 1 && argv?.length === 3 && argv[0] === "python3" && argv[1] === resolveCanonicalValidator(lifecycle.authorityOptions.validatorPath)) {
          if (!isInsideProject(fs.realpathSync(ctx.cwd), fs.realpathSync(argv[2]))) fail("canonical admission Ticket must be inside requested root");
          return resultText({ action: "inspect", results: [await executeArgv(["python3", "-B", ...argv.slice(1)], { cwd: ctx.cwd, signal })] });
        }
        const inspection = validateInspectRequest(params);
        return resultText({ action: "inspect", results: await Promise.all(inspection.commands.map(command => executeArgv(command, { cwd: ctx.cwd, signal }))) });
      }
      const state = currentExecution(actor);
      await lifecycle.ensureCurrent(state.execution_id, actor, { effect: params.action !== "inspect" });
      if (params.action === "inspect") {
        let request;
        const original = params.commands?.[0];
        const candidate = original?.[1] === "-B" ? [original[0], ...original.slice(2)] : original;
        if (params.version === 1 && params.commands?.length === 1 && candidate?.length === 3 && candidate[0] === "python3" && candidate[1] === state.validator_path && candidate[2] === state.ticket_path) {
          request = { commands: [["python3", "-B", ...candidate.slice(1)]] };
        } else request = validateInspectRequest(params);
        const results = await Promise.all(request.commands.map(argv => executeArgv(argv, { cwd: state.project_root, signal })));
        const outputRef = evidenceOutput(state, crypto.randomUUID(), results);
        return resultText({ action: "inspect", results, output_ref: outputRef });
      }
      const request = params.action === "mutate" ? validateMutationRequest(params) : validateExecutionRequest(params);
      if (params.action === "mutate") {
        if (state.purpose !== "implement" || !params.target_paths?.length) fail("mutate requires implement and explicit target_paths");
        validateMutationPaths(state, params.target_paths.map(file => canonicalPath(file, state.project_root)));
      }
      // Paths are a reviewed effect contract, not a proof of arbitrary program confinement.
      for (const argument of request.argv.slice(1)) {
        if (path.isAbsolute(argument) || argument.startsWith("../")) {
          const file = canonicalPath(argument, state.project_root);
          if (!isInsideProject(state.project_root, file) && !state.allowed_output_paths.includes(file)) fail(`argv outside root/output boundary: ${argument}`);
          if (params.action === "mutate") validateMutationPaths(state, [file]);
        }
      }
      const operation = lifecycle.beginOperation(state.execution_id, actor, { kind: "opaque_program", effect_surface: JSON.stringify(request.argv), target_paths: params.target_paths ?? [] });
      const controller = new AbortController();
      const abort = () => controller.abort();
      signal?.addEventListener("abort", abort, { once: true });
      if (signal?.aborted) abort();
      const promise = executeArgv(request.argv, { cwd: state.project_root, signal: controller.signal });
      commands.set(operation.operation_id, { controller, promise });
      try {
        const result = await promise;
        const outputRef = evidenceOutput(state, operation.operation_id, result);
        const uncertain = result.interrupted || result.terminationState !== "settled" || result.exitCode !== 0;
        lifecycle.finishOperation(state.execution_id, actor, operation.operation_id, { uncertain, detail: uncertain ? "opaque program may have partially applied; authoritative effect-owner readback required" : null, result: { exit_code: result.exitCode, output_ref: outputRef, termination_state: result.terminationState } });
        await lifecycle.ensureCurrent(state.execution_id, actor);
        return resultText({ action: params.action, operation_id: operation.operation_id, effect_surface: operation.effect_surface, exit_code: result.exitCode, interrupted: result.interrupted, termination_state: result.terminationState, stdout: String(result.stdout ?? "").slice(0, 48000), stderr: String(result.stderr ?? "").slice(0, 48000), output_ref: outputRef, execution: lifecycle.status(state.execution_id) });
      } catch (error) {
        if (lifecycle.status(state.execution_id).active_operation?.operation_id === operation.operation_id) lifecycle.finishOperation(state.execution_id, actor, operation.operation_id, { uncertain: true, detail: `host execution/output capture failed: ${error.message}` });
        throw error;
      } finally { signal?.removeEventListener("abort", abort); commands.delete(operation.operation_id); }
    },
  });
  return { store, lifecycle, getToolMap: () => toolMap };
}
