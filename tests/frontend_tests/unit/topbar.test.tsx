import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it, vi } from 'vitest'

import { Topbar } from '@src/components/Topbar'
import { AuthProvider } from '@src/providers/AuthProvider'
import { SettingsProvider } from '@src/providers/SettingsProvider'

import { mockAnonymousAuth, mockAuthenticatedAuth } from './helpers/auth'
import { installFetchMock } from './helpers/fetch'
import { seedSettings } from './helpers/settings'

function renderTopbar() {
  const toggleTheme = vi.fn()
  const view = render(
    <MemoryRouter>
      <SettingsProvider>
        <AuthProvider>
          <Topbar theme="dark" toggleTheme={toggleTheme} />
        </AuthProvider>
      </SettingsProvider>
    </MemoryRouter>,
  )
  return { toggleTheme, ...view }
}

describe('Topbar', () => {
  it('shows auth actions for anonymous users', async () => {
    seedSettings()
    installFetchMock([...mockAnonymousAuth()])

    renderTopbar()

    expect(await screen.findByRole('button', { name: 'Log in' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sign up' })).toBeInTheDocument()
  })

  it('shows logout for authenticated users and handles logout flow', async () => {
    seedSettings({ visualMode: 'cinematic' })
    installFetchMock([...mockAuthenticatedAuth()])

    renderTopbar()

    const logout = await screen.findByRole('button', { name: 'Log out' })
    fireEvent.click(logout)

    await waitFor(() => expect(screen.getByRole('button', { name: 'Log in' })).toBeInTheDocument())
  })

  it('invokes theme toggle from the shell action', async () => {
    seedSettings()
    installFetchMock([...mockAnonymousAuth()])

    const { toggleTheme, container } = renderTopbar()
    const themeButton = (container.querySelector('.lucide-sun') as SVGElement | null)?.closest('button')
    fireEvent.click(themeButton!)

    expect(toggleTheme).toHaveBeenCalled()
  })
})
