import type {
  BrowserLogger,
  BrowserManagedSlotCapability,
  BrowserModelIdentityEvidence,
  BrowserReasoningIntent,
  BrowserReasoningSelectionEvidence,
  ChromeClient,
} from "../types.js";
import type { ThinkingTimeLevel } from "../../oracle/types.js";
import {
  MENU_CONTAINER_SELECTOR,
  MENU_ITEM_SELECTOR,
  MODEL_BUTTON_SELECTOR,
} from "../constants.js";
import { logDomFailure } from "../domDebug.js";
import { buildClickDispatcher } from "./domEvents.js";

// Snapshot of the model-picker / thinking-effort subtree, captured at the moment
// detection fails so a chip-not-found can be diagnosed without re-running with
// --verbose. Loosely typed: the shape is whatever the injected probe returns.
type ThinkingTimePickerDiagnostic = Record<string, unknown>;

type ThinkingTimeOutcome = (
  | { status: "already-selected"; label?: string | null }
  | { status: "switched"; label?: string | null }
  | { status: "chip-not-found"; diagnostic?: ThinkingTimePickerDiagnostic }
  | { status: "menu-not-found"; diagnostic?: ThinkingTimePickerDiagnostic }
  | { status: "option-not-found"; diagnostic?: ThinkingTimePickerDiagnostic }
  | { status: "selection-unverified"; diagnostic?: ThinkingTimePickerDiagnostic }
  | {
      status: "model-kind-not-found";
      diagnostic?: ThinkingTimePickerDiagnostic;
    }
) & { modelKind?: string | null };

const BROWSER_THINKING_LOG_PREFIX = "[browser] Thinking time:";

type BrowserReasoningOutcome = {
  status?:
    | "already-selected"
    | "switched"
    | "unavailable"
    | "ambiguous"
    | "model-changed"
    | "model-mismatch";
  controlKind?: "slider" | "dropdown" | null;
  availableLevels?: BrowserReasoningIntent[];
  resolvedLevel?: BrowserReasoningIntent | null;
  modelUnchanged?: boolean;
  originalModelFingerprint?: string | null;
  observedModelFingerprint?: string | null;
  diagnostic?: {
    controlCount?: number;
    matchingControlCount?: number;
    observedKinds?: Array<"slider" | "dropdown">;
  };
};

export class BrowserReasoningSelectionError extends Error {
  constructor(
    message: string,
    readonly evidence: BrowserReasoningSelectionEvidence,
  ) {
    super(message);
    this.name = "BrowserReasoningSelectionError";
  }
}

/**
 * A new conversation establishes its bounded model identity on turn zero.
 * Only explicit resume and later conversation turns require it to exist first;
 * retries within turn zero must still be allowed to capture it.
 */
export function shouldRequirePersistedOriginalModelIdentity(args: {
  isResumingConversation: boolean;
  turnIndex: number;
}): boolean {
  return args.isResumingConversation || args.turnIndex > 0;
}

/**
 * Strict browser-only reasoning gate. Unlike the legacy thinking-time helper,
 * every non-success outcome rejects before the prompt composer is submitted.
 */
export async function ensureBrowserReasoning(
  Runtime: ChromeClient["Runtime"],
  args: {
    intent: BrowserReasoningIntent;
    managedSlot?: BrowserManagedSlotCapability | null;
    originalModelIdentity?: BrowserModelIdentityEvidence | null;
    requireOriginalModelIdentity?: boolean;
  },
  logger: BrowserLogger,
): Promise<BrowserReasoningSelectionEvidence> {
  const capturedAt = new Date().toISOString();
  if (args.requireOriginalModelIdentity && !args.originalModelIdentity) {
    const evidence: BrowserReasoningSelectionEvidence = {
      requestedIntent: args.intent,
      controlKind: null,
      availableLevels: [],
      resolvedLevel: null,
      status: "original-model-missing",
      verified: false,
      modelUnchanged: false,
      originalModelIdentity: null,
      observedModelFingerprint: null,
      managedSlotId: args.managedSlot?.slotId,
      capturedAt,
      diagnostic: { controlCount: 0, matchingControlCount: 0, observedKinds: [] },
    };
    throw new BrowserReasoningSelectionError(
      "Browser reasoning selection failed before prompt submission: the resumed conversation has no persisted original model identity.",
      evidence,
    );
  }
  const outcome = await evaluateBrowserReasoningSelection(Runtime, args);
  const diagnostic = {
    controlCount: outcome?.diagnostic?.controlCount ?? 0,
    matchingControlCount: outcome?.diagnostic?.matchingControlCount ?? 0,
    observedKinds: outcome?.diagnostic?.observedKinds ?? [],
  };
  const originalModelIdentity =
    args.originalModelIdentity ??
    (outcome?.originalModelFingerprint
      ? {
          fingerprint: outcome.originalModelFingerprint,
          source: "chatgpt-model-picker" as const,
          capturedAt,
        }
      : null);
  const evidence: BrowserReasoningSelectionEvidence = {
    requestedIntent: args.intent,
    controlKind: outcome?.controlKind ?? null,
    availableLevels: outcome?.availableLevels ?? [],
    resolvedLevel: outcome?.resolvedLevel ?? null,
    status: outcome?.status ?? "unavailable",
    verified:
      (outcome?.status === "already-selected" || outcome?.status === "switched") &&
      outcome?.resolvedLevel === args.intent &&
      outcome?.modelUnchanged === true &&
      originalModelIdentity !== null &&
      outcome?.observedModelFingerprint === originalModelIdentity.fingerprint,
    modelUnchanged: outcome?.modelUnchanged === true,
    originalModelIdentity,
    observedModelFingerprint: outcome?.observedModelFingerprint ?? null,
    managedSlotId: args.managedSlot?.slotId,
    capturedAt,
    diagnostic,
  };
  logger(
    `[browser] Reasoning selection evidence: intent=${evidence.requestedIntent}; control=${evidence.controlKind ?? "unavailable"}; available=${evidence.availableLevels.join(",") || "none"}; resolved=${evidence.resolvedLevel ?? "none"}; verified=${evidence.verified ? "yes" : "no"}; modelUnchanged=${evidence.modelUnchanged ? "yes" : "no"}.`,
  );
  if (!evidence.verified) {
    throw new BrowserReasoningSelectionError(
      `Browser reasoning selection failed before prompt submission (requested ${args.intent}; status ${evidence.status}; control ${evidence.controlKind ?? "unavailable"}; available ${evidence.availableLevels.join(",") || "none"}; model unchanged ${evidence.modelUnchanged ? "yes" : "no"}).`,
      evidence,
    );
  }
  return evidence;
}

async function evaluateBrowserReasoningSelection(
  Runtime: ChromeClient["Runtime"],
  args: {
    intent: BrowserReasoningIntent;
    managedSlot?: BrowserManagedSlotCapability | null;
    originalModelIdentity?: BrowserModelIdentityEvidence | null;
  },
): Promise<BrowserReasoningOutcome | undefined> {
  const outcome = await Runtime.evaluate({
    expression: buildBrowserReasoningExpression(args),
    awaitPromise: true,
    returnByValue: true,
  });
  return outcome.result?.value as BrowserReasoningOutcome | undefined;
}

/**
 * Kept self-contained because it executes in the ChatGPT tab. It intentionally
 * records only recognised control labels and numeric/control metadata, never
 * composer or conversation text.
 */
