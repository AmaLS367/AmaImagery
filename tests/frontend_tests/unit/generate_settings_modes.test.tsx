import '@testing-library/jest-dom/vitest'
import '@src/i18n/i18n'

import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router'

import Generate from '@src/pages/Generate'
import Settings from '@src/pages/Settings'
import { AuthProvider } from '@src/providers/AuthProvider'
import { JobProvider } from '@src/providers/JobProvider'
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

function seedMode(mode: 'dashboard' | 'editorial' | 'cinematic') {
  localStorage.setItem('amaimagery.settings.v3', JSON.stringify({ visualMode: mode }))
}

function renderGenerate(mode: 'dashboard' | 'editorial' | 'cinematic') {
  seedMode(mode)
  return render(
    <MemoryRouter>
      <SettingsProvider>
        <JobProvider>
          <Generate />
        </JobProvider>
      </SettingsProvider>
    </MemoryRouter>,
  )
}

function renderSettings(mode: 'dashboard' | 'editorial' | 'cinematic') {
  seedMode(mode)
  return render(
    <MemoryRouter>
      <SettingsProvider>
        <AuthProvider>
          <Settings />
        </AuthProvider>
      </SettingsProvider>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  localStorage.clear()
  document.documentElement.className = ''
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: FetchInput, init?: RequestInit) => {
      const url = getUrl(input)
      const method = init?.method ?? 'GET'

      if (url.includes('/api/v1/users/me/settings')) {
        if (method === 'PATCH') return jsonResponse({ ok: true })
        return jsonResponse({ data: {} })
      }

      if (url.includes('/api/v1/auth/me') || url.includes('/api/v1/auth/refresh')) {
        return jsonResponse({ detail: 'unauthorized' }, { status: 401 })
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

      return jsonResponse({})
    }),
  )
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('Generate page visual modes', () => {
  it.each(['dashboard', 'editorial', 'cinematic'] as const)('keeps the full generation inventory in %s mode', async (mode) => {
    renderGenerate(mode)

    expect(await screen.findByText('Prompt')).toBeInTheDocument()
    expect(screen.getByText('Negative prompt')).toBeInTheDocument()
    expect(screen.getByText('Dimensions')).toBeInTheDocument()
    expect(screen.getByText('Advanced controls')).toBeInTheDocument()
    expect(screen.getByText('Reference upload')).toBeInTheDocument()
    expect(screen.getByText('Result')).toBeInTheDocument()
    expect(screen.getByText('Run controls')).toBeInTheDocument()
  })
})

describe('Settings page visual modes', () => {
  it.each(['dashboard', 'editorial', 'cinematic'] as const)('keeps the full local settings inventory in %s mode', async (mode) => {
    renderSettings(mode)

    await waitFor(() => {
      expect(screen.getByText('Appearance')).toBeInTheDocument()
    })
    expect(screen.getByText('Mode orchestration')).toBeInTheDocument()
    expect(screen.getByText('Queue and archive')).toBeInTheDocument()
    expect(screen.getByText('Notifications')).toBeInTheDocument()
    expect(screen.getByText('Safety and prompt defaults')).toBeInTheDocument()
  })
})
