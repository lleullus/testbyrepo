import assert from "node:assert/strict";
import test from "node:test";

import {
  extractApplyPatchPaths,
  extractOmpTargetPaths,
  makePseudoToolUseId,
  reminderTextFromHookOutput,
  textFromAgentMessage,
  toClaudeCompatibleCalls,
} from "../extensions/adapter.mjs";

test("extracts write paths", () => {
  assert.deepEqual(
    extractOmpTargetPaths("write", { path: "src/index.ts", content: "x" }),
    ["src/index.ts"],
  );
});

test("extracts multi-file edit paths and apply_patch paths", () => {
  const input = {
    paths: ["src/a.ts", "src/b.ts"],
    operations: [{ file_path: "src/c.ts" }],
    patch: [
      "*** Begin Patch",
      "*** Update File: src/d.ts",
      "*** Add File: src/e.ts",
      "*** Move to: src/f.ts",
      "*** End Patch",
    ].join("\n"),
  };
  assert.deepEqual(
    extractOmpTargetPaths("edit", input).sort(),
    [
      "src/a.ts",
      "src/b.ts",
      "src/c.ts",
      "src/d.ts",
      "src/e.ts",
      "src/f.ts",
    ],
  );
});

test("ignores non-mutating tools and internal resources", () => {
  assert.deepEqual(extractOmpTargetPaths("read", { path: "src/a.ts" }), []);
  assert.deepEqual(
    extractOmpTargetPaths("write", { path: "xd://device" }),
    [],
  );
});

test("builds deterministic Claude-compatible hook calls", () => {
  const calls = toClaudeCompatibleCalls("tool/call:1", "edit", {
    paths: ["src/a.ts", "src/b.ts"],
  });
  assert.equal(calls.length, 2);
  assert.equal(calls[0].tool_name, "Edit");
  assert.equal(calls[0].tool_input.file_path, "src/a.ts");
  assert.match(calls[0].tool_use_id, /^omp_[a-f0-9]{32}$/);
  assert.equal(calls[0].tool_use_id, makePseudoToolUseId("tool/call:1", 0));
});

test("extracts reminders and assistant text", () => {
  assert.equal(
    reminderTextFromHookOutput({
      hookSpecificOutput: { additionalContext: "  review this  " },
    }),
    "review this",
  );
  assert.equal(
    textFromAgentMessage({
      content: [
        { type: "text", text: "first" },
        { type: "thinking", thinking: "hidden" },
        { type: "text", text: "second" },
      ],
    }),
    "first\nsecond",
  );
});

test("parses apply_patch file headers", () => {
  assert.deepEqual(
    extractApplyPatchPaths(
      "*** Update File: a.ts\n*** Delete File: b.ts\n*** Move to: c.ts",
    ),
    ["a.ts", "b.ts", "c.ts"],
  );
});