function buildBrowserReasoningExpression(args: {
  intent: BrowserReasoningIntent;
  managedSlot?: BrowserManagedSlotCapability | null;
  originalModelIdentity?: BrowserModelIdentityEvidence | null;
}): string {
  const targetLiteral = JSON.stringify(args.intent);
  const expectedControlLiteral = JSON.stringify(args.managedSlot?.expectedControl ?? null);
  const maximumReasoningLiteral = JSON.stringify(args.managedSlot?.maximumReasoning ?? null);
  const originalModelFingerprintLiteral = JSON.stringify(
    args.originalModelIdentity?.fingerprint ?? null,
  );
  const modelButtonLiteral = JSON.stringify(MODEL_BUTTON_SELECTOR);
  return `(async () => {
    ${buildClickDispatcher()}
    const TARGET = ${targetLiteral};
    const EXPECTED_CONTROL = ${expectedControlLiteral};
    const MAXIMUM_REASONING = ${maximumReasoningLiteral};
    const ORIGINAL_MODEL_FINGERPRINT = ${originalModelFingerprintLiteral};
    const MODEL_BUTTON_SELECTOR = ${modelButtonLiteral};
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const normalize = (value) => String(value || '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, ' ')
      .replace(/\\s+/g, ' ')
      .trim();
    const ownedDisplayText = (node) => {
      const rendered = String(node?.innerText || '').trim();
      const fallback = String(node?.textContent || '').trim();
      return (rendered || fallback).slice(0, 256);
    };
    const ownedSemanticText = (node) =>
      ownedDisplayText(node) + ' ' + String(node?.getAttribute?.('aria-label') || '').slice(0, 256);
    const isVisible = (node) => {
      if (!node || node.getAttribute?.('aria-hidden') === 'true') return false;
      const rect = node.getBoundingClientRect?.();
      return !rect || (rect.width > 0 && rect.height > 0);
    };
    const selected = (node) => {
      const state = String(node?.getAttribute?.('data-state') || '').toLowerCase();
      return node?.getAttribute?.('aria-checked') === 'true' ||
        node?.getAttribute?.('aria-selected') === 'true' ||
        node?.getAttribute?.('aria-current') === 'true' ||
        node?.getAttribute?.('data-selected') === 'true' ||
        ['checked', 'selected', 'on', 'true'].includes(state);
    };
    const levelFor = (node) => {
      const text = normalize(
        ownedSemanticText(node) + ' ' +
        String(node?.getAttribute?.('aria-valuetext') || '').slice(0, 256),
      );
      if (!text || text.includes('gpt ')) return null;
      const words = text.split(' ');
      if (words.includes('pro')) return 'pro';
      if ((words.includes('extra') && words.includes('high')) || words.includes('heavy')) return 'heavy';
      if (words.includes('high') || words.includes('extended')) return 'high';
      if (words.includes('standard') || words.includes('medium')) return 'standard';
      if (words.includes('light') || words.includes('instant')) return 'light';
      return null;
    };
    // Model identity must not be derived from a reasoning pill: ChatGPT can
    // change that pill from Standard to Pro without changing the base model.
    // The authenticated intelligence picker exposes the active model as a
    // distinct version-bearing menuitem inside the same owned container as the
    // effort control. Keep identity scoped to that owner: the closed composer
    // pill is reasoning-only, while the wider model catalog is not proof of the
    // current selection.
    const canonicalModelSignal = (value) => {
      const normalized = normalize(value);
      const version = normalized.match(/(?:^| )(?:gpt )?(\\d+) (\\d+)(?: |$)/);
      if (!version) return null;
      const words = normalized.split(' ');
      const variant = words.includes('sol') ? ' sol' : words.includes('instant') ? ' instant' : '';
      return 'gpt ' + version[1] + ' ' + version[2] + variant;
    };
    const isReasoningIdentityNode = (node) => {
      const role = normalize(node?.getAttribute?.('role'));
      if (role === 'slider') return true;
      const attributes = normalize([
        node?.getAttribute?.('data-testid'),
        node?.getAttribute?.('aria-label'),
        node?.getAttribute?.('data-model-picker-thinking-effort-action'),
        node?.getAttribute?.('data-composer-intelligence-pro-effort-action'),
      ].filter(Boolean).join(' '));
      const text = normalize(ownedDisplayText(node));
      const words = new Set((attributes + ' ' + text).trim().split(' ').filter(Boolean));
      return (
        words.has('effort') ||
        words.has('reasoning') ||
        words.has('intelligence') ||
        words.has('standard') ||
        words.has('medium') ||
        words.has('high') ||
        words.has('heavy') ||
        words.has('light') ||
        words.has('extended') ||
        words.has('pro')
      );
    };
    const fingerprintForSignals = (signals) => {
      const source = Array.from(new Set(signals.filter(Boolean))).sort().join('|');
      if (!source) return null;
      let hash = 2166136261;
      for (let index = 0; index < source.length; index += 1) {
        hash ^= source.charCodeAt(index);
        hash = Math.imul(hash, 16777619);
      }
      return String(hash >>> 0);
    };
    const stableModelFingerprint = (owner) => {
      if (!owner) return null;
      const ownedModelSignals = Array.from(owner.querySelectorAll?.('[role="menuitem"]') || [])
        .slice(0, 24)
        .filter(isVisible)
        .filter((node) => !isReasoningIdentityNode(node))
        .map((node) => canonicalModelSignal(ownedSemanticText(node)))
        .filter(Boolean);
      const uniqueOwnedModelSignals = Array.from(new Set(ownedModelSignals));
      return uniqueOwnedModelSignals.length === 1
        ? fingerprintForSignals(uniqueOwnedModelSignals)
        : null;
    };
    const diagnostic = (controlCount, matchingControlCount, observedKinds) => ({
      controlCount,
      matchingControlCount,
      observedKinds: Array.from(new Set(observedKinds)),
    });
    let originalModelFingerprint = ORIGINAL_MODEL_FINGERPRINT;
    let observedModelFingerprint = null;
    const fail = (status, details) => ({
      status,
      controlKind: details.controlKind || null,
      availableLevels: details.availableLevels || [],
      resolvedLevel: details.resolvedLevel || null,
      modelUnchanged: details.modelUnchanged === true,
      originalModelFingerprint: details.originalModelFingerprint ?? originalModelFingerprint,
      observedModelFingerprint: details.observedModelFingerprint ?? observedModelFingerprint,
      diagnostic: diagnostic(details.controlCount || 0, details.matchingControlCount || 0, details.observedKinds || []),
    });
    const REASONING_OWNER_SELECTOR = [
      '[data-testid="composer-intelligence-picker-content"]',
      '[data-testid*="intelligence-picker-content"]',
      '[data-testid*="thinking-effort"][data-testid]:not([aria-controls])',
      '[data-testid*="reasoning"][data-testid]:not([aria-controls])',
    ].join(', ');
    const REASONING_TRIGGER_SELECTOR = [
      '[data-testid*="intelligence"][aria-controls]',
      '[data-testid*="thinking"][aria-controls]',
      '[data-testid*="reasoning"][aria-controls]',
      '[aria-label*="thinking"][aria-controls]',
      '[aria-label*="reasoning"][aria-controls]',
    ].join(', ');
    const ownerFromDedicatedTrigger = (trigger) => {
      const id = trigger?.getAttribute?.('aria-controls') || trigger?.getAttribute?.('aria-labelledby');
      const owner = id ? document.getElementById?.(id) : null;
      return owner && isVisible(owner) ? owner : null;
    };
    const reasoningOwners = () => {
      const owners = [
        ...Array.from(document.querySelectorAll(REASONING_OWNER_SELECTOR)),
        ...Array.from(document.querySelectorAll(REASONING_TRIGGER_SELECTOR)).map(ownerFromDedicatedTrigger),
      ].filter((node, index, nodes) => node && isVisible(node) && nodes.indexOf(node) === index);
      return owners;
    };
    const readNumericSliderMetrics = (node) => {
      const min = Number(node?.min ?? node?.getAttribute?.('aria-valuemin'));
      const max = Number(node?.max ?? node?.getAttribute?.('aria-valuemax'));
      const now = Number(node?.value ?? node?.getAttribute?.('aria-valuenow'));
      if (
        !Number.isFinite(min) ||
        !Number.isFinite(max) ||
        !Number.isFinite(now) ||
        !Number.isInteger(min) ||
        !Number.isInteger(max) ||
        !Number.isInteger(now) ||
        max <= min ||
        now < min ||
        now > max ||
        max - min > 20
      ) return null;
      return { min, max, now };
    };
    const ownedCompositeSlider = (ownerNode) => {
      if (!ownerNode || !isVisible(ownerNode)) return null;
      if (ownerNode.getAttribute?.('role') !== 'menuitem') return null;
      if (ownerNode.getAttribute?.('tabindex') !== '0') return null;
      if (normalize(ownerNode.getAttribute?.('data-orientation')) !== 'vertical') return null;
      const shortcuts = new Set(normalize(ownerNode.getAttribute?.('aria-keyshortcuts')).split(' ').filter(Boolean));
      if (!shortcuts.has('arrowleft') || !shortcuts.has('arrowright')) return null;
      const readbacks = Array.from(ownerNode.querySelectorAll?.('[role="slider"]') || []);
      if (readbacks.length !== 1) return null;
      const readback = readbacks[0];
      if (readback.getAttribute?.('aria-hidden') !== 'true') return null;
      if (readback.getAttribute?.('tabindex') !== '-1') return null;
      if (!readNumericSliderMetrics(readback)) return null;
      return { interactionNode: ownerNode, readbackNode: readback, composite: true };
    };
    const controlsWithinOwner = (owner) => {
      if (!owner) return { sliders: [], dropdownItems: [] };
      const nodes = [
        owner,
        ...Array.from(owner.querySelectorAll?.('input[type="range"], [role="slider"], [role="option"], [role="menuitemradio"], [role="radio"]') || []),
      ].filter((node, index, values) => node && isVisible(node) && values.indexOf(node) === index);
      const directSliders = nodes
        .filter((node) => node?.matches?.('input[type="range"], [role="slider"]') || node?.getAttribute?.('role') === 'slider')
        .map((node) => ({ interactionNode: node, readbackNode: node, composite: false }));
      const compositeSliders = Array.from(owner.querySelectorAll?.('[role="menuitem"]') || [])
        .map(ownedCompositeSlider)
        .filter(Boolean);
      return {
        sliders: [...directSliders, ...compositeSliders],
        dropdownItems: nodes.filter((node) => {
          const role = node?.getAttribute?.('role');
          return (role === 'option' || role === 'menuitemradio' || role === 'radio') && levelFor(node) !== null;
        }),
      };
    };
    const effortLevelWithinOwner = (owner) => {
      if (!owner) return null;
      const candidates = Array.from(owner.querySelectorAll?.('[role="menuitem"]') || [])
        .filter(isVisible)
        .filter((node) => {
          const words = new Set(normalize(ownedSemanticText(node)).split(' ').filter(Boolean));
          return words.has('effort') || words.has('reasoning') || words.has('intelligence');
        });
      const levels = candidates
        .map((node) => {
          const words = normalize(ownedSemanticText(node)).split(' ');
          if (words.includes('pro')) return 'pro';
          if ((words.includes('extra') && words.includes('high')) || words.includes('heavy')) return 'heavy';
          if (words.includes('high') || words.includes('extended')) return 'high';
          if (words.includes('standard') || words.includes('medium')) return 'standard';
          if (words.includes('light')) return 'light';
          return null;
        })
        .filter(Boolean);
      const uniqueLevels = Array.from(new Set(levels));
      return uniqueLevels.length === 1 ? uniqueLevels[0] : null;
    };
    const dispatchArrow = (node, key) => {
      const KeyboardEventCtor = window?.KeyboardEvent || window?.Event;
      if (!node || typeof KeyboardEventCtor !== 'function') return false;
      const keyCode = key === 'ArrowLeft' ? 37 : 39;
      try { node.focus?.(); } catch {}
      try {
        node.dispatchEvent(new KeyboardEventCtor('keydown', {
          key, code: key, keyCode, which: keyCode,
          bubbles: true, cancelable: true,
        }));
        node.dispatchEvent(new KeyboardEventCtor('keyup', {
          key, code: key, keyCode, which: keyCode,
          bubbles: true, cancelable: true,
        }));
        return true;
      } catch {
        return false;
      }
    };
    const discoverControls = () => {
      const owners = reasoningOwners();
      // A bare model-menu row is deliberately not an owner and therefore
      // cannot become a Pro reasoning option by text matching alone.
      if (owners.length !== 1) return { owner: null, ownerCount: owners.length, sliders: [], dropdownItems: [] };
      return { owner: owners[0], ownerCount: 1, ...controlsWithinOwner(owners[0]) };
    };
    const controlMatchesExpectation = (controls) => {
      if (!controls.owner) return false;
      if (EXPECTED_CONTROL === 'slider') return controls.sliders.length > 0;
      if (EXPECTED_CONTROL === 'dropdown') return controls.dropdownItems.length > 0;
      return controls.sliders.length > 0 || controls.dropdownItems.length > 0;
    };
    const openReasoningControl = async () => {
      const modelButton = document.querySelector(MODEL_BUTTON_SELECTOR);
      const dedicatedTriggers = () => Array.from(document.querySelectorAll(REASONING_TRIGGER_SELECTOR))
        .filter(isVisible);
      // First open the canonical model/composer button. Its menu may expose a
      // nested dedicated reasoning trigger, but its model rows are never used
      // as reasoning controls.
      if (modelButton && isVisible(modelButton) && modelButton.getAttribute?.('aria-expanded') !== 'true') {
        dispatchClickSequence(modelButton);
      }
      const deadline = Date.now() + 2_500;
      let clickedDedicatedTrigger = false;
      while (Date.now() < deadline) {
        const controls = discoverControls();
        if (controlMatchesExpectation(controls)) return true;
        const triggers = dedicatedTriggers();
        if (!clickedDedicatedTrigger && triggers.length === 1) {
          const trigger = triggers[0];
          if (trigger.getAttribute?.('aria-expanded') !== 'true') dispatchClickSequence(trigger);
          clickedDedicatedTrigger = true;
        } else if (!modelButton && triggers.length > 1) {
          return false;
        }
        await sleep(100);
      }
      return false;
    };
    const LEVEL_RANK = { light: 0, standard: 1, high: 2, heavy: 3, pro: 4 };
    const sliderLevel = (control, owner) =>
      levelFor(control?.readbackNode) || effortLevelWithinOwner(owner);
    const sliderAtMaximum = (node) => {
      const max = node?.max || node?.getAttribute?.('aria-valuemax');
      const now = node?.value || node?.getAttribute?.('aria-valuenow');
      return max != null && max !== '' && now != null && now !== '' && String(now) === String(max);
    };
    let controls = discoverControls();
    if (!controlMatchesExpectation(controls)) {
      await openReasoningControl();
      controls = discoverControls();
    }
    observedModelFingerprint = stableModelFingerprint(controls.owner);
    originalModelFingerprint = originalModelFingerprint || observedModelFingerprint;
    if (!originalModelFingerprint || observedModelFingerprint !== originalModelFingerprint) {
      return fail('model-mismatch', {
        modelUnchanged: false,
        originalModelFingerprint,
        observedModelFingerprint,
        controlCount: 0,
        matchingControlCount: 0,
        observedKinds: [],
      });
    }
    const modelStill = () => {
      const refreshedIdentityControls = discoverControls();
      observedModelFingerprint = stableModelFingerprint(refreshedIdentityControls.owner);
      return observedModelFingerprint !== null && observedModelFingerprint === originalModelFingerprint;
    };
    if (controls.ownerCount !== 1) {
      return fail(controls.ownerCount > 1 ? 'ambiguous' : 'unavailable', {
        controlKind: null,
        controlCount: 0,
        matchingControlCount: 0,
        observedKinds: [],
      });
    }
    const { sliders, dropdownItems } = controls;
    const observedKinds = [
      ...(sliders.length ? ['slider'] : []),
      ...(dropdownItems.length ? ['dropdown'] : []),
    ];
    if (EXPECTED_CONTROL === 'slider' && (sliders.length !== 1 || dropdownItems.length > 0)) {
      return fail(sliders.length === 0 ? 'unavailable' : 'ambiguous', {
        controlKind: sliders.length > 0 ? 'slider' : null,
        controlCount: sliders.length + dropdownItems.length,
        matchingControlCount: sliders.length,
        observedKinds,
      });
    }
    if (EXPECTED_CONTROL === 'dropdown' && (dropdownItems.length === 0 || sliders.length > 0)) {
      return fail(dropdownItems.length === 0 ? 'unavailable' : 'ambiguous', {
        controlKind: dropdownItems.length > 0 ? 'dropdown' : null,
        controlCount: sliders.length + dropdownItems.length,
        matchingControlCount: dropdownItems.length,
        observedKinds,
      });
    }
    if (!EXPECTED_CONTROL && sliders.length + (dropdownItems.length ? 1 : 0) !== 1) {
      return fail('ambiguous', {
        controlKind: sliders.length === 1 ? 'slider' : (dropdownItems.length ? 'dropdown' : null),
        controlCount: sliders.length + dropdownItems.length,
        matchingControlCount: 0,
        observedKinds,
      });
    }
    if ((EXPECTED_CONTROL === 'slider' || (!EXPECTED_CONTROL && sliders.length === 1)) && sliders.length === 1) {
      const initialSliderControl = sliders[0];
      const initialSlider = initialSliderControl.readbackNode;
      const initialMetrics = initialSliderControl.composite
        ? readNumericSliderMetrics(initialSlider)
        : null;
      if (initialSliderControl.composite && !initialMetrics) {
        return fail('unavailable', {
          controlKind: 'slider', controlCount: sliders.length + dropdownItems.length,
          matchingControlCount: 0, observedKinds,
        });
      }
      const initialLevel = sliderLevel(initialSliderControl, controls.owner);
      let observedEffortLabel = initialLevel !== null;
      const initialAtMaximum = sliderAtMaximum(initialSlider);
      const canUseProMaximumFallback =
        TARGET === 'pro' && MAXIMUM_REASONING === 'pro' && !observedEffortLabel && initialAtMaximum;
      const availableLevels = initialLevel ? [initialLevel] : [];
      if (!initialLevel && !canUseProMaximumFallback) {
        return fail('unavailable', {
          controlKind: 'slider', availableLevels, modelUnchanged: true,
          controlCount: sliders.length + dropdownItems.length,
          matchingControlCount: 1, observedKinds,
        });
      }
      if (initialLevel === TARGET || canUseProMaximumFallback) {
        return {
          status: 'already-selected',
          controlKind: 'slider', availableLevels: canUseProMaximumFallback ? ['pro'] : availableLevels,
          resolvedLevel: TARGET,
          modelUnchanged: true,
          originalModelFingerprint,
          observedModelFingerprint,
          diagnostic: diagnostic(1, 1, ['slider']),
        };
      }

      let currentLevel = initialLevel;
      const maxSteps = Math.max(5, (initialMetrics?.max ?? 0) - (initialMetrics?.min ?? 0) + 2);
      for (let step = 0; step < maxSteps; step += 1) {
        const liveControls = discoverControls();
        const liveKinds = [
          ...(liveControls.sliders.length ? ['slider'] : []),
          ...(liveControls.dropdownItems.length ? ['dropdown'] : []),
        ];
        if (
          liveControls.ownerCount !== 1 ||
          !liveControls.owner ||
          liveControls.sliders.length !== 1 ||
          liveControls.dropdownItems.length > 0
        ) {
          return fail(
            liveControls.ownerCount > 1 || liveControls.sliders.length > 1 || liveControls.dropdownItems.length > 0
              ? 'ambiguous'
              : 'unavailable',
            {
              controlKind: liveControls.sliders.length ? 'slider' : null,
              controlCount: liveControls.sliders.length + liveControls.dropdownItems.length,
              matchingControlCount: liveControls.sliders.length,
              observedKinds: liveKinds,
            },
          );
        }
        const liveControl = liveControls.sliders[0];
        const liveLevel = sliderLevel(liveControl, liveControls.owner);
        if (liveLevel) observedEffortLabel = true;
        const liveAtMaximum = sliderAtMaximum(liveControl.readbackNode);
        observedModelFingerprint = stableModelFingerprint(liveControls.owner);
        if (observedModelFingerprint !== originalModelFingerprint) {
          return fail('model-changed', {
            controlKind: 'slider', modelUnchanged: false,
            controlCount: 1, matchingControlCount: 1, observedKinds: liveKinds,
          });
        }
        if (!liveLevel || !(liveLevel in LEVEL_RANK)) {
          if (TARGET === 'pro' && MAXIMUM_REASONING === 'pro' && !observedEffortLabel && liveAtMaximum) {
            return {
              status: 'switched', controlKind: 'slider', availableLevels: ['pro'], resolvedLevel: 'pro',
              modelUnchanged: true, originalModelFingerprint, observedModelFingerprint,
              diagnostic: diagnostic(1, 1, ['slider']),
            };
          }
          return fail('unavailable', {
            controlKind: 'slider', availableLevels: [], resolvedLevel: null,
            modelUnchanged: true, controlCount: 1, matchingControlCount: 1, observedKinds: liveKinds,
          });
        }
        currentLevel = liveLevel;
        if (currentLevel === TARGET) {
          return {
            status: 'switched', controlKind: 'slider', availableLevels: [TARGET], resolvedLevel: TARGET,
            modelUnchanged: true, originalModelFingerprint, observedModelFingerprint,
            diagnostic: diagnostic(1, 1, ['slider']),
          };
        }
        const direction = LEVEL_RANK[TARGET] > LEVEL_RANK[currentLevel] ? 'ArrowRight' : 'ArrowLeft';
        if (!dispatchArrow(liveControl.interactionNode, direction)) {
          return fail('unavailable', {
            controlKind: 'slider', availableLevels: [currentLevel], resolvedLevel: currentLevel,
            modelUnchanged: true, controlCount: 1, matchingControlCount: 1, observedKinds: liveKinds,
          });
        }
        const stepDeadline = Date.now() + 2_500;
        let progressed = false;
        while (Date.now() < stepDeadline) {
          await sleep(100);
          const refreshedControls = discoverControls();
          const refreshedKinds = [
            ...(refreshedControls.sliders.length ? ['slider'] : []),
            ...(refreshedControls.dropdownItems.length ? ['dropdown'] : []),
          ];
          if (
            refreshedControls.ownerCount !== 1 ||
            !refreshedControls.owner ||
            refreshedControls.sliders.length !== 1 ||
            refreshedControls.dropdownItems.length > 0
          ) {
            return fail('unavailable', {
              controlKind: 'slider', availableLevels: currentLevel ? [currentLevel] : [],
              resolvedLevel: currentLevel || null, modelUnchanged: true,
              controlCount: refreshedControls.sliders.length + refreshedControls.dropdownItems.length,
              matchingControlCount: refreshedControls.sliders.length, observedKinds: refreshedKinds,
            });
          }
          const refreshedControl = refreshedControls.sliders[0];
          const refreshedLevel = sliderLevel(refreshedControl, refreshedControls.owner);
          if (refreshedLevel) observedEffortLabel = true;
          const refreshedAtMaximum = sliderAtMaximum(refreshedControl.readbackNode);
          observedModelFingerprint = stableModelFingerprint(refreshedControls.owner);
          if (observedModelFingerprint !== originalModelFingerprint) {
            return fail('model-changed', {
              controlKind: 'slider', modelUnchanged: false,
              controlCount: 1, matchingControlCount: 1, observedKinds: refreshedKinds,
            });
          }
          if (!refreshedLevel || !(refreshedLevel in LEVEL_RANK)) {
            if (
              TARGET === 'pro' &&
              MAXIMUM_REASONING === 'pro' &&
              !observedEffortLabel &&
              refreshedAtMaximum
            ) {
              return {
                status: 'switched', controlKind: 'slider', availableLevels: ['pro'], resolvedLevel: 'pro',
                modelUnchanged: true, originalModelFingerprint, observedModelFingerprint,
                diagnostic: diagnostic(1, 1, ['slider']),
              };
            }
            continue;
          }
          if (refreshedLevel === TARGET) {
            return {
              status: 'switched', controlKind: 'slider', availableLevels: [TARGET], resolvedLevel: TARGET,
              modelUnchanged: true, originalModelFingerprint, observedModelFingerprint,
              diagnostic: diagnostic(1, 1, ['slider']),
            };
          }
          if (refreshedLevel === currentLevel) {
            continue;
          }
          const previousRank = LEVEL_RANK[currentLevel];
          const refreshedRank = LEVEL_RANK[refreshedLevel];
          const targetRank = LEVEL_RANK[TARGET];
          const movedTowardTarget = direction === 'ArrowRight'
            ? refreshedRank > previousRank && refreshedRank < targetRank
            : refreshedRank < previousRank && refreshedRank > targetRank;
          if (movedTowardTarget) {
            currentLevel = refreshedLevel;
            progressed = true;
            break;
          }
          return fail('unavailable', {
            controlKind: 'slider', availableLevels: [refreshedLevel], resolvedLevel: refreshedLevel,
            modelUnchanged: true, controlCount: 1, matchingControlCount: 1, observedKinds: refreshedKinds,
          });
        }
        if (!progressed) {
          return fail('unavailable', {
            controlKind: 'slider', availableLevels: currentLevel ? [currentLevel] : [],
            resolvedLevel: currentLevel || null, modelUnchanged: true,
            controlCount: 1, matchingControlCount: 1, observedKinds: ['slider'],
          });
        }
      }
      return fail('unavailable', {
        controlKind: 'slider', availableLevels: currentLevel ? [currentLevel] : [],
        resolvedLevel: currentLevel || null, modelUnchanged: true,
        controlCount: 1, matchingControlCount: 1, observedKinds: ['slider'],
      });
    }
    const availableLevels = Array.from(new Set(dropdownItems.map(levelFor).filter(Boolean)));
    const matches = dropdownItems.filter((node) => levelFor(node) === TARGET);
    if (matches.length !== 1) {
      return fail(matches.length > 1 ? 'ambiguous' : 'unavailable', {
        controlKind: 'dropdown', availableLevels, resolvedLevel: null,
        modelUnchanged: modelStill(),
        controlCount: sliders.length + dropdownItems.length,
        matchingControlCount: matches.length, observedKinds,
      });
    }
    const target = matches[0];
    const wasSelected = selected(target);
    if (!wasSelected) {
      dispatchClickSequence(target);
      await sleep(150);
    }
    const refreshedControls = discoverControls();
    const refreshed = refreshedControls.owner
      ? refreshedControls.dropdownItems.filter((node) => levelFor(node) === TARGET)
      : [];
    const verifiedTarget = refreshed.length === 1 && selected(refreshed[0]);
    const modelUnchanged = modelStill();
    if (!modelUnchanged) {
      return fail('model-changed', {
        controlKind: 'dropdown', availableLevels, resolvedLevel: verifiedTarget ? TARGET : null,
        modelUnchanged: false, controlCount: sliders.length + dropdownItems.length,
        matchingControlCount: refreshed.length, observedKinds,
      });
    }
    if (!verifiedTarget) {
      return fail('unavailable', {
        controlKind: 'dropdown', availableLevels, resolvedLevel: null,
        modelUnchanged: true, controlCount: sliders.length + dropdownItems.length,
        matchingControlCount: refreshed.length, observedKinds,
      });
    }
    return {
      status: wasSelected ? 'already-selected' : 'switched',
      controlKind: 'dropdown', availableLevels, resolvedLevel: TARGET,
      modelUnchanged: true,
      originalModelFingerprint,
      observedModelFingerprint,
      diagnostic: diagnostic(sliders.length + dropdownItems.length, refreshed.length, observedKinds),
    };
  })()`;
}

