import { describe, expect, it } from 'vitest'
import {
  applyMoveDelta,
  applyNudge,
  applyResizeDelta,
  computeCutSlots,
  MIN_BUBBLE_H,
  MIN_BUBBLE_W,
  NUDGE_SHIFT_STEP,
  NUDGE_STEP,
  projectLocalRectToCanvas,
} from '@/domain/geometry'

describe('geometry: resolved integer slots', () => {
  it.each([
    [[7680], 24, [{ cut_id: 1, top_px: 0, bottom_px: 7680, height_px: 7680 }]],
    [[1000, 1201], 24, [
      { cut_id: 1, top_px: 0, bottom_px: 1000, height_px: 1000 },
      { cut_id: 2, top_px: 1024, bottom_px: 2225, height_px: 1201 },
    ]],
    [[1516, 1517, 1517, 1517, 1517], 24, [
      { cut_id: 1, top_px: 0, bottom_px: 1516, height_px: 1516 },
      { cut_id: 2, top_px: 1540, bottom_px: 3057, height_px: 1517 },
      { cut_id: 3, top_px: 3081, bottom_px: 4598, height_px: 1517 },
      { cut_id: 4, top_px: 4622, bottom_px: 6139, height_px: 1517 },
      { cut_id: 5, top_px: 6163, bottom_px: 7680, height_px: 1517 },
    ]],
  ] as const)('resolves exact cumulative bounds', (heights, gap, expected) => {
    expect(computeCutSlots(heights, gap)).toEqual(expected)
  })

  it('rejects empty, non-positive and negative inputs', () => {
    expect(() => computeCutSlots([], 24)).toThrow()
    expect(() => computeCutSlots([0], 24)).toThrow()
    expect(() => computeCutSlots([1], -1)).toThrow()
  })

  it('projects local rect within the owner slot', () => {
    const slot = computeCutSlots([1000, 1200], 24)[1]
    expect(projectLocalRectToCanvas({ local_x_pct: 10, local_y_pct: 5, local_w_pct: 30, local_h_pct: 15 }, slot, 1024, 2224)).toEqual({
      x_pct: 10,
      y_pct: ((1024 + 60) / 2224) * 100,
      w_pct: 30,
      h_pct: (180 / 2224) * 100,
    })
  })
})

describe('geometry: cut-local move and nudge', () => {
  it('moves within local bounds and rounds', () => {
    const start = { local_x_pct: 10, local_y_pct: 20, local_w_pct: 30, local_h_pct: 10 }
    expect(applyMoveDelta(start, 5, -3)).toEqual({ local_x_pct: 15, local_y_pct: 17, local_w_pct: 30, local_h_pct: 10 })
  })
  it('clamps local edges', () => {
    const result = applyMoveDelta({ local_x_pct: 80, local_y_pct: 95, local_w_pct: 30, local_h_pct: 10 }, 50, 50)
    expect(result.local_x_pct).toBe(70)
    expect(result.local_y_pct).toBe(90)
  })
  it('uses exact nudge steps', () => {
    expect(NUDGE_STEP).toBe(0.5)
    expect(NUDGE_SHIFT_STEP).toBe(2)
    const rect = { local_x_pct: 50, local_y_pct: 50, local_w_pct: 10, local_h_pct: 5 }
    expect(applyNudge(rect, 'right', false).local_x_pct).toBe(50.5)
    expect(applyNudge(rect, 'down', true).local_y_pct).toBe(52)
  })
})

describe('geometry: cut-local resize', () => {
  const start = { local_x_pct: 30, local_y_pct: 40, local_w_pct: 20, local_h_pct: 10 }
  it('resizes SE and NW', () => {
    expect(applyResizeDelta(start, 'se', 5, 3)).toEqual({ local_x_pct: 30, local_y_pct: 40, local_w_pct: 25, local_h_pct: 13 })
    expect(applyResizeDelta(start, 'nw', -5, -3)).toEqual({ local_x_pct: 25, local_y_pct: 37, local_w_pct: 25, local_h_pct: 13 })
  })
  it('enforces minimum dimensions and local boundaries', () => {
    const small = applyResizeDelta({ local_x_pct: 50, local_y_pct: 50, local_w_pct: 5, local_h_pct: 3 }, 'se', -10, -10)
    expect(small.local_w_pct).toBeGreaterThanOrEqual(MIN_BUBBLE_W)
    expect(small.local_h_pct).toBeGreaterThanOrEqual(MIN_BUBBLE_H)
    const large = applyResizeDelta(start, 'se', 200, 200)
    expect(large.local_x_pct + large.local_w_pct).toBeLessThanOrEqual(100)
    expect(large.local_y_pct + large.local_h_pct).toBeLessThanOrEqual(100)
  })
})
