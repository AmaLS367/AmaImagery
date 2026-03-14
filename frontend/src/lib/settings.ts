export type Motion = 0 | 1 | 2
export type ThemeMode = 'light' | 'dark'
export type DensityMode = 'comfortable' | 'compact'
export type VisualMode = 'dashboard' | 'editorial' | 'cinematic'
export type ShellPreset = 'creator-luxury' | 'editorial'
export type ComponentStyle = 'glass' | 'clean-soft'

export type Preset = {
  id: string
  name: string
  steps: number
  guidance: number
  width: number
  height: number
  seed: number | null
  ipScale: number
  neg: string
}

export type HeaderKV = { key: string; value: string }

export type Settings = {
  theme: ThemeMode
  accentHex: string
  motion: Motion
  glass: boolean
  density: DensityMode
  visualMode: VisualMode
  shellPreset: ShellPreset
  componentStyle: ComponentStyle

  presets: Preset[]
  defaultPresetId: string | null

  queue: { maxParallel: 1 | 2 | 3; cancelPrevious: boolean }

  historyLimit: 50 | 100 | 500

  headers: HeaderKV[]

  notifyOnDone: boolean
  soundOnDone: boolean

  nsfwHide: boolean

  banlist: string // строки через запятую/перенос
}

const KEY = 'amaimagery.settings.v3'

const DEFAULT_PRESETS: Preset[] = [
  { id: 'portrait', name: 'Portrait 896×1152', steps: 28, guidance: 7, width: 896, height: 1152, seed: null, ipScale: 0.6, neg: '' },
  { id: 'landscape', name: 'Landscape 1152×896', steps: 24, guidance: 6.5 as any, width: 1152, height: 896, seed: null, ipScale: 0.6, neg: '' }
]

const DEFAULTS: Settings = {
  theme: 'dark',
  accentHex: '#06B6D4',
  motion: 1,
  glass: true,
  density: 'comfortable',
  visualMode: 'dashboard',
  shellPreset: 'creator-luxury',
  componentStyle: 'glass',
  presets: DEFAULT_PRESETS,
  defaultPresetId: 'portrait',
  queue: { maxParallel: 1, cancelPrevious: true },
  historyLimit: 100,
  headers: [],
  notifyOnDone: false,
  soundOnDone: false,
  nsfwHide: false,
  banlist: 'nsfw, nude, nudity, porn, explicit'
}

function readLegacyTheme(): ThemeMode | null {
  try {
    const raw = localStorage.getItem('theme')
    if (raw === 'light' || raw === 'dark') return raw
    return null
  } catch {
    return null
  }
}

export function loadSettings(): Settings {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return { ...DEFAULTS, theme: readLegacyTheme() ?? DEFAULTS.theme }
    const parsed = JSON.parse(raw)
    const s: Settings = {
      ...DEFAULTS,
      ...parsed,
      theme: parsed.theme ?? readLegacyTheme() ?? DEFAULTS.theme,
      queue: { ...DEFAULTS.queue, ...parsed.queue },
    }
    return s
  } catch {
    return { ...DEFAULTS, theme: readLegacyTheme() ?? DEFAULTS.theme }
  }
}

export function saveSettings(s: Settings) {
  try { localStorage.setItem(KEY, JSON.stringify(s)) } catch {}
}

export function applySettingsToDOM(s: Settings) {
  const r = document.documentElement
  const hsl = hexToHslString(s.accentHex) || '199 89% 48%'
  r.style.setProperty('--primary', hsl)
  r.style.setProperty('--accent', hsl)
  r.style.setProperty('--ring', hsl)
  r.classList.toggle('dark', s.theme === 'dark')
  r.classList.toggle('reduce-motion', s.motion === 0)
  r.style.setProperty('--motion-mult', String(s.motion === 2 ? 1.4 : s.motion === 1 ? 1 : 0))
  r.style.setProperty('--radius', s.density === 'compact' ? '18px' : '24px')
  r.dataset.visualMode = s.visualMode
}

export function hexToHslString(hex: string): string | null {
  const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex.trim())
  if (!m) return null
  const r = parseInt(m[1], 16)/255, g = parseInt(m[2], 16)/255, b = parseInt(m[3], 16)/255
  const max = Math.max(r,g,b), min = Math.min(r,g,b)
  let h = 0, s = 0, l = (max + min) / 2
  if (max !== min) {
    const d = max - min
    s = l > .5 ? d/(2 - max - min) : d/(max + min)
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break
      case g: h = (b - r) / d + 2; break
      case b: h = (r - g) / d + 4; break
    }
    h /= 6
  }
  return `${Math.round(h*360)} ${Math.round(s*100)}% ${Math.round(l*100)}%`
}
