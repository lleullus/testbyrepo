import type { BrowserLogger, ChromeClient } from "../types.js";
import type { ProviderDomAdapter, ProviderDomFlowContext } from "../providerDomFlow.js";
import { ensurePromptReady } from "../actions/navigation.js";
import {
  submitPrompt,
  type AttachmentReadyExpectation,
  type PromptCommitTurnIdentity,
} from "../actions/promptComposer.js";
import type { ConversationTurnIdentity } from "../conversationTurns.js";
import {
  waitForAssistantResponse,
  type AssistantResponseIdentityScope,
} from "../actions/assistantResponse.js";

interface ChatgptDomProviderState {
  runtime: ChromeClient["Runtime"];
  input: ChromeClient["Input"];
  logger: BrowserLogger;
  timeoutMs: number;
  inputTimeoutMs?: number;
  attachmentTimeoutMs?: number;
  baselineTurns?: number | null;
  attachmentNames?: AttachmentReadyExpectation[];
  committedUserTurn?: PromptCommitTurnIdentity | null;
  committedAssistantTurn?: ConversationTurnIdentity | null;
  onPromptSubmitted?: () => Promise<void> | void;
}

function requireState(ctx: ProviderDomFlowContext): ChatgptDomProviderState {
  const state = ctx.state as ChatgptDomProviderState | undefined;
  if (!state?.runtime || !state?.input || !state?.logger) {
    throw new Error("chatgptDomProvider requires runtime/input/logger in context.state.");
  }
  return state;
}

async function waitForUi(ctx: ProviderDomFlowContext): Promise<void> {
  const state = requireState(ctx);
  await ensurePromptReady(state.runtime, state.inputTimeoutMs ?? 30_000, state.logger);
}

async function typePrompt(_ctx: ProviderDomFlowContext): Promise<void> {
  // submitPrompt() handles typing + send for ChatGPT.
}

async function submitPromptViaAdapter(ctx: ProviderDomFlowContext): Promise<void> {
  const state = requireState(ctx);
  const committedUserTurn = await submitPrompt(
    {
      runtime: state.runtime,
      input: state.input,
      attachmentNames: state.attachmentNames ?? [],
      baselineTurns: state.baselineTurns ?? undefined,
      inputTimeoutMs: state.inputTimeoutMs ?? undefined,
      attachmentTimeoutMs: state.attachmentTimeoutMs ?? undefined,
      onPromptSubmitted: state.onPromptSubmitted,
    },
    ctx.prompt,
    state.logger,
  );
  state.committedUserTurn = committedUserTurn;
  state.committedAssistantTurn = null;
}

async function waitForResponse(ctx: ProviderDomFlowContext): Promise<{
  text: string;
  html?: string;
  meta?: { turnId?: string | null; messageId?: string | null };
}> {
  const state = requireState(ctx);
  const identityScope: AssistantResponseIdentityScope | undefined = state.committedUserTurn
    ? {
        committedUserTurn: state.committedUserTurn,
        committedAssistantTurn: state.committedAssistantTurn,
      }
    : undefined;
  const answer = await waitForAssistantResponse(
    state.runtime,
    state.timeoutMs,
    state.logger,
    state.baselineTurns ?? undefined,
    undefined,
    identityScope,
  );
  if (identityScope?.committedAssistantTurn) {
    state.committedAssistantTurn = identityScope.committedAssistantTurn;
  }
  return {
    text: answer.text,
    html: answer.html,
    meta: answer.meta,
  };
}

export const chatgptDomProvider: ProviderDomAdapter = {
  providerName: "chatgpt-web",
  waitForUi,
  typePrompt,
  submitPrompt: submitPromptViaAdapter,
  waitForResponse,
};
