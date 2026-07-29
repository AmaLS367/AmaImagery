import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'

import ForgotPassword from '@src/pages/ForgotPassword'
import { SettingsProvider } from '@src/providers/SettingsProvider'

import { installFetchMock, emptyResponse, jsonResponse, route } from './helpers/fetch'

function renderForgotPassword() {
  return render(
    <MemoryRouter>
      <SettingsProvider>
        <ForgotPassword />
      </SettingsProvider>
    </MemoryRouter>,
  )
}

describe('ForgotPassword page', () => {
  it('rejects blank identifiers', async () => {
    installFetchMock([])
    renderForgotPassword()

    fireEvent.click(screen.getByRole('button', { name: 'Send reset link' }))
    expect(await screen.findByText('Email or username is required.')).toBeInTheDocument()
  })

  it('shows success state after a reset request', async () => {
    installFetchMock([
      route('/api/v1/auth/forgot-password', () => emptyResponse(204), 'POST'),
    ])
    const { container } = renderForgotPassword()

    fireEvent.change(container.querySelector('input[type="text"]')!, { target: { value: 'tester@example.com' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send reset link' }))

    expect(await screen.findByText('If that account exists, the reset link has been sent.')).toBeInTheDocument()
  })

  it('shows server failures', async () => {
    installFetchMock([
      route('/api/v1/auth/forgot-password', () => jsonResponse({ detail: 'Email service unavailable' }, { status: 503 }), 'POST'),
    ])
    const { container } = renderForgotPassword()

    fireEvent.change(container.querySelector('input[type="text"]')!, { target: { value: 'tester@example.com' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send reset link' }))

    expect(await screen.findByText('Email service unavailable')).toBeInTheDocument()
  })
})