export function buildBrowserReasoningExpressionForTest(args: {
  intent: BrowserReasoningIntent;
  managedSlot?: BrowserManagedSlotCapability | null;
  originalModelIdentity?: BrowserModelIdentityEvidence | null;
}): string {
  return buildBrowserReasoningExpression(args);
}

function formatBrowserThinkingLog(message: string): string {
  return `${BROWSER_THINKING_LOG_PREFIX} ${message.replace(/^Thinking time:\s*/, "")}`;
}

/**
 * Surfaces the model-picker snapshot captured alongside a failed detection.
 *
 * The browser prefix routes this through the session runner's non-verbose
 * always-print path. The injected probe bounds and redacts all text values.
 */
function logPickerDiagnostic(result: ThinkingTimeOutcome | undefined, logger: BrowserLogger): void {
  const diagnostic =
    result && "diagnostic" in result
      ? (result.diagnostic as ThinkingTimePickerDiagnostic | undefined)
      : undefined;
  if (!diagnostic) {
    return;
  }
  logger(`[browser] Model picker diagnostic: ${JSON.stringify(diagnostic)}`);
}

/**
 * Selects a thinking-time level in ChatGPT's composer.
 *
 * Missing controls remain best-effort except Pro Extended, which fails closed
 * unless the selected option is confirmed.
 */
