import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import Register from '@src/pages/Register'
import { AuthProvider } from '@src/providers/AuthProvider'
import { SettingsProvider } from '@src/providers/SettingsProvider'

import { mockAnonymousAuth, mockLoginFlow } from './helpers/auth'
import { installFetchMock, jsonResponse, route } from './helpers/fetch'

function renderRegister() {
  return render(
    <MemoryRouter initialEntries={['/register']}>
      <SettingsProvider>
        <AuthProvider>
          <Routes>
            <Route path="/register" element={<Register />} />
            <Route path="/generate" element={<div>generate-target</div>} />
          </Routes>
        </AuthProvider>
      </SettingsProvider>
    </MemoryRouter>,
  )
}

describe('Register page', () => {
  it('validates required registration fields', async () => {
    installFetchMock([...mockAnonymousAuth()])
    renderRegister()

    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))

    expect(await screen.findByText('Email is required.')).toBeInTheDocument()
    expect(screen.getByText('Username is required.')).toBeInTheDocument()
  })

  it('redirects to generate on successful registration', async () => {
    installFetchMock([...mockLoginFlow()])
    const { container } = renderRegister()

    fireEvent.change(container.querySelector('#username')!, { target: { value: 'tester' } })
    fireEvent.change(container.querySelector('#email')!, { target: { value: 'tester@example.com' } })
    fireEvent.change(container.querySelector('#password')!, { target: { value: 'password123' } })
    fireEvent.change(container.querySelector('#confirm')!, { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))

    expect(await screen.findByText('generate-target')).toBeInTheDocument()
  })

  it('shows duplicate account errors from the server', async () => {
    installFetchMock([
      ...mockAnonymousAuth(),
      route('/api/v1/auth/register', () => jsonResponse({ detail: 'Username already exists' }, { status: 409 }), 'POST'),
    ])
    const { container } = renderRegister()

    fireEvent.change(container.querySelector('#username')!, { target: { value: 'tester' } })
    fireEvent.change(container.querySelector('#email')!, { target: { value: 'tester@example.com' } })
    fireEvent.change(container.querySelector('#password')!, { target: { value: 'password123' } })
    fireEvent.change(container.querySelector('#confirm')!, { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))

    expect(await screen.findByText('Username already exists')).toBeInTheDocument()
  })
})
