import fs from "node:fs";
import path from "node:path";
import { hashBytes, isInsideProject } from "./authority-binding.js";

const fail = (code, detail) => { throw new Error(`${code}: ${detail}`); };

function exactFile(file) {
  if (typeof file !== "string" || !path.isAbsolute(file)) fail("PLAN_REVIEW_STALE", "paths must be exact absolute paths");
  let canonical;
  try { canonical = fs.realpathSync(file); }
  catch (error) { fail("PLAN_REVIEW_STALE", error.message); }
  if (canonical !== file || !fs.statSync(file).isFile()) fail("PLAN_REVIEW_STALE", `not a canonical file: ${file}`);
  return canonical;
}

function bindFindings(decision, reviewPath) {
  const projection = decision.projection;
  if (!projection || !["preserved", "gap", "unknown"].includes(projection.status) || typeof projection.basis !== "string" || !projection.basis.trim()) {
    fail("PLAN_REVIEW_STALE", "missing projection judgment");
  }
  if (!Array.isArray(decision.findings)) fail("PLAN_REVIEW_STALE", "missing findings");
  const evidence = [];
  let unresolved = projection.status !== "preserved";
  for (const finding of decision.findings) {
    if (!finding || !["contract_gap", "method", "evidence_limit"].includes(finding.kind) ||
        typeof finding.material !== "boolean" || !["unresolved", "dismissed", "resolved"].includes(finding.disposition)) {
      fail("PLAN_REVIEW_STALE", "malformed finding disposition");
    }
    for (const field of ["anchor", "observation", "basis", "next_owner"]) {
      if (typeof finding[field] !== "string" || !finding[field].trim()) fail("PLAN_REVIEW_STALE", `malformed finding: ${field}`);
    }
    unresolved ||= finding.disposition === "unresolved" && (finding.material || finding.kind === "contract_gap");
    if (finding.evidence_refs !== undefined && !Array.isArray(finding.evidence_refs)) fail("PLAN_REVIEW_STALE", "malformed evidence references");
    for (const ref of finding.evidence_refs ?? []) {
      if (!ref || typeof ref.path !== "string" || !ref.path.trim() || !/^[0-9a-f]{64}$/.test(ref.sha256) || typeof ref.locator !== "string" || !ref.locator.trim()) {
        fail("PLAN_REVIEW_STALE", "malformed evidence reference");
      }
      const file = exactFile(path.resolve(path.dirname(reviewPath), ref.path));
      if (hashBytes(fs.readFileSync(file)) !== ref.sha256) fail("PLAN_REVIEW_STALE", `evidence changed: ${file}`);
      evidence.push({ path: file, sha256: ref.sha256 });
    }
  }
  if (decision.decision === "ADMIT" && unresolved) fail("PLAN_NOT_ADMITTED", "ADMIT contradicts unresolved projection or material findings");
  return evidence;
}

// This verifies exact current byte pairing. Reviewer independence and semantic sufficiency
// remain properties of the planning/review workflow rather than this boundary check.
export function bindPlanReview({ planReviewPath, authority, requireAdmit = true }) {
  if (!planReviewPath) fail("PLAN_REVIEW_REQUIRED", "supply the actual reviewer result path");
  try {
    const reviewPath = exactFile(planReviewPath);
    if (isInsideProject(authority.project_root, reviewPath)) fail("PLAN_REVIEW_STALE", "review must be outside Project Root");
    const bytes = fs.readFileSync(reviewPath);
    const review = JSON.parse(bytes);
    if (review.schema !== "iis-plan-review/v2" || review.project_root !== authority.project_root) fail("PLAN_REVIEW_STALE", "schema/root mismatch");
    if (!Array.isArray(review.plans) || !review.plans.length || !Array.isArray(review.contracts) || !Array.isArray(review.decisions)) fail("PLAN_REVIEW_STALE", "missing bindings");
    if (!review.review_origin?.reviewer || !review.review_origin?.evidence_reference) fail("PLAN_REVIEW_STALE", "missing review origin");
    const plans = review.plans.map(plan => {
      const file = exactFile(plan.path);
      if (!isInsideProject(authority.project_root, file)) fail("PLAN_REVIEW_STALE", "plans must be project-local");
      const sha256 = hashBytes(fs.readFileSync(file));
      if (sha256 !== plan.sha256) fail("PLAN_REVIEW_STALE", `plan changed: ${file}`);
      return { path: file, sha256 };
    });
    if (new Set(plans.map(item => item.path)).size !== plans.length) fail("PLAN_REVIEW_STALE", "duplicate plan binding");
    const contracts = review.contracts.filter(item => item.ticket_path === authority.ticket_path);
    const decisions = review.decisions.filter(item => item.ticket_path === authority.ticket_path);
    if (contracts.length !== 1 || decisions.length !== 1) fail("PLAN_REVIEW_STALE", "exact Ticket pairing missing or ambiguous");
    const contract = contracts[0];
    const decision = decisions[0];
    if (contract.ticket_sha256 !== hashBytes(fs.readFileSync(authority.ticket_path)) || contract.authority_digest !== authority.authority_digest) fail("PLAN_REVIEW_STALE", "product authority changed");
    if (!["ADMIT", "REVISE", "EVIDENCE_NEEDED"].includes(decision.decision)) fail("PLAN_REVIEW_STALE", "unknown decision");
    if (typeof decision.rationale !== "string" || typeof decision.start_scope !== "string" || !Array.isArray(decision.conditions)) fail("PLAN_REVIEW_STALE", "malformed decision");
    for (const condition of decision.conditions) {
      for (const field of ["plan_anchor", "permitted_initial_work", "discriminating_observation", "dependent_work_not_yet_permitted", "response_if_refuted"]) {
        if (typeof condition[field] !== "string") fail("PLAN_REVIEW_STALE", `malformed condition: ${field}`);
      }
    }
    const evidence = bindFindings(decision, reviewPath);
    if (requireAdmit && decision.decision !== "ADMIT") fail("PLAN_NOT_ADMITTED", decision.decision);
    return {
      review_path: reviewPath,
      review_sha256: hashBytes(bytes),
      plans,
      evidence,
      authority_digest: authority.authority_digest,
      decision,
    };
  } catch (error) {
    if (/^PLAN_/.test(error.message)) throw error;
    fail("PLAN_REVIEW_STALE", error.message);
  }
}

export function checkPlanCurrentness(binding) {
  const changed = [];
  for (const item of [{ path: binding.review_path, sha256: binding.review_sha256 }, ...(binding.plans || []), ...(binding.evidence || [])]) {
    try {
      if (hashBytes(fs.readFileSync(item.path)) !== item.sha256) changed.push(item.path);
    } catch {
      changed.push(item.path);
    }
  }
  return { current: changed.length === 0, changed };
}
