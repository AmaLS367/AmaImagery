import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import Reset from '@src/pages/Reset'
import { SettingsProvider } from '@src/providers/SettingsProvider'

import { installFetchMock, emptyResponse, jsonResponse, route } from './helpers/fetch'

function renderReset(routeValue: string) {
  window.history.pushState({}, '', routeValue)
  return render(
    <MemoryRouter initialEntries={[routeValue]}>
      <SettingsProvider>
        <Routes>
          <Route path="/reset-password" element={<Reset />} />
          <Route path="/login" element={<div>login-target</div>} />
        </Routes>
      </SettingsProvider>
    </MemoryRouter>,
  )
}

describe('Reset page', () => {
  it('shows invalid state when token is missing', async () => {
    installFetchMock([])
    renderReset('/reset-password')

    fireEvent.click(screen.getByRole('button', { name: 'Update password' }))
    expect(await screen.findByText('Invalid or expired link')).toBeInTheDocument()
  })

  it('validates short and mismatched passwords', async () => {
    installFetchMock([])
    const { container } = renderReset('/reset-password?token=abc')

    fireEvent.change(container.querySelector('#password')!, { target: { value: 'short' } })
    fireEvent.change(container.querySelector('#password_confirm')!, { target: { value: 'short' } })
    fireEvent.click(screen.getByRole('button', { name: 'Update password' }))
    expect(await screen.findByText('Password must contain at least 8 characters.')).toBeInTheDocument()

    fireEvent.change(container.querySelector('#password')!, { target: { value: 'password123' } })
    fireEvent.change(container.querySelector('#password_confirm')!, { target: { value: 'password124' } })
    fireEvent.click(screen.getByRole('button', { name: 'Update password' }))
    expect(await screen.findByText('Passwords do not match.')).toBeInTheDocument()
  })

  it('shows invalid state for expired tokens', async () => {
    installFetchMock([
      route('/api/v1/auth/reset-password', () => jsonResponse({ detail: 'invalid or expired token' }, { status: 400 }), 'POST'),
    ])
    const { container } = renderReset('/reset-password?token=expired')

    fireEvent.change(container.querySelector('#password')!, { target: { value: 'password123' } })
    fireEvent.change(container.querySelector('#password_confirm')!, { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: 'Update password' }))

    expect(await screen.findByText('Invalid or expired link')).toBeInTheDocument()
  })

  it('shows success after a valid reset request', async () => {
    installFetchMock([
      route('/api/v1/auth/reset-password', () => emptyResponse(200), 'POST'),
    ])
    const { container } = renderReset('/reset-password?token=valid')

    fireEvent.change(container.querySelector('#password')!, { target: { value: 'password123' } })
    fireEvent.change(container.querySelector('#password_confirm')!, { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: 'Update password' }))

    expect(await screen.findByText('Success! Your password is now updated.')).toBeInTheDocument()
  })
})
