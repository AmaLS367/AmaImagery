import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { SettingsProvider, useSettings } from '@src/providers/SettingsProvider'

function SettingsHarness() {
  const { settings, update } = useSettings()

  return (
    <div>
      <div data-testid="theme">{settings.theme}</div>
      <div data-testid="mode">{settings.visualMode}</div>
      <button onClick={() => update('theme', settings.theme === 'dark' ? 'light' : 'dark')}>toggle-theme</button>
      <button onClick={() => update('visualMode', 'cinematic')}>cinematic</button>
    </div>
  )
}

describe('SettingsProvider', () => {
  it('loads settings from local storage', async () => {
    localStorage.setItem('amaimagery.settings.v3', JSON.stringify({
      theme: 'light',
      visualMode: 'editorial',
      queue: { maxParallel: 2, cancelPrevious: false },
    }))

    render(
      <SettingsProvider>
        <SettingsHarness />
      </SettingsProvider>,
    )

    expect(screen.getByTestId('theme')).toHaveTextContent('light')
    expect(screen.getByTestId('mode')).toHaveTextContent('editorial')
  })

  it('persists updates and applies dom attributes', async () => {
    render(
      <SettingsProvider>
        <SettingsHarness />
      </SettingsProvider>,
    )

    fireEvent.click(screen.getByText('toggle-theme'))
    fireEvent.click(screen.getByText('cinematic'))

    await waitFor(() => expect(screen.getByTestId('theme')).toHaveTextContent('light'))
    expect(JSON.parse(localStorage.getItem('amaimagery.settings.v3') || '{}').visualMode).toBe('cinematic')
    expect(document.documentElement.dataset.visualMode).toBe('cinematic')
  })

  it('does not perform network requests', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    render(
      <SettingsProvider>
        <SettingsHarness />
      </SettingsProvider>,
    )

    fireEvent.click(screen.getByText('toggle-theme'))

    await waitFor(() => expect(screen.getByTestId('theme')).toHaveTextContent('light'))
    expect(fetchMock).not.toHaveBeenCalled()
  })
})
