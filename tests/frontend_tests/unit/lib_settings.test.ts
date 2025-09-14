import { describe, it, expect } from 'vitest'
import * as settings from '@src/lib/settings'
describe('settings.ts', () => {
  it('loads and exports something', () => {
    expect(settings).toBeTruthy()
  })
})