export async function ensureThinkingTime(
  Runtime: ChromeClient["Runtime"],
  level: ThinkingTimeLevel,
  logger: BrowserLogger,
  desiredModel?: string | null,
) {
  const result = await evaluateThinkingTimeSelection(Runtime, level, desiredModel);
  const capitalizedLevel = level.charAt(0).toUpperCase() + level.slice(1);
  const targetModelKind = inferThinkingTargetModelKind(desiredModel);
  const observedModelKind = result && "modelKind" in result ? result.modelKind : null;
  const strictProEffort =
    (targetModelKind === "pro" || observedModelKind === "pro") && level === "extended";

  switch (result?.status) {
    case "already-selected":
      logger(formatBrowserThinkingLog(`${result.label ?? capitalizedLevel} (already selected)`));
      return;
    case "switched":
      logger(formatBrowserThinkingLog(result.label ?? capitalizedLevel));
      return;
    case "chip-not-found":
    case "menu-not-found":
    case "option-not-found":
    case "selection-unverified":
    case "model-kind-not-found": {
      await logDomFailure(Runtime, logger, `thinking-${result.status}`);
      logPickerDiagnostic(result, logger);
      const kindHint =
        result.status === "model-kind-not-found" && result.modelKind
          ? ` for ${result.modelKind}`
          : targetModelKind
            ? ` for ${targetModelKind}`
            : "";
      const message = `Thinking time: ${result.status.replaceAll("-", " ")}${kindHint} (requested ${capitalizedLevel})`;
      if (strictProEffort) {
        throw new Error(`${message}; refusing to submit without confirmed Pro Extended.`);
      }
      logger(formatBrowserThinkingLog(`${message}; continuing with ChatGPT default.`));
      return;
    }
    default: {
      await logDomFailure(Runtime, logger, "thinking-time-unknown");
      logPickerDiagnostic(result, logger);
      if (strictProEffort) {
        throw new Error(
          `Thinking time: unknown outcome selecting ${capitalizedLevel}; refusing to submit without confirmed Pro Extended.`,
        );
      }
      logger(
        formatBrowserThinkingLog(
          `unknown outcome selecting ${capitalizedLevel}; continuing with ChatGPT default.`,
        ),
      );
      return;
    }
  }
}

