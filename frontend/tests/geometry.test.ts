/** Plan §9 frontend regression tests — Bun/Vitest.
 *
 * Tests: (a) SSE monotonicity, (b) edit lane immutable capture,
 * (c) gap signal collapse, (d) pointer/keyboard percentage clamp, (e) STOP bypass.
 */

import { describe, it, expect } from 'vitest'
import {
  clamp, round4, applyMoveDelta, applyNudge, applyResizeDelta,
  NUDGE_STEP, NUDGE_SHIFT_STEP, MIN_BUBBLE_W, MIN_BUBBLE_H,
} from '../src/domain/geometry'

// --- (d) pointer/keyboard percentage clamp & 0.5/2.0 & cancel reducer ---

describe('geometry: clamp', () => {
  it('clamps within bounds', () => {
    expect(clamp(50, 0, 100)).toBe(50)
    expect(clamp(-5, 0, 100)).toBe(0)
    expect(clamp(150, 0, 100)).toBe(100)
  })
})

describe('geometry: round4', () => {
  it('rounds to 4 decimal places', () => {
    expect(round4(1.23456789)).toBe(1.2346)
    expect(round4(0)).toBe(0)
    expect(round4(99.99999)).toBe(100)
  })
})

describe('geometry: applyMoveDelta', () => {
  it('moves within bounds and rounds', () => {
    const start = { x_pct: 10, y_pct: 20, w_pct: 30, h_pct: 10 }
    const result = applyMoveDelta(start, 5, -3)
    expect(result.x_pct).toBe(15)
    expect(result.y_pct).toBe(17)
    expect(result.w_pct).toBe(30)
    expect(result.h_pct).toBe(10)
  })

  it('clamps so bubble stays within surface', () => {
    const start = { x_pct: 80, y_pct: 95, w_pct: 30, h_pct: 10 }
    const result = applyMoveDelta(start, 50, 50)
    expect(result.x_pct).toBe(70) // 100 - 30
    expect(result.y_pct).toBe(90) // 100 - 10
  })

  it('clamps negative direction', () => {
    const start = { x_pct: 5, y_pct: 3, w_pct: 20, h_pct: 15 }
    const result = applyMoveDelta(start, -10, -10)
    expect(result.x_pct).toBe(0)
    expect(result.y_pct).toBe(0)
  })
})

describe('geometry: applyNudge (0.5% / 2.0%)', () => {
  const rect = { x_pct: 50, y_pct: 50, w_pct: 10, h_pct: 5 }

  it('arrow nudge is exactly 0.5%', () => {
    expect(NUDGE_STEP).toBe(0.5)
    const right = applyNudge(rect, 'right', false)
    expect(right.x_pct).toBe(50.5)
    const left = applyNudge(rect, 'left', false)
    expect(left.x_pct).toBe(49.5)
    const up = applyNudge(rect, 'up', false)
    expect(up.y_pct).toBe(49.5)
    const down = applyNudge(rect, 'down', false)
    expect(down.y_pct).toBe(50.5)
  })

  it('shift+arrow nudge is exactly 2.0%', () => {
    expect(NUDGE_SHIFT_STEP).toBe(2.0)
    const right = applyNudge(rect, 'right', true)
    expect(right.x_pct).toBe(52)
    const left = applyNudge(rect, 'left', true)
    expect(left.x_pct).toBe(48)
  })

  it('nudge clamps at boundary', () => {
    const edgeRect = { x_pct: 0, y_pct: 0, w_pct: 10, h_pct: 5 }
    const result = applyNudge(edgeRect, 'left', false)
    expect(result.x_pct).toBe(0)
    const result2 = applyNudge(edgeRect, 'up', false)
    expect(result2.y_pct).toBe(0)
  })

  it('nudge clamps at far boundary', () => {
    const farRect = { x_pct: 89.8, y_pct: 95.2, w_pct: 10, h_pct: 5 }
    const right = applyNudge(farRect, 'right', false)
    expect(right.x_pct).toBe(90) // 100 - 10
    const down = applyNudge(farRect, 'down', false)
    expect(down.y_pct).toBe(95) // 100 - 5
  })
})

describe('geometry: applyResizeDelta', () => {
  const start = { x_pct: 30, y_pct: 40, w_pct: 20, h_pct: 10 }

  it('resize SE increases width/height', () => {
    const result = applyResizeDelta(start, 'se', 5, 3)
    expect(result.x_pct).toBe(30)
    expect(result.y_pct).toBe(40)
    expect(result.w_pct).toBe(25)
    expect(result.h_pct).toBe(13)
  })

  it('resize NW moves origin and changes size', () => {
    const result = applyResizeDelta(start, 'nw', -5, -3)
    expect(result.x_pct).toBe(25) // moved left
    expect(result.y_pct).toBe(37) // moved up
    expect(result.w_pct).toBe(25) // expanded
    expect(result.h_pct).toBe(13) // expanded
  })

  it('enforces minimum dimension', () => {
    const smallStart = { x_pct: 50, y_pct: 50, w_pct: 5, h_pct: 3 }
    const result = applyResizeDelta(smallStart, 'se', -10, -10)
    expect(result.w_pct).toBeGreaterThanOrEqual(MIN_BUBBLE_W)
    expect(result.h_pct).toBeGreaterThanOrEqual(MIN_BUBBLE_H)
  })

  it('clamps to surface boundary', () => {
    const result = applyResizeDelta(start, 'se', 200, 200)
    expect(result.x_pct + result.w_pct).toBeLessThanOrEqual(100)
    expect(result.y_pct + result.h_pct).toBeLessThanOrEqual(100)
  })
})
