import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

import { bindAuthority, checkAuthorityCurrentness, isInsideProject, validateTicketWith } from "./authority-binding.js";
import {
  MAX_OBSERVATION_OUTPUT_BYTES,
  prepareObservation,
  recordObservationResult,
} from "./observation-ledger.js";
import { isReadOnlyArgv, parseSimpleReadOnlyCommand, runArgv, validateInspectRequest, validateMutationRequest } from "./argv-policy.js";
import { inventoryAllowedForPhase, isBroadInventory } from "./inventory-policy.js";
import { ReadyLifecycle } from "./lifecycle.js";
import {
  assertAcceptanceEvidenceBinding,
  buildEvidenceFingerprint,
  dependencyProvenance,
  environmentTaint,
  fileDigest,
  productionPathProvenance,
  revalidateEvidenceFingerprint,
  resolveAcceptanceRunner,
  resolveEvidencePath,
  scanFileGraph,
  scanProspectiveMutation,
} from "./no-mock-policy.js";
import { classifyError } from "./retry-policy.js";
import { ManagedServiceRegistry } from "./service-supervisor.js";
import { RuntimeStore, stableDigest } from "./state-store.js";
import { buildExactToolMap, mappedPolicy } from "./tool-map.js";

const INTERNAL_TOOLS = new Set(["ready_guard", "ready_argv", "ready_service", "ready_verify_guard"]);
const ACCEPTANCE_PROVENANCE_KINDS = new Set(["LOCAL_PATH", "LOCAL_SQLITE", "EXTERNAL_HTTP_PROVIDER"]);
const EXTERNAL_PROVIDER_CORRELATION_ERROR = "external provider execution correlation is unsupported by the ready runtime";

function sessionId(ctx) {
  const id = ctx?.sessionManager?.getSessionId?.();
  if (!id) throw new Error("Ready runtime requires an explicit OMP session id");
  return id;
}

function resultText(value, details = undefined) {
  return {
    content: [{ type: "text", text: typeof value === "string" ? value : JSON.stringify(value, null, 2) }],
    details,
  };
}

function runtimeView(state) {
  if (!state) return null;
  return {
    execution_id: state.execution_id,
    execution_mode: state.execution_mode,
    phase: state.phase,
    project_root: state.project_root,
    ticket_path: state.ticket_path,
    mutation_revision: state.mutation_revision,
    latest_evidence_revision: state.latest_evidence_revision,
    checkpoint_state: state.checkpoint_state,
    authority_drift: state.authority_drift,
    mutation_uncertainty: state.uncertainty
      ? { tool_call_id: state.uncertainty.tool_call_id, detail: state.uncertainty.detail, resolution: state.uncertainty.resolution ?? null }
      : null,
    managed_service: state.managed_service ? { pid: state.managed_service.pid, argv: state.managed_service.argv } : null,
    verification_verdict: state.verification_verdict ?? null,
    zero_mock: {
      violations: state.zero_mock?.violations?.length ?? 0,
      touched_paths: state.zero_mock?.touched_paths?.length ?? 0,
      self_check_paths: state.zero_mock?.self_check_paths?.length ?? 0,
      observed_paths: state.zero_mock?.observed_paths?.length ?? 0,
      acceptance_provenance: state.zero_mock?.acceptance_provenance?.length ?? 0,
      inspection_provenance: state.zero_mock?.inspection_provenance?.length ?? 0,
    },
  };
}

function isReadySkillRead(event) {
  if (event?.toolName !== "read") return false;
  const raw = String(event?.input?.path ?? "");
  if (/^skill:\/\/ready-ticket-implement(?=[:/]|$)/.test(raw)) return true;
  const normalized = raw.replace(/\\/g, "/").replace(/:[0-9]+(?:-[0-9]+)?$/, "");
  return normalized.endsWith("/ready-ticket-implement/SKILL.md");
}

function isReadyVerifySkillRead(event) {
  if (event?.toolName !== "read") return false;
  const raw = String(event?.input?.path ?? "");
  if (/^skill:\/\/ready-ticket-verify(?=[:/]|$)/.test(raw)) return true;
  const normalized = raw.replace(/\\/g, "/").replace(/:[0-9]+(?:-[0-9]+)?$/, "");
  return normalized.endsWith("/ready-ticket-verify/SKILL.md");
}

function nearestExistingCanonical(absolutePath) {
  let cursor = absolutePath;
  const suffix = [];
  while (!fs.existsSync(cursor)) {
    const parent = path.dirname(cursor);
    if (parent === cursor) return absolutePath;
    suffix.unshift(path.basename(cursor));
    cursor = parent;
  }
  const base = fs.realpathSync(cursor);
  return path.join(base, ...suffix);
}

