import '@testing-library/jest-dom/vitest'
import '@src/i18n/i18n'

import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router'

import History from '@src/pages/History'
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

function renderHistory() {
  return render(
    <MemoryRouter>
      <SettingsProvider>
        <AuthProvider>
          <History />
        </AuthProvider>
      </SettingsProvider>
    </MemoryRouter>,
  )
}

describe('History data sources', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.className = ''
  })

  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
  })

  it('uses backend history for authenticated users', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: FetchInput) => {
        const url = getUrl(input)

        if (url.includes('/api/v1/auth/me')) {
          return jsonResponse({
            id: 'user-1',
            email: 'tester@example.com',
            username: 'tester',
            settings: {},
          })
        }

        if (url.includes('/api/v1/users/me/generations')) {
          return jsonResponse({
            total: 1,
            items: [
              {
                id: 'gen-1',
                task_id: 'gen-1',
                status: 'completed',
                provider_name: 'backend-provider',
                image_path: 'result.png',
                image_filename: 'result.png',
                prompt: { prompt: 'Backend history prompt' },
                params: { width: 1024, height: 1024, guidance_scale: 7.5, steps: 28 },
                created_at: '2025-01-01T00:00:00Z',
              },
            ],
          })
        }

        if (url.includes('/api/v1/auth/refresh')) {
          return jsonResponse({ detail: 'unauthorized' }, { status: 401 })
        }

        return jsonResponse({})
      }),
    )

    renderHistory()

    expect(await screen.findAllByText('Backend history prompt')).toHaveLength(2)
    expect(screen.queryByText('Local prompt')).not.toBeInTheDocument()
  })

  it('uses local history fallback for anonymous users', async () => {
    localStorage.setItem('amaimagery.history.v2', JSON.stringify([
      {
        prompt: 'Local prompt',
        neg: '',
        steps: 28,
        guidance: 7.5,
        width: 896,
        height: 1024,
        seed: null,
        ipScale: 0.6,
        path: 'local.png',
        ts: 1735689600000,
      },
    ]))

    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: FetchInput) => {
        const url = getUrl(input)

        if (url.includes('/api/v1/auth/me') || url.includes('/api/v1/auth/refresh')) {
          return jsonResponse({ detail: 'unauthorized' }, { status: 401 })
        }

        if (url.includes('/api/v1/users/me/generations')) {
          return jsonResponse({
            total: 0,
            items: [],
          })
        }

        return jsonResponse({})
      }),
    )

    renderHistory()

    expect(await screen.findAllByText('Local prompt')).toHaveLength(2)
  })
})
