import type CDP from "chrome-remote-interface";
import type Protocol from "devtools-protocol";
import type {
  BrowserModelSelectionEvidence,
  BrowserRunWarning,
  BrowserRuntimeMetadata,
} from "../sessionStore.js";
import type { SessionArtifact } from "../sessionStore.js";
import type { ThinkingTimeLevel } from "../oracle/types.js";

export type ChromeClient = Awaited<ReturnType<typeof CDP>>;
export type CookieParam = Protocol.Network.CookieParam;
export type BrowserModelStrategy = "select" | "current" | "ignore";
export type BrowserResearchMode = "off" | "deep";
export type BrowserArchiveMode = "auto" | "always" | "never";
/**
 * Browser-only reasoning intents. These deliberately do not share the API
 * reasoning domain: ChatGPT's Pro control is an effort level, never a model
 * picker row.
 */
export type BrowserReasoningIntent = "instant" | "medium" | "high" | "extra-high" | "pro";
export type BrowserReasoningControlKind = "slider" | "dropdown";

/** Exact model/version rows owned by the current ChatGPT picker. */
export type BrowserModelChoice = "Latest" | "GPT-5.6 Sol" | "GPT-5.5";

/** Capability declared by the managed Browser-slots transport. */
export interface BrowserManagedSlotCapability {
  slotId: 1 | 2 | 3 | 4 | 5 | 10;
  expectedControl: BrowserReasoningControlKind;
  maximumReasoning: "pro" | "high";
}

/** Redacted identity captured from bounded model-picker signals. */
export interface BrowserModelIdentityEvidence {
  fingerprint: string;
  /** Exact visible model row, when the picker exposed one. */
  row?: BrowserModelChoice | null;
  source: "chatgpt-model-picker";
  capturedAt: string;
}

export type BrowserLogger = ((message: string) => void) & {
  verbose?: boolean;
  sessionLog?: (message: string) => void;
};

export interface BrowserAttachment {
  path: string;
  displayPath: string;
  sizeBytes?: number;
  generatedBundle?: boolean;
}

export interface BrowserGeneratedImage {
  url: string;
  alt?: string;
  width?: number;
  height?: number;
  fileId?: string;
}

export interface BrowserDownloadableFile {
  url: string;
  downloadUrl?: string;
  sandboxUrl?: string;
  filename?: string;
  label?: string;
  mimeType?: string;
}

export interface SavedBrowserImage extends SessionArtifact {
  kind: "image";
  url: string;
  finalUrl?: string;
  alt?: string;
  width?: number;
  height?: number;
  fileId?: string;
}

export interface SavedBrowserFile extends SessionArtifact {
  kind: "file";
  url: string;
  finalUrl?: string;
  sandboxUrl?: string;
  filename?: string;
}

