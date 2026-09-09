import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { BOUNDARY_PROTOCOL, hashBytes, validateTicket } from "./authority-binding.js";
import { checkVerificationCurrentness, readVerificationBinding, readVerificationVerdict, sealVerificationVerdict } from "./verification-binding.js";

export function ticketStatus(bytes) {
  const header = bytes.toString("utf8").split(/^##\s/m)[0];
  return /^Status:[ \t]*(\S+)[ \t]*\r?$/m.exec(header)?.[1] ?? "unknown";
}

function statusCandidate(before, from, to) {
  const text = before.toString("utf8");
  if (!Buffer.from(text).equals(before)) throw new Error("Ticket must be valid UTF-8");
  const header = text.split(/^##\s/m)[0];
  const exact = new RegExp(`^Status:[ \\t]*${from}[ \\t]*\\r?$`, "gm");
  const matches = [...header.matchAll(exact)];
  if (matches.length !== 1 || [...header.matchAll(/^Status:/gm)].length !== 1) throw new Error(`exactly one top metadata Status: ${from} is required`);
  const start = matches[0].index + matches[0][0].indexOf(from);
  return Buffer.from(text.slice(0, start) + to + text.slice(start + from.length));
}

export const readyCandidate = before => statusCandidate(before, "ready", "done");
export const doneReadyCandidate = before => statusCandidate(before, "done", "ready");

function replaceExact(file, expectedHash, bytes, mode) {
  if (hashBytes(fs.readFileSync(file)) !== expectedHash) throw new Error("Ticket compare-and-swap failed");
  const temporary = path.join(path.dirname(file), `.iis-finalize-${crypto.randomUUID()}.tmp`);
  try {
    const fd = fs.openSync(temporary, "wx", mode);
    try {
      fs.writeFileSync(fd, bytes);
      fs.fchmodSync(fd, mode);
      fs.fsyncSync(fd);
    } finally {
      fs.closeSync(fd);
    }
    if (hashBytes(fs.readFileSync(file)) !== expectedHash) throw new Error("Ticket changed before atomic replacement");
    fs.renameSync(temporary, file);
    const directory = fs.openSync(path.dirname(file), "r");
    try { fs.fsyncSync(directory); } finally { fs.closeSync(directory); }
  } finally {
    if (fs.existsSync(temporary)) fs.unlinkSync(temporary);
  }
}

function baseResult(binding, loadedBinding, loadedVerdict, terminal) {
  return {
    ticket_path: binding.ticket_path,
    verification_terminal: terminal.handle,
    verification_owner: terminal.owner_id,
    ...(terminal.verifier_model ? { verifier_model: terminal.verifier_model } : {}),
    ...(terminal.verifier_model_role ? { verifier_model_role: terminal.verifier_model_role } : {}),
    verification_binding: loadedBinding.binding_path,
    verification_binding_sha256: loadedBinding.binding_sha256,
    verification_verdict_record: loadedVerdict.verdict_path,
    verification_verdict_record_sha256: loadedVerdict.verdict_sha256,
    verification_verdict: terminal.verification_verdict,
    verifier_ticket_progression: terminal.ticket_progression,
    verifier_observed_ticket_status: terminal.observed_ticket_status,
  };
}

function loadAcceptedTerminal(terminal, verdictRecordPath) {
  if (!terminal || terminal.schema !== "iis-ready-host-terminal/v1") throw new Error("ready_finalize requires a host-accepted verifier terminal");
  if (!["VERIFIED", "FAILED", "INCONCLUSIVE"].includes(terminal.verification_verdict)) throw new Error("host verifier terminal has an invalid verdict");
  if (typeof terminal.handle !== "string" || typeof terminal.owner_id !== "string") throw new Error("host verifier terminal identity is incomplete");
  const loadedBinding = readVerificationBinding(terminal.verification_binding, terminal.verification_binding_sha256);
  const binding = loadedBinding.binding;
  if (terminal.project_root !== binding.project_root
      || terminal.ticket_path !== binding.ticket_path
      || JSON.stringify(terminal.stable_target_paths) !== JSON.stringify(binding.stable_target_paths)
      || JSON.stringify(terminal.scenario_effect_paths) !== JSON.stringify(binding.scenario_effect_paths)) {
    throw new Error("host verifier terminal does not match its verification binding");
  }
  let loadedVerdict;
  if (verdictRecordPath && fs.existsSync(verdictRecordPath)) {
    const stat = fs.lstatSync(verdictRecordPath);
    if (!stat.isFile() || stat.isSymbolicLink()) throw new Error("host verification verdict record must be a regular file");
    if (process.platform !== "win32" && (stat.mode & 0o077) !== 0) throw new Error("host verification verdict record permissions must be 0600");
    const bytes = fs.readFileSync(verdictRecordPath);
    loadedVerdict = readVerificationVerdict(verdictRecordPath, hashBytes(bytes));
  } else {
    const sealed = sealVerificationVerdict({
      bindingPath: loadedBinding.binding_path,
      bindingSha256: loadedBinding.binding_sha256,
      verdict: terminal.verification_verdict,
      verdictPath: verdictRecordPath,
    });
    loadedVerdict = readVerificationVerdict(sealed.verdict_path, sealed.verdict_sha256);
  }
  if (loadedVerdict.binding.binding_path !== loadedBinding.binding_path
      || loadedVerdict.binding.binding_sha256 !== loadedBinding.binding_sha256
      || loadedVerdict.verdict.verification_verdict !== terminal.verification_verdict) {
    throw new Error("host verification verdict record does not match its terminal");
  }
  return { binding, loadedBinding, loadedVerdict };
}

async function requireCurrent(binding, expectedTicketSha256) {
  const current = await checkVerificationCurrentness(binding, { expectedTicketSha256 });
  if (!current.current) {
    const details = [
      ...current.authority_changed.map(item => `${item.kind}:${item.path}`),
      ...current.stable_target_changed.map(item => `stable:${item}`),
    ];
    throw new Error(`verification target/authority changed${details.length ? `: ${details.join(", ")}` : ""}`);
  }
  return current;
}


// Semantic verification belongs to the host-designated verifier invocation.
// This function consumes that accepted terminal and owns only the narrow
// binding-current status progression; caller-authored verdict evidence is never accepted.
export async function finalizeVerification({
  acceptedTerminal,
  verdictRecordPath,
  executeArgv,
  bundleIdentity,
  boundaryProtocol = BOUNDARY_PROTOCOL,
  recordResult,
  hooks = {},
  ...unsupported
}) {
  if (Object.keys(unsupported).length) throw new Error("ready_finalize accepts only a host verifier terminal");
  if (typeof bundleIdentity !== "string" || !bundleIdentity) throw new Error("current loaded bundle identity is required");
  const finish = async result => recordResult ? recordResult(result) : result;
  const { binding, loadedBinding, loadedVerdict } = loadAcceptedTerminal(acceptedTerminal, verdictRecordPath);
  const verdictRecord = loadedVerdict.verdict;
  const verdict = acceptedTerminal.verification_verdict;
  const base = baseResult(binding, loadedBinding, loadedVerdict, acceptedTerminal);
  const actualStatus = () => ticketStatus(fs.readFileSync(binding.ticket_path));

  if ((binding.ticket_status_at_capture === "ready" && acceptedTerminal.ticket_progression !== "PENDING CALLER FINALIZATION")
      || (binding.ticket_status_at_capture === "done" && acceptedTerminal.ticket_progression !== "NOT APPLICABLE")) {
    throw new Error("host verifier terminal progression does not match capture status");
  }

  if (binding.bundle_identity !== bundleIdentity
      || binding.boundary_protocol !== boundaryProtocol
      || verdictRecord.bundle_identity !== binding.bundle_identity
      || verdictRecord.boundary_protocol !== binding.boundary_protocol) {
    return finish({
      ...base,
      ticket_progression: "FAILED",
      progression_basis: "NONE",
      ticket_status_after: actualStatus(),
      progression_detail: "verification binding belongs to a different boundary bundle/protocol",
    });
  }

  if (binding.ticket_status_at_capture === "done") {
    let detail;
    try {
      await requireCurrent(binding);
      await validateTicket(binding.validator_path, binding.ticket_path, binding.project_root, executeArgv);
    } catch (error) {
      detail = `diagnostic re-verification drift/validation: ${error.message}`;
    }
    return finish({
      ...base,
      ticket_progression: "NOT APPLICABLE",
      progression_basis: "NONE",
      ticket_status_after: actualStatus(),
      ...(detail ? { progression_detail: detail } : {}),
    });
  }

  if (binding.ticket_status_at_capture !== "ready") {
    return finish({
      ...base,
      ticket_progression: "FAILED",
      progression_basis: "NONE",
      ticket_status_after: actualStatus(),
      progression_detail: `unsupported capture status: ${binding.ticket_status_at_capture}`,
    });
  }

  if (verdict !== "VERIFIED") {
    return finish({
      ...base,
      ticket_progression: "NOT APPLICABLE",
      progression_basis: "NONE",
      ticket_status_after: actualStatus(),
    });
  }

  let readyBytes = null;
  let candidateBytes = null;
  let candidateSha256 = null;
  let mode = null;
  let wroteThisCall = false;
  try {
    const currentBytes = fs.readFileSync(binding.ticket_path);
    const status = ticketStatus(currentBytes);
    mode = fs.statSync(binding.ticket_path).mode & 0o777;

    if (status === "done") {
      readyBytes = doneReadyCandidate(currentBytes);
      if (hashBytes(readyBytes) !== binding.ticket_sha256) throw new Error("current done Ticket does not match captured ready bytes");
      candidateBytes = currentBytes;
      candidateSha256 = hashBytes(currentBytes);
      await requireCurrent(binding, candidateSha256);
      await validateTicket(binding.validator_path, binding.ticket_path, binding.project_root, executeArgv);
      return finish({
        ...base,
        ticket_progression: "NOT APPLICABLE",
        progression_basis: "ALREADY_DONE_MATCHING_BINDING",
        ticket_status_after: "done",
        progression_detail: "canonical Ticket already matches this binding's expected done candidate without attributable prior finalizer result",
      });
    }

    if (status !== "ready") throw new Error(`Ticket status must be ready for progression; found ${status}`);
    if (hashBytes(currentBytes) !== binding.ticket_sha256) throw new Error("current ready Ticket bytes differ from verification capture");
    readyBytes = currentBytes;
    candidateBytes = readyCandidate(currentBytes);
    candidateSha256 = hashBytes(candidateBytes);
    await requireCurrent(binding);
    await validateTicket(binding.validator_path, binding.ticket_path, binding.project_root, executeArgv);
    await hooks.beforeRename?.({ binding, candidate_sha256: candidateSha256 });
    replaceExact(binding.ticket_path, binding.ticket_sha256, candidateBytes, mode);
    wroteThisCall = true;
    await hooks.afterRename?.({ binding, candidate_sha256: candidateSha256 });
    await validateTicket(binding.validator_path, binding.ticket_path, binding.project_root, executeArgv);
    await requireCurrent(binding, candidateSha256);
    await hooks.afterPostValidation?.({ binding, candidate_sha256: candidateSha256 });
    if (hashBytes(fs.readFileSync(binding.ticket_path)) !== candidateSha256) throw new Error("Ticket changed after post-validation");
    return await finish({
      ...base,
      ticket_progression: "COMPLETED",
      progression_basis: "WRITE_PERFORMED_THIS_CALL",
      ticket_status_after: "done",
    });
  } catch (error) {
    let rollback;
    let detail = error.message;
    if (wroteThisCall && candidateSha256 && readyBytes) {
      try {
        if (hashBytes(fs.readFileSync(binding.ticket_path)) === candidateSha256) {
          const current = await checkVerificationCurrentness(binding, { expectedTicketSha256: candidateSha256 });
          if (current.current) {
            replaceExact(binding.ticket_path, candidateSha256, readyBytes, mode);
            rollback = hashBytes(fs.readFileSync(binding.ticket_path)) === binding.ticket_sha256 ? "restored exact ready bytes" : "readback mismatch";
          } else {
            rollback = "withheld because authority/stable target drifted";
          }
        } else {
          rollback = "withheld because Ticket no longer equals this call's candidate";
        }
      } catch (restoreError) {
        rollback = `withheld/failed: ${restoreError.message}`;
      }
    }
    if (rollback) detail += `; rollback ${rollback}`;
    return finish({
      ...base,
      ticket_progression: "FAILED",
      progression_basis: "NONE",
      ticket_status_after: actualStatus(),
      progression_detail: detail,
      ...(rollback ? { rollback } : {}),
    });
  }
}
