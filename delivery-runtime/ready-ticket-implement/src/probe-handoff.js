import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

import { bindAuthority } from "./authority-binding.js";
import { captureVerificationTarget } from "./verification-target.js";

const SCHEMA = "iis-ready-probe-handoff/v1";
const TERMINAL_LANE_STATUSES = new Set(["FINDING", "NO_FINDING", "EVIDENCE_LIMIT"]);
const VERDICT_VALUES = new Set(["PASS", "FAIL", "VERIFIED", "FAILED", "SATISFIED", "CONTRADICTED"]);
const VERDICT_KEYS = new Set(["verdict", "verification_verdict", "ac_verdict", "flow_result", "whole_ticket"]);
const VERDICTISH_KEYS = new Set(["status", "evaluation", "result"]);

function sha256(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

function verificationSection(text) {
  const match = text.match(/^## Verification\s*$([\s\S]*?)(?=^##\s+|(?![\s\S]))/m);
  if (!match) throw new Error("Ticket has no ## Verification section");
  return match[1].trimEnd() + "\n";
}

function flowDenominator(ticketPath) {
  const text = fs.readFileSync(ticketPath, "utf8");
  const section = verificationSection(text);
  const count = (section.match(/^- Parent outcome ordinal:/gm) || []).length;
  if (count < 1) throw new Error("Ticket has no authored Verification flows");
  return { count, sha256: sha256(section) };
}

function compactTarget(target) {
  return {
    git_head: target.git_head,
    digest: target.digest,
    target_paths: target.target_paths,
    allowed_output_paths: target.allowed_output_paths,
  };
}

function identityFromAuthority(authority) {
  return {
    ticket: { path: authority.ticket_path, sha256: authority.ticket_sha256 },
    parent_spec: { path: authority.parent_spec_path, sha256: authority.parent_spec_sha256 },
    behavior_authorities: (authority.behavior_authorities || []).map(item => ({ path: item.path, sha256: item.sha256 })),
    ui_authority: authority.ui_authority ? { path: authority.ui_authority.path, sha256: authority.ui_authority.sha256 } : null,
    verification_flow_denominator: flowDenominator(authority.ticket_path),
  };
}

function assertNoVerdictFields(value, key = null) {
  if (Array.isArray(value)) {
    for (const item of value) assertNoVerdictFields(item, key);
    return;
  }
  if (!value || typeof value !== "object") {
    if (key && VERDICTISH_KEYS.has(key) && typeof value === "string" && VERDICT_VALUES.has(value.trim().toUpperCase())) {
      throw new Error(`Probe machine binding contains verifier-owned value in ${key}: ${value}`);
    }
    return;
  }
  for (const [rawKey, child] of Object.entries(value)) {
    const normalized = rawKey.trim().toLowerCase().replace(/[ -]+/g, "_");
    if (VERDICT_KEYS.has(normalized)) throw new Error(`Probe machine binding contains verifier-owned field: ${rawKey}`);
    assertNoVerdictFields(child, normalized);
  }
}

function validateLaneClosure(binding) {
  if (binding.probe_completion !== "COMPLETE") throw new Error("Probe Completion is not COMPLETE");
  if (binding.cleanup !== "CLOSED") throw new Error("Probe cleanup is not CLOSED");
  if (!Array.isArray(binding.admitted_lanes)) throw new Error("admitted_lanes must be an array");
  if (new Set(binding.admitted_lanes).size !== binding.admitted_lanes.length) throw new Error("admitted_lanes contains duplicates");
  if (!Array.isArray(binding.lane_terminals)) throw new Error("lane_terminals must be an array");
  const terminalMap = new Map();
  for (const entry of binding.lane_terminals) {
    if (!entry || typeof entry !== "object" || Object.keys(entry).sort().join(",") !== "lane,status") {
      throw new Error("each lane terminal must contain exactly lane and status");
    }
    if (typeof entry.lane !== "string" || !entry.lane) throw new Error("lane terminal has invalid lane");
    if (!TERMINAL_LANE_STATUSES.has(entry.status)) throw new Error(`lane ${entry.lane} is not terminal: ${entry.status}`);
    if (terminalMap.has(entry.lane)) throw new Error(`duplicate lane terminal: ${entry.lane}`);
    terminalMap.set(entry.lane, entry.status);
  }
  if (new Set(terminalMap.keys()).size !== new Set(binding.admitted_lanes).size || binding.admitted_lanes.some(lane => !terminalMap.has(lane))) {
    throw new Error("admitted lane denominator is not exactly terminal");
  }
}

export async function buildProbeBinding({ projectRoot, ticketPath, targetPaths = [], allowedOutputPaths = [], admittedLanes = [], laneTerminals = [], bindAuthorityFn = bindAuthority, captureTargetFn = captureVerificationTarget }) {
  const authority = await bindAuthorityFn({ projectRoot, ticketPath });
  const target = captureTargetFn({ projectRoot: authority.project_root, targetPaths, allowedOutputPaths });
  const identity = identityFromAuthority(authority);
  return {
    schema: SCHEMA,
    ...identity,
    implementation_target: compactTarget(target),
    probe_completion: "COMPLETE",
    cleanup: "CLOSED",
    admitted_lanes: [...admittedLanes],
    lane_terminals: laneTerminals.map(entry => ({ lane: entry.lane, status: entry.status })),
  };
}

export async function validateProbeHandoff({ probeBindingPath, projectRoot, ticketPath, targetPaths = [], allowedOutputPaths = [], bindAuthorityFn = bindAuthority, captureTargetFn = captureVerificationTarget }) {
  const absolute = path.resolve(probeBindingPath);
  const raw = JSON.parse(fs.readFileSync(absolute, "utf8"));
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) throw new Error("Probe machine binding must be one JSON object");
  if (raw.schema !== SCHEMA) throw new Error(`unsupported Probe machine binding schema: ${raw.schema}`);
  assertNoVerdictFields(raw);
  validateLaneClosure(raw);

  const authority = await bindAuthorityFn({ projectRoot, ticketPath });
  const target = captureTargetFn({ projectRoot: authority.project_root, targetPaths, allowedOutputPaths });
  const expected = {
    ...identityFromAuthority(authority),
    implementation_target: compactTarget(target),
  };
  for (const [field, value] of Object.entries(expected)) {
    if (JSON.stringify(raw[field]) !== JSON.stringify(value)) throw new Error(`STALE ${field}`);
  }
  return { valid: true, path: absolute, binding: raw };
}

export { SCHEMA as PROBE_HANDOFF_SCHEMA };