export interface BrowserAutomationConfig {
  chromeProfile?: string | null;
  chromePath?: string | null;
  chromeCookiePath?: string | null;
  attachRunning?: boolean;
  browserTabRef?: string | null;
  url?: string;
  chatgptUrl?: string | null;
  timeoutMs?: number;
  debugPort?: number | null;
  inputTimeoutMs?: number;
  /** Time budget for attachment upload/readiness before clicking send. */
  attachmentTimeoutMs?: number;
  /** Delay before rechecking the conversation after an assistant timeout. */
  assistantRecheckDelayMs?: number;
  /** Time budget for the delayed recheck attempt. */
  assistantRecheckTimeoutMs?: number;
  /** Wait for an existing shared Chrome to appear before launching a new one. */
  reuseChromeWaitMs?: number;
  /** Max time to wait for a shared manual-login profile lock (serializes parallel runs). */
  profileLockTimeoutMs?: number;
  /** Soft limit for concurrent ChatGPT tabs sharing one manual-login profile. */
  maxConcurrentTabs?: number;
  /** Delay before starting periodic auto-reattach attempts after a timeout. */
  autoReattachDelayMs?: number;
  /** Interval between auto-reattach attempts (0 disables). */
  autoReattachIntervalMs?: number;
  /** Time budget for each auto-reattach attempt. */
  autoReattachTimeoutMs?: number;
  cookieSync?: boolean;
  cookieNames?: string[] | null;
  cookieSyncWaitMs?: number;
  inlineCookies?: CookieParam[] | null;
  inlineCookiesSource?: string | null;
  headless?: boolean;
  keepBrowser?: boolean;
  hideWindow?: boolean;
  desiredModel?: string | null;
  /** True only when this resumed turn explicitly requested a model row. */
  explicitResumeModel?: boolean;
  modelStrategy?: BrowserModelStrategy;
  debug?: boolean;
  allowCookieErrors?: boolean;
  remoteChrome?: { host: string; port: number } | null;
  remoteChromeBrowserWSEndpoint?: string | null;
  remoteChromeProfileRoot?: string | null;
  manualLogin?: boolean;
  manualLoginProfileDir?: string | null;
  manualLoginCookieSync?: boolean;
  /** Copy this signed-in Chrome user-data dir to a throwaway profile and run against it (login-free). */
  copyProfileSource?: string | null;
  /** Thinking time intensity level for Thinking/Pro models: light, standard, extended, heavy */
  thinkingTime?: ThinkingTimeLevel;
  /**
   * Resolved browser reasoning intent. This is distinct from `desiredModel`;
   * it is normally derived from thinkingTime/model compatibility by the CLI
   * or MCP adapter and may be supplied by managed slot execution.
   */
  reasoningIntent?: BrowserReasoningIntent;
  /** Managed-slot capability derived from the runner environment. */
  managedSlot?: BrowserManagedSlotCapability | null;
  /** Original conversation model identity used to fail closed across later turns/resume. */
  originalModelIdentity?: BrowserModelIdentityEvidence | null;
  /** Browser-only research mode. "deep" activates ChatGPT Deep Research. */
  researchMode?: BrowserResearchMode;
  /** Archive completed ChatGPT conversations after local artifacts are saved. */
  archiveConversations?: BrowserArchiveMode;
  /** Existing ChatGPT conversation URL to open before submitting the prompt. */
  resumeConversationUrl?: string | null;
}

export interface BrowserRunOptions {
  prompt: string;
  attachments?: BrowserAttachment[];
  /**
   * Optional secondary submission to try if the initial prompt is rejected by ChatGPT
   * (e.g. inline file paste exceeds composer limits). Intended for auto inline->upload fallback.
   */
  fallbackSubmission?: { prompt: string; attachments: BrowserAttachment[] };
  config?: BrowserAutomationConfig;
  log?: BrowserLogger;
  heartbeatIntervalMs?: number;
  verbose?: boolean;
  /** Session id used for cross-process browser slot diagnostics. */
  sessionId?: string;
  /** Browser-only image generation output path. */
  generateImagePath?: string;
  /** Optional output path for image operations. */
  outputPath?: string;
  /** Additional prompts to submit in the same browser conversation after the initial answer. */
  followUpPrompts?: string[];
  /**
   * Close a newly-created completed run tab even when the owning Chrome process
   * must remain alive. Used by long-lived shared browser services; incomplete
   * and attached-existing tabs are still preserved for recovery/user ownership.
   */
  closeOwnedTabOnComplete?: boolean;
  /** Optional hook to persist runtime and independently captured browser evidence. */
  runtimeHintCb?: (
    hint: BrowserRuntimeMetadata,
    modelSelection?: BrowserModelSelectionEvidence,
    reasoningSelection?: BrowserReasoningSelectionEvidence,
    reasoningSelections?: BrowserReasoningSelectionEvidence[],
  ) => void | Promise<void>;
}

export interface BrowserArchiveResult {
  mode: BrowserArchiveMode;
  attempted: boolean;
  archived: boolean;
  reason?: string;
  conversationUrl?: string;
  error?: string;
}

