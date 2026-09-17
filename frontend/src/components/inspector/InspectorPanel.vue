<script setup lang="ts">
import { computed } from 'vue'
import { useStudioStore } from '@/store/studio'
import type { CutIntentInputDTO, BubbleDTO } from '@/api/contracts'

const store = useStudioStore()

const selectedCut = computed(() =>
  store.server?.cuts.find((c) => c.cut_id === store.selection.cutId) ?? null,
)

const activeComposition = computed(() =>
  store.drafts.composition?.value.state ?? store.server?.composition.state ?? store.server?.render_contract.default_composition ?? null,
)

const selectedBubble = computed((): BubbleDTO | null => {
  if (!store.selection.bubbleId) return null
  return activeComposition.value?.bubbles.find(
    (bubble) => bubble.bubble_id === store.selection.bubbleId,
  ) ?? null
})

const currentIntent = computed<CutIntentInputDTO>(() =>
  store.drafts.intents[store.selection.cutId]?.value ??
  selectedCut.value?.effective_intent ??
  { prompt: '', dialogue: '' },
)

const intentPrompt = computed({
  get: () => currentIntent.value.prompt,
  set: (prompt: string) => {
    store.setIntentDraft(
      store.selection.cutId,
      { ...currentIntent.value, prompt },
      false,
    )
  },
})

const intentDialogue = computed({
  get: () => currentIntent.value.dialogue,
  set: (dialogue: string) => {
    store.setIntentDraft(
      store.selection.cutId,
      { ...currentIntent.value, dialogue },
      false,
    )
  },
})

function saveIntent() {
  store.saveIntentDraft(store.selection.cutId)
}

function updateSelectedBubble(patch: Partial<BubbleDTO>, enqueue = false) {
  const selected = selectedBubble.value
  const composition = activeComposition.value
  if (!selected || selected.anchor_status !== 'ANCHORED' || !composition) return
  store.setCompositionDraft({
    ...composition,
    bubbles: composition.bubbles.map((bubble) =>
      bubble.bubble_id === selected.bubble_id ? { ...bubble, ...patch } as BubbleDTO : bubble,
    ),
  }, enqueue)
}

const bubbleText = computed({
  get: () => selectedBubble.value?.text ?? '',
  set: (text: string) => {
    const selected = selectedBubble.value
    const composition = activeComposition.value
    if (!selected || !composition) return
    // Keep all bubbles of the same cut uniform with the dialogue
    store.setCompositionDraft({
      ...composition,
      bubbles: composition.bubbles.map((bubble) =>
        bubble.cut_id === selected.cut_id ? { ...bubble, text } : bubble,
      ),
    }, false)
  },
})

function saveComposition() {
  store.saveCompositionDraft()
}

function updateBubbleNumber(
  key: 'local_x_pct' | 'local_y_pct' | 'local_w_pct' | 'local_h_pct' | 'font_size_pct' | 'line_spacing_pct',
  event: Event,
) {
  const value = Number((event.target as HTMLInputElement).value)
  if (Number.isFinite(value)) updateSelectedBubble({ [key]: value })
}

function updateBubbleChoice(
  key: 'shape' | 'text_align',
  event: Event,
) {
  updateSelectedBubble({ [key]: (event.target as HTMLSelectElement).value }, true)
}

function updateBubbleColor(
  key: 'text_rgba' | 'fill_rgba' | 'outline_rgba',
  event: Event,
) {
  updateSelectedBubble({ [key]: `${(event.target as HTMLInputElement).value}FF` })
}

function updateGap(event: Event) {
  const composition = activeComposition.value
  const gapPx = Number((event.target as HTMLInputElement).value)
  if (!composition || !Number.isInteger(gapPx)) return
  store.setCompositionDraft({ ...composition, gap_px: gapPx }, false)
}

