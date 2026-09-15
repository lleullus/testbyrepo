<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import { useStudioStore } from '@/store/studio'

const store = useStudioStore()
const dialogRef = ref<HTMLDialogElement | null>(null)

const review = computed(() => store.ui.review)

watch(
  () => review.value,
  (val) => {
    if (val && dialogRef.value && !dialogRef.value.open) {
      dialogRef.value.showModal()
    } else if (!val && dialogRef.value?.open) {
      dialogRef.value.close()
    }
  },
)

function onClose() {
  store.closeReview()
}

function onApprove() {
  store.authorizeReview()
}

function onCancel() {
  store.closeReview()
}
</script>

<template>
  <dialog
    ref="dialogRef"
    class="review-dialog"
    aria-label="검토물 검토 및 승인"
    @close="onClose"
  >
    <div class="review-content" v-if="review">
      <header class="review-header">
        <h2 class="review-title">검토물 확인</h2>
        <button class="review-close" aria-label="닫기" @click="onCancel">✕</button>
      </header>

      <div class="review-image-container">
        <img
          :src="`/api/review-artifacts/${review.artifact.artifact_id}/content`"
          alt="조판 검토물"
          class="review-image"
          :style="{ transform: `scale(${review.zoom})` }"
          draggable="false"
        />
      </div>

      <div class="review-meta">
        <div class="meta-row">
          <span class="meta-label">Artifact ID</span>
          <code class="meta-value">{{ review.artifact.artifact_id }}</code>
        </div>
        <div class="meta-row">
          <span class="meta-label">Content Hash</span>
          <code class="meta-value">{{ review.displayedByteHash }}</code>
        </div>
        <div class="meta-row">
          <span class="meta-label">Composition Rev</span>
          <span class="meta-value tabular-nums">{{ review.artifact.composition_revision }}</span>
        </div>
        <div class="meta-row">
          <span class="meta-label">컷 Closure</span>
          <span class="meta-value tabular-nums">
            {{ review.artifact.cuts.map(c => `${c.cut_id}:r${c.realized_revision}`).join(', ') }}
          </span>
        </div>
      </div>

      <div class="review-zoom-controls">
        <button
          class="zoom-btn"
          @click="review.zoom = Math.max(0.25, review.zoom - 0.25)"
          aria-label="축소"
        >−</button>
        <span class="zoom-label tabular-nums">{{ Math.round(review.zoom * 100) }}%</span>
        <button
          class="zoom-btn"
          @click="review.zoom = Math.min(4, review.zoom + 0.25)"
          aria-label="확대"
        >+</button>
      </div>

      <footer class="review-footer">
        <button class="review-btn review-btn-cancel" @click="onCancel">닫기</button>
        <button
          class="review-btn review-btn-approve"
          :disabled="!store.canAuthorize"
          @click="onApprove"
        >승인</button>
      </footer>
    </div>
  </dialog>
</template>

<style scoped>
.review-dialog {
  max-width: min(90vw, 800px);
  max-height: 90vh;
  padding: 0;
  border: none;
  border-radius: var(--radius-panel);
  box-shadow: 0 8px 32px rgba(0,0,0,0.24);
  background: var(--surface-white);
}
.review-dialog::backdrop {
  background: rgba(0,0,0,0.5);
}

.review-content {
  display: flex;
  flex-direction: column;
  gap: var(--sp-12);
  padding: var(--sp-16);
  max-height: 90vh;
  overflow: auto;
}

.review-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.review-title {
  font-size: var(--font-size-heading);
  font-weight: 600;
}

.review-close {
  min-width: 44px;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-inner);
  font-size: 18px;
}
.review-close:hover {
  background: var(--surface-light);
}

.review-image-container {
  background: var(--canvas-bg);
  border-radius: var(--radius-inner);
  overflow: auto;
  max-height: 50vh;
  display: flex;
  align-items: flex-start;
  justify-content: center;
}

.review-image {
  max-width: 100%;
  height: auto;
  object-fit: contain;
  transform-origin: top center;
}

.review-meta {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  padding: var(--sp-8);
  background: var(--surface-light);
  border-radius: var(--radius-inner);
  font-size: var(--font-size-sm);
}

.meta-row {
  display: flex;
  justify-content: space-between;
  gap: var(--sp-8);
}

.meta-label {
  color: var(--text-secondary);
  font-weight: 500;
  flex-shrink: 0;
}

.meta-value {
  font-family: monospace, var(--font-family);
  word-break: break-all;
  text-align: end;
}

.review-zoom-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-8);
}

.zoom-btn {
  min-width: 36px;
  min-height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border);
  border-radius: var(--radius-inner);
  font-size: 18px;
  font-weight: 700;
}
.zoom-btn:hover {
  background: var(--surface-light);
}

.zoom-label {
  font-size: var(--font-size-sm);
  min-width: 48px;
  text-align: center;
}

.review-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-8);
  padding-top: var(--sp-8);
  border-top: 1px solid var(--border);
}

.review-btn {
  padding: var(--sp-8) var(--sp-24);
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: var(--font-size-body);
  min-height: 40px;
}

.review-btn-cancel {
  border: 1px solid var(--border);
  background: var(--surface-white);
}
.review-btn-cancel:hover {
  background: var(--surface-light);
}

.review-btn-approve {
  background: var(--accent);
  color: #fff;
}
.review-btn-approve:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.review-btn-approve:not(:disabled):hover {
  background: var(--accent-hover);
}
</style>
