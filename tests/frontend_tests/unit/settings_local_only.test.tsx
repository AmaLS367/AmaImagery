import '@testing-library/jest-dom/vitest'
import '@src/i18n/i18n'

import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router'

import Settings from '@src/pages/Settings'
import { AuthProvider } from '@src/providers/AuthProvider'
import { SettingsProvider } from '@src/providers/SettingsProvider'

type FetchInput = RequestInfo | URL

function jsonResponse(data: unknown, init?: ResponseInit) {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
}

function getUrl(input: FetchInput) {
  if (typeof input === 'string') return input
  if (input instanceof URL) return input.toString()
  return input.url
}

describe('Settings backend sync', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.className = ''
  })

  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
  })

  it('stays local and does not request backend settings endpoints', async () => {
    const fetchMock = vi.fn(async (input: FetchInput) => {
      const url = getUrl(input)
      if (url.includes('/api/v1/auth/me') || url.includes('/api/v1/auth/refresh')) {
        return jsonResponse({ detail: 'unauthorized' }, { status: 401 })
      }
      return jsonResponse({})
    })

    vi.stubGlobal('fetch', fetchMock)

    render(
      <MemoryRouter>
        <SettingsProvider>
          <AuthProvider>
            <Settings />
          </AuthProvider>
        </SettingsProvider>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('Appearance')).toBeInTheDocument()
    })

    const requestedUrls = fetchMock.mock.calls.map(([input]) => getUrl(input))
    expect(requestedUrls.some((url) => url.includes('/api/v1/users/me/settings'))).toBe(false)
  })
})
