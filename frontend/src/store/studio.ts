/** useStudioStore — sole domain Pinia store. Plan §5 exact. */

import { defineStore } from 'pinia'
import { computed, reactive, ref } from 'vue'
import {
  type CutId,
  type CutIntentInputDTO,
  type CompositionStateDTO,
  type BaselineStructureDTO,
  type BaselineCutIntentInputDTO,
  type DraftGenerationResponseDTO,
  type ReviewArtifactDTO,
  type Sha256,
  type StudioSnapshotDTO,
  isStudioSnapshotDTO,
} from '@/api/contracts'
import {
  ApiError,
  fetchSnapshot,
  postBaseline,
  postAddCut,
  postRetireCut,
  postReorderCuts,
  postGenerateDraft,
  postCutIntent,
  putComposition,
  postGenerationJobs,
  postJobStop,
  postGlobalStop,
  postMaterializeReview,
  postAuthorize,
  postExportPng,
  postBloggerRelease,
  fetchArtifactMetadata,
} from '@/api/client'
import { createStudioEventSource } from '@/api/events'
import type { StudioEvent } from '@/api/events'
import type {
  StudioClientState,
  EditKind,
  ToastMessage,
  BaselineDraft,
  CompositionDraftPatch,
  SaveState,
} from './types'
import { isRealizationComplete, countActiveJobs, isJobStoppable } from '@/domain/currency'
import { ACTIVE_CUT_COUNT_MISMATCH_MESSAGE } from '@/domain/rebaseline'

