<script setup lang="ts">
import { computed } from 'vue'
import { useStudioStore } from '@/store/studio'
import type { CutId } from '@/api/contracts'
import CutCard from './CutCard.vue'

const store = useStudioStore()

const cuts = computed(() => store.server?.cuts ?? [])
</script>

<template>
  <nav class="cut-rail" aria-label="컷 목록">
    <CutCard
      v-for="cut in cuts"
      :key="cut.cut_id"
      :cut="cut"
      :selected="store.selection.cutId === cut.cut_id"
      @select="store.selectCut(cut.cut_id as CutId)"
    />
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
