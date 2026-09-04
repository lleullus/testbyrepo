import { mayRetryRead } from "./retry-policy.js";
import { stableDigest } from "./state-store.js";

export const MAX_OBSERVATION_OUTPUT_BYTES = 48_000;

function normalize(value) {
  if (Array.isArray(value)) return value.map(normalize);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(Object.keys(value).sort().map(key => [key, normalize(value[key])]));
}

export function observationDigest(toolName, input, currentnessToken = null) {
  const payload = { tool: String(toolName).toLowerCase(), input: normalize(input) };
  if (currentnessToken !== null) payload.currentness_token = String(currentnessToken);
  return stableDigest(payload);
}

export function prepareObservation(state, toolName, input, broadInventory = false, currentnessToken = null) {
  state.observations ??= { entries: {} };
  state.observations.entries ??= {};
  const revision = Number(state.mutation_revision ?? 0);
  const inputDigest = observationDigest(toolName, input, currentnessToken);
  const digest = `${revision}:${inputDigest}`;
  const existing = state.observations.entries[digest];

  if (existing?.status === "success") {
    return {
      allowed: false,
      digest,
      reason: `Ready runtime blocked an observation that already succeeded in mutation revision ${revision}; reuse the existing result.`,
      existing,
    };
  }
  if (existing?.status === "running") {
    return {
      allowed: false,
      digest,
      reason: "Ready runtime blocked a duplicate observation while the same observation is already running.",
      existing,
    };
  }
  if (existing && ["failed", "incomplete"].includes(existing.status)) {
    const retryAllowed = mayRetryRead({
      classification: existing.error_classification,
      attempts: Number(existing.attempts ?? 0),
      sameInput: true,
    });
    if (!retryAllowed) {
      return {
        allowed: false,
        digest,
        reason: `Ready runtime will not repeat this unchanged ${existing.status} observation; change the bounded action or fix the cause.`,
        existing,
      };
    }
  }

  const attempts = Number(existing?.attempts ?? 0) + 1;
  state.observations.entries[digest] = {
    tool_name: String(toolName).toLowerCase(),
    input_digest: inputDigest,
    mutation_revision: revision,
    status: "running",
    attempts,
    unchanged_retries: Math.max(0, attempts - 1),
    output_bytes: 0,
    broad_inventory: Boolean(broadInventory),
    currentness_token: currentnessToken,
    started_at: Date.now(),
    ended_at: null,
    error_classification: null,
  };
  return { allowed: true, digest, entry: state.observations.entries[digest] };
}

export function recordObservationResult(
  state,
  digest,
  { success, outputBytes = 0, errorClassification = null, incomplete = false },
) {
  const entry = state.observations?.entries?.[digest];
  if (!entry) throw new Error(`unknown observation digest: ${digest}`);
  const capped = Number(outputBytes) > MAX_OBSERVATION_OUTPUT_BYTES || incomplete;
  entry.status = capped ? "incomplete" : success ? "success" : "failed";
  entry.output_bytes = Number(outputBytes) || 0;
  entry.error_classification = errorClassification;
  entry.ended_at = Date.now();
  if (entry.status === "success") {
    state.latest_evidence_revision = Math.max(Number(state.latest_evidence_revision ?? -1), entry.mutation_revision);
  }
  return entry;
}
