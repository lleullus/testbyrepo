import CDP from "chrome-remote-interface";
import os from "node:os";
import path from "node:path";
import { mkdtemp, mkdir, rm } from "node:fs/promises";
import type { BrowserRuntimeMetadata, BrowserSessionConfig } from "../sessionStore.js";
import {
  waitForAssistantResponse,
  captureAssistantMarkdown,
  navigateToChatGPT,
  ensureNotBlocked,
  ensureLoggedIn,
  ensurePromptReady,
} from "./pageActions.js";
import type { BrowserLogger, ChromeClient } from "./types.js";
import {
  launchChrome,
  connectToChrome,
  positionChromeWindowOffscreen,
  connectToRemoteChromeTarget,
  listRemoteChromeTargets,
} from "./chromeLifecycle.js";
import { resolveBrowserConfig } from "./config.js";
import { clearStaleChatGptConversationCookies, syncCookies } from "./cookies.js";
import { CHATGPT_URL } from "./constants.js";
import {
  normalizeConversationTurnIdentity,
  type AssistantResponseIdentityScope,
} from "./conversationTurns.js";
import { cleanupStaleProfileState } from "./profileState.js";
import { readDevToolsActivePortInfo } from "./detect.js";
import {
  pickTarget,
  extractConversationIdFromUrl,
  buildConversationUrl,
  withTimeout,
  openConversationFromSidebar,
  openConversationFromSidebarWithRetry,
  waitForLocationChange,
  type TargetInfoLite,
} from "./reattachHelpers.js";
import { waitForDeepResearchCompletion } from "./actions/deepResearch.js";

export interface ReattachDeps {
  listTargets?: () => Promise<TargetInfoLite[]>;
  connect?: (options?: unknown) => Promise<ChromeClient>;
  waitForAssistantResponse?: typeof waitForAssistantResponse;
  captureAssistantMarkdown?: typeof captureAssistantMarkdown;
  waitForDeepResearchCompletion?: typeof waitForDeepResearchCompletion;
  recoverSession?: (
    runtime: BrowserRuntimeMetadata,
    config: BrowserSessionConfig | undefined,
  ) => Promise<ReattachResult>;
  promptPreview?: string;
  onIdentityScopeResolved?: (scope: AssistantResponseIdentityScope) => Promise<void> | void;
}

export interface ReattachResult {
  answerText: string;
  answerMarkdown: string;
  identityScope?: AssistantResponseIdentityScope;
}

interface RecoveryAttribution {
  expectedConversationId: string;
  identityScope: AssistantResponseIdentityScope;
}

function requireRecoveryAttribution(runtime: BrowserRuntimeMetadata): RecoveryAttribution {
  const storedConversationId = runtime.conversationId?.trim() || undefined;
  const urlConversationId = extractConversationIdFromUrl(runtime.tabUrl ?? "");
  if (storedConversationId && urlConversationId && storedConversationId !== urlConversationId) {
    throw new Error("recovery-attribution-unavailable: conflicting conversation identity");
  }
  const expectedConversationId = storedConversationId ?? urlConversationId;
  const committedUserTurn = normalizeConversationTurnIdentity(runtime.committedUserTurn);
  const scopedUserTurn = normalizeConversationTurnIdentity(runtime.identityScope?.committedUserTurn);
  const committedAssistantTurn = normalizeConversationTurnIdentity(
    runtime.identityScope?.committedAssistantTurn,
  );
  const topLevelAssistantTurn = normalizeConversationTurnIdentity(runtime.committedAssistantTurn);
  if (runtime.committedAssistantTurn && !topLevelAssistantTurn) {
    throw new Error("recovery-attribution-unavailable: malformed committed assistant turn identity");
  }
  if (runtime.identityScope?.committedAssistantTurn && !committedAssistantTurn) {
    throw new Error("recovery-attribution-unavailable: malformed committed assistant turn identity");
  }
  if (!expectedConversationId || !committedUserTurn || !scopedUserTurn) {
    throw new Error("recovery-attribution-unavailable: missing durable conversation or user turn identity");
  }
  if (JSON.stringify(committedUserTurn) !== JSON.stringify(scopedUserTurn)) {
    throw new Error("recovery-attribution-unavailable: conflicting committed user turn identity");
  }
  if (
    topLevelAssistantTurn &&
    committedAssistantTurn &&
    JSON.stringify(topLevelAssistantTurn) !== JSON.stringify(committedAssistantTurn)
  ) {
    throw new Error("recovery-attribution-unavailable: conflicting committed assistant turn identity");
  }
  return {
    expectedConversationId,
    identityScope: {
      committedUserTurn,
      committedAssistantTurn: committedAssistantTurn ?? topLevelAssistantTurn,
    },
  };
}

