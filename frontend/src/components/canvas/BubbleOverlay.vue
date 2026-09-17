<script setup lang="ts">
import { ref, computed, type CSSProperties } from 'vue'
import type { AnchoredBubbleDTO, ResolvedSlotDTO } from '@/api/contracts'
import type { CanvasPercentageRect, LocalPercentageRect } from '@/domain/geometry'
import { applyNudge, applyResizeDelta, NUDGE_SHIFT_STEP, NUDGE_STEP, projectLocalRectToCanvas } from '@/domain/geometry'
import { useBubblePointer } from '@/composables/useBubblePointer'

const props = defineProps<{
  bubble: AnchoredBubbleDTO
  slot: ResolvedSlotDTO
  slotElement: HTMLElement | null
  projectedRect: CanvasPercentageRect
  canvasWidthPx: number
  canvasHeightPx: number
  selected: boolean
}>()

const emit = defineEmits<{
  commit: [rect: LocalPercentageRect]
  select: []
}>()

const slotRef = computed(() => props.slotElement)
const { gesture, startGesture, moveGesture, endGesture, cancelGesture } = useBubblePointer(slotRef)
const animFrame = ref(0)

const localRect = (): LocalPercentageRect => ({
  local_x_pct: props.bubble.local_x_pct,
  local_y_pct: props.bubble.local_y_pct,
  local_w_pct: props.bubble.local_w_pct,
  local_h_pct: props.bubble.local_h_pct,
})

const displayRect = computed((): CanvasPercentageRect => {
  if (!gesture.value?.active) return props.projectedRect
  return projectLocalRectToCanvas(
    gesture.value.transientRect,
    props.slot,
    props.canvasWidthPx,
    props.canvasHeightPx,
  )
})

function onPointerDown(e: PointerEvent) {
  emit('select')
  startGesture(e, localRect(), 'move', null)
}

function onPointerMove(e: PointerEvent) {
  cancelAnimationFrame(animFrame.value)
  animFrame.value = requestAnimationFrame(() => { moveGesture(e) })
}

function onPointerUp(e: PointerEvent) {
  cancelAnimationFrame(animFrame.value)
  const result = endGesture(e)
  if (result) emit('commit', result)
}

function onPointerCancel(e: PointerEvent) {
  cancelAnimationFrame(animFrame.value)
  cancelGesture(e)
}

function onResizeDown(e: PointerEvent, handle: 'se' | 'sw' | 'ne' | 'nw' | 'e' | 'w' | 'n' | 's') {
  e.stopPropagation()
  emit('select')
  startGesture(e, localRect(), 'resize', handle)
}

function onKeyDown(e: KeyboardEvent) {
  const dirMap: Record<string, 'left' | 'right' | 'up' | 'down'> = {
    ArrowLeft: 'left', ArrowRight: 'right', ArrowUp: 'up', ArrowDown: 'down',
  }
  const dir = dirMap[e.key]
  if (!dir) return
  e.preventDefault()
  emit('commit', applyNudge(localRect(), dir, e.shiftKey))
}

function onResizeKeyDown(
  e: KeyboardEvent,
  handle: 'se' | 'sw' | 'ne' | 'nw' | 'e' | 'w' | 'n' | 's',
) {
  const step = e.shiftKey ? NUDGE_SHIFT_STEP : NUDGE_STEP
  const delta = {
    ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step],
  }[e.key]
  if (!delta) return
  e.preventDefault()
  emit('commit', applyResizeDelta(localRect(), handle, delta[0], delta[1]))
}

const HANDLES = ['nw', 'ne', 'sw', 'se', 'n', 's', 'e', 'w'] as const
const bubbleTextStyle = computed((): CSSProperties => ({ textAlign: props.bubble.text_align }))
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
    <div class="bubble-text" :style="bubbleTextStyle">{{ bubble.text }}</div>
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
.bubble-overlay.selected { outline: 2px solid var(--accent); z-index: 5; }
.bubble-text { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; padding: var(--sp-4); pointer-events: none; overflow: hidden; white-space: pre-wrap; word-break: break-word; }
.resize-handle { position: absolute; width: 10px; height: 10px; border: 1px solid var(--accent); background: var(--surface); border-radius: 50%; padding: 0; }
.handle-nw { top: -5px; left: -5px; cursor: nw-resize; }
.handle-ne { top: -5px; right: -5px; cursor: ne-resize; }
.handle-sw { bottom: -5px; left: -5px; cursor: sw-resize; }
.handle-se { bottom: -5px; right: -5px; cursor: se-resize; }
.handle-n { top: -5px; left: 50%; transform: translateX(-50%); cursor: n-resize; }
.handle-s { bottom: -5px; left: 50%; transform: translateX(-50%); cursor: s-resize; }
.handle-e { top: 50%; right: -5px; transform: translateY(-50%); cursor: e-resize; }
.handle-w { top: 50%; left: -5px; transform: translateY(-50%); cursor: w-resize; }
</style>
