import crypto from "node:crypto";
import path from "node:path";
import { MAX_OBSERVATION_OUTPUT_BYTES } from "./observation-ledger.js";

function now() {
  return new Date().toISOString();
}

function sameRequestedPath(left, right) {
  return path.resolve(left) === path.resolve(right);
}

function hasAdmissionBinding(session) {
  return Boolean(
    session?.execution_id
    || session?.assignment_id
    || session?.parent_session_id
    || session?.role,
  );
}

function executionFromBinding(binding, fields) {
  const createdAt = now();
  return {
    execution_id: crypto.randomUUID(),
    session_id: fields.sessionId,
    parent_session_id: fields.parentSessionId ?? null,
    assignment_id: fields.assignmentId ?? null,
    execution_mode: fields.executionMode,
    purpose: fields.purpose ?? "implement",
    ...binding,
    mutation_revision: 0,
    phase: fields.phase,
    checkpoint_state: fields.checkpointState ?? null,
    active_operation: null,
    observations: { entries: {} },
    latest_evidence_revision: -1,
    preflight_broad_inventory_used: false,
    implementation_mutation_started: false,
    managed_service: null,
    uncertainty: null,
    last_failed_mutation: null,
    authority_drift: null,
    created_at: createdAt,
    updated_at: createdAt,
  };
}

function assertOwner(state, sessionId) {
  if (state.session_id !== sessionId) throw new Error(`session ${sessionId} does not own Ready execution ${state.execution_id}`);
  if (state.worker_inactive) throw new Error("Ready worker is suspended and cannot perform owner actions");
}

export class ReadyLifecycle {
  constructor({ store, bindAuthority, checkAuthorityCurrentness }) {
    this.store = store;
    this.bindAuthority = bindAuthority;
    this.checkAuthorityCurrentness = checkAuthorityCurrentness;
    this.admissions = new Set();
  }

  // A host invokes this only for an explicit begin/assignment request, never a resource read.
  async admit(sessionId, purpose, execute) {
    if (this.admissions.has(sessionId)) throw new Error("Ready admission is already in progress for this session");
    this.admissions.add(sessionId);
    let token;
    try {
      if (!this.sessionState(sessionId)?.armed) this.armSession(sessionId, purpose);
      token = this.captureAdmission(sessionId, purpose);
      return await execute(token);
    } catch (error) {
      this.store.withLock(() => {
        const current = this.sessionState(sessionId);
        if (token && current?.admission_token === token && !hasAdmissionBinding(current)) {
          this.store.writeSession(sessionId, { ...current, armed: false, purpose: null, admission_token: null, updated_at: now() });
        }
      });
      throw error;
    } finally {
      this.admissions.delete(sessionId);
    }
  }

  armSession(sessionId, purpose = "implement") {
    return this.store.withLock(() => {
      const current = this.store.readSession(sessionId) || {};
      if (current.execution_id && current.purpose && current.purpose !== purpose) {
        throw new Error(`Ready session is already bound for ${current.purpose}`);
      }
      const next = {
        ...current,
        armed: true,
        purpose,
        admission_token: hasAdmissionBinding(current) ? current.admission_token ?? null : crypto.randomUUID(),
        updated_at: now(),
      };
      this.store.writeSession(sessionId, next);
      return next;
    });
  }

  captureAdmission(sessionId, purpose = null) {
    const session = this.store.readSession(sessionId);
    if (!session?.armed) throw new Error("Ready session has no explicit admission request");
    if (purpose && session.purpose && session.purpose !== purpose) {
      throw new Error(`Ready session is armed for ${session.purpose}, not ${purpose}`);
    }
    if (hasAdmissionBinding(session)) return null;
    if (!session.admission_token) throw new Error("Ready session has no current admission identity; begin a new admission");
    return session.admission_token;
  }

  cancelAdmission(sessionId) {
    return this.store.withLock(() => {
      const session = this.store.readSession(sessionId);
      if (!session?.armed) throw new Error("Ready admission cancellation requires the current session to be ARMED");
      if (hasAdmissionBinding(session)) {
        throw new Error("Ready admission cancellation is unavailable after execution, assignment, parent, or worker binding");
      }
      const cancelled = {
        ...session,
        armed: false,
        purpose: null,
        admission_token: null,
        updated_at: now(),
      };
      this.store.writeSession(sessionId, cancelled);
      return cancelled;
    });
  }

  sessionState(sessionId) {
    return this.store.readSession(sessionId);
  }

