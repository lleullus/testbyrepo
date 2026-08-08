import { describe, expect, it, vi } from "vitest";
import {
  buildBrowserReasoningExpressionForTest,
  ensureBrowserReasoning,
  shouldRequirePersistedOriginalModelIdentity,
} from "../../src/browser/actions/thinkingTime.js";

describe("strict browser reasoning selection", () => {
  it("lets a new current-strategy conversation establish its original identity on turn zero", async () => {
    const runtime = {
      evaluate: async () => ({
        result: {
          value: {
            status: "already-selected",
            controlKind: "dropdown",
            availableLevels: ["medium", "high"],
            resolvedLevel: "high",
            modelUnchanged: true,
            originalModelFingerprint: "new-conversation-model",
            observedModelFingerprint: "new-conversation-model",
            diagnostic: {
              controlCount: 2,
              matchingControlCount: 1,
              observedKinds: ["dropdown"],
            },
          },
        },
      }),
    };
    const requireOriginalModelIdentity = shouldRequirePersistedOriginalModelIdentity({
      isResumingConversation: false,
      turnIndex: 0,
    });

    const evidence = await ensureBrowserReasoning(
      runtime as never,
      {
        intent: "high",
        managedSlot: { slotId: 3, expectedControl: "dropdown", maximumReasoning: "high" },
        originalModelIdentity: null,
        requireOriginalModelIdentity,
      },
      (() => {}) as never,
    );

    expect(requireOriginalModelIdentity).toBe(false);
    expect(evidence).toMatchObject({
      status: "already-selected",
      verified: true,
      originalModelIdentity: {
        fingerprint: "new-conversation-model",
        source: "chatgpt-model-picker",
      },
    });
  });

  it("opens the exact Plus intelligence owner before establishing turn-zero identity", async () => {
    class Target {
      dispatchEvent(_event: unknown): boolean {
        return true;
      }
    }
    class Node extends Target {
      constructor(
        public textContent: string,
        private readonly attributes: Record<string, string>,
        private readonly onDispatch?: (event: unknown) => void,
      ) {
        super();
      }
      getAttribute(name: string): string | null {
        return this.attributes[name] ?? null;
      }
      getBoundingClientRect(): { width: number; height: number } {
        return { width: 100, height: 30 };
      }
      override dispatchEvent(event: unknown): boolean {
        this.onDispatch?.(event);
        return true;
      }
    }
    class EventStub {
      constructor(
        public readonly type: string,
        _init?: unknown,
      ) {}
    }

    let ownerOpen = false;
    let openClicks = 0;
    const reasoningPill = new Node(
      "High",
      { "data-testid": "model-switcher-dropdown-button", "aria-expanded": "false" },
      () => {
        ownerOpen = true;
        openClicks += 1;
      },
    );
    const standard = new Node("Standard", {
      role: "menuitemradio",
      "aria-checked": "false",
    });
    const high = new Node("High", { role: "menuitemradio", "aria-checked": "true" });
    const modelMenuItem = new Node("GPT-5.6 Sol", { role: "menuitem" });
    const reasoningOwner = {
      getAttribute: (name: string) => {
        if (name === "data-testid") return "composer-intelligence-picker-content";
        if (name === "role") return "group";
        return null;
      },
      getBoundingClientRect: () => ({ width: 100, height: 30 }),
      querySelectorAll: () => [standard, high, modelMenuItem],
    };
    const documentStub = {
      querySelector: (selector: string) =>
        selector.includes("model-switcher-dropdown-button") ? reasoningPill : null,
      querySelectorAll: (selector: string) => {
        if (selector.includes("composer-intelligence-picker-content")) {
          return ownerOpen ? [reasoningOwner] : [];
        }
        return [];
      },
    };
    const evaluateExpression = (expression: string) => {
      const evaluate = new Function(
        "document",
        "setTimeout",
        "window",
        "EventTarget",
        "PointerEvent",
        "MouseEvent",
        "Event",
        `return ${expression};`,
      ) as (...args: unknown[]) => Promise<unknown>;
      return evaluate(
        documentStub,
        (callback: () => void) => callback(),
        { PointerEvent: EventStub },
        Target,
        EventStub,
        EventStub,
        EventStub,
      );
    };
    const runtime = {
      evaluate: async ({ expression }: { expression: string }) => ({
        result: { value: await evaluateExpression(expression) },
      }),
    };

    const evidence = await ensureBrowserReasoning(
      runtime as never,
      {
        intent: "high",
        managedSlot: { slotId: 3, expectedControl: "dropdown", maximumReasoning: "high" },
        originalModelIdentity: null,
        requireOriginalModelIdentity: false,
      },
      (() => {}) as never,
    );

    expect(evidence).toMatchObject({
      status: "already-selected",
      resolvedLevel: "high",
      verified: true,
      originalModelIdentity: {
        fingerprint: expect.any(String),
        source: "chatgpt-model-picker",
      },
    });
    expect(evidence.observedModelFingerprint).toBe(evidence.originalModelIdentity?.fingerprint);
    expect(openClicks).toBeGreaterThan(0);
  });

  it("polls the exact Pro intelligence owner until its delayed update is verified", async () => {
    class Target {
      dispatchEvent(_event: unknown): boolean {
        return true;
      }
    }
    class Node extends Target {
      public children: Node[] = [];
      public focused = false;
      public innerText: string | null = null;
      constructor(
        public textContent: string,
        private readonly attributes: Record<string, string>,
        private readonly onDispatch?: (event: unknown) => void,
      ) {
        super();
      }
      getAttribute(name: string): string | null {
        return this.attributes[name] ?? null;
      }
      setAttribute(name: string, value: string): void {
        this.attributes[name] = value;
      }
      getBoundingClientRect(): { width: number; height: number } {
        return { width: 100, height: 30 };
      }
      querySelectorAll(_selector: string): Node[] {
        return this.children;
      }
      focus(): void {
        this.focused = true;
      }
      override dispatchEvent(event: unknown): boolean {
        this.onDispatch?.(event);
        return true;
      }
    }
    class EventStub {
      constructor(
        public readonly type: string,
        _init?: unknown,
      ) {}
    }

    let ownerOpen = false;
    let openClicks = 0;
    const reasoningPill = new Node(
      "Extra High",
      { "data-testid": "model-switcher-dropdown-button", "aria-expanded": "false" },
      (event) => {
        if ((event as { type?: string }).type === "click") {
          ownerOpen = true;
          openClicks += 1;
        }
      },
    );
    const sliderReadback = new Node("", {
      role: "slider",
      tabindex: "-1",
      "aria-hidden": "true",
      "aria-valuemin": "0",
      "aria-valuemax": "4",
      "aria-valuenow": "3",
      "aria-orientation": "horizontal",
    });
    const modelMenuItem = new Node("ModelGPT-5.6 Sol", { role: "menuitem" });
    modelMenuItem.innerText = "Model\nGPT-5.6 Sol";
    const effortMenuItem = new Node("EffortExtra High GPT-9.9", { role: "menuitem" });
    effortMenuItem.innerText = "Effort\nExtra High GPT-9.9";
    let arrowRightKeydowns = 0;
    let updateScheduled = false;
    const powerOwner = new Node(
      "",
      {
        role: "menuitem",
        tabindex: "0",
        "aria-label": "Power",
        "aria-keyshortcuts": "ArrowLeft ArrowRight",
        "data-orientation": "vertical",
      },
      (event) => {
        if ((event as { type?: string }).type !== "keydown") return;
        arrowRightKeydowns += 1;
        if (updateScheduled) return;
        updateScheduled = true;
        setTimeout(() => {
          sliderReadback.setAttribute("aria-valuenow", "4");
          effortMenuItem.textContent = "EffortPro";
          effortMenuItem.innerText = "Effort\nPro";
        }, 350);
      },
    );
    powerOwner.children = [sliderReadback];
    const reasoningOwner = {
      textContent:
        "Extra High, 4 of 5. Use Left and Right arrow keys to adjust power. Advanced Faster Smarter Model GPT-5.6 Sol Effort Extra High",
      getAttribute: (name: string) => {
        if (name === "data-testid") return "composer-intelligence-picker-content";
        if (name === "role") return "group";
        return null;
      },
      getBoundingClientRect: () => ({ width: 100, height: 30 }),
      querySelectorAll: () => [powerOwner, sliderReadback, modelMenuItem, effortMenuItem],
    };
    const documentStub = {
      querySelector: (selector: string) =>
        selector.includes("model-switcher-dropdown-button") ? reasoningPill : null,
      querySelectorAll: (selector: string) => {
        if (selector.includes("composer-intelligence-picker-content")) {
          return ownerOpen ? [reasoningOwner] : [];
        }
        return [];
      },
    };
    const expression = buildBrowserReasoningExpressionForTest({
      intent: "pro",
      managedSlot: { slotId: 1, expectedControl: "slider", maximumReasoning: "pro" },
    });
    const evaluate = new Function(
      "document",
      "setTimeout",
      "window",
      "EventTarget",
      "PointerEvent",
      "MouseEvent",
      "Event",
      `return ${expression};`,
    ) as (...args: unknown[]) => Promise<unknown>;

    await expect(
      evaluate(
        documentStub,
        setTimeout,
        { PointerEvent: EventStub, KeyboardEvent: EventStub },
        Target,
        EventStub,
        EventStub,
        EventStub,
      ),
    ).resolves.toMatchObject({
      status: "switched",
      controlKind: "slider",
      resolvedLevel: "pro",
      modelUnchanged: true,
      originalModelFingerprint: expect.any(String),
      observedModelFingerprint: expect.any(String),
    });
    expect(openClicks).toBeGreaterThan(0);
    expect(arrowRightKeydowns).toBe(1);
    expect(powerOwner.focused).toBe(true);
    expect(sliderReadback.getAttribute("aria-valuenow")).toBe("4");
  });

  it.each([
    { initial: "medium", target: "extra-high", key: "ArrowRight" },
    { initial: "extra-high", target: "medium", key: "ArrowLeft" },
  ] as const)(
    "moves a composite slider from $initial to $target by fresh labels",
    async ({ initial, target, key }) => {
      class Target {
        dispatchEvent(_event: unknown): boolean {
          return true;
        }
      }
      class Node extends Target {
        public children: Node[] = [];

        constructor(
          public textContent: string,
          private readonly attributes: Record<string, string>,
          private readonly onDispatch?: (event: unknown) => void,
          private readonly onRead?: (value: string) => void,
        ) {
          super();
        }

        getAttribute(name: string): string | null {
          const value = this.attributes[name] ?? null;
          if (name === "aria-valuetext" && value) this.onRead?.(value);
          return value;
        }

        getBoundingClientRect(): { width: number; height: number } {
          return { width: 100, height: 30 };
        }

        querySelectorAll(_selector: string): Node[] {
          return this.children;
        }

        focus(): void {}

        override dispatchEvent(event: unknown): boolean {
          this.onDispatch?.(event);
          return true;
        }
      }
      class EventStub {
        public readonly key?: string;

        constructor(
          public readonly type: string,
          init?: { key?: string },
        ) {
          this.key = init?.key;
        }
      }

      const levels = ["instant", "medium", "high", "extra-high", "pro"] as const;
      let currentIndex = levels.indexOf(initial);
      const targetIndex = levels.indexOf(target);
      const arrowKeys: string[] = [];
      const observedLabels: string[] = [];
      const readbacks: Node[] = [];
      const modelMenuItem = new Node("GPT-5.6 Sol", { role: "menuitem" });
      const makeReadback = (level: (typeof levels)[number]) => {
        const readback = new Node(
          "",
          {
            role: "slider",
            tabindex: "-1",
            "aria-hidden": "true",
            "aria-valuemin": "0",
            "aria-valuemax": "4",
            "aria-valuenow": String(levels.indexOf(level)),
            "aria-valuetext": level,
          },
          undefined,
          (value) => observedLabels.push(value),
        );
        readbacks.push(readback);
        return readback;
      };
      let liveReadback = makeReadback(initial);
      let liveEffort = new Node(`Effort ${initial}`, { role: "menuitem" });
      const powerOwner = new Node(
        "",
        {
          role: "menuitem",
          tabindex: "0",
          "aria-label": "Power",
          "aria-keyshortcuts": "ArrowLeft ArrowRight",
          "data-orientation": "vertical",
        },
        (event) => {
          const eventKey = (event as { key?: string; type?: string }).key;
          if ((event as { type?: string }).type !== "keydown" || eventKey !== key) return;
          arrowKeys.push(eventKey);
          currentIndex += key === "ArrowRight" ? 1 : -1;
          const nextLevel = levels[currentIndex];
          liveReadback = makeReadback(nextLevel);
          liveEffort = new Node(`Effort ${nextLevel}`, { role: "menuitem" });
          powerOwner.children = [liveReadback];
        },
      );
      powerOwner.children = [liveReadback];
      const reasoningOwner = {
        getAttribute: (name: string) =>
          name === "data-testid" ? "composer-intelligence-picker-content" : null,
        getBoundingClientRect: () => ({ width: 100, height: 30 }),
        querySelectorAll: (selector: string) => {
          if (selector.includes('[role="menuitem"]')) {
            return [powerOwner, modelMenuItem, liveEffort];
          }
          if (selector.includes('[role="slider"]')) return [liveReadback];
          return [];
        },
      };
      const documentStub = {
        querySelector: () => null,
        querySelectorAll: (selector: string) =>
          selector.includes("composer-intelligence-picker-content") ? [reasoningOwner] : [],
      };
      const expression = buildBrowserReasoningExpressionForTest({
        intent: target,
        managedSlot: { slotId: 1, expectedControl: "slider", maximumReasoning: "pro" },
      });
      const evaluate = new Function(
        "document",
        "setTimeout",
        "window",
        "EventTarget",
        "PointerEvent",
        "MouseEvent",
        "Event",
        `return ${expression};`,
      ) as (...args: unknown[]) => Promise<unknown>;

      await expect(
        evaluate(
          documentStub,
          (callback: () => void) => callback(),
          { KeyboardEvent: EventStub },
          Target,
          EventStub,
          EventStub,
          EventStub,
        ),
      ).resolves.toMatchObject({
        status: "switched",
        controlKind: "slider",
        resolvedLevel: target,
        modelUnchanged: true,
      });
      expect(currentIndex).toBe(targetIndex);
      expect(arrowKeys).toEqual(
        Array.from({ length: Math.abs(targetIndex - levels.indexOf(initial)) }, () => key),
      );
      expect(new Set(readbacks).size).toBe(arrowKeys.length + 1);
      expect(observedLabels).toEqual(expect.arrayContaining([initial, "high", target]));
    },
  );

  it("times out when an exact Pro composite slider never applies its update", async () => {
    class Target {
      dispatchEvent(_event: unknown): boolean {
        return true;
      }
    }
    class Node extends Target {
      public children: Node[] = [];
      constructor(
        public textContent: string,
        private readonly attributes: Record<string, string>,
        private readonly onDispatch?: (event: unknown) => void,
      ) {
        super();
      }
      getAttribute(name: string): string | null {
        return this.attributes[name] ?? null;
      }
      getBoundingClientRect(): { width: number; height: number } {
        return { width: 100, height: 30 };
      }
      querySelectorAll(_selector: string): Node[] {
        return this.children;
      }
      focus(): void {}
      override dispatchEvent(event: unknown): boolean {
        this.onDispatch?.(event);
        return true;
      }
    }
    class EventStub {
      constructor(
        public readonly type: string,
        _init?: unknown,
      ) {}
    }

    const sliderReadback = new Node("", {
      role: "slider",
      tabindex: "-1",
      "aria-hidden": "true",
      "aria-valuemin": "0",
      "aria-valuemax": "4",
      "aria-valuenow": "3",
    });
    let arrowRightKeydowns = 0;
    const powerOwner = new Node(
      "",
      {
        role: "menuitem",
        tabindex: "0",
        "aria-label": "Power",
        "aria-keyshortcuts": "ArrowLeft ArrowRight",
        "data-orientation": "vertical",
      },
      (event) => {
        if ((event as { type?: string }).type === "keydown") arrowRightKeydowns += 1;
      },
    );
    powerOwner.children = [sliderReadback];
    const modelMenuItem = new Node("Model GPT-5.6 Sol", { role: "menuitem" });
    const effortMenuItem = new Node("Effort Extra High", { role: "menuitem" });
    const reasoningOwner = {
      getAttribute: (name: string) =>
        name === "data-testid" ? "composer-intelligence-picker-content" : null,
      getBoundingClientRect: () => ({ width: 100, height: 30 }),
      querySelectorAll: () => [powerOwner, sliderReadback, modelMenuItem, effortMenuItem],
    };
    const documentStub = {
      querySelector: () => null,
      querySelectorAll: (selector: string) =>
        selector.includes("composer-intelligence-picker-content") ? [reasoningOwner] : [],
    };
    const expression = buildBrowserReasoningExpressionForTest({
      intent: "pro",
      managedSlot: { slotId: 1, expectedControl: "slider", maximumReasoning: "pro" },
    });
    const evaluate = new Function(
      "document",
      "setTimeout",
      "window",
      "EventTarget",
      "PointerEvent",
      "MouseEvent",
      "Event",
      `return ${expression};`,
    ) as (...args: unknown[]) => Promise<unknown>;

    await expect(
      evaluate(
        documentStub,
        setTimeout,
        { PointerEvent: EventStub, KeyboardEvent: EventStub },
        Target,
        EventStub,
        EventStub,
        EventStub,
      ),
    ).resolves.toMatchObject({
      status: "unavailable",
      controlKind: "slider",
      resolvedLevel: "extra-high",
      modelUnchanged: true,
      originalModelFingerprint: expect.any(String),
      observedModelFingerprint: expect.any(String),
      diagnostic: { controlCount: 1, matchingControlCount: 1, observedKinds: ["slider"] },
    });
    expect(arrowRightKeydowns).toBe(1);
    expect(sliderReadback.getAttribute("aria-valuenow")).toBe("3");
  });

  it("ignores an aria-hidden slider without the exact focusable keyboard owner", async () => {
    class Target {
      dispatchEvent(_event: unknown): boolean {
        return true;
      }
    }
    class Node extends Target {
      public children: Node[] = [];
      constructor(
        public textContent: string,
        private readonly attributes: Record<string, string>,
      ) {
        super();
      }
      getAttribute(name: string): string | null {
        return this.attributes[name] ?? null;
      }
      getBoundingClientRect(): { width: number; height: number } {
        return { width: 100, height: 30 };
      }
      querySelectorAll(_selector: string): Node[] {
        return this.children;
      }
    }
    class EventStub {
      constructor(
        public readonly type: string,
        _init?: unknown,
      ) {}
    }

    const hiddenSlider = new Node("", {
      role: "slider",
      tabindex: "-1",
      "aria-hidden": "true",
      "aria-valuemin": "0",
      "aria-valuemax": "4",
      "aria-valuenow": "3",
    });
    const invalidOwner = new Node("Power", {
      role: "menuitem",
      tabindex: "0",
      "data-orientation": "vertical",
    });
    invalidOwner.children = [hiddenSlider];
    const modelMenuItem = new Node("Model GPT-5.6 Sol", { role: "menuitem" });
    const reasoningOwner = {
      getAttribute: (name: string) =>
        name === "data-testid" ? "composer-intelligence-picker-content" : null,
      getBoundingClientRect: () => ({ width: 100, height: 30 }),
      querySelectorAll: () => [invalidOwner, hiddenSlider, modelMenuItem],
    };
    const documentStub = {
      querySelector: () => null,
      querySelectorAll: (selector: string) =>
        selector.includes("composer-intelligence-picker-content") ? [reasoningOwner] : [],
    };
    const expression = buildBrowserReasoningExpressionForTest({
      intent: "pro",
      managedSlot: { slotId: 1, expectedControl: "slider", maximumReasoning: "pro" },
    });
    const evaluate = new Function(
      "document",
      "setTimeout",
      "window",
      "EventTarget",
      "PointerEvent",
      "MouseEvent",
      "Event",
      `return ${expression};`,
    ) as (...args: unknown[]) => Promise<unknown>;

    await expect(
      evaluate(
        documentStub,
        (callback: () => void) => callback(),
        { PointerEvent: EventStub, KeyboardEvent: EventStub },
        Target,
        EventStub,
        EventStub,
        EventStub,
      ),
    ).resolves.toMatchObject({
      status: "unavailable",
      controlKind: null,
      modelUnchanged: false,
      originalModelFingerprint: expect.any(String),
      diagnostic: { controlCount: 0, matchingControlCount: 0 },
    });
  });

  it("keeps resume and later turns strict while allowing turn-zero retries to establish identity", () => {
    expect(
      shouldRequirePersistedOriginalModelIdentity({
        isResumingConversation: false,
        turnIndex: 0,
      }),
    ).toBe(false);
    expect(
      shouldRequirePersistedOriginalModelIdentity({
        isResumingConversation: true,
        turnIndex: 0,
      }),
    ).toBe(true);
    expect(
      shouldRequirePersistedOriginalModelIdentity({
        isResumingConversation: false,
        turnIndex: 1,
      }),
    ).toBe(true);
  });

  it("records independently verified dropdown evidence", async () => {
    const runtime = {
      evaluate: async () => ({
        result: {
          value: {
            status: "switched",
            controlKind: "dropdown",
            availableLevels: ["medium", "high"],
            resolvedLevel: "high",
            modelUnchanged: true,
            originalModelFingerprint: "model-fingerprint-a",
            observedModelFingerprint: "model-fingerprint-a",
            diagnostic: {
              controlCount: 3,
              matchingControlCount: 1,
              observedKinds: ["dropdown"],
            },
          },
        },
      }),
    };

    const evidence = await ensureBrowserReasoning(
      runtime as never,
      {
        intent: "high",
        managedSlot: { slotId: 3, expectedControl: "dropdown", maximumReasoning: "high" },
      },
      (() => {}) as never,
    );

    expect(evidence).toMatchObject({
      requestedIntent: "high",
      controlKind: "dropdown",
      availableLevels: ["medium", "high"],
      resolvedLevel: "high",
      verified: true,
      modelUnchanged: true,
      managedSlotId: 3,
      originalModelIdentity: expect.objectContaining({
        fingerprint: "model-fingerprint-a",
        source: "chatgpt-model-picker",
      }),
      observedModelFingerprint: "model-fingerprint-a",
    });
  });

  it("rejects resume before page evaluation when the original model identity is missing", async () => {
    const evaluate = vi.fn();

    await expect(
      ensureBrowserReasoning(
        { evaluate } as never,
        { intent: "high", requireOriginalModelIdentity: true },
        (() => {}) as never,
      ),
    ).rejects.toMatchObject({
      evidence: expect.objectContaining({ status: "original-model-missing", verified: false }),
    });
    expect(evaluate).not.toHaveBeenCalled();
  });

  it("rejects a follow-up whose observed model differs from the original fingerprint", async () => {
    const runtime = {
      evaluate: async () => ({
        result: {
          value: {
            status: "model-mismatch",
            controlKind: "dropdown",
            availableLevels: ["medium", "high"],
            resolvedLevel: null,
            modelUnchanged: false,
            originalModelFingerprint: "model-fingerprint-a",
            observedModelFingerprint: "model-fingerprint-b",
            diagnostic: {
              controlCount: 2,
              matchingControlCount: 0,
              observedKinds: ["dropdown"],
            },
          },
        },
      }),
    };

    await expect(
      ensureBrowserReasoning(
        runtime as never,
        {
          intent: "high",
          originalModelIdentity: {
            fingerprint: "model-fingerprint-a",
            source: "chatgpt-model-picker",
            capturedAt: "2026-08-03T00:00:00.000Z",
          },
        },
        (() => {}) as never,
      ),
    ).rejects.toMatchObject({
      evidence: expect.objectContaining({
        status: "model-mismatch",
        originalModelIdentity: expect.objectContaining({ fingerprint: "model-fingerprint-a" }),
        observedModelFingerprint: "model-fingerprint-b",
        verified: false,
      }),
    });
  });

  it("compares the live resume model with the persisted original instead of a new baseline", async () => {
    class Target {
      dispatchEvent(_event: unknown): boolean {
        return true;
      }
    }
    class Node extends Target {
      constructor(
        public textContent: string,
        private readonly attributes: Record<string, string>,
      ) {
        super();
      }
      getAttribute(name: string): string | null {
        return this.attributes[name] ?? null;
      }
      getBoundingClientRect(): { width: number; height: number } {
        return { width: 100, height: 30 };
      }
    }
    class EventStub {
      constructor(
        public readonly type: string,
        _init?: unknown,
      ) {}
    }

    const model = new Node("Thinking 5.6", {
      "data-testid": "model-switcher-dropdown-button",
    });
    const standard = new Node("Standard", { role: "menuitemradio", "aria-checked": "true" });
    const high = new Node("High", { role: "menuitemradio", "aria-checked": "false" });
    const modelMenuItem = new Node("GPT-5.6 Sol", { role: "menuitem" });
    const reasoningOwner = {
      getAttribute: (name: string) =>
        name === "data-testid" ? "composer-intelligence-picker-content" : null,
      getBoundingClientRect: () => ({ width: 100, height: 30 }),
      querySelectorAll: () => [standard, high, modelMenuItem],
    };
    const documentStub = {
      querySelector: () => model,
      querySelectorAll: (selector: string) =>
        selector.includes("composer-intelligence-picker-content") ? [reasoningOwner] : [],
    };
    const expression = buildBrowserReasoningExpressionForTest({
      intent: "high",
      managedSlot: { slotId: 3, expectedControl: "dropdown", maximumReasoning: "high" },
      originalModelIdentity: {
        fingerprint: "persisted-original-fingerprint",
        source: "chatgpt-model-picker",
        capturedAt: "2026-08-03T00:00:00.000Z",
      },
    });
    const evaluate = new Function(
      "document",
      "setTimeout",
      "window",
      "EventTarget",
      "PointerEvent",
      "MouseEvent",
      "Event",
      `return ${expression};`,
    ) as (...args: unknown[]) => Promise<unknown>;

    await expect(
      evaluate(
        documentStub,
        (callback: () => void) => callback(),
        { PointerEvent: EventStub },
        Target,
        EventStub,
        EventStub,
        EventStub,
      ),
    ).resolves.toMatchObject({
      status: "model-mismatch",
      originalModelFingerprint: "persisted-original-fingerprint",
      observedModelFingerprint: expect.not.stringMatching(/^persisted-original-fingerprint$/),
      modelUnchanged: false,
    });
  });

  it.each([
    { status: "unavailable", controlKind: null, modelUnchanged: true },
    { status: "ambiguous", controlKind: "dropdown", modelUnchanged: true },
    { status: "model-changed", controlKind: "slider", modelUnchanged: false },
    undefined,
  ] as const)("fails closed for %o", async (value) => {
    const runtime = { evaluate: async () => ({ result: { value } }) };

    await expect(
      ensureBrowserReasoning(runtime as never, { intent: "pro" }, (() => {}) as never),
    ).rejects.toThrow(/failed before prompt submission/i);
  });

  it("keeps the control plan separate from model picker text", () => {
    const expression = buildBrowserReasoningExpressionForTest({
      intent: "pro",
      managedSlot: { slotId: 1, expectedControl: "slider", maximumReasoning: "pro" },
    });

    expect(expression).toContain('const TARGET = "pro"');
    expect(expression).toContain('const EXPECTED_CONTROL = "slider"');
    expect(expression).toContain('input[type="range"]');
    expect(expression).toContain("stableModelFingerprint");
    expect(expression).not.toContain("conversation");
  });

  it("selects and verifies High from one observable Plus dropdown", async () => {
    class FakeEventTarget {
      dispatchEvent(_event: unknown): boolean {
        return true;
      }
    }
    class FakeElement extends FakeEventTarget {
      constructor(
        public textContent: string,
        private readonly attributes: Record<string, string>,
        private readonly onDispatch?: () => void,
      ) {
        super();
      }
      getAttribute(name: string): string | null {
        return this.attributes[name] ?? null;
      }
      setAttribute(name: string, value: string): void {
        this.attributes[name] = value;
      }
      getBoundingClientRect(): { width: number; height: number } {
        return { width: 100, height: 30 };
      }
      override dispatchEvent(event: unknown): boolean {
        if ((event as { type?: string }).type === "click") this.onDispatch?.();
        return true;
      }
    }
    class FakeEvent {
      constructor(
        public readonly type: string,
        _init?: unknown,
      ) {}
    }

    const model = new FakeElement("Thinking 5.5", {
      "data-testid": "model-switcher-dropdown-button",
    });
    const standard = new FakeElement("Standard", { role: "menuitemradio", "aria-checked": "true" });
    const high = new FakeElement("High", { role: "menuitemradio", "aria-checked": "false" }, () => {
      standard.setAttribute("aria-checked", "false");
      high.setAttribute("aria-checked", "true");
    });
    const modelMenuItem = new FakeElement("GPT-5.6 Sol", { role: "menuitem" });
    const reasoningOwner = {
      getAttribute: (name: string) =>
        name === "data-testid" ? "composer-intelligence-picker-content" : null,
      getBoundingClientRect: () => ({ width: 100, height: 30 }),
      querySelectorAll: (_selector: string) => [standard, high, modelMenuItem],
    };
    const documentStub = {
      querySelector: (selector: string) =>
        selector.includes("model-switcher-dropdown-button") ? model : null,
      querySelectorAll: (selector: string) => {
        if (selector.includes("composer-intelligence-picker-content")) return [reasoningOwner];
        return selector.includes('role="option"') || selector.includes('role="menuitemradio"')
          ? [standard, high]
          : [];
      },
    };
    const expression = buildBrowserReasoningExpressionForTest({
      intent: "high",
      managedSlot: { slotId: 3, expectedControl: "dropdown", maximumReasoning: "high" },
    });
    const evaluate = new Function(
      "document",
      "setTimeout",
      "window",
      "EventTarget",
      "PointerEvent",
      "MouseEvent",
      "Event",
      `return ${expression};`,
    ) as (
      document: unknown,
      setTimeout: unknown,
      window: unknown,
      EventTarget: unknown,
      PointerEvent: unknown,
      MouseEvent: unknown,
      Event: unknown,
    ) => Promise<unknown>;

    await expect(
      evaluate(
        documentStub,
        (callback: () => void) => callback(),
        { PointerEvent: FakeEvent },
        FakeEventTarget,
        FakeEvent,
        FakeEvent,
        FakeEvent,
      ),
    ).resolves.toMatchObject({
      status: "switched",
      controlKind: "dropdown",
      availableLevels: ["medium", "high"],
      resolvedLevel: "high",
      modelUnchanged: true,
    });
  });

  it("fails a managed slot when conflicting slider and dropdown controls are visible", async () => {
    const expression = buildBrowserReasoningExpressionForTest({
      intent: "pro",
      managedSlot: { slotId: 1, expectedControl: "slider", maximumReasoning: "pro" },
    });
    expect(expression).toContain("dropdownItems.length > 0");
  });

  it("opens a closed composer control before discovering and selecting High", async () => {
    class Target {
      dispatchEvent(_event: unknown): boolean {
        return true;
      }
    }
    class Node extends Target {
      constructor(
        public textContent: string,
        private readonly attributes: Record<string, string>,
        private readonly onClick?: () => void,
      ) {
        super();
      }
      getAttribute(name: string): string | null {
        return this.attributes[name] ?? null;
      }
      setAttribute(name: string, value: string): void {
        this.attributes[name] = value;
      }
      getBoundingClientRect(): { width: number; height: number } {
        return { width: 100, height: 30 };
      }
      override dispatchEvent(event: unknown): boolean {
        if ((event as { type?: string }).type === "click") this.onClick?.();
        return true;
      }
    }
    class EventStub {
      constructor(
        public readonly type: string,
        _init?: unknown,
      ) {}
    }

    let modelMenuOpen = false;
    let reasoningOwnerOpen = false;
    let openClicks = 0;
    const composer = new Node(
      "Thinking 5.5",
      { "data-testid": "model-switcher-dropdown-button", "aria-expanded": "false" },
      () => {
        modelMenuOpen = true;
        openClicks += 1;
        composer.setAttribute("aria-expanded", "true");
      },
    );
    const standard = new Node("Standard", { role: "menuitemradio", "aria-checked": "true" });
    const high = new Node("High", { role: "menuitemradio", "aria-checked": "false" }, () => {
      standard.setAttribute("aria-checked", "false");
      high.setAttribute("aria-checked", "true");
    });
    const modelMenuItem = new Node("GPT-5.6 Sol", { role: "menuitem" });
    const reasoningTrigger = new Node(
      "Reasoning",
      {
        "data-testid": "composer-intelligence-thinking-trigger",
        "aria-controls": "reasoning-owner",
        "aria-expanded": "false",
      },
      () => {
        reasoningOwnerOpen = true;
        reasoningTrigger.setAttribute("aria-expanded", "true");
      },
    );
    const reasoningOwner = {
      getAttribute: (name: string) =>
        name === "data-testid" ? "composer-intelligence-picker-content" : null,
      getBoundingClientRect: () => ({ width: reasoningOwnerOpen ? 100 : 0, height: 30 }),
      querySelectorAll: (_selector: string) => [standard, high, modelMenuItem],
    };
    const documentStub = {
      querySelector: (_selector: string) => composer,
      getElementById: (id: string) => (id === "reasoning-owner" ? reasoningOwner : null),
      querySelectorAll: (selector: string) => {
        if (selector.includes("composer-intelligence-picker-content")) {
          return reasoningOwnerOpen ? [reasoningOwner] : [];
        }
        if (selector.includes("aria-controls") && selector.includes("thinking")) {
          return modelMenuOpen ? [reasoningTrigger] : [];
        }
        return selector.includes('role="option"') || selector.includes('role="menuitemradio"')
          ? reasoningOwnerOpen
            ? [standard, high]
            : []
          : [];
      },
    };
    const expression = buildBrowserReasoningExpressionForTest({
      intent: "high",
      managedSlot: { slotId: 3, expectedControl: "dropdown", maximumReasoning: "high" },
    });
    const evaluate = new Function(
      "document",
      "setTimeout",
      "window",
      "EventTarget",
      "PointerEvent",
      "MouseEvent",
      "Event",
      `return ${expression};`,
    ) as (...args: unknown[]) => Promise<unknown>;

    await expect(
      evaluate(
        documentStub,
        (callback: () => void) => callback(),
        { PointerEvent: EventStub },
        Target,
        EventStub,
        EventStub,
        EventStub,
      ),
    ).resolves.toMatchObject({
      status: "switched",
      controlKind: "dropdown",
      resolvedLevel: "high",
    });
    expect(openClicks).toBeGreaterThan(0);
  });

  it("verifies Pro slider state from a refreshed live node without forging ARIA", async () => {
    class Target {
      dispatchEvent(_event: unknown): boolean {
        return true;
      }
    }
    class Slider extends Target {
      public parentElement: { querySelectorAll: () => unknown[] } | null = null;
      public ariaWrites = 0;
      constructor(
        private currentValue: string,
        private readonly attributes: Record<string, string>,
        private readonly onInput?: () => void,
      ) {
        super();
      }
      get value(): string {
        return this.currentValue;
      }
      set value(value: string) {
        this.currentValue = value;
      }
      getAttribute(name: string): string | null {
        return this.attributes[name] ?? null;
      }
      setAttribute(name: string, value: string): void {
        if (name.startsWith("aria-value")) this.ariaWrites += 1;
        this.attributes[name] = value;
      }
      getBoundingClientRect(): { width: number; height: number } {
        return { width: 100, height: 30 };
      }
      matches(selector: string): boolean {
        return selector.includes('input[type="range"]');
      }
      override dispatchEvent(event: unknown): boolean {
        if ((event as { type?: string }).type === "keydown") this.onInput?.();
        return true;
      }
    }
    class Node extends Target {
      constructor(
        public textContent: string,
        private readonly attributes: Record<string, string>,
      ) {
        super();
      }
      getAttribute(name: string): string | null {
        return this.attributes[name] ?? null;
      }
      getBoundingClientRect(): { width: number; height: number } {
        return { width: 100, height: 30 };
      }
    }
    class EventStub {
      constructor(
        public readonly type: string,
        _init?: unknown,
      ) {}
    }

    const model = new Node("Thinking 5.5", { "data-testid": "model-switcher-dropdown-button" });
    let refreshed = false;
    let liveSlider: Slider;
    const replacement = new Slider("4", {
      "aria-valuemax": "4",
      "aria-valuetext": "Pro",
    });
    const initial = new Slider("1", { "aria-valuemax": "4", "aria-valuetext": "Standard" }, () => {
      refreshed = true;
      liveSlider = replacement;
    });
    liveSlider = initial;
    const modelMenuItem = new Node("Model GPT-5.6 Sol", { role: "menuitem" });
    const reasoningOwner = {
      getAttribute: (name: string) =>
        name === "data-testid" ? "composer-intelligence-picker-content" : null,
      getBoundingClientRect: () => ({ width: 100, height: 30 }),
      querySelectorAll: (_selector: string) => [liveSlider, modelMenuItem],
    };
    const documentStub = {
      querySelector: (_selector: string) => model,
      querySelectorAll: (selector: string) => {
        if (selector.includes("composer-intelligence-picker-content")) return [reasoningOwner];
        return selector.includes('input[type="range"]') || selector.includes('role="slider"')
          ? [liveSlider]
          : [];
      },
    };
    const expression = buildBrowserReasoningExpressionForTest({
      intent: "pro",
      managedSlot: { slotId: 1, expectedControl: "slider", maximumReasoning: "pro" },
    });
    const evaluate = new Function(
      "document",
      "setTimeout",
      "window",
      "EventTarget",
      "PointerEvent",
      "MouseEvent",
      "Event",
      `return ${expression};`,
    ) as (...args: unknown[]) => Promise<unknown>;

    await expect(
      evaluate(
        documentStub,
        (callback: () => void) => callback(),
        { PointerEvent: EventStub, KeyboardEvent: EventStub },
        Target,
        EventStub,
        EventStub,
        EventStub,
      ),
    ).resolves.toMatchObject({ status: "switched", controlKind: "slider", resolvedLevel: "pro" });
    expect(refreshed).toBe(true);
    expect(initial.ariaWrites).toBe(0);
  });

  it("uses the verified readback level for a composite slider with an unreadable effort label", async () => {
    class Target {
      dispatchEvent(_event: unknown): boolean {
        return true;
      }
    }
    class Node extends Target {
      public children: Node[] = [];
      constructor(
        public textContent: string,
        private readonly attributes: Record<string, string>,
      ) {
        super();
      }
      getAttribute(name: string): string | null {
        return this.attributes[name] ?? null;
      }
      getBoundingClientRect(): { width: number; height: number } {
        return { width: 100, height: 30 };
      }
      querySelectorAll(_selector: string): Node[] {
        return this.children;
      }
      focus(): void {}
      override dispatchEvent(event: unknown): boolean {
        return true;
      }
    }
    class EventStub {
      constructor(
        public readonly type: string,
        _init?: unknown,
      ) {}
    }

    const sliderReadback = new Node("", {
      role: "slider",
      tabindex: "-1",
      "aria-hidden": "true",
      "aria-valuemin": "0",
      "aria-valuemax": "4",
      "aria-valuenow": "4",
      "aria-valuetext": "Pro",
    });
    const powerOwner = new Node("", {
      role: "menuitem",
      tabindex: "0",
      "aria-label": "Power",
      "aria-keyshortcuts": "ArrowLeft ArrowRight",
      "data-orientation": "vertical",
    });
    powerOwner.children = [sliderReadback];
    const modelMenuItem = new Node("Model GPT-5.6 Sol", { role: "menuitem" });
    const effortMenuItem = new Node("Effort GPT-9.9", { role: "menuitem" });
    const reasoningOwner = {
      getAttribute: (name: string) =>
        name === "data-testid" ? "composer-intelligence-picker-content" : null,
      getBoundingClientRect: () => ({ width: 100, height: 30 }),
      querySelectorAll: () => [powerOwner, sliderReadback, modelMenuItem, effortMenuItem],
    };
    const documentStub = {
      querySelector: () => null,
      querySelectorAll: (selector: string) =>
        selector.includes("composer-intelligence-picker-content") ? [reasoningOwner] : [],
    };
    const expression = buildBrowserReasoningExpressionForTest({
      intent: "pro",
      managedSlot: { slotId: 1, expectedControl: "slider", maximumReasoning: "pro" },
    });
    const evaluate = new Function(
      "document",
      "setTimeout",
      "window",
      "EventTarget",
      "PointerEvent",
      "MouseEvent",
      "Event",
      `return ${expression};`,
    ) as (...args: unknown[]) => Promise<unknown>;

    await expect(
      evaluate(
        documentStub,
        setTimeout,
        { PointerEvent: EventStub, KeyboardEvent: EventStub },
        Target,
        EventStub,
        EventStub,
        EventStub,
      ),
    ).resolves.toMatchObject({
      status: "already-selected",
      controlKind: "slider",
      availableLevels: ["pro"],
      resolvedLevel: "pro",
      modelUnchanged: true,
    });
  });

  it("resolves a label-less composite slider at maximum from the managed maximum", async () => {
    class Target {
      dispatchEvent(_event: unknown): boolean {
        return true;
      }
    }
    class Node extends Target {
      public children: Node[] = [];
      constructor(
        public textContent: string,
        private readonly attributes: Record<string, string>,
      ) {
        super();
      }
      getAttribute(name: string): string | null {
        return this.attributes[name] ?? null;
      }
      getBoundingClientRect(): { width: number; height: number } {
        return { width: 100, height: 30 };
      }
      querySelectorAll(_selector: string): Node[] {
        return this.children;
      }
      focus(): void {}
      override dispatchEvent(event: unknown): boolean {
        return true;
      }
    }
    class EventStub {
      constructor(
        public readonly type: string,
        _init?: unknown,
      ) {}
    }

    const sliderReadback = new Node("", {
      role: "slider",
      tabindex: "-1",
      "aria-hidden": "true",
      "aria-valuemin": "0",
      "aria-valuemax": "2",
      "aria-valuenow": "2",
    });
    const powerOwner = new Node("", {
      role: "menuitem",
      tabindex: "0",
      "aria-label": "Power",
      "aria-keyshortcuts": "ArrowLeft ArrowRight",
      "data-orientation": "vertical",
    });
    powerOwner.children = [sliderReadback];
    const modelMenuItem = new Node("Model GPT-5.6 Sol", { role: "menuitem" });
    const effortMenuItem = new Node("Effort GPT-9.9", { role: "menuitem" });
    const reasoningOwner = {
      getAttribute: (name: string) =>
        name === "data-testid" ? "composer-intelligence-picker-content" : null,
      getBoundingClientRect: () => ({ width: 100, height: 30 }),
      querySelectorAll: () => [powerOwner, sliderReadback, modelMenuItem, effortMenuItem],
    };
    const documentStub = {
      querySelector: () => null,
      querySelectorAll: (selector: string) =>
        selector.includes("composer-intelligence-picker-content") ? [reasoningOwner] : [],
    };
    const expression = buildBrowserReasoningExpressionForTest({
      intent: "high",
      managedSlot: { slotId: 3, expectedControl: "slider", maximumReasoning: "high" },
    });
    const evaluate = new Function(
      "document",
      "setTimeout",
      "window",
      "EventTarget",
      "PointerEvent",
      "MouseEvent",
      "Event",
      `return ${expression};`,
    ) as (...args: unknown[]) => Promise<unknown>;

    await expect(
      evaluate(
        documentStub,
        setTimeout,
        { PointerEvent: EventStub, KeyboardEvent: EventStub },
        Target,
        EventStub,
        EventStub,
        EventStub,
      ),
    ).resolves.toMatchObject({
      status: "already-selected",
      controlKind: "slider",
      availableLevels: ["high"],
      resolvedLevel: "high",
      modelUnchanged: true,
    });
  });

  it("does not override a read label with the managed maximum", async () => {
    class Target {
      dispatchEvent(_event: unknown): boolean {
        return true;
      }
    }
    class Node extends Target {
      public children: Node[] = [];
      constructor(
        public textContent: string,
        private readonly attributes: Record<string, string>,
      ) {
        super();
      }
      getAttribute(name: string): string | null {
        return this.attributes[name] ?? null;
      }
      getBoundingClientRect(): { width: number; height: number } {
        return { width: 100, height: 30 };
      }
      querySelectorAll(_selector: string): Node[] {
        return this.children;
      }
      focus(): void {}
      override dispatchEvent(event: unknown): boolean {
        return true;
      }
    }
    class EventStub {
      constructor(
        public readonly type: string,
        _init?: unknown,
      ) {}
    }

    const sliderReadback = new Node("", {
      role: "slider",
      tabindex: "-1",
      "aria-hidden": "true",
      "aria-valuemin": "0",
      "aria-valuemax": "4",
      "aria-valuenow": "4",
      "aria-valuetext": "Standard",
    });
    const powerOwner = new Node("", {
      role: "menuitem",
      tabindex: "0",
      "aria-label": "Power",
      "aria-keyshortcuts": "ArrowLeft ArrowRight",
      "data-orientation": "vertical",
    });
    powerOwner.children = [sliderReadback];
    const modelMenuItem = new Node("Model GPT-5.6 Sol", { role: "menuitem" });
    const effortMenuItem = new Node("Effort Standard", { role: "menuitem" });
    const reasoningOwner = {
      getAttribute: (name: string) =>
        name === "data-testid" ? "composer-intelligence-picker-content" : null,
      getBoundingClientRect: () => ({ width: 100, height: 30 }),
      querySelectorAll: () => [powerOwner, sliderReadback, modelMenuItem, effortMenuItem],
    };
    const documentStub = {
      querySelector: () => null,
      querySelectorAll: (selector: string) =>
        selector.includes("composer-intelligence-picker-content") ? [reasoningOwner] : [],
    };
    const expression = buildBrowserReasoningExpressionForTest({
      intent: "pro",
      managedSlot: { slotId: 1, expectedControl: "slider", maximumReasoning: "pro" },
    });
    const evaluate = new Function(
      "document",
      "setTimeout",
      "window",
      "EventTarget",
      "PointerEvent",
      "MouseEvent",
      "Event",
      `return ${expression};`,
    ) as (...args: unknown[]) => Promise<unknown>;

    await expect(
      evaluate(
        documentStub,
        setTimeout,
        { PointerEvent: EventStub, KeyboardEvent: EventStub },
        Target,
        EventStub,
        EventStub,
        EventStub,
      ),
    ).resolves.toMatchObject({
      status: "unavailable",
      controlKind: "slider",
      availableLevels: ["medium"],
      resolvedLevel: "medium",
      modelUnchanged: true,
      diagnostic: { controlCount: 1, matchingControlCount: 1, observedKinds: ["slider"] },
    });
  });

  it("resolves a label-less direct slider at maximum from the managed maximum", async () => {
    class Target {
      dispatchEvent(_event: unknown): boolean {
        return true;
      }
    }
    class Slider extends Target {
      public parentElement: { querySelectorAll: () => unknown[] } | null = null;
      constructor(
        private currentValue: string,
        private readonly attributes: Record<string, string>,
        private readonly onInput?: () => void,
      ) {
        super();
      }
      get value(): string {
        return this.currentValue;
      }
      set value(value: string) {
        this.currentValue = value;
      }
      getAttribute(name: string): string | null {
        return this.attributes[name] ?? null;
      }
      setAttribute(name: string, value: string): void {
        this.attributes[name] = value;
      }
      getBoundingClientRect(): { width: number; height: number } {
        return { width: 100, height: 30 };
      }
      matches(selector: string): boolean {
        return selector.includes('input[type="range"]');
      }
      override dispatchEvent(event: unknown): boolean {
        if ((event as { type?: string }).type === "input") this.onInput?.();
        return true;
      }
    }
    class Node extends Target {
      constructor(
        public textContent: string,
        private readonly attributes: Record<string, string>,
      ) {
        super();
      }
      getAttribute(name: string): string | null {
        return this.attributes[name] ?? null;
      }
      getBoundingClientRect(): { width: number; height: number } {
        return { width: 100, height: 30 };
      }
    }
    class EventStub {
      constructor(
        public readonly type: string,
        _init?: unknown,
      ) {}
    }

    const liveSlider = new Slider("4", {
      "aria-valuemax": "4",
      "aria-valuetext": "3.7",
    });
    const modelMenuItem = new Node("Model GPT-5.6 Sol", { role: "menuitem" });
    const reasoningOwner = {
      getAttribute: (name: string) =>
        name === "data-testid" ? "composer-intelligence-picker-content" : null,
      getBoundingClientRect: () => ({ width: 100, height: 30 }),
      querySelectorAll: (_selector: string) => [liveSlider, modelMenuItem],
    };
    const documentStub = {
      querySelector: () => null,
      querySelectorAll: (selector: string) => {
        if (selector.includes("composer-intelligence-picker-content")) return [reasoningOwner];
        return selector.includes('input[type="range"]') || selector.includes('role="slider"')
          ? [liveSlider]
          : [];
      },
    };
    const expression = buildBrowserReasoningExpressionForTest({
      intent: "pro",
      managedSlot: { slotId: 1, expectedControl: "slider", maximumReasoning: "pro" },
    });
    const evaluate = new Function(
      "document",
      "setTimeout",
      "window",
      "EventTarget",
      "PointerEvent",
      "MouseEvent",
      "Event",
      `return ${expression};`,
    ) as (...args: unknown[]) => Promise<unknown>;

    await expect(
      evaluate(
        documentStub,
        (callback: () => void) => callback(),
        { PointerEvent: EventStub },
        Target,
        EventStub,
        EventStub,
        EventStub,
      ),
    ).resolves.toMatchObject({
      status: "already-selected",
      controlKind: "slider",
      availableLevels: ["pro"],
      resolvedLevel: "pro",
      modelUnchanged: true,
    });
  });

  it("does not fall back without a managed slot maximum", async () => {
    class Target {
      dispatchEvent(_event: unknown): boolean {
        return true;
      }
    }
    class Slider extends Target {
      constructor(
        private currentValue: string,
        private readonly attributes: Record<string, string>,
      ) {
        super();
      }
      get value(): string {
        return this.currentValue;
      }
      set value(value: string) {
        this.currentValue = value;
      }
      getAttribute(name: string): string | null {
        return this.attributes[name] ?? null;
      }
      setAttribute(name: string, value: string): void {
        this.attributes[name] = value;
      }
      getBoundingClientRect(): { width: number; height: number } {
        return { width: 100, height: 30 };
      }
      matches(selector: string): boolean {
        return selector.includes('input[type="range"]');
      }
      override dispatchEvent(event: unknown): boolean {
        return true;
      }
    }
    class Node extends Target {
      constructor(
        public textContent: string,
        private readonly attributes: Record<string, string>,
      ) {
        super();
      }
      getAttribute(name: string): string | null {
        return this.attributes[name] ?? null;
      }
      getBoundingClientRect(): { width: number; height: number } {
        return { width: 100, height: 30 };
      }
    }
    class EventStub {
      constructor(
        public readonly type: string,
        _init?: unknown,
      ) {}
    }

    const liveSlider = new Slider("4", {
      "aria-valuemax": "4",
      "aria-valuetext": "3.7",
    });
    const modelMenuItem = new Node("Model GPT-5.6 Sol", { role: "menuitem" });
    const reasoningOwner = {
      getAttribute: (name: string) =>
        name === "data-testid" ? "composer-intelligence-picker-content" : null,
      getBoundingClientRect: () => ({ width: 100, height: 30 }),
      querySelectorAll: (_selector: string) => [liveSlider, modelMenuItem],
    };
    const documentStub = {
      querySelector: () => null,
      querySelectorAll: (selector: string) => {
        if (selector.includes("composer-intelligence-picker-content")) return [reasoningOwner];
        return selector.includes('input[type="range"]') || selector.includes('role="slider"')
          ? [liveSlider]
          : [];
      },
    };
    const expression = buildBrowserReasoningExpressionForTest({
      intent: "pro",
      managedSlot: null,
    });
    const evaluate = new Function(
      "document",
      "setTimeout",
      "window",
      "EventTarget",
      "PointerEvent",
      "MouseEvent",
      "Event",
      `return ${expression};`,
    ) as (...args: unknown[]) => Promise<unknown>;

    await expect(
      evaluate(
        documentStub,
        (callback: () => void) => callback(),
        { PointerEvent: EventStub },
        Target,
        EventStub,
        EventStub,
        EventStub,
      ),
    ).resolves.toMatchObject({
      status: "unavailable",
      controlKind: "slider",
      resolvedLevel: null,
    });
  });

  it("does not fall back when the managed maximum differs from the requested intent", async () => {
    class Target {
      dispatchEvent(_event: unknown): boolean {
        return true;
      }
    }
    class Slider extends Target {
      constructor(
        private currentValue: string,
        private readonly attributes: Record<string, string>,
      ) {
        super();
      }
      get value(): string {
        return this.currentValue;
      }
      set value(value: string) {
        this.currentValue = value;
      }
      getAttribute(name: string): string | null {
        return this.attributes[name] ?? null;
      }
      setAttribute(name: string, value: string): void {
        this.attributes[name] = value;
      }
      getBoundingClientRect(): { width: number; height: number } {
        return { width: 100, height: 30 };
      }
      matches(selector: string): boolean {
        return selector.includes('input[type="range"]');
      }
      override dispatchEvent(event: unknown): boolean {
        return true;
      }
    }
    class Node extends Target {
      constructor(
        public textContent: string,
        private readonly attributes: Record<string, string>,
      ) {
        super();
      }
      getAttribute(name: string): string | null {
        return this.attributes[name] ?? null;
      }
      getBoundingClientRect(): { width: number; height: number } {
        return { width: 100, height: 30 };
      }
    }
    class EventStub {
      constructor(
        public readonly type: string,
        _init?: unknown,
      ) {}
    }

    const liveSlider = new Slider("4", {
      "aria-valuemax": "4",
      "aria-valuetext": "3.7",
    });
    const modelMenuItem = new Node("Model GPT-5.6 Sol", { role: "menuitem" });
    const reasoningOwner = {
      getAttribute: (name: string) =>
        name === "data-testid" ? "composer-intelligence-picker-content" : null,
      getBoundingClientRect: () => ({ width: 100, height: 30 }),
      querySelectorAll: (_selector: string) => [liveSlider, modelMenuItem],
    };
    const documentStub = {
      querySelector: () => null,
      querySelectorAll: (selector: string) => {
        if (selector.includes("composer-intelligence-picker-content")) return [reasoningOwner];
        return selector.includes('input[type="range"]') || selector.includes('role="slider"')
          ? [liveSlider]
          : [];
      },
    };
    const expression = buildBrowserReasoningExpressionForTest({
      intent: "pro",
      managedSlot: { slotId: 1, expectedControl: "slider", maximumReasoning: "high" },
    });
    const evaluate = new Function(
      "document",
      "setTimeout",
      "window",
      "EventTarget",
      "PointerEvent",
      "MouseEvent",
      "Event",
      `return ${expression};`,
    ) as (...args: unknown[]) => Promise<unknown>;

    await expect(
      evaluate(
        documentStub,
        (callback: () => void) => callback(),
        { PointerEvent: EventStub },
        Target,
        EventStub,
        EventStub,
        EventStub,
      ),
    ).resolves.toMatchObject({
      status: "unavailable",
      controlKind: "slider",
      resolvedLevel: null,
    });
  });

  it("does not confuse a reasoning-pill change with a base-model change", async () => {
    class Target {
      dispatchEvent(_event: unknown): boolean {
        return true;
      }
    }
    class Node extends Target {
      constructor(
        public textContent: string,
        private readonly attributes: Record<string, string>,
        private readonly onClick?: () => void,
      ) {
        super();
      }
      getAttribute(name: string): string | null {
        return this.attributes[name] ?? null;
      }
      setAttribute(name: string, value: string): void {
        this.attributes[name] = value;
      }
      getBoundingClientRect(): { width: number; height: number } {
        return { width: 100, height: 30 };
      }
      override dispatchEvent(event: unknown): boolean {
        if ((event as { type?: string }).type === "click") this.onClick?.();
        return true;
      }
    }
    class EventStub {
      constructor(
        public readonly type: string,
        _init?: unknown,
      ) {}
    }
    const run = async (changeBaseModel: boolean) => {
      const reasoningPill = new Node("Standard", {
        "data-testid": "model-switcher-dropdown-button",
      });
      const baseModel = new Node("GPT 5.5", { role: "menuitem" });
      const standard = new Node("Standard", { role: "menuitemradio", "aria-checked": "true" });
      const high = new Node("High", { role: "menuitemradio", "aria-checked": "false" }, () => {
        // This visual pill is reasoning-only and must not affect model proof.
        reasoningPill.textContent = "High";
        standard.setAttribute("aria-checked", "false");
        high.setAttribute("aria-checked", "true");
        if (changeBaseModel) {
          baseModel.textContent = "GPT 5.6";
        }
      });
      const reasoningOwner = {
        getAttribute: (name: string) =>
          name === "data-testid" ? "composer-intelligence-picker-content" : null,
        getBoundingClientRect: () => ({ width: 100, height: 30 }),
        querySelectorAll: (_selector: string) => [standard, high, baseModel],
      };
      const documentStub = {
        querySelector: (_selector: string) => reasoningPill,
        querySelectorAll: (selector: string) => {
          if (selector.includes("composer-intelligence-picker-content")) return [reasoningOwner];
          if (selector.includes('role="option"') || selector.includes('role="menuitemradio"')) {
            return [standard, high];
          }
          return [];
        },
      };
      const expression = buildBrowserReasoningExpressionForTest({
        intent: "high",
        managedSlot: { slotId: 3, expectedControl: "dropdown", maximumReasoning: "high" },
      });
      const evaluate = new Function(
        "document",
        "setTimeout",
        "window",
        "EventTarget",
        "PointerEvent",
        "MouseEvent",
        "Event",
        `return ${expression};`,
      ) as (...args: unknown[]) => Promise<unknown>;
      return evaluate(
        documentStub,
        (callback: () => void) => callback(),
        { PointerEvent: EventStub },
        Target,
        EventStub,
        EventStub,
        EventStub,
      );
    };

    await expect(run(false)).resolves.toMatchObject({ status: "switched", modelUnchanged: true });
    await expect(run(true)).resolves.toMatchObject({
      status: "model-changed",
      modelUnchanged: false,
    });
  });

  it("never treats a bare Pro model row outside the owned reasoning container as effort", async () => {
    class Target {
      dispatchEvent(_event: unknown): boolean {
        return true;
      }
    }
    class Node extends Target {
      constructor(
        public textContent: string,
        private readonly attributes: Record<string, string>,
        private readonly onClick?: () => void,
      ) {
        super();
      }
      getAttribute(name: string): string | null {
        return this.attributes[name] ?? null;
      }
      setAttribute(name: string, value: string): void {
        this.attributes[name] = value;
      }
      getBoundingClientRect(): { width: number; height: number } {
        return { width: 100, height: 30 };
      }
      override dispatchEvent(event: unknown): boolean {
        if ((event as { type?: string }).type === "click") this.onClick?.();
        return true;
      }
    }
    class EventStub {
      constructor(
        public readonly type: string,
        _init?: unknown,
      ) {}
    }
    const run = async (intent: "high" | "pro") => {
      let bareProClicks = 0;
      const model = new Node("Thinking 5.5", { "data-testid": "model-switcher-dropdown-button" });
      const bareProModelRow = new Node(
        "Pro",
        { role: "menuitemradio", "aria-checked": "false" },
        () => {
          bareProClicks += 1;
        },
      );
      const standard = new Node("Standard", { role: "menuitemradio", "aria-checked": "true" });
      const high = new Node("High", { role: "menuitemradio", "aria-checked": "false" }, () => {
        standard.setAttribute("aria-checked", "false");
        high.setAttribute("aria-checked", "true");
      });
      const modelMenuItem = new Node("GPT-5.6 Sol", { role: "menuitem" });
      const reasoningOwner = {
        getAttribute: (name: string) =>
          name === "data-testid" ? "composer-intelligence-picker-content" : null,
        getBoundingClientRect: () => ({ width: 100, height: 30 }),
        querySelectorAll: (_selector: string) => [standard, high, modelMenuItem],
      };
      const documentStub = {
        querySelector: (_selector: string) => model,
        querySelectorAll: (selector: string) => {
          if (selector.includes("composer-intelligence-picker-content")) return [reasoningOwner];
          if (selector.includes('role="option"') || selector.includes('role="menuitemradio"')) {
            return [bareProModelRow, standard, high];
          }
          return [];
        },
      };
      const expression = buildBrowserReasoningExpressionForTest({ intent });
      const evaluate = new Function(
        "document",
        "setTimeout",
        "window",
        "EventTarget",
        "PointerEvent",
        "MouseEvent",
        "Event",
        `return ${expression};`,
      ) as (...args: unknown[]) => Promise<unknown>;
      const result = await evaluate(
        documentStub,
        (callback: () => void) => callback(),
        { PointerEvent: EventStub },
        Target,
        EventStub,
        EventStub,
        EventStub,
      );
      return { result, bareProClicks };
    };

    await expect(run("high")).resolves.toMatchObject({
      result: { status: "switched", resolvedLevel: "high" },
      bareProClicks: 0,
    });
    await expect(run("pro")).resolves.toMatchObject({
      result: { status: "unavailable", resolvedLevel: null },
      bareProClicks: 0,
    });
  });
});
