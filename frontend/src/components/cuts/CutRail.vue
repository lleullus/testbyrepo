<script setup lang="ts">
import { computed } from 'vue'
import { useStudioStore } from '@/store/studio'
import type { CutId } from '@/api/contracts'
import CutCard from './CutCard.vue'

const store = useStudioStore()

const cuts = computed(() => store.server?.cuts ?? [])
const slotHeights = computed(() => new Map((store.server?.render_contract.slots ?? []).map((slot) => [slot.cut_id, slot.height_px])))
</script>

<template>
  <nav class="cut-rail" aria-label="컷 목록">
    <div class="rail-actions">
      <button type="button" @click="store.addCut()">컷 추가</button>
    </div>
    <div v-for="(cut, index) in cuts" :key="cut.cut_id" class="cut-entry">
      <CutCard
        :cut="cut"
        :selected="store.selection.cutId === cut.cut_id"
        :slot-height="slotHeights.get(cut.cut_id)"
        @select="store.selectCut(cut.cut_id as CutId)"
      />
      <div class="cut-actions">
        <button type="button" :disabled="index === 0" @click="store.reorderCuts(cuts.map((item, i) => i === index - 1 ? cut.cut_id : i === index ? cuts[index - 1].cut_id : item.cut_id))">위</button>
        <button type="button" :disabled="index === cuts.length - 1" @click="store.reorderCuts(cuts.map((item, i) => i === index ? cuts[index + 1].cut_id : i === index + 1 ? cut.cut_id : item.cut_id))">아래</button>
        <button type="button" :disabled="cuts.length <= 1" @click="store.retireCut(cut.cut_id as CutId)">비활성화</button>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.cut-rail {
  display: flex;
  flex-direction: column;
  gap: var(--sp-8);
  padding: var(--sp-12);
}
</style>
