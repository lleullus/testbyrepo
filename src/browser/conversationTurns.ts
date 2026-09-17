import { CONVERSATION_TURN_CONTAINER_SELECTOR, CONVERSATION_TURN_SELECTOR } from "./constants.js";

export interface ConversationTurnIdentity {
  turnId: string | null;
  messageId: string | null;
  testId: string | null;
  absoluteOrdinal: number | null;
}

export interface AssistantResponseIdentityScope {
  committedUserTurn: ConversationTurnIdentity;
  committedAssistantTurn?: ConversationTurnIdentity | null;
}

/** Build a browser-context expression that returns one DOM node per conversation turn. */
export function buildConversationTurnListExpression(rootExpression = "document"): string {
  const containerSelector = JSON.stringify(CONVERSATION_TURN_CONTAINER_SELECTOR);
  const fallbackSelector = JSON.stringify(CONVERSATION_TURN_SELECTOR);
  return `(() => {
    const root = ${rootExpression};
    const containers = Array.from(root.querySelectorAll(${containerSelector}));
    return containers.length > 0
      ? containers
      : Array.from(root.querySelectorAll(${fallbackSelector}));
  })()`;
}

export function buildConversationTurnCountExpression(rootExpression = "document"): string {
  return `(${buildConversationTurnListExpression(rootExpression)}).length`;
}

/**
 * Build a browser-context expression that reads top-level turn roles and stable identities.
 * The node reference is intentionally kept inside the expression so callers can use document
 * order for selection without ever persisting a DOM index as identity.
 */
export function buildConversationTurnRecordsExpression(rootExpression = "document"): string {
  return `(() => {
    const allTurns = ${buildConversationTurnListExpression(rootExpression)};
    const turns = allTurns.filter((turn) =>
      !allTurns.some(
        (other) =>
          other !== turn &&
          typeof other?.contains === 'function' &&
          other.contains(turn),
      ),
    );
    const readAttribute = (node, name) => {
      const value = node?.getAttribute?.(name);
      return typeof value === 'string' && value.trim() ? value.trim() : null;
    };
    const readRoleValues = (node) =>
      [readAttribute(node, 'data-message-author-role'), readAttribute(node, 'data-turn')]
        .filter(Boolean)
        .map((value) => value.toLowerCase());
    const readRole = (node) => {
      const roles = [...new Set(readRoleValues(node))];
      return roles.length === 1 ? roles[0] : null;
    };
    const getRoleNodes = (turn) => {
      const nested =
        typeof turn?.querySelectorAll === 'function'
          ? Array.from(turn.querySelectorAll('[data-message-author-role], [data-turn]'))
          : [];
      return [turn, ...nested];
    };
    const readConsistentAttribute = (nodes, name) => {
      const values = [
        ...new Set(nodes.map((node) => readAttribute(node, name)).filter(Boolean)),
      ];
      return {
        value: values.length === 1 ? values[0] : null,
        ambiguous: values.length > 1,
      };
    };
    const readIdentity = (turn, roleNodes) => {
      const identityNodes = [
        turn,
        ...roleNodes,
        ...roleNodes.flatMap((node) =>
          typeof node?.querySelectorAll === 'function'
            ? Array.from(node.querySelectorAll('[data-turn-id], [data-message-id], [data-testid]'))
            : [],
        ),
      ];
      const turnId = readConsistentAttribute(identityNodes, 'data-turn-id');
      const messageId = readConsistentAttribute(identityNodes, 'data-message-id');
      const testIds = [
        ...new Set(
          identityNodes
            .map((node) => readAttribute(node, 'data-testid'))
            .filter((value) => /^conversation-turn-\\d+$/.test(value || '')),
        ),
      ];
      if (turnId.ambiguous || messageId.ambiguous || testIds.length > 1) return null;
      const testId = testIds[0] || null;
      const ordinalMatch = testId?.match(/^conversation-turn-(\\d+)$/);
      const parsedOrdinal = ordinalMatch ? Number(ordinalMatch[1]) : null;
      const absoluteOrdinal =
        parsedOrdinal !== null && Number.isSafeInteger(parsedOrdinal) && parsedOrdinal >= 0
          ? parsedOrdinal
          : null;
      if (!turnId.value && !messageId.value && !testId) return null;
      return {
        turnId: turnId.value,
        messageId: messageId.value,
        testId,
        absoluteOrdinal,
      };
    };

    return turns.map((turn) => {
      const roleNodes = getRoleNodes(turn);
      const roles = [
        ...new Set(roleNodes.flatMap((node) => readRoleValues(node))),
      ];
      const role = roles.length === 1 ? roles[0] : null;
      const identityRoleNodes = roleNodes.filter((node) => readRole(node) === role);
      return {
        node: turn,
        role,
        identity: role ? readIdentity(turn, identityRoleNodes) : null,
        text: String(turn?.innerText ?? turn?.textContent ?? ''),
      };
    });
  })()`;
}