  recoverInterruptedOperation(sessionId, liveToolCallIds = new Set()) {
    return this.store.withLock(() => {
      const session = this.store.readSession(sessionId);
      if (!session?.execution_id) return null;
      const state = this.store.readExecution(session.execution_id);
      if (!state?.active_operation || state.session_id !== sessionId) return state;
      if (liveToolCallIds.has(state.active_operation.tool_call_id)) return state;
      const operation = state.active_operation;
      if (operation.kind === "mutation") {
        state.phase = "MUTATION_UNCERTAIN";
        state.latest_evidence_revision = -1;
        state.uncertainty = {
          tool_call_id: operation.tool_call_id,
          operation,
          detail: "persisted running mutation was interrupted before a terminal tool result was attributable",
          detected_at: now(),
        };
      } else if (operation.kind === "observation" && operation.observation_digest) {
        const entry = state.observations?.entries?.[operation.observation_digest];
        if (entry?.status === "running") {
          entry.status = "incomplete";
          entry.ended_at = Date.now();
        }
      }
      state.active_operation = null;
      state.updated_at = now();
      this.store.writeExecution(state);
      return state;
    });
  }

  async beginDirect({ sessionId, projectRoot, ticketPath, purpose = null, admissionToken = undefined, prepareBinding = null }) {
    const session = this.store.readSession(sessionId);
    if (!session?.armed) throw new Error("Ready session has no explicit admission request");
    const requestedPurpose = purpose ?? session.purpose ?? "implement";
    const expectedAdmissionToken = admissionToken === undefined ? session.admission_token : admissionToken;
    if (session.purpose && session.purpose !== requestedPurpose) {
      throw new Error(`Ready session is armed for ${session.purpose}, not ${requestedPurpose}`);
    }

    const existing = session.execution_id ? this.store.readExecution(session.execution_id) : null;
    if (
      existing
      && existing.execution_mode === "DIRECT"
      && existing.purpose === requestedPurpose
      && !["COMPLETE", "BLOCKED"].includes(existing.phase)
      && sameRequestedPath(existing.project_root, projectRoot)
      && sameRequestedPath(existing.ticket_path, ticketPath)
    ) {
      if (!["ACTIVE", "AUTHORITY_REVIEW_REQUIRED"].includes(existing.phase)) {
        throw new Error(`DIRECT execution cannot be rebound from phase ${existing.phase}`);
      }
      let binding = await this.bindAuthority({
        projectRoot,
        ticketPath,
        allowedStatuses: requestedPurpose === "verify" ? ["ready", "done"] : ["ready"],
      });
      if (prepareBinding) binding = await prepareBinding(binding);
      const rebound = {
        ...existing,
        ...binding,
        phase: "ACTIVE",
        authority_drift: null,
        updated_at: now(),
      };
      this.store.withLock(() => {
        const current = this.status(existing.execution_id);
        assertOwner(current, sessionId);
        if (current.active_operation || JSON.stringify(current) !== JSON.stringify(existing)) throw new Error("Ready execution changed during admission; retry from current state");
        if (this.sessionState(sessionId)?.execution_id !== current.execution_id) throw new Error("Ready session binding changed during admission");
        this.store.writeExecution(rebound);
        this.store.writeActiveTicket(binding.project_root, binding.ticket_path, {
          identity: rebound.execution_id,
          execution_id: rebound.execution_id,
          session_id: sessionId,
          mode: "DIRECT",
          updated_at: now(),
        });
      });
      return rebound;
    }

    let binding = await this.bindAuthority({
      projectRoot,
      ticketPath,
      allowedStatuses: requestedPurpose === "verify" ? ["ready", "done"] : ["ready"],
    });
    if (prepareBinding) binding = await prepareBinding(binding);
    return this.store.withLock(() => {
      const currentSession = this.#assertAdmissionCurrent(sessionId, requestedPurpose, expectedAdmissionToken);
      const active = this.store.readActiveTicket(binding.project_root, binding.ticket_path);
      if (active) throw new Error(`exact Ticket already has an active Ready execution: ${active.identity}`);
      const state = executionFromBinding(binding, {
        sessionId,
        executionMode: "DIRECT",
        purpose: requestedPurpose,
        phase: "ACTIVE",
      });
      this.store.writeExecution(state);
      this.store.writeSession(sessionId, {
        ...currentSession,
        armed: true,
        purpose: requestedPurpose,
        role: "worker",
        execution_id: state.execution_id,
        updated_at: now(),
      });
      this.store.writeActiveTicket(binding.project_root, binding.ticket_path, {
        identity: state.execution_id,
        execution_id: state.execution_id,
        session_id: sessionId,
        mode: "DIRECT",
        updated_at: now(),
      });
      return state;
    });
  }

