/** Pure geometry functions — clamp, normalize, round for canonical percentage coordinates. */

/** Clamp val to [min, max]. */
export function clamp(val: number, min: number, max: number): number {
  return val < min ? min : val > max ? max : val
}

/** Round to 4 decimal places. */
export function round4(val: number): number {
  return Math.round(val * 10000) / 10000
}

/** Clamp x_pct so that [x_pct, x_pct+w_pct] stays within [0,100]. */
export function clampX(x: number, w: number): number {
  return clamp(x, 0, 100 - w)
}

/** Clamp y_pct so that [y_pct, y_pct+h_pct] stays within [0,100]. */
export function clampY(y: number, h: number): number {
  return clamp(y, 0, 100 - h)
}

/** Minimum bubble dimension (percentage). */
export const MIN_BUBBLE_W = 2
export const MIN_BUBBLE_H = 1

/** Arrow key nudge steps — THESIS-001 §6.5 exact. */
export const NUDGE_STEP = 0.5
export const NUDGE_SHIFT_STEP = 2.0

export interface PercentageRect {
  x_pct: number
  y_pct: number
  w_pct: number
  h_pct: number
}

/** Apply a move delta and clamp. Returns rounded rect. */
export function applyMoveDelta(
  start: PercentageRect,
  dxPct: number,
  dyPct: number,
): PercentageRect {
  return {
    x_pct: round4(clampX(start.x_pct + dxPct, start.w_pct)),
    y_pct: round4(clampY(start.y_pct + dyPct, start.h_pct)),
    w_pct: start.w_pct,
    h_pct: start.h_pct,
  }
}

/** Apply keyboard nudge in a direction. */
export function applyNudge(
  rect: PercentageRect,
  dir: 'left' | 'right' | 'up' | 'down',
  shift: boolean,
): PercentageRect {
  const step = shift ? NUDGE_SHIFT_STEP : NUDGE_STEP
  let dx = 0
  let dy = 0
  switch (dir) {
    case 'left': dx = -step; break
    case 'right': dx = step; break
    case 'up': dy = -step; break
    case 'down': dy = step; break
  }
  return applyMoveDelta(rect, dx, dy)
}

/** Apply a resize delta from a corner/edge handle. Returns rounded rect with min dimension enforce. */
export function applyResizeDelta(
  start: PercentageRect,
  handle: 'se' | 'sw' | 'ne' | 'nw' | 'e' | 'w' | 'n' | 's',
  dxPct: number,
  dyPct: number,
): PercentageRect {
  let { x_pct, y_pct, w_pct, h_pct } = start
  const right = x_pct + w_pct
  const bottom = y_pct + h_pct

  // Adjust edges based on handle
  if (handle.includes('e')) {
    w_pct = clamp(w_pct + dxPct, MIN_BUBBLE_W, 100 - x_pct)
  }
  if (handle.includes('w')) {
    const newX = clamp(x_pct + dxPct, 0, right - MIN_BUBBLE_W)
    w_pct = right - newX
    x_pct = newX
  }
  if (handle.includes('s')) {
    h_pct = clamp(h_pct + dyPct, MIN_BUBBLE_H, 100 - y_pct)
  }
  if (handle.includes('n')) {
    const newY = clamp(y_pct + dyPct, 0, bottom - MIN_BUBBLE_H)
    h_pct = bottom - newY
    y_pct = newY
  }

  return {
    x_pct: round4(x_pct),
    y_pct: round4(y_pct),
    w_pct: round4(w_pct),
    h_pct: round4(h_pct),
  }
}
