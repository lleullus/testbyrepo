<script setup lang="ts">
import { computed } from 'vue'
import { useStudioStore } from '@/store/studio'
import TruthSummary from './TruthSummary.vue'
import QueuePopover from '../jobs/QueuePopover.vue'

const store = useStudioStore()
const emit = defineEmits<{ rebaseline: [] }>()

const snap = computed(() => store.server)
const activeCount = computed(() => store.activeJobCount)
const hasStoppable = computed(() => activeCount.value > 0)

const statusLabel = computed(() => {
  if (store.stream.status === 'DEGRADED') return 'DEGRADED / 재동기화 필요'
  if (store.stream.status === 'CONNECTING') return 'CONNECTING'
  return 'OPEN'
})

const genAriaLabel = computed(() => {
  if (!store.hasCurrentSnapshot) return '재동기화 필요: 전체 생성 비활성화됨'
  if (store.hasBlockingEdit) return '미저장 편집이 있어 생성할 수 없음'
  if (!store.server?.baseline) return '기준(Baseline) 설정 필요'
  return '전체 생성'
})

const reviewAriaLabel = computed(() => {
  if (!store.hasCurrentSnapshot) return '재동기화 필요: 검토물 생성 비활성화됨'
  if (!store.realizationComplete) return '컷 실체화 미완료'
  if (store.hasBlockingEdit) return '미저장 편집이 있어 검토물을 생성할 수 없음'
  return '검토물 생성'
})

const exportAriaLabel = computed(() => {
  if (!store.hasCurrentSnapshot) return '재동기화 필요: PNG 내보내기 비활성화됨'
  if (store.hasBlockingEdit) return '미저장 편집이 있어 내보낼 수 없음'
  return 'PNG 내보내기'
})

const bloggerAriaLabel = computed(() => {
  if (!store.hasCurrentSnapshot) return '재동기화 필요: Blogger 발행 비활성화됨'
  if (store.hasBlockingEdit) return '미저장 편집이 있어 발행할 수 없음'
  return 'Blogger 발행'
})
</script>

<template>
  <header class="header" role="banner">
    <div class="header-left">
      <button
        class="header-toggle"
        :aria-label="store.ui.leftOpen ? '컷 목록 닫기' : '컷 목록 열기'"
        @click="store.toggleLeft()"
      >☰</button>
      <h1 class="header-title">Web Comic Studio</h1>
    </div>

    <TruthSummary v-if="snap" :snapshot="snap" />

    <div class="header-actions">
      <!-- Queue summary + popover trigger -->
      <button
        class="header-btn baseline-action"
        :aria-label="snap?.baseline ? 'Re-baseline 열기' : 'Baseline 설정 열기'"
        @click="emit('rebaseline')"
      >기준</button>

      <div class="queue-trigger-wrapper">
        <button
          class="header-btn queue-btn"
          :aria-label="`작업 큐: ${activeCount}개 진행 중`"
          @click="store.toggleQueue()"
        >
          <span class="tabular-nums">큐 {{ activeCount }}</span>
        </button>
        <QueuePopover v-if="store.ui.queueOpen" @close="store.toggleQueue()" />
      </div>

      <!-- Immediate STOP -->
      <button
        class="header-btn stop-btn"
        :disabled="!hasStoppable"
        aria-label="전체 중지"
        @click="store.stopAll()"
      >STOP</button>

      <!-- Generate all -->
      <button
        class="header-btn gen-btn"
        :disabled="!store.canGenerate"
        :aria-label="genAriaLabel"
        @click="store.generateAll()"
      >생성</button>

      <!-- Review trigger -->
      <button
        class="header-btn review-btn"
        :disabled="!store.canMaterializeReview"
        :aria-label="reviewAriaLabel"
        @click="store.materializeReview()"
      >검토</button>

      <!-- Export PNG -->
      <button
        class="header-btn export-btn"
        :disabled="!store.canRelease"
        :aria-label="exportAriaLabel"
        @click="store.exportPng()"
      >내보내기</button>

      <!-- Release Blogger -->
      <button
        class="header-btn blogger-btn"
        :disabled="!store.canRelease"
        :aria-label="bloggerAriaLabel"
        @click="store.releaseBlogger()"
      >발행</button>

      <!-- SSE connection indicator -->
      <span
        class="stream-indicator"
        :class="store.stream.status.toLowerCase()"
        :aria-label="`연결: ${statusLabel}`"
        role="status"
      >
        <span class="stream-dot" aria-hidden="true">●</span>
        <span class="stream-label">{{ statusLabel }}</span>
      </span>

      <button
        class="header-toggle inspector-toggle"
        :aria-label="store.ui.rightOpen ? '인스펙터 닫기' : '인스펙터 열기'"
        @click="store.toggleRight()"
      >⚙</button>
    </div>
  </header>
