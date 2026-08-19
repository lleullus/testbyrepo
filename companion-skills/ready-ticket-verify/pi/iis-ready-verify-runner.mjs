#!/usr/bin/env node
import {
  canonicalDirectory,
  canonicalFile,
  optionalString,
  requireArray,
  requireBoolean,
  requireModel,
  requireRecord,
  requireRunId,
  requireString,
  requireThinking,
  runOwner,
} from "../../../.pi/lib/pi-owner-runner.mjs";
import { runTicketPreflight } from "../../../.pi/lib/ticket-preflight.mjs";
import {
  captureVerificationPostcondition,
  verifyVerificationPostcondition,
} from "../../../.pi/lib/verification-postcondition.mjs";

const TOOLS = [
  "read",
  "grep",
  "find",
  "ls",
  "bash",
  "iis_ticket_mark_done",
  "iis_audit_start",
  "iis_audit_reply",
  "iis_audit_cancel",
  "iis_audit_fan_in",
];
const DEFAULT_AUDITOR_MODEL = "opencodex/gpt-5.6-luna";
const DEFAULT_AUDITOR_THINKING = "xhigh";

function positiveOrdinal(value, field) {
  if (!Number.isInteger(value) || value < 1) throw new Error(`${field} must be a positive integer`);
  return value;
}

async function normalize(value, configuredModel, defaultThinking) {
  const input = requireRecord(value);
  if (input.schema !== "iis.pi.ready-ticket-verify/v1") {
    throw new Error("schema must be iis.pi.ready-ticket-verify/v1");
  }
  const auditors = requireArray(input.auditors, "auditors");
  const seenAcs = new Set();
  const normalizedAuditors = auditors.map((value, index) => {
    const auditor = requireRecord(value, `auditors[${index}]`);
    const acOrdinal = positiveOrdinal(auditor.acOrdinal, `auditors[${index}].acOrdinal`);
    if (seenAcs.has(acOrdinal)) throw new Error(`duplicate verification auditor AC: ${acOrdinal}`);
    seenAcs.add(acOrdinal);
    const linkedFlows = requireArray(auditor.linkedFlows, `auditors[${index}].linkedFlows`).map((flow, flowIndex) =>
      positiveOrdinal(flow, `auditors[${index}].linkedFlows[${flowIndex}]`),
    );
    if (!linkedFlows.length) throw new Error(`auditors[${index}].linkedFlows must not be empty`);
    if (new Set(linkedFlows).size !== linkedFlows.length) throw new Error(`duplicate linked flow for AC ${acOrdinal}`);
    return {
      acOrdinal,
      linkedFlows,
      model: requireModel(auditor.model ?? DEFAULT_AUDITOR_MODEL, `auditors[${index}].model`),
      thinking: requireThinking(auditor.thinking ?? DEFAULT_AUDITOR_THINKING, `auditors[${index}].thinking`),
      oracleBrowser: requireBoolean(auditor.oracleBrowser, `auditors[${index}].oracleBrowser`),
    };
  });

  return {
    runId: requireRunId(input.runId),
    ticket: await canonicalFile(input.ticket, "ticket"),
    projectRoot: await canonicalDirectory(input.projectRoot, "projectRoot"),
    targetIdentity: requireString(input.targetIdentity, "targetIdentity", 4096),
    candidateTarget: optionalString(input.candidateTarget, "candidateTarget", 4096) || "None",
    implementationReport: optionalString(input.implementationReport, "implementationReport", 4096) || "None",
    additionalInstructions: optionalString(input.additionalInstructions, "additionalInstructions") || "None",
    ownerModel: requireModel(input.ownerModel || configuredModel, "ownerModel"),
    ownerThinking: requireThinking(input.ownerThinking ?? defaultThinking, "ownerThinking"),
    diagnosticReverify: requireBoolean(input.diagnosticReverify, "diagnosticReverify"),
    auditors: normalizedAuditors,
  };
}

function buildTask(input, preflight) {
  const auditorConfiguration = input.auditors.length
    ? input.auditors
        .map(
          (auditor, index) =>
            [
              `Auditor ${index + 1}:`,
              `- AC Ordinal: ${auditor.acOrdinal}`,
              `- Linked Authored Flow Ordinals: ${auditor.linkedFlows.join(", ")}`,
              `- Assignment: observe only AC ${auditor.acOrdinal} and linked authored flows ${auditor.linkedFlows.join(", ")}`,
              `- Model: ${auditor.model}`,
              `- Thinking: ${auditor.thinking}`,
              `- Oracle Browser: ${auditor.oracleBrowser ? "AUTHORIZED" : "NOT REQUESTED"}`,
            ].join("\n"),
        )
        .join("\n")
    : "None";

  return [
    "PI READY TICKET VERIFY INVOCATION",
    "",
    `OMP Run ID: ${input.runId}`,
    "Owner Agent: iis-ready-verify",
    "Owner Session: none",
    `Canonical Ticket: ${input.ticket}`,
    `Project Root: ${input.projectRoot}`,
    `Stable Target Identity: ${input.targetIdentity}`,
    `Runner Preflight: ${preflight.validatorResult}`,
    `Runner Ticket Status: ${preflight.status}`,
    `Diagnostic Reverify: ${input.diagnosticReverify}`,
    `Candidate Target Hint: ${input.candidateTarget}`,
    `Implementation Report Hint: ${input.implementationReport}`,
    "Additional Instructions:",
    input.additionalInstructions,
    "",
    "AC Runtime Auditor Configuration:",
    `Auditor Count: ${input.auditors.length}`,
    auditorConfiguration,
    "",
    "Treat candidate target and implementation report as navigation only. Use iis_ticket_mark_done as the only Ticket mutation capability. Execute exactly one fresh canonical Ready Ticket verification lifecycle. Return only the required Pi owner preamble followed by either the canonical VERIFICATION NOT STARTED block or the complete canonical READY TICKET VERIFICATION RESULT, as admission requires.",
  ].join("\n");
}

