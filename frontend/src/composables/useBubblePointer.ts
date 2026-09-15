/** Pointer math and capture for bubble move/resize — Plan §6.1 */

import { ref, type Ref } from 'vue'
import type { PercentageRect } from '@/domain/geometry'
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
  startRect: PercentageRect
  frozenSurfaceRect: DOMRect
  transientRect: PercentageRect
}

export function useBubblePointer(
  surfaceRef: Readonly<Ref<HTMLElement | null>>,
) {
  const gesture = ref<GestureState | null>(null)

  function startGesture(
    e: PointerEvent,
    startRect: PercentageRect,
    mode: GestureMode,
    handle: ResizeHandle | null,
  ) {
    if (e.button !== 0) return // primary only
    const surface = surfaceRef.value
    if (!surface) return

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
      frozenSurfaceRect: surface.getBoundingClientRect(),
      transientRect: { ...startRect },
    }
  }

  function moveGesture(e: PointerEvent): PercentageRect | null {
    const g = gesture.value
    if (!g || !g.active || e.pointerId !== g.pointerId) return null

    const dxPct = ((e.clientX - g.startClientX) / g.frozenSurfaceRect.width) * 100
    const dyPct = ((e.clientY - g.startClientY) / g.frozenSurfaceRect.height) * 100

    let result: PercentageRect
    if (g.mode === 'move') {
      result = applyMoveDelta(g.startRect, dxPct, dyPct)
    } else {
      result = applyResizeDelta(g.startRect, g.handle!, dxPct, dyPct)
    }

    g.transientRect = result
    return result
  }

  function endGesture(e: PointerEvent): PercentageRect | null {
    const g = gesture.value
    if (!g || e.pointerId !== g.pointerId) return null

    const el = e.currentTarget as HTMLElement
    el.releasePointerCapture(e.pointerId)

    const finalRect: PercentageRect = {
      x_pct: round4(g.transientRect.x_pct),
      y_pct: round4(g.transientRect.y_pct),
      w_pct: round4(g.transientRect.w_pct),
      h_pct: round4(g.transientRect.h_pct),
    }

    gesture.value = null
    return finalRect
  }

  function cancelGesture(e: PointerEvent): PercentageRect | null {
    const g = gesture.value
    if (!g || e.pointerId !== g.pointerId) return null

    const el = e.currentTarget as HTMLElement | null
    if (el) {
      try { el.releasePointerCapture(e.pointerId) } catch { /* already released */ }
    }

    // Return to starting rect (last local draft), not transient
    const startRect = { ...g.startRect }
    gesture.value = null
    return startRect
  }

  return {
    gesture,
    startGesture,
    moveGesture,
    endGesture,
    cancelGesture,
  }
}
