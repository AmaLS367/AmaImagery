import { describe, it, expect } from 'vitest'
import * as nsfw from '@src/lib/nsfw'
describe('nsfw.ts', () => {
  it('loads and exports something', () => {
    expect(nsfw).toBeTruthy()
  })
})
