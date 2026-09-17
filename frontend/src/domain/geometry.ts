/** Pure geometry functions for resolved integer slots and cut-local bubbles. */

export function clamp(val: number, min: number, max: number): number {
  return val < min ? min : val > max ? max : val
}

export function round4(val: number): number {
  return Math.round(val * 10000) / 10000
}

export const MIN_BUBBLE_W = 2
export const MIN_BUBBLE_H = 1
export const NUDGE_STEP = 0.5
export const NUDGE_SHIFT_STEP = 2.0

export interface ResolvedSlot {
  cut_id: number
  top_px: number
  bottom_px: number
  height_px: number
}

export interface LocalPercentageRect {
  local_x_pct: number
  local_y_pct: number
  local_w_pct: number
  local_h_pct: number
}

export interface CanvasPercentageRect {
  x_pct: number
  y_pct: number
  w_pct: number
  h_pct: number
}

function assertInteger(value: number, name: string): void {
  if (!Number.isSafeInteger(value)) throw new Error(`${name} must be an integer`)
}

export function computeCutSlots(
  slotHeightsPx: readonly number[],
  gapPx: number,
  orderedCutIds?: readonly number[],
): ResolvedSlot[] {
  if (!Array.isArray(slotHeightsPx) || slotHeightsPx.length === 0) throw new Error('slotHeightsPx must be a non-empty array')
  assertInteger(gapPx, 'gapPx')
  if (gapPx < 0) throw new Error('gapPx must be non-negative')
  const ids = orderedCutIds ? [...orderedCutIds] : slotHeightsPx.map((_, index) => index + 1)
  if (ids.length !== slotHeightsPx.length || ids.some((id) => !Number.isSafeInteger(id) || id < 1) || new Set(ids).size !== ids.length) {
    throw new Error('orderedCutIds must contain unique positive IDs matching slotHeightsPx')
  }
  const slots: ResolvedSlot[] = []
  let cursor = 0
  for (let i = 0; i < slotHeightsPx.length; i += 1) {
    const height = slotHeightsPx[i]
    assertInteger(height, `slotHeightsPx[${i}]`)
    if (height <= 0) throw new Error(`slotHeightsPx[${i}] must be positive`)
    const top = cursor
    const bottom = top + height
    slots.push({ cut_id: ids[i], top_px: top, bottom_px: bottom, height_px: height })
    cursor = bottom + (i < slotHeightsPx.length - 1 ? gapPx : 0)
  }
  return slots
}

export function canvasHeight(slots: readonly ResolvedSlot[], gapPx?: number): number {
  if (slots.length === 0) throw new Error('slots must be non-empty')
  const last = slots[slots.length - 1]
  if (gapPx !== undefined) {
    assertInteger(gapPx, 'gapPx')
    if (gapPx < 0) throw new Error('gapPx must be non-negative')
  }
  return last.bottom_px
}

export function projectLocalRectToCanvas(
  localRect: LocalPercentageRect,
  slot: ResolvedSlot,
  widthPx: number,
  heightPx: number,
): CanvasPercentageRect {
  if (!Number.isFinite(widthPx) || widthPx <= 0 || !Number.isFinite(heightPx) || heightPx <= 0) {
    throw new Error('canvas dimensions must be positive')
  }
  const localRight = localRect.local_x_pct + localRect.local_w_pct
  const localBottom = localRect.local_y_pct + localRect.local_h_pct
  if (
    localRect.local_x_pct < 0 || localRect.local_y_pct < 0 ||
    localRect.local_w_pct <= 0 || localRect.local_h_pct <= 0 ||
    localRight > 100 || localBottom > 100
  ) throw new Error('local bubble rectangle is outside its slot')
  return {
    x_pct: localRect.local_x_pct,
    y_pct: ((slot.top_px + localRect.local_y_pct * slot.height_px / 100) / heightPx) * 100,
    w_pct: localRect.local_w_pct,
    h_pct: (localRect.local_h_pct * slot.height_px / 100 / heightPx) * 100,
  }
}

function clampX(x: number, w: number): number {
  return clamp(x, 0, 100 - w)
}
function clampY(y: number, h: number): number {
  return clamp(y, 0, 100 - h)
}

export function applyMoveDelta(start: LocalPercentageRect, dxPct: number, dyPct: number): LocalPercentageRect {
  return {
    local_x_pct: round4(clampX(start.local_x_pct + dxPct, start.local_w_pct)),
    local_y_pct: round4(clampY(start.local_y_pct + dyPct, start.local_h_pct)),
    local_w_pct: start.local_w_pct,
    local_h_pct: start.local_h_pct,
  }
}

export function applyNudge(
  rect: LocalPercentageRect,
  dir: 'left' | 'right' | 'up' | 'down',
  shift: boolean,
): LocalPercentageRect {
  const step = shift ? NUDGE_SHIFT_STEP : NUDGE_STEP
  const dx = dir === 'left' ? -step : dir === 'right' ? step : 0
  const dy = dir === 'up' ? -step : dir === 'down' ? step : 0
  return applyMoveDelta(rect, dx, dy)
}

export function applyResizeDelta(
  start: LocalPercentageRect,
  handle: 'se' | 'sw' | 'ne' | 'nw' | 'e' | 'w' | 'n' | 's',
  dxPct: number,
  dyPct: number,
): LocalPercentageRect {
  let { local_x_pct: x, local_y_pct: y, local_w_pct: w, local_h_pct: h } = start
  const right = x + w
  const bottom = y + h
  if (handle.includes('e')) w = clamp(w + dxPct, MIN_BUBBLE_W, 100 - x)
  if (handle.includes('w')) {
    const nextX = clamp(x + dxPct, 0, right - MIN_BUBBLE_W)
    w = right - nextX
    x = nextX
  }
  if (handle.includes('s')) h = clamp(h + dyPct, MIN_BUBBLE_H, 100 - y)
  if (handle.includes('n')) {
    const nextY = clamp(y + dyPct, 0, bottom - MIN_BUBBLE_H)
    h = bottom - nextY
    y = nextY
  }
  return {
    local_x_pct: round4(x),
    local_y_pct: round4(y),
    local_w_pct: round4(w),
    local_h_pct: round4(h),
  }
}
