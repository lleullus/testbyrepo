/** Client state types — Plan §5.1 exact shape */

import type {
  CutId,
  CutIntentDTO,
  CompositionStateDTO,
  BaselineStructureDTO,
  ReviewArtifactDTO,
  Sha256,
  StudioSnapshotDTO,
} from '@/api/contracts'

export type EditKind = 'baseline' | 'intent' | 'composition'

export interface EditDraft<T> {
  mutationId: string
  baseAuthorityRevision: number
  localVersion: number
  value: T
}

export interface CompositionDraftPatch {
  /** Full composition state snapshot as edited locally */
  state: CompositionStateDTO
}

export interface BaselineDraft {
  structure: BaselineStructureDTO
  intents: Array<{ cut_id: CutId; intent: CutIntentDTO }>
}

export type SaveState =
  | { state: 'idle' }
  | { state: 'pending'; mutationId: string }
  | { state: 'failed'; mutationId: string; message: string }
  | { state: 'conflict'; mutationId: string; message: string }
  | { state: 'base-changed'; mutationId: string }

export interface ToastMessage {
  id: string
  text: string
  role: 'status' | 'alert'
  createdAt: number
}

export interface StudioClientState {
  server: StudioSnapshotDTO | null
  drafts: {
    composition: (EditDraft<CompositionDraftPatch> & { baseCompositionRevision: number }) | null
    intents: Partial<Record<CutId, EditDraft<CutIntentDTO>>>
    baseline: EditDraft<BaselineDraft> | null
  }
  saves: Record<string, SaveState>
  authoritativeEditLane: {
    inFlight: null | { kind: EditKind; draftKey: string; mutationId: string }
  }
  jobsUi: Record<string, { stopRequested: boolean }>
  selection: { cutId: CutId; bubbleId?: string }
  stream: {
    state: 'connecting' | 'open' | 'reconnecting'
    lastEventId?: string
    gapFetchPending: boolean
  }
  ui: {
    leftOpen: boolean
    rightOpen: boolean
    queueOpen: boolean
    review: null | {
      artifact: ReviewArtifactDTO
      displayedByteHash: Sha256
      zoom: number
    }
  }
  toasts: ToastMessage[]
}
