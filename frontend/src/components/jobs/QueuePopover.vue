<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useStudioStore } from '@/store/studio'
import { isJobStoppable } from '@/domain/currency'

const emit = defineEmits<{ close: [] }>()
const store = useStudioStore()
const popoverRef = ref<HTMLElement | null>(null)

const jobs = computed(() => store.server?.jobs ?? [])

function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    emit('close')
  }
}

function onClickOutside(e: MouseEvent) {
  if (popoverRef.value && !popoverRef.value.contains(e.target as Node)) {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('keydown', onKeyDown)
  // Defer to avoid immediate close from the trigger click
  setTimeout(() => document.addEventListener('click', onClickOutside), 0)
})

onUnmounted(() => {
  document.removeEventListener('keydown', onKeyDown)
  document.removeEventListener('click', onClickOutside)
})
</script>

<template>
  <div ref="popoverRef" class="queue-popover" role="dialog" aria-label="작업 큐 상세">
    <div class="queue-header">
      <h2 class="queue-title">작업 큐</h2>
      <button class="queue-close" aria-label="닫기" @click="emit('close')">✕</button>
    </div>

    <div v-if="jobs.length === 0" class="queue-empty">
      대기 중인 작업 없음
    </div>

    <ul v-else class="queue-list">
      <li
        v-for="job in jobs"
        :key="job.job_id"
        class="queue-item"
        :class="job.status"
      >
        <div class="queue-item-info">
          <span class="queue-cut tabular-nums">컷 {{ job.cut_id }}</span>
          <span class="queue-rev tabular-nums">rev {{ job.target_desired_revision }}</span>
          <span class="queue-status">{{ job.status }}</span>
        </div>
        <button
          v-if="isJobStoppable(job.status)"
          class="queue-stop-btn"
          :disabled="store.jobsUi[job.job_id]?.stopRequested"
          aria-label="이 작업 중지"
          @click="store.stopJob(job.job_id)"
        >{{ store.jobsUi[job.job_id]?.stopRequested ? '중지 중…' : '중지' }}</button>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.queue-popover {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 300;
  min-width: 280px;
  max-width: 360px;
  max-height: 400px;
  overflow: auto;
  background: var(--surface-white);
  border: 1px solid var(--border);
  border-radius: var(--radius-panel);
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  padding: var(--sp-8);
}

.queue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: var(--sp-8);
  border-bottom: 1px solid var(--border);
  margin-bottom: var(--sp-8);
}

.queue-title {
  font-size: var(--font-size-body);
  font-weight: 600;
}

.queue-close {
  min-width: 32px;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-inner);
}
.queue-close:hover {
  background: var(--surface-light);
}

.queue-empty {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  padding: var(--sp-16);
  text-align: center;
}

.queue-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

.queue-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--sp-4) var(--sp-8);
  border-radius: var(--radius-inner);
  background: var(--surface-light);
}
.queue-item.running {
  background: #EFF6FF;
}
.queue-item.failed, .queue-item.interrupted {
  background: var(--color-error-bg);
}

.queue-item-info {
  display: flex;
  gap: var(--sp-8);
  align-items: center;
  font-size: var(--font-size-sm);
}

.queue-cut {
  font-weight: 600;
}

.queue-rev {
  color: var(--text-secondary);
}

.queue-status {
  font-size: var(--font-size-xs);
  font-weight: 500;
  text-transform: uppercase;
}

.queue-stop-btn {
  font-size: var(--font-size-xs);
  padding: 2px var(--sp-8);
  background: var(--color-error);
  color: #fff;
  border-radius: var(--radius-inner);
  font-weight: 600;
  min-height: 24px;
}
.queue-stop-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
