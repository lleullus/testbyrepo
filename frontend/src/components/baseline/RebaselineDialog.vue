<script setup lang="ts">
import { computed, ref } from 'vue'
import { useStudioStore } from '@/store/studio'
import type { CutId, BaselineStructureDTO, BaselineCutIntentInputDTO } from '@/api/contracts'

const store = useStudioStore()

const dialogRef = ref<HTMLDialogElement | null>(null)
const isOpen = ref(false)
const sourceBrief = ref('')
const isGenerating = ref(false)
const isSubmitting = ref(false)
const editorVisible = ref(false)
const generationError = ref('')
const localEditVersion = ref(0)
const cutCount = ref(5)
const cuts = ref<Array<{ cut_id: CutId; role: string; beat: string }>>([])
const intents = ref<Array<{ cut_id: CutId; prompt: string; dialogue: string; prompt_origin: BaselineCutIntentInputDTO['prompt_origin'] }>>([])

function resizeCuts(nextCount: number) {
  const count = Number.isSafeInteger(nextCount) && nextCount >= 1 ? nextCount : 1
  if (count < cuts.value.length) {
    const removedCuts = cuts.value.slice(count)
    const removedIntents = intents.value.slice(count)
    const hasData = removedCuts.some((cut) => cut.role.trim() || cut.beat.trim()) || removedIntents.some((intent) => intent.prompt.trim() || intent.dialogue.trim())
    if (hasData && typeof window !== 'undefined' && !window.confirm('줄어든 컷의 입력값이 제거됩니다. 계속하시겠습니까?')) {
      cutCount.value = cuts.value.length
      return
    }
  }
  const previousCuts = new Map(cuts.value.map((cut) => [cut.cut_id, cut]))
  const previousIntents = new Map(intents.value.map((intent) => [intent.cut_id, intent]))
  cuts.value = Array.from({ length: count }, (_, index) => previousCuts.get((index + 1) as CutId) ?? ({ cut_id: (index + 1) as CutId, role: '', beat: '' }))
  intents.value = Array.from({ length: count }, (_, index) => previousIntents.get((index + 1) as CutId) ?? ({ cut_id: (index + 1) as CutId, prompt: '', dialogue: '', prompt_origin: 'user' as const }))
  cutCount.value = count
  markLocalEdit()
}

const hasBaseline = computed(() => store.server?.baseline !== null)

function markLocalEdit() {
  localEditVersion.value += 1
}

function markPromptEdited(cutId: CutId) {
  const intent = intents.value.find((item) => item.cut_id === cutId)
  if (intent) intent.prompt_origin = 'user'
  markLocalEdit()
}

function open() {
  const draft = store.drafts.baseline?.value
  const baseline = store.server?.baseline
  const structure = draft?.structure ?? baseline?.structure
  const draftIntents = draft?.intents
  generationError.value = ''
  const activeCount = store.server?.cuts.length ?? 5
  cutCount.value = structure?.cuts.length ?? activeCount
  if (structure) {
    sourceBrief.value = structure.source_brief
    cuts.value = structure.cuts.map((cut) => ({ ...cut }))
    editorVisible.value = true
  } else {
    sourceBrief.value = ''
    resizeCuts(cutCount.value)
    editorVisible.value = false
  }
  if (draftIntents) {
    intents.value = draftIntents.map(({ cut_id, intent }) => ({ cut_id, ...intent }))
    editorVisible.value = true
  } else if (store.server?.baseline) {
    intents.value = store.server.cuts.map((cut) => ({
      cut_id: cut.cut_id,
      prompt: cut.effective_intent?.prompt ?? '',
      dialogue: cut.effective_intent?.dialogue ?? '',
      prompt_origin: cut.effective_intent?.prompt_origin ?? 'user',
    }))
  }
  localEditVersion.value = 0
  isOpen.value = true
  dialogRef.value?.showModal()
}