/**
 * Best-effort selection of a thinking time level in ChatGPT's composer pill menu.
 * Safe by default: if the pill/menu/option isn't present, we continue without throwing.
 * @param level - The thinking time intensity: 'light', 'standard', 'extended', or 'heavy'
 */
export async function ensureThinkingTimeIfAvailable(
  Runtime: ChromeClient["Runtime"],
  level: ThinkingTimeLevel,
  logger: BrowserLogger,
  desiredModel?: string | null,
): Promise<boolean> {
  try {
    const result = await evaluateThinkingTimeSelection(Runtime, level, desiredModel);
    const capitalizedLevel = level.charAt(0).toUpperCase() + level.slice(1);

    switch (result?.status) {
      case "already-selected":
        logger(formatBrowserThinkingLog(`${result.label ?? capitalizedLevel} (already selected)`));
        return true;
      case "switched":
        logger(formatBrowserThinkingLog(result.label ?? capitalizedLevel));
        return true;
      case "chip-not-found":
      case "menu-not-found":
      case "option-not-found":
      case "selection-unverified":
      case "model-kind-not-found":
        if (logger.verbose) {
          logger(
            formatBrowserThinkingLog(
              `${result.status.replaceAll("-", " ")}; continuing with default.`,
            ),
          );
        }
        return false;
      default:
        if (logger.verbose) {
          logger(formatBrowserThinkingLog("unknown outcome; continuing with default."));
        }
        return false;
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    if (logger.verbose) {
      logger(formatBrowserThinkingLog(`selection failed (${message}); continuing with default.`));
      await logDomFailure(Runtime, logger, "thinking-time");
    }
    return false;
  }
}

async function evaluateThinkingTimeSelection(
  Runtime: ChromeClient["Runtime"],
  level: ThinkingTimeLevel,
  desiredModel?: string | null,
): Promise<ThinkingTimeOutcome | undefined> {
  const outcome = await Runtime.evaluate({
    expression: buildThinkingTimeExpression(level, desiredModel),
    awaitPromise: true,
    returnByValue: true,
  });

  return outcome.result?.value as ThinkingTimeOutcome | undefined;
}

function buildThinkingTimeExpression(
  level: ThinkingTimeLevel,
  desiredModel?: string | null,
): string {
  const menuContainerLiteral = JSON.stringify(MENU_CONTAINER_SELECTOR);
  const menuItemLiteral = JSON.stringify(MENU_ITEM_SELECTOR);
  const modelButtonLiteral = JSON.stringify(MODEL_BUTTON_SELECTOR);
  const targetLevelLiteral = JSON.stringify(level.toLowerCase());
  const targetModelKindLiteral = JSON.stringify(inferThinkingTargetModelKind(desiredModel));
  const targetIsGpt56ModelLiteral = JSON.stringify(
    /(?:^|[^0-9])5[._ -]6(?:[^0-9]|$)/i.test(desiredModel ?? ""),
  );

  return `(async () => {
    ${buildClickDispatcher()}

    const MENU_CONTAINER_SELECTOR = ${menuContainerLiteral};
    const MENU_ITEM_SELECTOR = ${menuItemLiteral};
    const MODEL_BUTTON_SELECTOR = ${modelButtonLiteral};
    const TARGET_LEVEL = ${targetLevelLiteral};
    const TARGET_MODEL_KIND = ${targetModelKindLiteral};
    const TARGET_IS_GPT56_MODEL = ${targetIsGpt56ModelLiteral};

    // Bilingual matchers: English level token + observed Chinese variants.
    const LEVEL_TOKENS = {
      light: ['light', 'instant', '轻', '极速'],
      standard: ['standard', 'medium', '标准', '中'],
      extended: ['extended', 'high', '扩展', '深度', '加强', '高'],
      heavy: ['heavy', 'extra high', '重度', '加重', '极高'],
    };
    const targetTokens = LEVEL_TOKENS[TARGET_LEVEL] || [TARGET_LEVEL];

    const INITIAL_WAIT_MS = 150;
    const STEP_WAIT_MS = 200;
    const MAX_WAIT_MS = 8000;
    // The "Intelligence" menu renders right after opening the composer pill, so
    // a short probe is enough; if it's absent this is an older UI and we fall
    // back to the legacy paths without paying the full MAX_WAIT_MS.
    const INTELLIGENCE_WAIT_MS = 2500;

    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    // Keep CJK characters so we can match Chinese labels against LEVEL_TOKENS.
    const normalize = (value) => (value || '')
      .toLowerCase()
      .replace(/[^a-z0-9\\u4e00-\\u9fa5]+/g, ' ')
      .replace(/\\s+/g, ' ')
      .trim();
    const hasToken = (text, token) => normalize(text).split(' ').includes(token);
    const matchesLevel = (text) => {
      const t = normalize(text);
      if (!t) return false;
      return targetTokens.some((tok) => {
        const token = normalize(tok);
        if (!token) return false;
        if (token === 'high') return hasToken(t, 'high') && !hasToken(t, 'extra');
        if (token === 'extra high') return hasToken(t, 'extra') && hasToken(t, 'high');
        if (token === '极速') {
          const suffix = t.slice(token.length);
          return t === token || hasToken(t, token) || /^[0-9]/.test(suffix);
        }
        if (['中', '高', '极高'].includes(token)) {
          return t === token || hasToken(t, token);
        }
        return t === token || hasToken(t, token) || t.includes(token);
      });
    };
    const matchesAnyEffortLevel = (text) => {
      const normalizedText = normalize(text);
      if (!normalizedText) return false;
      for (const tokens of Object.values(LEVEL_TOKENS)) {
        for (const rawToken of tokens) {
          const token = normalize(rawToken);
          if (!token) continue;
          if (token.includes(' ')) {
            if (token.split(' ').every((part) => hasToken(normalizedText, part))) return true;
          } else if (/^[a-z0-9]+$/.test(token)) {
            if (hasToken(normalizedText, token)) return true;
          } else if (normalizedText.includes(token)) {
            return true;
          }
        }
      }
      return false;
    };
    const optionIsSelected = (node) => {
      if (!(node instanceof HTMLElement)) return false;
      const ariaChecked = node.getAttribute('aria-checked');
      const ariaSelected = node.getAttribute('aria-selected');
      const ariaCurrent = node.getAttribute('aria-current');
      const dataSelected = node.getAttribute('data-selected');
      const dataState = (node.getAttribute('data-state') || '').toLowerCase();
      if (ariaChecked === 'true' || ariaSelected === 'true' || ariaCurrent === 'true') return true;
      return (
        dataSelected === 'true' ||
        dataState === 'checked' ||
        dataState === 'selected' ||
        dataState === 'on' ||
        dataState === 'true'
      );
    };
    const closeOpenMenus = () => {
      try {
        document.dispatchEvent(
          new KeyboardEvent('keydown', { key: 'Escape', code: 'Escape', keyCode: 27, which: 27, bubbles: true }),
        );
      } catch {}
    };
    const dispatchHoverSequence = (target) => {
      if (!target || !(target instanceof EventTarget)) return false;
      const types = ['pointerover', 'pointerenter', 'mouseover', 'mouseenter', 'pointermove', 'mousemove'];
      for (const type of types) {
        try {
          const common = { bubbles: true, cancelable: true, view: window };
          const event =
            type.startsWith('pointer') && 'PointerEvent' in window
              ? new PointerEvent(type, { ...common, pointerId: 1, pointerType: 'mouse' })
              : new MouseEvent(type, common);
          target.dispatchEvent(event);
        } catch {}
      }
      try {
        target.focus?.();
      } catch {}
      return true;
    };

    const TRAILING_SELECTOR = '[data-model-picker-thinking-effort-action="true"]';
    const INTELLIGENCE_MENU_SELECTOR = '[data-testid="composer-intelligence-picker-content"]';
    const PRO_EFFORT_TRIGGER_SELECTOR = '[data-testid="composer-intelligence-pro-thinking-effort-trigger"]';

    const findModelButton = () => document.querySelector(MODEL_BUTTON_SELECTOR);
    const findTrailingButtons = () => Array.from(document.querySelectorAll(TRAILING_SELECTOR));
    const KIND_NOT_FOUND = { kindNotFound: true };

    const isVisible = (node) => {
      if (!node || node.getAttribute?.('aria-hidden') === 'true') return false;
      const rect = node.getBoundingClientRect?.();
      return Boolean(rect && rect.width > 0 && rect.height > 0);
    };
    const redactDiagnosticText = (value, maxLength = 120) =>
      String(value ?? '')
        .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}/gi, '[redacted-email]')
        .replace(/\\b[A-Za-z0-9_-]{32,}\\b/g, '[redacted]')
        .replace(/\\s+/g, ' ')
        .trim()
        .slice(0, maxLength);
    const describeNode = (el) => {
      if (!el || typeof el.getAttribute !== 'function') return null;
      let rect = null;
      try {
        const r = el.getBoundingClientRect?.();
        if (r) {
          rect = {
            w: Math.round(r.width),
            h: Math.round(r.height),
            visible: r.width > 0 && r.height > 0,
          };
        }
      } catch {}
      return {
        tag: el.tagName || null,
        testid: el.getAttribute('data-testid'),
        role: el.getAttribute('role'),
        ariaLabel: redactDiagnosticText(el.getAttribute('aria-label')),
        ariaExpanded: el.getAttribute('aria-expanded'),
        ariaChecked: el.getAttribute('aria-checked'),
        ariaSelected: el.getAttribute('aria-selected'),
        ariaHaspopup: el.getAttribute('aria-haspopup'),
        dataState: el.getAttribute('data-state'),
        text: redactDiagnosticText(el.textContent, 80),
        rect,
      };
    };
    const describeMenu = (menu) => {
      if (!menu || typeof menu.querySelectorAll !== 'function') return null;
      const items = Array.from(
        menu.querySelectorAll('[role="menuitem"], [role="menuitemradio"], [role="option"], button, [data-testid]'),
      )
        .slice(0, 30)
        .map(describeNode);
      return {
        role: menu.getAttribute?.('role') ?? null,
        testid: menu.getAttribute?.('data-testid') ?? null,
        itemCount: items.length,
        items,
      };
    };
    const collectPickerDiagnostic = () => {
      try {
        const trailings = findTrailingButtons();
        const switchers = Array.from(document.querySelectorAll('[data-testid*="model-switcher"]'));
        const composerButtons = Array.from(
          document.querySelectorAll(
            'form button[aria-haspopup="menu"], [data-testid="model-switcher-dropdown-button"]',
          ),
        );
        const menus = Array.from(document.querySelectorAll(MENU_CONTAINER_SELECTOR)).filter(
          isVisible,
        );
        const modelBtn = findModelButton();
        return {
          targetModelKind: TARGET_MODEL_KIND,
          targetLevel: TARGET_LEVEL,
          modelButton: describeNode(modelBtn),
          composerButtons: composerButtons.slice(0, 12).map(describeNode),
          trailingCount: trailings.length,
          trailings: trailings.slice(0, 12).map(describeNode),
          modelSwitcherCount: switchers.length,
          modelSwitcher: switchers.slice(0, 12).map(describeNode),
          menuCount: menus.length,
          menus: menus.slice(0, 4).map(describeMenu),
        };
      } catch (err) {
        return { error: redactDiagnosticText(err && err.message ? err.message : err) };
      }
    };
    const modelKindFromNode = (button) => {
      const label = normalize(
        (button?.textContent ?? '') + ' ' + (button?.getAttribute?.('aria-label') ?? ''),
      );
      if (hasToken(label, 'pro')) return 'pro';
      if (hasToken(label, 'thinking')) return 'thinking';
      if (hasToken(label, 'instant')) return 'instant';
      return null;
    };
    const currentModelKind = () => modelKindFromNode(findModelButton());
    const effectiveTargetModelKind = () => TARGET_MODEL_KIND || currentModelKind();
    const isIntelligenceEffortMenu = (menu) => {
      if (menu?.getAttribute?.('data-testid') === 'composer-intelligence-picker-content') {
        return true;
      }
      if (menu?.querySelector?.(INTELLIGENCE_MENU_SELECTOR)) {
        return true;
      }
      const label = menu?.querySelector?.('.__menu-label, [class*="menu-label"]');
      return normalize(label?.textContent ?? '').includes('intelligence');
    };
    const failure = (status, extra = {}) => ({
      status,
      modelKind: effectiveTargetModelKind(),
      ...extra,
      diagnostic: collectPickerDiagnostic(),
    });
    const findOptionInMenu = (menu, modelKindOverride = null) => {
      const items = Array.from(menu.querySelectorAll(MENU_ITEM_SELECTOR));
      const modelKind = modelKindOverride || effectiveTargetModelKind();
      if (modelKind === 'pro') {
        // GPT-5.6's unified Intelligence picker exposes Pro as the highest
        // effort radio directly. It no longer has a nested "Pro Extended"
        // row, so preserve the legacy request semantics by selecting Pro.
        if (
          TARGET_LEVEL === 'extended' &&
          isIntelligenceEffortMenu(menu) &&
          !document.querySelector(PRO_EFFORT_TRIGGER_SELECTOR)
        ) {
          for (const item of items) {
            const itemText = normalize(
              (item.textContent ?? '') + ' ' + (item.getAttribute?.('aria-label') ?? ''),
            );
            if (itemText === 'pro') return item;
          }
        }
        for (const item of items) {
          const itemText = normalize(
            (item.textContent ?? '') + ' ' + (item.getAttribute?.('aria-label') ?? ''),
          );
          if (
            hasToken(itemText, 'pro') &&
            (matchesLevel(item.textContent ?? '') ||
              matchesLevel(item.getAttribute?.('aria-label') ?? ''))
          ) {
            return item;
          }
        }
        if (isIntelligenceEffortMenu(menu)) {
          return null;
        }
      }
      for (const item of items) {
        const itemText = normalize(
          (item.textContent ?? '') + ' ' + (item.getAttribute?.('aria-label') ?? ''),
        );
        if (modelKind !== 'pro' && hasToken(itemText, 'pro')) {
          continue;
        }
        if (
          matchesLevel(item.textContent ?? '') ||
          matchesLevel(item.getAttribute?.('aria-label') ?? '')
        ) {
          return item;
        }
      }
      if (TARGET_LEVEL === 'heavy') {
        // Older Chinese layouts used bare 高 for the highest effort. Keep it
        // only as a second-pass exact fallback so a current 高 row can never
        // win before the primary 极高 row.
        for (const item of items) {
          const itemText = normalize(item.textContent ?? '');
          const ariaLabel = normalize(item.getAttribute?.('aria-label') ?? '');
          if (itemText === '高' || ariaLabel === '高') return item;
        }
      }
      return null;
    };
    const countEffortLevels = (menu) => {
      const text = normalize(menu?.textContent ?? '');
      let hits = 0;
      for (const tokens of Object.values(LEVEL_TOKENS)) {
        if (tokens.some((token) => text.includes(String(token).toLowerCase()))) hits += 1;
      }
      return hits;
    };
    const isEffortMenu = (menu) => {
      if (!isVisible(menu)) return false;
      if (menu.getAttribute?.('data-testid') === 'composer-intelligence-picker-content') return true;
      if (menu.querySelector?.(INTELLIGENCE_MENU_SELECTOR)) return true;
      const label = menu.querySelector?.('.__menu-label, [class*="menu-label"]');
      const labelText = normalize(label?.textContent ?? '');
      return (
        labelText.includes('intelligence') ||
        labelText.includes('thinking time') ||
        labelText.includes('thinking effort') ||
        countEffortLevels(menu) >= 2
      );
    };
    const isProEffortMenu = (menu) => {
      if (!isVisible(menu)) return false;
      const text = normalize(menu?.textContent ?? '');
      return text.includes('pro standard') && text.includes('pro extended');
    };
    const controlledMenu = (trigger) => {
      const id = trigger?.getAttribute?.('aria-controls');
      if (!id) return null;
      const menu = document.getElementById?.(id);
      return isEffortMenu(menu) ? menu : null;
    };
    const findVisibleEffortMenu = (trigger) => {
      const controlled = controlledMenu(trigger);
      if (controlled) return controlled;
      for (const menu of document.querySelectorAll(MENU_CONTAINER_SELECTOR)) {
        if (isEffortMenu(menu)) return menu;
      }
      return null;
    };
    const controlledProEffortMenu = (trigger) => {
      const id = trigger?.getAttribute?.('aria-controls');
      if (!id) return null;
      const menu = document.getElementById?.(id);
      return isProEffortMenu(menu) ? menu : null;
    };
    const findVisibleProEffortMenu = (trigger) => {
      const controlled = controlledProEffortMenu(trigger);
      if (controlled) return controlled;
      for (const menu of document.querySelectorAll(MENU_CONTAINER_SELECTOR)) {
        if (isProEffortMenu(menu)) return menu;
      }
      return null;
    };
    const matchesProEffortLevel = (node) => {
      const text = normalize(
        (node?.textContent ?? '') + ' ' + (node?.getAttribute?.('aria-label') ?? ''),
      );
      if (TARGET_LEVEL === 'standard') {
        return text.includes('pro') && text.includes('standard');
      }
      if (TARGET_LEVEL === 'extended') {
        return text.includes('pro') && text.includes('extended');
      }
      return false;
    };
    const findProEffortOptionInMenu = (menu) => {
      for (const item of menu.querySelectorAll(MENU_ITEM_SELECTOR)) {
        if (matchesProEffortLevel(item)) return item;
      }
      return null;
    };
    const freshComposerTrigger = (trigger) => {
      if (!trigger?.matches?.('button.__composer-pill')) return null;
      // React can replace the composer pill after an effort click. Keep using
      // the captured node while it is live, but re-query once it is detached so
      // verification does not read its stale pre-click label.
      if (trigger.isConnected !== false) return trigger;
      return findComposerEffortPill() || findModelButton() || trigger;
    };
    const currentProEffortPillMatchesTarget = (trigger, modelKindOverride = null) => {
      const button = freshComposerTrigger(trigger) || findModelButton();
      if ((modelKindOverride || TARGET_MODEL_KIND || modelKindFromNode(button)) !== 'pro') {
        return false;
      }
      const label = normalize(button?.textContent ?? '');
      if (TARGET_LEVEL === 'standard') {
        return hasToken(label, 'pro') && !hasToken(label, 'extended');
      }
      if (TARGET_LEVEL === 'extended') {
        return hasToken(label, 'pro') && hasToken(label, 'extended');
      }
      return false;
    };
    const currentEffortPillMatchesTarget = (trigger, modelKindOverride = null) => {
      if (currentProEffortPillMatchesTarget(trigger, modelKindOverride)) return true;
      const button = freshComposerTrigger(trigger) || findModelButton();
      if ((modelKindOverride || TARGET_MODEL_KIND || modelKindFromNode(button)) === 'pro') {
        return false;
      }
      const label = (button?.textContent ?? '') + ' ' + (button?.getAttribute?.('aria-label') ?? '');
      return matchesLevel(label);
    };
    const selectAndVerify = async (trigger, findOption, modelKindOverride = null) => {
      const option = findOption();
      const triggerModelKind =
        modelKindOverride ||
        TARGET_MODEL_KIND ||
        modelKindFromNode(trigger) ||
        effectiveTargetModelKind();
      if (!option) return failure('option-not-found', { modelKind: triggerModelKind });
      const label = option.textContent?.trim?.() || null;
      if (optionIsSelected(option)) {
        closeOpenMenus();
        return { status: 'already-selected', label };
      }

      dispatchClickSequence(option);
      await sleep(STEP_WAIT_MS);
      const refreshed = findOption();
      if (refreshed && optionIsSelected(refreshed)) {
        closeOpenMenus();
        return { status: 'switched', label: refreshed.textContent?.trim?.() || label };
      }
      if (currentEffortPillMatchesTarget(trigger, triggerModelKind)) {
        closeOpenMenus();
        return { status: 'switched', label };
      }

      const reopenTrigger = freshComposerTrigger(trigger) || trigger;
      if (!refreshed && reopenTrigger?.getAttribute?.('aria-expanded') !== 'true') {
        dispatchClickSequence(reopenTrigger);
        await sleep(INITIAL_WAIT_MS);
      }
      const deadline = performance.now() + 2000;
      while (performance.now() < deadline) {
        const selected = findOption();
        if (selected && optionIsSelected(selected)) {
          closeOpenMenus();
          return { status: 'switched', label: selected.textContent?.trim?.() || label };
        }
        if (currentEffortPillMatchesTarget(trigger, triggerModelKind)) {
          closeOpenMenus();
          return { status: 'switched', label };
        }
        await sleep(100);
      }
      const result = failure('selection-unverified', { modelKind: triggerModelKind });
      closeOpenMenus();
      return result;
    };
    const selectProEffortFromSubmenu = async () => {
      if (TARGET_MODEL_KIND !== 'pro' || (TARGET_LEVEL !== 'standard' && TARGET_LEVEL !== 'extended')) {
        return null;
      }
      const trigger = document.querySelector(PRO_EFFORT_TRIGGER_SELECTOR);
      if (!trigger) {
        return null;
      }
      dispatchHoverSequence(trigger);
      if (trigger.getAttribute?.('aria-expanded') !== 'true') {
        dispatchClickSequence(trigger);
      }
      const deadline = performance.now() + MAX_WAIT_MS;
      while (performance.now() < deadline) {
        const menu = findVisibleProEffortMenu(trigger);
        if (menu) {
          return selectAndVerify(trigger, () => {
            const currentMenu = findVisibleProEffortMenu(trigger);
            return currentMenu ? findProEffortOptionInMenu(currentMenu) : null;
          });
        }
        await sleep(100);
      }
      return null;
    };

    // Current ChatGPT exposes a standalone Pro or Thinking composer pill whose
    // controlled menu contains the effort levels. Prefer this ownership boundary
    // before probing older model-picker layouts.
    const COMPOSER_EFFORT_PILL_SELECTORS = [
      'form button.__composer-pill',
      '[data-testid="composer-footer-actions"] button.__composer-pill',
      '.__composer-pill-composite button.__composer-pill',
    ];
    const findComposerEffortPill = () => {
      const seen = new Set();
      let gpt56Fallback = null;
      for (const selector of COMPOSER_EFFORT_PILL_SELECTORS) {
        for (const button of document.querySelectorAll(selector)) {
          if (seen.has(button) || !isVisible(button)) continue;
          seen.add(button);
          if (button.getAttribute?.('data-testid') === 'model-switcher-dropdown-button') continue;
          const label = normalize(
            (button.getAttribute?.('aria-label') ?? '') + ' ' +
            (button.getAttribute?.('data-testid') ?? '') + ' ' +
            (button.textContent ?? ''),
          );
          if (
            (TARGET_MODEL_KIND === 'pro' && hasToken(label, 'pro') && !hasToken(label, 'thinking')) ||
            (TARGET_MODEL_KIND === 'thinking' && hasToken(label, 'thinking') && !hasToken(label, 'pro')) ||
            (!TARGET_MODEL_KIND && hasToken(label, 'thinking')) ||
            (button.matches?.('button.__composer-pill') && matchesAnyEffortLevel(label))
          ) {
            return button;
          }
          if (
            TARGET_IS_GPT56_MODEL &&
            button.matches?.('button.__composer-pill') &&
            normalize(button.textContent ?? '') === 'pro'
          ) {
            gpt56Fallback ||= button;
          }
        }
      }
      return gpt56Fallback;
    };
    let composerEffortPill = findComposerEffortPill();
    let modelBtn = findModelButton();
    const modelKindFromLegacyTrailing = (trailing) => {
      const row = trailing.closest?.(
        '[role="menuitem"], [role="menuitemradio"], [data-radix-collection-item]',
      );
      const idText = normalize(
        (row?.getAttribute?.('data-testid') ?? '') + ' ' +
        (trailing.getAttribute?.('data-testid') ?? '')
      );
      if (!idText.includes('model switcher')) return null;
      const modelPart = normalize(idText.replace(/\\bthinking effort\\b.*$/, ''));
      if (hasToken(modelPart, 'pro')) return 'pro';
      if (hasToken(modelPart, 'thinking')) return 'thinking';
      if (hasToken(modelPart, 'instant')) return 'instant';
      return null;
    };
    const legacyEffortOwnerIsReady = () => {
      if (
        TARGET_MODEL_KIND === 'pro' &&
        TARGET_LEVEL === 'extended' &&
        isVisible(document.querySelector(INTELLIGENCE_MENU_SELECTOR))
      ) {
        return true;
      }
      const expectedKind = TARGET_MODEL_KIND || modelKindFromNode(modelBtn);
      return Boolean(
        expectedKind &&
        findTrailingButtons().some(
          (button) => isVisible(button) && modelKindFromLegacyTrailing(button) === expectedKind,
        ),
      );
    };
    let attemptedModelButton =
      modelBtn?.getAttribute?.('aria-expanded') === 'true' ? modelBtn : null;
    const effortOwnerDeadline = performance.now() + MAX_WAIT_MS;
    while (!composerEffortPill && performance.now() < effortOwnerDeadline) {
      if (
        modelBtn &&
        attemptedModelButton !== modelBtn &&
        modelBtn.getAttribute?.('aria-expanded') !== 'true'
      ) {
        dispatchClickSequence(modelBtn);
        attemptedModelButton = modelBtn;
        await sleep(INITIAL_WAIT_MS);
      }
      if (modelBtn && legacyEffortOwnerIsReady()) break;
      await sleep(100);
      composerEffortPill = findComposerEffortPill();
      modelBtn = findModelButton();
      if (modelBtn?.getAttribute?.('aria-expanded') === 'true') {
        attemptedModelButton = modelBtn;
      }
    }
    if (composerEffortPill) {
      if (attemptedModelButton && attemptedModelButton !== composerEffortPill) closeOpenMenus();
      const composerModelKind =
        TARGET_MODEL_KIND ||
        (TARGET_IS_GPT56_MODEL ? 'versioned' : modelKindFromNode(composerEffortPill));
      if (composerEffortPill.getAttribute?.('aria-expanded') !== 'true') {
        dispatchClickSequence(composerEffortPill);
        await sleep(INITIAL_WAIT_MS);
      }
      const deadline = performance.now() + MAX_WAIT_MS;
      while (performance.now() < deadline) {
        const menu = findVisibleEffortMenu(composerEffortPill);
        if (menu) {
          const proEffortResult = await selectProEffortFromSubmenu();
          if (proEffortResult) {
            return proEffortResult;
          }
          return selectAndVerify(
            composerEffortPill,
            () => {
              const currentMenu = findVisibleEffortMenu(composerEffortPill);
              return currentMenu ? findOptionInMenu(currentMenu, composerModelKind) : null;
            },
            composerModelKind,
          );
        }
        await sleep(100);
      }
      const result = failure('menu-not-found', {
        modelKind: composerModelKind,
      });
      closeOpenMenus();
      return result;
    }

    // Older ChatGPT layouts attach effort controls to rows inside the model
    // picker. Keep these compatibility paths after the standalone pill owner.
    const findEffortRow = (node) => {
      let current = node instanceof HTMLElement ? node.parentElement : null;
      while (current && current !== document.body) {
        if (current.getAttribute?.('data-model-picker-thinking-effort-row') === 'true') {
          return current;
        }
        current = current.parentElement;
      }
      return null;
    };
    const rowIsSelected = (row) => {
      if (!(row instanceof HTMLElement)) return false;
      const modelItem = row.querySelector('[data-model-picker-thinking-effort-menu-item="true"], [role="menuitemradio"]');
      if (optionIsSelected(modelItem)) return true;
      return Boolean(
        row.querySelector(
          '[aria-checked="true"], [aria-selected="true"], [aria-current="true"], [data-selected="true"], [data-state="checked"], [data-state="selected"], [data-state="on"]',
        ),
      );
    };
    const rowForTrailing = (trailing) =>
      trailing.closest('[role="menuitem"], [role="menuitemradio"], [data-radix-collection-item]');
    const rowTextForTrailing = (trailing) => {
      const row = rowForTrailing(trailing) || findEffortRow(trailing);
      return normalize(
        (row?.getAttribute?.('aria-label') ?? '') + ' ' +
        (row?.getAttribute?.('data-testid') ?? '') + ' ' +
        (row?.textContent ?? '') + ' ' +
        (trailing.getAttribute?.('aria-label') ?? '') + ' ' +
        (trailing.getAttribute?.('data-testid') ?? '')
      );
    };
    const modelKindFromTrailing = modelKindFromLegacyTrailing;
    const trailingMatchesTargetModelKind = (trailing) => {
      if (!TARGET_MODEL_KIND) return false;
      const idKind = modelKindFromTrailing(trailing);
      if (idKind) return idKind === TARGET_MODEL_KIND;
      const text = rowTextForTrailing(trailing);
      if (TARGET_MODEL_KIND === 'pro') {
        return hasToken(text, 'pro') && !hasToken(text, 'thinking');
      }
      if (TARGET_MODEL_KIND === 'thinking') {
        return hasToken(text, 'thinking') && !hasToken(text, 'pro');
      }
      if (TARGET_MODEL_KIND === 'instant') {
        return hasToken(text, 'instant') && !hasToken(text, 'thinking') && !hasToken(text, 'pro');
      }
      return false;
    };
    const pickSingleStableTrailing = (trailings) => {
      const visible = trailings.filter((trailing) => isVisible(trailing));
      return visible.length === 1 ? visible[0] : null;
    };
    const pickTrailingForCurrentModel = () => {
      const trailings = findTrailingButtons();
      if (trailings.length === 0) return null;
      if (trailings.length === 1) return trailings[0];
      // Prefer the trailing button whose model row is currently selected.
      for (const t of trailings) {
        const row = findEffortRow(t);
        if (rowIsSelected(row)) return t;
      }
      if (TARGET_MODEL_KIND) {
        const targetTrailings = trailings.filter((t) => trailingMatchesTargetModelKind(t));
        return pickSingleStableTrailing(targetTrailings) || KIND_NOT_FOUND;
      }
      return null;
    };

    const modelButtonDeadline = performance.now() + MAX_WAIT_MS;
    while (!modelBtn && performance.now() < modelButtonDeadline) {
      await sleep(100);
      modelBtn = findModelButton();
    }
    if (!modelBtn) {
      return failure('chip-not-found');
    }
    // Open model menu (idempotent — leaves it open if already open).
    if (
      modelBtn.getAttribute('aria-expanded') !== 'true' &&
      !legacyEffortOwnerIsReady()
    ) {
      dispatchClickSequence(modelBtn);
      await sleep(INITIAL_WAIT_MS);
    }

    // ---------- COMPATIBILITY UI: unified "Intelligence" effort picker ----------
    // One observed ChatGPT layout replaced the per-model trailing buttons with a single
    // "Intelligence" menu ([data-testid="composer-intelligence-picker-content"]),
    // whose role="menuitemradio" rows are the effort tiers. We verify the checked
    // radio instead of trusting the composer-pill label; non-Pro targets also
    // explicitly skip Pro rows before matching effort labels.
    if (TARGET_MODEL_KIND === 'pro' && TARGET_LEVEL === 'extended') {
      const matchesProExtended = (node) => {
        const text = normalize(
          (node?.textContent ?? '') + ' ' + (node?.getAttribute?.('aria-label') ?? ''),
        );
        return text.includes('pro') && text.includes('extended');
      };
      const findProExtendedOption = () => {
        const menu = document.querySelector(INTELLIGENCE_MENU_SELECTOR);
        if (!isVisible(menu)) return null;
        for (const item of menu.querySelectorAll(
          '[role="menuitemradio"], [role="menuitem"], [role="option"]',
        )) {
          if (matchesProExtended(item)) return item;
        }
        return null;
      };
      let proExtended = null;
      const intelligenceDeadline = performance.now() + INTELLIGENCE_WAIT_MS;
      while (performance.now() < intelligenceDeadline) {
        proExtended = findProExtendedOption();
        if (proExtended) break;
        await sleep(100);
      }
      if (proExtended) {
        return selectAndVerify(modelBtn, findProExtendedOption);
      }
      // Intelligence menu absent (older UI) or its Pro Extended row is missing:
      // fall through to the legacy trailing-button path below.
    }

    let trailing = null;
    const trailingDeadline = performance.now() + MAX_WAIT_MS;
    while (performance.now() < trailingDeadline) {
      trailing = pickTrailingForCurrentModel();
      if (trailing) break;
      await sleep(100);
    }
    if (!trailing) {
      const result = failure('chip-not-found');
      closeOpenMenus();
      return result;
    }
    if (trailing.kindNotFound) {
      const result = failure('model-kind-not-found', { modelKind: TARGET_MODEL_KIND });
      closeOpenMenus();
      return result;
    }

    dispatchClickSequence(trailing);
    await sleep(STEP_WAIT_MS);

    // Resolve the effort submenu via aria-controls when ChatGPT exposes it,
    // otherwise fall back to scanning newly opened menus for our level tokens.
    const resolveEffortMenu = () => {
      const id = trailing.getAttribute('aria-controls');
      if (id) {
        const node = document.getElementById?.(id);
        if (isEffortMenu(node)) return node;
      }
      const menus = document.querySelectorAll(MENU_CONTAINER_SELECTOR);
      let best = null;
      for (const menu of menus) {
        if (menu === modelBtn || menu.contains(trailing)) continue;
        if (!isVisible(menu)) continue;
        const hits = countEffortLevels(menu);
        if (hits >= 2 && (!best || hits > best.hits)) best = { menu, hits };
      }
      return best?.menu ?? null;
    };

    let effortMenu = null;
    const effortDeadline = performance.now() + MAX_WAIT_MS;
    while (performance.now() < effortDeadline) {
      effortMenu = resolveEffortMenu();
      if (effortMenu) break;
      await sleep(100);
    }
    if (!effortMenu) {
      const result = failure('menu-not-found');
      closeOpenMenus();
      return result;
    }

    return selectAndVerify(trailing, () => {
      const currentMenu = resolveEffortMenu();
      return currentMenu ? findOptionInMenu(currentMenu) : null;
    });
  })()`;
}

export function buildThinkingTimeExpressionForTest(
  level: ThinkingTimeLevel = "extended",
  desiredModel?: string | null,
): string {
  return buildThinkingTimeExpression(level, desiredModel);
}

function inferThinkingTargetModelKind(
  desiredModel?: string | null,
): "pro" | "thinking" | "instant" | null {
  const normalized = (desiredModel ?? "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  if (!normalized) return null;
  const tokens = normalized.split(" ");
  if (tokens.includes("pro")) return "pro";
  if (tokens.includes("thinking")) return "thinking";
  if (tokens.includes("instant")) return "instant";
  return null;
}

export function inferThinkingTargetModelKindForTest(
  desiredModel?: string | null,
): "pro" | "thinking" | "instant" | null {
  return inferThinkingTargetModelKind(desiredModel);
}
