import { vi } from 'vitest'

export type FetchInput = RequestInfo | URL
export type FetchRoute = {
  match: (url: string, init?: RequestInit) => boolean
  response: (url: string, init?: RequestInit) => Response | Promise<Response>
}

export function getUrl(input: FetchInput) {
  if (typeof input === 'string') return input
  if (input instanceof URL) return input.toString()
  return input.url
}

export function jsonResponse(data: unknown, init?: ResponseInit) {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
}

export function textResponse(body: string, init?: ResponseInit) {
  return new Response(body, {
    status: 200,
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    ...init,
  })
}

export function emptyResponse(status = 204, init?: ResponseInit) {
  return new Response(null, {
    status,
    ...init,
  })
}

export function route(pathname: string, response: FetchRoute['response'], method?: string): FetchRoute {
  return {
    match: (url, init) => {
      const currentMethod = (init?.method ?? 'GET').toUpperCase()
      const expectedMethod = (method ?? currentMethod).toUpperCase()
      return url.includes(pathname) && currentMethod === expectedMethod
    },
    response,
  }
}

export function installFetchMock(routes: FetchRoute[], fallback?: FetchRoute['response']) {
  const mock = vi.fn(async (input: FetchInput, init?: RequestInit) => {
    const url = getUrl(input)
    const matched = routes.find((item) => item.match(url, init))
    if (matched) {
      return matched.response(url, init)
    }

    if (fallback) {
      return fallback(url, init)
    }

    return jsonResponse({ detail: `Unhandled request for ${url}` }, { status: 404 })
  })

  vi.stubGlobal('fetch', mock)
  return mock
}
