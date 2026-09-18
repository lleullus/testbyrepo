import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useStudioStore } from '../src/store/studio'
import type { CompositionStateDTO, CutId, StudioSnapshotDTO } from '../src/api/contracts'

function makeSnapshot(cutIds: CutId[], authorityRevision: number): StudioSnapshotDTO {
  const slotHeight = 100
  const composition: CompositionStateDTO = {
    schema_version: 2,
    canvas_width_px: 1024,
    gap_px: 0,
    slot_heights_px: cutIds.map(() => slotHeight),
    fit: 'contain',
    font_sha256: '0'.repeat(64),
    bubbles: [],
  }
  const cuts = cutIds.map((cutId, index) => ({
    cut_id: cutId,
    display_order: index + 1,
    desired_revision: 1,
    latest_generation_request_seq: 0,
    effective_intent: {
      prompt: `prompt-${cutId}`,
      dialogue: `dialogue-${cutId}`,
      prompt_origin: 'user' as const,
    },
    realized_revision: 1,
    realized_asset_id: `asset-${cutId}`,
    realized_content_hash: '0'.repeat(64),
    realized_asset_url: `/api/cuts/${cutId}/realization?asset_id=asset-${cutId}&revision=1`,
    currency: 'CURRENT' as const,
  }))

  return {
    schema_version: 7,
    authority_revision: authorityRevision,
    baseline: {
      baseline_id: `baseline-${authorityRevision}`,
      structure: {
        source_brief: 'brief',
        cuts: cutIds.map((cutId) => ({ cut_id: cutId, role: 'role', beat: 'beat' })),
      },
      authority_revision: authorityRevision,
      created_at: '2026-09-18T00:00:00Z',
      intents: cutIds.map((cutId) => ({ cut_id: cutId, intent_revision: 1 })),
    },
    cuts,
    realization_complete: { complete: true, status: 'COMPLETE' },
    composition: {
      revision: 1,
      state: composition,
      updated_at: '2026-09-18T00:00:00Z',
    },
    render_contract: {
      width_px: 1024,
      height_px: cutIds.length * slotHeight,
      gap_px: 0,
      fit: 'contain',
      slots: cutIds.map((cutId, index) => ({
        cut_id: cutId,
        top_px: index * slotHeight,
        bottom_px: (index + 1) * slotHeight,
        height_px: slotHeight,
      })),
      default_composition: composition,
    },
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
  }
}

beforeEach(() => {
  setActivePinia(createPinia())
})

describe('inactive intent draft blocking', () => {
  it('does not let a retired cut draft or save conflict lock the studio', () => {
    const store = useStudioStore()
    store.server = makeSnapshot([2 as CutId, 7 as CutId], 1)
    store.setIntentDraft(7 as CutId, { prompt: 'local', dialogue: 'draft' }, false)
    store.saves['intent-7'] = {
      state: 'conflict',
      mutationId: store.drafts.intents[7]!.mutationId,
      message: 'conflict',
    }

    expect(store.hasAnyDraft).toBe(true)
    expect(store.hasAnySaveProblem).toBe(true)
    expect(store.hasBlockingEdit).toBe(true)

    expect(store.applySnapshot(makeSnapshot([2 as CutId], 2))).toBe(true)

    expect(store.drafts.intents[7]).toBeDefined()
    expect(store.hasAnyDraft).toBe(false)
    expect(store.hasAnySaveProblem).toBe(false)
    expect(store.hasBlockingEdit).toBe(false)
  })
})