  async assignSubagent({ parentSessionId, projectRoot, ticketPath }) {
    const parent = this.store.readSession(parentSessionId);
    if (!parent?.armed) throw new Error("parent session is not ARMED for Ready work");
    if (parent.role === "worker" || parent.parent_session_id) throw new Error("delegated Ready worker may not issue another implementation assignment");
    const expectedAdmissionToken = parent.admission_token;
    const binding = await this.bindAuthority({
      projectRoot,
      ticketPath,
      allowedStatuses: (parent.purpose ?? "implement") === "verify" ? ["ready", "done"] : ["ready"],
    });
    return this.store.withLock(() => {
      const currentParent = this.#assertAdmissionCurrent(parentSessionId, parent.purpose ?? "implement", expectedAdmissionToken);
      const active = this.store.readActiveTicket(binding.project_root, binding.ticket_path);
      if (active) throw new Error(`exact Ticket already has an active Ready execution: ${active.identity}`);
      const assignmentId = crypto.randomUUID();
      const assignment = {
        assignment_id: assignmentId,
        ticket_path: binding.ticket_path,
        ticket_sha256: binding.ticket_sha256,
        project_root: binding.project_root,
        purpose: currentParent.purpose ?? "implement",
        parent_session_id: parentSessionId,
        expected_child_session_id: null,
        status: "issued",
        one_use_nonce: crypto.randomBytes(24).toString("hex"),
        expires_at: null,
        created_at: now(),
        updated_at: now(),
      };
      this.store.writeAssignment(assignment);
      this.store.writeSession(parentSessionId, {
        ...currentParent,
        armed: true,
        purpose: currentParent.purpose ?? "implement",
        role: "parent",
        assignment_id: assignmentId,
        execution_id: null,
        updated_at: now(),
      });
      this.store.writeActiveTicket(binding.project_root, binding.ticket_path, {
        identity: `assignment:${assignmentId}`,
        assignment_id: assignmentId,
        parent_session_id: parentSessionId,
        mode: "SUBAGENT",
        updated_at: now(),
      });
      return assignment;
    });
  }

  suspendWorker(executionId, ownerSessionId, continuationTarget) {
    return this.store.withLock(() => {
      const state = this.status(executionId);
      assertOwner(state, ownerSessionId);
      if (state.execution_mode !== "SUBAGENT") throw new Error("only delegated workers require replacement suspension");
      if (state.active_operation || state.managed_service) throw new Error("stop owned operations and services before suspending");
      if (["COMPLETE", "BLOCKED", "MUTATION_UNCERTAIN"].includes(state.phase)) throw new Error(`cannot suspend from ${state.phase}`);
      state.worker_inactive = true;
      state.continuation_target = continuationTarget;
      state.updated_at = now();
      this.store.writeExecution(state);
      return state;
    });
  }

  replaceWorker(executionId, parentSessionId) {
    return this.store.withLock(() => {
      const state = this.status(executionId);
      if (state.parent_session_id !== parentSessionId || state.execution_mode !== "SUBAGENT") throw new Error("only the bound parent may replace a delegated worker");
      if (!state.worker_inactive || state.active_operation || state.managed_service) throw new Error("prior worker must be suspended with no owned activity before replacement");
      const previous = this.store.readAssignment(state.assignment_id);
      if (previous.status === "superseded") throw new Error("replacement assignment already issued");
      const assignment = {
        ...previous, assignment_id: crypto.randomUUID(), status: "issued", execution_id: null,
        expected_child_session_id: null, resume_execution_id: state.execution_id,
        one_use_nonce: crypto.randomBytes(24).toString("hex"), created_at: now(), updated_at: now(),
      };
      this.store.writeAssignment({ ...previous, status: "superseded", replacement_assignment_id: assignment.assignment_id, updated_at: now() });
      this.store.writeAssignment(assignment);
      const parent = this.sessionState(parentSessionId);
      this.store.writeSession(parentSessionId, { ...parent, assignment_id: assignment.assignment_id, updated_at: now() });
      this.store.writeActiveTicket(state.project_root, state.ticket_path, {
        identity: `assignment:${assignment.assignment_id}`, assignment_id: assignment.assignment_id,
        parent_session_id: parentSessionId, mode: "SUBAGENT", updated_at: now(),
      });
      return assignment;
    });
  }