function addBubble() {
  const composition = activeComposition.value
  if (!composition) return
  const cutId = store.selection.cutId
  const sameCutBubble = composition.bubbles.find((b) => b.cut_id === cutId)
  const bubbleId = `bubble-${crypto.randomUUID()}`
  const bubble: BubbleDTO = {
    anchor_status: 'ANCHORED',
    bubble_id: bubbleId,
    cut_id: cutId,
    shape: 'rounded_rectangle',
    local_x_pct: 25,
    local_y_pct: 5,
    local_w_pct: 50,
    local_h_pct: 20,
    text: sameCutBubble?.text ?? (currentIntent.value.dialogue ?? ''),
    font_size_pct: 2,
    line_spacing_pct: 20,
    text_align: 'center',
    text_rgba: '#000000FF',
    fill_rgba: '#FFFFFFFF',
    outline_rgba: '#17191DFF',
    outline_width_pct: 0.2,
    padding_pct: 5,
  }
  store.setCompositionDraft({
    ...composition,
    bubbles: [...composition.bubbles, bubble],
  })
  store.selectBubble(bubbleId)
}
function reanchorSelectedBubble() {
  const selected = selectedBubble.value
  const composition = activeComposition.value
  if (!selected || selected.anchor_status !== 'REANCHOR_REQUIRED' || !composition) return
  const anchored: BubbleDTO = {
    anchor_status: 'ANCHORED',
    cut_id: store.selection.cutId,
    bubble_id: selected.bubble_id,
    shape: selected.shape,
    local_x_pct: 25,
    local_y_pct: 5,
    local_w_pct: 50,
    local_h_pct: 20,
    text: selected.text,
    font_size_pct: selected.font_size_pct,
    line_spacing_pct: selected.line_spacing_pct,
    text_align: selected.text_align,
    text_rgba: selected.text_rgba,
    fill_rgba: selected.fill_rgba,
    outline_rgba: selected.outline_rgba,
    outline_width_pct: selected.outline_width_pct,
    padding_pct: selected.padding_pct,
  }
  store.setCompositionDraft({
    ...composition,
    bubbles: composition.bubbles.map((bubble) => bubble.bubble_id === selected.bubble_id ? anchored : bubble),
  })
}

function deleteBubble() {
  const selected = selectedBubble.value
  const composition = activeComposition.value
  if (!selected || !composition) return
  store.setCompositionDraft({
    ...composition,
    bubbles: composition.bubbles.filter((bubble) => bubble.bubble_id !== selected.bubble_id),
  })
  store.selectCut(store.selection.cutId)
}

const intentSaveState = computed(() => {
  const key = `intent-${store.selection.cutId}`
  return store.saves[key] ?? null
})

const compSaveState = computed(() => store.saves['composition'] ?? null)
const serverCompositionText = computed(() =>
  JSON.stringify(store.server?.composition.state ?? null, null, 2),
)

// Generation for selected cut
function generateSelectedCut() {
  store.generateCut(store.selection.cutId)
}
</script>

