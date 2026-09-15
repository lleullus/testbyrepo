<script setup lang="ts">
import { useStudioStore } from '@/store/studio'

const store = useStudioStore()
</script>

<template>
  <div class="toast-region" aria-live="polite" aria-relevant="additions">
    <div
      v-for="toast in store.toasts"
      :key="toast.id"
      class="toast"
      :class="toast.role === 'alert' ? 'toast-alert' : 'toast-status'"
      :role="toast.role"
    >
      {{ toast.text }}
    </div>
  </div>
</template>

<style scoped>
.toast-region {
  position: fixed;
  bottom: var(--sp-16);
  right: var(--sp-16);
  z-index: 500;
  display: flex;
  flex-direction: column-reverse;
  gap: var(--sp-8);
  pointer-events: none;
  max-width: min(400px, calc(100vw - 32px));
}

.toast {
  padding: var(--sp-8) var(--sp-16);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  font-weight: 500;
  pointer-events: auto;
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
}

.toast-status {
  background: var(--surface-white);
  border: 1px solid var(--border);
  color: var(--text-primary);
}

.toast-alert {
  background: var(--color-error-bg);
  border: 1px solid var(--color-error);
  color: var(--color-error);
}
</style>