function resolveToolPath(rawPath, cwd) {
  if (typeof rawPath !== "string" || rawPath.length === 0) return null;
  if (/^[a-z][a-z0-9+.-]*:\/\//i.test(rawPath)) return rawPath;
  const absolute = path.isAbsolute(rawPath) ? path.resolve(rawPath) : path.resolve(cwd, rawPath);
  return nearestExistingCanonical(absolute);
}

function pathFromEvent(event, cwd) {
  const raw = event?.input?.path;
  return resolveToolPath(raw, cwd);
}

function protectedMutationReason(state, target) {
  if (!target || /^[a-z][a-z0-9+.-]*:\/\//i.test(target)) return null;
  const protectedArtifact = (state.protected_artifacts || []).find(item => item.path === target);
  return protectedArtifact
    ? `Ready runtime blocks mutation of protected ${protectedArtifact.kind} authority: ${target}`
    : null;
}

function projectConfinementReason(state, target) {
  if (!target) return null;
  if (/^[a-z][a-z0-9+.-]*:\/\//i.test(target)) return `Ready runtime blocks non-project URI access during implementation: ${target}`;
  return isInsideProject(state.project_root, target) ? null : `Ready runtime blocks access outside Project Root: ${target}`;
}

function argvConfinementReason(state, argv) {
  for (const value of argv.slice(1)) {
    if (value.startsWith("-")) continue;
    const looksPathLike = path.isAbsolute(value) || value === ".." || value.startsWith(`..${path.sep}`) || value.startsWith("../") || value.startsWith("./");
    if (!looksPathLike) continue;
    const target = nearestExistingCanonical(path.isAbsolute(value) ? path.resolve(value) : path.resolve(state.project_root, value));
    if (!isInsideProject(state.project_root, target)) return `Ready runtime blocks argv access outside Project Root: ${value}`;
  }
  return null;
}

function hashFileMaybe(file) {
  try {
    return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
  } catch {
    return null;
  }
}

function mutationSnapshot(event, cwd) {
  const target = pathFromEvent(event, cwd);
  if (!target || /^[a-z][a-z0-9+.-]*:\/\//i.test(target)) return null;
  const beforeHash = hashFileMaybe(target);
  let expectedHash = null;
  if (event.toolName === "write" && typeof event?.input?.content === "string") {
    expectedHash = crypto.createHash("sha256").update(event.input.content).digest("hex");
  }
  return {
    target_path: target,
    before_hash: beforeHash,
    expected_hash: expectedHash,
    tool_name: event.toolName,
  };
}

function resolveSnapshotOutcome(snapshot) {
  if (!snapshot?.target_path) return "inconclusive";
  const currentHash = hashFileMaybe(snapshot.target_path);
  if (snapshot.expected_hash && currentHash === snapshot.expected_hash) return "applied";
  if (currentHash === snapshot.before_hash) return "not_applied";
  return "inconclusive";
}

function exactReadyDoneProgression(beforeText, afterText) {
  if (typeof beforeText !== "string" || typeof afterText !== "string") return false;
  const matches = beforeText.match(/^Status:\s*ready\s*$/gm) || [];
  if (matches.length !== 1) return false;
  const expected = beforeText.replace(/^Status:\s*ready\s*$/m, "Status: done");
  return afterText === expected;
}

function contentBytes(content) {
  return Buffer.byteLength(
    (content || [])
      .filter(item => item?.type === "text")
      .map(item => String(item.text ?? ""))
      .join("\n"),
    "utf8",
  );
}

function mutationDigestFor(state, toolName, input) {
  return stableDigest({
    mutation_revision: Number(state.mutation_revision ?? 0),
    tool_name: String(toolName).toLowerCase(),
    input,
  });
}

function repeatedMutationReason(state, mutationDigest) {
  const failed = state.last_failed_mutation;
  if (!failed) return null;
  if (
    Number(failed.mutation_revision) === Number(state.mutation_revision ?? 0)
    && failed.mutation_digest === mutationDigest
  ) {
    return "Ready runtime blocks an unchanged repeat of the same deterministic mutation failure; fix the cause or choose a different bounded action.";
  }
  return null;
}

function ensureZeroMockState(state) {
  state.zero_mock ??= {};
  state.zero_mock.violations ??= [];
  state.zero_mock.touched_paths ??= [];
  state.zero_mock.self_check_paths ??= [];
  state.zero_mock.observed_paths ??= [];
  state.zero_mock.observed_evidence ??= {};
  state.zero_mock.acceptance_provenance ??= [];
  state.zero_mock.inspection_provenance ??= [];
  return state.zero_mock;
}

function recordZeroMockViolations(state, violations) {
  const zeroMock = ensureZeroMockState(state);
  const seen = new Set(zeroMock.violations.map(item => `${item.code}|${item.path}|${item.detail}`));
  for (const violation of violations || []) {
    const key = `${violation.code}|${violation.path}|${violation.detail}`;
    if (!seen.has(key)) {
      zeroMock.violations.push(violation);
      seen.add(key);
    }
  }
  return zeroMock.violations;
}

function recordZeroMockPaths(state, field, paths) {
  const zeroMock = ensureZeroMockState(state);
  const values = new Set(zeroMock[field] || []);
  for (const value of paths || []) if (value) values.add(value);
  zeroMock[field] = [...values];
}

function currentZeroMockScan(state) {
  const zeroMock = ensureZeroMockState(state);
  const existingTouched = zeroMock.touched_paths.filter(file => fs.existsSync(file) && fs.statSync(file).isFile());
  const report = scanFileGraph(state.project_root, [...existingTouched, ...zeroMock.self_check_paths]);
  const violations = [...report.violations, ...environmentTaint()];
  recordZeroMockViolations(state, violations);
  return { ...report, violations, mock_taint: violations.length > 0 || zeroMock.violations.length > 0 };
}

function recordInspectionEvidence(state, params) {
  if (!params.production_entrypoint || !params.authoritative_readback_path) {
    throw new Error("direct inspection admission requires production_entrypoint and authoritative_readback_path");
  }
  const productionResult = productionPathProvenance(
    state.project_root,
    [params.production_entrypoint],
    params.production_entrypoint,
  );
  const production = productionResult.production_entrypoint;
  const readback = resolveEvidencePath(state.project_root, params.authoritative_readback_path, "authoritative readback path");
  const zeroMock = ensureZeroMockState(state);
  const observed = zeroMock.observed_evidence?.[readback];
  if (
    !observed
    || observed.mutation_revision !== Number(state.mutation_revision ?? 0)
    || observed.sha256 !== fileDigest(readback)
  ) {
    throw new Error("direct inspection admission requires a current successful runtime read of the unchanged authoritative readback path");
  }
  const dependencies = Array.isArray(params.dependency_paths) && params.dependency_paths.length > 0
    ? dependencyProvenance(state.project_root, params.dependency_paths)
    : [];
  const scan = scanFileGraph(state.project_root, [production, readback, ...dependencies.map(item => item.path)]);
  const violations = [
    ...environmentTaint(),
    ...productionResult.violations,
    ...scan.violations,
    ...dependencyUsageViolations(scan.referenced_paths, dependencies),
  ];
  recordZeroMockPaths(state, "self_check_paths", [production, readback, ...dependencies.map(item => item.path)]);
  recordZeroMockViolations(state, violations);
  if (violations.length > 0) {
    throw new Error(`Zero-Mock direct inspection is tainted or unproven: ${violations.map(item => item.code).join(", ")}`);
  }
  const fingerprint = buildEvidenceFingerprint({
    projectRoot: state.project_root,
    mutationRevision: Number(state.mutation_revision ?? 0),
    provenanceKind: "LOCAL_PATH",
    productionEntrypoint: production,
    evidenceRootPaths: [production, readback, ...dependencies.map(item => item.path)],
    dependencyPaths: dependencies.map(item => item.path),
    authoritativeReadback: {
      available: true,
      kind: "path",
      path: readback,
      sha256: observed.sha256,
    },
    resolvedRunner: {
      runner: "direct-inspection",
      command_argv: [],
      resolved_argv: [],
      package_script: null,
      package_json: null,
    },
  });
  const provenance = {
    status: "PASSED",
    provenance_kind: "LOCAL_PATH",
    production_entrypoint: production,
    dependencies,
    authoritative_readback: {
      available: true,
      kind: "path",
      path: readback,
      sha256: fileDigest(readback),
    },
    fingerprint,
    mock_taint: false,
    mutation_revision: Number(state.mutation_revision ?? 0),
    recorded_at: new Date().toISOString(),
  };
  ensureZeroMockState(state).inspection_provenance.push(provenance);
  return provenance;
}

function isNominallyCleanProvenance(item) {
  return item?.status === "PASSED"
    && item.mock_taint === false
    && item.authoritative_readback?.available === true;
}

async function revalidateCleanProvenance(state, records, signal) {
  for (const provenance of records) {
    await revalidateEvidenceFingerprint({
      projectRoot: state.project_root,
      mutationRevision: Number(state.mutation_revision ?? 0),
      provenance,
      signal,
    });
  }
}

function prospectiveZeroMockReason(event, target) {
  if (!target) return null;
  const violations = scanProspectiveMutation(event.input, target);
  if (violations.length === 0) return null;
  return `Zero-Mock Delivery blocked mutation before execution: ${violations.map(item => item.code).join(", ")}`;
}

function unverifiableCustomToolReason(pi, toolName) {
  const matches = (pi.getAllTools?.() || []).filter(tool => tool?.name === toolName);
  const unverifiable = matches.find(tool => ["mcp", "extension", "sdk"].includes(tool?.sourceInfo?.source));
  return unverifiable
    ? `Zero-Mock Delivery blocks custom/MCP tool without verifiable execution provenance: ${toolName}`
    : null;
}

function projectRootFromTicket(ticketPath) {
  const text = fs.readFileSync(ticketPath, "utf8");
  const match = text.match(/^Project-Root:\s*(.+?)\s*$/m);
  if (!match) throw new Error("Ticket Project-Root metadata is missing");
  return match[1].trim();
}

function dependencyUsageViolations(referencedPaths, dependencies) {
  const referenced = new Set(referencedPaths);
  const implicitRunnerConfig = new Set(["package.json", "pyproject.toml", "setup.cfg", "tox.ini"]);
  return dependencies.flatMap(item => {
    if (implicitRunnerConfig.has(path.basename(item.path))) return [];
    if (referenced.has(item.path)) return [];
    return [{
      code: "DEPENDENCY_PATH_UNPROVEN",
      path: item.path,
      detail: `declared dependency/config is not structurally referenced by the production/evidence closure: ${item.path}`,
    }];
  });
}

function acceptanceTestPaths(projectRoot, rawPaths) {
  if (!Array.isArray(rawPaths) || rawPaths.length === 0) throw new Error("ready_argv acceptance requires evidence_paths");
  return rawPaths.map(raw => resolveEvidencePath(projectRoot, raw, "acceptance evidence path"));
}

async function runAcceptanceEvidence({ lifecycle, store, state, params, signal }) {
  if (!["ACTIVE", "VERIFY_ACTIVE"].includes(state.phase)) {
    throw new Error(`ready_argv acceptance is unavailable in phase ${state.phase}`);
  }
  if (!ACCEPTANCE_PROVENANCE_KINDS.has(params.provenance_kind)) {
    throw new Error(`ready_argv acceptance requires provenance_kind to be exactly one of LOCAL_PATH, LOCAL_SQLITE, EXTERNAL_HTTP_PROVIDER; received ${String(params.provenance_kind)}`);
  }
  const runner = resolveAcceptanceRunner(params.argv, state.project_root);
  const evidencePaths = acceptanceTestPaths(state.project_root, params.evidence_paths);
  assertAcceptanceEvidenceBinding(state.project_root, runner, evidencePaths);
  const production = productionPathProvenance(state.project_root, evidencePaths, params.production_entrypoint);
  const dependencies = dependencyProvenance(state.project_root, params.dependency_paths);
  const dependencyPaths = dependencies.map(item => item.path);
  const scan = scanFileGraph(state.project_root, [...evidencePaths, production.production_entrypoint, ...dependencyPaths]);
  const violations = [
    ...environmentTaint(),
    ...production.violations,
    ...scan.violations,
    ...dependencyUsageViolations(scan.referenced_paths, dependencies),
  ];
  recordZeroMockPaths(state, "self_check_paths", [...evidencePaths, production.production_entrypoint, ...dependencyPaths]);
  recordZeroMockViolations(state, violations);
  store.writeExecution(state);
  if (violations.length > 0) {
    throw new Error(`Zero-Mock acceptance blocked by mock-tainted or unproven evidence: ${violations.map(item => item.code).join(", ")}`);
  }
  const hasReadbackPath = typeof params.authoritative_readback_path === "string" && params.authoritative_readback_path.length > 0;
  const hasReadbackArgv = Array.isArray(params.readback_argv) && params.readback_argv.length > 0;
  if (!hasReadbackPath && !hasReadbackArgv) {
    throw new Error("ready_argv acceptance requires authoritative_readback_path or readback_argv");
  }
  if (hasReadbackArgv && !isReadOnlyArgv(params.readback_argv)) {
    throw new Error("authoritative readback argv must be on the structured read-only allowlist");
  }
  let readbackBeforeDigest = null;
  if (hasReadbackPath) {
    const absolute = path.isAbsolute(params.authoritative_readback_path)
      ? path.resolve(params.authoritative_readback_path)
      : path.resolve(state.project_root, params.authoritative_readback_path);
    if (!isInsideProject(state.project_root, absolute)) {
      throw new Error(`authoritative readback path is outside Project Root: ${absolute}`);
    }
    if (params.provenance_kind !== "EXTERNAL_HTTP_PROVIDER" && fs.existsSync(absolute) && fs.statSync(absolute).isFile()) {
      readbackBeforeDigest = fileDigest(absolute);
    }
  }
  if (params.provenance_kind === "EXTERNAL_HTTP_PROVIDER") {
    const current = lifecycle.status(state.execution_id);
    const authoritativeReadback = {
      available: false,
      kind: "external_provider_execution_correlation_unsupported",
      error: EXTERNAL_PROVIDER_CORRELATION_ERROR,
    };
    ensureZeroMockState(current).acceptance_provenance.push({
      provenance_kind: params.provenance_kind,
      command: params.argv,
      runner,
      mutation_revision: Number(current.mutation_revision ?? 0),
      production_entrypoint: production.production_entrypoint,
      dependencies,
      evidence_paths: evidencePaths,
      authoritative_readback: authoritativeReadback,
      fingerprint: null,
      mock_taint: false,
      status: "INCONCLUSIVE",
      exit_code: null,
      timed_out: false,
      recorded_at: new Date().toISOString(),
    });
    store.writeExecution(current);
    return {
      status: "INCONCLUSIVE",
      provenance_kind: params.provenance_kind,
      runner,
      command: params.argv,
      production_entrypoint: production.production_entrypoint,
      dependencies,
      authoritative_readback: authoritativeReadback,
      fingerprint: null,
      mock_taint: false,
      exit_code: null,
      timed_out: false,
      stdout: "",
      stderr: "",
    };
  }
  const preExecutionDigests = new Map(
    scan.scanned_paths
      .filter(file => fs.existsSync(file) && fs.statSync(file).isFile())
      .map(file => [file, fileDigest(file)]),
  );

  const syntheticId = `ready-acceptance-${crypto.randomUUID()}`;
  lifecycle.beginOperation(state.execution_id, { toolCallId: syntheticId, kind: "observation" });
  let testResult;
  try {
    testResult = await runArgv(params.argv, { cwd: state.project_root, signal });
  } catch (error) {
    lifecycle.finishOperation(state.execution_id, syntheticId, { mutationApplied: false });
    throw error;
  }

  const changedEvidence = [];
  for (const [file, beforeDigest] of preExecutionDigests.entries()) {
    let afterDigest = null;
    try {
      afterDigest = fileDigest(file);
    } catch {
      afterDigest = null;
    }
    if (afterDigest !== beforeDigest) {
      changedEvidence.push({
        code: "ACCEPTANCE_EVIDENCE_MUTATION",
        path: file,
        detail: "acceptance runner modified a production/test/config provenance input",
      });
    }
  }
  const postScan = scanFileGraph(state.project_root, [...evidencePaths, production.production_entrypoint, ...dependencyPaths]);
  const postViolations = [...changedEvidence, ...postScan.violations];
  if (postViolations.length > 0) {
    const current = lifecycle.status(state.execution_id);
    recordZeroMockViolations(current, postViolations);
    store.writeExecution(current);
    lifecycle.finishOperation(state.execution_id, syntheticId, { mutationApplied: false });
    throw new Error(`Zero-Mock acceptance invalidated its own evidence inputs: ${postViolations.map(item => item.code).join(", ")}`);
  }

  let authoritativeReadback = { available: false };
  if (testResult.exitCode === 0 && !testResult.timedOut) {
    if (params.authoritative_readback_path) {
      try {
        const readbackPath = resolveEvidencePath(state.project_root, params.authoritative_readback_path, "authoritative readback path");
        const reserved = new Set([...evidencePaths, ...dependencyPaths]);
        if (reserved.has(readbackPath)) throw new Error("authoritative readback must be distinct from test/config provenance inputs");
        const afterDigest = fileDigest(readbackPath);
        const referenced = scan.referenced_paths.includes(readbackPath);
        const producedOrChanged = readbackBeforeDigest === null || readbackBeforeDigest !== afterDigest;
        if (!referenced && !producedOrChanged) {
          throw new Error("authoritative readback path is not attributable to the production/evidence execution");
        }
        authoritativeReadback = {
          available: true,
          kind: "path",
          path: readbackPath,
          sha256: afterDigest,
          attribution: referenced ? "referenced_by_execution_closure" : "created_or_changed_by_execution",
        };
      } catch (error) {
        authoritativeReadback = { available: false, kind: "path", error: String(error?.message ?? error) };
      }
    } else if (hasReadbackArgv) {
      try {
        const readbackResult = await runArgv(params.readback_argv, { cwd: state.project_root, signal });
        authoritativeReadback = {
          available: readbackResult.exitCode === 0 && !readbackResult.timedOut,
          kind: "argv",
          argv: params.readback_argv,
          exit_code: readbackResult.exitCode,
          stdout_sha256: crypto.createHash("sha256").update(readbackResult.stdout).digest("hex"),
          timed_out: readbackResult.timedOut,
        };
      } catch (error) {
        authoritativeReadback = {
          available: false,
          kind: "argv",
          argv: params.readback_argv,
          error: String(error?.message ?? error),
        };
      }
    }
  }

  const status = testResult.exitCode === 0 && !testResult.timedOut && authoritativeReadback.available ? "PASSED"
    : testResult.exitCode === 0 && !testResult.timedOut ? "INCONCLUSIVE"
      : "FAILED";
  const current = lifecycle.status(state.execution_id);
  let fingerprint = null;
  if (status === "PASSED") {
    try {
      fingerprint = buildEvidenceFingerprint({
        projectRoot: current.project_root,
        mutationRevision: Number(current.mutation_revision ?? 0),
        provenanceKind: params.provenance_kind,
        productionEntrypoint: production.production_entrypoint,
        evidenceRootPaths: evidencePaths,
        dependencyPaths,
        authoritativeReadback,
        resolvedRunner: runner,
      });
    } catch (error) {
      lifecycle.finishOperation(state.execution_id, syntheticId, { mutationApplied: false });
      throw new Error(`Zero-Mock acceptance fingerprint failed closed: ${error.message}`);
    }
  }
  ensureZeroMockState(current).acceptance_provenance.push({
    provenance_kind: params.provenance_kind,
    command: params.argv,
    runner,
    mutation_revision: Number(current.mutation_revision ?? 0),
    production_entrypoint: production.production_entrypoint,
    dependencies,
    evidence_paths: evidencePaths,
    authoritative_readback: authoritativeReadback,
    fingerprint,
    mock_taint: false,
    status,
    exit_code: testResult.exitCode,
    timed_out: testResult.timedOut,
    recorded_at: new Date().toISOString(),
  });
  store.writeExecution(current);
  lifecycle.finishOperation(state.execution_id, syntheticId, { mutationApplied: false });
  if (status === "PASSED") lifecycle.noteCurrentEvidence(state.execution_id, current.mutation_revision);
  return {
    status,
    provenance_kind: params.provenance_kind,
    runner,
    command: params.argv,
    production_entrypoint: production.production_entrypoint,
    dependencies,
    authoritative_readback: authoritativeReadback,
    mock_taint: false,
    stdout: testResult.stdout.slice(0, MAX_OBSERVATION_OUTPUT_BYTES),
    stderr: testResult.stderr.slice(0, MAX_OBSERVATION_OUTPUT_BYTES),
  };
}

function maybeRewritePath(event, target) {
  if (!target || /^[a-z][a-z0-9+.-]*:\/\//i.test(target)) return undefined;
  if (!["read", "write", "grep", "glob"].includes(event.toolName)) return undefined;
  if (typeof event?.input?.path !== "string" || event.input.path === target) return undefined;
  return { ...event.input, path: target };
}

function targetMatchesDrift(state, event, cwd) {
  if (event.toolName !== "read") return false;
  const target = pathFromEvent(event, cwd);
  return Boolean(target && state.authority_drift?.changed?.some(item => item.path === target));
}

async function authorityGate(lifecycle, state, event, cwd) {
  const currentness = await lifecycle.checkAuthorityCurrentness(state);
  if (currentness.current) return { allowed: true, state };
  if (!["AUTHORITY_REVIEW_REQUIRED", "MATERIAL_TURN_REQUIRED", "VERIFY_AUTHORITY_REVIEW_REQUIRED"].includes(state.phase)) {
    state = lifecycle.markAuthorityDrift(state.execution_id, currentness.changed);
  }
  if (targetMatchesDrift(state, event, cwd)) return { allowed: true, state, reviewRead: true };
  return {
    allowed: false,
    state,
    reason: state.execution_mode === "SUBAGENT"
      ? "Ready authority changed. Re-read the changed authority and issue MATERIAL_TURN before further guarded work."
      : state.execution_mode === "VERIFY"
        ? "Ready verification authority changed. Re-read the changed authority, resolve the verifier material turn, and call ready_verify_guard begin again to rebind."
        : "Ready authority changed. Re-read the changed authority and call begin_direct again to rebind before further guarded work.",
  };
}

function requireWorkerExecution(lifecycle, sid) {
  const session = lifecycle.sessionState(sid);
  if (!session?.execution_id) throw new Error("current session has no bound Ready execution");
  if (!new Set(["worker", "verifier"]).has(session.role)) {
    throw new Error("current session is the SUBAGENT parent and may not execute guarded Ready argv");
  }
  const state = lifecycle.status(session.execution_id);
  if (state.session_id !== sid) throw new Error("current session does not own the bound Ready execution");
  return state;
}

function isAcceptanceCommand(argv, projectRoot) {
  try {
    resolveAcceptanceRunner(argv, projectRoot);
    return true;
  } catch {
    return false;
  }
}

function validateExplicitTargets(state, targets) {
  if (!Array.isArray(targets) || targets.length === 0) throw new Error("ready_argv mutate requires explicit target_paths");
  const resolved = targets.map(raw => resolveToolPath(raw, state.project_root));
  for (const target of resolved) {
    const confinement = projectConfinementReason(state, target);
    if (confinement) throw new Error(confinement);
    const protectedReason = protectedMutationReason(state, target);
    if (protectedReason) throw new Error(protectedReason);
  }
  return resolved;
}

export function installReadyRuntime(pi, options = {}) {
  const store = options.store ?? new RuntimeStore(options.dataRoot);
  const lifecycle = options.lifecycle ?? new ReadyLifecycle({
    store,
    bindAuthority: options.bindAuthority ?? bindAuthority,
    checkAuthorityCurrentness: options.checkAuthorityCurrentness ?? checkAuthorityCurrentness,
  });
  const services = options.services ?? new ManagedServiceRegistry({ lifecycle });
  const readySkillDir = options.readySkillDir;
  const operationIndex = new Map();
  let toolMap = { mapped: {}, boundaries: [], customMutationBoundary: [] };
  let toolMapInitialized = false;

  const refreshToolMap = () => {
    toolMap = buildExactToolMap(pi);
    toolMapInitialized = true;
    return toolMap;
  };

  pi.on("resources_discover", async () => {
    refreshToolMap();
    return readySkillDir ? { skillPaths: [readySkillDir] } : {};
  });
  const refreshSessionRuntime = ctx => {
    refreshToolMap();
    lifecycle.recoverInterruptedOperation(sessionId(ctx));
  };
  pi.on("session_start", async (_event, ctx) => {
    refreshSessionRuntime(ctx);
  });
  pi.on("session_switch", async (_event, ctx) => {
    refreshSessionRuntime(ctx);
  });
  pi.on("session_branch", async (_event, ctx) => {
    refreshSessionRuntime(ctx);
  });

  pi.on("tool_call", async (event, ctx) => {
    if (!toolMapInitialized) refreshToolMap();
    const sid = sessionId(ctx);
    if (isReadySkillRead(event)) {
      lifecycle.armSession(sid, "IMPLEMENT");
      return;
    }
    if (isReadyVerifySkillRead(event)) {
      lifecycle.armSession(sid, "VERIFY");
      return;
    }
    if (INTERNAL_TOOLS.has(event.toolName)) return;

    const session = lifecycle.sessionState(sid);
    if (!session?.armed) return;
    const policy = mappedPolicy(toolMap, event.toolName);
    if (!policy) {
      if (session.execution_id) {
        const reason = unverifiableCustomToolReason(pi, event.toolName);
        if (reason) return { block: true, reason };
      }
      return;
    }

    let effectivePolicy = policy;
    let normalizedObservationInput = event.input;
    if (policy === "dynamic") {
      const argv = parseSimpleReadOnlyCommand(event?.input?.command);
      if (!argv) {
        return {
          block: true,
          reason: "Ready runtime does not guess Bash mutation semantics. Use ready_argv inspect for read-only argv or ready_argv mutate with explicit target_paths.",
        };
      }
      effectivePolicy = "observation";
      normalizedObservationInput = { argv };
    }

    if (!session.execution_id) {
      if (effectivePolicy === "mutation") {
        return { block: true, reason: "ready-ticket-implement is ARMED but ready_guard begin has not bound the exact Ticket yet." };
      }
      return;
    }

    const state = lifecycle.status(session.execution_id);
    if (session.role === "parent") {
      if (effectivePolicy === "mutation") return { block: true, reason: "SUBAGENT parent session may not mutate implementation source." };
      return;
    }
    if (state.session_id !== sid) return { block: true, reason: "Ready execution/session binding mismatch." };
    const verifierMode = session.role === "verifier" && state.execution_mode === "VERIFY";

    if (state.phase === "MUTATION_UNCERTAIN") {
      const snapshot = state.uncertainty?.operation?.mutation_snapshot;
      const target = pathFromEvent(event, ctx.cwd);
      if (event.toolName === "read" && snapshot?.target_path === target) {
        operationIndex.set(event.toolCallId, { executionId: state.execution_id, kind: "uncertainty_readback", sessionId: sid });
        return maybeRewritePath(event, target) ? { input: maybeRewritePath(event, target) } : undefined;
      }
      return { block: true, reason: "Ready mutation outcome is uncertain; only exact target readback or terminal BLOCKED is allowed." };
    }

    const authority = await authorityGate(lifecycle, state, event, ctx.cwd);
    if (!authority.allowed) return { block: true, reason: authority.reason };
    if (authority.reviewRead) {
      const target = pathFromEvent(event, ctx.cwd);
      const rewritten = maybeRewritePath(event, target);
      return rewritten ? { input: rewritten } : undefined;
    }

    const current = lifecycle.status(state.execution_id);
    if (effectivePolicy === "mutation") {
      if (verifierMode) {
        const verifierTarget = pathFromEvent(event, ctx.cwd);
        if (current.phase !== "VERIFY_VERIFIED_ADMITTED" || verifierTarget !== current.ticket_path || current.verification_progression_used) {
          return { block: true, reason: "Zero-Mock verifier runtime is read-only except for one admitted exact Ticket ready-to-done progression." };
        }
      } else if (current.phase !== "ACTIVE") {
        return { block: true, reason: `Ready runtime blocks source mutation in phase ${current.phase}.` };
      }
    }
    if (current.active_operation) {
      return { block: true, reason: `Ready execution already has active guarded operation ${current.active_operation.tool_call_id}.` };
    }

    const target = pathFromEvent(event, ctx.cwd);
    if (target) {
      const confinement = projectConfinementReason(current, target);
      if (confinement) return { block: true, reason: confinement };
      if (effectivePolicy === "mutation") {
        if (!(verifierMode && target === current.ticket_path)) {
          const protectedReason = protectedMutationReason(current, target);
          if (protectedReason) return { block: true, reason: protectedReason };
        }
        const zeroMockReason = prospectiveZeroMockReason(event, target);
        if (zeroMockReason) return { block: true, reason: zeroMockReason };
      }
    }
    if (policy === "dynamic") {
      const argvReason = argvConfinementReason(current, normalizedObservationInput.argv);
      if (argvReason) return { block: true, reason: argvReason };
    }

    if (effectivePolicy === "observation") {
      const broad = isBroadInventory(event.toolName === "bash" ? "bash" : event.toolName, normalizedObservationInput);
      const inventory = inventoryAllowedForPhase(current, broad);
      if (!inventory.allowed) return { block: true, reason: inventory.reason };
      const prepared = prepareObservation(current, event.toolName, normalizedObservationInput, broad);
      if (!prepared.allowed) return { block: true, reason: prepared.reason };
      store.writeExecution(current);
      lifecycle.beginOperation(current.execution_id, {
        toolCallId: event.toolCallId,
        kind: "observation",
        observationDigest: prepared.digest,
      });
      operationIndex.set(event.toolCallId, {
        executionId: current.execution_id,
        kind: "observation",
        observationDigest: prepared.digest,
        targetPath: target,
        sessionId: sid,
      });
    } else {
      const mutationDigest = mutationDigestFor(current, event.toolName, event.input);
      const repeatedReason = repeatedMutationReason(current, mutationDigest);
      if (repeatedReason) return { block: true, reason: repeatedReason };
      const snapshot = mutationSnapshot(event, ctx.cwd);
      lifecycle.beginOperation(current.execution_id, {
        toolCallId: event.toolCallId,
        kind: "mutation",
        mutationSnapshot: snapshot,
        mutationDigest,
      });
      operationIndex.set(event.toolCallId, {
        executionId: current.execution_id,
        kind: "mutation",
        mutationDigest,
        targetPath: target,
        verifierProgression: verifierMode && target === current.ticket_path,
        verifierProgressionBeforeText: verifierMode && target === current.ticket_path && fs.existsSync(target)
          ? fs.readFileSync(target, "utf8")
          : null,
        sessionId: sid,
      });
    }

    const rewritten = maybeRewritePath(event, target);
    return rewritten ? { input: rewritten } : undefined;
  });

  pi.on("tool_result", async (event, ctx) => {
    const tracked = operationIndex.get(event.toolCallId);
    if (!tracked) return;
    if (tracked.sessionId && tracked.sessionId !== sessionId(ctx)) return;
    operationIndex.delete(event.toolCallId);

    if (tracked.kind === "uncertainty_readback") {
      const state = lifecycle.status(tracked.executionId);
      const snapshot = state.uncertainty?.operation?.mutation_snapshot;
      const outcome = event.isError ? "inconclusive" : resolveSnapshotOutcome(snapshot);
      lifecycle.resolveMutationUncertainty(tracked.executionId, outcome);
      return;
    }

    if (tracked.kind === "observation") {
      const state = lifecycle.status(tracked.executionId);
      const bytes = contentBytes(event.content);
      const classification = event.isError ? classifyError(event.content) : null;
      recordObservationResult(state, tracked.observationDigest, {
        success: !event.isError,
        outputBytes: bytes,
        errorClassification: classification,
        incomplete: bytes > MAX_OBSERVATION_OUTPUT_BYTES,
      });
      if (!event.isError && tracked.targetPath && !/^[a-z][a-z0-9+.-]*:\/\//i.test(tracked.targetPath)) {
        recordZeroMockPaths(state, "observed_paths", [tracked.targetPath]);
        if (fs.existsSync(tracked.targetPath) && fs.statSync(tracked.targetPath).isFile()) {
          ensureZeroMockState(state).observed_evidence[tracked.targetPath] = {
            sha256: fileDigest(tracked.targetPath),
            mutation_revision: Number(state.mutation_revision ?? 0),
            observed_at: new Date().toISOString(),
          };
        }
      }
      store.writeExecution(state);
      lifecycle.finishOperation(tracked.executionId, event.toolCallId, { mutationApplied: false });
      return;
    }

    const state = lifecycle.status(tracked.executionId);
    if (!event.isError) {
      const finished = lifecycle.finishOperation(tracked.executionId, event.toolCallId, { mutationApplied: true });
      if (tracked.targetPath) {
        recordZeroMockPaths(finished, "touched_paths", [tracked.targetPath]);
        if (fs.existsSync(tracked.targetPath) && fs.statSync(tracked.targetPath).isFile()) {
          const scan = scanFileGraph(finished.project_root, [tracked.targetPath]);
          recordZeroMockViolations(finished, scan.violations);
        }
      }
      if (tracked.verifierProgression) {
        const afterText = fs.existsSync(tracked.targetPath) ? fs.readFileSync(tracked.targetPath, "utf8") : null;
        finished.verification_progression_used = true;
        finished.verification_progression_exact = exactReadyDoneProgression(
          tracked.verifierProgressionBeforeText,
          afterText,
        );
      }
      store.writeExecution(finished);
      return;
    }
    if (tracked.targetPath) {
      recordZeroMockPaths(state, "touched_paths", [tracked.targetPath]);
      if (fs.existsSync(tracked.targetPath) && fs.statSync(tracked.targetPath).isFile()) {
        recordZeroMockViolations(state, scanFileGraph(state.project_root, [tracked.targetPath]).violations);
      }
      store.writeExecution(state);
    }
    const classification = classifyError(event.content);
    if (classification === "TRANSPORT_NETWORK") {
      const uncertain = lifecycle.markMutationUncertain(tracked.executionId, event.toolCallId, "mutation-capable tool returned transport/network failure");
      const snapshot = uncertain.uncertainty?.operation?.mutation_snapshot;
      const outcome = resolveSnapshotOutcome(snapshot);
      if (outcome !== "inconclusive") lifecycle.resolveMutationUncertainty(tracked.executionId, outcome);
      return;
    }
    lifecycle.finishOperation(tracked.executionId, event.toolCallId, {
      mutationApplied: false,
      failureClassification: classification,
      failureDetail: JSON.stringify(event.content),
    });
  });

  pi.on("session_shutdown", async (_event, ctx) => {
    const sid = sessionId(ctx);
    await services.cleanupSession(sid);
    const session = lifecycle.sessionState(sid);
    if (session?.assignment_id && !session.execution_id) {
      const assignment = store.readAssignment(session.assignment_id);
      if (assignment?.status === "issued" && assignment.parent_session_id === sid) {
        lifecycle.blockAssignment(assignment.assignment_id, sid, "parent session shutdown before delegated execution began");
      }
      return;
    }
    if (!session?.execution_id) return;
    const state = store.readExecution(session.execution_id);
    if (!state?.active_operation || state.session_id !== sid) return;
    if (state.active_operation.kind === "mutation") {
      lifecycle.markMutationUncertain(
        state.execution_id,
        state.active_operation.tool_call_id,
        "session shutdown interrupted an active mutation",
      );
    } else {
      const digest = state.active_operation.observation_digest;
      if (digest) {
        recordObservationResult(state, digest, {
          success: false,
          outputBytes: 0,
          incomplete: true,
        });
        store.writeExecution(state);
      }
      lifecycle.finishOperation(state.execution_id, state.active_operation.tool_call_id, { mutationApplied: false });
    }
  });

  const z = pi.zod;
  pi.registerTool({
    name: "ready_guard",
    label: "Ready Guard",
    description: "Bind and advance the internal ready-ticket-implement runtime without changing its external delivery contract.",
    parameters: z.object({
      action: z.enum([
        "begin_direct", "assign_subagent", "begin_delegated", "checkpoint_pre_action", "checkpoint_material_turn",
        "release_checkpoint", "complete", "block", "status",
      ]),
      ticket_path: z.string().optional(),
      project_root: z.string().optional(),
      assignment_id: z.string().optional(),
      execution_id: z.string().optional(),
      decision: z.enum(["CONTINUE", "STEER", "STOP"]).optional(),
      summary: z.string().optional(),
      reason: z.string().optional(),
    }),
    async execute(_toolCallId, params, _signal, _onUpdate, ctx) {
      const sid = sessionId(ctx);
      let value;
      switch (params.action) {
        case "begin_direct":
          value = await lifecycle.beginDirect({ sessionId: sid, projectRoot: params.project_root, ticketPath: params.ticket_path });
          return resultText(runtimeView(value));
        case "assign_subagent":
          value = await lifecycle.assignSubagent({ parentSessionId: sid, projectRoot: params.project_root, ticketPath: params.ticket_path });
          return resultText({
            assignment_id: value.assignment_id,
            ticket_path: value.ticket_path,
            project_root: value.project_root,
            status: value.status,
          });
        case "begin_delegated":
          value = await lifecycle.beginDelegated({ childSessionId: sid, assignmentId: params.assignment_id });
          return resultText(runtimeView(value));
        case "checkpoint_pre_action":
          value = lifecycle.checkpointPreAction(params.execution_id, sid, params.summary ?? null);
          return resultText(runtimeView(value));
        case "checkpoint_material_turn": {
          const before = lifecycle.status(params.execution_id);
          if (before.phase === "MATERIAL_TURN_REQUIRED") await lifecycle.refreshDelegatedAuthority(params.execution_id, sid);
          value = lifecycle.checkpointMaterialTurn(params.execution_id, sid, params.summary ?? null);
          return resultText(runtimeView(value));
        }
        case "release_checkpoint":
          value = lifecycle.releaseCheckpoint(params.execution_id, sid, params.decision);
          return resultText(runtimeView(value));
        case "complete": {
          const execution = lifecycle.status(params.execution_id);
          if (execution.managed_service) await services.stop(execution.execution_id, sid);
          const scan = currentZeroMockScan(execution);
          const provenance = execution.zero_mock?.acceptance_provenance || [];
          const badProvenance = provenance.filter(item => !isNominallyCleanProvenance(item));
          store.writeExecution(execution);
          if (provenance.length === 0) {
            throw new Error("Zero-Mock Delivery blocks COMPLETE because clean Zero-Mock acceptance provenance is required.");
          }
          if (scan.mock_taint || badProvenance.length > 0) {
            throw new Error("Zero-Mock Delivery blocks COMPLETE because current implementation/self-check evidence is mock-tainted, non-passing, or lacks authoritative readback.");
          }
          await revalidateCleanProvenance(execution, provenance, _signal);
          value = await lifecycle.complete(params.execution_id, sid);
          return resultText(runtimeView(value));
        }
        case "block": {
          if (!params.execution_id && params.assignment_id) {
            value = lifecycle.blockAssignment(params.assignment_id, sid, params.reason ?? "Ready implementation assignment blocked");
            return resultText({ assignment_id: value.assignment_id, status: value.status, block_reason: value.block_reason });
          }
          const execution = lifecycle.status(params.execution_id);
          if (execution.managed_service) await services.stop(execution.execution_id, sid);
          value = lifecycle.block(params.execution_id, sid, params.reason ?? "Ready implementation blocked");
          return resultText(runtimeView(value));
        }
        case "status": {
          const session = lifecycle.sessionState(sid);
          const executionId = params.execution_id ?? session?.execution_id;
          return resultText({
            session: session ? { armed: session.armed, role: session.role, execution_id: session.execution_id, assignment_id: session.assignment_id } : null,
            execution: executionId ? runtimeView(lifecycle.status(executionId)) : null,
            tool_map: { mapped: toolMap.mapped, boundaries: toolMap.boundaries, custom_mutation_boundary: toolMap.customMutationBoundary },
          });
        }
        default:
          throw new Error(`unsupported ready_guard action: ${params.action}`);
      }
    },
  });

  pi.registerTool({
    name: "ready_argv",
    label: "Ready Argv",
    description: "Run explicit structured argv for Ready inspection or mutation. Shell strings are not accepted.",
    parameters: z.object({
      action: z.enum(["inspect", "mutate", "acceptance"]),
      version: z.literal(1),
      commands: z.array(z.array(z.string())).optional(),
      argv: z.array(z.string()).optional(),
      target_paths: z.array(z.string()).optional(),
      evidence_paths: z.array(z.string()).optional(),
      production_entrypoint: z.string().optional(),
      dependency_paths: z.array(z.string()).optional(),
      authoritative_readback_path: z.string().optional(),
      provenance_kind: z.enum(["LOCAL_PATH", "LOCAL_SQLITE", "EXTERNAL_HTTP_PROVIDER"]),
      readback_argv: z.array(z.string()).optional(),
    }),
    async execute(_toolCallId, params, signal, _onUpdate, ctx) {
      const sid = sessionId(ctx);
      let state = requireWorkerExecution(lifecycle, sid);
      const authority = await lifecycle.checkAuthorityCurrentness(state);
      if (!authority.current) {
        lifecycle.markAuthorityDrift(state.execution_id, authority.changed);
        throw new Error("Ready authority changed; re-confirm authority before ready_argv execution");
      }

      if (params.action === "acceptance") {
        if (!params.production_entrypoint) throw new Error("ready_argv acceptance requires production_entrypoint");
        const result = await runAcceptanceEvidence({ lifecycle, store, state, params, signal });
        return resultText(result);
      }

      if (params.action === "inspect") {
        const request = validateInspectRequest({ version: params.version, commands: params.commands });
        const outputs = [];
        for (const argv of request.commands) {
          state = lifecycle.status(state.execution_id);
          if (["COMPLETE", "BLOCKED", "MUTATION_UNCERTAIN"].includes(state.phase)) throw new Error(`ready_argv inspect is unavailable in phase ${state.phase}`);
          const confinement = argvConfinementReason(state, argv);
          if (confinement) throw new Error(confinement);
          const broad = isBroadInventory("bash", { argv });
          const inventory = inventoryAllowedForPhase(state, broad);
          if (!inventory.allowed) throw new Error(inventory.reason);
          const prepared = prepareObservation(state, "ready_argv.inspect", { argv }, broad);
          if (!prepared.allowed) throw new Error(prepared.reason);
          store.writeExecution(state);
          const syntheticId = `ready-argv-${crypto.randomUUID()}`;
          lifecycle.beginOperation(state.execution_id, { toolCallId: syntheticId, kind: "observation", observationDigest: prepared.digest });
          let result;
          try {
            result = await runArgv(argv, { cwd: state.project_root, signal });
          } catch (error) {
            const current = lifecycle.status(state.execution_id);
            recordObservationResult(current, prepared.digest, {
              success: false,
              outputBytes: 0,
              errorClassification: classifyError(error?.message ?? error),
            });
            store.writeExecution(current);
            lifecycle.finishOperation(state.execution_id, syntheticId, { mutationApplied: false });
            throw error;
          }
          const combined = `${result.stdout}${result.stderr}`;
          const bytes = Buffer.byteLength(combined, "utf8");
          const success = result.exitCode === 0 && !result.timedOut;
          const current = lifecycle.status(state.execution_id);
          recordObservationResult(current, prepared.digest, {
            success,
            outputBytes: bytes,
            errorClassification: success ? null : classifyError(result.timedOut ? "timeout" : result.stderr || `exit ${result.exitCode}`),
            incomplete: bytes > MAX_OBSERVATION_OUTPUT_BYTES,
          });
          store.writeExecution(current);
          lifecycle.finishOperation(state.execution_id, syntheticId, { mutationApplied: false });
          outputs.push({
            argv,
            exit_code: result.exitCode,
            timed_out: result.timedOut,
            stdout: result.stdout.slice(0, MAX_OBSERVATION_OUTPUT_BYTES),
            stderr: result.stderr.slice(0, MAX_OBSERVATION_OUTPUT_BYTES),
          });
        }
        return resultText({ action: "inspect", results: outputs });
      }

      if (state.execution_mode === "VERIFY") throw new Error("Zero-Mock verifier runtime is read-only; ready_argv mutate is unavailable.");
      if (state.phase !== "ACTIVE") throw new Error(`ready_argv mutate requires ACTIVE execution; found ${state.phase}`);
      const request = validateMutationRequest({ version: params.version, argv: params.argv });
      if (isAcceptanceCommand(request.argv, state.project_root)) {
        throw new Error("acceptance tests must run through ready_argv acceptance so Zero-Mock provenance is recorded");
      }
      const argvTaint = scanProspectiveMutation({ argv: request.argv }, "<ready_argv mutate>");
      if (argvTaint.length > 0) {
        recordZeroMockViolations(state, argvTaint);
        store.writeExecution(state);
        throw new Error(`Zero-Mock Delivery blocked structured mutation: ${argvTaint.map(item => item.code).join(", ")}`);
      }
      const targetPaths = validateExplicitTargets(state, params.target_paths);
      const confinement = argvConfinementReason(state, request.argv);
      if (confinement) throw new Error(confinement);
      const mutationDigest = mutationDigestFor(state, "ready_argv.mutate", {
        argv: request.argv,
        target_paths: targetPaths,
      });
      const repeatedReason = repeatedMutationReason(state, mutationDigest);
      if (repeatedReason) throw new Error(repeatedReason);
      const syntheticId = `ready-argv-${crypto.randomUUID()}`;
      lifecycle.beginOperation(state.execution_id, {
        toolCallId: syntheticId,
        kind: "mutation",
        mutationDigest,
      });
      let result;
      try {
        result = await runArgv(request.argv, { cwd: state.project_root, signal });
      } catch (error) {
        const classification = classifyError(error?.message ?? error);
        if (classification === "TRANSPORT_NETWORK") {
          lifecycle.markMutationUncertain(
            state.execution_id,
            syntheticId,
            "structured mutation argv ended with transport/network uncertainty; automatic replay is forbidden",
          );
        } else {
          lifecycle.finishOperation(state.execution_id, syntheticId, {
            mutationApplied: false,
            failureClassification: classification,
            failureDetail: String(error?.message ?? error),
          });
        }
        throw error;
      }
      if (result.timedOut) {
        lifecycle.markMutationUncertain(state.execution_id, syntheticId, "structured mutation argv timed out; automatic replay is forbidden");
      } else if (result.exitCode === 0) {
        lifecycle.finishOperation(state.execution_id, syntheticId, { mutationApplied: true });
      } else {
        const classification = classifyError(result.stderr || `exit ${result.exitCode}`);
        if (classification === "TRANSPORT_NETWORK") {
          lifecycle.markMutationUncertain(
            state.execution_id,
            syntheticId,
            "structured mutation argv returned a transport/network failure; automatic replay is forbidden",
          );
        } else {
          lifecycle.finishOperation(state.execution_id, syntheticId, {
            mutationApplied: false,
            failureClassification: classification,
            failureDetail: result.stderr || `exit ${result.exitCode}`,
          });
        }
      }
      const postMutationState = lifecycle.status(state.execution_id);
      recordZeroMockPaths(postMutationState, "touched_paths", targetPaths);
      for (const targetPath of targetPaths) {
        if (fs.existsSync(targetPath) && fs.statSync(targetPath).isFile()) {
          recordZeroMockViolations(postMutationState, scanFileGraph(postMutationState.project_root, [targetPath]).violations);
        }
      }
      store.writeExecution(postMutationState);
      return resultText({
        action: "mutate",
        argv: request.argv,
        exit_code: result.exitCode,
        timed_out: result.timedOut,
        stdout: result.stdout.slice(0, MAX_OBSERVATION_OUTPUT_BYTES),
        stderr: result.stderr.slice(0, MAX_OBSERVATION_OUTPUT_BYTES),
        execution: runtimeView(lifecycle.status(state.execution_id)),
      });
    },
  });

  pi.registerTool({
    name: "ready_verify_guard",
    label: "Ready Verify Guard",
    description: "Bind the Zero-Mock verifier runtime and admit only mock-clean VERIFIED evidence without changing verifier verdict authority.",
    parameters: z.object({
      action: z.enum(["begin", "admit", "post_validate", "status"]),
      ticket_path: z.string().optional(),
      project_root: z.string().optional(),
      execution_id: z.string().optional(),
      verdict: z.enum(["VERIFIED", "FAILED", "INCONCLUSIVE"]).optional(),
      production_entrypoint: z.string().optional(),
      dependency_paths: z.array(z.string()).optional(),
      authoritative_readback_path: z.string().optional(),
    }),
    async execute(_toolCallId, params, signal, _onUpdate, ctx) {
      const sid = sessionId(ctx);
      if (params.action === "begin") {
        if (!params.ticket_path) throw new Error("ready_verify_guard begin requires ticket_path");
        const projectRoot = params.project_root ?? projectRootFromTicket(params.ticket_path);
        const value = await lifecycle.beginVerification({ sessionId: sid, projectRoot, ticketPath: params.ticket_path });
        return resultText(runtimeView(value));
      }
      const session = lifecycle.sessionState(sid);
      const executionId = params.execution_id ?? session?.execution_id;
      if (!executionId) throw new Error("current verifier session has no bound execution");
      if (params.action === "status") return resultText(runtimeView(lifecycle.status(executionId)));
      if (params.action === "admit") {
        const state = lifecycle.status(executionId);
        const scan = currentZeroMockScan(state);
        let currentEvidenceVerified = false;
        if (params.verdict === "VERIFIED" && scan.mock_taint) {
          store.writeExecution(state);
          throw new Error("mock-tainted verification evidence cannot be admitted for VERIFIED");
        }
        if (params.verdict === "VERIFIED") {
          const cleanAcceptance = (state.zero_mock?.acceptance_provenance || []).filter(isNominallyCleanProvenance);
          if (cleanAcceptance.length > 0) {
            await revalidateCleanProvenance(state, cleanAcceptance, signal);
            currentEvidenceVerified = true;
          } else if (params.authoritative_readback_path) {
            const inspection = recordInspectionEvidence(state, params);
            await revalidateCleanProvenance(state, [inspection], signal);
            currentEvidenceVerified = true;
          } else {
            const cleanInspection = (state.zero_mock?.inspection_provenance || []).filter(isNominallyCleanProvenance);
            if (cleanInspection.length > 0) {
              await revalidateCleanProvenance(state, cleanInspection, signal);
              currentEvidenceVerified = true;
            }
          }
        }
        store.writeExecution(state);
        const value = await lifecycle.admitVerification(executionId, sid, params.verdict, { currentEvidenceVerified });
        return resultText(runtimeView(value));
      }
      if (params.action === "post_validate") {
        const state = lifecycle.status(executionId);
        if (
          state.execution_mode !== "VERIFY"
          || state.phase !== "VERIFY_VERIFIED_ADMITTED"
          || !state.verification_progression_used
          || state.verification_progression_exact !== true
        ) {
          throw new Error("post_validate requires one exact admitted Status: ready to Status: done Ticket progression");
        }
        validateTicketWith(state.validator_path, state.ticket_path, state.project_root);
        const status = fs.readFileSync(state.ticket_path, "utf8").match(/^Status:\s*(.+?)\s*$/m)?.[1]?.trim();
        if (status !== "done") throw new Error(`post-progression Ticket status must be exact done; found ${status ?? "missing"}`);
        const value = lifecycle.finishVerificationProgression(executionId, sid);
        return resultText(runtimeView(value));
      }
      throw new Error(`unsupported ready_verify_guard action: ${params.action}`);
    },
  });

  pi.registerTool({
    name: "ready_service",
    label: "Ready Service",
    description: "Start, stop, or inspect one execution-owned local service required for implementation self-checks.",
    parameters: z.object({
      action: z.enum(["start", "stop", "status"]),
      execution_id: z.string(),
      version: z.literal(1).optional(),
      argv: z.array(z.string()).optional(),
    }),
    async execute(_toolCallId, params, _signal, _onUpdate, ctx) {
      const sid = sessionId(ctx);
      if (params.action === "start") return resultText(services.start(params.execution_id, sid, { version: params.version, argv: params.argv }));
      if (params.action === "stop") return resultText(await services.stop(params.execution_id, sid));
      return resultText(services.status(params.execution_id));
    },
  });

  return { store, lifecycle, services, getToolMap: () => toolMap };
}
