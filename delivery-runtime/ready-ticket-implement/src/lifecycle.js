import crypto from "node:crypto";
import fs from "node:fs";
import { bindAuthority, checkAuthorityCurrentness } from "./authority-binding.js";
import { bindPlanReview, checkPlanCurrentness, hashBytes } from "./plan-binding.js";
import { captureVerificationTarget, checkVerificationTarget, validateOutputPaths } from "./verification-target.js";

const terminal = state => ["COMPLETE", "BLOCKED"].includes(state.phase);
const copy = value => structuredClone(value);
const fail = message => { throw new Error(message); };

export class ReadyLifecycle {
  constructor({ store, executeArgv, validatorPath, runtimeProtocol = "iis-ready/v2", bundleIdentity = "source", recoveryOwner, bindAuthority: bind = bindAuthority, checkAuthorityCurrentness: check = checkAuthorityCurrentness }) {
    this.store = store;
    this.executeArgv = executeArgv;
    this.authorityOptions = { executeArgv, validatorPath, runtimeProtocol, bundleIdentity };
    this.bindAuthority = input => bind({ ...this.authorityOptions, ...input });
    this.checkAuthorityCurrentness = check;
    this.recoveryOwner = recoveryOwner;
  }
  sessionState(id) { return this.store.readSession(id); }
  status(id) { return this.store.readExecution(id) ?? fail(`unknown execution: ${id}`); }
  assertOwner(state, actor, { controller = false, inactive = false } = {}) {
    const expected = controller ? (state.parent_session_id || state.session_id) : state.session_id;
    if (expected !== actor || (!inactive && state.worker_inactive)) fail("OWNER_MISMATCH: inactive or different owner");
    const slot = this.store.readActiveTicket(state.project_root, state.ticket_path);
    if (!slot || slot.identity !== state.reservation_id || slot.execution_id !== state.execution_id) fail("OWNER_SUPERSEDED: execution no longer owns Ticket");
    if (terminal(state)) fail(`execution is ${state.phase}`);
    return state;
  }
  assertDispatch(id, actor, effect = false) {
    const state = this.assertOwner(this.status(id), actor);
    if (effect && state.phase !== "ACTIVE") fail(`effect requires ACTIVE; found ${state.phase}`);
    if (effect && (state.active_operation || state.uncertainty)) fail("effect already active or uncertain");
    return state;
  }
  update(id, mutate) {
    return this.store.withLock(() => {
      const state = this.status(id);
      mutate(state);
      return this.store.writeExecution(state);
    });
  }
  async prepare({ projectRoot, ticketPath, purpose = "implement", planReviewPath, targetPaths = [], allowedOutputPaths = [] }) {
    if (!["implement", "verify"].includes(purpose)) fail("invalid purpose");
    if (purpose === "implement" && !planReviewPath) fail("PLAN_REVIEW_REQUIRED: supply actual current plan review");
    const binding = await this.bindAuthority({ projectRoot, ticketPath, allowedStatuses: purpose === "verify" ? ["ready", "done"] : ["ready"] });
    const plan = purpose === "implement" ? bindPlanReview({ planReviewPath, authority: binding }) : null;
    let navigation = null;
    if (purpose === "verify" && planReviewPath) navigation = bindPlanReview({ planReviewPath, authority: binding, requireAdmit: false });
    const outputs = validateOutputPaths(binding.project_root, allowedOutputPaths);
    if ([...binding.protected_artifacts.map(item => item.path), plan?.review_path, navigation?.review_path].some(file => outputs.includes(file))) fail("authority/review cannot be an allowed output");
    const target = purpose === "verify" ? await captureVerificationTarget({ projectRoot: binding.project_root, targetPaths, allowedOutputPaths: outputs, methodPaths: navigation ? [navigation.review_path, ...navigation.plans.map(p => p.path)] : [], productPaths: binding.protected_artifacts.map(p => p.path), executeArgv: this.executeArgv }) : null;
    return { ...binding, purpose, plan_binding: plan, navigation_binding: navigation, verification_target: target, allowed_output_paths: outputs };
  }
  reserve(binding, actor, fields) {
    return this.store.withLock(() => {
      const existing = this.store.readActiveTicket(binding.project_root, binding.ticket_path);
      if (existing) fail(`TICKET_BUSY: ${existing.identity}`);
      const session = this.sessionState(actor);
      if (session?.execution_id && !terminal(this.status(session.execution_id))) fail("actor already bound to an execution");
      if (session?.reservation_id) fail("actor already has an in-flight admission");
      const reservation = { identity: crypto.randomUUID(), owner: actor, recovery_owner: this.recoveryOwner || actor, state: "reserved", ...fields };
      this.store.writeActiveTicket(binding.project_root, binding.ticket_path, reservation);
      this.store.writeSession(actor, { role: "admission", reservation_id: reservation.identity, project_root: binding.project_root, ticket_path: binding.ticket_path });
      return reservation;
    });
  }
  assertReservation(binding, reservation) {
    const current = this.store.readActiveTicket(binding.project_root, binding.ticket_path);
    if (!current || current.identity !== reservation.identity) fail("ADMISSION_REVOKED: reservation identity changed");
  }
  async checkPrepared(binding) {
    if (!(await this.checkAuthorityCurrentness(binding)).current) fail("AUTHORITY_DRIFT during admission");
    if (binding.plan_binding && !checkPlanCurrentness(binding.plan_binding).current) fail("PLAN_REVIEW_STALE during admission");
    if (binding.verification_target && !(await checkVerificationTarget(binding.verification_target, { executeArgv: this.executeArgv })).current) fail("TARGET_DRIFT during admission");
  }
  newExecution(binding, actor, reservation, fields = {}) {
    return { ...binding, execution_id: reservation.execution_id ?? crypto.randomUUID(), session_id: actor, parent_session_id: null, assignment_id: null, execution_mode: "DIRECT", reservation_id: reservation.identity, phase: "ACTIVE", pause: null, active_operation: null, owned_service: null, uncertainty: null, worker_inactive: false, ...fields };
  }
  commitExecution(state, reservation) {
    this.assertReservation(state, reservation);
    this.store.writeExecution(state);
    this.store.writeActiveTicket(state.project_root, state.ticket_path, { ...reservation, state: "active", execution_id: state.execution_id, owner: state.session_id });
    this.store.writeSession(state.session_id, { execution_id: state.execution_id, role: "worker", assignment_id: state.assignment_id });
    if (state.parent_session_id) this.store.writeSession(state.parent_session_id, { execution_id: state.execution_id, role: "parent", assignment_id: state.assignment_id });
    return state;
  }
  async beginDirect({ sessionId, ...input }) {
    const existing = this.sessionState(sessionId);
    if (existing?.execution_id) {
      const previous = this.status(existing.execution_id);
      if (!terminal(previous)) {
        if (previous.execution_mode !== "DIRECT" || previous.project_root !== fs.realpathSync(input.projectRoot) || previous.ticket_path !== fs.realpathSync(input.ticketPath) || previous.purpose !== (input.purpose ?? "implement")) fail("actor already owns different Ready work");
        return this.ensureCurrent(previous.execution_id, sessionId, { effect: true });
      }
    }
    const binding = await this.prepare(input);
    const reservation = this.reserve(binding, sessionId, { execution_id: crypto.randomUUID() });
    await this.checkPrepared(binding);
    return this.store.withLock(() => this.commitExecution(this.newExecution(binding, sessionId, reservation), reservation));
  }
  async assignSubagent({ parentSessionId, ...input }) {
    if (this.sessionState(parentSessionId)?.role === "worker") fail("worker cannot delegate its Ready ownership");
    const binding = await this.prepare(input);
    const assignmentId = crypto.randomUUID();
    const reservation = this.reserve(binding, parentSessionId, { assignment_id: assignmentId });
    await this.checkPrepared(binding);
    return this.store.withLock(() => {
      this.assertReservation(binding, reservation);
      const assignment = { ...binding, assignment_id: assignmentId, parent_session_id: parentSessionId, status: "issued", reservation_id: reservation.identity };
      this.store.writeAssignment(assignment);
      this.store.writeActiveTicket(binding.project_root, binding.ticket_path, { ...reservation, state: "assigned" });
      this.store.writeSession(parentSessionId, { assignment_id: assignmentId, role: "parent" });
      return assignment;
    });
  }
  async beginDelegated({ childSessionId, assignmentId, planReviewPath }) {
    const assignment = this.store.readAssignment(assignmentId) ?? fail("unknown assignment");
    if (assignment.status !== "issued") fail("assignment is one-use and no longer issued");
    if (childSessionId === assignment.parent_session_id) fail("parent cannot consume its child assignment");
    const existing = this.sessionState(childSessionId);
    if (existing?.execution_id) fail("child already bound");
    const binding = await this.prepare({ projectRoot: assignment.project_root, ticketPath: assignment.ticket_path, purpose: assignment.purpose, planReviewPath: planReviewPath ?? assignment.plan_binding?.review_path ?? assignment.navigation_binding?.review_path, targetPaths: assignment.verification_target?.target_paths, allowedOutputPaths: assignment.allowed_output_paths });
    if (binding.authority_digest !== assignment.authority_digest || binding.plan_binding?.review_sha256 !== assignment.plan_binding?.review_sha256 || binding.verification_target?.digest !== assignment.verification_target?.digest) fail("PLAN_REVIEW_STALE or authority/target mismatch with assignment");
    await this.checkPrepared(binding);
    return this.store.withLock(() => {
      const current = this.store.readAssignment(assignmentId);
      if (current.status !== "issued") fail("assignment already consumed");
      const reservation = this.store.readActiveTicket(binding.project_root, binding.ticket_path);
      if (this.sessionState(childSessionId)?.execution_id) fail("child concurrently bound another execution");
      if (reservation?.identity !== assignment.reservation_id || reservation.assignment_id !== assignmentId) fail("assignment superseded");
      const state = this.newExecution(binding, childSessionId, reservation, { execution_mode: "SUBAGENT", parent_session_id: assignment.parent_session_id, assignment_id: assignmentId, ...(binding.purpose === "verify" ? { phase: "PAUSED", pause: { kind: "PRE_RUNTIME", summary: null } } : {}) });
      this.store.writeAssignment({ ...current, status: "consumed", execution_id: state.execution_id });
      return this.commitExecution(state, reservation);
    });
  }
  async ensureCurrent(id, actor, { effect = false } = {}) {
    const before = this.assertDispatch(id, actor, effect);
    const authority = await this.checkAuthorityCurrentness(before);
    let reason = authority.current ? null : "AUTHORITY_DRIFT";
    if (!reason && before.plan_binding && !checkPlanCurrentness(before.plan_binding).current) reason = "PLAN_DRIFT";
    if (!reason && before.verification_target && !(await checkVerificationTarget(before.verification_target, { executeArgv: this.executeArgv })).current) reason = "TARGET_DRIFT";
    const current = this.assertDispatch(id, actor, effect);
    if (reason) {
      if (!current.uncertainty) this.update(id, state => { state.phase = "PAUSED"; state.pause = { kind: reason }; });
      if (effect) fail(reason);
    }
    return this.status(id);
  }
  checkpoint(id, actor, kind, summary) {
    if (!["PRE_RUNTIME", "MATERIAL_TURN", "PRE_PROGRESSION"].includes(kind)) fail("invalid checkpoint kind");
    return this.update(id, state => {
      this.assertOwner(state, actor);
      if (state.active_operation || state.uncertainty) fail("settle effect before checkpoint");
      if (kind !== "MATERIAL_TURN" && state.purpose !== "verify") fail("runtime/progression checkpoints are verifier boundaries");
      if (state.phase === "PAUSED" && state.pause?.kind !== kind) fail("cannot overwrite an existing pause");
      state.phase = "PAUSED"; state.pause = { kind, summary };
    });
  }
  async releaseCheckpoint(id, actor, decision, { planReviewPath } = {}) {
    const before = this.assertOwner(this.status(id), actor, { controller: true });
    if (before.phase !== "PAUSED") fail("execution is not paused");
    if (decision === "STOP") return this.block(id, actor, "checkpoint STOP");
    if (!["CONTINUE", "STEER"].includes(decision)) fail("invalid decision");
    if (decision === "STEER") return before;
    if (before.active_operation || before.uncertainty) fail("settle effects before resume");
    if (before.active_operation?.kind === "finalization") fail("recover finalization intent before checkpoint release");
    let refreshed = null;
    if (before.purpose === "implement" && (planReviewPath || ["PLAN_DRIFT", "MATERIAL_TURN", "AUTHORITY_DRIFT"].includes(before.pause.kind))) {
      if (!planReviewPath) fail("PLAN_REVIEW_REQUIRED for material resume");
      refreshed = await this.prepare({ projectRoot: before.project_root, ticketPath: before.ticket_path, purpose: "implement", planReviewPath, allowedOutputPaths: before.allowed_output_paths });
      if (before.pause.kind === "MATERIAL_TURN" && refreshed.plan_binding.review_sha256 === before.plan_binding.review_sha256) fail("PLAN_REVIEW_STALE: material method turn requires updated independent review");
    } else await this.checkPrepared(before);
    return this.store.withLock(() => {
      const current = this.assertOwner(this.status(id), actor, { controller: true });
      if (JSON.stringify(current) !== JSON.stringify(before)) fail("execution changed during resume");
      const next = { ...current, ...refreshed, phase: "ACTIVE", pause: null, progression_released: before.pause.kind === "PRE_PROGRESSION" };
      this.store.writeExecution(next);
      if (next.assignment_id && refreshed) this.store.writeAssignment({ ...this.store.readAssignment(next.assignment_id), ...refreshed });
      return next;
    });
  }
  beginOperation(id, actor, operation) {
    return this.store.withLock(() => {
      const state = this.assertDispatch(id, actor, true);
      state.active_operation = { ...operation, operation_id: operation.operation_id || crypto.randomUUID(), owner: actor };
      state.progression_released = false;
      this.store.writeExecution(state);
      return copy(state.active_operation);
    });
  }
  finishOperation(id, actor, operationId, { uncertain = false, detail = null, result = null } = {}) {
    return this.update(id, state => {
      this.assertOwner(state, actor);
      if (state.active_operation?.operation_id !== operationId || state.active_operation.owner !== actor) fail("late or mismatched operation result");
      if (uncertain) { state.phase = "EFFECT_UNCERTAIN"; state.uncertainty = { operation: state.active_operation, detail }; }
      state.last_operation_result = { operation_id: operationId, result, uncertain };
      state.active_operation = null;
    });
  }
  recoverInterruptedOperation(actor, liveIds = new Set()) {
    const session = this.sessionState(actor);
    if (!session?.execution_id) return null;
    const state = this.status(session.execution_id);
    if (state.session_id !== actor || !state.active_operation || liveIds.has(state.active_operation.operation_id)) return state;
    if (state.active_operation.kind === "finalization") return this.update(state.execution_id, current => { current.phase = "PAUSED"; current.pause = { kind: "RECOVERY_REQUIRED" }; });
    return this.finishOperation(state.execution_id, actor, state.active_operation.operation_id, { uncertain: true, detail: "process resumed without an attributable terminal operation result" });
  }
  resolveMutationUncertainty(id, actor, { operationId, effectSurface, evidenceReference, outcome }) {
    return this.update(id, state => {
      this.assertOwner(state, actor, { controller: true, inactive: true });
      const operation = state.uncertainty?.operation;
      if (!operation || operation.operation_id !== operationId || operation.effect_surface !== effectSurface) fail("exact uncertain operation/effect surface required");
      if (!["applied", "not_applied", "inconclusive"].includes(outcome)) fail("invalid effect outcome");
      const evidence = this.readEvidence(evidenceReference);
      if (evidence.execution_id !== id || evidence.operation_id !== operationId || evidence.effect_surface !== effectSurface || evidence.owner !== actor || evidence.outcome !== outcome || !evidence.readback_reference) fail("recovery evidence does not attribute owner decision to exact effect");
      if (outcome === "inconclusive") return;
      state.effect_resolution = { operation_id: operationId, outcome, evidence_reference: evidenceReference, evidence_sha256: hashBytes(fs.readFileSync(evidenceReference)), adjudication: "explicit recovery-owner decision; not automated effect proof" };
      state.uncertainty = null; state.phase = "PAUSED"; state.pause = { kind: "RECOVERY_REQUIRED" };
    });
  }
  readEvidence(file) {
    if (!file || !fs.statSync(file).isFile()) fail("exact recovery evidence file required");
    return JSON.parse(fs.readFileSync(file, "utf8"));
  }
  recoverAdmission({ actor, projectRoot, ticketPath, reservationId, recoveryEvidenceReference }) {
    const root = fs.realpathSync(projectRoot), ticket = fs.realpathSync(ticketPath);
    const evidence = this.readEvidence(recoveryEvidenceReference);
    return this.store.withLock(() => {
      const slot = this.store.readActiveTicket(root, ticket);
      if (!slot || slot.identity !== reservationId) fail("reservation identity no longer current");
      if (![slot.owner, slot.recovery_owner, this.recoveryOwner].includes(actor)) fail("only designated recovery owner may release reservation");
      if (slot.execution_id && this.store.readExecution(slot.execution_id) || slot.assignment_id && this.store.readAssignment(slot.assignment_id)) fail("reservation has execution/assignment; use its owner closure");
      if (slot.state !== "reserved") fail("not an orphan admission reservation");
      if (evidence.reservation_id !== reservationId || evidence.project_root !== root || evidence.ticket_path !== ticket || evidence.owner !== actor || evidence.admission_disposition !== "terminated_or_withdrawn" || evidence.live_work !== "absent" || evidence.uncertain_effects !== "absent" || !evidence.readback_reference) fail("recovery-owner evidence must establish terminated/withdrawn admission and absence of linked work/effects");
      const released = this.store.clearActiveTicket(root, ticket, reservationId);
      const ownerSession = this.sessionState(slot.owner);
      if (ownerSession?.reservation_id === reservationId) this.store.writeSession(slot.owner, { role: null });
      return { reservation_id: reservationId, released, reason: "explicit designated-owner adjudication of attributed evidence; not host-automated proof" };
    });
  }
  cancelAdmission(actor, assignmentId) {
    if (!assignmentId) return { cancelled: false, reason: "no pre-begin session arming exists" };
    return this.store.withLock(() => {
      const assignment = this.store.readAssignment(assignmentId) ?? fail("unknown assignment");
      if (assignment.parent_session_id !== actor || assignment.status !== "issued") fail("only parent may cancel unconsumed assignment");
      this.store.writeAssignment({ ...assignment, status: "terminal" });
      this.store.clearActiveTicket(assignment.project_root, assignment.ticket_path, assignment.reservation_id);
      return { cancelled: true, assignment_id: assignmentId };
    });
  }
  suspendWorker(id, actor) {
    return this.update(id, state => {
      this.assertOwner(state, actor);
      if (state.execution_mode !== "SUBAGENT") fail("suspension is for delegated replacement");
      if (state.active_operation || state.owned_service || state.uncertainty) fail("stop and settle owned work before suspension");
      state.worker_inactive = true; state.phase = "PAUSED"; state.pause = { kind: "RECOVERY_REQUIRED" };
    });
  }
  async replaceWorker(id, actor, { planReviewPath } = {}) {
    const before = this.assertOwner(this.status(id), actor, { controller: true, inactive: true });
    if (!before.worker_inactive || before.active_operation || before.owned_service || before.uncertainty) fail("old worker must be revoked with all tracked activity settled");
    const binding = await this.prepare({ projectRoot: before.project_root, ticketPath: before.ticket_path, purpose: before.purpose, planReviewPath: planReviewPath ?? before.plan_binding?.review_path ?? before.navigation_binding?.review_path, targetPaths: before.verification_target?.target_paths, allowedOutputPaths: before.allowed_output_paths });
    await this.checkPrepared(before);
    return this.store.withLock(() => {
      const current = this.assertOwner(this.status(id), actor, { controller: true, inactive: true });
      if (JSON.stringify(current) !== JSON.stringify(before)) fail("old worker changed during replacement");
      const assignmentId = crypto.randomUUID(), reservationId = crypto.randomUUID();
      const assignment = { ...binding, assignment_id: assignmentId, parent_session_id: actor, status: "issued", reservation_id: reservationId };
      this.store.writeAssignment({ ...this.store.readAssignment(before.assignment_id), status: "superseded" });
      this.store.writeExecution({ ...current, phase: "BLOCKED", block_reason: "superseded by replacement", worker_inactive: true });
      this.store.writeActiveTicket(before.project_root, before.ticket_path, { identity: reservationId, assignment_id: assignmentId, owner: actor, recovery_owner: this.recoveryOwner || actor, state: "reserved" });
      this.store.writeAssignment(assignment);
      this.store.writeActiveTicket(before.project_root, before.ticket_path, { identity: reservationId, assignment_id: assignmentId, owner: actor, state: "assigned" });
      this.store.writeSession(actor, { role: "parent", assignment_id: assignmentId });
      return assignment;
    });
  }
  recordService(id, actor, handle, operationId) {
    return this.update(id, state => {
      if (!handle.resourceId || !handle.generation || !handle.evidenceReference) fail("service requires host-attributed exact handle");
      this.assertOwner(state, actor);
      if (state.active_operation?.operation_id !== operationId) fail("service event operation mismatch");
      const previous = state.owned_service;
      if (previous && (previous.resourceId !== handle.resourceId || previous.generation !== handle.generation || previous.name !== handle.name)) fail("service generation changed; do not control replacement process");
      state.owned_service = ["stopped", "exited", "failed"].includes(handle.terminalState) ? null : handle;
    });
  }
  closeLocked(state, phase, result) {
    if (state.active_operation || state.owned_service || state.uncertainty) fail("terminal requires owned work/service/effect closure");
    const next = this.store.writeExecution({ ...state, phase, terminal_result: result });
    if (state.assignment_id) this.store.writeAssignment({ ...this.store.readAssignment(state.assignment_id), status: "terminal" });
    this.store.clearActiveTicket(state.project_root, state.ticket_path, state.reservation_id);
    // Keep session tombstones: late owner dispatch must not become unbound general work.
    return next;
  }
  async complete(id, actor) {
    const previous = this.status(id);
    if (previous.phase === "COMPLETE" && previous.purpose === "implement" && previous.session_id === actor) {
      return this.store.withLock(() => {
        const current = this.status(id), slot = this.store.readActiveTicket(current.project_root, current.ticket_path);
        if (current.phase !== "COMPLETE" || current.session_id !== actor || slot && slot.identity !== current.reservation_id) fail("terminal cleanup identity changed");
        if (current.assignment_id) this.store.writeAssignment({ ...this.store.readAssignment(current.assignment_id), status: "terminal" });
        if (slot) this.store.clearActiveTicket(current.project_root, current.ticket_path, current.reservation_id);
        return current;
      });
    }
    await this.ensureCurrent(id, actor, { effect: true });
    return this.store.withLock(() => {
      const state = this.assertDispatch(id, actor, true);
      if (state.purpose !== "implement") fail("verification closes through finalize_verification");
      return this.closeLocked(state, "COMPLETE", { implementation: "COMPLETE" });
    });
  }
  block(id, actor, reason) {
    return this.store.withLock(() => {
      const state = this.status(id);
      this.assertOwner(state, actor, { controller: actor === state.parent_session_id, inactive: true });
      if (state.uncertainty) { state.block_reason = reason; return this.store.writeExecution(state); }
      return this.closeLocked(state, "BLOCKED", { reason });
    });
  }
}
