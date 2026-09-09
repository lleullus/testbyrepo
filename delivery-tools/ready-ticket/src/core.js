import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { bindAuthority, hashBytes } from "./authority-binding.js";
import { bindPlanReview } from "./plan-binding.js";
import { captureVerification as captureVerificationCore } from "./verification-binding.js";
import { finalizeVerification as finalizeVerificationCore } from "./finalization.js";

const execFileAsync = promisify(execFile);

export async function executeArgvNode(argv, options = {}) {
  try {
    const result = await execFileAsync(argv[0], argv.slice(1), {
      cwd: options.cwd,
      timeout: options.timeout,
      signal: options.signal,
      maxBuffer: 8 * 1024 * 1024,
    });
    return {
      exitCode: 0,
      interrupted: false,
      terminationState: "settled",
      stdout: result.stdout ?? "",
      stderr: result.stderr ?? "",
    };
  } catch (error) {
    const interrupted = Boolean(error.killed || options.signal?.aborted || error.name === "AbortError");
    return {
      exitCode: typeof error.code === "number" ? error.code : null,
      interrupted,
      terminationState: interrupted ? "unknown" : "settled",
      stdout: error.stdout ?? "",
      stderr: error.stderr ?? error.message ?? "",
    };
  }
}

export async function inspectAuthority({
  projectRoot,
  ticketPath,
  validatorPath,
  executeArgv = executeArgvNode,
  bundleIdentity = "source",
}) {
  return bindAuthority({
    projectRoot,
    ticketPath,
    allowedStatuses: ["ready", "done"],
    validatorPath,
    executeArgv,
    bundleIdentity,
  });
}

export async function checkPlanAdmission({
  projectRoot,
  ticketPath,
  planReviewPath,
  validatorPath,
  executeArgv = executeArgvNode,
  bundleIdentity = "source",
}) {
  const authority = await bindAuthority({
    projectRoot,
    ticketPath,
    allowedStatuses: ["ready"],
    validatorPath,
    executeArgv,
    bundleIdentity,
  });
  const plan = bindPlanReview({ planReviewPath, authority, requireAdmit: true });
  const admission = {
    schema: "iis-implementation-admission/v1",
    project_root: authority.project_root,
    ticket_path: authority.ticket_path,
    ticket_sha256: authority.ticket_sha256,
    authority_digest: authority.authority_digest,
    review_path: plan.review_path,
    review_sha256: plan.review_sha256,
    plans: plan.plans,
    decision: plan.decision.decision,
    start_scope: plan.decision.start_scope,
    conditions: plan.decision.conditions,
  };
  admission.admission_digest = hashBytes(JSON.stringify(admission));
  return admission;
}

export async function captureVerification(options) {
  return captureVerificationCore({ ...options, executeArgv: options.executeArgv ?? executeArgvNode });
}

export async function finalizeVerification(options) {
  return finalizeVerificationCore({ ...options, executeArgv: options.executeArgv ?? executeArgvNode });
}

export { bindAuthority, checkAuthorityCurrentness, hashBytes, validateTicket } from "./authority-binding.js";
export { bindPlanReview, checkPlanCurrentness } from "./plan-binding.js";
export { checkVerificationCurrentness, readVerificationBinding, snapshotStableTargets } from "./verification-binding.js";
export { ticketStatus, readyCandidate, doneReadyCandidate } from "./finalization.js";
