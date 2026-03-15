import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '@src/lib/api'

describe('api transport contract', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.unstubAllGlobals()
  })

  it('uses cookie-based requests without synthesizing Authorization from local storage', async () => {
    localStorage.setItem('access_token', 'legacy-token')
    localStorage.setItem('auth', JSON.stringify({ access_token: 'legacy-auth-token' }))

    const fetchMock = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    })
    vi.stubGlobal('fetch', fetchMock)

    await api('/probe', {
      method: 'POST',
      body: JSON.stringify({ ok: true }),
    }, { retryOn401: false })

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [, init] = fetchMock.mock.calls[0]!
    const headers = new Headers(init?.headers)

    expect(init?.credentials).toBe('include')
    expect(headers.has('Authorization')).toBe(false)
    expect(headers.get('Content-Type')).toBe('application/json')
  })
})
