import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router'
import { describe, expect, it } from 'vitest'

import Login from '@src/pages/Login'
import { AuthProvider } from '@src/providers/AuthProvider'
import { SettingsProvider } from '@src/providers/SettingsProvider'

import { mockAnonymousAuth, mockLoginFlow } from './helpers/auth'
import { installFetchMock, emptyResponse, jsonResponse, route } from './helpers/fetch'

function renderLogin(initialMode: 'login' | 'forgot' = 'login') {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <SettingsProvider>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login initialMode={initialMode} />} />
            <Route path="/generate" element={<div>generate-target</div>} />
          </Routes>
        </AuthProvider>
      </SettingsProvider>
    </MemoryRouter>,
  )
}

describe('Login page', () => {
  it('shows validation errors for invalid sign in data', async () => {
    installFetchMock([...mockAnonymousAuth()])
    renderLogin()

    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByText('Email or username is required.')).toBeInTheDocument()
    expect(screen.getByText('Password must contain at least 8 characters.')).toBeInTheDocument()
  })

  it('redirects to generate on successful login', async () => {
    installFetchMock([...mockLoginFlow()])
    const { container } = renderLogin()

    fireEvent.change(container.querySelector('#identifier')!, { target: { value: 'tester@example.com' } })
    fireEvent.change(container.querySelector('#password')!, { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByText('generate-target')).toBeInTheDocument()
  })

  it('submits forgot mode requests and shows success', async () => {
    installFetchMock([
      ...mockAnonymousAuth(),
      route('/api/v1/auth/forgot-password', () => emptyResponse(204), 'POST'),
    ])
    const { container } = renderLogin('forgot')

    fireEvent.change(container.querySelector('#identifier')!, { target: { value: 'tester@example.com' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send reset link' }))

    expect(await screen.findByText('If that account exists, a reset link has been sent.')).toBeInTheDocument()
  })

  it('renders server errors from login failures', async () => {
    installFetchMock([
      ...mockAnonymousAuth(),
      route('/api/v1/auth/login', () => jsonResponse({ detail: 'Invalid credentials' }, { status: 401 }), 'POST'),
    ])
    const { container } = renderLogin()

    fireEvent.change(container.querySelector('#identifier')!, { target: { value: 'tester@example.com' } })
    fireEvent.change(container.querySelector('#password')!, { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByText('Invalid credentials')).toBeInTheDocument()
  })
})