  async beginDelegated({ childSessionId, assignmentId, admissionToken = undefined, prepareBinding = null }) {
    const child = this.store.readSession(childSessionId);
    if (!child?.armed) throw new Error("child session has no explicit admission request");
    const expectedAdmissionToken = admissionToken === undefined ? child.admission_token : admissionToken;
    const assignment = this.store.readAssignment(assignmentId);
    if (!assignment) throw new Error(`unknown assignment: ${assignmentId}`);
    if (assignment.status !== "issued") throw new Error(`assignment already consumed or terminal: ${assignmentId}`);
    if (child.purpose && child.purpose !== assignment.purpose) {
      throw new Error(`delegated Ready purpose mismatch: assignment=${assignment.purpose}, child=${child.purpose}`);
    }

    let binding = await this.bindAuthority({
      projectRoot: assignment.project_root,
      ticketPath: assignment.ticket_path,
      allowedStatuses: (assignment.purpose ?? "implement") === "verify" ? ["ready", "done"] : ["ready"],
    });
    if (binding.ticket_sha256 !== assignment.ticket_sha256) throw new Error("assignment Ticket authority changed before child consumption");
    if (binding.project_root !== assignment.project_root) throw new Error("assignment Project Root binding changed before child consumption");
    if (prepareBinding) binding = await prepareBinding(binding);
    const resumed = assignment.resume_execution_id ? this.status(assignment.resume_execution_id) : null;
    if (resumed) {
      const currentness = await this.checkAuthorityCurrentness(resumed);
      if (!currentness.current) throw new Error("replacement continuation authority changed");
      if (resumed.purpose === "verify" && resumed.verification_target?.digest !== binding.verification_target?.digest) throw new Error("replacement continuation target changed");
    }

    return this.store.withLock(() => {
      const currentAssignment = this.store.readAssignment(assignmentId);
      const currentChild = this.#assertAdmissionCurrent(childSessionId, currentAssignment?.purpose ?? child.purpose ?? "implement", expectedAdmissionToken);
      if (!currentAssignment || currentAssignment.status !== "issued") throw new Error(`assignment already consumed or terminal: ${assignmentId}`);
      const active = this.store.readActiveTicket(binding.project_root, binding.ticket_path);
      if (!active || active.identity !== `assignment:${assignmentId}`) {
        throw new Error("assignment no longer owns the exact Ticket execution slot");
      }
      if (resumed) {
        const previous = this.status(resumed.execution_id);
        if (!previous.worker_inactive || previous.active_operation || previous.managed_service || JSON.stringify(previous) !== JSON.stringify(resumed)) throw new Error("prior worker changed during replacement admission");
      }
      const state = resumed ? {
        ...resumed, ...binding, session_id: childSessionId, assignment_id: assignmentId,
        worker_inactive: false, phase: "PRE_ACTION_PENDING", latest_evidence_revision: -1,
        superseded_session_ids: [...(resumed.superseded_session_ids ?? []), resumed.session_id],
        previous_checkpoint_state: resumed.checkpoint_state,
        checkpoint_state: { kind: "PRE_ACTION", status: "NOT_REPORTED", decision: null }, updated_at: now(),
      } : executionFromBinding(binding, {
        sessionId: childSessionId,
        parentSessionId: currentAssignment.parent_session_id,
        assignmentId,
        executionMode: "SUBAGENT",
        purpose: currentAssignment.purpose ?? "implement",
        phase: "PRE_ACTION_PENDING",
        checkpointState: { kind: "PRE_ACTION", status: "NOT_REPORTED", decision: null },
      });
      this.store.writeExecution(state);
      this.store.writeAssignment({
        ...currentAssignment,
        expected_child_session_id: childSessionId,
        status: "consumed",
        execution_id: state.execution_id,
        updated_at: now(),
      });
      this.store.writeSession(childSessionId, {
        ...currentChild,
        armed: true,
        purpose: currentAssignment.purpose ?? "implement",
        role: "worker",
        execution_id: state.execution_id,
        assignment_id: assignmentId,
        parent_session_id: currentAssignment.parent_session_id,
        updated_at: now(),
      });
      const parent = this.store.readSession(currentAssignment.parent_session_id) || {};
      this.store.writeSession(currentAssignment.parent_session_id, {
        ...parent,
        armed: true,
        purpose: currentAssignment.purpose ?? "implement",
        role: "parent",
        execution_id: state.execution_id,
        assignment_id: assignmentId,
        updated_at: now(),
      });
      this.store.writeActiveTicket(binding.project_root, binding.ticket_path, {
        identity: state.execution_id,
        execution_id: state.execution_id,
        session_id: childSessionId,
        parent_session_id: currentAssignment.parent_session_id,
        mode: "SUBAGENT",
        updated_at: now(),
      });
      return state;
    });
  }

  status(executionId) {
    const state = this.store.readExecution(executionId);
    if (!state) throw new Error(`unknown Ready execution: ${executionId}`);
    return state;
  }


  markTargetDrift(executionId, changed) {
    return this.store.withLock(() => {
      const state = this.status(executionId);
      if (state.purpose !== "verify") throw new Error("target drift is only valid for verify purpose");
      state.target_drift = { changed: [...changed], detected_at: now() };
      state.phase = "TARGET_DRIFT";
      state.active_operation = null;
      state.updated_at = now();
      this.store.writeExecution(state);
      return state;
    });
  }

