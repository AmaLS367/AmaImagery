/* @vitest-environment jsdom */

import '@testing-library/jest-dom/vitest'

import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import App from '@src/App'
import { AuthProvider } from '@src/providers/AuthProvider'
import { JobProvider } from '@src/providers/JobProvider'
import { SettingsProvider } from '@src/providers/SettingsProvider'

type FetchInput = RequestInfo | URL

const canonicalRoutes = [
  ['/', /HomePage/i],
  ['/generate', /Main product shell with preserved IA and internal state variants\./i],
  ['/history', /Searchable history with filters, metadata, and explicit state handling\./i],
  ['/settings', /Serious control center with visual lab and live shell preview\./i],
  ['/login', /Sign in to your account/i],
  ['/register', /Create your account/i],
  ['/forgot-password', /Reset your password/i],
  ['/reset-password?token=smoke-token', /Create your new password/i],
  ['/about', /AmaImagery is a premium image-generation shell built around clarity\./i],
  ['/faq', /Production answers for the product, not placeholder support text\./i],
  ['/prompt-guide', /Write prompts that stay readable for both the model and the operator\./i],
  ['/privacy', /Privacy is framed around how the product actually works\./i],
  ['/404', /This route is not part of the screen system\./i],
  ['/modes', /Curated visual direction study for the AmaImagery shell\./i],
  ['/prototype', /Full clickthrough map and start states for the Figma file\./i],
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

      if (url.includes('/api/v1/auth/forgot-password')) {
        return new Response(null, { status: 204 })
      }

      if (url.includes('/api/v1/auth/reset-password')) {
        return jsonResponse({ ok: true })
      }

      if (url.includes('/api/v1/auth/login') || url.includes('/api/v1/auth/register')) {
        return jsonResponse({ access_token: 'test-token', user: { username: 'tester' } })
      }

      if (url.includes('/api/v1/auth/me')) {
        return jsonResponse({ id: 'user-1', email: 'tester@example.com', username: 'tester', settings: {} })
      }

      if (url.includes('/api/v1/auth/logout')) {
        return jsonResponse({ ok: true })
      }

      if (url.includes('/api/v1/auth/refresh')) {
        return new Response(null, { status: 401 })
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
  it.each(canonicalRoutes)('renders %s as a standalone route', async (route, heading) => {
    renderApp(route)
    expect(await screen.findByRole('heading', { name: heading, level: 1 })).toBeInTheDocument()
  })

  it('keeps landing and generate separated', async () => {
    renderApp('/')
    expect(await screen.findByRole('heading', { name: /HomePage/i, level: 1 })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /Main product shell with preserved IA and internal state variants\./i, level: 1 })).not.toBeInTheDocument()

    cleanup()

    renderApp('/generate')
    expect(await screen.findByRole('heading', { name: /Main product shell with preserved IA and internal state variants\./i, level: 1 })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /HomePage/i, level: 1 })).not.toBeInTheDocument()
  })

  it('redirects legacy routes to their canonical destinations', async () => {
    renderApp('/gen')
    await waitFor(() => expect(window.location.pathname).toBe('/generate'))
    expect(await screen.findByRole('heading', { name: /Main product shell with preserved IA and internal state variants\./i, level: 1 })).toBeInTheDocument()

    cleanup()

    renderApp('/guide')
    await waitFor(() => expect(window.location.pathname).toBe('/prompt-guide'))
    expect(await screen.findByRole('heading', { name: /Write prompts that stay readable for both the model and the operator\./i, level: 1 })).toBeInTheDocument()

    cleanup()

    renderApp('/reset?token=redirect-token')
    await waitFor(() => expect(window.location.pathname).toBe('/reset-password'))
    await waitFor(() => expect(window.location.search).toBe('?token=redirect-token'))
    expect(await screen.findByRole('heading', { name: /Create your new password/i, level: 1 })).toBeInTheDocument()
  })

  it('renders the catch-all 404 screen for unknown routes', async () => {
    renderApp('/totally-missing-route')
    expect(await screen.findByRole('heading', { name: /This route is not part of the screen system\./i, level: 1 })).toBeInTheDocument()
  })
})
