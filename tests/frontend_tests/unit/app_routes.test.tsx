import '@testing-library/jest-dom/vitest'

import { cleanup, render, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import App from '@src/App'
import { AuthProvider } from '@src/providers/AuthProvider'
import { JobProvider } from '@src/providers/JobProvider'
import { SettingsProvider } from '@src/providers/SettingsProvider'

type FetchInput = RequestInfo | URL

const canonicalRoutes = [
  ['/', 'landing'],
  ['/generate', 'generate'],
  ['/history', 'history'],
  ['/settings', 'settings'],
  ['/login', 'login'],
  ['/register', 'register'],
  ['/forgot-password', 'forgot-password'],
  ['/reset-password?token=smoke-token', 'reset-password'],
  ['/about', 'about'],
  ['/faq', 'faq'],
  ['/prompt-guide', 'prompt-guide'],
  ['/privacy', 'privacy'],
  ['/404', 'not-found'],
] as const

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

function renderApp(route: string) {
  window.history.pushState({}, '', route)
  return render(
    <SettingsProvider>
      <AuthProvider>
        <JobProvider>
          <App />
        </JobProvider>
      </AuthProvider>
    </SettingsProvider>,
  )
}

async function expectPage(pageId: string) {
  await waitFor(() => {
    expect(document.querySelector(`[data-page-id="${pageId}"]`)).toBeInTheDocument()
  })
}

beforeEach(() => {
  localStorage.clear()
  document.documentElement.className = ''
  document.documentElement.removeAttribute('data-visual-mode')

  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  })

  Object.defineProperty(window, 'scrollTo', {
    writable: true,
    value: vi.fn(),
  })

  Object.defineProperty(window, 'Notification', {
    writable: true,
    value: class NotificationMock {
      static permission = 'granted'
      static requestPermission = vi.fn(async () => 'granted')
      constructor(_: string, __?: NotificationOptions) {}
    },
  })

  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: FetchInput, init?: RequestInit) => {
      const url = getUrl(input)
      const method = init?.method ?? 'GET'

      if (url.includes('/api/v1/users/me/generations')) {
        return jsonResponse({ items: [] })
      }

      if (url.includes('/api/v1/users/me/settings')) {
        if (method === 'PATCH') return jsonResponse({ ok: true })
        return jsonResponse({ data: {} })
      }

      if (url.includes('/api/v1/auth/me') || url.includes('/api/v1/auth/refresh')) {
        return jsonResponse({ detail: 'unauthorized' }, { status: 401 })
      }

      if (url.includes('/api/v1/auth/forgot-password')) {
        return new Response(null, { status: 204 })
      }

      if (url.includes('/api/v1/auth/reset-password')) {
        return new Response(null, { status: 200 })
      }

      if (url.includes('/api/v1/auth/login') || url.includes('/api/v1/auth/register')) {
        return jsonResponse({
          id: 'user-1',
          email: 'tester@example.com',
          username: 'tester',
          access_token: 'test-token',
          token_type: 'bearer',
          expires_in: 900,
        })
      }

      if (url.includes('/api/v1/auth/logout')) {
        return new Response(null, { status: 204 })
      }

      if (url.includes('/api/v1/images/generate')) {
        return jsonResponse({ task_id: 'task-1', status: 'queued' })
      }

      if (url.includes('/api/v1/images/status/')) {
        return jsonResponse({
          task_id: 'task-1',
          status: 'completed',
          image_filename: 'result.png',
          exp: 1,
          sig: 'signature',
        })
      }

      if (url.includes('/api/v1/file')) {
        return new Response('image', { status: 200 })
      }

      return jsonResponse({})
    }),
  )
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('app route smoke tests', () => {
  it.each(canonicalRoutes)('renders %s as a standalone route', async (route, pageId) => {
    renderApp(route)
    await expectPage(pageId)
  })

  it('keeps landing and generate separated', async () => {
    renderApp('/')
    await expectPage('landing')
    expect(document.querySelector('[data-page-id="generate"]')).not.toBeInTheDocument()

    cleanup()

    renderApp('/generate')
    await expectPage('generate')
    expect(document.querySelector('[data-page-id="landing"]')).not.toBeInTheDocument()
  })

  it('redirects legacy routes to their canonical destinations', async () => {
    renderApp('/gen')
    await waitFor(() => expect(window.location.pathname).toBe('/generate'))
    await expectPage('generate')

    cleanup()

    renderApp('/guide')
    await waitFor(() => expect(window.location.pathname).toBe('/prompt-guide'))
    await expectPage('prompt-guide')

    cleanup()

    renderApp('/reset?token=redirect-token')
    await waitFor(() => expect(window.location.pathname).toBe('/reset-password'))
    await waitFor(() => expect(window.location.search).toBe('?token=redirect-token'))
    await expectPage('reset-password')
  })

  it('renders the catch-all 404 screen for unknown routes', async () => {
    renderApp('/totally-missing-route')
    await expectPage('not-found')
  })
})
