export const ERROR_CLASS = Object.freeze({
  TRANSPORT_NETWORK: "TRANSPORT_NETWORK",
  PROTOCOL_SESSION: "PROTOCOL_SESSION",
  TOOL_APPLICATION: "TOOL_APPLICATION",
  DOMAIN_DATA: "DOMAIN_DATA",
  MUTATION_UNCERTAIN: "MUTATION_UNCERTAIN",
});

export const MAX_READ_ONLY_TRANSPORT_RETRIES = 3;

export function resultText(content) {
  if (typeof content === "string") return content;
  if (!Array.isArray(content)) return "";
  return content
    .map(item => (item && typeof item === "object" && typeof item.text === "string" ? item.text : ""))
    .filter(Boolean)
    .join("\n");
}

export function classifyExplicitFailure({ isError, text = "", killed = false }) {
  if (!isError && !killed) return null;
  const message = String(text);
  if (
    killed ||
    /\b(connection failed|network error|network_error|timed out|timeout|econnreset|econnrefused|eai_again|http 502|http 503|http 504)\b/i.test(message)
  ) {
    return ERROR_CLASS.TRANSPORT_NETWORK;
  }
  if (/\b(session not found|unknown session|expired session|unknown workspace_id|unknown assignment|assignment expired)\b/i.test(message)) {
    return ERROR_CLASS.PROTOCOL_SESSION;
  }
  if (/\b(permission denied|enoent|file not found|no such file|invalid ticket|validator rejected|validator returned invalid|outside project root)\b/i.test(message)) {
    return ERROR_CLASS.DOMAIN_DATA;
  }
  return ERROR_CLASS.TOOL_APPLICATION;
}

export function mutationFailureState(failureClass) {
  return failureClass === ERROR_CLASS.TRANSPORT_NETWORK ? ERROR_CLASS.MUTATION_UNCERTAIN : failureClass;
}

export function classifyError(value) {
  const text = typeof value === "string" ? value : resultText(value);
  return classifyExplicitFailure({ isError: true, text });
}

export function mayRetryRead({ classification, attempts, sameInput, readOnly = true, idempotent = true }) {
  return Boolean(readOnly && idempotent && sameInput && classification === ERROR_CLASS.TRANSPORT_NETWORK && Number.isInteger(attempts) && attempts < MAX_READ_ONLY_TRANSPORT_RETRIES);
}
