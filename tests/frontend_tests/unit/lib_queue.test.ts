import { describe, it, expect } from 'vitest'
import * as mod from '@src/lib/queue'

describe('queue.ts API surface', () => {
  it('module loads', () => {
    expect(mod).toBeTruthy()
  })
})