</template>


<style scoped>
.header {
  display: flex;
  align-items: center;
  gap: var(--sp-12);
  padding: 0 var(--sp-16);
  background: var(--surface-white);
  border-bottom: 1px solid var(--border);
  height: var(--header-height);
  position: sticky;
  top: 0;
  z-index: 200;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--sp-8);
  flex-shrink: 0;
}

.header-title {
  font-size: var(--font-size-body);
  font-weight: 600;
  white-space: nowrap;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--sp-8);
  margin-inline-start: auto;
  flex-shrink: 0;
}

.header-toggle {
  min-width: 44px;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-inner);
  color: var(--text-primary);
}
.header-toggle:hover {
  background: var(--surface-light);
}

.header-btn {
  padding: var(--sp-4) var(--sp-12);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  font-weight: 500;
  min-height: 32px;
  white-space: nowrap;
}

.queue-btn {
  background: var(--surface-light);
}
.queue-btn:hover {
  background: var(--surface-bg);
}
.baseline-action {
  border: 1px solid var(--border);
  background: var(--surface-white);
}
.baseline-action:hover {
  background: var(--surface-light);
}


.stop-btn {
  background: var(--color-error);
  color: #fff;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.stop-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.stop-btn:not(:disabled):hover {
  background: #9A1F12;
}

.gen-btn {
  background: var(--color-current);
  color: #fff;
}
.gen-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.gen-btn:not(:disabled):hover {
  background: #137040;
}

.review-btn {
  background: var(--accent);
  color: #fff;
}
.review-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.review-btn:not(:disabled):hover {
  background: var(--accent-hover);
}

.queue-trigger-wrapper {
  position: relative;
}

.stream-indicator {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-4);
  font-size: var(--font-size-xs);
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
}
.stream-indicator.open { color: var(--color-current); }
.stream-indicator.connecting { color: var(--color-stale); }
.stream-indicator.degraded { color: var(--color-stale); }
@media (max-width: 1099px) {
  .header {
    display: grid;
    grid-template-columns: 44px minmax(0, 1fr);
    grid-template-rows: 44px 44px 28px;
    gap: 2px var(--sp-4);
    height: var(--header-height);
    padding: var(--sp-4) var(--sp-8);
  }
  .header-left {
    grid-column: 1;
    grid-row: 1;
  }
  .header-title {
    display: none;
  }
  .header-actions {
    grid-column: 2;
    grid-row: 1 / 3;
    display: grid;
    grid-template-columns: repeat(4, minmax(44px, 1fr));
    grid-template-rows: 44px 44px;
    grid-template-areas:
      "base queue stop right"
      "generate review stream .";
    gap: 2px var(--sp-4);
    margin: 0;
  }
  .baseline-action { grid-area: base; }
  .queue-trigger-wrapper { grid-area: queue; }
  .queue-trigger-wrapper > .queue-btn { width: 100%; height: 44px; }
  .stop-btn { grid-area: stop; }
  .gen-btn { grid-area: generate; }
  .review-btn { grid-area: review; }
  .stream-indicator { grid-area: stream; align-self: center; justify-self: center; }
  .stream-indicator .stream-label { display: none; }
  .inspector-toggle { grid-area: right; }
  .header-btn,
  .header-toggle {
    min-height: 44px;
    padding-inline: var(--sp-4);
  }
}
</style>
