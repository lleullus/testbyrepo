/** Pointer math and capture for cut-local bubble move/resize. */

import { ref, type Ref } from 'vue'
import type { LocalPercentageRect } from '@/domain/geometry'
import { applyMoveDelta, applyResizeDelta, round4 } from '@/domain/geometry'

export type GestureMode = 'move' | 'resize'
export type ResizeHandle = 'se' | 'sw' | 'ne' | 'nw' | 'e' | 'w' | 'n' | 's'

export interface GestureState {
  active: boolean
  mode: GestureMode
  handle: ResizeHandle | null
  pointerId: number
  startClientX: number
  startClientY: number
  startRect: LocalPercentageRect
  frozenSlotRect: DOMRect
  transientRect: LocalPercentageRect
}

export function useBubblePointer(ownerSlotRef: Readonly<Ref<HTMLElement | null>>) {
  const gesture = ref<GestureState | null>(null)

  function startGesture(
    e: PointerEvent,
    startRect: LocalPercentageRect,
    mode: GestureMode,
    handle: ResizeHandle | null,
  ) {
    if (e.button !== 0) return
    const slot = ownerSlotRef.value
    if (!slot) return
    e.preventDefault()
    const el = e.currentTarget as HTMLElement
    el.setPointerCapture(e.pointerId)
    el.style.touchAction = 'none'
    gesture.value = {
      active: true,
      mode,
      handle,
      pointerId: e.pointerId,
      startClientX: e.clientX,
      startClientY: e.clientY,
      startRect: { ...startRect },
      frozenSlotRect: slot.getBoundingClientRect(),
      transientRect: { ...startRect },
    }
  }

  function moveGesture(e: PointerEvent): LocalPercentageRect | null {
    const current = gesture.value
    if (!current || !current.active || e.pointerId !== current.pointerId) return null
    const dxPct = ((e.clientX - current.startClientX) / current.frozenSlotRect.width) * 100
    const dyPct = ((e.clientY - current.startClientY) / current.frozenSlotRect.height) * 100
    const result = current.mode === 'move'
      ? applyMoveDelta(current.startRect, dxPct, dyPct)
      : applyResizeDelta(current.startRect, current.handle!, dxPct, dyPct)
    current.transientRect = result
    return result
  }

  function endGesture(e: PointerEvent): LocalPercentageRect | null {
    const current = gesture.value
    if (!current || e.pointerId !== current.pointerId) return null
    const el = e.currentTarget as HTMLElement
    el.releasePointerCapture(e.pointerId)
    const finalRect: LocalPercentageRect = {
      local_x_pct: round4(current.transientRect.local_x_pct),
      local_y_pct: round4(current.transientRect.local_y_pct),
      local_w_pct: round4(current.transientRect.local_w_pct),
      local_h_pct: round4(current.transientRect.local_h_pct),
    }
    gesture.value = null
    return finalRect
  }

  function cancelGesture(e: PointerEvent): LocalPercentageRect | null {
    const current = gesture.value
    if (!current || e.pointerId !== current.pointerId) return null
    const el = e.currentTarget as HTMLElement | null
    if (el) {
      try { el.releasePointerCapture(e.pointerId) } catch { /* already released */ }
    }
    const startRect = { ...current.startRect }
    gesture.value = null
    return startRect
  }

  return { gesture, startGesture, moveGesture, endGesture, cancelGesture }
}