/** Build browser-context helpers for matching a persisted conversation-turn identity. */
export function buildConversationTurnIdentityMatcherExpression(): string {
  return `
    const hasStableConversationTurnIdentity = (identity) =>
      Boolean(identity && (identity.turnId || identity.messageId || identity.testId));
    const conversationTurnOrdinal = (identity) => {
      if (
        typeof identity?.absoluteOrdinal === 'number' &&
        Number.isSafeInteger(identity.absoluteOrdinal) &&
        identity.absoluteOrdinal >= 0
      ) {
        return identity.absoluteOrdinal;
      }
      const match =
        typeof identity?.testId === 'string'
          ? identity.testId.match(/^conversation-turn-(\\d+)$/)
          : null;
      if (!match) return null;
      const ordinal = Number(match[1]);
      return Number.isSafeInteger(ordinal) && ordinal >= 0 ? ordinal : null;
    };
    const sameConversationTurnIdentity = (candidate, expected) => {
      if (
        !hasStableConversationTurnIdentity(candidate) ||
        !hasStableConversationTurnIdentity(expected)
      ) {
        return false;
      }
      const expectedOrdinal = conversationTurnOrdinal(expected);
      if (expectedOrdinal !== null) {
        return conversationTurnOrdinal(candidate) === expectedOrdinal;
      }
      let comparedFields = 0;
      for (const key of ['turnId', 'messageId']) {
        const expectedValue = expected[key];
        if (expectedValue == null) continue;
        if (candidate[key] !== expectedValue) return false;
        comparedFields += 1;
      }
      return comparedFields > 0;
    };
    const sameCommittedConversationTurnIdentity = (candidate, expected) => {
      if (
        !hasStableConversationTurnIdentity(candidate) ||
        !hasStableConversationTurnIdentity(expected)
      ) {
        return false;
      }
      let sharedFields = 0;
      for (const key of ['turnId', 'messageId', 'testId', 'absoluteOrdinal']) {
        const candidateValue = candidate[key];
        const expectedValue = expected[key];
        if (candidateValue == null || expectedValue == null) continue;
        if (candidateValue !== expectedValue) return false;
        sharedFields += 1;
      }
      return sharedFields > 0;
    };
  `;
}

