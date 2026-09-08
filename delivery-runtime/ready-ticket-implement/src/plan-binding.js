import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { isInsideProject } from "./authority-binding.js";

export const hashBytes = bytes => crypto.createHash("sha256").update(bytes).digest("hex");
const fail = (code, detail) => { throw new Error(`${code}: ${detail}`); };
const exactFile = file => {
  if (typeof file !== "string" || !path.isAbsolute(file)) fail("PLAN_REVIEW_STALE", "paths must be exact absolute paths");
  const canonical = fs.realpathSync(file);
  if (canonical !== file || !fs.statSync(file).isFile()) fail("PLAN_REVIEW_STALE", `not a canonical file: ${file}`);
  return canonical;
};

// This verifies current byte pairing, not independence or semantic sufficiency.
export function bindPlanReview({ planReviewPath, authority, requireAdmit = true }) {
  if (!planReviewPath) fail("PLAN_REVIEW_REQUIRED", "supply the actual reviewer result path");
  try {
    const reviewPath = exactFile(planReviewPath);
    if (isInsideProject(authority.project_root, reviewPath)) fail("PLAN_REVIEW_STALE", "review must be outside Project Root");
    const bytes = fs.readFileSync(reviewPath);
    const review = JSON.parse(bytes);
    if (review.schema !== "iis-plan-review/v1" || review.project_root !== authority.project_root) fail("PLAN_REVIEW_STALE", "schema/root mismatch");
    if (!Array.isArray(review.plans) || !review.plans.length || !Array.isArray(review.contracts) || !Array.isArray(review.decisions)) fail("PLAN_REVIEW_STALE", "missing bindings");
    if (!review.review_origin?.reviewer || !review.review_origin?.evidence_reference || !review.heuristic?.evidence_reference || typeof review.heuristic.disposition_summary !== "string") fail("PLAN_REVIEW_STALE", "missing review origin or heuristic result");
    const plans = review.plans.map(plan => {
      const file = exactFile(plan.path);
      if (!isInsideProject(authority.project_root, file)) fail("PLAN_REVIEW_STALE", "plans must be project-local");
      const sha256 = hashBytes(fs.readFileSync(file));
      if (sha256 !== plan.sha256) fail("PLAN_REVIEW_STALE", `plan changed: ${file}`);
      return { path: file, sha256 };
    });
    if (new Set(plans.map(p => p.path)).size !== plans.length) fail("PLAN_REVIEW_STALE", "duplicate plan binding");
    const contracts = review.contracts.filter(c => c.ticket_path === authority.ticket_path);
    const decisions = review.decisions.filter(d => d.ticket_path === authority.ticket_path);
    if (contracts.length !== 1 || decisions.length !== 1) fail("PLAN_REVIEW_STALE", "exact Ticket pairing missing or ambiguous");
    const contract = contracts[0], decision = decisions[0];
    if (contract.ticket_sha256 !== hashBytes(fs.readFileSync(authority.ticket_path)) || contract.authority_digest !== authority.authority_digest) fail("PLAN_REVIEW_STALE", "product authority changed");
    if (!["ADMIT", "REVISE", "EVIDENCE_NEEDED"].includes(decision.decision)) fail("PLAN_REVIEW_STALE", "unknown decision");
    if (typeof decision.rationale !== "string" || typeof decision.start_scope !== "string" || !Array.isArray(decision.conditions)) fail("PLAN_REVIEW_STALE", "malformed decision");
    for (const condition of decision.conditions) for (const field of ["plan_anchor", "permitted_initial_work", "discriminating_observation", "dependent_work_not_yet_permitted", "response_if_refuted"]) {
      if (typeof condition[field] !== "string") fail("PLAN_REVIEW_STALE", `malformed condition: ${field}`);
    }
    if (requireAdmit && decision.decision !== "ADMIT") fail("PLAN_NOT_ADMITTED", decision.decision);
    return { review_path: reviewPath, review_sha256: hashBytes(bytes), plans, authority_digest: authority.authority_digest, decision };
  } catch (error) {
    if (/^PLAN_/.test(error.message)) throw error;
    fail("PLAN_REVIEW_STALE", error.message);
  }
}

export function checkPlanCurrentness(binding) {
  const changed = [];
  for (const item of [{ path: binding.review_path, sha256: binding.review_sha256 }, ...binding.plans]) {
    try { if (hashBytes(fs.readFileSync(item.path)) !== item.sha256) changed.push(item.path); }
    catch { changed.push(item.path); }
  }
  return { current: changed.length === 0, changed };
}
