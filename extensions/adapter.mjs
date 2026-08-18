import { createHash } from "node:crypto";

const DIRECT_PATH_KEYS = new Set([
  "path",
  "file_path",
  "filePath",
  "target_path",
  "targetPath",
]);

const COLLECTION_KEYS = new Set([
  "paths",
  "files",
  "edits",
  "patches",
  "operations",
  "changes",
]);

function addPath(out, value) {
  if (typeof value !== "string") return;
  const trimmed = value.trim();
  if (!trimmed || /^[a-z][a-z0-9+.-]*:\/\//i.test(trimmed)) return;
  out.add(trimmed);
}

function collectPathFields(value, out, depth = 0) {
  if (depth > 5 || value == null) return;

  if (Array.isArray(value)) {
    for (const item of value) collectPathFields(item, out, depth + 1);
    return;
  }

  if (typeof value === "string") {
    addPath(out, value);
    return;
  }

  if (typeof value !== "object") return;

  for (const [key, child] of Object.entries(value)) {
    if (DIRECT_PATH_KEYS.has(key)) {
      addPath(out, child);
      continue;
    }
    if (COLLECTION_KEYS.has(key)) {
      collectPathFields(child, out, depth + 1);
    }
  }
}

export function extractApplyPatchPaths(patchText) {
  if (typeof patchText !== "string") return [];
  const out = new Set();
  for (const line of patchText.split(/\r?\n/)) {
    const match = /^\*\*\*\s+(?:Add|Update|Delete)\s+File:\s*(.+?)\s*$/.exec(line);
    if (match) addPath(out, match[1]);
    const move = /^\*\*\*\s+Move\s+to:\s*(.+?)\s*$/.exec(line);
    if (move) addPath(out, move[1]);
  }
  return [...out];
}

export function extractOmpTargetPaths(toolName, input) {
  if (toolName !== "write" && toolName !== "edit") return [];
  const out = new Set();
  collectPathFields(input, out);

  if (input && typeof input === "object") {
    for (const key of ["patch", "diff", "input"]) {
      for (const file of extractApplyPatchPaths(input[key])) out.add(file);
    }
  }

  return [...out];
}

export function makePseudoToolUseId(toolCallId, index = 0) {
  const digest = createHash("sha256")
    .update(`${String(toolCallId)}:${index}`)
    .digest("hex")
    .slice(0, 32);
  return `omp_${digest}`;
}

export function toClaudeCompatibleCalls(toolCallId, toolName, input) {
  const mappedName = toolName === "write" ? "Write" : toolName === "edit" ? "Edit" : null;
  if (!mappedName) return [];
  return extractOmpTargetPaths(toolName, input).map((filePath, index) => ({
    tool_name: mappedName,
    tool_use_id: makePseudoToolUseId(toolCallId, index),
    tool_input: {
      file_path: filePath,
    },
  }));
}

export function reminderTextFromHookOutput(output) {
  const text = output?.hookSpecificOutput?.additionalContext;
  return typeof text === "string" && text.trim() ? text.trim() : "";
}

export function textFromAgentMessage(message) {
  if (!message || typeof message !== "object") return "";
  if (typeof message.content === "string") return message.content;
  if (!Array.isArray(message.content)) return "";

  const chunks = [];
  for (const block of message.content) {
    if (block?.type === "text" && typeof block.text === "string") {
      chunks.push(block.text);
    }
  }
  return chunks.join("\n");
}