function parseOutput(output) {
  if (!output.includes("Pi Owner Agent: iis-ready-verify")) throw new Error("missing Verify Pi owner identity");
  if (!output.includes("Pi Owner Session: none")) throw new Error("missing fresh Verify Pi session evidence");
  const notStarted = output.match(/^VERIFICATION NOT STARTED(?::\s*(.+?))?\s*$/m);
  if (notStarted) {
    if (!/^AC verdicts:\s*Not issued\s*$/mi.test(output)) throw new Error("VERIFICATION NOT STARTED issued AC verdicts");
    const reason = output.match(/^Reason:\s*(.+?)\s*$/m)?.[1] || notStarted[1] || "Unspecified admission failure";
    return { status: "NOT_STARTED", reason };
  }
  if (!output.includes("READY TICKET VERIFICATION RESULT")) throw new Error("missing canonical READY TICKET VERIFICATION RESULT");
  const verdict = output.match(/^Verification Verdict:\s*`?(VERIFIED|FAILED|INCONCLUSIVE)`?\s*$/m);
  const progression = output.match(/^Ticket Progression:\s*`?(COMPLETED|NOT APPLICABLE|FAILED)`?\s*$/m);
  const status = output.match(/^Ticket status after verification:\s*`?(ready|done)`?\s*$/m);
  if (!verdict) throw new Error("missing or invalid Verification Verdict");
  if (!progression) throw new Error("missing or invalid Ticket Progression");

  if (!status) throw new Error("missing Ticket status after verification");
  return { verdict: verdict[1], progression: progression[1], ticketStatus: status[1] };
}
function validateWorkflowPostcondition(workflow, postcondition, preflight) {
  if (!postcondition || postcondition.status !== "PASSED") throw new Error("Verify postcondition evidence is unavailable");
  if (workflow.status === "NOT_STARTED") {
    if (postcondition.ticketChange !== "UNCHANGED") throw new Error("Ticket changed during a not-started verification");
    return;
  }
  const expectedStatus = postcondition.ticketChange === "READY_TO_DONE" ? "done" : preflight.status;
  if (workflow.ticketStatus !== expectedStatus) {
    throw new Error(`reported Ticket status ${workflow.ticketStatus} does not match observed ${expectedStatus}`);
  }
  if (workflow.verdict !== "VERIFIED" && workflow.progression !== "NOT APPLICABLE") {
    throw new Error(`${workflow.verdict} cannot produce Ticket Progression ${workflow.progression}`);
  }
  if (preflight.status === "done" && workflow.progression !== "NOT APPLICABLE") {
    throw new Error("diagnostic re-verification cannot progress an already-done Ticket");
  }
  if (workflow.progression === "COMPLETED") {
    if (workflow.verdict !== "VERIFIED" || postcondition.ticketChange !== "READY_TO_DONE") {
      throw new Error("Ticket Progression COMPLETED without VERIFIED and an exact guarded ready-to-done transition");
    }
    return;
  }
  if (postcondition.ticketChange !== "UNCHANGED") {
    throw new Error("Ticket changed without completed guarded progression");
  }
  if (workflow.verdict === "VERIFIED" && preflight.status === "ready" && workflow.progression !== "FAILED") {
    throw new Error("VERIFIED ready Ticket must report completed or failed progression");
  }
}

await runOwner({
  mode: "VERIFY",
  agent: "iis-ready-verify",
  sourceUrl: import.meta.url,
  agentRelativePath: "companion-skills/ready-ticket-verify/pi/iis-ready-verify.md",
  modelEnvironment: "IIS_READY_VERIFY_MODEL",
  defaultModel: "opencodex/gpt-5.6-luna",
  defaultThinking: "max",
  tools: TOOLS,
  preflight: (input, root) =>
    runTicketPreflight({
      iisSkillsRoot: root,
      ticket: input.ticket,
      mode: "VERIFY",
      projectRoot: input.projectRoot,
      diagnosticReverify: input.diagnosticReverify,
    }),
  capturePostcondition: (input) => captureVerificationPostcondition(input.projectRoot, input.ticket),
  verifyPostcondition: (capture) => verifyVerificationPostcondition(capture),
  childEnvironment: (input, preflight) => ({
    IIS_READY_TICKET_MODE: "VERIFY",
    IIS_READY_TICKET_PATH: input.ticket,
    IIS_CANONICAL_TICKET_VALIDATOR: preflight.validator,
  }),
  validateWorkflowPostcondition,
  normalize,
  buildTask,
  parseOutput,
});
