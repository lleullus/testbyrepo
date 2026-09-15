<script setup lang="ts">
import { ref, computed } from 'vue'
import { useStudioStore } from '@/store/studio'
import type { CutId, CutIntentDTO, BaselineStructureDTO } from '@/api/contracts'

const store = useStudioStore()

const dialogRef = ref<HTMLDialogElement | null>(null)
const isOpen = ref(false)

const sourceBrief = ref('')
const cuts = ref<Array<{ cut_id: CutId; role: string; beat: string }>>([
  { cut_id: 1, role: '', beat: '' },
  { cut_id: 2, role: '', beat: '' },
  { cut_id: 3, role: '', beat: '' },
  { cut_id: 4, role: '', beat: '' },
  { cut_id: 5, role: '', beat: '' },
])
const intents = ref<Array<{ cut_id: CutId; prompt: string; dialogue: string }>>([
  { cut_id: 1, prompt: '', dialogue: '' },
  { cut_id: 2, prompt: '', dialogue: '' },
  { cut_id: 3, prompt: '', dialogue: '' },
  { cut_id: 4, prompt: '', dialogue: '' },
  { cut_id: 5, prompt: '', dialogue: '' },
])

const hasBaseline = computed(() => store.server?.baseline !== null)

function open() {
  const draft = store.drafts.baseline?.value
  const baseline = store.server?.baseline
  const structure = draft?.structure ?? baseline?.structure
  if (structure) {
    sourceBrief.value = structure.source_brief
    cuts.value = structure.cuts.map((cut) => ({ ...cut }))
  }
  const draftIntents = draft?.intents
  if (draftIntents) {
    intents.value = draftIntents.map(({ cut_id, intent }) => ({ cut_id, ...intent }))
  } else if (store.server) {
    intents.value = store.server.cuts.map((cut) => ({
      cut_id: cut.cut_id,
      prompt: cut.effective_intent?.prompt ?? '',
      dialogue: cut.effective_intent?.dialogue ?? '',
    }))
  }
  isOpen.value = true
  dialogRef.value?.showModal()
}

function close() {
  isOpen.value = false
  dialogRef.value?.close()
}

function updateDraft() {
  const structure: BaselineStructureDTO = {
    source_brief: sourceBrief.value,
    cuts: cuts.value.map((cut) => ({ ...cut })) as BaselineStructureDTO['cuts'],
  }
  store.setBaselineDraft(
    structure,
    intents.value.map(({ cut_id, prompt, dialogue }) => ({
      cut_id,
      intent: { prompt, dialogue },
    })),
    false,
  )
}

function submit() {
  updateDraft()
  store.saveBaselineDraft()
  close()
}

// Expose open method for external trigger
defineExpose({ open })
</script>

<template>
  <dialog ref="dialogRef" class="rebaseline-dialog" aria-label="Baseline 설정" @close="close">
    <div class="rebaseline-content" v-if="isOpen">
      <h2 class="rebaseline-title">{{ hasBaseline ? 'Re-baseline' : '1차 승인 — Baseline 설정' }}</h2>

      <label class="field-label">
        Source Brief (시놉시스)
        <textarea class="field-textarea" v-model="sourceBrief" rows="3" />
      </label>

      <div v-for="(cut, idx) in cuts" :key="cut.cut_id" class="cut-fields">
        <h3 class="cut-field-title">컷 {{ cut.cut_id }}</h3>
        <label class="field-label">
          역할
          <input class="field-input" v-model="cut.role" />
        </label>
        <label class="field-label">
          비트
          <input class="field-input" v-model="cut.beat" />
        </label>
        <label class="field-label">
          프롬프트
          <textarea class="field-textarea" v-model="intents[idx].prompt" rows="2" />
        </label>
        <label class="field-label">
          대사
          <input class="field-input" v-model="intents[idx].dialogue" />
        </label>
      </div>

      <footer class="rebaseline-footer">
        <button class="btn btn-cancel" @click="close">취소</button>
        <button class="btn btn-confirm" @click="submit">
          {{ hasBaseline ? 'Re-baseline 확인' : 'Baseline 승인' }}
        </button>
      </footer>
    </div>
  </dialog>
</template>

<style scoped>
.rebaseline-dialog {
  max-width: min(90vw, 640px);
  max-height: 90vh;
  padding: 0;
  border: none;
  border-radius: var(--radius-panel);
  box-shadow: 0 8px 32px rgba(0,0,0,0.24);
  background: var(--surface-white);
}
.rebaseline-dialog::backdrop {
  background: rgba(0,0,0,0.5);
}

.rebaseline-content {
  padding: var(--sp-16);
  display: flex;
  flex-direction: column;
  gap: var(--sp-12);
  max-height: 90vh;
  overflow: auto;
}

.rebaseline-title {
  font-size: var(--font-size-heading);
  font-weight: 600;
}

.cut-fields {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  padding: var(--sp-8);
  background: var(--surface-light);
  border-radius: var(--radius-inner);
}

.cut-field-title {
  font-size: var(--font-size-body);
  font-weight: 600;
}

.field-label {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  font-weight: 500;
}

.field-input, .field-textarea {
  width: 100%;
  padding: var(--sp-4) var(--sp-8);
  border: 1px solid var(--border);
  border-radius: var(--radius-inner);
  font-size: var(--font-size-body);
  background: var(--surface-white);
}
.field-textarea {
  resize: vertical;
  line-height: var(--line-height);
}

.rebaseline-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-8);
  padding-top: var(--sp-8);
  border-top: 1px solid var(--border);
}

.btn {
  padding: var(--sp-8) var(--sp-24);
  border-radius: var(--radius-sm);
  font-weight: 600;
  min-height: 40px;
}
.btn-cancel {
  border: 1px solid var(--border);
  background: var(--surface-white);
}
.btn-cancel:hover {
  background: var(--surface-light);
}
.btn-confirm {
  background: var(--accent);
  color: #fff;
}
.btn-confirm:hover {
  background: var(--accent-hover);
}
</style>
