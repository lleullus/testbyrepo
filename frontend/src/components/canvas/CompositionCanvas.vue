<script setup lang="ts">
import { computed, ref } from 'vue'
import { useStudioStore } from '@/store/studio'
import type { AnchoredBubbleDTO, BubbleDTO, CompositionStateDTO, ResolvedSlotDTO, CutId } from '@/api/contracts'
import { cutRealizationUrl } from '@/domain/currency'
import { canvasHeight as resolvedCanvasHeight, computeCutSlots, projectLocalRectToCanvas } from '@/domain/geometry'
import type { LocalPercentageRect } from '@/domain/geometry'
import BubbleOverlay from './BubbleOverlay.vue'

const store = useStudioStore()
const snap = computed(() => store.server)
const slotElements = ref<Record<number, HTMLElement | null>>({})

const projectedComposition = computed((): CompositionStateDTO | null => {
  if (!snap.value) return null
  if (store.drafts.composition) return store.drafts.composition.value.state
  return snap.value.composition.state ?? snap.value.render_contract.default_composition
})

const projectedSlots = computed<ResolvedSlotDTO[]>(() => {
  const state = projectedComposition.value
  if (!state) return []
  if (!store.drafts.composition && snap.value?.render_contract.slots) return snap.value.render_contract.slots
  return computeCutSlots(state.slot_heights_px, state.gap_px, snap.value?.cuts.map((cut) => cut.cut_id))
})

const canvasHeight = computed(() => {
  if (!projectedSlots.value.length) return 1
  return resolvedCanvasHeight(projectedSlots.value, projectedComposition.value?.gap_px)
})
const canvasWidth = computed(() => projectedComposition.value?.canvas_width_px ?? 1024)
const bubbles = computed(() => projectedComposition.value?.bubbles ?? [])
const anchoredBubbles = computed(() => bubbles.value.filter((bubble): bubble is AnchoredBubbleDTO => bubble.anchor_status === 'ANCHORED'))
const reanchorBubbles = computed(() => bubbles.value.filter((bubble) => bubble.anchor_status === 'REANCHOR_REQUIRED'))

const cutImages = computed(() => {
  if (!snap.value) return []
  return snap.value.cuts.map((cut) => ({
    cut_id: cut.cut_id,
    url: cutRealizationUrl(cut),
    stale: cut.currency === 'STALE',
  }))
})

function setSlotRef(cutId: number, element: unknown) {
  slotElements.value[cutId] = element instanceof HTMLElement ? element : null
}
function slotForBubble(cutId: CutId): ResolvedSlotDTO | undefined {
  return projectedSlots.value.find((slot) => slot.cut_id === cutId)
}
function imageForCut(cutId: number) {
  return cutImages.value.find((image) => image.cut_id === cutId)
}
function projectedRect(bubble: AnchoredBubbleDTO, slot: ResolvedSlotDTO) {
  return projectLocalRectToCanvas(
    {
      local_x_pct: bubble.local_x_pct,
      local_y_pct: bubble.local_y_pct,
      local_w_pct: bubble.local_w_pct,
      local_h_pct: bubble.local_h_pct,
    },
    slot,
    canvasWidth.value,
    canvasHeight.value,
  )
}

function onBubbleCommit(bubbleId: string, rect: LocalPercentageRect) {
  const composition = projectedComposition.value
  if (!composition) return
  const bubbles = composition.bubbles.map((bubble) =>
    bubble.bubble_id === bubbleId && bubble.anchor_status === 'ANCHORED'
      ? { ...bubble, ...rect }
      : bubble,
  )
  store.setCompositionDraft({ ...composition, bubbles })
}

function onBubbleSelect(bubbleId: string) {
  const bubble = bubbles.value.find((item) => item.bubble_id === bubbleId)
  if (bubble) store.selectCut(bubble.cut_id as CutId)
  store.selectBubble(bubbleId)
}
</script>