<template>
  <div class="inspector">
    <section class="inspector-section">
      <h2 class="inspector-heading">컷 {{ store.selection.cutId }} 의도</h2>

      <label class="inspector-label">
        프롬프트
        <textarea
          class="inspector-textarea"
          v-model="intentPrompt"
          rows="3"
          @blur="saveIntent"
        />
      </label>

      <label class="inspector-label">
        대사
        <textarea
          class="inspector-textarea"
          v-model="intentDialogue"
          rows="2"
          @blur="saveIntent"
        />
      </label>

      <div class="inspector-save-state" v-if="intentSaveState">
        <span v-if="intentSaveState.state === 'pending'" class="save-pending">저장 중…</span>
        <span v-else-if="intentSaveState.state === 'failed'" class="save-error" role="alert">
          저장 안 됨
          <button class="inline-btn" @click="store.retrySave(`intent-${store.selection.cutId}`)">다시 시도</button>
        </span>
        <span v-else-if="intentSaveState.state === 'conflict'" class="save-error" role="alert">
          충돌 발생
          <button class="inline-btn" @click="store.retrySave(`intent-${store.selection.cutId}`)">최신본에 다시 적용</button>
        </span>
        <span v-else-if="intentSaveState.state === 'base-changed'" class="save-warn">
          서버 변경됨
          <button class="inline-btn" @click="store.retrySave(`intent-${store.selection.cutId}`)">다시 시도</button>
        </span>
        <details v-if="intentSaveState.state === 'conflict'" class="server-comparison">
          <summary>서버 값 보기</summary>
          <p>프롬프트: {{ selectedCut?.effective_intent?.prompt ?? '없음' }}</p>
          <p>대사: {{ selectedCut?.effective_intent?.dialogue ?? '없음' }}</p>
        </details>
      </div>

      <button
        class="inspector-btn"
        :disabled="!store.canGenerate"
        @click="generateSelectedCut"
      >이 컷 생성</button>
    </section>

    <section class="inspector-section" v-if="activeComposition">
      <h2 class="inspector-heading">조판</h2>
      <label class="inspector-label">
        컷 간격 (px)
        <input
          class="inspector-input"
          type="number"
          min="0"
          step="1"
          :value="activeComposition.gap_px"
          @input="updateGap"
          @blur="saveComposition"
        />
      </label>
      <button class="inspector-btn" @click="addBubble">선택 컷에 말풍선 추가</button>
    </section>

    <section class="inspector-section" v-if="selectedBubble?.anchor_status === 'REANCHOR_REQUIRED'" role="alert">
      <h2 class="inspector-heading">말풍선 수동 재배치 필요</h2>
      <p class="inspector-hint">기존 전역 좌표를 안전하게 컷에 귀속할 수 없습니다. 원 좌표를 보존했으며, 현재 컷에 새 말풍선을 추가해 위치를 명시하세요.</p>
      <pre>{{ selectedBubble.legacy_global_rect }}</pre>
      <button class="inspector-btn" @click="reanchorSelectedBubble">현재 컷에 명시적으로 재배치</button>
    </section>
    <section class="inspector-section" v-if="selectedBubble?.anchor_status === 'ANCHORED'">
      <div class="inspector-heading-row">
        <h2 class="inspector-heading">말풍선</h2>
        <button class="delete-btn" @click="deleteBubble">삭제</button>
      </div>
      <label class="inspector-label">
        텍스트
        <textarea
          class="inspector-textarea"
          v-model="bubbleText"
          rows="3"
          @blur="saveComposition"
        />
      </label>
      <div class="field-grid">
        <label v-for="field in ['local_x_pct', 'local_y_pct', 'local_w_pct', 'local_h_pct'] as const" :key="field" class="inspector-label">
          {{ field }}
          <input
            class="inspector-input"
            type="number"
            min="0"
            max="100"
            step="0.1"
            :value="selectedBubble[field]"
            @input="updateBubbleNumber(field, $event)"
            @blur="saveComposition"
          />
        </label>
      </div>
      <div class="field-grid">
        <label class="inspector-label">
          모양
          <select class="inspector-input" :value="selectedBubble.shape" @change="updateBubbleChoice('shape', $event)">
            <option value="rounded_rectangle">둥근 사각형</option>
            <option value="ellipse">타원</option>
          </select>
        </label>
        <label class="inspector-label">
          정렬
          <select class="inspector-input" :value="selectedBubble.text_align" @change="updateBubbleChoice('text_align', $event)">
            <option value="left">왼쪽</option>
            <option value="center">가운데</option>
            <option value="right">오른쪽</option>
          </select>
        </label>
        <label class="inspector-label">
          글자 크기 (%)
          <input class="inspector-input" type="number" min="0.1" max="100" step="0.1" :value="selectedBubble.font_size_pct" @input="updateBubbleNumber('font_size_pct', $event)" @blur="saveComposition" />
        </label>
        <label class="inspector-label">
          줄 간격 (%)
          <input class="inspector-input" type="number" min="0" max="500" step="1" :value="selectedBubble.line_spacing_pct" @input="updateBubbleNumber('line_spacing_pct', $event)" @blur="saveComposition" />
        </label>
      </div>
      <div class="field-grid color-grid">
        <label v-for="field in ['text_rgba', 'fill_rgba', 'outline_rgba'] as const" :key="field" class="inspector-label">
          {{ field }}
          <input class="color-input" type="color" :value="selectedBubble[field].slice(0, 7)" @input="updateBubbleColor(field, $event)" @blur="saveComposition" />
        </label>
      </div>

      <div class="inspector-save-state" v-if="compSaveState">
        <span v-if="compSaveState.state === 'pending'" class="save-pending">저장 중…</span>
        <span v-else-if="compSaveState.state === 'failed'" class="save-error" role="alert">
          저장 안 됨
          <button class="inline-btn" @click="store.retrySave('composition')">다시 시도</button>
        </span>
        <span v-else-if="compSaveState.state === 'conflict'" class="save-error" role="alert">
          충돌 발생
          <button class="inline-btn" @click="store.retrySave('composition')">최신본에 다시 적용</button>
        </span>
        <span v-else-if="compSaveState.state === 'base-changed'" class="save-warn">
          서버 변경됨
          <button class="inline-btn" @click="store.retrySave('composition')">최신본에 다시 적용</button>
        </span>
        <details v-if="compSaveState.state === 'conflict'" class="server-comparison">
          <summary>서버 값 보기</summary>
          <pre>{{ serverCompositionText }}</pre>
        </details>
      </div>
    </section>

    <section class="inspector-section" v-if="!selectedBubble && selectedCut">
      <p class="inspector-hint">말풍선을 추가하거나 캔버스에서 선택하세요.</p>
    </section>
  </div>
