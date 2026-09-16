import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useStudioStore } from '../src/store/studio'
import {
  type BaselineStructureDTO,
  type CompositionStateDTO,
  type CutDTO,
  type CutId,
  type ReviewArtifactDTO,
  type StudioSnapshotDTO,
  isStudioSnapshotDTO,
  validateStudioSnapshot,
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
    latest_generation_request_seq: 0,
    effective_intent: { prompt: `prompt-${cutId}`, dialogue: `dialogue-${cutId}` },
    realized_revision: 1,
    realized_asset_id: `asset-${cutId}`,
    realized_content_hash: '0'.repeat(64),
    realized_asset_url: `/api/cuts/${cutId}/realization?asset_id=asset-${cutId}&revision=1`,
    currency: 'CURRENT' as const,
  })) as [CutDTO, CutDTO, CutDTO, CutDTO, CutDTO]

  return {
    schema_version: 4,
    authority_revision: 1,
    baseline: {
      baseline_id: 'baseline-1',
      structure: {
        source_brief: 'brief',
        cuts: [1, 2, 3, 4, 5].map((cutId) => ({
          cut_id: cutId as CutId,
          role: `role-${cutId}`,
          beat: `beat-${cutId}`,
        })) as BaselineStructureDTO['cuts'],
      },
      authority_revision: 1,
      created_at: '2026-01-01T00:00:00Z',
      intents: [1, 2, 3, 4, 5].map((cutId) => ({ cut_id: cutId as CutId, intent_revision: 1 })),
    },
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

describe('review authorization identity', () => {
  it('disables approval when the displayed artifact no longer matches current composition', () => {
    const store = useStudioStore()
    store.stream.status = 'OPEN'
    const contentHash = 'a'.repeat(64)
    const artifact: ReviewArtifactDTO = {
      artifact_id: `artifact-${contentHash}`,
      content_hash: contentHash,
      composition_revision: 1,
      created_at: '2026-01-01T00:00:00Z',
      cuts: ([1, 2, 3, 4, 5] as CutId[]).map((cutId) => ({
        cut_id: cutId,
        desired_revision: 1,
        realized_revision: 1,
        asset_id: `asset-${cutId}`,
        source_content_hash: '0'.repeat(64),
      })),
      asset_url: `/api/review-artifacts/artifact-${contentHash}/content`,
    }
    const summary = {
      ...artifact,
      cuts: artifact.cuts.map(({ cut_id, realized_revision, asset_id }) => ({
        cut_id,
        realized_revision,
        asset_id,
      })),
    }
    store.server = makeSnapshot({ review_artifacts: [summary] })
    store.ui.review = { artifact, displayedByteHash: contentHash, zoom: 1 }
    expect(store.canAuthorize).toBe(true)

    store.applySnapshot(makeSnapshot({
      authority_revision: 2,
      composition: { revision: 2, state: DEFAULT_COMPOSITION, updated_at: '2026-01-01T00:01:00Z' },
      review_artifacts: [summary],
    }))

    expect(store.canAuthorize).toBe(false)
  })
})

describe('cross-type authoritative edit lane', () => {
  it('keeps a newer draft, preserves the first request, and serializes the latest value from the fresh base', async () => {
    const pending = controlledFetch()
    const store = useStudioStore()
    store.stream.status = 'OPEN'
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
    store.stream.status = 'OPEN'
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
    store.stream.status = 'OPEN'
    store.server = makeSnapshot({
      jobs: [{
        job_id: 'job-1', cut_id: 1, target_desired_revision: 1, request_seq: 0, status: 'running',
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
    store.stream.status = 'OPEN'
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

describe('client resync safety and empirical cutover', () => {
  class MockEventSource {
    static latest: MockEventSource | null = null
    onopen: (() => void) | null = null
    onerror: (() => void) | null = null
    private listeners = new Map<string, Array<(event: MessageEvent) => void>>()

    constructor(_url: string) {
      MockEventSource.latest = this
      queueMicrotask(() => {
        if (this.onopen) this.onopen()
      })
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

  it('transitions to DEGRADED on disconnect, disables consequential gates, and keeps STOP callable', async () => {
    const initial = makeSnapshot({ authority_revision: 4 })
    initial.cuts[0] = {
      ...initial.cuts[0],
      latest_generation_request_seq: 1,
      currency: 'STALE',
    }
    initial.realization_complete = { complete: false, status: 'UNRESOLVED' }
    initial.jobs = [{
      job_id: 'job-1', cut_id: 1 as CutId, target_desired_revision: 1, request_seq: 1, status: 'running',
      terminal_detail: null, created_at: '', updated_at: '', attempts: [],
    }]
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(initial))
    vi.stubGlobal('fetch', fetchMock)
    vi.stubGlobal('EventSource', MockEventSource as unknown as typeof EventSource)

    const store = useStudioStore()
    await store.loadStudio()
    const eventSource = MockEventSource.latest!
    await vi.waitFor(() => expect(store.stream.status).toBe('OPEN'))
    expect(store.hasCurrentSnapshot).toBe(true)
    expect(store.canGenerate).toBe(true)

    // Trigger disconnect
    eventSource.onerror?.()
    expect(store.stream.status).toBe('DEGRADED')
    expect(store.hasCurrentSnapshot).toBe(false)
    expect(store.canMutateAuthority).toBe(false)
    expect(store.canGenerate).toBe(false)
    expect(store.canMaterializeReview).toBe(false)
    expect(store.canAuthorize).toBe(false)
    expect(store.canRelease).toBe(false)
    expect(store.server).not.toBeNull()

    // STOP remains callable while degraded
    fetchMock.mockResolvedValueOnce(jsonResponse({ receipt: {}, snapshot: makeSnapshot({ authority_revision: 5 }) }))
    await store.stopJob('job-1')
    expect(fetchMock).toHaveBeenCalledWith('/api/generation/jobs/job-1/stop', expect.anything())
    store.dispose()
  })

  it('leaves DEGRADED latched after a failed recovery retry', async () => {
    let rejectFetch!: (err: Error) => void
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse(makeSnapshot({ authority_revision: 4 })))
      .mockImplementationOnce(() => new Promise<Response>((_, reject) => { rejectFetch = reject }))
    vi.stubGlobal('fetch', fetchMock)
    vi.stubGlobal('EventSource', MockEventSource as unknown as typeof EventSource)

    const store = useStudioStore()
    await store.loadStudio()
    const eventSource = MockEventSource.latest!
    await vi.waitFor(() => expect(store.stream.status).toBe('OPEN'))

    eventSource.emit('snapshot-required', {
      schema: 'studio-event/v1',
      reason: 'revision-gap',
      authority_revision: 6,
    })
    expect(store.stream.status).toBe('DEGRADED')
    expect(store.stream.resyncPending).toBe(true)

    rejectFetch(new Error('Network error'))
    await vi.waitFor(() => expect(store.stream.resyncPending).toBe(false))
    expect(store.stream.status).toBe('DEGRADED')
    expect(store.hasCurrentSnapshot).toBe(false)
    expect(store.canMutateAuthority).toBe(false)
    store.dispose()
  })

  it('collapses concurrent resync triggers and rejects late older recovery snapshot', async () => {
    let resolveGap!: (response: Response) => void
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse(makeSnapshot({ authority_revision: 4 })))
      .mockImplementationOnce(() => new Promise<Response>((resolve) => { resolveGap = resolve }))
    vi.stubGlobal('fetch', fetchMock)
    vi.stubGlobal('EventSource', MockEventSource as unknown as typeof EventSource)

    const store = useStudioStore()
    await store.loadStudio()
    const eventSource = MockEventSource.latest!
    await vi.waitFor(() => expect(store.stream.status).toBe('OPEN'))

    const gap = {
      schema: 'studio-event/v1',
      reason: 'revision-gap',
      authority_revision: 7,
    }
    eventSource.emit('snapshot-required', gap)
    eventSource.emit('snapshot-required', gap)

    expect(fetchMock).toHaveBeenCalledTimes(2) // 1 initial load + 1 collapsed resync
    expect(store.stream.resyncPending).toBe(true)
    expect(store.stream.status).toBe('DEGRADED')

    // Newer SSE event arrives before recovery fetch resolves
    eventSource.emit('studio.snapshot', {
      schema: 'studio-event/v1',
      boot_id: 'boot-new',
      authority_revision: 8,
      snapshot: makeSnapshot({ authority_revision: 8 }),
    })
    expect(store.server?.authority_revision).toBe(8)
    expect(store.stream.status).toBe('OPEN')

    // Stale gap recovery fetch resolves with rev 7
    resolveGap(jsonResponse(makeSnapshot({ authority_revision: 7 })))
    await vi.waitFor(() => expect(store.stream.resyncPending).toBe(false))
    expect(store.server?.authority_revision).toBe(8)
    store.dispose()
  })

  it('keeps DEGRADED when recovery resolves during disconnect until transport reconnects', async () => {
    let resolveGap!: (response: Response) => void
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse(makeSnapshot({ authority_revision: 4 })))
      .mockImplementationOnce(() => new Promise<Response>((resolve) => { resolveGap = resolve }))
      .mockResolvedValueOnce(jsonResponse(makeSnapshot({ authority_revision: 5 })))
    vi.stubGlobal('fetch', fetchMock)
    vi.stubGlobal('EventSource', MockEventSource as unknown as typeof EventSource)

    const store = useStudioStore()
    await store.loadStudio()
    const eventSource = MockEventSource.latest!
    await vi.waitFor(() => expect(store.stream.status).toBe('OPEN'))

    // Disconnect transport and trigger gap
    eventSource.onerror?.()
    expect(store.stream.status).toBe('DEGRADED')

    eventSource.emit('snapshot-required', {
      schema: 'studio-event/v1',
      reason: 'revision-gap',
      authority_revision: 5,
    })

    // Recovery fetch resolves while transport is still disconnected
    resolveGap(jsonResponse(makeSnapshot({ authority_revision: 5 })))
    await vi.waitFor(() => expect(store.stream.resyncPending).toBe(false))

    // Monotonic server state updated, but status MUST remain DEGRADED!
    expect(store.server?.authority_revision).toBe(5)
    expect(store.stream.status).toBe('DEGRADED')
    expect(store.hasCurrentSnapshot).toBe(false)

    // Reconnect transport -> triggers resync and settles to OPEN
    eventSource.onopen?.()
    await vi.waitFor(() => expect(store.stream.status).toBe('OPEN'))
    expect(store.hasCurrentSnapshot).toBe(true)
    store.dispose()
  })

  it('establishes freshness on equal revision after reconnect without wiping local drafts', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse(makeSnapshot({ authority_revision: 4 })))
      .mockResolvedValueOnce(jsonResponse(makeSnapshot({ authority_revision: 4 })))
    vi.stubGlobal('fetch', fetchMock)
    vi.stubGlobal('EventSource', MockEventSource as unknown as typeof EventSource)

    const store = useStudioStore()
    await store.loadStudio()
    const eventSource = MockEventSource.latest!
    await vi.waitFor(() => expect(store.stream.status).toBe('OPEN'))

    // Create a local draft
    store.setIntentDraft(1, { prompt: 'draft-p', dialogue: 'draft-d' }, false)

    // Disconnect then reconnect
    eventSource.onerror?.()
    expect(store.stream.status).toBe('DEGRADED')

    eventSource.onopen?.()
    await vi.waitFor(() => expect(store.stream.status).toBe('OPEN'))

    // Freshness restored, draft intact
    expect(store.hasCurrentSnapshot).toBe(true)
    expect(store.drafts.intents[1]?.value.prompt).toBe('draft-p')
    expect(store.saves['intent-1']?.state).toBe('idle')
    store.dispose()
  })

  it('rejects older, mismatched, and malformed snapshot events without clearing DEGRADED', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(makeSnapshot({ authority_revision: 6 })))
    vi.stubGlobal('fetch', fetchMock)
    vi.stubGlobal('EventSource', MockEventSource as unknown as typeof EventSource)

    const store = useStudioStore()
    await store.loadStudio()
    const eventSource = MockEventSource.latest!
    await vi.waitFor(() => expect(store.stream.status).toBe('OPEN'))

    eventSource.onerror?.()
    expect(store.stream.status).toBe('DEGRADED')

    // Envelope revision (8) != payload snapshot revision (7)
    eventSource.emit('studio.snapshot', {
      schema: 'studio-event/v1',
      boot_id: 'b1',
      authority_revision: 8,
      snapshot: makeSnapshot({ authority_revision: 7 }),
    })
    expect(store.stream.status).toBe('DEGRADED')
    expect(store.server?.authority_revision).toBe(6)

    // Older revision (5 < 6)
    eventSource.emit('studio.snapshot', {
      schema: 'studio-event/v1',
      boot_id: 'b1',
      authority_revision: 5,
      snapshot: makeSnapshot({ authority_revision: 5 }),
    })
    expect(store.stream.status).toBe('DEGRADED')
    expect(store.server?.authority_revision).toBe(6)

    // Malformed data
    eventSource.emit('studio.snapshot', {
      schema: 'studio-event/v1',
      boot_id: 'b1',
      authority_revision: 'not-a-number',
      snapshot: null,
    })
    expect(store.stream.status).toBe('DEGRADED')
    expect(store.server?.authority_revision).toBe(6)
    store.dispose()
  })

  it('preserves drafts and issues zero mutation requests while degraded', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(makeSnapshot({ authority_revision: 4 })))
    vi.stubGlobal('fetch', fetchMock)
    vi.stubGlobal('EventSource', MockEventSource as unknown as typeof EventSource)

    const store = useStudioStore()
    await store.loadStudio()
    const eventSource = MockEventSource.latest!
    await vi.waitFor(() => expect(store.stream.status).toBe('OPEN'))

    eventSource.onerror?.()
    expect(store.stream.status).toBe('DEGRADED')

    const baselineCalls = fetchMock.mock.calls.length

    // Update drafts while offline
    store.setIntentDraft(1, { prompt: 'offline-p', dialogue: 'offline-d' }, false)
    store.setCompositionDraft({ ...DEFAULT_COMPOSITION, gap_px: 48 }, false)

    // Trigger save actions
    store.saveIntentDraft(1)
    store.saveCompositionDraft()
    store.saveBaselineDraft()
    await store.generateAll()
    await store.materializeReview()
    await store.exportPng()
    await store.releaseBlogger()

    // Zero mutation HTTP calls were made
    expect(fetchMock.mock.calls.length).toBe(baselineCalls)

    // Drafts remain byte-equivalent
    expect(store.drafts.intents[1]?.value.prompt).toBe('offline-p')
    expect(store.drafts.composition?.value.state.gap_px).toBe(48)

    // Alert toast was posted
    expect(store.toasts.some((t) => t.role === 'alert' && t.text.includes('재동기화'))).toBe(true)
    store.dispose()
  })

  it('rejects matching and newer incomplete snapshots on recovery fetch and leaves DEGRADED latched', async () => {
    let resolveFetch!: (res: Response) => void
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse(makeSnapshot({ authority_revision: 6 })))
      .mockImplementationOnce(() => new Promise<Response>((resolve) => { resolveFetch = resolve }))
    vi.stubGlobal('fetch', fetchMock)
    vi.stubGlobal('EventSource', MockEventSource as unknown as typeof EventSource)

    const store = useStudioStore()
    await store.loadStudio()
    const eventSource = MockEventSource.latest!
    await vi.waitFor(() => expect(store.stream.status).toBe('OPEN'))

    // Enter degraded via disconnect
    eventSource.onerror?.()
    expect(store.stream.status).toBe('DEGRADED')

    // Local draft created while degraded
    store.setIntentDraft(1, { prompt: 'offline-draft-p', dialogue: 'offline-draft-d' }, false)

    // Trigger resync via gap for newer revision 8
    eventSource.emit('snapshot-required', {
      schema: 'studio-event/v1',
      reason: 'revision-gap',
      authority_revision: 8,
    })
    expect(store.stream.resyncPending).toBe(true)

    // Incomplete payload with newer revision 8 (omitted cuts, baseline, composition, etc.)
    const baselineFetchCalls = fetchMock.mock.calls.length
    resolveFetch(jsonResponse({
      schema_version: 4,
      authority_revision: 8,
    }))

    await vi.waitFor(() => expect(store.stream.resyncPending).toBe(false))

    // Recovery failed validation: remains DEGRADED and latched
    expect(store.stream.status).toBe('DEGRADED')
    expect(store.hasCurrentSnapshot).toBe(false)
    expect(store.canMutateAuthority).toBe(false)
    expect(store.canGenerate).toBe(false)
    expect(store.canMaterializeReview).toBe(false)
    expect(store.canAuthorize).toBe(false)
    expect(store.canRelease).toBe(false)
    expect(store.server?.authority_revision).toBe(6)

    // Draft preserved byte-for-byte
    expect(store.drafts.intents[1]?.value.prompt).toBe('offline-draft-p')

    // Mutation attempt while degraded results in zero HTTP calls
    store.saveIntentDraft(1)
    await store.generateAll()
    expect(fetchMock.mock.calls.length).toBe(baselineFetchCalls)
    store.dispose()
  })

  it('ignores matching and newer incomplete snapshots from SSE and preserves DEGRADED and drafts', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(makeSnapshot({ authority_revision: 6 })))
    vi.stubGlobal('fetch', fetchMock)
    vi.stubGlobal('EventSource', MockEventSource as unknown as typeof EventSource)

    const store = useStudioStore()
    await store.loadStudio()
    const eventSource = MockEventSource.latest!
    await vi.waitFor(() => expect(store.stream.status).toBe('OPEN'))

    eventSource.onerror?.()
    expect(store.stream.status).toBe('DEGRADED')

    store.setIntentDraft(1, { prompt: 'draft-p', dialogue: 'draft-d' }, false)

    // Matching revision 6 incomplete object
    eventSource.emit('studio.snapshot', {
      schema: 'studio-event/v1',
      boot_id: 'b1',
      authority_revision: 6,
      snapshot: { schema_version: 4, authority_revision: 6 },
    })
    expect(store.stream.status).toBe('DEGRADED')
    expect(store.hasCurrentSnapshot).toBe(false)
    expect(store.canMutateAuthority).toBe(false)
    expect(store.canGenerate).toBe(false)
    expect(store.server?.authority_revision).toBe(6)
    expect(store.drafts.intents[1]?.value.prompt).toBe('draft-p')

    // Newer revision 8 incomplete object
    eventSource.emit('studio.snapshot', {
      schema: 'studio-event/v1',
      boot_id: 'b1',
      authority_revision: 8,
      snapshot: { schema_version: 4, authority_revision: 8 },
    })
    expect(store.stream.status).toBe('DEGRADED')
    expect(store.hasCurrentSnapshot).toBe(false)
    expect(store.canMutateAuthority).toBe(false)
    expect(store.canGenerate).toBe(false)
    expect(store.server?.authority_revision).toBe(6)
    expect(store.drafts.intents[1]?.value.prompt).toBe('draft-p')

    // Selectors do not crash and remain safe
    expect(store.canRelease).toBe(false)
    expect(store.canMaterializeReview).toBe(false)
    expect(store.realizationComplete).toBe(true)

    const baselineCalls = fetchMock.mock.calls.length
    store.saveIntentDraft(1)
    expect(fetchMock.mock.calls.length).toBe(baselineCalls)
    store.dispose()
  })

  it('rejects five-cut ordering and cut ID inconsistency through recovery fetch and SSE', async () => {
    let resolveFetch!: (res: Response) => void
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse(makeSnapshot({ authority_revision: 6 })))
      .mockImplementationOnce(() => new Promise<Response>((resolve) => { resolveFetch = resolve }))
    vi.stubGlobal('fetch', fetchMock)
    vi.stubGlobal('EventSource', MockEventSource as unknown as typeof EventSource)

    const store = useStudioStore()
    await store.loadStudio()
    const eventSource = MockEventSource.latest!
    await vi.waitFor(() => expect(store.stream.status).toBe('OPEN'))

    eventSource.onerror?.()
    expect(store.stream.status).toBe('DEGRADED')

    // Cut IDs reversed [2, 1, 3, 4, 5]
    const reversedCuts = makeSnapshot({ authority_revision: 7 })
    const cut1 = reversedCuts.cuts[0]
    const cut2 = reversedCuts.cuts[1]
    reversedCuts.cuts[0] = cut2
    reversedCuts.cuts[1] = cut1

    eventSource.emit('snapshot-required', {
      schema: 'studio-event/v1',
      reason: 'revision-gap',
      authority_revision: 7,
    })
    resolveFetch(jsonResponse(reversedCuts))
    await vi.waitFor(() => expect(store.stream.resyncPending).toBe(false))

    expect(store.stream.status).toBe('DEGRADED')
    expect(store.hasCurrentSnapshot).toBe(false)
    expect(store.canMutateAuthority).toBe(false)
    expect(store.server?.authority_revision).toBe(6)

    // Cut ID 6 instead of 5 via SSE
    const invalidCutIdSnap = makeSnapshot({ authority_revision: 8 })
    invalidCutIdSnap.cuts[4] = { ...invalidCutIdSnap.cuts[4], cut_id: 6 as unknown as CutId }
    eventSource.emit('studio.snapshot', {
      schema: 'studio-event/v1',
      boot_id: 'b1',
      authority_revision: 8,
      snapshot: invalidCutIdSnap,
    })
    expect(store.stream.status).toBe('DEGRADED')
    expect(store.hasCurrentSnapshot).toBe(false)
    expect(store.canMutateAuthority).toBe(false)
    expect(store.server?.authority_revision).toBe(6)
    store.dispose()
  })

  it('rejects realization_complete inconsistency through recovery fetch and SSE', async () => {
    let resolveFetch!: (res: Response) => void
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse(makeSnapshot({ authority_revision: 6 })))
      .mockImplementationOnce(() => new Promise<Response>((resolve) => { resolveFetch = resolve }))
    vi.stubGlobal('fetch', fetchMock)
    vi.stubGlobal('EventSource', MockEventSource as unknown as typeof EventSource)

    const store = useStudioStore()
    await store.loadStudio()
    const eventSource = MockEventSource.latest!
    await vi.waitFor(() => expect(store.stream.status).toBe('OPEN'))

    eventSource.onerror?.()
    expect(store.stream.status).toBe('DEGRADED')

    // 1 cut STALE, but realization_complete claimed COMPLETE
    const staleWithComplete = makeSnapshot({ authority_revision: 7 })
    staleWithComplete.cuts[0] = { ...staleWithComplete.cuts[0], currency: 'STALE' }
    staleWithComplete.realization_complete = { complete: true, status: 'COMPLETE' }

    eventSource.emit('snapshot-required', {
      schema: 'studio-event/v1',
      reason: 'revision-gap',
      authority_revision: 7,
    })
    resolveFetch(jsonResponse(staleWithComplete))
    await vi.waitFor(() => expect(store.stream.resyncPending).toBe(false))

    expect(store.stream.status).toBe('DEGRADED')
    expect(store.hasCurrentSnapshot).toBe(false)
    expect(store.canMutateAuthority).toBe(false)
    expect(store.server?.authority_revision).toBe(6)

    // All 5 cuts CURRENT, but realization_complete claimed UNRESOLVED via SSE
    const currentWithUnresolved = makeSnapshot({ authority_revision: 8 })
    currentWithUnresolved.realization_complete = { complete: false, status: 'UNRESOLVED' }

    eventSource.emit('studio.snapshot', {
      schema: 'studio-event/v1',
      boot_id: 'b1',
      authority_revision: 8,
      snapshot: currentWithUnresolved,
    })
    expect(store.stream.status).toBe('DEGRADED')
    expect(store.hasCurrentSnapshot).toBe(false)
    expect(store.canMutateAuthority).toBe(false)
    expect(store.server?.authority_revision).toBe(6)
    store.dispose()
  })
})

