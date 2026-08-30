import crypto from "node:crypto";
import path from "node:path";

function now() {
  return new Date().toISOString();
}

function sameRequestedPath(left, right) {
  return path.resolve(left) === path.resolve(right);
}

function hasStoredEvidenceFingerprint(item) {
  return item?.fingerprint?.payload
    && typeof item.fingerprint.payload === "object"
    && typeof item.fingerprint.sha256 === "string"
    && /^[a-f0-9]{64}$/.test(item.fingerprint.sha256);
}

function executionFromBinding(binding, fields) {
  const createdAt = now();
  return {
    execution_id: crypto.randomUUID(),
    session_id: fields.sessionId,
    parent_session_id: fields.parentSessionId ?? null,
    assignment_id: fields.assignmentId ?? null,
    execution_mode: fields.executionMode,
    ...binding,
    mutation_revision: 0,
    phase: fields.phase,
    checkpoint_state: fields.checkpointState ?? null,
    active_operation: null,
    observations: { entries: {} },
    latest_evidence_revision: -1,
    preflight_broad_inventory_used: false,
    managed_service: null,
    uncertainty: null,
    last_failed_mutation: null,
    authority_drift: null,
    zero_mock: {
      violations: [],
      touched_paths: [],
      self_check_paths: [],
      observed_paths: [],
      observed_evidence: {},
      acceptance_provenance: [],
      inspection_provenance: [],
    },
    created_at: createdAt,
    updated_at: createdAt,
  };
}

function assertOwner(state, sessionId) {
  if (state.session_id !== sessionId) throw new Error(`session ${sessionId} does not own Ready execution ${state.execution_id}`);
}

export class ReadyLifecycle {
  constructor({ store, bindAuthority, checkAuthorityCurrentness }) {
    this.store = store;
    this.bindAuthority = bindAuthority;
    this.checkAuthorityCurrentness = checkAuthorityCurrentness;
  }

  armSession(sessionId, armedMode = "IMPLEMENT") {
    return this.store.withLock(() => {
      const current = this.store.readSession(sessionId) || {};
      const next = { ...current, armed: true, armed_mode: armedMode, updated_at: now() };
      this.store.writeSession(sessionId, next);
      return next;
    });
  }

  sessionState(sessionId) {
    return this.store.readSession(sessionId);
  }

