/** Store-facing SSE lifecycle — connects the event source to the store. */
// This composable is intentionally kept thin.
// The actual SSE connection and event dispatching is handled in the store itself
// (via connectSSE/disconnectSSE and handleEvent), because the store must own
// the decision of when to apply or ignore events (monotonic revision gating).
// This file exists for the architecture's declared directory structure.

export { createStudioEventSource } from '@/api/events'