describe('isStudioSnapshotDTO runtime validator unit tests', () => {
  it('accepts a fully valid StudioSnapshotDTO', () => {
    const snap = makeSnapshot()
    expect(isStudioSnapshotDTO(snap)).toBe(true)
    expect(validateStudioSnapshot(snap)).toBe(snap)
  })

  it('rejects incomplete object and primitive values', () => {
    expect(isStudioSnapshotDTO(null)).toBe(false)
    expect(isStudioSnapshotDTO(undefined)).toBe(false)
    expect(isStudioSnapshotDTO('snapshot')).toBe(false)
    expect(isStudioSnapshotDTO(123)).toBe(false)
    expect(isStudioSnapshotDTO([])).toBe(false)
    expect(isStudioSnapshotDTO({ schema_version: 4, authority_revision: 5 })).toBe(false)
    expect(() => validateStudioSnapshot({ schema_version: 4, authority_revision: 5 })).toThrow(
      'Invalid studio snapshot payload',
    )
  })

  it('rejects wrong schema_version or non-safe revision', () => {
    expect(isStudioSnapshotDTO({ ...makeSnapshot(), schema_version: 1 })).toBe(false)
    expect(isStudioSnapshotDTO({ ...makeSnapshot(), authority_revision: -1 })).toBe(false)
    expect(isStudioSnapshotDTO({ ...makeSnapshot(), authority_revision: 1.5 })).toBe(false)
    expect(isStudioSnapshotDTO({ ...makeSnapshot(), authority_revision: '10' })).toBe(false)
  })

  it('rejects cut counts other than 5 and cut IDs out of order', () => {
    const snap = makeSnapshot()
    const fourCuts = { ...snap, cuts: snap.cuts.slice(0, 4) }
    expect(isStudioSnapshotDTO(fourCuts)).toBe(false)

    const reversedCuts = makeSnapshot()
    const c0 = reversedCuts.cuts[0]
    reversedCuts.cuts[0] = reversedCuts.cuts[1]
    reversedCuts.cuts[1] = c0
    expect(isStudioSnapshotDTO(reversedCuts)).toBe(false)
  })

  it('rejects impossible cut null/currency shapes and realization_complete inconsistency', () => {
    // realized_revision is null but realized_asset_id is not null
    const badNullCut = makeSnapshot()
    badNullCut.cuts[0] = {
      ...badNullCut.cuts[0],
      realized_revision: null,
      realized_asset_id: 'asset-1',
      currency: 'STALE',
    }
    badNullCut.realization_complete = { complete: false, status: 'UNRESOLVED' }
    expect(isStudioSnapshotDTO(badNullCut)).toBe(false)

    // currency is CURRENT but desired_revision is null
    const badCurrentCut = makeSnapshot()
    badCurrentCut.cuts[0] = { ...badCurrentCut.cuts[0], desired_revision: null, currency: 'CURRENT' }
    expect(isStudioSnapshotDTO(badCurrentCut)).toBe(false)

    // realization_complete inconsistent with cuts' CURRENT status
    const inconsistentComplete = makeSnapshot()
    inconsistentComplete.cuts[0] = { ...inconsistentComplete.cuts[0], currency: 'STALE' }
    inconsistentComplete.realization_complete = { complete: true, status: 'COMPLETE' }
    expect(isStudioSnapshotDTO(inconsistentComplete)).toBe(false)

    const inconsistentUnresolved = makeSnapshot()
    inconsistentUnresolved.realization_complete = { complete: false, status: 'UNRESOLVED' }
    expect(isStudioSnapshotDTO(inconsistentUnresolved)).toBe(false)
  })

  it('rejects revision/currency and latest-job contradictions', () => {
    const mismatchedCurrent = makeSnapshot()
    mismatchedCurrent.cuts[0] = {
      ...mismatchedCurrent.cuts[0],
      desired_revision: 2,
      realized_revision: 1,
      currency: 'CURRENT',
    }
    expect(isStudioSnapshotDTO(mismatchedCurrent)).toBe(false)

    const latestJob = {
      job_id: 'job-latest',
      cut_id: 1 as CutId,
      target_desired_revision: 1,
      request_seq: 1,
      status: 'failed' as const,
      terminal_detail: 'provider failed',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
      attempts: [],
    }

    const failedLatestMarkedCurrent = makeSnapshot()
    failedLatestMarkedCurrent.cuts[0] = {
      ...failedLatestMarkedCurrent.cuts[0],
      latest_generation_request_seq: 1,
    }
    failedLatestMarkedCurrent.jobs = [latestJob]
    expect(isStudioSnapshotDTO(failedLatestMarkedCurrent)).toBe(false)

    const missingLatestJob = makeSnapshot()
    missingLatestJob.cuts[0] = {
      ...missingLatestJob.cuts[0],
      latest_generation_request_seq: 1,
      currency: 'STALE',
    }
    missingLatestJob.realization_complete = { complete: false, status: 'UNRESOLVED' }
    expect(isStudioSnapshotDTO(missingLatestJob)).toBe(false)

    const staleEqualRevision = makeSnapshot()
    staleEqualRevision.cuts[0] = {
      ...staleEqualRevision.cuts[0],
      latest_generation_request_seq: 1,
      currency: 'STALE',
    }
    staleEqualRevision.jobs = [latestJob]
    staleEqualRevision.realization_complete = { complete: false, status: 'UNRESOLVED' }
    expect(isStudioSnapshotDTO(staleEqualRevision)).toBe(true)
  })

  it('rejects invalid SHA-256 strings and invalid render_contract dimensions', () => {
    const badSha = makeSnapshot()
    badSha.composition = {
      ...badSha.composition,
      state: { ...DEFAULT_COMPOSITION, font_sha256: 'not-a-sha256' },
    }
    expect(isStudioSnapshotDTO(badSha)).toBe(false)

    const badDimensions = {
      ...makeSnapshot(),
      render_contract: { width: 800 as 1024, height: 600 as 7680, default_composition: DEFAULT_COMPOSITION },
    }
    expect(isStudioSnapshotDTO(badDimensions)).toBe(false)
  })
})