  beginVerificationFinalization(executionId, ownerSessionId, verdict, finalizationId) {
    if (!new Set(["VERIFIED", "FAILED", "INCONCLUSIVE"]).has(verdict)) {
      throw new Error(`invalid verification verdict: ${verdict}`);
    }
    if (!finalizationId) throw new Error("verification finalization requires an operation id");
    return this.store.withLock(() => {
      const state = this.status(executionId);
      assertOwner(state, ownerSessionId);
      if (state.purpose !== "verify") throw new Error("finalize_verification requires verify purpose");
      if (state.active_operation) throw new Error("verification cannot finalize while a guarded operation is active");
      if (verdict === "VERIFIED" && state.phase === "TARGET_DRIFT") throw new Error("VERIFIED blocked by target drift");
      if (verdict === "VERIFIED" && state.phase !== "ACTIVE") throw new Error(`VERIFIED cannot finalize from phase ${state.phase}`);
      if (["COMPLETE", "BLOCKED", "MUTATION_UNCERTAIN"].includes(state.phase)) throw new Error(`verification cannot finalize from phase ${state.phase}`);
      state.active_operation = {
        tool_call_id: finalizationId,
        kind: "verification_finalize",
        verdict,
        started_at: now(),
      };
      state.updated_at = now();
      this.store.writeExecution(state);
      return state;
    });
  }

  cancelVerificationFinalization(executionId, ownerSessionId, finalizationId) {
    return this.store.withLock(() => {
      const state = this.status(executionId);
      assertOwner(state, ownerSessionId);
      if (
        state.active_operation?.kind === "verification_finalize"
        && state.active_operation.tool_call_id === finalizationId
      ) {
        state.active_operation = null;
        state.updated_at = now();
        this.store.writeExecution(state);
      }
      return state;
    });
  }

  verificationFinalizationState(executionId, ownerSessionId, verdict, finalizationId) {
    return this.store.withLock(() => {
      const state = this.status(executionId);
      assertOwner(state, ownerSessionId);
      if (state.purpose !== "verify") throw new Error("finalize_verification requires verify purpose");
      if (
        !finalizationId
        || state.active_operation?.kind !== "verification_finalize"
        || state.active_operation.tool_call_id !== finalizationId
        || state.active_operation.verdict !== verdict
      ) {
        throw new Error("verification finalization reservation is not active");
      }
      if (verdict === "VERIFIED" && state.phase !== "ACTIVE") throw new Error(`VERIFIED cannot finalize from phase ${state.phase}`);
      if (["COMPLETE", "BLOCKED", "MUTATION_UNCERTAIN"].includes(state.phase)) throw new Error(`verification cannot finalize from phase ${state.phase}`);
      return state;
    });
  }

  finalizeVerification(executionId, ownerSessionId, { verdict, progression, finalizationId }) {
    if (!new Set(["VERIFIED", "FAILED", "INCONCLUSIVE"]).has(verdict)) {
      throw new Error(`invalid verification verdict: ${verdict}`);
    }
    if (!progression || typeof progression.progression !== "string") {
      throw new Error("verification finalization requires a valid progression result");
    }
    return this.store.withLock(() => {
      const state = this.status(executionId);
      assertOwner(state, ownerSessionId);
      if (state.purpose !== "verify") throw new Error("finalize_verification requires verify purpose");
      if (
        !finalizationId
        || state.active_operation?.kind !== "verification_finalize"
        || state.active_operation.tool_call_id !== finalizationId
        || state.active_operation.verdict !== verdict
      ) {
        throw new Error("verification finalization reservation is not active");
      }
      if (verdict === "VERIFIED" && state.phase !== "ACTIVE") throw new Error(`VERIFIED cannot finalize from phase ${state.phase}`);
      if (["COMPLETE", "BLOCKED", "MUTATION_UNCERTAIN"].includes(state.phase)) throw new Error(`verification cannot finalize from phase ${state.phase}`);
      if (state.managed_service) throw new Error("stop the managed service before terminal closure");
      state.active_operation = null;
      state.phase = "COMPLETE";
      state.verification_verdict = verdict;
      state.ticket_progression = progression.progression;
      state.updated_at = now();
      this.store.writeExecution(state);
      this.#releaseActiveTicket(state);
      this.#deactivateSessions(state);
      const assignment = state.assignment_id ? this.store.readAssignment(state.assignment_id) : null;
      if (assignment) this.store.writeAssignment({ ...assignment, status: "terminal", updated_at: now() });
      return state;
    });
  }

