import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { bindAuthority, hashBytes } from "./authority-binding.js";
import { bindPlanReview } from "./plan-binding.js";
import { captureVerification as captureVerificationCore, sealVerificationVerdict as sealVerificationVerdictCore } from "./verification-binding.js";
import { finalizeVerification as finalizeVerificationCore } from "./finalization.js";

const execFileAsync = promisify(execFile);
const PACKAGE_ROOT = path.resolve(path.dirname(fs.realpathSync(fileURLToPath(import.meta.url))), "..");
const REQUIRED_BOUNDARY_FILES = [
  "delivery-tools/ready-ticket/omp.js",
  "delivery-tools/ready-ticket/cli.js",
  "delivery-tools/ready-ticket/index.js",
  "delivery-tools/ready-ticket/src/authority-binding.js",
  "delivery-tools/ready-ticket/src/plan-binding.js",
  "delivery-tools/ready-ticket/src/verification-binding.js",
  "delivery-tools/ready-ticket/src/finalization.js",
  "delivery-tools/ready-ticket/src/core.js",
];

function invalidBundle(detail) {
  throw new Error(`READY_BUNDLE_INVALID: ${detail}`);
}

export function currentReadyBundleIdentity() {
  const releaseRoot = path.resolve(PACKAGE_ROOT, "..", "..");
  const manifestPath = path.join(releaseRoot, "bundle.json");
  let manifest;
  try {
    const stat = fs.lstatSync(manifestPath);
    if (!stat.isFile() || stat.isSymbolicLink()) invalidBundle("bundle.json must be a regular file");
    manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  } catch (error) {
    if (error.message?.startsWith("READY_BUNDLE_INVALID:")) throw error;
    invalidBundle(`cannot read bundle.json: ${error.message}`);
  }
  if (manifest?.schema !== "iis-bundle/v2" || manifest.protocol !== 2 || manifest.family !== "ready-boundary-tools") {
    invalidBundle("unsupported schema, protocol, or family");
  }
  if (typeof manifest.bundle_id !== "string" || !/^[0-9a-f]{64}$/.test(manifest.bundle_id)) {
    invalidBundle("bundle_id must be an exact SHA-256");
  }
  if (path.basename(releaseRoot) !== manifest.bundle_id) invalidBundle("loaded release path does not match bundle_id");
  if (!manifest.files || typeof manifest.files !== "object" || Array.isArray(manifest.files)) {
    invalidBundle("files manifest is missing");
  }
  for (const relative of REQUIRED_BOUNDARY_FILES) {
    const expected = manifest.files[relative];
    const file = path.join(releaseRoot, relative);
    if (!expected || typeof expected.sha256 !== "string" || !Number.isInteger(expected.mode)) {
      invalidBundle(`missing boundary file identity: ${relative}`);
    }
    let stat;
    let bytes;
    try {
      stat = fs.lstatSync(file);
      bytes = fs.readFileSync(file);
    } catch (error) {
      invalidBundle(`cannot read boundary file ${relative}: ${error.message}`);
    }
    if (!stat.isFile() || stat.isSymbolicLink() || hashBytes(bytes) !== expected.sha256 || (stat.mode & 0o777) !== expected.mode) {
      invalidBundle(`boundary file drift: ${relative}`);
    }
  }
  return manifest.bundle_id;
}

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
    bundle_identity: authority.bundle_identity,
    bundle_root: authority.bundle_root,
    role_document_paths: authority.role_document_paths,
    review_path: plan.review_path,
    review_sha256: plan.review_sha256,
    plans: plan.plans,
    evidence: plan.evidence,
    decision: plan.decision.decision,
    rationale: plan.decision.rationale,
    projection: plan.decision.projection,
    findings: plan.decision.findings,
    start_scope: plan.decision.start_scope,
    conditions: plan.decision.conditions,
  };
  admission.admission_digest = hashBytes(JSON.stringify(admission));
  return admission;
}

export async function captureVerification(options) {
  return captureVerificationCore({ ...options, executeArgv: options.executeArgv ?? executeArgvNode });
}
/** Internal/evaluator helper. Not exposed by the OMP Ready public tool surface. */
export function sealVerificationVerdict(options) {
  return sealVerificationVerdictCore(options);
}


export async function finalizeVerification(options) {
  return finalizeVerificationCore({ ...options, executeArgv: options.executeArgv ?? executeArgvNode });
}

export { BOUNDARY_PROTOCOL, bindAuthority, checkAuthorityCurrentness, hashBytes, validateTicket } from "./authority-binding.js";
export { bindPlanReview, checkPlanCurrentness } from "./plan-binding.js";
export { checkVerificationCurrentness, readVerificationBinding, readVerificationVerdict, snapshotStableTargets } from "./verification-binding.js";
export { ticketStatus, readyCandidate, doneReadyCandidate } from "./finalization.js";
