import { beforeEach, describe, expect, it } from 'vitest'
import * as settings from '@src/lib/settings'

describe('settings.ts', () => {
  beforeEach(() => {
    document.documentElement.className = ''
    document.documentElement.removeAttribute('data-visual-mode')
    document.documentElement.removeAttribute('data-shell-preset')
    document.documentElement.removeAttribute('data-component-style')
    document.documentElement.removeAttribute('data-density')
    document.documentElement.removeAttribute('data-glass')
    document.documentElement.removeAttribute('data-motion')
  })

  it('loads and exports something', () => {
    expect(settings).toBeTruthy()
  })

  it('applies runtime settings to the DOM', () => {
    settings.applySettingsToDOM({
      ...settings.loadSettings(),
      theme: 'light',
      accentHex: '#F97316',
      motion: 2,
      glass: false,
      density: 'compact',
      visualMode: 'cinematic',
      shellPreset: 'editorial',
      componentStyle: 'clean-soft',
    })

    expect(document.documentElement.dataset.visualMode).toBe('cinematic')
    expect(document.documentElement.dataset.shellPreset).toBe('editorial')
    expect(document.documentElement.dataset.componentStyle).toBe('clean-soft')
    expect(document.documentElement.dataset.density).toBe('compact')
    expect(document.documentElement.dataset.glass).toBe('off')
    expect(document.documentElement.dataset.motion).toBe('2')
    expect(document.documentElement.style.getPropertyValue('--primary')).not.toBe('')
    expect(document.documentElement.classList.contains('expressive-motion')).toBe(true)
  })
})