  checkpointPreAction(executionId, childSessionId, summary = null) {
    return this.store.withLock(() => {
      const state = this.status(executionId);
      assertOwner(state, childSessionId);
      if (state.execution_mode !== "SUBAGENT" || state.phase !== "PRE_ACTION_PENDING") {
        throw new Error(`PRE_ACTION checkpoint is not valid in phase ${state.phase}`);
      }
      state.checkpoint_state = { kind: "PRE_ACTION", status: "PENDING", decision: null, summary, reported_at: now() };
      state.updated_at = now();
      this.store.writeExecution(state);
      const assignment = this.store.readAssignment(state.assignment_id);
      if (assignment) this.store.writeAssignment({ ...assignment, status: "pre_action", updated_at: now() });
      return state;
    });
  }

  checkpointMaterialTurn(executionId, childSessionId, summary = null) {
    return this.store.withLock(() => {
      const state = this.status(executionId);
      assertOwner(state, childSessionId);
      if (state.execution_mode !== "SUBAGENT" || !["ACTIVE", "MATERIAL_TURN_REQUIRED", "MATERIAL_TURN_PENDING"].includes(state.phase)) {
        throw new Error(`MATERIAL_TURN checkpoint is not valid in phase ${state.phase}`);
      }
      if (state.active_operation) throw new Error("cannot checkpoint while a guarded operation is active");
      state.phase = "MATERIAL_TURN_PENDING";
      state.checkpoint_state = { kind: "MATERIAL_TURN", status: "PENDING", decision: null, summary, reported_at: now() };
      state.updated_at = now();
      this.store.writeExecution(state);
      return state;
    });
  }

  releaseCheckpoint(executionId, parentSessionId, decision) {
    if (!new Set(["CONTINUE", "STEER", "STOP"]).has(decision)) throw new Error(`invalid checkpoint decision: ${decision}`);
    return this.store.withLock(() => {
      const state = this.status(executionId);
      if (state.execution_mode !== "SUBAGENT" || state.parent_session_id !== parentSessionId) {
        throw new Error("only the bound parent session may release a SUBAGENT checkpoint");
      }
      if (!state.checkpoint_state || state.checkpoint_state.status !== "PENDING") throw new Error("no pending checkpoint to release");
      if (state.active_operation) throw new Error("cannot release checkpoint while a guarded operation is active");
      if (decision === "STOP" && state.managed_service) throw new Error("stop the managed service before terminal closure");
      const kind = state.checkpoint_state.kind;
      state.checkpoint_state = { ...state.checkpoint_state, status: "RELEASED", decision, released_at: now() };
      if (decision === "STOP") {
        state.phase = state.purpose === "verify" ? state.phase : "BLOCKED";
      } else if (decision === "STEER") {
        state.phase = kind === "PRE_ACTION" ? "PRE_ACTION_PENDING" : "MATERIAL_TURN_PENDING";
      } else {
        state.phase = "ACTIVE";
        state.authority_drift = null;
      }
      state.updated_at = now();
      this.store.writeExecution(state);
      const assignment = this.store.readAssignment(state.assignment_id);
      if (assignment) {
        this.store.writeAssignment({
          ...assignment,
          status: decision === "STOP" && state.purpose !== "verify" ? "terminal" : state.phase === "ACTIVE" ? "active" : assignment.status,
          updated_at: now(),
        });
      }
      if (decision === "STOP" && state.purpose !== "verify") {
        this.#releaseActiveTicket(state);
        this.#deactivateSessions(state);
      }
      return state;
    });
  }

  beginOperation(
    executionId,
    { toolCallId, kind, observationDigest = null, mutationSnapshot = null, mutationDigest = null },
  ) {
    return this.store.withLock(() => {
      const state = this.status(executionId);
      if (["COMPLETE", "BLOCKED", "MUTATION_UNCERTAIN", "TARGET_DRIFT"].includes(state.phase)) throw new Error(`Ready execution is not runnable in phase ${state.phase}`);
      if (state.active_operation) throw new Error(`Ready execution already has an active guarded operation: ${state.active_operation.tool_call_id}`);
      if (kind === "mutation" && (state.purpose ?? "implement") === "implement") {
        state.implementation_mutation_started = true;
      }
      state.active_operation = {
        tool_call_id: toolCallId,
        kind,
        observation_digest: observationDigest,
        mutation_snapshot: mutationSnapshot,
        mutation_digest: mutationDigest,
        started_at: now(),
      };
      state.updated_at = now();
      this.store.writeExecution(state);
      return state.active_operation;
    });
  }

