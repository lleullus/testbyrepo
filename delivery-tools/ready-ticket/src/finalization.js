import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { hashBytes, validateTicket } from "./authority-binding.js";
import { checkVerificationCurrentness, readVerificationBinding } from "./verification-binding.js";

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

function baseResult(binding, bindingPath, bindingSha256, verdict) {
  return {
    ticket_path: binding.ticket_path,
    verification_binding: bindingPath,
    verification_binding_sha256: bindingSha256,
    verification_verdict: verdict,
  };
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

function provenanceKey(bindingPath, bindingSha256) {
  return `${bindingPath}:${bindingSha256}`;
}

// Semantic VERIFIED belongs to the verifier. This function owns only the narrow
// binding-current status progression and has no execution/session lifecycle state.
export async function finalizeVerification({
  bindingPath,
  bindingSha256,
  verdict,
  executeArgv,
  provenance,
  hooks = {},
}) {
  if (!["VERIFIED", "FAILED", "INCONCLUSIVE"].includes(verdict)) throw new Error("invalid verification verdict");
  const loaded = readVerificationBinding(bindingPath, bindingSha256);
  const binding = loaded.binding;
  const base = baseResult(binding, loaded.binding_path, loaded.binding_sha256, verdict);
  const actualStatus = () => ticketStatus(fs.readFileSync(binding.ticket_path));

  if (binding.ticket_status_at_capture === "done") {
    let detail;
    try {
      await requireCurrent(binding);
      await validateTicket(binding.validator_path, binding.ticket_path, binding.project_root, executeArgv);
    } catch (error) {
      detail = `diagnostic re-verification drift/validation: ${error.message}`;
    }
    return {
      ...base,
      ticket_progression: "NOT APPLICABLE",
      progression_basis: "NONE",
      ticket_status_after: actualStatus(),
      ...(detail ? { progression_detail: detail } : {}),
    };
  }

  if (binding.ticket_status_at_capture !== "ready") {
    return {
      ...base,
      ticket_progression: "FAILED",
      progression_basis: "NONE",
      ticket_status_after: actualStatus(),
      progression_detail: `unsupported capture status: ${binding.ticket_status_at_capture}`,
    };
  }

  if (verdict !== "VERIFIED") {
    return {
      ...base,
      ticket_progression: "NOT APPLICABLE",
      progression_basis: "NONE",
      ticket_status_after: actualStatus(),
    };
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
      const previous = provenance?.get?.(provenanceKey(loaded.binding_path, loaded.binding_sha256));
      if (previous?.ticket_progression === "COMPLETED" && previous?.progression_basis === "WRITE_PERFORMED_THIS_CALL") {
        return {
          ...base,
          ticket_progression: "COMPLETED",
          progression_basis: "RECOVERED_CAPTURED_FINALIZER_RESULT",
          ticket_status_after: "done",
        };
      }
      return {
        ...base,
        ticket_progression: "NOT APPLICABLE",
        progression_basis: "ALREADY_DONE_MATCHING_BINDING",
        ticket_status_after: "done",
        progression_detail: "canonical Ticket already matches this binding's expected done candidate without attributable prior finalizer result",
      };
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
    return {
      ...base,
      ticket_progression: "COMPLETED",
      progression_basis: "WRITE_PERFORMED_THIS_CALL",
      ticket_status_after: "done",
    };
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
    return {
      ...base,
      ticket_progression: "FAILED",
      progression_basis: "NONE",
      ticket_status_after: actualStatus(),
      progression_detail: detail,
      ...(rollback ? { rollback } : {}),
    };
  }
}
