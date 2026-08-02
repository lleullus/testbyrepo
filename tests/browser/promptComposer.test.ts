import { describe, expect, test, vi } from "vitest";
import {
  __test__ as promptComposer,
  clearPromptComposer,
  submitPrompt,
} from "../../src/browser/actions/promptComposer.js";
import {
  CONVERSATION_TURN_CONTAINER_SELECTOR,
  CONVERSATION_TURN_SELECTOR,
} from "../../src/browser/constants.js";
import { buildConversationTurnCountExpression } from "../../src/browser/conversationTurns.js";

class IdentityElement {
  parentElement: IdentityElement | null = null;

  constructor(
    private readonly attributes: Record<string, string> = {},
    private readonly ownText = "",
    readonly children: IdentityElement[] = [],
  ) {
    for (const child of children) {
      child.parentElement = this;
    }
  }

  get innerText(): string {
    return this.textContent;
  }

  get textContent(): string {
    return `${this.ownText}${this.children.map((child) => child.textContent).join("")}`;
  }

  getAttribute(name: string): string | null {
    return this.attributes[name] ?? null;
  }

  contains(node: IdentityElement): boolean {
    return this.children.some((child) => child === node || child.contains(node));
  }

  querySelectorAll(selector: string): IdentityElement[] {
    return flattenIdentityElements(this.children).filter((element) =>
      matchesIdentitySelector(element, selector),
    );
  }
}

class IdentityDocument {
  constructor(readonly roots: IdentityElement[]) {}

  querySelector(): null {
    return null;
  }

  querySelectorAll(selector: string): IdentityElement[] {
    return flattenIdentityElements(this.roots).filter((element) =>
      matchesIdentitySelector(element, selector),
    );
  }
}

function flattenIdentityElements(elements: IdentityElement[]): IdentityElement[] {
  return elements.flatMap((element) => [element, ...flattenIdentityElements(element.children)]);
}

function matchesIdentitySelector(element: IdentityElement, selector: string): boolean {
  return selector
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean)
    .some((part) => {
      const attributes = Array.from(
        part.matchAll(/\[([a-z-]+)(?:([\^$*]?=)["']?([^\]"']*)["']?)?\]/gi),
      );
      return attributes.every(([, name, operator, expected]) => {
        const actual = element.getAttribute(name);
        if (actual === null) return false;
        if (!operator) return true;
        if (operator === "=") return actual === expected;
        if (operator === "^=") return actual.startsWith(expected);
        if (operator === "*=") return actual.includes(expected);
        if (operator === "$=") return actual.endsWith(expected);
        return false;
      });
    });
}

function evaluateIdentityProbe(document: IdentityDocument, expression: string): unknown {
  class FakeTextArea {}
  return Function(
    "document",
    "HTMLTextAreaElement",
    "location",
    `return ${expression};`,
  )(document, FakeTextArea, { href: "https://chatgpt.com/c/identity-test" });
}

function makeWindowTurn(
  ordinal: number,
  role: "user" | "assistant",
  text: string,
): IdentityElement {
  return new IdentityElement({ "data-testid": `conversation-turn-${ordinal}` }, "", [
    new IdentityElement(
      {
        "data-message-author-role": role,
        "data-turn-id": `${role}-turn-${ordinal}`,
        "data-message-id": `${role}-message-${ordinal}`,
      },
      text,
    ),
  ]);
}