  finishOperation(
    executionId,
    toolCallId,
    { mutationApplied = false, commandOutputBytes = null, failureClassification = null, failureDetail = null } = {},
  ) {
    return this.store.withLock(() => {
      const state = this.status(executionId);
      if (!state.active_operation || state.active_operation.tool_call_id !== toolCallId) {
        throw new Error(`toolCallId ${toolCallId} does not match the active Ready operation`);
      }
      const operation = state.active_operation;
      if (mutationApplied) {
        state.mutation_revision = Number(state.mutation_revision ?? 0) + 1;
        state.last_failed_mutation = null;
        if (Number.isSafeInteger(commandOutputBytes) && commandOutputBytes >= 0 && commandOutputBytes <= MAX_OBSERVATION_OUTPUT_BYTES) {
          state.latest_evidence_revision = state.mutation_revision;
        }
      }
      if (operation.kind === "mutation" && failureClassification) {
        state.last_failed_mutation = {
          mutation_revision: Number(state.mutation_revision ?? 0),
          mutation_digest: operation.mutation_digest,
          error_classification: failureClassification,
          detail: failureDetail,
          failed_at: now(),
        };
      }
      state.active_operation = null;
      state.updated_at = now();
      this.store.writeExecution(state);
      return state;
    });
  }

  markMutationUncertain(executionId, toolCallId, detail) {
    return this.store.withLock(() => {
      const state = this.status(executionId);
      if (!state.active_operation || state.active_operation.tool_call_id !== toolCallId) {
        throw new Error(`toolCallId ${toolCallId} does not match the active Ready mutation`);
      }
      state.phase = "MUTATION_UNCERTAIN";
      state.latest_evidence_revision = -1;
      state.uncertainty = {
        tool_call_id: toolCallId,
        operation: state.active_operation,
        detail,
        detected_at: now(),
      };
      state.active_operation = null;
      state.updated_at = now();
      this.store.writeExecution(state);
      return state;
    });
  }

  resolveMutationUncertainty(executionId, ownerSessionId, outcome) {
    if (!new Set(["applied", "not_applied", "inconclusive"]).has(outcome)) throw new Error(`invalid mutation uncertainty outcome: ${outcome}`);
    return this.store.withLock(() => {
      const state = this.status(executionId);
      assertOwner(state, ownerSessionId);
      if (state.phase !== "MUTATION_UNCERTAIN" || !state.uncertainty) throw new Error("Ready execution is not mutation-uncertain");
      if (outcome === "inconclusive") return state;
      if (outcome === "applied") state.mutation_revision = Number(state.mutation_revision ?? 0) + 1;
      state.phase = "ACTIVE";
      state.uncertainty = { ...state.uncertainty, resolution: outcome, resolved_at: now() };
      state.updated_at = now();
      this.store.writeExecution(state);
      return state;
    });
  }

  noteCurrentEvidence(executionId, revision) {
    return this.store.withLock(() => {
      const state = this.status(executionId);
      state.latest_evidence_revision = Math.max(Number(state.latest_evidence_revision ?? -1), Number(revision));
      state.updated_at = now();
      this.store.writeExecution(state);
      return state;
    });
  }

  markAuthorityDrift(executionId, changed) {
    return this.store.withLock(() => {
      const state = this.status(executionId);
      state.authority_drift = { changed, detected_at: now() };
      state.phase = state.execution_mode === "SUBAGENT" ? "MATERIAL_TURN_REQUIRED" : "AUTHORITY_REVIEW_REQUIRED";
      state.updated_at = now();
      this.store.writeExecution(state);
      return state;
    });
  }

  async refreshDelegatedAuthority(executionId, childSessionId) {
    const state = this.status(executionId);
    assertOwner(state, childSessionId);
    if (state.execution_mode !== "SUBAGENT") throw new Error("refreshDelegatedAuthority requires SUBAGENT execution");
    const binding = await this.bindAuthority({
      projectRoot: state.project_root,
      ticketPath: state.ticket_path,
      allowedStatuses: state.purpose === "verify" ? ["ready", "done"] : ["ready"],
    });
    const refreshed = { ...state, ...binding, authority_drift: null, updated_at: now() };
    this.store.withLock(() => this.store.writeExecution(refreshed));
    return refreshed;
  }

  async complete(executionId, ownerSessionId) {
    const state = this.status(executionId);
    assertOwner(state, ownerSessionId);
    if (state.phase !== "ACTIVE") throw new Error(`Ready execution cannot complete from phase ${state.phase}`);
    if (state.active_operation) throw new Error("Ready execution cannot complete while a guarded operation is active");
    if (Number(state.latest_evidence_revision ?? -1) !== Number(state.mutation_revision ?? 0)) {
      throw new Error("Ready runtime COMPLETE requires a successful observation in the current mutation revision; this gate does not establish product self-check sufficiency");
    }
    const currentness = await this.checkAuthorityCurrentness(state);
    if (!currentness.current) {
      this.markAuthorityDrift(executionId, currentness.changed);
      throw new Error("authority artifacts changed; current meaning must be re-confirmed before COMPLETE");
    }
    return this.store.withLock(() => {
      const current = this.status(executionId);
      assertOwner(current, ownerSessionId);
      if (current.phase !== "ACTIVE" || current.active_operation || current.mutation_revision !== state.mutation_revision || current.latest_evidence_revision !== current.mutation_revision) throw new Error("Ready execution changed during completion; current evidence is required");
      if (current.managed_service) throw new Error("stop the managed service before terminal closure");
      current.phase = "COMPLETE";
      current.updated_at = now();
      this.store.writeExecution(current);
      this.#releaseActiveTicket(current);
      this.#deactivateSessions(current);
      const assignment = current.assignment_id ? this.store.readAssignment(current.assignment_id) : null;
      if (assignment) this.store.writeAssignment({ ...assignment, status: "terminal", updated_at: now() });
      return current;
    });
  }

