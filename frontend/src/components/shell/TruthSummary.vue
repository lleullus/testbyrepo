<script setup lang="ts">
import { computed } from 'vue'
import type { StudioSnapshotDTO } from '@/api/contracts'
import { isRealizationComplete, countActiveJobs } from '@/domain/currency'

const props = defineProps<{ snapshot: StudioSnapshotDTO }>()

const executionLabel = computed(() => {
  const active = countActiveJobs(props.snapshot)
  return active > 0 ? `실행 중 ${active}` : '대기'
})

const currencyLabel = computed(() =>
  isRealizationComplete([...props.snapshot.cuts]) ? 'COMPLETE' : 'UNRESOLVED',
)

const authLabel = computed(() => {
  const auth = props.snapshot.release_authorization.active
  return auth ? `승인됨` : '미승인'
})

const deliveryLabel = computed(() => {
  const attempts = props.snapshot.delivery_attempts
  if (attempts.length === 0) return '미시도'
  const latest = attempts[attempts.length - 1]
  switch (latest.outcome) {
    case 'confirmed_success': return '전달 성공'
    case 'confirmed_failure': return '전달 실패'
    default: return '결과 미확인'
  }
})
</script>

<template>
  <nav class="truth-summary" aria-label="상태 요약">
    <span class="truth-dim">
      <span class="truth-label">실행</span>
      <span class="truth-value">{{ executionLabel }}</span>
    </span>
    <span class="truth-sep" aria-hidden="true">|</span>
    <span class="truth-dim">
      <span class="truth-label">실현</span>
      <span
        class="truth-value"
        :class="{ 'truth-current': currencyLabel === 'COMPLETE', 'truth-stale': currencyLabel === 'UNRESOLVED' }"
      >{{ currencyLabel === 'COMPLETE' ? '완료' : '미완료' }}</span>
    </span>
    <span class="truth-sep" aria-hidden="true">|</span>
    <span class="truth-dim">
      <span class="truth-label">승인</span>
      <span class="truth-value">{{ authLabel }}</span>
    </span>
    <span class="truth-sep" aria-hidden="true">|</span>
    <span class="truth-dim">
      <span class="truth-label">전달</span>
      <span class="truth-value">{{ deliveryLabel }}</span>
    </span>
  </nav>
</template>

<style scoped>
.truth-summary {
  display: flex;
  align-items: center;
  gap: var(--sp-8);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  flex-shrink: 1;
  overflow: hidden;
  white-space: nowrap;
}

.truth-dim {
  display: inline-flex;
  gap: var(--sp-4);
  align-items: baseline;
}

.truth-label {
  font-weight: 500;
  color: var(--text-secondary);
}

.truth-value {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.truth-current {
  color: var(--color-current);
}

.truth-stale {
  color: var(--color-stale);
}

.truth-sep {
  color: var(--border);
  user-select: none;
}

@media (max-width: 1099px) {
  .truth-summary {
    display: flex;
    grid-column: 1 / -1;
    grid-row: 3;
    justify-content: center;
    gap: var(--sp-4);
    overflow: visible;
    font-size: var(--font-size-xs);
  }
}
</style>