let _toastCounter = 0
function nextMutationId(): string {
  return `m_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}
function nextToastId(): string {
  return `t_${++_toastCounter}`
}

export const useStudioStore = defineStore('studio', () => {
  // --- State ---
  const server = ref<StudioSnapshotDTO | null>(null)
  const drafts = reactive<StudioClientState['drafts']>({
    composition: null,
    intents: {},
    baseline: null,
  })
  const saves = reactive<Record<string, SaveState>>({})
  const authoritativeEditLane = reactive<StudioClientState['authoritativeEditLane']>({
    inFlight: null,
  })
  const jobsUi = reactive<Record<string, { stopRequested: boolean }>>({})
  const selection = reactive<StudioClientState['selection']>({ cutId: 1 as CutId })
  const stream = reactive<StudioClientState['stream']>({
    status: 'CONNECTING',
    resyncPending: false,
    lastEventId: undefined,
  })
  const resyncRequired = ref(false)
  const transportOpen = ref(false)
  let minRequiredRevision = 0
  let inFlightResync: Promise<void> | null = null
  const narrowMedia = typeof window === 'undefined'
    ? null
    : window.matchMedia('(max-width: 1099px)')
  const panelsInitiallyOpen = narrowMedia?.matches !== true
  const ui = reactive<StudioClientState['ui']>({
    leftOpen: panelsInitiallyOpen,
    rightOpen: panelsInitiallyOpen,
    queueOpen: false,
    review: null,
  })
  const toasts = reactive<ToastMessage[]>([])

  // --- Computed selectors ---
  const hasCurrentSnapshot = computed(
    () =>
      server.value !== null &&
      stream.status === 'OPEN' &&
      !resyncRequired.value &&
      !stream.resyncPending,
  )

  const canMutateAuthority = computed(() => hasCurrentSnapshot.value)
  const realizationComplete = computed(() => {
    if (!server.value) return false
    return isRealizationComplete([...server.value.cuts])
  })
  const activeCutIds = computed(
    () => new Set((server.value?.cuts ?? []).map((cut) => cut.cut_id)),
  )

  const hasAnyDraft = computed(() => {
    const hasActiveIntentDraft = Object.keys(drafts.intents).some((cid) =>
      activeCutIds.value.has(Number(cid) as CutId),
    )
    return (
      drafts.composition !== null ||
      hasActiveIntentDraft ||
      drafts.baseline !== null
    )
  })

  const hasAnySaveProblem = computed(() => {
    return Object.entries(saves).some(([key, save]) => {
      if (key.startsWith('intent-')) {
        const cutId = Number(key.slice('intent-'.length)) as CutId
        if (!activeCutIds.value.has(cutId)) return false
      }
      return save.state === 'pending' || save.state === 'failed' || save.state === 'conflict' || save.state === 'base-changed'
    })
  })

  const hasBlockingEdit = computed(() => {
    return hasAnyDraft.value || hasAnySaveProblem.value || authoritativeEditLane.inFlight !== null
  })

  const activeJobCount = computed(() => {
    if (!server.value) return 0
    return countActiveJobs(server.value)
  })

  const canMaterializeReview = computed(() => {
    return (
      canMutateAuthority.value &&
      realizationComplete.value &&
      !hasBlockingEdit.value
    )
  })

  const canGenerate = computed(() => {
    return canMutateAuthority.value && !hasBlockingEdit.value && Boolean(server.value?.baseline)
  })
  const canAuthorize = computed(() => {
    if (!ui.review || !server.value || !canMutateAuthority.value || hasBlockingEdit.value) {
      return false
    }
    const displayed = ui.review
    const artifact = displayed.artifact
    const registered = server.value.review_artifacts.some(
      (candidate) =>
        candidate.artifact_id === artifact.artifact_id &&
        candidate.content_hash === displayed.displayedByteHash &&
        candidate.composition_revision === artifact.composition_revision,
    )
    if (
      !registered ||
      displayed.displayedByteHash !== artifact.content_hash ||
      server.value.composition.revision !== artifact.composition_revision
    ) {
      return false
    }
    return artifact.cuts.every((artifactCut) => {
      const current = server.value!.cuts.find((cut) => cut.cut_id === artifactCut.cut_id)
      return (
        current?.currency === 'CURRENT' &&
        current.desired_revision === artifactCut.desired_revision &&
        current.realized_revision === artifactCut.realized_revision &&
        current.realized_asset_id === artifactCut.asset_id
      )
    })
  })

  const canRelease = computed(() => {
    if (!server.value || !canMutateAuthority.value || hasBlockingEdit.value) {
      return false
    }
    const activeAuth = server.value.release_authorization?.active
    if (!activeAuth || activeAuth.revoked_authority_revision != null) {
      return false
    }
    return server.value.cuts.every((cut) => cut.currency === 'CURRENT')
  })

  // --- Internal helpers ---
  function recoverSelection(snapshot: StudioSnapshotDTO) {
    if (!snapshot.cuts.some((cut) => cut.cut_id === selection.cutId)) {
      selection.cutId = snapshot.cuts[0].cut_id
      selection.bubbleId = undefined
    }
  }


  function applySnapshot(snap: unknown): boolean {
    if (!isStudioSnapshotDTO(snap)) {
      return false
    }
    if (server.value) {
      if (snap.authority_revision < server.value.authority_revision) {
        return false // monotonic — ignore older
      }
      if (snap.authority_revision === server.value.authority_revision) {
        if (snap.composition.revision > server.value.composition.revision) {
          server.value = snap
          return true
        }
        return true // acceptable/current, do not reapply or change drafts
      }
    }
    server.value = snap
    recoverSelection(snap)
    const snapshotActiveCutIds = new Set(snap.cuts.map((cut) => cut.cut_id))
    // Mark any affected draft as base-changed if the server moved ahead
    if (drafts.composition) {
      const draftBaseRev = drafts.composition.baseAuthorityRevision
      if (snap.authority_revision > draftBaseRev) {
        const key = `composition`
        if (saves[key]?.state !== 'failed' && saves[key]?.state !== 'conflict') {
          saves[key] = { state: 'base-changed', mutationId: drafts.composition.mutationId }
        }
      }
    }
    for (const [cidStr, draft] of Object.entries(drafts.intents)) {
      const cutId = Number(cidStr) as CutId
      if (!snapshotActiveCutIds.has(cutId)) continue
      if (draft && snap.authority_revision > draft.baseAuthorityRevision) {
        const key = `intent-${cidStr}`
        if (saves[key]?.state !== 'failed' && saves[key]?.state !== 'conflict') {
          saves[key] = { state: 'base-changed', mutationId: draft.mutationId }
        }
      }
    }
    if (drafts.baseline) {
      if (snap.authority_revision > drafts.baseline.baseAuthorityRevision) {
        const key = `baseline`
        if (saves[key]?.state !== 'failed' && saves[key]?.state !== 'conflict') {
          saves[key] = { state: 'base-changed', mutationId: drafts.baseline.mutationId }
        }
      }
    }
    return true
  }

  function addToast(text: string, role: 'status' | 'alert' = 'status') {
    const t: ToastMessage = { id: nextToastId(), text, role, createdAt: Date.now() }
    toasts.push(t)
    setTimeout(() => {
      const idx = toasts.findIndex((x) => x.id === t.id)
      if (idx >= 0) toasts.splice(idx, 1)
    }, 6000)
  }

  // --- Recovery & SSE ---
  let eventSource: { close(): void } | null = null

  function requestResync(): Promise<void> {
    if (inFlightResync) return inFlightResync

    stream.resyncPending = true
    inFlightResync = (async () => {
      try {
        const snap = await fetchSnapshot()
        if (snap.authority_revision < minRequiredRevision) {
          return
        }
        const accepted = applySnapshot(snap)
        if (accepted && snap.authority_revision >= minRequiredRevision) {
          minRequiredRevision = Math.max(minRequiredRevision, snap.authority_revision)
          if (transportOpen.value) {
            resyncRequired.value = false
            stream.status = 'OPEN'
          }
        }
      } catch {
        // recovery failure: clear only resyncPending; remain DEGRADED and latched
      } finally {
        stream.resyncPending = false
        inFlightResync = null
      }
    })()

    return inFlightResync
  }

  function handleEvent(event: StudioEvent) {
    if (event.type === 'studio.snapshot') {
      const snap = event.snapshot
      if (
        !snap ||
        !isStudioSnapshotDTO(snap) ||
        event.authority_revision !== snap.authority_revision
      ) {
        return
      }
      const currentRev = server.value?.authority_revision ?? 0
      if (snap.authority_revision < currentRev || snap.authority_revision < minRequiredRevision) {
        return
      }
      const accepted = applySnapshot(snap)
      if (accepted) {
        minRequiredRevision = Math.max(minRequiredRevision, snap.authority_revision)
        if (transportOpen.value) {
          resyncRequired.value = false
          stream.status = 'OPEN'
        }
      }
    } else if (event.type === 'snapshot-required') {
      stream.status = 'DEGRADED'
      resyncRequired.value = true
      minRequiredRevision = Math.max(minRequiredRevision, event.authority_revision)
      requestResync()
    }
  }

  function handleTransportState(s: 'connecting' | 'open' | 'reconnecting') {
    if (s === 'open') {
      transportOpen.value = true
      if (resyncRequired.value) {
        stream.status = 'DEGRADED'
        requestResync()
      } else {
        stream.status = 'OPEN'
      }
    } else if (s === 'reconnecting') {
      transportOpen.value = false
      stream.status = 'DEGRADED'
      resyncRequired.value = true
    } else if (s === 'connecting') {
      transportOpen.value = false
      if (resyncRequired.value) {
        stream.status = 'DEGRADED'
      } else {
        stream.status = 'CONNECTING'
      }
    }
  }

  function connectSSE() {
    eventSource = createStudioEventSource({
      onEvent: handleEvent,
      onStateChange: handleTransportState,
    })
  }

  function disconnectSSE() {
    eventSource?.close()
    eventSource = null
    transportOpen.value = false
    stream.status = 'DEGRADED'
    resyncRequired.value = true
  }

  let responsiveListenerAttached = false

  function handleResponsiveChange(event: MediaQueryListEvent) {
    if (event.matches && ui.leftOpen && ui.rightOpen) {
      ui.rightOpen = false
    }
  }

  // --- Initial load ---
  async function loadStudio() {
    const snap = await fetchSnapshot()
    server.value = snap
    recoverSelection(snap)
    minRequiredRevision = snap.authority_revision
    if (narrowMedia && !responsiveListenerAttached) {
      narrowMedia.addEventListener('change', handleResponsiveChange)
      responsiveListenerAttached = true
    }
    connectSSE()
  }

  // --- Authoritative Edit Lane (§5.2) ---

  async function dispatchEdit(
    kind: EditKind,
    draftKey: string,
    mutationId: string,
    execute: () => Promise<{ accepted_mutation_id: string; snapshot: StudioSnapshotDTO }>,
  ): Promise<boolean> {
    if (!canMutateAuthority.value) {
      addToast('재동기화가 필요합니다. 연결 및 스냅샷 복구 후 다시 시도하세요.', 'alert')
      return false
    }
    if (authoritativeEditLane.inFlight) return false // max in-flight = 1

    authoritativeEditLane.inFlight = { kind, draftKey, mutationId }
    saves[draftKey] = { state: 'pending', mutationId }
    let accepted = false

    try {
      const result = await execute()

      // Apply fresh snapshot
      applySnapshot(result.snapshot)

      const currentMutationId = getCurrentDraftMutationId(kind, draftKey)
      if (
        result.accepted_mutation_id === mutationId &&
        currentMutationId === mutationId
      ) {
        clearDraft(kind, draftKey)
        delete saves[draftKey]
        if (kind === 'baseline' && result.snapshot.composition.state === null) {
          setCompositionDraft(result.snapshot.render_contract.default_composition)
        }
        accepted = true
      } else if (
        result.accepted_mutation_id === mutationId &&
        currentMutationId !== undefined
      ) {
        // A newer self-originated draft continues from this accepted response.
        rebaseCurrentDraft(kind, draftKey, result.snapshot)
        saves[draftKey] = { state: 'idle' }
      } else if (currentMutationId === undefined) {
        delete saves[draftKey]
      } else {
        saves[draftKey] = {
          state: 'failed',
          mutationId: currentMutationId,
          message: '저장 응답의 mutation identity가 일치하지 않습니다.',
        }
      }
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 409 && err.currentSnapshot) {
          applySnapshot(err.currentSnapshot)
          saves[draftKey] = {
            state: 'conflict',
            mutationId,
            message: err.body.message || '다른 사용자가 먼저 저장했습니다.',
          }
          addToast('저장 충돌 — 서버 값을 확인하세요.', 'alert')
        } else {
          saves[draftKey] = {
            state: 'failed',
            mutationId,
            message: err.body.message || '저장 실패',
          }
          addToast('저장 실패 — 변경 내용은 이 브라우저에만 남아 있습니다.', 'alert')
        }
      } else {
        saves[draftKey] = {
          state: 'failed',
          mutationId,
          message: '네트워크 오류',
        }
        addToast('저장 실패 — 변경 내용은 이 브라우저에만 남아 있습니다.', 'alert')
      }
    } finally {
      authoritativeEditLane.inFlight = null
      // Check if there's a newer draft waiting to be saved
      processNextLaneItem()
    }
    return accepted
  }

  function getCurrentDraftMutationId(kind: EditKind, draftKey: string): string | undefined {
    if (kind === 'baseline') return drafts.baseline?.mutationId
    if (kind === 'composition') return drafts.composition?.mutationId
    const cutId = parseInt(draftKey.replace('intent-', ''), 10) as CutId
    return drafts.intents[cutId]?.mutationId
  }

  function rebaseCurrentDraft(
    kind: EditKind,
    draftKey: string,
    snapshot: StudioSnapshotDTO,
  ) {
    if (kind === 'baseline' && drafts.baseline) {
      drafts.baseline.baseAuthorityRevision = snapshot.authority_revision
      return
    }
    if (kind === 'composition' && drafts.composition) {
      drafts.composition.baseAuthorityRevision = snapshot.authority_revision
      drafts.composition.baseCompositionRevision = snapshot.composition.revision
      return
    }
    if (kind === 'intent') {
      const cutId = parseInt(draftKey.replace('intent-', ''), 10) as CutId
      const draft = drafts.intents[cutId]
      if (draft) draft.baseAuthorityRevision = snapshot.authority_revision
    }
  }

  function saveIsBlocked(draftKey: string): boolean {
    const state = saves[draftKey]?.state
    return state === 'failed' || state === 'conflict' || state === 'base-changed'
  }

  function clearDraft(kind: EditKind, draftKey: string) {
    switch (kind) {
      case 'baseline':
        drafts.baseline = null
        break
      case 'intent': {
        const cid = parseInt(draftKey.replace('intent-', ''), 10) as CutId
        delete drafts.intents[cid]
        break
      }
      case 'composition':
        drafts.composition = null
        break
    }
  }

  function processNextLaneItem() {
    if (!canMutateAuthority.value) return
    if (authoritativeEditLane.inFlight) return
    if (!server.value) return

    // Priority: baseline > intent > composition
    if (drafts.baseline && !saveIsBlocked('baseline')) {
      saveBaselineDraft()
      return
    }
    for (const cid of (server.value.cuts.map((cut) => cut.cut_id) as CutId[])) {
      const draft = drafts.intents[cid]
      const key = `intent-${cid}`
      if (draft && !saveIsBlocked(key)) {
        saveIntentDraft(cid)
        return
      }
    }
    if (drafts.composition && !saveIsBlocked('composition')) {
      saveCompositionDraft()
    }
  }

  // --- Draft mutations (user edits) ---

  function setIntentDraft(cutId: CutId, intent: CutIntentInputDTO, enqueue = true) {
    const existing = drafts.intents[cutId]
    const mid = nextMutationId()
    drafts.intents[cutId] = {
      mutationId: mid,
      baseAuthorityRevision: server.value?.authority_revision ?? 0,
      localVersion: (existing?.localVersion ?? 0) + 1,
      value: intent,
    }
    // Clear any stale save state
    const key = `intent-${cutId}`
    if (!saves[key] || saves[key].state === 'idle') {
      saves[key] = { state: 'idle' }
    }
    if (enqueue) processNextLaneItem()
  }

  function setCompositionDraft(state: CompositionStateDTO, enqueue = true) {
    const existing = drafts.composition
    const mid = nextMutationId()
    drafts.composition = {
      mutationId: mid,
      baseAuthorityRevision: server.value?.authority_revision ?? 0,
      baseCompositionRevision: server.value?.composition.revision ?? 0,
      localVersion: (existing?.localVersion ?? 0) + 1,
      value: { state },
    }
    if (!saves['composition'] || saves['composition'].state === 'idle') {
      saves['composition'] = { state: 'idle' }
    }
    if (enqueue) processNextLaneItem()
  }
  function setBaselineDraft(
    structure: BaselineStructureDTO,
    intents: Array<{ cut_id: CutId; intent: CutIntentInputDTO | BaselineCutIntentInputDTO }>,
    enqueue = true,
  ) {
    const mid = nextMutationId()
    const normalizedIntents: BaselineDraft['intents'] = intents.map(({ cut_id, intent }) => ({
      cut_id,
      intent: {
        prompt: intent.prompt,
        dialogue: intent.dialogue,
        prompt_origin: 'prompt_origin' in intent ? intent.prompt_origin : 'user',
      },
    }))
    drafts.baseline = {
      mutationId: mid,
      baseAuthorityRevision: server.value?.authority_revision ?? 0,
      localVersion: (drafts.baseline?.localVersion ?? 0) + 1,
      value: { structure, intents: normalizedIntents },
    }
    if (!saves['baseline'] || saves['baseline'].state === 'idle') {
      saves['baseline'] = { state: 'idle' }
    }
    if (enqueue) processNextLaneItem()
  }
  async function generateBaselineDraft(
    topic: string,
    cutCount = 5,
    shouldApply?: () => boolean,
  ): Promise<DraftGenerationResponseDTO | null> {
    if (!topic.trim()) {
      throw new Error('주제 또는 시놉시스를 입력하세요.')
    }

    const result = await postGenerateDraft({ topic, cut_count: cutCount })
    if (result.cut_count < 1 || result.cuts.length !== result.cut_count) {
      throw new Error('Studio baseline draft must contain a non-empty dynamic cut set')
    }
    if (server.value?.baseline && server.value.cuts.length !== result.cut_count) {
      throw new Error(ACTIVE_CUT_COUNT_MISMATCH_MESSAGE)
    }
    if (shouldApply && !shouldApply()) {
      addToast('입력이 변경되어 생성 결과를 적용하지 않았습니다.', 'alert')
      return null
    }
    const activeIds = server.value?.baseline
      ? server.value.cuts.map((cut) => cut.cut_id)
      : result.cuts.map((cut) => cut.display_order)
    const structure: BaselineStructureDTO = {
      source_brief: result.source_brief,
      cuts: result.cuts.map((cut, index) => ({
        cut_id: activeIds[index] as CutId,
        role: cut.role,
        beat: cut.beat,
      })),
    }
    const intents = result.cuts.map((cut, index) => ({
      cut_id: activeIds[index] as CutId,
      intent: {
        prompt: cut.prompt,
        dialogue: cut.dialogue,
        prompt_origin: 'llm_draft' as const,
      },
    }))
    setBaselineDraft(structure, intents, false)
    addToast('초안이 생성되었습니다. 검토 후 승인하세요.', 'status')
    return result
  }

  // --- Save dispatchers ---

  async function saveBaselineDraft(): Promise<boolean> {
    const draft = drafts.baseline
    if (!draft || !server.value || saveIsBlocked('baseline')) return false
    if (!canMutateAuthority.value) {
      addToast('재동기화가 필요합니다. 연결 및 스냅샷 복구 후 다시 시도하세요.', 'alert')
      return false
    }
    const mid = draft.mutationId
    const baselineId = `bl_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
    return dispatchEdit('baseline', 'baseline', mid, () =>
      postBaseline({
        expected_authority_revision: draft.baseAuthorityRevision,
        mutation_id: mid,
        baseline_id: baselineId,
        structure: draft.value.structure,
        intents: draft.value.intents,
      }),
    )
  }

  function saveIntentDraft(cutId: CutId) {
    const draft = drafts.intents[cutId]
    if (!draft || !server.value || saveIsBlocked(`intent-${cutId}`)) return
    if (!canMutateAuthority.value) {
      addToast('재동기화가 필요합니다. 연결 및 스냅샷 복구 후 다시 시도하세요.', 'alert')
      return
    }
    const mid = draft.mutationId
    dispatchEdit('intent', `intent-${cutId}`, mid, () =>
      postCutIntent(cutId, {
        expected_authority_revision: draft.baseAuthorityRevision,
        mutation_id: mid,
        intent: draft.value,
      }),
    )
  }

  function saveCompositionDraft() {
    const draft = drafts.composition
    if (!draft || !server.value || saveIsBlocked('composition')) return
    if (!canMutateAuthority.value) {
      addToast('재동기화가 필요합니다. 연결 및 스냅샷 복구 후 다시 시도하세요.', 'alert')
      return
    }
    const mid = draft.mutationId
    dispatchEdit('composition', 'composition', mid, () =>
      putComposition({
        expected_authority_revision: draft.baseAuthorityRevision,
        expected_composition_revision: draft.baseCompositionRevision,
        mutation_id: mid,
        state: draft.value.state,
      }),
    )
  }

  // --- Retry / Reconcile ---

  function retrySave(draftKey: string) {
    const saveState = saves[draftKey]
    if (!saveState || (saveState.state !== 'failed' && saveState.state !== 'conflict' && saveState.state !== 'base-changed')) return
    if (!canMutateAuthority.value) {
      addToast('재동기화가 필요합니다. 연결 및 스냅샷 복구 후 다시 시도하세요.', 'alert')
      return
    }
    delete saves[draftKey]
    if (draftKey === 'baseline') {
      if (drafts.baseline) {
        drafts.baseline.mutationId = nextMutationId()
        drafts.baseline.baseAuthorityRevision = server.value?.authority_revision ?? 0
      }
    } else if (draftKey === 'composition') {
      if (drafts.composition) {
        drafts.composition.mutationId = nextMutationId()
        drafts.composition.baseAuthorityRevision = server.value?.authority_revision ?? 0
        drafts.composition.baseCompositionRevision = server.value?.composition.revision ?? 0
      }
    } else if (draftKey.startsWith('intent-')) {
      const cid = parseInt(draftKey.replace('intent-', ''), 10) as CutId
      const d = drafts.intents[cid]
      if (d) {
        d.mutationId = nextMutationId()
        d.baseAuthorityRevision = server.value?.authority_revision ?? 0
      }
    }
    processNextLaneItem()
  }

  function discardDraft(draftKey: string) {
    delete saves[draftKey]
    if (draftKey === 'baseline') drafts.baseline = null
    else if (draftKey === 'composition') drafts.composition = null
    else if (draftKey.startsWith('intent-')) {
      const cid = parseInt(draftKey.replace('intent-', ''), 10) as CutId
      delete drafts.intents[cid]
    }
  }

  // --- Commands (bypass edit lane) ---

  async function stopJob(jobId: string) {
    jobsUi[jobId] = { stopRequested: true }
    try {
      const result = await postJobStop(jobId)
      applySnapshot(result.snapshot)
    } catch (err) {
      if (err instanceof ApiError && err.currentSnapshot) {
        applySnapshot(err.currentSnapshot)
      }
      addToast('작업 중지 실패', 'alert')
    }
  }

  async function stopAll() {
    // Mark all active jobs as stop-requested
    if (server.value) {
      for (const job of server.value.jobs) {
        if (isJobStoppable(job.status)) {
          jobsUi[job.job_id] = { stopRequested: true }
        }
      }
    }
    try {
      const result = await postGlobalStop()
      applySnapshot(result.snapshot)
    } catch (err) {
      if (err instanceof ApiError && err.currentSnapshot) {
        applySnapshot(err.currentSnapshot)
      }
      addToast('전체 중지 실패', 'alert')
    }
  }

  async function generateAll() {
    if (!canGenerate.value || !server.value) return
    try {
      const result = await postGenerationJobs({
        expected_authority_revision: server.value.authority_revision,
        cut_id: null,
      })
      applySnapshot(result.snapshot)
    } catch (err) {
      if (err instanceof ApiError && err.currentSnapshot) {
        applySnapshot(err.currentSnapshot)
      }
      addToast('생성 요청 실패', 'alert')
    }
  }

  async function generateCut(cutId: CutId) {
    if (!canGenerate.value || !server.value) return
    try {
      const result = await postGenerationJobs({
        expected_authority_revision: server.value.authority_revision,
        cut_id: cutId,
      })
      applySnapshot(result.snapshot)
    } catch (err) {
      if (err instanceof ApiError && err.currentSnapshot) {
        applySnapshot(err.currentSnapshot)
      }
      addToast('생성 요청 실패', 'alert')
    }
  }

  async function materializeReview() {
    if (!canMaterializeReview.value || !server.value) return
    try {
      const result = await postMaterializeReview({
        expected_authority_revision: server.value.authority_revision,
        expected_composition_revision: server.value.composition.revision,
      })
      applySnapshot(result.snapshot)
      // Open review modal with artifact data
      const artifact = result.artifact
      // Fetch the actual PNG bytes hash via the content endpoint
      const resp = await fetch(`/api/review-artifacts/${artifact.artifact_id}/content`)
      if (!resp.ok) {
        addToast('검토물 로드 실패', 'alert')
        return
      }
      const blob = await resp.blob()
      const arrayBuf = await blob.arrayBuffer()
      const hashHex = await computeSha256Hex(arrayBuf)
      ui.review = {
        artifact,
        displayedByteHash: hashHex,
        zoom: 1,
      }
    } catch (err) {
      if (err instanceof ApiError && err.currentSnapshot) {
        applySnapshot(err.currentSnapshot)
      }
      addToast('검토물 생성 실패', 'alert')
    }
  }

  async function authorizeReview() {
    if (!canAuthorize.value || !ui.review || !server.value) return
    const { artifact, displayedByteHash } = ui.review
    try {
      const result = await postAuthorize(artifact.artifact_id, {
        expected_authority_revision: server.value.authority_revision,
        content_hash: displayedByteHash,
      })
      applySnapshot(result.snapshot)
      ui.review = null
      addToast('승인 요청이 전송되었습니다.', 'status')
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.currentSnapshot) applySnapshot(err.currentSnapshot)
        if (err.code === 'artifact_not_current') {
          addToast('표시된 검토물이 최신이 아닙니다. 다시 생성하세요.', 'alert')
          ui.review = null
        } else {
          addToast('승인 실패: ' + err.body.message, 'alert')
        }
      } else {
        addToast('승인 실패', 'alert')
      }
    }
  }

  async function exportPng() {
    if (!canRelease.value || !server.value) {
      if (hasBlockingEdit.value) {
        addToast('저장되지 않은 편집 내용이 있어 내보낼 수 없습니다.', 'alert')
      } else {
        addToast('릴리즈 권한이 없거나 컷이 최신 상태가 아닙니다.', 'alert')
      }
      return
    }
    try {
      const result = await postExportPng({
        expected_authority_revision: server.value.authority_revision,
      })
      applySnapshot(result.snapshot)
      addToast(`PNG 파일이 성공적으로 내보내졌습니다 (${result.bytes_written} bytes)`, 'status')
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.currentSnapshot) applySnapshot(err.currentSnapshot)
        addToast(`내보내기 실패: ${err.body.message}`, 'alert')
      } else {
        addToast('PNG 내보내기 실패', 'alert')
      }
    }
  }

  async function releaseBlogger() {
    if (!canRelease.value || !server.value) {
      if (hasBlockingEdit.value) {
        addToast('저장되지 않은 편집 내용이 있어 발행할 수 없습니다.', 'alert')
      } else {
        addToast('릴리즈 권한이 없거나 컷이 최신 상태가 아닙니다.', 'alert')
      }
      return
    }
    try {
      const result = await postBloggerRelease({
        expected_authority_revision: server.value.authority_revision,
      })
      applySnapshot(result.snapshot)
      if (result.outcome === 'confirmed_success') {
        addToast(`Blogger 발행 성공: ${result.destination_url || result.destination_id}`, 'status')
      } else if (result.outcome === 'unknown') {
        addToast('Blogger 발행 결과 미확인 (Unknown): 외부 서비스 응답 타임아웃', 'alert')
      } else {
        addToast('Blogger 발행 거절 또는 실패', 'alert')
      }
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.currentSnapshot) applySnapshot(err.currentSnapshot)
        addToast(`Blogger 발행 실패: ${err.body.message}`, 'alert')
      } else {
        addToast('Blogger 발행 실패', 'alert')
      }
    }
  }

  function closeReview() {
    ui.review = null
  }

  async function addCut(position?: number) {
    if (!canMutateAuthority.value || !server.value?.baseline) return
    try {
      const result = await postAddCut({
        expected_authority_revision: server.value.authority_revision,
        mutation_id: nextMutationId(),
        baseline_id: server.value.baseline.baseline_id,
        role: '새 장면',
        beat: '새 컷의 전개',
        position,
      })
      applySnapshot(result.snapshot)
    } catch (err) {
      if (err instanceof ApiError && err.currentSnapshot) applySnapshot(err.currentSnapshot)
      addToast('컷 추가 실패', 'alert')
    }
  }

  async function retireCut(cutId: CutId) {
    if (!canMutateAuthority.value || !server.value?.baseline || server.value.cuts.length <= 1) return
    try {
      const result = await postRetireCut(cutId, {
        expected_authority_revision: server.value.authority_revision,
        mutation_id: nextMutationId(),
        baseline_id: server.value.baseline.baseline_id,
      })
      applySnapshot(result.snapshot)
      delete drafts.intents[cutId]
      delete saves[`intent-${cutId}`]
      if (selection.cutId === cutId) selectCut(result.snapshot.cuts[0].cut_id)
    } catch (err) {
      if (err instanceof ApiError && err.currentSnapshot) applySnapshot(err.currentSnapshot)
      addToast('컷 비활성화 실패', 'alert')
    }
  }

  async function reorderCuts(orderedCutIds: CutId[]) {
    if (!canMutateAuthority.value || !server.value?.baseline) return
    try {
      const result = await postReorderCuts({
        expected_authority_revision: server.value.authority_revision,
        mutation_id: nextMutationId(),
        baseline_id: server.value.baseline.baseline_id,
        ordered_cut_ids: orderedCutIds,
      })
      applySnapshot(result.snapshot)
    } catch (err) {
      if (err instanceof ApiError && err.currentSnapshot) applySnapshot(err.currentSnapshot)
      addToast('컷 순서 변경 실패', 'alert')
    }
  }

  function selectCut(cutId: CutId) {
    selection.cutId = cutId
    selection.bubbleId = undefined
  }

  function selectBubble(bubbleId: string) {
    selection.bubbleId = bubbleId
  }

  // --- UI toggles ---
  function toggleLeft() {
    ui.leftOpen = !ui.leftOpen
    if (ui.leftOpen && narrowMedia?.matches) ui.rightOpen = false
  }

  function toggleRight() {
    ui.rightOpen = !ui.rightOpen
    if (ui.rightOpen && narrowMedia?.matches) ui.leftOpen = false
  }

  function toggleQueue() { ui.queueOpen = !ui.queueOpen }

  // --- Cleanup ---
  function dispose() {
    disconnectSSE()
    if (narrowMedia && responsiveListenerAttached) {
      narrowMedia.removeEventListener('change', handleResponsiveChange)
      responsiveListenerAttached = false
    }
  }

  return {
    // State
    server,
    drafts,
    saves,
    authoritativeEditLane,
    jobsUi,
    selection,
    stream,
    ui,
    toasts,
    // Computed
    hasCurrentSnapshot,
    canMutateAuthority,
    realizationComplete,
    hasAnyDraft,
    hasAnySaveProblem,
    hasBlockingEdit,
    activeJobCount,
    canMaterializeReview,
    canGenerate,
    canAuthorize,
    canRelease,
    // Actions
    loadStudio,
    setIntentDraft,
    setCompositionDraft,
    setBaselineDraft,
    generateBaselineDraft,
    saveBaselineDraft,
    saveIntentDraft,
    saveCompositionDraft,
    retrySave,
    discardDraft,
    stopJob,
    stopAll,
    generateAll,
    generateCut,
    materializeReview,
    authorizeReview,
    addCut,
    retireCut,
    reorderCuts,
    exportPng,
    releaseBlogger,
    closeReview,
    selectCut,
    selectBubble,
    toggleLeft,
    toggleRight,
    toggleQueue,
    applySnapshot,
    dispose,
    // Exposed for tests
    processNextLaneItem,
    requestResync,
  }
})

/** Compute SHA-256 hex string from bytes using Web Crypto API. */
async function computeSha256Hex(data: ArrayBuffer): Promise<string> {
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = new Uint8Array(hashBuffer)
  return Array.from(hashArray)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}
