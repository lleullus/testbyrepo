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

const TOOLS = [
  "read",
  "grep",
  "find",
  "ls",
  "bash",
  "edit",
  "write",
  "iis_audit_start",
  "iis_audit_reply",
  "iis_audit_cancel",
  "iis_audit_fan_in",
];
const DEFAULT_AUDITOR_MODEL = "opencodex/gpt-5.6-luna";
const DEFAULT_AUDITOR_THINKING = "xhigh";

async function normalize(value, configuredModel, defaultThinking) {
  const input = requireRecord(value);
  if (input.schema !== "iis.pi.ready-ticket-implement/v1") {
    throw new Error("schema must be iis.pi.ready-ticket-implement/v1");
  }
  const auditors = requireArray(input.auditors, "auditors");
  if (auditors.length > 3) throw new Error("implement auditor count must be between 0 and 3");

  const seenSlots = new Set();
  const normalizedAuditors = auditors.map((value, index) => {
    const auditor = requireRecord(value, `auditors[${index}]`);
    const slot = requireString(auditor.slot, `auditors[${index}].slot`, 128);
    if (seenSlots.has(slot)) throw new Error(`duplicate implement auditor slot: ${slot}`);
    seenSlots.add(slot);
    return {
      slot,
      assignment: requireString(auditor.assignment, `auditors[${index}].assignment`),
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
    additionalInstructions: optionalString(input.additionalInstructions, "additionalInstructions") || "None",
    ownerModel: requireModel(input.ownerModel || configuredModel, "ownerModel"),
    ownerThinking: requireThinking(input.ownerThinking ?? defaultThinking, "ownerThinking"),
    auditors: normalizedAuditors,
  };
}

function buildTask(input, preflight) {
  const auditorConfiguration = input.auditors.length
    ? input.auditors
        .map(
          (auditor, index) =>
            [
              `Slot ${index + 1}:`,
              `- Slot ID: ${auditor.slot}`,
              `- Assignment: ${auditor.assignment}`,
              `- Model: ${auditor.model}`,
              `- Thinking: ${auditor.thinking}`,
              `- Oracle Browser: ${auditor.oracleBrowser ? "AUTHORIZED" : "NOT REQUESTED"}`,
            ].join("\n"),
        )
        .join("\n")
    : "None";

  return [
    "PI READY TICKET IMPLEMENT INVOCATION",
    "",
    `OMP Run ID: ${input.runId}`,
    "Owner Agent: iis-ready-implement",
    "Owner Session: none",
    `Ticket: ${input.ticket}`,
    `Project Root: ${input.projectRoot}`,
    `Target Identity: ${input.targetIdentity}`,
    `Runner Preflight: ${preflight.validatorResult}`,
    `Runner Ticket Status: ${preflight.status}`,
    "Additional Instructions:",
    input.additionalInstructions,
    "",
    "Implementation Auditor Configuration:",
    `Auditor Count: ${input.auditors.length}`,
    auditorConfiguration,
    "",
    "Execute exactly one canonical Ready Ticket implementation lifecycle. Use only the supplied auditor slots. Return only the required Pi owner preamble followed by the complete canonical IMPLEMENT RESULT.",
  ].join("\n");
}

function parseOutput(output) {
  if (!output.includes("Pi Owner Agent: iis-ready-implement")) throw new Error("missing Implement Pi owner identity");
  if (!output.includes("Pi Owner Session: none")) throw new Error("missing fresh Implement Pi session evidence");
  if (!output.includes("IMPLEMENT RESULT")) throw new Error("missing canonical IMPLEMENT RESULT");
  const match = output.match(/^Completion:\s*(COMPLETE|BLOCKED|PARTIAL)\s*$/m);
  if (!match) throw new Error("missing or invalid IMPLEMENT RESULT Completion");
  return { completion: match[1] };
}

await runOwner({
  mode: "IMPLEMENT",
  agent: "iis-ready-implement",
  sourceUrl: import.meta.url,
  agentRelativePath: "companion-skills/ready-ticket-implement/pi/iis-ready-implement.md",
  modelEnvironment: "IIS_READY_IMPLEMENT_MODEL",
  defaultModel: "opencodex/gpt-5.6-luna",
  defaultThinking: "max",
  tools: TOOLS,
  preflight: (input, root) =>
    runTicketPreflight({ iisSkillsRoot: root, ticket: input.ticket, projectRoot: input.projectRoot, mode: "IMPLEMENT" }),
  normalize,
  buildTask,
  parseOutput,
});
