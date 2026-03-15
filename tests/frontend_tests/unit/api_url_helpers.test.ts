import { describe, expect, it } from 'vitest'

import { toApiUrl, toAssetUrl } from '@src/lib/api'

describe('api url helpers', () => {
  it('keeps relative api paths relative when no base url is configured', () => {
    expect(toApiUrl('/api/v1/auth/me')).toBe('/api/v1/auth/me')
    expect(toApiUrl('api/v1/auth/me')).toBe('/api/v1/auth/me')
  })

  it('passes through absolute urls unchanged', () => {
    expect(toApiUrl('https://example.com/file.png')).toBe('https://example.com/file.png')
    expect(toAssetUrl('https://example.com/file.png')).toBe('https://example.com/file.png')
  })

  it('normalizes relative asset paths', () => {
    expect(toAssetUrl('/api/v1/file?path=result.png')).toBe('/api/v1/file?path=result.png')
    expect(toAssetUrl('api/v1/file?path=result.png')).toBe('/api/v1/file?path=result.png')
  })

  it('returns null for missing asset values', () => {
    expect(toAssetUrl(null)).toBeNull()
    expect(toAssetUrl(undefined)).toBeNull()
  })
})
