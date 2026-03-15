import { fireEvent, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import SettingsPage from '@src/pages/Settings'

import { mockAnonymousAuth } from './helpers/auth'
import { installFetchMock } from './helpers/fetch'
import { renderWithProviders } from './helpers/render'
import { seedSettings } from './helpers/settings'

describe('Settings page local controls', () => {
  it.each(['dashboard', 'editorial', 'cinematic'] as const)('renders all local settings sections in %s mode', async (visualMode) => {
    seedSettings({ visualMode })
    installFetchMock([...mockAnonymousAuth()])

    renderWithProviders(<SettingsPage />)

    expect(await screen.findByText('Appearance')).toBeInTheDocument()
    expect(screen.getByText('Mode orchestration')).toBeInTheDocument()
    expect(screen.getByText('Queue and archive')).toBeInTheDocument()
    expect(screen.getByText('Notifications')).toBeInTheDocument()
    expect(screen.getByText('Safety and prompt defaults')).toBeInTheDocument()
  })

  it('updates visual mode, queue behavior, and banlist locally without hitting server settings endpoints', async () => {
    seedSettings()
    const fetchMock = installFetchMock([...mockAnonymousAuth()])

    renderWithProviders(<SettingsPage />)

    fireEvent.click(await screen.findByText('Cinematic'))
    fireEvent.click(screen.getByText('3 parallel'))
    fireEvent.change(screen.getByPlaceholderText('Keywords to exclude from generation (negatives).'), {
      target: { value: 'nsfw, gore, blood' },
    })

    await waitFor(() => {
      const saved = JSON.parse(localStorage.getItem('amaimagery.settings.v3') || '{}')
      expect(saved.visualMode).toBe('cinematic')
      expect(saved.queue.maxParallel).toBe(3)
      expect(saved.banlist).toBe('nsfw, gore, blood')
    })

    expect(fetchMock.mock.calls.some(([input]) => String(input).includes('/api/v1/users/me/settings'))).toBe(false)
  })

  it('accepts manual valid accent hex values', async () => {
    seedSettings()
    installFetchMock([...mockAnonymousAuth()])

    renderWithProviders(<SettingsPage />)
    const input = await screen.findByDisplayValue('#06B6D4')

    fireEvent.change(input, { target: { value: '#EF4444' } })

    await waitFor(() => {
      const saved = JSON.parse(localStorage.getItem('amaimagery.settings.v3') || '{}')
      expect(saved.accentHex).toBe('#EF4444')
    })
  })
})
