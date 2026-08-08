import { createContext, Script } from "node:vm";
import { describe, expect, test, vi } from "vitest";
import {
  bindAssistantTurnIdentity,
  buildAssistantTurnIdentityBindingExpressionForTest,
  buildActiveThinkingStatusPredicateJsForTest,
  buildResponseObserverExpressionForTest,
  buildAssistantSnapshotExpressionForTest,
  buildCompletionVisibilityExpressionForTest,
  buildMarkdownFallbackExtractorForTest,
  buildStopButtonVisibilityExpressionForTest,
  classifyTurnTerminal,
  createTerminalGateState,
  hasScopedCompletionProof,
  matchesThinkingStatusLabelForTest,
  readAssistantSnapshot,
  type TerminalGateConfig,
  type TerminalSample,
  type AssistantResponseIdentityScope,
} from "../../src/browser/actions/assistantResponse.js";
import {
  buildConversationTurnCountExpression,
  type ConversationTurnIdentity,
} from "../../src/browser/conversationTurns.js";
import {
  buildThinkingActivePredicateJsForTest,
  buildThinkingActivityDetailsPredicateJsForTest,
} from "../../src/browser/actions/thinkingStatus.js";
import { STOP_BUTTON_SELECTORS } from "../../src/browser/constants.js";

// Completed-summary shapes the veto must treat as NOT active: bare, heading-prefixed
// (the GPT-5.6 DOM renders "Reasoning Thought for 12s"), worded non-numeric durations,
// and heading fragments that concatenate without whitespace (CSS-spaced siblings).
const COMPLETED_SUMMARY_LABELS = [
  "Thought for 12s",
  "Reasoning Thought for 12s",
  "Thought for a few seconds",
  "Reasoning Thought for a moment",
  "ReasoningThought for 12s",
  "Thought for 1m 5s",
  "Reasoning Thought for 12s Edit",
  "Pro thinking Thought for 3.5s Edit",
];

function evaluatePredicate(text: string, generating: boolean): boolean {
  const predicate = buildActiveThinkingStatusPredicateJsForTest("isActiveThinkingStatus");
  class FakeHtmlElement {
    getBoundingClientRect() {
      return { width: 120, height: 40 };
    }
  }
  const context = createContext({
    Array,
    Number,
    String,
    HTMLElement: FakeHtmlElement,
    document: {
      querySelectorAll: () => (generating ? [new FakeHtmlElement()] : []),
    },
    window: {
      getComputedStyle: () => ({ display: "block", visibility: "visible", opacity: "1" }),
    },
  });
  return new Script(
    `${predicate}\nisActiveThinkingStatus({ text: ${JSON.stringify(text)} });`,
  ).runInContext(context) as boolean;
}

describe("assistant thinking-status capture", () => {
  const statusLabels = [
    "Pro thinking",
    "Finalizing answer",
    "Thinking",
    "Reading",
    "Thought for 12s",
    "Pro thinking - planning",
  ];

  test.each(statusLabels)("suppresses active status label %j", (label) => {
    expect(matchesThinkingStatusLabelForTest(label)).toBe(true);
    expect(evaluatePredicate(label, true)).toBe(true);
  });

  test.each(statusLabels)("preserves completed exact answer %j", (label) => {
    expect(evaluatePredicate(label, false)).toBe(false);
  });

  test("does not suppress normal text while generation is active", () => {
    expect(evaluatePredicate("Thinking about the design, use Postgres.", true)).toBe(false);
  });

  test.each(["Reasoning Thought for 12s", "Thought for a few seconds"])(
    "recognizes prefixed/worded completed summary %s as status chrome, not an answer",
    (label) => {
      expect(matchesThinkingStatusLabelForTest(label)).toBe(true);
      expect(evaluatePredicate(label, true)).toBe(true);
    },
  );

  test("does not treat a real answer mentioning 'thought for' as status chrome", () => {
    // Longer than the 40-char status cap: must never be held back as a placeholder.
    const answer = "I thought for a while about this tradeoff and Postgres still wins.";
    expect(matchesThinkingStatusLabelForTest(answer)).toBe(false);
    expect(evaluatePredicate(answer, true)).toBe(false);
  });

  test("uses the active-status predicate in snapshot capture", () => {
    const expression = buildAssistantSnapshotExpressionForTest();
    expect(expression).toContain("isActiveThinkingStatus");
    expect(expression).toContain('data-testid=\\"stop-button\\"');
    expect(expression).toContain("const fallback = extractFallback();");
  });

  test("aria-label stop fallback is scoped to the composer and excludes non-generation stops", () => {
    // Post-merge review of #285: a document-wide button[aria-label*="stop"] match let ANY
    // visible stop control (read-aloud, voice/dictation) hold isStopButtonVisible() true and
    // stall completion until the response timeout. Pin the scoping + exclusions.
    const fallback = STOP_BUTTON_SELECTORS.find((s) => s.includes('aria-label*="stop"'));
    expect(fallback).toBeDefined();
    expect(fallback).toMatch(/^form /);
    expect(fallback).toContain(':not([aria-label*="dictat" i])');
    expect(fallback).toContain(':not([aria-label*="voice" i])');
    expect(fallback).toContain(':not([aria-label*="read" i])');
  });

  test("shares all stop-control selectors with completion capture", () => {
    let observedSelector = "";
    new Script(buildStopButtonVisibilityExpressionForTest()).runInContext(
      createContext({
        Array,
        Number,
        HTMLElement: class {},
        document: {
          querySelectorAll: (selector: string) => {
            observedSelector = selector;
            return [];
          },
        },
        window: { getComputedStyle: () => ({}) },
      }),
    );
    expect(observedSelector).toBe(STOP_BUTTON_SELECTORS.join(", "));
  });

  test.each([
    {
      width: 120,
      height: 40,
      display: "block",
      visibility: "visible",
      opacity: "1",
      expected: true,
    },
    {
      width: 0,
      height: 40,
      display: "block",
      visibility: "visible",
      opacity: "1",
      expected: false,
    },
    {
      width: 120,
      height: 40,
      display: "none",
      visibility: "visible",
      opacity: "1",
      expected: false,
    },
  ])("requires a visible stop control before blocking completion: %o", (fixture) => {
    class FakeHtmlElement {
      getBoundingClientRect() {
        return { width: fixture.width, height: fixture.height };
      }
    }
    const result = new Script(buildStopButtonVisibilityExpressionForTest()).runInContext(
      createContext({
        Array,
        Number,
        HTMLElement: FakeHtmlElement,
        document: { querySelectorAll: () => [new FakeHtmlElement()] },
        window: {
          getComputedStyle: () => ({
            display: fixture.display,
            visibility: fixture.visibility,
            opacity: fixture.opacity,
          }),
        },
      }),
    );
    expect(result).toBe(fixture.expected);
  });
});