function close() {
  if (isGenerating.value || isSubmitting.value) return
  isOpen.value = false
  dialogRef.value?.close()
}
function handleCancel(event: Event) {
  if (isGenerating.value || isSubmitting.value) {
    event.preventDefault()
  }
}


function showManualEditor() {
  editorVisible.value = true
  markLocalEdit()
}

async function generateDraft() {
  if (!sourceBrief.value.trim()) {
    generationError.value = '주제 또는 시놉시스를 입력하세요.'
    await store.generateBaselineDraft('', cutCount.value)
    return
  }
  const requestVersion = localEditVersion.value
  const requestTopic = sourceBrief.value
  const requestCount = cutCount.value
  generationError.value = ''
  isGenerating.value = true
  try {
    const result = await store.generateBaselineDraft(
      requestTopic,
      requestCount,
      () => localEditVersion.value === requestVersion && sourceBrief.value === requestTopic && cutCount.value === requestCount,
    )
    if (!result) {
      generationError.value = '생성에 실패했습니다. 입력을 확인하고 다시 시도하거나 수동 입력을 사용하세요.'
      return
    }
    if (store.server?.baseline && store.server.cuts.length !== result.cut_count) {
      generationError.value = '기존 활성 컷 수와 다른 초안입니다. 먼저 컷 추가/비활성화로 구성을 명시적으로 변경하세요.'
      return
    }
    sourceBrief.value = result.source_brief
    cutCount.value = result.cut_count
    const activeIds = store.server?.baseline ? store.server.cuts.map((cut) => cut.cut_id) : result.cuts.map((cut) => cut.display_order)
    cuts.value = result.cuts.map((cut, index) => ({ cut_id: activeIds[index] as CutId, role: cut.role, beat: cut.beat }))
    intents.value = result.cuts.map((cut, index) => ({ cut_id: activeIds[index] as CutId, prompt: cut.prompt, dialogue: cut.dialogue, prompt_origin: 'llm_draft' as const }))
    editorVisible.value = true
  } finally {
    isGenerating.value = false
  }
}

function updateDraft() {
  const structure: BaselineStructureDTO = {
    source_brief: sourceBrief.value,
    cuts: cuts.value.map((cut) => ({ ...cut })) as BaselineStructureDTO['cuts'],
  }
  store.setBaselineDraft(
    structure,
    intents.value.map(({ cut_id, prompt, dialogue, prompt_origin }) => ({
      cut_id,
      intent: { prompt, dialogue, prompt_origin },
    })),
    false,
  )
}

async function submit() {
  if (isSubmitting.value || isGenerating.value) return
  updateDraft()
  isSubmitting.value = true
  try {
    const saved = await store.saveBaselineDraft()
    if (saved) {
      isSubmitting.value = false
      close()
    }
  } finally {
    isSubmitting.value = false
  }
}

defineExpose({ open })
</script>

