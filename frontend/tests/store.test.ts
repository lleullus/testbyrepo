import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useStudioStore } from '../src/store/studio'
import type {
  BaselineStructureDTO,
  CompositionStateDTO,
  CutDTO,
  CutId,
  StudioSnapshotDTO,
} from '../src/api/contracts'

const DEFAULT_COMPOSITION: CompositionStateDTO = {
  schema_version: 1,
  gap_px: 24,
  font_sha256: '0'.repeat(64),
  bubbles: [],
}

function makeSnapshot(overrides: Partial<StudioSnapshotDTO> = {}): StudioSnapshotDTO {
  const cuts = [1, 2, 3, 4, 5].map((cutId) => ({
    cut_id: cutId as CutId,
    desired_revision: 1,
    effective_intent: { prompt: `prompt-${cutId}`, dialogue: `dialogue-${cutId}` },
    realized_revision: 1,
    realized_asset_id: `asset-${cutId}`,
    realized_content_hash: '0'.repeat(64),
    realized_asset_url: `/api/cuts/${cutId}/realization?asset_id=asset-${cutId}&revision=1`,
    currency: 'CURRENT' as const,
  })) as [CutDTO, CutDTO, CutDTO, CutDTO, CutDTO]

  return {
    schema_version: 2,
    authority_revision: 1,
    baseline: null,
    cuts,
    realization_complete: { complete: true, status: 'COMPLETE' },
    composition: { revision: 1, state: DEFAULT_COMPOSITION, updated_at: '2026-01-01T00:00:00Z' },
    render_contract: { width: 1024, height: 7680, default_composition: DEFAULT_COMPOSITION },
    jobs: [],
    review_artifacts: [],
    release_authorization: { active: null, history: [] },
    delivery_attempts: [],
    generation_control: {
      stop_epoch: 0,
      runner_id: null,
      runner_pid: null,
      runner_start_token: null,
      runner_started_at: null,
    },
    ...overrides,
  }
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

interface PendingRequest {
  url: string
  init?: RequestInit
  resolve: (response: Response) => void
}

function controlledFetch(): PendingRequest[] {
  const pending: PendingRequest[] = []
  vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL, init?: RequestInit) =>
    new Promise<Response>((resolve) => pending.push({ url: String(input), init, resolve })),
  ))
  return pending
}