async function requireExpectedConversation(
  Runtime: ChromeClient["Runtime"],
  expectedConversationId: string,
): Promise<void> {
  const { result } = await Runtime.evaluate({ expression: "location.href", returnByValue: true });
  const href = typeof result?.value === "string" ? result.value : "";
  if (extractConversationIdFromUrl(href) !== expectedConversationId) {
    throw new Error("recovery-attribution-unavailable: active conversation does not match stored identity");
  }
}

export async function resumeBrowserSession(
  runtime: BrowserRuntimeMetadata,
  config: BrowserSessionConfig | undefined,
  logger: BrowserLogger,
  deps: ReattachDeps = {},
): Promise<ReattachResult> {
  const attribution = requireRecoveryAttribution(runtime);
  const recoverSession =
    deps.recoverSession ??
    (async (runtimeMeta, configMeta) =>
      resumeBrowserSessionViaNewChrome(runtimeMeta, configMeta, logger, deps));
  let closeAttachedConnection: (() => Promise<void>) | null = null;
  const closeAttached = async (): Promise<void> => {
    const close = closeAttachedConnection;
    closeAttachedConnection = null;
    await close?.().catch(() => undefined);
  };

  if (!runtime.chromePort && !runtime.chromeBrowserWSEndpoint) {
    logger("No running Chrome detected; reopening browser to locate the session.");
    return recoverSession(runtime, config);
  }

  try {
    const liveRuntime = (await refreshAttachRuntime(runtime).catch(() => runtime)) ?? runtime;
    const host = liveRuntime.chromeHost ?? "127.0.0.1";
    const port =
      liveRuntime.chromePort ?? inferPortFromBrowserWSEndpoint(liveRuntime.chromeBrowserWSEndpoint);
    const browserWSEndpoint = liveRuntime.chromeBrowserWSEndpoint ?? undefined;
    const listTargets =
      deps.listTargets ??
      (async () =>
        (await listRemoteChromeTargets({
          host,
          port: port ?? 9222,
          browserWSEndpoint,
        })) as TargetInfoLite[]);
    const targetList = (await listTargets()) as TargetInfoLite[];
    const target = pickTarget(targetList, liveRuntime);
    const connection =
      browserWSEndpoint && !deps.connect
        ? await connectToRemoteChromeTarget(host, port ?? 9222, logger, {
            browserWSEndpoint,
            targetId: target?.targetId ?? target?.id,
            closeTargetOnDispose: false,
          })
        : await (async () => {
            const client = (await (
              deps.connect ?? ((options?: unknown) => CDP(options as CDP.Options))
            )(
              browserWSEndpoint
                ? {
                    target: browserWSEndpoint,
                    local: true,
                    targetId: target?.targetId ?? target?.id,
                  }
                : {
                    host,
                    port,
                    target: target?.targetId ?? target?.id,
                  },
            )) as unknown as ChromeClient;
            return { client, close: () => client.close() };
          })();
    closeAttachedConnection = () => connection.close();

    const client: ChromeClient = connection.client;
    const { Runtime, DOM, Page } = client;
    if (Runtime?.enable) {
      await Runtime.enable();
    }
    if (DOM && typeof DOM.enable === "function") {
      await DOM.enable();
    }
    if (Page && typeof Page.enable === "function") {
      await Page.enable();
    }

    const ensureConversationOpen = async () => {
      const { result } = await Runtime.evaluate({
        expression: "location.href",
        returnByValue: true,
      });
      const href = typeof result?.value === "string" ? result.value : "";
      if (extractConversationIdFromUrl(href) === attribution.expectedConversationId) {
        return;
      }
      const opened = await openConversationFromSidebarWithRetry(
        Runtime,
        {
          conversationId: attribution.expectedConversationId,
          preferProjects: true,
          promptPreview: deps.promptPreview,
        },
        15_000,
      );
      if (!opened) {
        throw new Error("Unable to locate prior ChatGPT conversation in sidebar.");
      }
      await waitForLocationChange(Runtime, 15_000);
      await requireExpectedConversation(Runtime, attribution.expectedConversationId);
    };

    const waitForResponse = deps.waitForAssistantResponse ?? waitForAssistantResponse;
    const captureMarkdown = deps.captureAssistantMarkdown ?? captureAssistantMarkdown;
    const timeoutMs = config?.timeoutMs ?? 120_000;
    const pingTimeoutMs = Math.min(5_000, Math.max(1_500, Math.floor(timeoutMs * 0.05)));
    await withTimeout(
      Runtime.evaluate({ expression: "1+1", returnByValue: true }),
      pingTimeoutMs,
      "Reattach target did not respond",
    );
    await ensureConversationOpen();
    if (config?.researchMode === "deep") {
      throw new Error(
        "recovery-attribution-unavailable: Deep Research recovery lacks stable owned-assistant attribution",
      );
    }
    const answer = await withTimeout(
      waitForResponse(
        Runtime,
        timeoutMs,
        logger,
        undefined,
        attribution.expectedConversationId,
        attribution.identityScope,
        deps.onIdentityScopeResolved,
      ),
      timeoutMs + 5_000,
      "Reattach response timed out",
    );
    await requireExpectedConversation(Runtime, attribution.expectedConversationId);
    const markdown =
      (await withTimeout(
        captureMarkdown(Runtime, answer.meta, logger, attribution.identityScope),
        15_000,
        "Reattach markdown capture timed out",
      )) ?? answer.text;
    await requireExpectedConversation(Runtime, attribution.expectedConversationId);

    await closeAttached();
    return { answerText: answer.text, answerMarkdown: markdown, identityScope: attribution.identityScope };
  } catch (error) {
    await closeAttached();
    const message = error instanceof Error ? error.message : String(error);
    if (message.startsWith("recovery-attribution-unavailable:")) {
      throw error;
    }
    logger(
      `Existing Chrome reattach failed (${message}); reopening browser to locate the session.`,
    );
    return recoverSession(runtime, config);
  }
}