</template>

<style scoped>
.inspector {
  padding: var(--sp-12);
  display: flex;
  flex-direction: column;
  gap: var(--sp-16);
}

.inspector-section {
  display: flex;
  flex-direction: column;
  gap: var(--sp-8);
}

.inspector-heading {
  font-size: var(--font-size-body);
  font-weight: 600;
  margin: 0;
}

.inspector-label {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  font-weight: 500;
}

.inspector-textarea,
.inspector-input {
  width: 100%;
  padding: var(--sp-8);
  border: 1px solid var(--border);
  border-radius: var(--radius-inner);
  font-size: var(--font-size-body);
  background: var(--surface-white);
  line-height: var(--line-height);
}
.inspector-textarea {
  resize: vertical;
}
.inspector-textarea:focus,
.inspector-input:focus {
  border-color: var(--accent);
}

.inspector-btn {
  padding: var(--sp-8) var(--sp-16);
  background: var(--accent);
  color: #fff;
  border-radius: var(--radius-sm);
  font-weight: 500;
  font-size: var(--font-size-sm);
  min-height: 36px;
}
.inspector-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.inspector-btn:not(:disabled):hover {
  background: var(--accent-hover);
}

.inspector-heading-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.delete-btn {
  color: var(--color-error);
  font-size: var(--font-size-xs);
  text-decoration: underline;
}
.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--sp-8);
}
.color-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}
.color-input {
  width: 100%;
  min-height: 36px;
  border: 1px solid var(--border);
  border-radius: var(--radius-inner);
}
.inspector-meta {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-size-sm);
}
.meta-label {
  color: var(--text-secondary);
}
.meta-value {
  font-weight: 500;
}

.inspector-save-state {
  font-size: var(--font-size-sm);
}
.save-pending {
  color: var(--text-secondary);
}
.save-error {
  color: var(--color-error);
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  flex-wrap: wrap;
}
.save-warn {
  color: var(--color-stale);
  display: flex;
  align-items: center;
  gap: var(--sp-4);
}

.inline-btn {
  font-size: var(--font-size-xs);
  text-decoration: underline;
  color: var(--accent);
  padding: 0;
  min-height: auto;
}

.inspector-hint {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  font-style: italic;
}
.server-comparison {
  margin-top: var(--sp-8);
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
}
.server-comparison summary {
  color: var(--accent-hover);
  cursor: pointer;
  font-weight: 600;
}
.server-comparison pre {
  max-height: 160px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

</style>