export interface BrowserRunResult {
  answerText: string;
  answerMarkdown: string;
  answerHtml?: string;
  artifacts?: SessionArtifact[];
  generatedImages?: BrowserGeneratedImage[];
  savedImages?: SavedBrowserImage[];
  downloadableFiles?: BrowserDownloadableFile[];
  savedFiles?: SavedBrowserFile[];
  archive?: BrowserArchiveResult;
  modelSelection?: BrowserModelSelectionEvidence;
  reasoningSelection?: BrowserReasoningSelectionEvidence;
  reasoningSelections?: BrowserReasoningSelectionEvidence[];
  warnings?: BrowserRunWarning[];
  tookMs: number;
  answerTokens: number;
  answerChars: number;
  browserTransport?: "cdp";
  chromePid?: number;
  chromePort?: number;
  chromeHost?: string;
  chromeBrowserWSEndpoint?: string;
  chromeProfileRoot?: string;
  userDataDir?: string;
  chromeTargetId?: string;
  tabUrl?: string;
  conversationId?: string;
  promptSubmitted?: boolean;
  committedUserTurn?: BrowserRuntimeMetadata["committedUserTurn"];
  committedAssistantTurn?: BrowserRuntimeMetadata["committedAssistantTurn"];
  identityScope?: BrowserRuntimeMetadata["identityScope"];
  controllerPid?: number;
}

export type ResolvedBrowserConfig = Required<
  Omit<
    BrowserAutomationConfig,
    | "chromeProfile"
    | "chromePath"
    | "chromeCookiePath"
    | "desiredModel"
    | "explicitResumeModel"
    | "remoteChrome"
    | "remoteChromeBrowserWSEndpoint"
    | "remoteChromeProfileRoot"
    | "thinkingTime"
    | "reasoningIntent"
    | "managedSlot"
    | "originalModelIdentity"
    | "modelStrategy"
    | "maxConcurrentTabs"
    | "researchMode"
    | "copyProfileSource"
  >
> & {
  chromeProfile?: string | null;
  chromePath?: string | null;
  chromeCookiePath?: string | null;
  attachRunning?: boolean;
  browserTabRef?: string | null;
  desiredModel?: string | null;
  explicitResumeModel?: boolean;
  modelStrategy?: BrowserModelStrategy;
  thinkingTime?: ThinkingTimeLevel;
  reasoningIntent?: BrowserReasoningIntent;
  managedSlot?: BrowserManagedSlotCapability | null;
  originalModelIdentity?: BrowserModelIdentityEvidence | null;
  debugPort?: number | null;
  inlineCookiesSource?: string | null;
  remoteChrome?: { host: string; port: number } | null;
  remoteChromeBrowserWSEndpoint?: string | null;
  remoteChromeProfileRoot?: string | null;
  manualLogin?: boolean;
  manualLoginProfileDir?: string | null;
  manualLoginCookieSync?: boolean;
  copyProfileSource?: string | null;
  maxConcurrentTabs: number;
  researchMode: BrowserResearchMode;
  archiveConversations: BrowserArchiveMode;
};

export type BrowserReasoningSelectionStatus =
  | "already-selected"
  | "switched"
  | "unavailable"
  | "ambiguous"
  | "model-changed"
  | "model-mismatch"
  | "original-model-missing";

/**
 * Structured, redacted proof captured before a ChatGPT prompt is submitted.
 * Only recognised reasoning labels are retained; page text is never copied.
 */
export interface BrowserReasoningSelectionEvidence {
  requestedIntent: BrowserReasoningIntent;
  controlKind: BrowserReasoningControlKind | null;
  availableLevels: BrowserReasoningIntent[];
  resolvedLevel: BrowserReasoningIntent | null;
  status: BrowserReasoningSelectionStatus;
  verified: boolean;
  modelUnchanged: boolean;
  originalModelIdentity?: BrowserModelIdentityEvidence | null;
  /** Exact checked model row observed in the same reasoning attempt. */
  observedModelRow?: BrowserModelChoice | null;
  observedModelFingerprint?: string | null;
  managedSlotId?: number;
  turnIndex?: number;
  attemptIndex?: number;
  capturedAt: string;
  diagnostic: {
    controlCount: number;
    matchingControlCount: number;
    observedKinds: BrowserReasoningControlKind[];
  };
}
