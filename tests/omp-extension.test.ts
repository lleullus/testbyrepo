import { expect, test } from "bun:test";

import extension from "../extensions/lumin-repo-lens";

test("registers the complete OMP lifecycle adapter", () => {
  const handlers = new Map<string, unknown>();
  let label = "";

  extension({
    setLabel(value: string) {
      label = value;
    },
    on(name: string, handler: unknown) {
      handlers.set(name, handler);
    },
    logger: {
      warn() {},
    },
  } as any);

  expect(label).toBe("Lumin Repo Lens");
  expect([...handlers.keys()].sort()).toEqual([
    "before_agent_start",
    "session_branch",
    "session_shutdown",
    "session_start",
    "session_stop",
    "session_switch",
    "tool_execution_start",
    "tool_result",
  ]);
});