async function refreshAttachRuntime(
  runtime: BrowserRuntimeMetadata,
): Promise<BrowserRuntimeMetadata | null> {
  if (!runtime.chromeProfileRoot) {
    return runtime;
  }
  const host = runtime.chromeHost ?? "127.0.0.1";
  const activePort = await readDevToolsActivePortInfo(runtime.chromeProfileRoot, {
    host,
  });
  if (!activePort) {
    return runtime;
  }
  return {
    ...runtime,
    chromeHost: host,
    chromePort: activePort.port,
    chromeBrowserWSEndpoint: activePort.browserWSEndpoint,
  };
}

function inferPortFromBrowserWSEndpoint(browserWSEndpoint?: string): number | undefined {
  if (!browserWSEndpoint) {
    return undefined;
  }
  try {
    const parsed = new URL(browserWSEndpoint);
    const port = Number.parseInt(parsed.port, 10);
    if (Number.isFinite(port) && port > 0) {
      return port;
    }
  } catch {
    // ignore malformed ws endpoints and fall back to caller defaults
  }
  return undefined;
}

async function resumeBrowserSessionViaNewChrome(
  runtime: BrowserRuntimeMetadata,
  config: BrowserSessionConfig | undefined,
  logger: BrowserLogger,
  deps: ReattachDeps,
): Promise<ReattachResult> {
  const attribution = requireRecoveryAttribution(runtime);
  const resolved = resolveBrowserConfig(config ?? {});
  const manualLogin = Boolean(resolved.manualLogin);
  const userDataDir = manualLogin
    ? (resolved.manualLoginProfileDir ?? path.join(os.homedir(), ".oracle", "browser-profile"))
    : await mkdtemp(path.join(os.tmpdir(), "oracle-reattach-"));
  if (manualLogin) {
    await mkdir(userDataDir, { recursive: true });
  }
  const chrome = await launchChrome(resolved, userDataDir, logger);
  const chromeHost = (chrome as unknown as { host?: string }).host ?? "127.0.0.1";
  const client = await connectToChrome(chrome.port, logger, chromeHost);
  const { Network, Page, Runtime, DOM, Target } = client;

  if (Runtime?.enable) {
    await Runtime.enable();
  }
  if (DOM && typeof DOM.enable === "function") {
    await DOM.enable();
  }
  if (!resolved.headless && resolved.hideWindow) {
    await positionChromeWindowOffscreen(client, logger);
  }
  let appliedCookies = 0;
  if (!manualLogin && resolved.cookieSync) {
    appliedCookies = await syncCookies(Network, resolved.url, resolved.chromeProfile, logger, {
      allowErrors: resolved.allowCookieErrors,
      filterNames: resolved.cookieNames ?? undefined,
      inlineCookies: resolved.inlineCookies ?? undefined,
      cookiePath: resolved.chromeCookiePath ?? undefined,
      waitMs: resolved.cookieSyncWaitMs ?? 0,
    });
  }

  await clearStaleChatGptConversationCookies(Network, Target, logger, {
    preserveConversationIds: [
      runtime.conversationId,
      extractConversationIdFromUrl(runtime.tabUrl ?? ""),
      extractConversationIdFromUrl(resolved.url),
    ],
  });

  await navigateToChatGPT(Page, Runtime, CHATGPT_URL, logger);
  await ensureNotBlocked(Runtime, resolved.headless, logger);
  await ensureLoggedIn(Runtime, logger, { appliedCookies });
  if (resolved.url !== CHATGPT_URL) {
    await navigateToChatGPT(Page, Runtime, resolved.url, logger);
    await ensureNotBlocked(Runtime, resolved.headless, logger);
  }
  await ensurePromptReady(Runtime, resolved.inputTimeoutMs, logger);

  const conversationUrl = buildConversationUrl(runtime, resolved.url);
  if (conversationUrl) {
    logger(`Reopening conversation at ${conversationUrl}`);
    await navigateToChatGPT(Page, Runtime, conversationUrl, logger);
    await ensureNotBlocked(Runtime, resolved.headless, logger);
    await ensurePromptReady(Runtime, resolved.inputTimeoutMs, logger);
  } else {
    const opened = await openConversationFromSidebarWithRetry(
      Runtime,
      {
        conversationId:
          runtime.conversationId ?? extractConversationIdFromUrl(runtime.tabUrl ?? ""),
        preferProjects:
          resolved.url !== CHATGPT_URL ||
          Boolean(
            runtime.tabUrl && (/\/g\//.test(runtime.tabUrl) || runtime.tabUrl.includes("/project")),
          ),
        promptPreview: deps.promptPreview,
      },
      15_000,
    );
    if (!opened) {
      throw new Error("Unable to locate prior ChatGPT conversation in sidebar.");
    }
    await waitForLocationChange(Runtime, 15_000);
  }

  const waitForResponse = deps.waitForAssistantResponse ?? waitForAssistantResponse;
  const captureMarkdown = deps.captureAssistantMarkdown ?? captureAssistantMarkdown;
  const timeoutMs = resolved.timeoutMs ?? 120_000;
  const cleanup = async () => {
    if (client && typeof client.close === "function") {
      try {
        await client.close();
      } catch {
        // ignore
      }
    }
    if (!resolved.keepBrowser) {
      try {
        await chrome.kill();
      } catch {
        // ignore
      }
      if (manualLogin) {
        await cleanupStaleProfileState(userDataDir, logger, { lockRemovalMode: "never" }).catch(
          () => undefined,
        );
      } else {
        await rm(userDataDir, { recursive: true, force: true }).catch(() => undefined);
      }
    }
  };
  await requireExpectedConversation(Runtime, attribution.expectedConversationId);
  if (resolved.researchMode === "deep") {
    await cleanup();
    throw new Error(
      "recovery-attribution-unavailable: Deep Research recovery lacks stable owned-assistant attribution",
    );
  }
  const answer = await waitForResponse(
    Runtime,
    timeoutMs,
    logger,
    undefined,
    attribution.expectedConversationId,
    attribution.identityScope,
    deps.onIdentityScopeResolved,
  );
  await requireExpectedConversation(Runtime, attribution.expectedConversationId);
  const markdown =
    (await captureMarkdown(Runtime, answer.meta, logger, attribution.identityScope)) ?? answer.text;
  await requireExpectedConversation(Runtime, attribution.expectedConversationId);
  await cleanup();

  return {
    answerText: answer.text,
    answerMarkdown: markdown,
    identityScope: attribution.identityScope,
  };
}


// biome-ignore lint/style/useNamingConvention: test-only export used in vitest suite
export const __test__ = {
  pickTarget,
  extractConversationIdFromUrl,
  buildConversationUrl,
  openConversationFromSidebar,
  requireRecoveryAttribution,
};