/** Build a browser-context resolver for the assistant turn owned by a committed user turn. */
export function buildScopedAssistantRecordResolver(
  identityScope: AssistantResponseIdentityScope,
  functionName = "resolveScopedAssistantRecord",
  scopeName = "IDENTITY_SCOPE",
): string {
  return `
    const ${scopeName} = ${JSON.stringify(identityScope)};
    ${buildConversationTurnIdentityMatcherExpression()}
    const ${functionName} = () => {
      const records = ${buildConversationTurnRecordsExpression()};
      const expectedUser = ${scopeName}?.committedUserTurn;
      if (!hasStableConversationTurnIdentity(expectedUser)) return null;
      const userMatches = records
        .map((record, index) => ({ record, index }))
        .filter(
          ({ record }) =>
            record.role === 'user' &&
            sameCommittedConversationTurnIdentity(record.identity, expectedUser),
        );
      if (userMatches.length !== 1) return null;

      const userIndex = userMatches[0].index;
      const userOrdinal = conversationTurnOrdinal(expectedUser);
      const expectedAssistant = ${scopeName}?.committedAssistantTurn;
      if (hasStableConversationTurnIdentity(expectedAssistant)) {
        const matches = records
          .map((record, index) => ({ record, index }))
          .filter(
            ({ record }) =>
              record.role === 'assistant' &&
              sameConversationTurnIdentity(record.identity, expectedAssistant),
          );
        if (matches.length !== 1) return null;
        const owned = matches[0];
        const assistantOrdinal = conversationTurnOrdinal(owned.record.identity);
        const sharesCommittedBoundary =
          userOrdinal !== null && assistantOrdinal !== null
            ? assistantOrdinal === userOrdinal + 1
            : owned.index === userIndex + 1;
        return owned.index > userIndex && sharesCommittedBoundary ? owned.record : null;
      }

      const nextRecord = records[userIndex + 1];
      if (
        nextRecord?.role === 'assistant' &&
        !hasStableConversationTurnIdentity(nextRecord.identity)
      ) {
        return null;
      }
      if (
        nextRecord?.role === 'assistant' &&
        hasStableConversationTurnIdentity(nextRecord.identity) &&
        conversationTurnOrdinal(nextRecord.identity) === null
      ) {
        return nextRecord;
      }

      if (userOrdinal !== null) {
        const ordinalCandidates = records
          .map((record, index) => ({ record, index }))
          .filter(({ record, index }) => {
            const assistantOrdinal = conversationTurnOrdinal(record.identity);
            return (
              index > userIndex &&
              record.role === 'assistant' &&
              hasStableConversationTurnIdentity(record.identity) &&
              assistantOrdinal !== null &&
              assistantOrdinal > userOrdinal
            );
          });
        if (ordinalCandidates.length > 0) {
          const pairedCandidates = ordinalCandidates.filter(
            ({ record }) => conversationTurnOrdinal(record.identity) === userOrdinal + 1,
          );
          if (pairedCandidates.length === 0) return null;
          const closestOrdinal = Math.min(
            ...pairedCandidates.map(({ record }) => conversationTurnOrdinal(record.identity)),
          );
          const closest = pairedCandidates.filter(
            ({ record }) => conversationTurnOrdinal(record.identity) === closestOrdinal,
          );
          return closest.length === 1 ? closest[0].record : null;
        }
      }

      if (userOrdinal !== null) return null;
      if (
        nextRecord?.role !== 'assistant' ||
        !hasStableConversationTurnIdentity(nextRecord.identity)
      ) {
        return null;
      }
      const nextOrdinal = conversationTurnOrdinal(nextRecord.identity);
      if (userOrdinal !== null && nextOrdinal !== null && nextOrdinal <= userOrdinal) {
        return null;
      }
      return nextRecord;
    };
  `;
}

export function normalizeConversationTurnIdentity(value: unknown): ConversationTurnIdentity | null {
  if (!value || typeof value !== "object") return null;
  const candidate = value as Record<string, unknown>;
  const readOptionalString = (key: string): string | null => {
    const raw = candidate[key];
    return typeof raw === "string" && raw.trim() ? raw.trim() : null;
  };
  const turnId = readOptionalString("turnId");
  const messageId = readOptionalString("messageId");
  const rawTestId = readOptionalString("testId");
  const testId = /^conversation-turn-\d+$/.test(rawTestId ?? "") ? rawTestId : null;
  const ordinalMatch = testId?.match(/^conversation-turn-(\d+)$/);
  const parsedOrdinal = ordinalMatch ? Number(ordinalMatch[1]) : null;
  const explicitOrdinal =
    typeof candidate.absoluteOrdinal === "number" &&
    Number.isSafeInteger(candidate.absoluteOrdinal) &&
    candidate.absoluteOrdinal >= 0
      ? candidate.absoluteOrdinal
      : null;
  if (parsedOrdinal !== null && explicitOrdinal !== null && parsedOrdinal !== explicitOrdinal) {
    return null;
  }
  const absoluteOrdinal = parsedOrdinal ?? null;
  if (!turnId && !messageId && !testId) return null;
  return { turnId, messageId, testId, absoluteOrdinal };
}

export function hasConversationTurnIdentity(
  identity: ConversationTurnIdentity | null | undefined,
): identity is ConversationTurnIdentity {
  return Boolean(identity && (identity.turnId || identity.messageId || identity.testId));
}