describe("promptComposer", () => {
  test("fails composer clearing when stale text remains", async () => {
    const runtime = {
      evaluate: vi.fn().mockResolvedValue({
        result: { value: { cleared: true, remaining: ["old draft"] } },
      }),
    } as unknown as {
      evaluate: (args: { expression: string; returnByValue?: boolean }) => Promise<unknown>;
    };
    const logger = Object.assign(vi.fn(), { verbose: false });

    await expect(clearPromptComposer(runtime as never, logger as never)).rejects.toThrow(
      /Failed to clear prompt composer/,
    );
  });

  test("does not treat historical assistant content as committed without a new turn", async () => {
    vi.useFakeTimers();
    try {
      const runtime = {
        evaluate: vi
          .fn()
          // Baseline read (turn count)
          .mockResolvedValueOnce({ result: { value: 10 } })
          // Polls (repeat)
          .mockResolvedValue({
            result: {
              value: {
                baseline: 10,
                turnsCount: 10,
                userMatched: false,
                prefixMatched: false,
                lastMatched: false,
                hasNewTurn: false,
                stopVisible: true,
                assistantVisible: true,
                composerCleared: true,
                inConversation: false,
              },
            },
          }),
      } as unknown as {
        evaluate: (args: { expression: string; returnByValue?: boolean }) => Promise<unknown>;
      };

      const promise = promptComposer.verifyPromptCommitted(runtime as never, "hello", 150);
      // Attach the rejection handler before timers advance to avoid unhandled-rejection warnings.
      const assertion = expect(promise).rejects.toThrow(/prompt did not appear/i);
      await vi.advanceTimersByTimeAsync(250);
      await assertion;
    } finally {
      vi.useRealTimers();
    }
  });

  test("returns the identity of a new user turn when its prompt matches", async () => {
    const oldTurn = new IdentityElement(
      {
        "data-testid": "conversation-turn-10",
        "data-message-author-role": "user",
        "data-message-id": "message-old",
      },
      "old prompt",
    );
    const newTurn = new IdentityElement({ "data-testid": "conversation-turn-11" }, "", [
      new IdentityElement(
        {
          "data-message-author-role": "user",
          "data-turn-id": "turn-new",
          "data-message-id": "message-new",
        },
        "new prompt",
      ),
    ]);
    const document = new IdentityDocument([oldTurn, newTurn]);
    const runtime = {
      evaluate: vi.fn(async ({ expression }: { expression: string }) => ({
        result: { value: evaluateIdentityProbe(document, expression) },
      })),
    };

    await expect(
      promptComposer.verifyPromptCommitted(runtime as never, "new prompt", 150, undefined, 2, [
        {
          turnId: null,
          messageId: "message-old",
          testId: "conversation-turn-10",
          absoluteOrdinal: 10,
        },
      ]),
    ).resolves.toEqual({
      turnId: "turn-new",
      messageId: "message-new",
      testId: "conversation-turn-11",
      absoluteOrdinal: 11,
    });
  });

  test("returns turn-7 from a fixed five-turn [conversation-turn-2,3,4,5,6] -> [conversation-turn-4,5,6,7,8] window without count growth", async () => {
    const preSubmitTurns = [
      makeWindowTurn(2, "assistant", "answer 2"),
      makeWindowTurn(3, "user", "prompt 3"),
      makeWindowTurn(4, "assistant", "answer 4"),
      makeWindowTurn(5, "user", "prompt 5"),
      makeWindowTurn(6, "assistant", "answer 6"),
    ];
    const postSubmitTurns = [
      makeWindowTurn(4, "assistant", "answer 4"),
      makeWindowTurn(5, "user", "prompt 5"),
      makeWindowTurn(6, "assistant", "answer 6"),
      makeWindowTurn(7, "user", "sliding-window prompt"),
      makeWindowTurn(8, "assistant", "answer 8"),
    ];
    const document = new IdentityDocument(preSubmitTurns);

    expect(evaluateIdentityProbe(document, buildConversationTurnCountExpression())).toBe(5);

    const runtime = {
      evaluate: vi.fn(async ({ expression }: { expression: string }) => {
        if (expression.includes("document.readyState")) {
          return { result: { value: { ready: true, composer: true, fileInput: false } } };
        }
        if (expression.includes("focused: true")) {
          return { result: { value: { focused: true } } };
        }
        if (expression.includes("editorText")) {
          return {
            result: {
              value: {
                editorText: "sliding-window prompt",
                fallbackValue: "",
                activeValue: "sliding-window prompt",
              },
            },
          };
        }
        if (expression.includes("button.scrollIntoView")) {
          document.roots.splice(0, document.roots.length, ...postSubmitTurns);
          return { result: { value: { status: "clicked" } } };
        }
        if (expression.includes("const allTurns")) {
          return { result: { value: evaluateIdentityProbe(document, expression) } };
        }
        return { result: { value: true } };
      }),
    };
    const input = { insertText: vi.fn(), dispatchKeyEvent: vi.fn() };
    const logger = Object.assign(vi.fn(), { verbose: false });

    const committedUserTurn = await submitPrompt(
      {
        runtime: runtime as never,
        input: input as never,
        baselineTurns: 5,
      },
      "sliding-window prompt",
      logger as never,
    );

    expect(evaluateIdentityProbe(document, buildConversationTurnCountExpression())).toBe(5);
    expect(document.roots.map((turn) => turn.getAttribute("data-testid"))).toEqual([
      "conversation-turn-4",
      "conversation-turn-5",
      "conversation-turn-6",
      "conversation-turn-7",
      "conversation-turn-8",
    ]);
    expect(committedUserTurn).toEqual({
      turnId: "user-turn-7",
      messageId: "user-message-7",
      testId: "conversation-turn-7",
      absoluteOrdinal: 7,
    });
  });

  test("rejects a stale user turn with the same prompt as a new commit", async () => {
    vi.useFakeTimers();
    try {
      const staleTurn = new IdentityElement(
        {
          "data-testid": "conversation-turn-10",
          "data-message-author-role": "user",
          "data-turn-id": "turn-old",
          "data-message-id": "message-old",
        },
        "same prompt",
      );
      const document = new IdentityDocument([staleTurn]);
      const runtime = {
        evaluate: vi.fn(async ({ expression }: { expression: string }) => ({
          result: { value: evaluateIdentityProbe(document, expression) },
        })),
      };
      const promise = promptComposer.verifyPromptCommitted(
        runtime as never,
        "same prompt",
        150,
        undefined,
        1,
        [
          {
            turnId: "turn-old",
            messageId: "message-old",
            testId: "conversation-turn-10",
            absoluteOrdinal: 10,
          },
        ],
      );
      const assertion = expect(promise).rejects.toMatchObject({
        name: "BrowserAutomationError",
        details: expect.objectContaining({ code: "prompt-commit-timeout" }),
      });
      await vi.advanceTimersByTimeAsync(250);
      await assertion;
    } finally {
      vi.useRealTimers();
    }
  });

  test("does not count nested broad-selector matches as new turns in a reused conversation", async () => {
    vi.useFakeTimers();
    try {
      const topLevelTurns = [{ innerText: "old user" }, { innerText: "old assistant" }];
      const nestedMatches = [
        topLevelTurns[0],
        { innerText: "old user" },
        topLevelTurns[1],
        { innerText: "old assistant" },
      ];
      const document = {
        querySelector: () => null,
        querySelectorAll: (selector: string) => {
          if (selector === CONVERSATION_TURN_CONTAINER_SELECTOR) return topLevelTurns;
          if (selector === CONVERSATION_TURN_SELECTOR) return nestedMatches;
          return [];
        },
      };
      class FakeTextArea {}
      const runtime = {
        evaluate: vi.fn(async ({ expression }: { expression: string }) => ({
          result: {
            value: Function(
              "document",
              "HTMLTextAreaElement",
              "location",
              `return ${expression};`,
            )(document, FakeTextArea, { href: "https://chatgpt.com/c/reused" }),
          },
        })),
      } as unknown as {
        evaluate: (args: { expression: string; returnByValue?: boolean }) => Promise<unknown>;
      };

      const promise = promptComposer.verifyPromptCommitted(
        runtime as never,
        "new prompt",
        150,
        undefined,
        2,
      );
      const assertion = expect(promise).rejects.toThrow(/prompt did not appear/i);
      await vi.advanceTimersByTimeAsync(250);
      await assertion;
    } finally {
      vi.useRealTimers();
    }
  });

  test("commit timeout throws a structured error with probe diagnostics", async () => {
    vi.useFakeTimers();
    try {
      const probe = {
        baseline: 10,
        turnsCount: 10,
        userMatched: false,
        prefixMatched: false,
        lastMatched: false,
        hasNewTurn: false,
        stopVisible: false,
        assistantVisible: false,
        composerCleared: true,
        inConversation: false,
        editorValue: "",
        lastTurn: "previous turn text",
      };
      const runtime = {
        evaluate: vi
          .fn()
          // Baseline read (turn count)
          .mockResolvedValueOnce({ result: { value: 10 } })
          // Polls + final diagnostic probe
          .mockResolvedValue({ result: { value: probe } }),
      } as unknown as {
        evaluate: (args: { expression: string; returnByValue?: boolean }) => Promise<unknown>;
      };

      const promise = promptComposer.verifyPromptCommitted(runtime as never, "hello", 150);
      const assertion = promise.then(
        () => {
          throw new Error("expected verifyPromptCommitted to reject");
        },
        (error: unknown) => error,
      );
      await vi.advanceTimersByTimeAsync(250);
      const error = (await assertion) as {
        name?: string;
        details?: Record<string, unknown>;
        message?: string;
      };
      expect(error.message).toMatch(/prompt did not appear/i);
      expect(error.name).toBe("BrowserAutomationError");
      expect(error.details).toMatchObject({
        stage: "submit-prompt",
        code: "prompt-commit-timeout",
        commitProbe: expect.objectContaining({
          hasNewTurn: false,
          composerCleared: true,
          turnsCount: 10,
          lastTurnLength: "previous turn text".length,
        }),
      });
      // Free text must not leak into the structured details.
      const commitProbe = error.details?.commitProbe as Record<string, unknown>;
      expect(commitProbe).not.toHaveProperty("lastTurn");
      expect(commitProbe).not.toHaveProperty("editorValue");
    } finally {
      vi.useRealTimers();
    }
  });

  test("does not allow a prompt match without a stable pre-submit identity set", async () => {
    const runtime = {
      evaluate: vi
        .fn()
        // Baseline read fails
        .mockRejectedValueOnce(new Error("turn read failed"))
        // Polls show a prompt match without a stable identity proof.
        .mockResolvedValue({
          result: {
            value: {
              baseline: -1,
              turnsCount: 1,
              userMatched: true,
              prefixMatched: false,
              lastMatched: true,
              hasNewTurn: false,
              stopVisible: false,
              assistantVisible: false,
              composerCleared: false,
              inConversation: true,
            },
          },
        }),
    } as unknown as {
      evaluate: (args: { expression: string; returnByValue?: boolean }) => Promise<unknown>;
    };

    await expect(
      promptComposer.verifyPromptCommitted(runtime as never, "hello", 150),
    ).rejects.toMatchObject({
      name: "BrowserAutomationError",
      details: expect.objectContaining({ code: "prompt-commit-timeout" }),
    });
  });

  test("attachment sends time out instead of allowing Enter fallback", async () => {
    vi.useFakeTimers();
    try {
      const runtime = {
        evaluate: vi.fn(async ({ expression }: { expression: string }) => {
          if (expression.includes("dispatchClickSequence")) {
            return { result: { value: { status: "disabled" } } };
          }
          return { result: { value: true } };
        }),
      } as unknown as {
        evaluate: (args: { expression: string; returnByValue?: boolean }) => Promise<unknown>;
      };

      const promise = promptComposer.attemptSendButton(
        runtime as never,
        (() => undefined) as never,
        undefined,
        ["oracle-attach-verify.txt"],
      );
      const assertion = expect(promise).rejects.toThrow(/after 45s/i);
      await vi.advanceTimersByTimeAsync(46_000);
      await assertion;
    } finally {
      vi.useRealTimers();
    }
  });

  test("only attachment sends get the longer send-button deadline", () => {
    expect(promptComposer.sendButtonTimeoutMs()).toBe(20_000);
    expect(promptComposer.sendButtonTimeoutMs([])).toBe(20_000);
    expect(promptComposer.sendButtonTimeoutMs(["oracle-attach-verify.txt"])).toBe(45_000);
    expect(promptComposer.sendButtonTimeoutMs(["oracle-attach-verify.txt"], 120_000)).toBe(120_000);
  });

  test("marks prompt submitted before commit verification finishes", async () => {
    const onPromptSubmitted = vi.fn();
    const runtime = {
      evaluate: vi.fn(async ({ expression }: { expression: string }) => {
        if (expression.includes("document.readyState")) {
          return { result: { value: { ready: true, composer: true, fileInput: false } } };
        }
        if (expression.includes("focused: true")) {
          return { result: { value: { focused: true } } };
        }
        if (expression.includes("editorText")) {
          return {
            result: { value: { editorText: "hello", fallbackValue: "", activeValue: "hello" } },
          };
        }
        if (expression.includes("button.scrollIntoView")) {
          return { result: { value: { status: "clicked" } } };
        }
        if (expression.includes("const userTurnCandidates")) {
          return {
            result: {
              value: {
                baseline: 0,
                turnsCount: 1,
                userMatched: true,
                prefixMatched: false,
                lastMatched: true,
                hasNewTurn: true,
                stableIdentityProof: true,
                committedUserTurn: {
                  turnId: "turn-new",
                  messageId: "message-new",
                  testId: "conversation-turn-1",
                  absoluteOrdinal: 1,
                },
                stopVisible: true,
                assistantVisible: false,
                composerCleared: true,
                inConversation: true,
              },
            },
          };
        }
        if (expression.includes("const allTurns")) {
          return { result: { value: [] } };
        }
        return {
          result: {
            value: {
              baseline: 0,
              turnsCount: 1,
              userMatched: true,
              prefixMatched: false,
              lastMatched: true,
              hasNewTurn: true,
              stopVisible: true,
              assistantVisible: false,
              composerCleared: true,
              inConversation: true,
            },
          },
        };
      }),
    };
    const input = { insertText: vi.fn(), dispatchKeyEvent: vi.fn() };
    const logger = Object.assign(vi.fn(), { verbose: false });

    const committedUserTurn = await submitPrompt(
      {
        runtime: runtime as never,
        input: input as never,
        baselineTurns: 0,
        onPromptSubmitted,
      },
      "hello",
      logger as never,
    );

    expect(onPromptSubmitted).toHaveBeenCalledTimes(1);
    expect(committedUserTurn).toEqual({
      turnId: "turn-new",
      messageId: "message-new",
      testId: "conversation-turn-1",
      absoluteOrdinal: 1,
    });
    const expressions = runtime.evaluate.mock.calls.map(([args]) => args.expression);
    expect(
      expressions.findIndex((expression) => expression.includes("const allTurns")),
    ).toBeLessThan(
      expressions.findIndex((expression) => expression.includes("button.scrollIntoView")),
    );
  });

  test("waits for a delayed trusted click without issuing a second send", async () => {
    vi.useFakeTimers();
    try {
      const evaluate = vi.fn().mockResolvedValue({
        result: { value: { status: "point", x: 10, y: 20 } },
      });
      const input = {
        dispatchMouseEvent: vi.fn(async ({ type }: { type: string }) => {
          if (type === "mouseReleased") {
            await new Promise((resolve) => setTimeout(resolve, 1_000));
          }
        }),
      };

      const result = promptComposer.attemptSendButton(
        { evaluate } as never,
        input as never,
        undefined,
        undefined,
      );
      await vi.advanceTimersByTimeAsync(1_000);

      await expect(result).resolves.toBe(true);
      expect(evaluate).toHaveBeenCalledTimes(1);
      expect(input.dispatchMouseEvent).toHaveBeenCalledTimes(3);
    } finally {
      vi.useRealTimers();
    }
  });
});
