import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { validateTicket } from "./authority-binding.js";
import { hashBytes } from "./plan-binding.js";
import { checkVerificationTarget } from "./verification-target.js";

export function ticketStatus(bytes) {
  const header = bytes.toString("utf8").split(/^##\s/m)[0];
  return /^Status:[ \t]*(\S+)[ \t]*\r?$/m.exec(header)?.[1] ?? "unknown";
}
export function readyCandidate(before) {
  const text = before.toString("utf8");
  if (!Buffer.from(text).equals(before)) throw new Error("Ticket must be valid UTF-8");
  const header = text.split(/^##\s/m)[0];
  const matches = [...header.matchAll(/^Status:[ \t]*ready[ \t]*\r?$/gm)];
  if (matches.length !== 1 || [...header.matchAll(/^Status:/gm)].length !== 1) throw new Error("exactly one top metadata Status: ready is required");
  const start = matches[0].index + matches[0][0].indexOf("ready");
  return Buffer.from(text.slice(0, start) + "done" + text.slice(start + 5));
}
function replaceExact(file, expectedHash, bytes, mode) {
  if (hashBytes(fs.readFileSync(file)) !== expectedHash) throw new Error("Ticket compare-and-swap failed");
  const temporary = path.join(path.dirname(file), `.iis-finalize-${crypto.randomUUID()}.tmp`);
  try {
    const fd = fs.openSync(temporary, "wx", mode);
    try { fs.writeFileSync(fd, bytes); fs.fchmodSync(fd, mode); fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
    if (hashBytes(fs.readFileSync(file)) !== expectedHash) throw new Error("Ticket changed before atomic replacement");
    fs.renameSync(temporary, file);
    const directory = fs.openSync(path.dirname(file), "r");
    try { fs.fsyncSync(directory); } finally { fs.closeSync(directory); }
  } finally { if (fs.existsSync(temporary)) fs.unlinkSync(temporary); }
}
async function expectedCurrent(lifecycle, state, intent) {
  const authority = await lifecycle.checkAuthorityCurrentness(state);
  const unexpected = authority.changed.filter(item => !(item.path === state.ticket_path && item.actual === intent.candidate_sha256));
  if (unexpected.length) throw new Error("authority changed during finalization");
  const target = await checkVerificationTarget(state.verification_target, { executeArgv: lifecycle.executeArgv, expectedTicket: { path: state.ticket_path, sha256: intent.candidate_sha256 } });
  if (!target.current) throw new Error(`product changed during finalization: ${target.changed.join(", ")}`);
}
function exactIntent(lifecycle, id, actor, operationId) {
  const state = lifecycle.assertOwner(lifecycle.status(id), actor);
  if (state.active_operation?.operation_id !== operationId || state.active_operation.kind !== "finalization") throw new Error("finalization owner/intent changed");
  return state;
}

// Semantic VERIFIED belongs to the verifier. This module owns only guarded progression.
export async function finalizeVerification(lifecycle, id, actor, verdict) {
  if (!["VERIFIED", "FAILED", "INCONCLUSIVE"].includes(verdict)) throw new Error("invalid verification verdict");
  let state = lifecycle.status(id);
  if (state.phase === "COMPLETE" && state.terminal_result) {
    if (state.session_id !== actor || state.terminal_result.verification_verdict !== verdict) throw new Error("terminal recovery owner/verdict mismatch");
    if (state.finalized_ticket_sha256) {
      if (hashBytes(fs.readFileSync(state.ticket_path)) !== state.finalized_ticket_sha256) throw new Error("terminal recovery Ticket changed");
      await expectedCurrent(lifecycle, state, { candidate_sha256: state.finalized_ticket_sha256 });
      await validateTicket(state.validator_path, state.ticket_path, state.project_root, lifecycle.executeArgv);
    }
    return lifecycle.store.withLock(() => {
      const current = lifecycle.status(id);
      if (JSON.stringify(current) !== JSON.stringify(state)) throw new Error("terminal changed during recovery");
      const slot = lifecycle.store.readActiveTicket(state.project_root, state.ticket_path);
      if (slot && slot.identity !== state.reservation_id) throw new Error("terminal recovery cannot release a newer owner");
      if (state.assignment_id) lifecycle.store.writeAssignment({ ...lifecycle.store.readAssignment(state.assignment_id), status: "terminal" });
      if (slot) lifecycle.store.clearActiveTicket(state.project_root, state.ticket_path, state.reservation_id);
      return state.terminal_result;
    });
  }
  state = lifecycle.assertOwner(state, actor);
  if (state.purpose !== "verify") throw new Error("verification execution required");
  if (state.owned_service || state.uncertainty) throw new Error("settle services and uncertain effects before finalization");
  if (state.active_operation && state.active_operation.kind !== "finalization") throw new Error("settle active operation before finalization");
  if (verdict !== "VERIFIED") {
    if (state.active_operation) throw new Error("recover pending finalization before changing verdict");
    return lifecycle.store.withLock(() => {
      const current = lifecycle.assertOwner(lifecycle.status(id), actor);
      const result = { verification_verdict: verdict, ticket_progression: "NOT APPLICABLE", ticket_status_after: ticketStatus(fs.readFileSync(current.ticket_path)) };
      lifecycle.closeLocked(current, "COMPLETE", result);
      return result;
    });
  }
  let intent = state.active_operation;
  try {
    if (!intent) {
      await lifecycle.ensureCurrent(id, actor, { effect: true });
      state = lifecycle.assertDispatch(id, actor, true);
      if (state.execution_mode === "SUBAGENT" && !state.progression_released) throw new Error("PRE_PROGRESSION must be released before delegated VERIFIED progression");
      await validateTicket(state.validator_path, state.ticket_path, state.project_root, lifecycle.executeArgv);
      await lifecycle.checkPrepared(state);
      const before = fs.readFileSync(state.ticket_path);
      if (ticketStatus(before) === "done") {
        return lifecycle.store.withLock(() => {
          const current = lifecycle.assertDispatch(id, actor, true);
          const result = { verification_verdict: verdict, ticket_progression: "NOT APPLICABLE", ticket_status_after: "done" };
          lifecycle.closeLocked(current, "COMPLETE", result);
          return result;
        });
      }
      const candidate = readyCandidate(before);
      intent = lifecycle.beginOperation(id, actor, { kind: "finalization", effect_surface: state.ticket_path, before_sha256: hashBytes(before), candidate_sha256: hashBytes(candidate), before_bytes: before.toString("base64"), candidate_bytes: candidate.toString("base64"), mode: fs.statSync(state.ticket_path).mode & 0o777, authority_digest: state.authority_digest, target_digest: state.verification_target.digest });
    }
    state = exactIntent(lifecycle, id, actor, intent.operation_id);
    let currentHash = hashBytes(fs.readFileSync(state.ticket_path));
    if (currentHash !== intent.before_sha256 && currentHash !== intent.candidate_sha256) throw new Error("recovery requires owner review: Ticket differs from before and candidate");
    if (currentHash === intent.before_sha256) {
      await lifecycle.checkPrepared(state);
      lifecycle.store.withLock(() => {
        exactIntent(lifecycle, id, actor, intent.operation_id);
        replaceExact(state.ticket_path, intent.before_sha256, Buffer.from(intent.candidate_bytes, "base64"), intent.mode);
      });
    }
    await expectedCurrent(lifecycle, state, intent);
    await validateTicket(state.validator_path, state.ticket_path, state.project_root, lifecycle.executeArgv);
    await expectedCurrent(lifecycle, state, intent);
    return lifecycle.store.withLock(() => {
      const current = exactIntent(lifecycle, id, actor, intent.operation_id);
      if (hashBytes(fs.readFileSync(state.ticket_path)) !== intent.candidate_sha256) throw new Error("Ticket changed after post-validation");
      const result = { verification_verdict: "VERIFIED", ticket_progression: "COMPLETED", ticket_status_after: "done", finalization_id: intent.operation_id };
      current.active_operation = null;
      current.finalized_ticket_sha256 = intent.candidate_sha256;
      lifecycle.closeLocked(current, "COMPLETE", result);
      return result;
    });
  } catch (error) {
    let rollback = "not attempted", recovery = error.message;
    if (intent) {
      try {
        const current = exactIntent(lifecycle, id, actor, intent.operation_id);
        if (hashBytes(fs.readFileSync(current.ticket_path)) === intent.candidate_sha256) {
          await expectedCurrent(lifecycle, current, intent);
          lifecycle.store.withLock(() => {
            exactIntent(lifecycle, id, actor, intent.operation_id);
            replaceExact(current.ticket_path, intent.candidate_sha256, Buffer.from(intent.before_bytes, "base64"), intent.mode);
          });
          rollback = hashBytes(fs.readFileSync(current.ticket_path)) === intent.before_sha256 ? "restored exact ready bytes" : "readback mismatch";
        }
      } catch (restoreError) { recovery += `; rollback withheld/failed: ${restoreError.message}`; }
    }
    const result = { verification_verdict: verdict, ticket_progression: "FAILED", ticket_status_after: ticketStatus(fs.readFileSync(state.ticket_path)), progression_detail: recovery, rollback };
    try {
      lifecycle.update(id, current => {
        // Never erase a crash intent or overwrite a durably committed terminal.
        if (current.phase === "COMPLETE") throw new Error("terminal cleanup requires recovery");
        current.phase = "PAUSED"; current.pause = { kind: "RECOVERY_REQUIRED" }; current.progression_failure = result;
      });
    } catch (writeError) { result.progression_detail += `; state recovery required: ${writeError.message}`; }
    return result;
  }
}
