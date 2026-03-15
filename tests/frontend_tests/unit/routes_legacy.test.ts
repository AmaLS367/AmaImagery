import { describe, expect, it } from 'vitest'

import { appRoutes, legacyTabRoutes, resolveLegacyTabRoute } from '@src/lib/routes'

describe('legacy route resolution', () => {
  it('resolves every known legacy tab to a canonical route', () => {
    Object.entries(legacyTabRoutes).forEach(([tab, route]) => {
      expect(resolveLegacyTabRoute(tab)).toBe(route)
    })
  })

  it('returns null for unknown or missing tabs', () => {
    expect(resolveLegacyTabRoute(null)).toBeNull()
    expect(resolveLegacyTabRoute(undefined)).toBeNull()
    expect(resolveLegacyTabRoute('unknown-tab')).toBeNull()
  })

  it('keeps canonical routes stable', () => {
    expect(appRoutes.generate).toBe('/generate')
    expect(appRoutes.history).toBe('/history')
    expect(appRoutes.settings).toBe('/settings')
    expect(appRoutes.resetPassword).toBe('/reset-password')
  })
})
