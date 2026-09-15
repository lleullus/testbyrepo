<script setup lang="ts">
import { computed, ref } from 'vue'
import { useStudioStore } from '@/store/studio'
import type { CutId, BubbleDTO, CompositionStateDTO } from '@/api/contracts'
import { cutRealizationUrl } from '@/domain/currency'
import BubbleOverlay from './BubbleOverlay.vue'

const store = useStudioStore()
const surfaceRef = ref<HTMLElement | null>(null)

const snap = computed(() => store.server)

// Projected composition: merge server composition with draft if present
const projectedComposition = computed((): CompositionStateDTO | null => {
  if (!snap.value) return null
  // If there's a composition draft, use its state (full replacement)
  if (store.drafts.composition) {
    return store.drafts.composition.value.state
  }
  return snap.value.composition.state ?? null
})

const bubbles = computed((): BubbleDTO[] => {
  return projectedComposition.value?.bubbles ?? []
})

const gapPx = computed(() => projectedComposition.value?.gap_px ?? 24)

// Canonical surface aspect: 1024:7680
const SURFACE_W = 1024
const SURFACE_H = 7680
const aspectRatio = SURFACE_H / SURFACE_W

// Cut slot geometry (mirrors Python compute_cut_slots)
const cutSlots = computed(() => {
  const gap = gapPx.value
  const totalGap = gap * 4
  const availableHeight = SURFACE_H - totalGap
  const cutHeight = Math.floor(availableHeight / 5)
  const slots: Array<{ yPct: number; hPct: number }> = []
  for (let i = 0; i < 5; i++) {
    const y0 = i * (cutHeight + gap)
    slots.push({
      yPct: (y0 / SURFACE_H) * 100,
      hPct: (cutHeight / SURFACE_H) * 100,
    })
  }
  return slots
})

// Build cut image URLs
const cutImages = computed(() => {
  if (!snap.value) return []
  return snap.value.cuts.map((cut) => ({
    cut_id: cut.cut_id,
    url: cutRealizationUrl(cut),
    stale: cut.currency === 'STALE',
  }))
})

// When a bubble geometry changes via interaction
function onBubbleCommit(bubbleId: string, rect: { x_pct: number; y_pct: number; w_pct: number; h_pct: number }) {
  if (!projectedComposition.value) return
  const newBubbles = projectedComposition.value.bubbles.map((b) => {
    if (b.bubble_id === bubbleId) {
      return { ...b, ...rect }
    }
    return b
  })
  const newState: CompositionStateDTO = {
    ...projectedComposition.value,
    bubbles: newBubbles,
  }
  store.setCompositionDraft(newState)
}

function onBubbleSelect(bubbleId: string) {
  store.selectBubble(bubbleId)
}
</script>

<template>
  <section
    ref="surfaceRef"
    class="composition-surface"
    :style="{ aspectRatio: `${SURFACE_W} / ${SURFACE_H}` }"
    aria-label="조판 캔버스"
  >
    <!-- Cut image layers -->
    <div
      v-for="(slot, i) in cutSlots"
      :key="i"
      class="cut-slot"
      :style="{
        top: `${slot.yPct}%`,
        height: `${slot.hPct}%`,
      }"
    >
      <img
        v-if="cutImages[i]?.url"
        :src="cutImages[i].url!"
        :alt="`컷 ${i + 1}`"
        class="cut-image"
        loading="lazy"
        draggable="false"
      />
      <div v-else class="cut-placeholder">
        <span>컷 {{ i + 1 }}</span>
      </div>
      <!-- STALE overlay -->
      <div
        v-if="cutImages[i]?.stale"
        class="stale-overlay"
      >
        <span class="stale-badge">STALE</span>
      </div>
    </div>

    <!-- Bubble overlay layer -->
    <BubbleOverlay
      v-for="bubble in bubbles"
      :key="bubble.bubble_id"
      :bubble="bubble"
      :surfaceRef="surfaceRef"
      :selected="store.selection.bubbleId === bubble.bubble_id"
      @commit="(rect) => onBubbleCommit(bubble.bubble_id, rect)"
      @select="onBubbleSelect(bubble.bubble_id)"
    />

    <!-- Unsaved / conflict / save-failure overlay -->
    <div
      v-if="store.saves['composition']?.state === 'failed' || store.saves['composition']?.state === 'conflict'"
      class="save-status-overlay"
      role="alert"
    >
      <span class="save-status-badge">저장 안 됨</span>
    </div>
    <div
      v-else-if="store.drafts.composition"
      class="save-status-overlay save-status-unsaved"
    >
      <span class="save-status-badge">미저장</span>
    </div>
  </section>
</template>

<style scoped>
.composition-surface {
  position: relative;
  width: 100%;
  max-height: 100%;
  background: var(--canvas-bg);
  overflow: hidden;
  container-type: inline-size;
}

.cut-slot {
  position: absolute;
  left: 0;
  width: 100%;
  overflow: hidden;
}

.cut-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  user-select: none;
  pointer-events: none;
}

.cut-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1E2028;
  color: #5E6572;
  font-size: 24px;
  font-weight: 700;
}

.stale-overlay {
  position: absolute;
  inset: 0;
  background: rgba(161, 92, 0, 0.12);
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
  padding: var(--sp-4);
}

.stale-badge {
  background: var(--color-stale);
  color: #fff;
  font-size: var(--font-size-xs);
  font-weight: 700;
  padding: 2px var(--sp-4);
  border-radius: var(--radius-inner);
}

.save-status-overlay {
  position: absolute;
  bottom: var(--sp-8);
  right: var(--sp-8);
  z-index: 10;
}

.save-status-badge {
  background: var(--color-error);
  color: #fff;
  font-size: var(--font-size-xs);
  font-weight: 600;
  padding: 2px var(--sp-8);
  border-radius: var(--radius-inner);
}

.save-status-unsaved .save-status-badge {
  background: var(--color-stale);
}
</style>