<template>
  <section
    class="composition-surface"
    :style="{ aspectRatio: `${canvasWidth} / ${canvasHeight}` }"
    aria-label="조판 캔버스"
  >
    <div
      v-for="slot in projectedSlots"
      :key="slot.cut_id"
      :ref="(element) => setSlotRef(slot.cut_id, element)"
      class="cut-slot"
      :style="{
        top: `${slot.top_px / canvasHeight * 100}%`,
        height: `${slot.height_px / canvasHeight * 100}%`,
      }"
    >
      <img
        v-if="imageForCut(slot.cut_id)?.url"
        :src="imageForCut(slot.cut_id)!.url!"
        :alt="`컷 ${slot.cut_id}`"
        class="cut-image"
        loading="lazy"
        draggable="false"
      />
      <div v-else class="cut-placeholder"><span>컷 {{ slot.cut_id }}</span></div>
      <div v-if="imageForCut(slot.cut_id)?.stale" class="stale-overlay"><span class="stale-badge">STALE</span></div>
      <button
        v-for="bubble in reanchorBubbles.filter((item) => item.cut_id === slot.cut_id)"
        :key="bubble.bubble_id"
        type="button"
        class="reanchor-required"
        :class="{ selected: store.selection.bubbleId === bubble.bubble_id }"
        :aria-pressed="store.selection.bubbleId === bubble.bubble_id"
        :aria-label="`말풍선 ${bubble.bubble_id} 수동 재배치 선택`"
        @click.stop="onBubbleSelect(bubble.bubble_id)"
      >수동 재배치 필요 · {{ bubble.bubble_id }}</button>
    </div>

    <template v-for="bubble in anchoredBubbles" :key="bubble.bubble_id">
      <BubbleOverlay
        v-if="slotForBubble(bubble.cut_id)"
        :bubble="bubble"
        :slot="slotForBubble(bubble.cut_id)!"
        :slotElement="slotElements[bubble.cut_id] ?? null"
        :projectedRect="projectedRect(bubble, slotForBubble(bubble.cut_id)!)"
        :canvasWidthPx="canvasWidth"
        :canvasHeightPx="canvasHeight"
        :selected="store.selection.bubbleId === bubble.bubble_id"
        @commit="(rect) => onBubbleCommit(bubble.bubble_id, rect)"
        @select="onBubbleSelect(bubble.bubble_id)"
      />
    </template>

    <div v-if="store.saves['composition']?.state === 'failed' || store.saves['composition']?.state === 'conflict'" class="save-status-overlay" role="alert">
      <span class="save-status-badge">저장 안 됨</span>
    </div>
    <div v-else-if="store.drafts.composition" class="save-status-overlay save-status-unsaved"><span class="save-status-badge">미저장</span></div>
  </section>
</template>

<style scoped>
.composition-surface { position: relative; width: min(100%, 1024px); margin-inline: auto; flex: none; background: #ffffff; overflow: hidden; container-type: inline-size; }
.cut-slot { position: absolute; left: 0; width: 100%; background: #ffffff; overflow: hidden; }
.cut-image { width: 100%; height: 100%; object-fit: contain; display: block; user-select: none; pointer-events: none; }
.cut-placeholder { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: #1E2028; color: #5E6572; font-size: 24px; font-weight: 700; }
.stale-overlay { position: absolute; inset: 0; background: rgba(161, 92, 0, 0.12); display: flex; align-items: flex-start; justify-content: flex-end; padding: var(--sp-4); }
.stale-badge { background: var(--color-stale); color: #fff; font-size: var(--font-size-xs); font-weight: 700; padding: 2px var(--sp-4); border-radius: var(--radius-inner); }
.reanchor-required { position: absolute; top: var(--sp-8); left: var(--sp-8); max-width: calc(100% - (2 * var(--sp-8))); padding: var(--sp-4) var(--sp-8); border: 1px solid currentColor; border-radius: var(--radius-inner); color: var(--color-error); background: rgba(255,255,255,.9); font-size: var(--font-size-xs); text-align: start; cursor: pointer; z-index: 4; }
.reanchor-required:hover,
.reanchor-required:focus-visible,
.reanchor-required.selected { background: #fff; box-shadow: 0 0 0 2px rgba(180, 35, 24, .2); }
.save-status-overlay { position: absolute; bottom: var(--sp-8); right: var(--sp-8); z-index: 10; }
.save-status-badge { background: var(--color-error); color: #fff; font-size: var(--font-size-xs); font-weight: 600; padding: 2px var(--sp-8); border-radius: var(--radius-inner); }
.save-status-unsaved .save-status-badge { background: var(--color-stale); }
</style>
