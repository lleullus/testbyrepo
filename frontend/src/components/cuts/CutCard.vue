<script setup lang="ts">
import { computed } from 'vue'
import type { CutDTO } from '@/api/contracts'
import { isCutCurrent, cutRealizationUrl } from '@/domain/currency'
import { useStudioStore } from '@/store/studio'

const props = defineProps<{
  cut: CutDTO
  selected: boolean
}>()

const emit = defineEmits<{ select: [] }>()

const store = useStudioStore()

const current = computed(() => isCutCurrent(props.cut))
const thumbUrl = computed(() => cutRealizationUrl(props.cut))

const hasSaveIssue = computed(() => {
  const key = `intent-${props.cut.cut_id}`
  const s = store.saves[key]
  return s && (s.state === 'failed' || s.state === 'conflict' || s.state === 'base-changed')
})

const hasIntentDraft = computed(() => !!store.drafts.intents[props.cut.cut_id])
</script>

<template>
  <button
    class="cut-card"
    :class="{ selected, stale: !current }"
    :aria-label="`컷 ${cut.cut_id} ${current ? '현재' : '최신 의도 미실현'}`"
    :aria-pressed="selected"
    @click="emit('select')"
  >
    <div class="cut-thumb">
      <img
        v-if="thumbUrl"
        :src="thumbUrl"
        :alt="`컷 ${cut.cut_id} 썸네일`"
        class="cut-thumb-img"
        loading="lazy"
      />
      <div v-else class="cut-thumb-empty" :aria-label="`컷 ${cut.cut_id} 이미지 없음`">
        {{ cut.cut_id }}
      </div>
    </div>
    <div class="cut-meta">
      <span class="cut-id">컷 {{ cut.cut_id }}</span>
      <span class="cut-revisions tabular-nums">
        {{ cut.desired_revision ?? '—' }} / {{ cut.realized_revision ?? '—' }}
      </span>
      <span
        class="cut-badge"
        :class="current ? 'badge-current' : 'badge-stale'"
      >{{ current ? '현재' : '최신 의도 미실현' }}</span>
      <span v-if="hasIntentDraft" class="cut-unsaved">미저장</span>
      <span v-if="hasSaveIssue" class="cut-save-error">저장 안 됨</span>
    </div>
  </button>
</template>

<style scoped>
.cut-card {
  display: flex;
  gap: var(--sp-8);
  padding: var(--sp-8);
  border: 1px solid var(--border);
  border-radius: var(--radius-panel);
  background: var(--surface-white);
  text-align: start;
  cursor: pointer;
  transition: border-color 0.1s;
  width: 100%;
}
.cut-card.selected {
  border-color: var(--accent);
  background: var(--surface-light);
}
.cut-card:hover:not(.selected) {
  border-color: var(--text-secondary);
}

.cut-thumb {
  width: 56px;
  height: 56px;
  flex-shrink: 0;
  border-radius: var(--radius-inner);
  overflow: hidden;
  background: var(--surface-bg);
}
.cut-thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.cut-thumb-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: var(--font-size-heading);
  color: var(--text-secondary);
  font-weight: 700;
}

.cut-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.cut-id {
  font-weight: 600;
  font-size: var(--font-size-sm);
}

.cut-revisions {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.cut-badge {
  font-size: var(--font-size-xs);
  font-weight: 600;
  padding: 1px var(--sp-4);
  border-radius: var(--radius-inner);
  align-self: flex-start;
}
.badge-current {
  background: #E7F5EF;
  color: var(--color-current);
}
.badge-stale {
  background: #FFF7ED;
  color: var(--color-stale);
}

.cut-unsaved, .cut-save-error {
  font-size: var(--font-size-xs);
  font-weight: 500;
}
.cut-unsaved {
  color: var(--color-stale);
}
.cut-save-error {
  color: var(--color-error);
}
</style>
