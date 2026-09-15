<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed } from 'vue'
import { useStudioStore } from '@/store/studio'
import StudioHeader from './StudioHeader.vue'
import CutRail from '../cuts/CutRail.vue'
import CanvasRegion from '../canvas/CanvasRegion.vue'
import InspectorPanel from '../inspector/InspectorPanel.vue'
import CanonicalReviewDialog from '../review/CanonicalReviewDialog.vue'
import RebaselineDialog from '../baseline/RebaselineDialog.vue'
import ToastRegion from '../feedback/ToastRegion.vue'

const store = useStudioStore()
const rebaselineRef = ref<InstanceType<typeof RebaselineDialog> | null>(null)

const hasBaseline = computed(() => store.server?.baseline !== null)

function openBaseline() {
  rebaselineRef.value?.open()
}

onMounted(() => {
  store.loadStudio()
})

onUnmounted(() => {
  store.dispose()
})
</script>

<template>
  <div class="studio-shell" v-if="store.hasCurrentSnapshot">
    <StudioHeader class="studio-header" @rebaseline="openBaseline" />
    <aside
      class="left-panel"
      role="complementary"
      aria-label="컷 목록"
      :data-open="store.ui.leftOpen"
    >
      <CutRail />
    </aside>
    <main id="main-canvas" class="canvas-region" role="main">
      <template v-if="hasBaseline">
        <CanvasRegion />
      </template>
      <div v-else class="no-baseline-prompt">
        <p>Baseline이 없습니다. 1차 승인을 수행하세요.</p>
        <p v-if="store.drafts.baseline" class="draft-marker">Baseline 초안 미저장</p>
        <button class="baseline-btn" @click="openBaseline">Baseline 설정</button>
      </div>
    </main>
    <aside
      class="right-panel"
      role="complementary"
      aria-label="인스펙터"
      :data-open="store.ui.rightOpen"
    >
      <InspectorPanel />
    </aside>
    <CanonicalReviewDialog />
    <RebaselineDialog ref="rebaselineRef" />
    <ToastRegion />
  </div>
  <div v-else class="studio-loading" role="status" aria-live="polite">
    <p>스튜디오 로딩 중…</p>
  </div>
</template>

<style scoped>
.studio-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100dvh;
  font-size: var(--font-size-heading);
  color: var(--text-secondary);
}
.no-baseline-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: var(--sp-16);
  color: #CBD5E1;
  font-size: var(--font-size-body);
}
.draft-marker {
  color: #FBBF24;
  font-weight: 600;
}

.baseline-btn {
  padding: var(--sp-8) var(--sp-24);
  background: var(--accent);
  color: #fff;
  border-radius: var(--radius-sm);
  font-weight: 600;
  min-height: 40px;
}
.baseline-btn:hover {
  background: var(--accent-hover);
}
</style>