function requestBody(request: PendingRequest): Record<string, unknown> {
  return JSON.parse(String(request.init?.body)) as Record<string, unknown>
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe('authoritative snapshot monotonicity', () => {
  it('applies only a strictly newer snapshot without clearing local drafts', () => {
    const store = useStudioStore()
    store.server = makeSnapshot({ authority_revision: 10 })
    store.setIntentDraft(1, { prompt: 'local', dialogue: 'draft' }, false)

    store.applySnapshot(makeSnapshot({ authority_revision: 5 }))
    store.applySnapshot(makeSnapshot({ authority_revision: 10 }))
    expect(store.server.authority_revision).toBe(10)
    expect(store.drafts.intents[1]?.value.prompt).toBe('local')

    store.applySnapshot(makeSnapshot({ authority_revision: 11 }))
    expect(store.server.authority_revision).toBe(11)
    expect(store.drafts.intents[1]?.value.prompt).toBe('local')
    expect(store.saves['intent-1']?.state).toBe('base-changed')
  })
})

describe('cross-type authoritative edit lane', () => {
  it('keeps a newer draft, preserves the first request, and serializes the latest value from the fresh base', async () => {
    const pending = controlledFetch()
    const store = useStudioStore()
    store.server = makeSnapshot({ authority_revision: 1 })

    store.setIntentDraft(1, { prompt: 'first', dialogue: 'one' })
    await vi.waitFor(() => expect(pending).toHaveLength(1))
    const firstBody = requestBody(pending[0])

    store.setIntentDraft(1, { prompt: 'latest', dialogue: 'two' })
    expect(requestBody(pending[0])).toEqual(firstBody)

    pending[0].resolve(jsonResponse({
      accepted_mutation_id: firstBody.mutation_id,
      snapshot: makeSnapshot({ authority_revision: 2 }),
    }))

    await vi.waitFor(() => expect(pending).toHaveLength(2))
    const secondBody = requestBody(pending[1])
    expect(store.drafts.intents[1]?.value).toEqual({ prompt: 'latest', dialogue: 'two' })
    expect(secondBody.expected_authority_revision).toBe(2)
    expect(secondBody.intent).toEqual({ prompt: 'latest', dialogue: 'two' })
    expect(secondBody.mutation_id).not.toBe(firstBody.mutation_id)

    pending[1].resolve(jsonResponse({
      accepted_mutation_id: secondBody.mutation_id,
      snapshot: makeSnapshot({ authority_revision: 3 }),
    }))
    await vi.waitFor(() => expect(store.drafts.intents[1]).toBeUndefined())
  })

  it('serializes default composition only after a baseline is accepted', async () => {
    const pending = controlledFetch()
    const store = useStudioStore()
    store.server = makeSnapshot({
      authority_revision: 0,
      composition: { revision: 0, state: null, updated_at: '2026-01-01T00:00:00Z' },
    })
    const structure: BaselineStructureDTO = {
      source_brief: 'brief',
      cuts: [1, 2, 3, 4, 5].map((cutId) => ({
        cut_id: cutId as CutId,
        role: `role-${cutId}`,
        beat: `beat-${cutId}`,
      })) as BaselineStructureDTO['cuts'],
    }
    const intents = [1, 2, 3, 4, 5].map((cutId) => ({
      cut_id: cutId as CutId,
      intent: { prompt: `prompt-${cutId}`, dialogue: `dialogue-${cutId}` },
    }))

    store.setBaselineDraft(structure, intents)
    await vi.waitFor(() => expect(pending).toHaveLength(1))
    const baselineBody = requestBody(pending[0])
    pending[0].resolve(jsonResponse({
      accepted_mutation_id: baselineBody.mutation_id,
      snapshot: makeSnapshot({
        authority_revision: 1,
        baseline: {
          baseline_id: String(baselineBody.baseline_id),
          structure,
          authority_revision: 1,
          created_at: '2026-01-01T00:00:00Z',
          intents: intents.map(({ cut_id }) => ({ cut_id, intent_revision: 1 })),
        },
        composition: { revision: 0, state: null, updated_at: '2026-01-01T00:00:00Z' },
      }),
    }))

    await vi.waitFor(() => expect(pending).toHaveLength(2))
    expect(pending[1].url).toBe('/api/composition')
    const compositionBody = requestBody(pending[1])
    expect(compositionBody.expected_authority_revision).toBe(1)
    expect(compositionBody.expected_composition_revision).toBe(0)
    expect(compositionBody.state).toEqual(DEFAULT_COMPOSITION)

    pending[1].resolve(jsonResponse({
      accepted_mutation_id: compositionBody.mutation_id,
      snapshot: makeSnapshot({ authority_revision: 2 }),
    }))
    await vi.waitFor(() => expect(store.drafts.composition).toBeNull())
    expect(store.drafts.baseline).toBeNull()
  })

  it('sends STOP immediately while an edit request is held and preserves the draft on conflict', async () => {
    const pending = controlledFetch()
    const store = useStudioStore()
    store.server = makeSnapshot({
      jobs: [{
        job_id: 'job-1', cut_id: 1, target_desired_revision: 1, status: 'running',
        terminal_detail: null, created_at: '', updated_at: '', attempts: [],
      }],
    })

    store.setCompositionDraft({ ...DEFAULT_COMPOSITION, gap_px: 32 })
    await vi.waitFor(() => expect(pending).toHaveLength(1))
    const editBody = requestBody(pending[0])

    const stopPromise = store.stopAll()
    await vi.waitFor(() => expect(pending).toHaveLength(2))
    expect(pending[1].url).toBe('/api/generation/stop')
    expect(store.drafts.composition?.value.state.gap_px).toBe(32)

    pending[1].resolve(jsonResponse({ receipt: {}, snapshot: makeSnapshot({ authority_revision: 2 }) }))
    await stopPromise
    pending[0].resolve(jsonResponse({
      error: {
        code: 'conflict',
        message: 'conflict',
        current_snapshot: makeSnapshot({ authority_revision: 2 }),
        expected_revision: editBody.expected_authority_revision,
        actual_revision: 2,
      },
    }, 409))

    await vi.waitFor(() => expect(store.saves.composition?.state).toBe('conflict'))
    expect(store.drafts.composition?.value.state.gap_px).toBe(32)
  })

  it('requires explicit reapply after an external snapshot changes the draft base', async () => {
    const pending = controlledFetch()
    const store = useStudioStore()
    store.server = makeSnapshot({ authority_revision: 5 })
    store.setIntentDraft(1, { prompt: 'local', dialogue: 'draft' }, false)

    store.applySnapshot(makeSnapshot({ authority_revision: 6 }))
    expect(store.saves['intent-1']?.state).toBe('base-changed')
    store.saveIntentDraft(1)
    expect(pending).toHaveLength(0)

    store.retrySave('intent-1')
    await vi.waitFor(() => expect(pending).toHaveLength(1))
    const body = requestBody(pending[0])
    expect(body.expected_authority_revision).toBe(6)
    expect(body.intent).toEqual({ prompt: 'local', dialogue: 'draft' })

    pending[0].resolve(jsonResponse({
      accepted_mutation_id: body.mutation_id,
      snapshot: makeSnapshot({ authority_revision: 7 }),
    }))
    await vi.waitFor(() => expect(store.drafts.intents[1]).toBeUndefined())
  })
})

describe('SSE gap recovery', () => {
  it('collapses repeated snapshot-required events into one authoritative GET', async () => {
    class MockEventSource {
      static latest: MockEventSource | null = null
      onopen: (() => void) | null = null
      onerror: (() => void) | null = null
      private listeners = new Map<string, Array<(event: MessageEvent) => void>>()

      constructor(_url: string) {
        MockEventSource.latest = this
      }

      addEventListener(type: string, listener: EventListenerOrEventListenerObject) {
        const callback = listener as (event: MessageEvent) => void
        this.listeners.set(type, [...(this.listeners.get(type) ?? []), callback])
      }

      emit(type: string, data: unknown) {
        const event = { data: JSON.stringify(data) } as MessageEvent
        for (const listener of this.listeners.get(type) ?? []) listener(event)
      }

      close() {}
    }

    let resolveGap!: (response: Response) => void
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse(makeSnapshot({ authority_revision: 4 })))
      .mockImplementationOnce(() => new Promise<Response>((resolve) => { resolveGap = resolve }))
    vi.stubGlobal('fetch', fetchMock)
    vi.stubGlobal('EventSource', MockEventSource as unknown as typeof EventSource)

    const store = useStudioStore()
    await store.loadStudio()
    const eventSource = MockEventSource.latest!
    const gap = {
      schema: 'studio-event/v1',
      reason: 'revision-gap',
      authority_revision: 7,
    }
    eventSource.emit('snapshot-required', gap)
    eventSource.emit('snapshot-required', gap)

    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(store.stream.gapFetchPending).toBe(true)
    resolveGap(jsonResponse(makeSnapshot({ authority_revision: 7 })))
    await vi.waitFor(() => expect(store.stream.gapFetchPending).toBe(false))
    expect(store.server?.authority_revision).toBe(7)
    store.dispose()
  })
})
