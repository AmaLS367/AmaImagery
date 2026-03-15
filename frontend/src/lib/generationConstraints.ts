export const generationConstraints = {
  steps: { min: 24, max: 128, step: 1, default: 28 },
  guidance: { min: 0, max: 20, step: 0.5, default: 7.5 },
  width: { min: 256, max: 1024, step: 64, default: 896 },
  height: { min: 256, max: 1024, step: 64, default: 1024 },
  ipScale: { min: 0, max: 2, step: 0.05, default: 0.65 },
} as const

export type GenerationConstraintKey = keyof typeof generationConstraints

export function clampToConstraint(key: GenerationConstraintKey, value: number): number {
  const constraint = generationConstraints[key]
  if (!Number.isFinite(value)) {
    return constraint.default
  }

  const clamped = Math.min(constraint.max, Math.max(constraint.min, value))
  if (constraint.step >= 1) {
    return Math.round(clamped / constraint.step) * constraint.step
  }

  const precision = String(constraint.step).split('.')[1]?.length ?? 0
  const stepped = Math.round(clamped / constraint.step) * constraint.step
  return Number(stepped.toFixed(precision))
}

export function coerceDimension(value: number, fallback: number): number {
  const next = clampToConstraint('width', value)
  return Number.isFinite(next) ? next : fallback
}
