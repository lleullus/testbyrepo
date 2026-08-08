import { afterEach, beforeEach, describe, expect, test } from "vitest";
import os from "node:os";
import path from "node:path";
import {
  assertManagedBrowserReasoningIntent,
  DEFAULT_CHATGPT_COOKIE_NAMES,
  resolveBrowserConfig,
  resolveManagedBrowserSlotCapability,
} from "../../src/browser/config.js";
import { CHATGPT_URL, DEEP_RESEARCH_DEFAULT_TIMEOUT_MS } from "../../src/browser/constants.js";

describe("resolveBrowserConfig", () => {
  const originalProfileDir = process.env.ORACLE_BROWSER_PROFILE_DIR;
  const originalMaxTabs = process.env.ORACLE_BROWSER_MAX_CONCURRENT_TABS;
  const originalSlotId = process.env.ORACLE_BROWSER_SLOT_ID;

  beforeEach(() => {
    // Isolate from the caller's environment: a developer/CI export of the max-tabs
    // override must not leak into tests that assert built-in defaults. afterEach
    // below still restores the caller's original value once the suite finishes.
    delete process.env.ORACLE_BROWSER_MAX_CONCURRENT_TABS;
    delete process.env.ORACLE_BROWSER_SLOT_ID;
  });

  afterEach(() => {
    if (originalProfileDir === undefined) {
      delete process.env.ORACLE_BROWSER_PROFILE_DIR;
    } else {
      process.env.ORACLE_BROWSER_PROFILE_DIR = originalProfileDir;
    }
    if (originalMaxTabs === undefined) {
      delete process.env.ORACLE_BROWSER_MAX_CONCURRENT_TABS;
    } else {
      process.env.ORACLE_BROWSER_MAX_CONCURRENT_TABS = originalMaxTabs;
    }
    if (originalSlotId === undefined) {
      delete process.env.ORACLE_BROWSER_SLOT_ID;
    } else {
      process.env.ORACLE_BROWSER_SLOT_ID = originalSlotId;
    }
  });

  test("maps managed slots to their independently verified UI capabilities", () => {
    expect(resolveManagedBrowserSlotCapability({ ORACLE_BROWSER_SLOT_ID: "1" })).toEqual({
      slotId: 1,
      expectedControl: "slider",
      maximumReasoning: "pro",
    });
    expect(resolveManagedBrowserSlotCapability({ ORACLE_BROWSER_SLOT_ID: "2" })).toMatchObject({
      expectedControl: "slider",
      maximumReasoning: "pro",
    });
    expect(resolveManagedBrowserSlotCapability({ ORACLE_BROWSER_SLOT_ID: "3" })).toEqual({
      slotId: 3,
      expectedControl: "slider",
      maximumReasoning: "high",
    });
    expect(resolveManagedBrowserSlotCapability({ ORACLE_BROWSER_SLOT_ID: "4" })).toMatchObject({
      expectedControl: "slider",
      maximumReasoning: "high",
    });
    expect(resolveManagedBrowserSlotCapability({ ORACLE_BROWSER_SLOT_ID: "5" })).toMatchObject({
      expectedControl: "dropdown",
      maximumReasoning: "high",
    });
  });

  test("rejects explicit reasoning above a managed capability", () => {
    for (const intent of ["light", "standard", "high", "heavy", "pro"] as const) {
      expect(() =>
        assertManagedBrowserReasoningIntent(
          { slotId: 1, expectedControl: "slider", maximumReasoning: "pro" },
          intent,
        ),
      ).not.toThrow();
    }
    expect(() =>
      assertManagedBrowserReasoningIntent(
        { slotId: 4, expectedControl: "dropdown", maximumReasoning: "high" },
        "heavy",
      ),
    ).toThrow(/supports reasoning up to High/i);
    expect(() =>
      assertManagedBrowserReasoningIntent(
        { slotId: 4, expectedControl: "dropdown", maximumReasoning: "high" },
        "pro",
      ),
    ).toThrow(/supports reasoning up to High/i);
    expect(() =>
      assertManagedBrowserReasoningIntent(
        { slotId: 4, expectedControl: "dropdown", maximumReasoning: "high" },
        "standard",
      ),
    ).not.toThrow();
    expect(() =>
      assertManagedBrowserReasoningIntent(
        { slotId: 4, expectedControl: "dropdown", maximumReasoning: "high" },
        "high",
      ),
    ).not.toThrow();
  });

  test("does not turn a managed capability into a reasoning default", () => {
    process.env.ORACLE_BROWSER_SLOT_ID = "3";

    const resolved = resolveBrowserConfig({ desiredModel: "gpt-5.5-pro" });

    expect(resolved.reasoningIntent).toBeUndefined();
    expect(resolved.managedSlot).toMatchObject({ slotId: 3, maximumReasoning: "high" });
  });

  test("rejects real Pro-only intent on a High-only managed slot", () => {
    process.env.ORACLE_BROWSER_SLOT_ID = "3";

    expect(() =>
      resolveBrowserConfig({ desiredModel: "Thinking 5.5", reasoningIntent: "pro" }),
    ).toThrow(/supports reasoning up to High/i);
  });

  test("maps explicit extended reasoning to High without promoting Pro slots", () => {
    process.env.ORACLE_BROWSER_SLOT_ID = "1";

    expect(resolveBrowserConfig({ thinkingTime: "extended" }).reasoningIntent).toBe("high");
    expect(resolveBrowserConfig({ thinkingTime: "heavy" }).reasoningIntent).toBe("heavy");
  });

  test("returns defaults when config missing", () => {
    const resolved = resolveBrowserConfig(undefined);
    expect(resolved.url).toBe(CHATGPT_URL);
    const isWindows = process.platform === "win32";
    expect(resolved.cookieSync).toBe(!isWindows);
    expect(resolved.cookieNames).toEqual(DEFAULT_CHATGPT_COOKIE_NAMES);
    expect(resolved.headless).toBe(false);
    expect(resolved.manualLogin).toBe(isWindows);
    expect(resolved.profileLockTimeoutMs).toBe(300_000);
    expect(resolved.attachmentTimeoutMs).toBe(45_000);
    expect(resolved.maxConcurrentTabs).toBe(3);
    expect(resolved.researchMode).toBe("off");
    expect(resolved.archiveConversations).toBe("auto");
  });

  test("applies overrides", () => {
    const resolved = resolveBrowserConfig({
      url: "https://example.com",
      timeoutMs: 123,
      inputTimeoutMs: 456,
      attachmentTimeoutMs: 789,
      cookieSync: false,
      headless: true,
      desiredModel: "Custom",
      chromeProfile: "Profile 1",
      chromePath: "/Applications/Chrome",
      browserTabRef: "current",
      debug: true,
      maxConcurrentTabs: 5,
      researchMode: "deep",
      archiveConversations: "never",
    });
    expect(resolved.url).toBe("https://example.com/");
    expect(resolved.timeoutMs).toBe(123);
    expect(resolved.inputTimeoutMs).toBe(456);
    expect(resolved.attachmentTimeoutMs).toBe(789);
    expect(resolved.cookieSync).toBe(false);
    expect(resolved.headless).toBe(true);
    expect(resolved.desiredModel).toBe("Custom");
    expect(resolved.chromeProfile).toBe("Profile 1");
    expect(resolved.chromePath).toBe("/Applications/Chrome");
    expect(resolved.browserTabRef).toBe("current");
    expect(resolved.debug).toBe(true);
    expect(resolved.maxConcurrentTabs).toBe(5);
    expect(resolved.researchMode).toBe("deep");
    expect(resolved.archiveConversations).toBe("never");
  });

  test("allows temporary chat URLs when desiredModel is Pro", () => {
    const resolved = resolveBrowserConfig({
      url: "https://chatgpt.com/?temporary-chat=true",
      desiredModel: "GPT-5.2 Pro",
    });

    expect(resolved.url).toBe("https://chatgpt.com/?temporary-chat=true");
    expect(resolved.desiredModel).toBe("GPT-5.2 Pro");
    expect(resolved.modelStrategy).toBe("select");
  });

  test("resolves manual-login profile dirs from config, env, and default", () => {
    process.env.ORACLE_BROWSER_PROFILE_DIR = "/tmp/env-profile";

    expect(
      resolveBrowserConfig({
        manualLogin: true,
        manualLoginProfileDir: " /tmp/config-profile ",
      }).manualLoginProfileDir,
    ).toBe("/tmp/config-profile");

    expect(resolveBrowserConfig({ manualLogin: true }).manualLoginProfileDir).toBe(
      "/tmp/env-profile",
    );

    process.env.ORACLE_BROWSER_PROFILE_DIR = "   ";
    expect(resolveBrowserConfig({ manualLogin: true }).manualLoginProfileDir).toBe(
      path.join(os.homedir(), ".oracle", "browser-profile"),
    );

    expect(resolveBrowserConfig({ manualLogin: false }).manualLoginProfileDir).toBeNull();
  });

  test("resolves maxConcurrentTabs from config, env, and default", () => {
    process.env.ORACLE_BROWSER_MAX_CONCURRENT_TABS = "5";
    expect(resolveBrowserConfig({ maxConcurrentTabs: 2 }).maxConcurrentTabs).toBe(2);
    expect(resolveBrowserConfig(undefined).maxConcurrentTabs).toBe(5);

    process.env.ORACLE_BROWSER_MAX_CONCURRENT_TABS = "0";
    expect(resolveBrowserConfig(undefined).maxConcurrentTabs).toBe(3);

    process.env.ORACLE_BROWSER_MAX_CONCURRENT_TABS = "not-a-number";
    expect(resolveBrowserConfig(undefined).maxConcurrentTabs).toBe(3);

    for (const malformed of ["5junk", "2.5", "1e2"]) {
      process.env.ORACLE_BROWSER_MAX_CONCURRENT_TABS = malformed;
      expect(resolveBrowserConfig(undefined).maxConcurrentTabs).toBe(3);
    }
  });

  test("uses the longer Deep Research timeout unless explicitly overridden", () => {
    expect(resolveBrowserConfig({ researchMode: "deep" }).timeoutMs).toBe(
      DEEP_RESEARCH_DEFAULT_TIMEOUT_MS,
    );
    expect(resolveBrowserConfig({ researchMode: "deep", timeoutMs: 123 }).timeoutMs).toBe(123);
  });
});
