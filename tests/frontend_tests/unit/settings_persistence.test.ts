import { describe, expect, it } from 'vitest'

import { applySettingsToDOM, hexToHslString, loadSettings, saveSettings } from '@src/lib/settings'

describe('settings persistence and dom sync', () => {
  it('loads defaults when local storage is empty', () => {
    const settings = loadSettings()
    expect(settings.visualMode).toBe('dashboard')
    expect(settings.queue.maxParallel).toBe(1)
    expect(settings.theme).toBe('dark')
  })

  it('merges partial persisted settings with defaults', () => {
    localStorage.setItem('amaimagery.settings.v3', JSON.stringify({
      theme: 'light',
      queue: { maxParallel: 3 },
      visualMode: 'cinematic',
    }))

    const settings = loadSettings()
    expect(settings.theme).toBe('light')
    expect(settings.visualMode).toBe('cinematic')
    expect(settings.queue.maxParallel).toBe(3)
    expect(settings.queue.cancelPrevious).toBe(true)
  })

  it('falls back to defaults on malformed persisted settings', () => {
    localStorage.setItem('amaimagery.settings.v3', '{broken')
    localStorage.setItem('theme', 'light')

    const settings = loadSettings()
    expect(settings.theme).toBe('light')
    expect(settings.visualMode).toBe('dashboard')
  })

  it('saves settings under the expected key', () => {
    const settings = loadSettings()
    saveSettings({ ...settings, visualMode: 'editorial' })

    expect(JSON.parse(localStorage.getItem('amaimagery.settings.v3') || '{}').visualMode).toBe('editorial')
  })

  it('applies all expected dom attributes', () => {
    const settings = {
      ...loadSettings(),
      theme: 'light' as const,
      motion: 2 as const,
      visualMode: 'cinematic' as const,
      shellPreset: 'editorial' as const,
      componentStyle: 'clean-soft' as const,
      density: 'compact' as const,
      glass: false,
      accentHex: '#F97316',
    }

    applySettingsToDOM(settings)

    expect(document.documentElement.classList.contains('dark')).toBe(false)
    expect(document.documentElement.classList.contains('expressive-motion')).toBe(true)
    expect(document.documentElement.dataset.visualMode).toBe('cinematic')
    expect(document.documentElement.dataset.shellPreset).toBe('editorial')
    expect(document.documentElement.dataset.componentStyle).toBe('clean-soft')
    expect(document.documentElement.dataset.density).toBe('compact')
    expect(document.documentElement.dataset.glass).toBe('off')
    expect(document.documentElement.dataset.motion).toBe('2')
  })

  it('converts valid hex colors to hsl strings and rejects invalid ones', () => {
    expect(hexToHslString('#06B6D4')).toMatch(/^\d+ \d+% \d+%$/)
    expect(hexToHslString('not-a-color')).toBeNull()
  })
})
