import type { MeResponse } from '@src/lib/api'

import { emptyResponse, jsonResponse, route, type FetchRoute } from './fetch'

export function makeUser(overrides: Partial<MeResponse> = {}): MeResponse {
  return {
    id: 'user-1',
    email: 'tester@example.com',
    username: 'tester',
    settings: {},
    ...overrides,
  }
}

export function mockAnonymousAuth(): FetchRoute[] {
  return [
    route('/api/v1/auth/me', () => jsonResponse({ detail: 'unauthorized' }, { status: 401 })),
    route('/api/v1/auth/refresh', () => jsonResponse({ detail: 'unauthorized' }, { status: 401 }), 'POST'),
    route('/api/v1/auth/logout', () => emptyResponse(204), 'POST'),
  ]
}

export function mockAuthenticatedAuth(user: MeResponse = makeUser()): FetchRoute[] {
  return [
    route('/api/v1/auth/me', () => jsonResponse(user)),
    route('/api/v1/auth/refresh', () => jsonResponse({ ok: true }), 'POST'),
    route('/api/v1/auth/logout', () => emptyResponse(204), 'POST'),
  ]
}

export function mockLoginFlow(user: MeResponse = makeUser()): FetchRoute[] {
  return [
    route('/api/v1/auth/login', () =>
      jsonResponse({
        ...user,
        access_token: 'cookie-backed',
        token_type: 'bearer',
        expires_in: 900,
      }), 'POST'),
    route('/api/v1/auth/register', () =>
      jsonResponse({
        ...user,
        access_token: 'cookie-backed',
        token_type: 'bearer',
        expires_in: 900,
      }), 'POST'),
    ...mockAuthenticatedAuth(user),
  ]
}
