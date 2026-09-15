<script setup lang="ts">
import { ref, computed, type CSSProperties } from 'vue'
import type { BubbleDTO } from '@/api/contracts'
import type { PercentageRect } from '@/domain/geometry'
import { applyNudge, applyResizeDelta, NUDGE_SHIFT_STEP, NUDGE_STEP } from '@/domain/geometry'
import { useBubblePointer } from '@/composables/useBubblePointer'

const props = defineProps<{
  bubble: BubbleDTO
  surfaceRef: HTMLElement | null
  selected: boolean
}>()

const emit = defineEmits<{
  commit: [rect: PercentageRect]
  select: []
}>()

// Computed wrapping props.surfaceRef satisfies Readonly<Ref<HTMLElement | null>>
const surfRef = computed(() => props.surfaceRef)
const { gesture, startGesture, moveGesture, endGesture, cancelGesture } = useBubblePointer(surfRef)
const animFrame = ref(0)

const displayRect = computed((): PercentageRect => {
  if (gesture.value?.active) {
    return gesture.value.transientRect
  }
  return {
    x_pct: props.bubble.x_pct,
    y_pct: props.bubble.y_pct,
    w_pct: props.bubble.w_pct,
    h_pct: props.bubble.h_pct,
  }
})

function onPointerDown(e: PointerEvent) {
  emit('select')
  startGesture(e, {
    x_pct: props.bubble.x_pct,
    y_pct: props.bubble.y_pct,
    w_pct: props.bubble.w_pct,
    h_pct: props.bubble.h_pct,
  }, 'move', null)
}

function onPointerMove(e: PointerEvent) {
  cancelAnimationFrame(animFrame.value)
  animFrame.value = requestAnimationFrame(() => {
    moveGesture(e)
  })
}

function onPointerUp(e: PointerEvent) {
  cancelAnimationFrame(animFrame.value)
  const result = endGesture(e)
  if (result) {
    emit('commit', result)
  }
}

function onPointerCancel(e: PointerEvent) {
  cancelAnimationFrame(animFrame.value)
  cancelGesture(e) // returns to start rect — no commit
}

function onResizeDown(e: PointerEvent, handle: 'se' | 'sw' | 'ne' | 'nw' | 'e' | 'w' | 'n' | 's') {
  e.stopPropagation()
  emit('select')
  startGesture(e, {
    x_pct: props.bubble.x_pct,
    y_pct: props.bubble.y_pct,
    w_pct: props.bubble.w_pct,
    h_pct: props.bubble.h_pct,
  }, 'resize', handle)
}

function onKeyDown(e: KeyboardEvent) {
  const dirMap: Record<string, 'left' | 'right' | 'up' | 'down'> = {
    ArrowLeft: 'left',
    ArrowRight: 'right',
    ArrowUp: 'up',
    ArrowDown: 'down',
  }
  const dir = dirMap[e.key]
  if (!dir) return
  e.preventDefault()
  const rect = applyNudge(
    { x_pct: props.bubble.x_pct, y_pct: props.bubble.y_pct, w_pct: props.bubble.w_pct, h_pct: props.bubble.h_pct },
    dir,
    e.shiftKey,
  )
  emit('commit', rect)
}

function onResizeKeyDown(
  e: KeyboardEvent,
  handle: 'se' | 'sw' | 'ne' | 'nw' | 'e' | 'w' | 'n' | 's',
) {
  const step = e.shiftKey ? NUDGE_SHIFT_STEP : NUDGE_STEP
  const delta = {
    ArrowLeft: [-step, 0],
    ArrowRight: [step, 0],
    ArrowUp: [0, -step],
    ArrowDown: [0, step],
  }[e.key]
  if (!delta) return
  e.preventDefault()
  emit('commit', applyResizeDelta(
    { x_pct: props.bubble.x_pct, y_pct: props.bubble.y_pct, w_pct: props.bubble.w_pct, h_pct: props.bubble.h_pct },
    handle,
    delta[0],
    delta[1],
  ))
}

const HANDLES = ['nw', 'ne', 'sw', 'se', 'n', 's', 'e', 'w'] as const
const bubbleTextStyle = computed((): CSSProperties => ({
  textAlign: props.bubble.text_align,
}))
const bubbleStyle = computed((): CSSProperties => ({
  left: `${displayRect.value.x_pct}%`,
  top: `${displayRect.value.y_pct}%`,
  width: `${displayRect.value.w_pct}%`,
  height: `${displayRect.value.h_pct}%`,
  backgroundColor: props.bubble.fill_rgba,
  borderColor: props.bubble.outline_rgba,
  borderRadius: props.bubble.shape === 'ellipse' ? '50%' : 'var(--radius-inner)',
  color: props.bubble.text_rgba,
  fontSize: `${props.bubble.font_size_pct}cqw`,
  lineHeight: String(1 + props.bubble.line_spacing_pct / 100),
}))
</script>

<template>
  <div
    class="bubble-overlay"
    :class="{ selected }"
    :style="bubbleStyle"
    role="group"
    tabindex="0"
    :aria-label="`말풍선: ${bubble.text}`"
    @pointerdown="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointercancel="onPointerCancel"
    @lostpointercapture="onPointerCancel"
    @keydown="onKeyDown"
    @click.stop="emit('select')"
  >
    <div class="bubble-text" :style="bubbleTextStyle">
      {{ bubble.text }}
    </div>

    <!-- Resize handles (visible only when selected) -->
    <template v-if="selected">
      <button
        v-for="h in HANDLES"
        :key="h"
        type="button"
        :class="['resize-handle', `handle-${h}`]"
        @pointerdown="(e: PointerEvent) => onResizeDown(e, h)"
        @keydown.stop="(e: KeyboardEvent) => onResizeKeyDown(e, h)"
        :aria-label="`크기 조절 ${h}`"
      />
    </template>
  </div>
</template>

<style scoped>
.bubble-overlay {
  position: absolute;
  border: 2px solid transparent;
  border-radius: var(--radius-inner);
  cursor: grab;
  user-select: none;
  touch-action: none;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.bubble-overlay.selected {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
.bubble-overlay:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.bubble-text {
  color: inherit;
  padding: 4px;
  font-size: inherit;
  pointer-events: none;
  word-break: break-word;
  overflow: hidden;
}

/* Resize handles */
.resize-handle {
  position: absolute;
  width: 10px;
  height: 10px;
  background: var(--accent);
  border: 1px solid #fff;
  border-radius: 2px;
  z-index: 1;
  padding: 0;
}
.handle-nw { top: -5px; left: -5px; cursor: nw-resize; }
.handle-ne { top: -5px; right: -5px; cursor: ne-resize; }
.handle-sw { bottom: -5px; left: -5px; cursor: sw-resize; }
.handle-se { bottom: -5px; right: -5px; cursor: se-resize; }
.handle-n { top: -5px; left: 50%; transform: translateX(-50%); cursor: n-resize; }
.handle-s { bottom: -5px; left: 50%; transform: translateX(-50%); cursor: s-resize; }
.handle-e { top: 50%; right: -5px; transform: translateY(-50%); cursor: e-resize; }
.handle-w { top: 50%; left: -5px; transform: translateY(-50%); cursor: w-resize; }
</style>