  recoverInterruptedOperation(sessionId) {
    return this.store.withLock(() => {
      const session = this.store.readSession(sessionId);
      if (!session?.execution_id) return null;
      const state = this.store.readExecution(session.execution_id);
      if (!state?.active_operation) return state;
      const operation = state.active_operation;
      if (operation.kind === "mutation") {
        state.phase = "MUTATION_UNCERTAIN";
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

  async beginDirect({ sessionId, projectRoot, ticketPath }) {
    const session = this.store.readSession(sessionId);
    if (!session?.armed || session.armed_mode === "VERIFY") throw new Error("ready-ticket-implement session is not ARMED; read the Skill before begin_direct");

    const existing = session.execution_id ? this.store.readExecution(session.execution_id) : null;
    if (
      existing
      && existing.execution_mode === "DIRECT"
      && !["COMPLETE", "BLOCKED"].includes(existing.phase)
      && sameRequestedPath(existing.project_root, projectRoot)
      && sameRequestedPath(existing.ticket_path, ticketPath)
    ) {
      if (!["ACTIVE", "AUTHORITY_REVIEW_REQUIRED"].includes(existing.phase)) {
        throw new Error(`DIRECT execution cannot be rebound from phase ${existing.phase}`);
      }
      const binding = await this.bindAuthority({ projectRoot, ticketPath });
      const rebound = {
        ...existing,
        ...binding,
        phase: "ACTIVE",
        authority_drift: null,
        updated_at: now(),
      };
      this.store.withLock(() => {
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

    const binding = await this.bindAuthority({ projectRoot, ticketPath });
    return this.store.withLock(() => {
      const active = this.store.readActiveTicket(binding.project_root, binding.ticket_path);
      if (active) throw new Error(`exact Ticket already has an active Ready execution: ${active.identity}`);
      const state = executionFromBinding(binding, {
        sessionId,
        executionMode: "DIRECT",
        phase: "ACTIVE",
      });
      this.store.writeExecution(state);
      this.store.writeSession(sessionId, {
        ...session,
        armed: true,
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

  async beginVerification({ sessionId, projectRoot, ticketPath }) {
    const session = this.store.readSession(sessionId);
    if (!session?.armed || session.armed_mode !== "VERIFY") {
      throw new Error("ready-ticket-verify session is not ARMED; read the verifier Skill before begin");
    }
    const existing = session.execution_id ? this.store.readExecution(session.execution_id) : null;
    if (
      existing
      && existing.execution_mode === "VERIFY"
      && ["VERIFY_ACTIVE", "VERIFY_AUTHORITY_REVIEW_REQUIRED"].includes(existing.phase)
      && sameRequestedPath(existing.project_root, projectRoot)
      && sameRequestedPath(existing.ticket_path, ticketPath)
    ) {
      const binding = await this.bindAuthority({ projectRoot, ticketPath });
      const rebound = { ...existing, ...binding, phase: "VERIFY_ACTIVE", authority_drift: null, updated_at: now() };
      this.store.withLock(() => {
        this.store.writeExecution(rebound);
        this.store.writeActiveTicket(binding.project_root, binding.ticket_path, {
          identity: rebound.execution_id, execution_id: rebound.execution_id, session_id: sessionId, mode: "VERIFY", updated_at: now(),
        });
      });
      return rebound;
    }
    const binding = await this.bindAuthority({ projectRoot, ticketPath });
    return this.store.withLock(() => {
      const active = this.store.readActiveTicket(binding.project_root, binding.ticket_path);
      if (active) throw new Error(`exact Ticket already has an active Ready execution: ${active.identity}`);
      const state = executionFromBinding(binding, {
        sessionId,
        executionMode: "VERIFY",
        phase: "VERIFY_ACTIVE",
      });
      this.store.writeExecution(state);
      this.store.writeSession(sessionId, {
        ...session,
        armed: true,
        armed_mode: "VERIFY",
        role: "verifier",
        execution_id: state.execution_id,
        updated_at: now(),
      });
      this.store.writeActiveTicket(binding.project_root, binding.ticket_path, {
        identity: state.execution_id,
        execution_id: state.execution_id,
        session_id: sessionId,
        mode: "VERIFY",
        updated_at: now(),
      });
      return state;
    });
  }

  async assignSubagent({ parentSessionId, projectRoot, ticketPath }) {
    const parent = this.store.readSession(parentSessionId);
    if (!parent?.armed) throw new Error("parent session is not ARMED for ready-ticket-implement");
    if (parent.role === "worker" || parent.parent_session_id) throw new Error("delegated Ready worker may not issue another implementation assignment");
    const binding = await this.bindAuthority({ projectRoot, ticketPath });
    return this.store.withLock(() => {
      const active = this.store.readActiveTicket(binding.project_root, binding.ticket_path);
      if (active) throw new Error(`exact Ticket already has an active Ready execution: ${active.identity}`);
      const assignmentId = crypto.randomUUID();
      const assignment = {
        assignment_id: assignmentId,
        ticket_path: binding.ticket_path,
        ticket_sha256: binding.ticket_sha256,
        project_root: binding.project_root,
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
        ...parent,
        armed: true,
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

  async beginDelegated({ childSessionId, assignmentId }) {
    const child = this.store.readSession(childSessionId);
    if (!child?.armed) throw new Error("child session is not ARMED; read ready-ticket-implement before begin_delegated");
    const assignment = this.store.readAssignment(assignmentId);
    if (!assignment) throw new Error(`unknown assignment: ${assignmentId}`);
    if (assignment.status !== "issued") throw new Error(`assignment already consumed or terminal: ${assignmentId}`);

    const binding = await this.bindAuthority({ projectRoot: assignment.project_root, ticketPath: assignment.ticket_path });
    if (binding.ticket_sha256 !== assignment.ticket_sha256) throw new Error("assignment Ticket authority changed before child consumption");
    if (binding.project_root !== assignment.project_root) throw new Error("assignment Project Root binding changed before child consumption");

    return this.store.withLock(() => {
      const currentAssignment = this.store.readAssignment(assignmentId);
      if (!currentAssignment || currentAssignment.status !== "issued") throw new Error(`assignment already consumed or terminal: ${assignmentId}`);
      const active = this.store.readActiveTicket(binding.project_root, binding.ticket_path);
      if (!active || active.identity !== `assignment:${assignmentId}`) {
        throw new Error("assignment no longer owns the exact Ticket execution slot");
      }
      const state = executionFromBinding(binding, {
        sessionId: childSessionId,
        parentSessionId: currentAssignment.parent_session_id,
        assignmentId,
        executionMode: "SUBAGENT",
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
        ...child,
        armed: true,
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
      const kind = state.checkpoint_state.kind;
      state.checkpoint_state = { ...state.checkpoint_state, status: "RELEASED", decision, released_at: now() };
      if (decision === "STOP") {
        state.phase = "BLOCKED";
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
          status: decision === "STOP" ? "terminal" : state.phase === "ACTIVE" ? "active" : assignment.status,
          updated_at: now(),
        });
      }
      if (decision === "STOP") {
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
      if (["COMPLETE", "BLOCKED", "MUTATION_UNCERTAIN"].includes(state.phase)) throw new Error(`Ready execution is not runnable in phase ${state.phase}`);
      if (state.active_operation) throw new Error(`Ready execution already has an active guarded operation: ${state.active_operation.tool_call_id}`);
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
    { mutationApplied = false, failureClassification = null, failureDetail = null } = {},
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
      } else if (operation.kind === "mutation" && failureClassification) {
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

  resolveMutationUncertainty(executionId, outcome) {
    if (!new Set(["applied", "not_applied", "inconclusive"]).has(outcome)) throw new Error(`invalid mutation uncertainty outcome: ${outcome}`);
    return this.store.withLock(() => {
      const state = this.status(executionId);
      if (state.phase !== "MUTATION_UNCERTAIN" || !state.uncertainty) throw new Error("Ready execution is not mutation-uncertain");
      if (outcome === "inconclusive") return state;
      if (outcome === "applied") state.mutation_revision = Number(state.mutation_revision ?? 0) + 1;
      if (state.execution_mode === "VERIFY") {
        state.phase = "VERIFY_VERIFIED_ADMITTED";
        if (outcome === "applied") state.verification_progression_used = true;
      } else {
        state.phase = "ACTIVE";
      }
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
      state.phase = state.execution_mode === "SUBAGENT"
        ? "MATERIAL_TURN_REQUIRED"
        : state.execution_mode === "VERIFY"
          ? "VERIFY_AUTHORITY_REVIEW_REQUIRED"
          : "AUTHORITY_REVIEW_REQUIRED";
      state.updated_at = now();
      this.store.writeExecution(state);
      return state;
    });
  }

  async refreshDelegatedAuthority(executionId, childSessionId) {
    const state = this.status(executionId);
    assertOwner(state, childSessionId);
    if (state.execution_mode !== "SUBAGENT") throw new Error("refreshDelegatedAuthority requires SUBAGENT execution");
    const binding = await this.bindAuthority({ projectRoot: state.project_root, ticketPath: state.ticket_path });
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
      throw new Error("Ready execution requires successful current-revision self-check evidence before COMPLETE");
    }
    const currentness = await this.checkAuthorityCurrentness(state);
    if (!currentness.current) {
      this.markAuthorityDrift(executionId, currentness.changed);
      throw new Error("authority artifacts changed; current meaning must be re-confirmed before COMPLETE");
    }
    return this.store.withLock(() => {
      const current = this.status(executionId);
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

  async admitVerification(executionId, ownerSessionId, verdict, { currentEvidenceVerified = false } = {}) {
    if (!new Set(["VERIFIED", "FAILED", "INCONCLUSIVE"]).has(verdict)) {
      throw new Error(`invalid verification verdict: ${verdict}`);
    }
    const state = this.status(executionId);
    assertOwner(state, ownerSessionId);
    if (state.execution_mode !== "VERIFY" || state.phase !== "VERIFY_ACTIVE") {
      throw new Error(`verification admission is not available in phase ${state.phase}`);
    }
    if (verdict === "VERIFIED") {
      if ((state.zero_mock?.violations || []).length > 0) {
        throw new Error("mock-tainted evidence cannot be admitted for VERIFIED");
      }
      const cleanAcceptance = (state.zero_mock?.acceptance_provenance || []).some(
        item => item.status === "PASSED"
          && item.mock_taint === false
          && item.authoritative_readback?.available === true
          && hasStoredEvidenceFingerprint(item),
      );
      const cleanInspection = (state.zero_mock?.inspection_provenance || []).some(
        item => item.status === "PASSED"
          && item.mock_taint === false
          && item.authoritative_readback?.available === true
          && hasStoredEvidenceFingerprint(item),
      );
      if (!currentEvidenceVerified || (!cleanAcceptance && !cleanInspection)) {
        throw new Error("VERIFIED requires current Zero-Mock acceptance or direct-inspection provenance with authoritative readback and a gate-revalidated fingerprint");
      }
      await this.bindAuthority({ projectRoot: state.project_root, ticketPath: state.ticket_path });
      const currentness = await this.checkAuthorityCurrentness(state);
      if (!currentness.current) {
        this.markAuthorityDrift(executionId, currentness.changed);
        throw new Error("authority artifacts changed before VERIFIED admission");
      }
    }
    return this.store.withLock(() => {
      const current = this.status(executionId);
      current.verification_verdict = verdict;
      current.phase = verdict === "VERIFIED" ? "VERIFY_VERIFIED_ADMITTED" : "VERIFY_TERMINAL";
      current.updated_at = now();
      this.store.writeExecution(current);
      if (verdict !== "VERIFIED") {
        this.#releaseActiveTicket(current);
        this.#deactivateSessions(current);
      }
      return current;
    });
  }

  finishVerificationProgression(executionId, ownerSessionId) {
    return this.store.withLock(() => {
      const state = this.status(executionId);
      assertOwner(state, ownerSessionId);
      if (state.execution_mode !== "VERIFY" || state.phase !== "VERIFY_VERIFIED_ADMITTED") {
        throw new Error(`verification progression is not available in phase ${state.phase}`);
      }
      state.phase = "VERIFY_DONE";
      state.updated_at = now();
      this.store.writeExecution(state);
      this.#releaseActiveTicket(state);
      this.#deactivateSessions(state);
      return state;
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
      this.store.writeAssignment(terminal);
      this.store.clearActiveTicket(assignment.project_root, assignment.ticket_path, `assignment:${assignmentId}`);
      const parent = this.store.readSession(parentSessionId);
      if (parent) {
        this.store.writeSession(parentSessionId, {
          ...parent,
          armed: false,
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

  #deactivateSessions(state) {
    for (const sid of new Set([state.session_id, state.parent_session_id].filter(Boolean))) {
      const session = this.store.readSession(sid);
      if (!session) continue;
      this.store.writeSession(sid, {
        ...session,
        armed: false,
        role: null,
        execution_id: null,
        updated_at: now(),
      });
    }
  }

  #releaseActiveTicket(state) {
    this.store.clearActiveTicket(state.project_root, state.ticket_path, state.execution_id);
  }
}
