import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '@src/lib/api'

describe('api refresh handling', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('retries the original request after a successful refresh', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url

      if (url.includes('/api/v1/auth/refresh')) {
        return new Response(JSON.stringify({ ok: true }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }

      const attempt = fetchMock.mock.calls.filter(([value]) => {
        const current = typeof value === 'string' ? value : value instanceof URL ? value.toString() : value.url
        return current.includes('/probe')
      }).length

      if (attempt === 1) {
        return new Response(JSON.stringify({ detail: 'unauthorized' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        })
      }

      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    })

    vi.stubGlobal('fetch', fetchMock)

    const response = await api('/probe')

    expect(response.status).toBe(200)
    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it('returns the original unauthorized response when refresh fails', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url
      if (url.includes('/api/v1/auth/refresh')) {
        return new Response(JSON.stringify({ detail: 'refresh failed' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        })
      }

      return new Response(JSON.stringify({ detail: 'unauthorized' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      })
    })

    vi.stubGlobal('fetch', fetchMock)

    const response = await api('/probe')

    expect(response.status).toBe(401)
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })
})
