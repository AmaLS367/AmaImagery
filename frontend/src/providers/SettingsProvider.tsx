import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { Settings, loadSettings, saveSettings, applySettingsToDOM } from '../lib/settings'
import { configureApiHeaders } from '../lib/api'

type Ctx = {
  settings: Settings
  setSettings: (s: Settings) => void
  update: <K extends keyof Settings>(key: K, value: Settings[K]) => void
}

const SettingsCtx = createContext<Ctx | null>(null)

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<Settings>(() => loadSettings())

  useEffect(() => {
    saveSettings(settings)
    applySettingsToDOM(settings)
    // прокинем заголовки в API
    configureApiHeaders(() => {
      const h: Record<string, string> = {}
      for (const kv of settings.headers) {
        const k = (kv.key || '').trim()
        if (k) h[k] = kv.value ?? ''
      }
      return h
    })
  }, [settings])

  const ctx = useMemo<Ctx>(() => ({
    settings,
    setSettings,
    update: (k: keyof Settings, v: Settings[keyof Settings]) => setSettings((prev: Settings) => ({ ...prev, [k]: v })),
  }), [settings])

  return <SettingsCtx.Provider value={ctx}>{children}</SettingsCtx.Provider>
}

export function useSettings() {
  console.log('useSettings hook called');
  const v = useContext(SettingsCtx)
  if (!v) {
    console.error('SettingsProvider is missing in the component tree');
    throw new Error('SettingsProvider is missing')
  }
  console.log('Settings context:', v);
  return v
}