<template>
  <dialog
    ref="dialogRef"
    class="rebaseline-dialog"
    aria-label="Baseline 설정"
    :aria-busy="isGenerating ? 'true' : 'false'"
    @cancel="handleCancel"
    @close="close"
  >
    <div class="rebaseline-content" v-if="isOpen">
      <h2 class="rebaseline-title">{{ hasBaseline ? 'Re-baseline' : '새 웹툰 시작' }}</h2>

      <section class="ai-start" aria-labelledby="draft-heading">
        <h3 id="draft-heading">스토리보드 초안</h3>
        <label class="field-label" for="source-brief">
          주제 또는 시놉시스
          <textarea
            id="source-brief"
            class="field-textarea topic-input"
            v-model="sourceBrief"
            rows="3"
            placeholder="예: 비 오는 밤, 길 잃은 로봇이 고양이를 만난다"
            @input="markLocalEdit"
          />
        </label>
        <label class="field-label count-label" for="cut-count">
          컷 수
          <input id="cut-count" class="field-input" type="number" min="1" step="1" v-model.number="cutCount" @change="resizeCuts(cutCount)" />
        </label>
        <div class="ai-actions">
          <button class="btn btn-ai" type="button" :disabled="isGenerating || isSubmitting" :aria-busy="isGenerating ? 'true' : 'false'" @click="generateDraft">
            {{ isGenerating ? 'AI 콘티 생성 중…' : 'AI 콘티 자동 생성' }}
          </button>
          <button class="btn btn-manual" type="button" :disabled="isGenerating || isSubmitting" @click="showManualEditor">수동 입력</button>
        </div>
        <p v-if="isGenerating" class="generation-status" aria-live="polite">AI 콘티 생성 중… 잠시만 기다려 주세요.</p>
        <p v-if="generationError" class="generation-error" role="alert">{{ generationError }}</p>
      </section>

      <section v-if="editorVisible" class="cut-editor" aria-label="컷 상세 편집">
        <div v-for="(cut, idx) in cuts" :key="cut.cut_id" class="cut-fields">
          <h3 class="cut-field-title">컷 {{ cut.cut_id }}</h3>
          <label class="field-label">역할<input class="field-input" v-model="cut.role" @input="markLocalEdit" /></label>
          <label class="field-label">비트<input class="field-input" v-model="cut.beat" @input="markLocalEdit" /></label>
          <label class="field-label">프롬프트<textarea class="field-textarea" v-model="intents[idx].prompt" rows="3" @input="markPromptEdited(cut.cut_id)" /></label>
          <label class="field-label">대사<input class="field-input" v-model="intents[idx].dialogue" @input="markLocalEdit" /></label>
        </div>
      </section>

      <footer class="rebaseline-footer">
        <button class="btn btn-cancel" type="button" :disabled="isSubmitting || isGenerating" @click="close">취소</button>
        <button class="btn btn-confirm" type="button" :disabled="isSubmitting || isGenerating" @click="submit">
          {{ isSubmitting ? '승인 중…' : '승인' }}
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
.rebaseline-dialog::backdrop { background: rgba(0,0,0,0.5); }
.rebaseline-content {
  padding: var(--sp-16);
  display: flex;
  flex-direction: column;
  gap: var(--sp-12);
  max-height: 90vh;
  overflow: auto;
}
.rebaseline-title { font-size: var(--font-size-heading); font-weight: 600; }
.ai-start {
  display: flex;
  flex-direction: column;
  gap: var(--sp-8);
  padding: var(--sp-12);
  border: 2px solid var(--accent);
  border-radius: var(--radius-inner);
  background: color-mix(in srgb, var(--accent) 6%, var(--surface-white));
}
.ai-start h3 { font-size: var(--font-size-body); font-weight: 700; }
.topic-input { min-height: 76px; }
.ai-actions { display: flex; gap: var(--sp-8); flex-wrap: wrap; }
.generation-status { color: var(--accent); font-size: var(--font-size-sm); }
.generation-error { color: var(--text-danger, #b42318); font-size: var(--font-size-sm); }
.cut-editor { display: flex; flex-direction: column; gap: var(--sp-8); }
.cut-fields {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  padding: var(--sp-8);
  background: var(--surface-light);
  border-radius: var(--radius-inner);
}
.cut-field-title { font-size: var(--font-size-body); font-weight: 600; }
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
.field-textarea { resize: vertical; line-height: var(--line-height); }
.rebaseline-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-8);
  padding-top: var(--sp-8);
  border-top: 1px solid var(--border);
}
.btn { padding: var(--sp-8) var(--sp-24); border-radius: var(--radius-sm); font-weight: 600; min-height: 40px; }
.btn-ai { background: var(--accent); color: #fff; }
.btn-ai:hover { background: var(--accent-hover); }
.btn-manual, .btn-cancel { border: 1px solid var(--border); background: var(--surface-white); }
.btn-manual:hover, .btn-cancel:hover { background: var(--surface-light); }
.btn-confirm { background: var(--accent); color: #fff; }
.btn-confirm:hover { background: var(--accent-hover); }
</style>