  blockAssignment(assignmentId, parentSessionId, reason) {
    return this.store.withLock(() => {
      const assignment = this.store.readAssignment(assignmentId);
      if (!assignment) throw new Error(`unknown assignment: ${assignmentId}`);
      if (assignment.parent_session_id !== parentSessionId) throw new Error("only the bound parent may close an issued assignment");
      if (assignment.execution_id) throw new Error("assignment already has a delegated execution; block that execution instead");
      if (assignment.status === "terminal") return assignment;
      if (assignment.status !== "issued") throw new Error(`assignment cannot be closed from status ${assignment.status}`);
      const terminal = { ...assignment, status: "terminal", block_reason: reason, updated_at: now() };
      if (assignment.resume_execution_id) {
        const suspended = this.status(assignment.resume_execution_id);
        suspended.phase = "BLOCKED";
        suspended.block_reason = reason;
        suspended.updated_at = now();
        this.store.writeExecution(suspended);
        this.#deactivateSessions(suspended);
      }
      this.store.writeAssignment(terminal);
      this.store.clearActiveTicket(assignment.project_root, assignment.ticket_path, `assignment:${assignmentId}`);
      const parent = this.store.readSession(parentSessionId);
      if (parent) {
        this.store.writeSession(parentSessionId, {
          ...parent,
          armed: false,
          purpose: null,
          admission_token: null,
          role: null,
          assignment_id: null,
          execution_id: null,
          updated_at: now(),
        });
      }
      return terminal;
    });
  }

  block(executionId, ownerSessionId, reason) {
    return this.store.withLock(() => {
      const state = this.status(executionId);
      if (state.session_id !== ownerSessionId && state.parent_session_id !== ownerSessionId) {
        throw new Error("only the bound worker or parent may block this Ready execution");
      }
      if (state.phase === "COMPLETE") throw new Error("completed Ready execution cannot be blocked");
      if (state.active_operation) throw new Error("stop or recover the active operation before blocking");
      if (state.managed_service) throw new Error("stop the managed service before terminal closure");
      state.phase = "BLOCKED";
      state.block_reason = reason;
      state.active_operation = null;
      state.updated_at = now();
      this.store.writeExecution(state);
      this.#releaseActiveTicket(state);
      this.#deactivateSessions(state);
      const assignment = state.assignment_id ? this.store.readAssignment(state.assignment_id) : null;
      if (assignment) this.store.writeAssignment({ ...assignment, status: "terminal", updated_at: now() });
      return state;
    });
  }

  #assertAdmissionCurrent(sessionId, purpose, expectedToken) {
    const session = this.store.readSession(sessionId);
    if (
      !session?.armed
      || hasAdmissionBinding(session)
      || !expectedToken
      || session.admission_token !== expectedToken
      || (session.purpose && session.purpose !== purpose)
    ) {
      throw new Error("Ready admission is no longer current; begin a new admission");
    }
    return session;
  }

  #deactivateSessions(state) {
    for (const sid of new Set([state.session_id, state.parent_session_id, ...(state.superseded_session_ids ?? [])].filter(Boolean))) {
      const session = this.store.readSession(sid);
      if (!session || session.execution_id !== state.execution_id) continue;
      this.store.writeSession(sid, {
        ...session, armed: false, purpose: null, role: null, execution_id: null,
        assignment_id: null, parent_session_id: null, admission_token: null, updated_at: now(),
      });
    }
  }

  #releaseActiveTicket(state) {
    const active = this.store.readActiveTicket(state.project_root, state.ticket_path);
    const pending = active?.assignment_id ? this.store.readAssignment(active.assignment_id) : null;
    if (pending?.resume_execution_id === state.execution_id) {
      this.store.writeAssignment({ ...pending, status: "terminal", updated_at: now() });
      this.store.clearActiveTicket(state.project_root, state.ticket_path, active.identity);
    } else this.store.clearActiveTicket(state.project_root, state.ticket_path, state.execution_id);
  }
}
