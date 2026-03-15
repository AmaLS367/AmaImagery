import { describe, expect, it } from 'vitest'

import { clampToConstraint, generationConstraints } from '@src/lib/generationConstraints'

describe('generationConstraints', () => {
  it('exports runtime-safe limits', () => {
    expect(generationConstraints.steps).toEqual({ min: 24, max: 128, step: 1, default: 28 })
    expect(generationConstraints.width.max).toBe(1024)
    expect(generationConstraints.height.max).toBe(1024)
    expect(generationConstraints.ipScale.max).toBe(2)
  })

  it('clamps and snaps values to safe ranges', () => {
    expect(clampToConstraint('steps', 300)).toBe(128)
    expect(clampToConstraint('steps', 8)).toBe(24)
    expect(clampToConstraint('width', 913)).toBe(896)
    expect(clampToConstraint('height', 2000)).toBe(1024)
    expect(clampToConstraint('ipScale', 0.333)).toBe(0.35)
  })
})