describe("completion action correlation", () => {
  class FakeTurn {
    public dataset: Record<string, string> = {};
    constructor(
      private attrs: Record<string, string>,
      private finished: boolean,
    ) {}
    getAttribute(name: string): string | null {
      return this.attrs[name] ?? null;
    }
    querySelector(): object | null {
      return this.finished ? {} : null;
    }
    querySelectorAll(): FakeTurn[] {
      return [];
    }
  }

  function evaluateCompletionVisibility(args: {
    messageId?: string;
    minTurnIndex?: number;
    turns: FakeTurn[];
  }): boolean {
    const expression = buildCompletionVisibilityExpressionForTest(
      { messageId: args.messageId },
      args.minTurnIndex,
    );
    const context = createContext({
      Array,
      Boolean,
      HTMLElement: FakeTurn,
      document: { querySelectorAll: () => args.turns },
    });
    return new Script(expression).runInContext(context) as boolean;
  }

  test("rejects a persistent action bar from before the new-turn baseline", () => {
    const oldTurn = new FakeTurn(
      { "data-turn": "assistant", "data-message-id": "old-message" },
      true,
    );
    expect(evaluateCompletionVisibility({ minTurnIndex: 1, turns: [oldTurn] })).toBe(false);
  });

  test("accepts controls correlated to the sampled message identity", () => {
    const currentTurn = new FakeTurn(
      { "data-turn": "assistant", "data-message-id": "current-message" },
      true,
    );
    expect(
      evaluateCompletionVisibility({ messageId: "current-message", turns: [currentTurn] }),
    ).toBe(true);
  });

  test("rejects controls whose assistant identity differs from the sample", () => {
    const oldTurn = new FakeTurn(
      { "data-turn": "assistant", "data-message-id": "old-message" },
      true,
    );
    expect(evaluateCompletionVisibility({ messageId: "new-message", turns: [oldTurn] })).toBe(
      false,
    );
  });

  test("accepts completion controls scoped by the fallback extractor", () => {
    expect(hasScopedCompletionProof({ completionVisible: true })).toBe(true);
    expect(hasScopedCompletionProof({})).toBe(false);
  });

  test("fallback snapshots carry only node-scoped completion evidence", () => {
    const expression = buildMarkdownFallbackExtractorForTest("1");
    expect(expression).toContain("completionVisible: actionMarkdowns.includes(node)");
    expect(expression).toContain("return Boolean(lastUser.compareDocumentPosition(node) & 4)");
    expect(expression).toContain("if (!hasTurns) return isAfterCurrentUser(node)");
  });
});

