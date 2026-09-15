/** useStudioStore — sole domain Pinia store. Plan §5 exact. */

import { defineStore } from 'pinia'
import { computed, reactive, ref } from 'vue'
import type {
  CutId,
  CutIntentDTO,
  CompositionStateDTO,
  BaselineStructureDTO,
  ReviewArtifactDTO,
  Sha256,
  StudioSnapshotDTO,
} from '@/api/contracts'
import {
  ApiError,
  fetchSnapshot,
  postBaseline,
  postCutIntent,
  putComposition,
  postGenerationJobs,
  postJobStop,
  postGlobalStop,
  postMaterializeReview,
  postAuthorize,
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
    state: 'connecting',
    gapFetchPending: false,
  })
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
    () => server.value !== null && !stream.gapFetchPending,
  )

  const realizationComplete = computed(() => {
    if (!server.value) return false
    return isRealizationComplete([...server.value.cuts])
  })

  const hasAnyDraft = computed(() => {
    return (
      drafts.composition !== null ||
      Object.keys(drafts.intents).length > 0 ||
      drafts.baseline !== null
    )
  })

  const hasAnySaveProblem = computed(() => {
    return Object.values(saves).some(
      (s) => s.state === 'pending' || s.state === 'failed' || s.state === 'conflict' || s.state === 'base-changed',
    )
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
      hasCurrentSnapshot.value &&
      realizationComplete.value &&
      !hasBlockingEdit.value
    )
  })

  const canGenerate = computed(() => {
    return hasCurrentSnapshot.value && !hasBlockingEdit.value && server.value?.baseline !== null
  })

  const canAuthorize = computed(() => {
    if (!ui.review || !server.value || !hasCurrentSnapshot.value || hasBlockingEdit.value) {
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

  // --- Internal helpers ---

  function applySnapshot(snap: StudioSnapshotDTO) {
    if (server.value && snap.authority_revision <= server.value.authority_revision) {
      return // monotonic — ignore older/equal
    }
    server.value = snap
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
  }

  function addToast(text: string, role: 'status' | 'alert' = 'status') {
    const t: ToastMessage = { id: nextToastId(), text, role, createdAt: Date.now() }
    toasts.push(t)
    setTimeout(() => {
      const idx = toasts.findIndex((x) => x.id === t.id)
      if (idx >= 0) toasts.splice(idx, 1)
    }, 6000)
  }

  // --- SSE ---
  let eventSource: { close(): void } | null = null

  function handleEvent(event: StudioEvent) {
    if (event.type === 'studio.snapshot') {
      applySnapshot(event.snapshot)
    } else if (event.type === 'snapshot-required') {
      if (!stream.gapFetchPending) {
        stream.gapFetchPending = true
        fetchSnapshot()
          .then((snap) => {
            applySnapshot(snap)
            stream.gapFetchPending = false
          })
          .catch(() => {
            stream.gapFetchPending = false
          })
      }
    }
  }

  function connectSSE() {
    eventSource = createStudioEventSource({
      onEvent: handleEvent,
      onStateChange: (s) => {
        stream.state = s
      },
    })
  }

  function disconnectSSE() {
    eventSource?.close()
    eventSource = null
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
  ) {
    if (authoritativeEditLane.inFlight) return // max in-flight = 1

    authoritativeEditLane.inFlight = { kind, draftKey, mutationId }
    saves[draftKey] = { state: 'pending', mutationId }

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
    if (authoritativeEditLane.inFlight) return
    if (!server.value) return

    // Priority: baseline > intent > composition
    if (drafts.baseline && !saveIsBlocked('baseline')) {
      saveBaselineDraft()
      return
    }
    for (const cid of [1, 2, 3, 4, 5] as CutId[]) {
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

  function setIntentDraft(cutId: CutId, intent: CutIntentDTO, enqueue = true) {
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

  function setBaselineDraft(structure: BaselineStructureDTO, intents: Array<{ cut_id: CutId; intent: CutIntentDTO }>, enqueue = true) {
    const mid = nextMutationId()
    drafts.baseline = {
      mutationId: mid,
      baseAuthorityRevision: server.value?.authority_revision ?? 0,
      localVersion: (drafts.baseline?.localVersion ?? 0) + 1,
      value: { structure, intents },
    }
    if (!saves['baseline'] || saves['baseline'].state === 'idle') {
      saves['baseline'] = { state: 'idle' }
    }
    if (enqueue) processNextLaneItem()
  }

  // --- Save dispatchers ---

  function saveBaselineDraft() {
    const draft = drafts.baseline
    if (!draft || !server.value || saveIsBlocked('baseline')) return
    const mid = draft.mutationId
    const baselineId = `bl_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
    dispatchEdit('baseline', 'baseline', mid, () =>
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

  function closeReview() {
    ui.review = null
  }

  // --- Selection ---

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
    realizationComplete,
    hasAnyDraft,
    hasAnySaveProblem,
    hasBlockingEdit,
    activeJobCount,
    canMaterializeReview,
    canGenerate,
    canAuthorize,
    // Actions
    loadStudio,
    setIntentDraft,
    setCompositionDraft,
    setBaselineDraft,
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
