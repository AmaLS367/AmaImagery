import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'

import { AuthProvider, useAuth } from '@src/providers/AuthProvider'

import { makeUser, mockAnonymousAuth, mockAuthenticatedAuth, mockLoginFlow } from './helpers/auth'
import { emptyResponse, installFetchMock, jsonResponse, route } from './helpers/fetch'

function AuthHarness() {
  const auth = useAuth()

  return (
    <div>
      <div data-testid="status">{auth.status}</div>
      <div data-testid="user">{auth.user?.email ?? 'anonymous'}</div>
      <button onClick={() => void auth.login({ identifier: 'tester', password: 'password123' })}>login</button>
      <button onClick={() => void auth.register({ email: 'new@example.com', username: 'new-user', password: 'password123' })}>register</button>
      <button onClick={() => void auth.logout()}>logout</button>
      <button onClick={() => void auth.refreshIfNeeded()}>refresh</button>
      <button onClick={() => void auth.loadMe({ allowRefresh: false })}>load-no-refresh</button>
    </div>
  )
}

function renderAuthHarness() {
  return render(
    <AuthProvider>
      <AuthHarness />
    </AuthProvider>,
  )
}

describe('AuthProvider', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('bootstraps anonymous state when me fails and refresh fails', async () => {
    installFetchMock([...mockAnonymousAuth()])

    renderAuthHarness()

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('anonymous'))
    expect(screen.getByTestId('user')).toHaveTextContent('anonymous')
  })

  it('bootstraps authenticated state when me succeeds', async () => {
    installFetchMock([...mockAuthenticatedAuth(makeUser({ email: 'signed@example.com' }))])

    renderAuthHarness()

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('authenticated'))
    expect(screen.getByTestId('user')).toHaveTextContent('signed@example.com')
  })

  it('logs in and then loads auth/me', async () => {
    installFetchMock([...mockLoginFlow(makeUser({ email: 'login@example.com' }))])

    renderAuthHarness()

    fireEvent.click(screen.getByText('login'))

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('authenticated'))
    expect(screen.getByTestId('user')).toHaveTextContent('login@example.com')
  })

  it('registers and then loads auth/me', async () => {
    installFetchMock([...mockLoginFlow(makeUser({ email: 'register@example.com', username: 'registered' }))])

    renderAuthHarness()

    fireEvent.click(screen.getByText('register'))

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('authenticated'))
    expect(screen.getByTestId('user')).toHaveTextContent('register@example.com')
  })

  it('clears local auth state on logout even if the server call fails', async () => {
    installFetchMock([
      ...mockAuthenticatedAuth(makeUser({ email: 'logout@example.com' })),
      route('/api/v1/auth/logout', () => jsonResponse({ detail: 'failed' }, { status: 500 }), 'POST'),
    ])

    renderAuthHarness()

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('authenticated'))
    fireEvent.click(screen.getByText('logout'))

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('anonymous'))
  })

  it('delegates refreshIfNeeded to the refresh endpoint', async () => {
    const fetchMock = installFetchMock([
      ...mockAnonymousAuth(),
      route('/api/v1/auth/refresh', () => jsonResponse({ ok: true }), 'POST'),
    ])

    renderAuthHarness()

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('anonymous'))
    fireEvent.click(screen.getByText('refresh'))

    await waitFor(() => {
      expect(fetchMock.mock.calls.some(([input]) => String(input).includes('/api/v1/auth/refresh'))).toBe(true)
    })
  })

  it('does not try refresh when loadMe is called with allowRefresh false', async () => {
    const fetchMock = installFetchMock([
      route('/api/v1/auth/me', () => jsonResponse({ detail: 'unauthorized' }, { status: 401 })),
      route('/api/v1/auth/refresh', () => emptyResponse(204), 'POST'),
    ])

    renderAuthHarness()
    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('anonymous'))

    fetchMock.mockClear()
    fireEvent.click(screen.getByText('load-no-refresh'))

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('anonymous'))
    expect(fetchMock.mock.calls.some(([input]) => String(input).includes('/api/v1/auth/refresh'))).toBe(false)
  })
})