describe("assistant turn identity binding", () => {
  class BindingElement {
    parentElement: BindingElement | null = null;

    constructor(
      private readonly attributes: Record<string, string> = {},
      private readonly ownText = "",
      readonly children: BindingElement[] = [],
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

    getBoundingClientRect() {
      return { left: 0, top: 0, width: 120, height: 40, right: 120, bottom: 40 };
    }

    get innerHTML(): string {
      return this.textContent;
    }

    getAttribute(name: string): string | null {
      return this.attributes[name] ?? null;
    }

    contains(node: BindingElement): boolean {
      return this.children.some((child) => child === node || child.contains(node));
    }

    querySelectorAll(selector: string): BindingElement[] {
      return flattenBindingElements(this.children).filter((element) =>
        matchesBindingSelector(element, selector),
      );
    }

    querySelector(selector: string): BindingElement | null {
      return this.querySelectorAll(selector)[0] ?? null;
    }
  }

  class BindingDocument {
    readonly body: BindingElement;

    constructor(readonly roots: BindingElement[]) {
      this.body = new BindingElement({}, "", roots);
    }

    querySelector(): null {
      return null;
    }

    querySelectorAll(selector: string): BindingElement[] {
      return flattenBindingElements(this.roots).filter((element) =>
        matchesBindingSelector(element, selector),
      );
    }
  }

  function flattenBindingElements(elements: BindingElement[]): BindingElement[] {
    return elements.flatMap((element) => [element, ...flattenBindingElements(element.children)]);
  }

  function matchesBindingSelector(element: BindingElement, selector: string): boolean {
    return selector
      .split(",")
      .map((part) => part.trim())
      .filter(Boolean)
      .some((part) => {
        const attributes = Array.from(
          part.matchAll(/\[([a-z-]+)(?:([\^$*]?=)["']?([^\]"']*)["']?)?\]/gi),
        );
        if (attributes.length === 0) return false;
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

  function makeTurn(
    testId: string,
    role: "user" | "assistant",
    turnId: string,
    messageId?: string,
    text = "",
  ): BindingElement {
    return new BindingElement({ "data-testid": testId }, "", [
      new BindingElement(
        {
          "data-message-author-role": role,
          "data-turn-id": turnId,
          ...(messageId ? { "data-message-id": messageId } : {}),
        },
        text,
      ),
    ]);
  }

  function makeUnnumberedTurn(role: "user" | "assistant", turnId: string): BindingElement {
    return new BindingElement({
      "data-message-author-role": role,
      "data-turn-id": turnId,
    });
  }

  function evaluateBinding(
    document: BindingDocument,
    user: ConversationTurnIdentity,
  ): ConversationTurnIdentity | null {
    return Function(
      "document",
      `return ${buildAssistantTurnIdentityBindingExpressionForTest(user)};`,
    )(document) as ConversationTurnIdentity | null;
  }

  function evaluateSnapshot(
    document: BindingDocument,
    expression: string,
  ): Record<string, unknown> | null {
    return Function(
      "document",
      "HTMLElement",
      "location",
      "window",
      `return ${expression};`,
    )(
      document,
      BindingElement,
      { href: "https://chatgpt.com/c/identity-test" },
      {
        getComputedStyle: () => ({ display: "block", visibility: "visible", opacity: "1" }),
      },
    ) as Record<string, unknown> | null;
  }

  function evaluateTurnCount(document: BindingDocument): number {
    return Function(
      "document",
      `return ${buildConversationTurnCountExpression()};`,
    )(document) as number;
  }

  async function evaluateObserver(
    document: BindingDocument,
    expression: string,
  ): Promise<Record<string, unknown> | null> {
    class FakeMutationObserver {
      observe(): void {}

      disconnect(): void {}
    }
    return (await Function(
      "document",
      "HTMLElement",
      "HTMLProgressElement",
      "location",
      "window",
      "MutationObserver",
      `return ${expression};`,
    )(
      document,
      BindingElement,
      class {},
      { href: "https://chatgpt.com/c/identity-test" },
      {
        getComputedStyle: () => ({ display: "block", visibility: "visible", opacity: "1" }),
        innerHeight: 900,
        innerWidth: 1440,
      },
      FakeMutationObserver,
    )) as Record<string, unknown> | null;
  }

  function evaluateCompletion(document: BindingDocument, expression: string): boolean {
    return Function(
      "document",
      "HTMLElement",
      `return ${expression};`,
    )(document, BindingElement) as boolean;
  }

  function makeFinishedAssistantTurn(
    testId: string,
    turnId: string,
    messageId: string,
    text: string,
    finished = true,
  ): BindingElement {
    return new BindingElement({ "data-testid": testId }, "", [
      new BindingElement(
        {
          "data-message-author-role": "assistant",
          "data-turn-id": turnId,
          "data-message-id": messageId,
        },
        text,
        finished ? [new BindingElement({ "data-testid": "copy-turn-action-button" })] : [],
      ),
    ]);
  }

  const committedUser: ConversationTurnIdentity = {
    turnId: "user-turn-10",
    messageId: "user-message-10",
    testId: "conversation-turn-10",
    absoluteOrdinal: 10,
  };

  test("binds a placeholder assistant without a message ID", async () => {
    const document = new BindingDocument([
      makeTurn("conversation-turn-10", "user", "user-turn-10", "user-message-10"),
      makeTurn("conversation-turn-11", "assistant", "assistant-turn-11"),
    ]);
    const runtime = {
      evaluate: vi.fn().mockResolvedValue({
        result: { value: evaluateBinding(document, committedUser) },
      }),
    };

    await expect(bindAssistantTurnIdentity(runtime as never, committedUser, 0)).resolves.toEqual({
      turnId: "assistant-turn-11",
      messageId: null,
      testId: "conversation-turn-11",
      absoluteOrdinal: 11,
    });
  });

  test("falls back to the immediate top-level assistant when no ordinal is available", () => {
    const user = makeUnnumberedTurn("user", "user-without-ordinal");
    const document = new BindingDocument([
      makeUnnumberedTurn("assistant", "stale-assistant"),
      user,
      makeUnnumberedTurn("assistant", "owned-assistant"),
      makeUnnumberedTurn("assistant", "unrelated-latest"),
    ]);

    expect(
      evaluateBinding(document, {
        turnId: "user-without-ordinal",
        messageId: null,
        testId: null,
        absoluteOrdinal: null,
      }),
    ).toEqual({
      turnId: "owned-assistant",
      messageId: null,
      testId: null,
      absoluteOrdinal: null,
    });
  });

  test("chooses the owned assistant over stale and unrelated latest assistants", () => {
    const document = new BindingDocument([
      makeTurn("conversation-turn-9", "assistant", "stale-assistant-9", "stale-message-9"),
      makeTurn("conversation-turn-10", "user", "user-turn-10", "user-message-10"),
      makeTurn("conversation-turn-11", "assistant", "owned-assistant-11", "owned-message-11"),
      makeTurn("conversation-turn-12", "assistant", "latest-assistant-12", "latest-message-12"),
    ]);

    expect(evaluateBinding(document, committedUser)).toEqual({
      turnId: "owned-assistant-11",
      messageId: "owned-message-11",
      testId: "conversation-turn-11",
      absoluteOrdinal: 11,
    });
  });

  test("does not infer an assistant when the committed user anchor is absent", () => {
    const document = new BindingDocument([
      makeTurn("conversation-turn-11", "assistant", "assistant-turn-11"),
      makeTurn("conversation-turn-12", "assistant", "assistant-turn-12", "message-12"),
    ]);

    expect(evaluateBinding(document, committedUser)).toBeNull();
  });

  test("keeps the bound identity after a DOM prefix is removed", () => {
    const stale = makeTurn("conversation-turn-9", "assistant", "stale-assistant-9");
    const user = makeTurn("conversation-turn-10", "user", "user-turn-10", "user-message-10");
    const owned = makeTurn("conversation-turn-11", "assistant", "owned-assistant-11");
    const latest = makeTurn("conversation-turn-12", "assistant", "latest-assistant-12");
    const document = new BindingDocument([stale, user, owned, latest]);

    const first = evaluateBinding(document, committedUser);
    document.roots.splice(0, 1);
    const afterPrefixRemoval = evaluateBinding(document, committedUser);

    expect(afterPrefixRemoval).toEqual(first);
  });

  test("rejects a contradictory user identity instead of choosing one field's node", () => {
    const contradictoryUser = new BindingElement({ "data-testid": "conversation-turn-10" }, "", [
      new BindingElement({
        "data-message-author-role": "user",
        "data-turn-id": "user-turn-10",
        "data-message-id": "different-message-10",
      }),
    ]);
    const document = new BindingDocument([
      contradictoryUser,
      makeTurn("conversation-turn-11", "assistant", "assistant-turn-11"),
    ]);

    expect(evaluateBinding(document, committedUser)).toBeNull();
  });

  test("accepts the owned assistant after its DOM index drops and IDs are refreshed", async () => {
    const document = new BindingDocument([
      makeTurn("conversation-turn-10", "user", "user-turn-10", "user-message-10"),
      makeTurn(
        "conversation-turn-11",
        "assistant",
        "assistant-turn-final",
        "final-message",
        "owned answer",
      ),
      makeTurn("conversation-turn-12", "assistant", "latest-assistant-12", "latest-message-12"),
    ]);
    const scope = {
      committedUserTurn: committedUser,
      committedAssistantTurn: {
        turnId: "assistant-turn-placeholder",
        messageId: "placeholder-message",
        testId: "conversation-turn-11",
        absoluteOrdinal: 11,
      },
    } satisfies AssistantResponseIdentityScope;
    const expression = buildAssistantSnapshotExpressionForTest(99, undefined, scope);
    const runtime = {
      evaluate: vi.fn().mockResolvedValue({
        result: { value: evaluateSnapshot(document, expression) },
      }),
    };

    await expect(
      readAssistantSnapshot(runtime as never, 99, undefined, scope),
    ).resolves.toMatchObject({
      text: "owned answer",
      turnIndex: 1,
    });
    const snapshot = evaluateSnapshot(document, expression);
    expect(snapshot).toMatchObject({ text: "owned answer", turnIndex: 1 });
    expect(buildResponseObserverExpressionForTest(1_000, 99, undefined, scope)).toContain(
      "if (!HAS_IDENTITY_SCOPE && MIN_TURN_INDEX >= 0)",
    );
  });

  test("accepts turn-8 at current index 4 in [conversation-turn-4,5,6,7,8] after [conversation-turn-2,3,4,5,6] slides, even with legacy minTurnIndex 5", async () => {
    const preSubmitDocument = new BindingDocument([
      makeTurn("conversation-turn-2", "assistant", "assistant-turn-2", "assistant-message-2"),
      makeTurn("conversation-turn-3", "user", "user-turn-3", "user-message-3"),
      makeTurn("conversation-turn-4", "assistant", "assistant-turn-4", "assistant-message-4"),
      makeTurn("conversation-turn-5", "user", "user-turn-5", "user-message-5"),
      makeTurn("conversation-turn-6", "assistant", "assistant-turn-6", "assistant-message-6"),
    ]);
    const postSubmitDocument = new BindingDocument([
      makeTurn("conversation-turn-4", "assistant", "assistant-turn-4", "assistant-message-4"),
      makeTurn("conversation-turn-5", "user", "user-turn-5", "user-message-5"),
      makeTurn("conversation-turn-6", "assistant", "assistant-turn-6", "assistant-message-6"),
      makeTurn("conversation-turn-7", "user", "user-turn-7", "user-message-7"),
      makeFinishedAssistantTurn(
        "conversation-turn-8",
        "assistant-turn-8",
        "assistant-message-8",
        "owned turn-8 answer",
      ),
    ]);
    const committedUserTurn: ConversationTurnIdentity = {
      turnId: "user-turn-7",
      messageId: "user-message-7",
      testId: "conversation-turn-7",
      absoluteOrdinal: 7,
    };
    const scope: AssistantResponseIdentityScope = {
      committedUserTurn,
      committedAssistantTurn: null,
    };

    expect(evaluateTurnCount(preSubmitDocument)).toBe(5);
    expect(evaluateTurnCount(postSubmitDocument)).toBe(5);
    expect(postSubmitDocument.roots.map((turn) => turn.getAttribute("data-testid"))).toEqual([
      "conversation-turn-4",
      "conversation-turn-5",
      "conversation-turn-6",
      "conversation-turn-7",
      "conversation-turn-8",
    ]);
    expect(evaluateBinding(postSubmitDocument, committedUserTurn)).toEqual({
      turnId: "assistant-turn-8",
      messageId: "assistant-message-8",
      testId: "conversation-turn-8",
      absoluteOrdinal: 8,
    });

    const snapshotExpression = buildAssistantSnapshotExpressionForTest(5, undefined, scope);
    const runtime = {
      evaluate: vi.fn().mockResolvedValue({
        result: { value: evaluateSnapshot(postSubmitDocument, snapshotExpression) },
      }),
    };
    await expect(
      readAssistantSnapshot(runtime as never, 5, undefined, scope),
    ).resolves.toMatchObject({
      text: "owned turn-8 answer",
      turnIndex: 4,
    });

    vi.useFakeTimers();
    try {
      const observerResult = evaluateObserver(
        postSubmitDocument,
        buildResponseObserverExpressionForTest(1_000, 5, undefined, scope),
      );
      await vi.advanceTimersByTimeAsync(400);
      await expect(observerResult).resolves.toMatchObject({
        text: "owned turn-8 answer",
        turnIndex: 4,
      });
    } finally {
      vi.useRealTimers();
    }
  });

  test("binds the owned assistant from the committed user when the scope has no assistant yet", () => {
    const document = new BindingDocument([
      makeTurn("conversation-turn-10", "user", "user-turn-10", "user-message-10"),
      makeTurn(
        "conversation-turn-11",
        "assistant",
        "assistant-turn-bound",
        "bound-message",
        "bound answer",
      ),
      makeTurn("conversation-turn-12", "assistant", "latest-assistant-12", "latest-message-12"),
    ]);
    const scope: AssistantResponseIdentityScope = {
      committedUserTurn: committedUser,
      committedAssistantTurn: null,
    };

    expect(
      evaluateSnapshot(document, buildAssistantSnapshotExpressionForTest(99, undefined, scope)),
    ).toMatchObject({ text: "bound answer", turnIndex: 1 });
  });

  test("rejects a different latest assistant instead of using the stable-scope fallback", () => {
    const document = new BindingDocument([
      makeTurn("conversation-turn-10", "user", "user-turn-10", "user-message-10"),
      makeTurn(
        "conversation-turn-12",
        "assistant",
        "latest-assistant-12",
        "latest-message-12",
        "unrelated latest",
      ),
    ]);
    const scope: AssistantResponseIdentityScope = {
      committedUserTurn: committedUser,
      committedAssistantTurn: {
        turnId: "assistant-turn-11",
        messageId: "owned-message-11",
        testId: "conversation-turn-11",
        absoluteOrdinal: 11,
      },
    };

    expect(
      evaluateSnapshot(document, buildAssistantSnapshotExpressionForTest(0, undefined, scope)),
    ).toBeNull();
  });

  test("does not return turn-6 or unrelated turn-9 when [conversation-turn-6,7] lacks owned turn-8", () => {
    const committedUserTurn: ConversationTurnIdentity = {
      turnId: "user-turn-7",
      messageId: "user-message-7",
      testId: "conversation-turn-7",
      absoluteOrdinal: 7,
    };
    const scope: AssistantResponseIdentityScope = {
      committedUserTurn,
      committedAssistantTurn: null,
    };
    const postSubmitWithoutOwnedAssistant = new BindingDocument([
      makeFinishedAssistantTurn(
        "conversation-turn-6",
        "assistant-turn-6",
        "assistant-message-6",
        "completed turn-6 answer",
      ),
      makeTurn("conversation-turn-7", "user", "user-turn-7", "user-message-7", "new prompt"),
    ]);

    expect(
      evaluateSnapshot(
        postSubmitWithoutOwnedAssistant,
        buildAssistantSnapshotExpressionForTest(5, undefined, scope),
      ),
    ).toBeNull();

    const unrelatedLatestAssistant = new BindingDocument([
      ...postSubmitWithoutOwnedAssistant.roots,
      makeFinishedAssistantTurn(
        "conversation-turn-9",
        "assistant-turn-9",
        "assistant-message-9",
        "unrelated latest answer",
      ),
    ]);
    expect(
      evaluateSnapshot(
        unrelatedLatestAssistant,
        buildAssistantSnapshotExpressionForTest(5, undefined, scope),
      ),
    ).toBeNull();
    expect(evaluateBinding(unrelatedLatestAssistant, committedUserTurn)).toBeNull();
  });

  test("correlates completion action bars to the same scoped assistant turn", () => {
    const scope: AssistantResponseIdentityScope = {
      committedUserTurn: committedUser,
      committedAssistantTurn: {
        turnId: "assistant-turn-11",
        messageId: "owned-message-11",
        testId: "conversation-turn-11",
        absoluteOrdinal: 11,
      },
    };
    const expression = buildCompletionVisibilityExpressionForTest({}, 99, scope);
    const ownedWithAction = new BindingDocument([
      makeTurn("conversation-turn-10", "user", "user-turn-10", "user-message-10"),
      makeFinishedAssistantTurn(
        "conversation-turn-11",
        "assistant-turn-final",
        "final-message",
        "owned answer",
      ),
      makeFinishedAssistantTurn(
        "conversation-turn-12",
        "latest-assistant-12",
        "latest-message-12",
        "latest answer",
      ),
    ]);
    expect(evaluateCompletion(ownedWithAction, expression)).toBe(true);

    const onlyLatestHasAction = new BindingDocument([
      makeTurn("conversation-turn-10", "user", "user-turn-10", "user-message-10"),
      makeFinishedAssistantTurn(
        "conversation-turn-11",
        "assistant-turn-final",
        "final-message",
        "owned answer",
        false,
      ),
      makeFinishedAssistantTurn(
        "conversation-turn-12",
        "latest-assistant-12",
        "latest-message-12",
        "latest answer",
      ),
    ]);
    expect(evaluateCompletion(onlyLatestHasAction, expression)).toBe(false);
  });
});

describe("classifyTurnTerminal", () => {
  const config: TerminalGateConfig = {
    barConfirmCycles: 3,
    minStableMs: 200,
  };

  // Drive the pure classifier over a sequence of samples (each 400ms apart by default),
  // returning the per-sample terminal decisions.
  function runGate(
    samples: Array<Partial<TerminalSample> & { len: number }>,
    cfg: TerminalGateConfig = config,
    stepMs = 400,
  ): boolean[] {
    let now = 0;
    let state = createTerminalGateState(now);
    const out: boolean[] = [];
    for (const partial of samples) {
      const sample: TerminalSample = {
        now,
        len: partial.len,
        // Default fingerprint = the length, so a changing length reads as "still moving"; tests
        // that need an equal-length rewrite pass an explicit contentKey.
        contentKey: partial.contentKey ?? String(partial.len),
        stopVisible: partial.stopVisible ?? false,
        barVisible: partial.barVisible ?? false,
        strongThinkingActive: partial.strongThinkingActive ?? false,
      };
      const result = classifyTurnTerminal(state, sample, cfg);
      state = result.state;
      out.push(result.terminal);
      now += stepMs;
    }
    return out;
  }

  test("never finalizes while the stop control is visible", () => {
    const out = runGate(Array.from({ length: 20 }, () => ({ len: 400, stopVisible: true })));
    expect(out.some(Boolean)).toBe(false);
  });

  test("holds a settled long preamble until the reasoning phase resolves", () => {
    // A 150-char preamble settles (stop gone, no bar), then thinking mounts for ~4s, then the
    // real answer streams and its action bar appears. It must NOT finalize the preamble.
    const samples: Array<Partial<TerminalSample> & { len: number }> = [];
    // preamble streaming
    for (let i = 0; i < 3; i++) samples.push({ len: 50 * (i + 1), stopVisible: true });
    // settle gap: stop gone, no bar, no thinking yet (the exact window the bug exploited)
    for (let i = 0; i < 2; i++) samples.push({ len: 150 });
    // thinking phase mounts (connector/reasoning)
    for (let i = 0; i < 10; i++) samples.push({ len: 150, strongThinkingActive: true });
    // real answer streams after thinking, bar appears and debounces
    samples.push({ len: 600, stopVisible: true });
    samples.push({ len: 900, stopVisible: true });
    for (let i = 0; i < 5; i++) samples.push({ len: 900, barVisible: true });
    const out = runGate(samples);
    // No terminal:true may occur before the real answer streamed (index of first len>150).
    const firstAnswerIdx = samples.findIndex((s) => s.len > 150);
    const finalizedEarly = out.slice(0, firstAnswerIdx).some(Boolean);
    expect(finalizedEarly).toBe(false);
    // It DOES finalize once the real answer's bar debounces.
    expect(out.some(Boolean)).toBe(true);
  });

  test("proofA: a debounced action bar finalizes (and bypasses the thinking veto)", () => {
    const out = runGate([
      { len: 800, stopVisible: true }, // streaming
      { len: 800, barVisible: true }, // grew stopped; bar appears (cycle 1)
      { len: 800, barVisible: true }, // cycle 2
      { len: 800, barVisible: true }, // cycle 3 -> barStableCycles reaches 3
      { len: 800, barVisible: true },
    ]);
    // First three post-stream cycles build the debounce; terminal by the time cycles>=3.
    expect(out.at(-1)).toBe(true);
  });

  test("proofA fires even if weak stale-sidecar evidence lingers", () => {
    const out = runGate([
      { len: 800, stopVisible: true },
      { len: 800, barVisible: true },
      { len: 800, barVisible: true },
      { len: 800, barVisible: true },
      { len: 800, barVisible: true },
    ]);
    // Weak activity can be a stale mounted sidecar; the debounced bar may override it.
    expect(out.at(-1)).toBe(true);
  });

  test("proofA cannot override strong live activity and rebuilds its debounce afterward", () => {
    const samples: Array<Partial<TerminalSample> & { len: number }> = [
      { len: 800, stopVisible: true },
    ];
    for (let i = 0; i < 5; i++) {
      samples.push({
        len: 800,
        barVisible: true,
        strongThinkingActive: true,
      });
    }
    samples.push({ len: 800, barVisible: true });
    samples.push({ len: 800, barVisible: true });
    samples.push({ len: 800, barVisible: true });
    const out = runGate(samples);
    expect(out.slice(0, 6).some(Boolean)).toBe(false);
    expect(out.at(-1)).toBe(true);
  });

  test("proofA does NOT finalize a transient bar while the answer is still rendering", () => {
    // Repo history: finished-action controls can surface while only the first tokens exist.
    // The bar is present the whole time, but the text keeps changing, so proofA must not fire.
    const out = runGate([
      { len: 4, barVisible: true },
      { len: 8, barVisible: true },
      { len: 12, barVisible: true },
      { len: 40, barVisible: true },
      { len: 90, barVisible: true },
    ]);
    expect(out.some(Boolean)).toBe(false);
  });

  test("any content change (even equal length) resets the stability clocks", () => {
    // An equal-length rewrite (preamble replaced by an answer of the same length) must reset:
    // length-only tracking would have treated it as stable and could finalize mid-rewrite.
    const out = runGate([
      { len: 200, barVisible: true, contentKey: "preamble-aaaaaaaaaaaaaaaaaaaa" },
      { len: 200, barVisible: true, contentKey: "answer-bbbbbbbbbbbbbbbbbbbbbb" }, // same len, new text
      { len: 200, barVisible: true, contentKey: "answer-bbbbbbbbbbbbbbbbbbbbbb" },
    ]);
    // The rewrite at sample 1 resets the debounce; only ~1 stable cycle follows -> not terminal.
    expect(out.some(Boolean)).toBe(false);
  });

  test("does not finalize stable text without correlated completion controls", () => {
    const samples: Array<Partial<TerminalSample> & { len: number }> = [
      { len: 800, stopVisible: true },
    ];
    for (let i = 0; i < 8; i++) samples.push({ len: 800 });
    const out = runGate(samples);
    expect(out.some(Boolean)).toBe(false);
  });

  test("an implausibly short capture still requires correlated completion controls", () => {
    const samples: Array<Partial<TerminalSample> & { len: number }> = [{ len: 1 }];
    for (let i = 0; i < 20; i++) samples.push({ len: 1 }); // stable "I", quiet, no bar/thinking
    const out = runGate(samples);
    expect(out.some(Boolean)).toBe(false);
  });

  test("a short answer still finalizes once its action bar debounces", () => {
    const out = runGate([
      { len: 4 },
      { len: 4, barVisible: true },
      { len: 4, barVisible: true },
      { len: 4, barVisible: true },
    ]);
    expect(out.at(-1)).toBe(true);
  });

  test("text growth resets the action-bar debounce", () => {
    const out = runGate([
      { len: 100, barVisible: true },
      { len: 100, barVisible: true },
      { len: 200, barVisible: true },
      { len: 200, barVisible: true },
    ]);
    expect(out.some(Boolean)).toBe(false);
  });
});

describe("thinking-active completion veto", () => {
  class FakeEl {
    public rect = { left: 0, top: 0, width: 120, height: 40 };
    constructor(
      public textContent = "",
      private attrs: Record<string, string> = {},
    ) {}
    getBoundingClientRect() {
      return this.rect;
    }
    getAttribute(name: string): string | null {
      return this.attrs[name] ?? null;
    }
    querySelectorAll(selector: string) {
      const matches: FakeEl[] = [];
      if (selector.includes("progress"))
        matches.push(
          ...this.children.filter((child) => child.getAttribute("role") === "progressbar"),
        );
      if (selector.includes("loading-shimmer"))
        matches.push(
          ...this.children.filter((child) => child.getAttribute("data-kind") === "shimmer"),
        );
      if (selector.includes("aria-busy"))
        matches.push(
          ...this.children.filter((child) => child.getAttribute("aria-busy") === "true"),
        );
      return [...new Set(matches)];
    }
    public children: FakeEl[] = [];
  }

  interface ThinkingFixtureOptions {
    stop?: boolean;
    shimmer?: boolean;
    ariaBusy?: boolean;
    statusText?: string;
    statusTestId?: string;
    progress?: boolean;
    progressNow?: number;
    progressMax?: number;
    unrelatedProgress?: boolean;
    unrelatedBusy?: boolean;
    panel?: FakeEl;
  }

  function createThinkingContext(opts: ThinkingFixtureOptions) {
    const statusNodes =
      opts.statusText != null
        ? [
            new FakeEl(
              opts.statusText,
              opts.statusTestId ? { "data-testid": opts.statusTestId } : {},
            ),
          ]
        : [];
    const progressAttrs: Record<string, string> =
      opts.progressNow != null
        ? {
            "aria-valuenow": String(opts.progressNow),
            "aria-valuemax": String(opts.progressMax ?? 100),
            role: "progressbar",
          }
        : { "aria-valuenow": "40", role: "progressbar" };
    const progressNodes =
      opts.progress || opts.progressNow != null ? [new FakeEl("", progressAttrs)] : [];
    // Progress is scoped to the CURRENT assistant turn (review P1): the harness models the
    // turn container; unrelatedProgress mounts a live bar OUTSIDE any turn, which must not veto.
    const turn = new FakeEl("turn");
    turn.children = [
      ...progressNodes,
      ...(opts.shimmer ? [new FakeEl("", { "data-kind": "shimmer" })] : []),
      ...(opts.ariaBusy ? [new FakeEl("", { "aria-busy": "true" })] : []),
    ];
    const turnNodes = [turn];
    const panelNodes = opts.panel ? [opts.panel] : [];
    return createContext({
      Array,
      Number,
      String,
      HTMLElement: FakeEl,
      HTMLProgressElement: class {},
      document: {
        querySelectorAll: (selector: string) => {
          if (selector.includes("stop") || selector.includes('aria-label*="stop"')) {
            return opts.stop ? [new FakeEl()] : [];
          }
          if (selector.includes("loading-shimmer")) return opts.unrelatedBusy ? [new FakeEl()] : [];
          if (selector.includes("aria-busy")) return opts.unrelatedBusy ? [new FakeEl()] : [];
          if (selector.includes("progressbar") || selector.includes("aria-valuenow")) {
            // Only an UNRELATED page-wide bar is ever visible at document level now; the
            // turn-scoped bars are reached through the turn node's own querySelectorAll.
            return opts.unrelatedProgress ? [new FakeEl("", progressAttrs)] : [];
          }
          if (selector.includes("conversation-turn") || selector.includes("data-turn")) {
            return turnNodes;
          }
          // The panel selector carries "aside"/"complementary"/"sidecar"; the status selector
          // does not, so match panels first to disambiguate (both mention thinking/reasoning).
          if (
            selector.includes("aside") ||
            selector.includes("complementary") ||
            selector.includes("sidecar") ||
            selector.includes("sidebar")
          ) {
            return panelNodes;
          }
          if (
            selector.includes("thinking") ||
            selector.includes("reasoning") ||
            selector.includes("status") ||
            selector.includes("aria-live")
          ) {
            return statusNodes;
          }
          return [];
        },
      },
      window: {
        getComputedStyle: () => ({ display: "block", visibility: "visible", opacity: "1" }),
        innerHeight: 900,
        innerWidth: 1440,
      },
    });
  }

  function evalThinkingActive(opts: ThinkingFixtureOptions): boolean {
    const predicate = buildThinkingActivePredicateJsForTest("isThinkingActive");
    return new Script(`${predicate}\nisThinkingActive();`).runInContext(
      createThinkingContext(opts),
    ) as boolean;
  }

  function evalThinkingActivityDetails(opts: ThinkingFixtureOptions): {
    active: boolean;
    strong: boolean;
  } {
    const predicate = buildThinkingActivityDetailsPredicateJsForTest("readThinkingActivity");
    return new Script(`${predicate}\nreadThinkingActivity();`).runInContext(
      createThinkingContext(opts),
    ) as { active: boolean; strong: boolean };
  }

  test("fires on a visible stop control", () => {
    expect(evalThinkingActive({ stop: true })).toBe(true);
  });

  test("fires on a visible loading-shimmer skeleton", () => {
    expect(evalThinkingActive({ shimmer: true })).toBe(true);
  });

  test("fires on aria-busy", () => {
    expect(evalThinkingActive({ ariaBusy: true })).toBe(true);
  });

  test.each(["Thinking", "Pro thinking", "Searching the web", "Reading", "Finalizing answer"])(
    "fires on active status label %j",
    (label) => {
      expect(evalThinkingActive({ statusText: label, statusTestId: "thinking-status" })).toBe(true);
    },
  );

  test("does NOT treat ordinary live-region answer prose as active thinking", () => {
    expect(
      evalThinkingActivityDetails({ statusText: "Thinking clearly requires practice." }),
    ).toEqual({
      active: false,
      strong: false,
    });
  });

  test("allows prefix matching only in verified thinking chrome", () => {
    expect(
      evalThinkingActivityDetails({
        statusText: "Thinking through the remaining cases",
        statusTestId: "reasoning-status",
      }),
    ).toEqual({ active: true, strong: true });
  });

  test.each(COMPLETED_SUMMARY_LABELS)(
    "does NOT fire on the persistent completed reasoning summary %s",
    (statusText) => {
      // The headline hang the design must avoid: this summary lingers in the DOM on every
      // finished Pro turn and on reattach. A presence-based veto would hang forever here.
      expect(evalThinkingActive({ statusText })).toBe(false);
    },
  );

  test("fires on a live progress bar inside the current assistant turn", () => {
    expect(evalThinkingActive({ progress: true })).toBe(true);
    expect(evalThinkingActivityDetails({ progress: true })).toEqual({ active: true, strong: true });
  });

  test("does NOT fire on a completed progress bar (value at max)", () => {
    // A finished connector bar must not veto completion forever.
    expect(evalThinkingActive({ progressNow: 100, progressMax: 100 })).toBe(false);
  });

  test("does NOT fire on an unrelated progress bar outside the assistant turn", () => {
    // Review P1: unrelated page UI can keep a visible progress bar mounted indefinitely; a
    // document-wide veto would then hold a completed response until the watchdog timeout.
    expect(evalThinkingActive({ unrelatedProgress: true })).toBe(false);
  });

  test("does NOT fire on unrelated page-wide busy indicators", () => {
    expect(evalThinkingActivityDetails({ unrelatedBusy: true })).toEqual({
      active: false,
      strong: false,
    });
  });

  test("fires on a right-side reasoning sidecar panel with no inline label", () => {
    const panel = new FakeEl("Reasoning");
    panel.rect = { left: 1000, top: 100, width: 380, height: 400 }; // right side, large
    expect(evalThinkingActive({ panel })).toBe(true);
    expect(evalThinkingActivityDetails({ panel })).toEqual({
      active: true,
      strong: false,
    });
  });

  test("does NOT treat progress in a generic panel as model activity", () => {
    const panel = new FakeEl("Upload");
    panel.rect = { left: 1000, top: 100, width: 380, height: 400 };
    panel.children = [new FakeEl("", { "aria-valuenow": "40", role: "progressbar" })];
    expect(evalThinkingActivityDetails({ panel })).toEqual({ active: false, strong: false });
  });

  test("treats progress in verified reasoning chrome as strong activity", () => {
    const panel = new FakeEl("", { "data-testid": "reasoning-panel" });
    panel.rect = { left: 1000, top: 100, width: 380, height: 400 };
    panel.children = [new FakeEl("", { "aria-valuenow": "40", role: "progressbar" })];
    expect(evalThinkingActivityDetails({ panel })).toEqual({ active: true, strong: true });
  });

  test.each(COMPLETED_SUMMARY_LABELS)("does NOT fire on completed sidecar summary %s", (text) => {
    const panel = new FakeEl(text);
    panel.rect = { left: 1000, top: 100, width: 380, height: 400 };
    expect(evalThinkingActive({ panel })).toBe(false);
  });

  test("still fires on a live sidecar trace that embeds a completed sub-step summary", () => {
    // A running trace accumulates sub-step summaries ("Thought for 2s") alongside live
    // reasoning text. Only a SHORT summary-only panel means the turn is done; a long trace
    // must keep vetoing completion even though it contains the completed phrase.
    const panel = new FakeEl(
      "Thought for 2s: Searching the web. Reasoning about the diff and enumerating candidate hunks to inspect next.",
    );
    panel.rect = { left: 1000, top: 100, width: 380, height: 400 };
    expect(evalThinkingActive({ panel })).toBe(true);
  });

  test("fires on a short live trace that begins with a completed sub-step", () => {
    const panel = new FakeEl("Thought for 2s: Searching the web");
    panel.rect = { left: 1000, top: 100, width: 380, height: 400 };
    expect(evalThinkingActive({ panel })).toBe(true);
  });

  test("does NOT fire on an idle DOM (finished, no controls)", () => {
    expect(evalThinkingActive({})).toBe(false);
  });
});
