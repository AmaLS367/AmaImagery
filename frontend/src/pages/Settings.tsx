import { motion } from 'framer-motion'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { Button } from '../components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { MetaPill, SectionEyebrow, SurfacePanel } from '../components/ui/foundation'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Switch } from '../components/ui/switch'
import LanguageSwitcher from '../components/LanguageSwitcher'
import { appRoutes } from '../lib/routes'
import { getMySettings, patchMySettings } from '../lib/api'
import { useSettings } from '../providers/SettingsProvider'
import { useTranslation } from 'react-i18next'

const PRESETS_ACCENT = [
  '#06B6D4',
  '#0EA5E9',
  '#3B82F6',
  '#0F7ABF',
  '#2DD4BF',
  '#10B981',
  '#F59E0B',
  '#F97316',
  '#EF4444',
] as const

const CONTROL_GROUPS = [
  { id: 'appearance', label: 'Appearance' },
  { id: 'generation-shell', label: 'Generation shell' },
  { id: 'queue-history', label: 'Queue & history' },
  { id: 'notifications', label: 'Notifications' },
  { id: 'safety-language', label: 'Safety & language' },
  { id: 'visual-lab', label: 'Visual lab' },
] as const

export default function Settings() {
  const { settings, update } = useSettings()
  const defaultRef = useRef<typeof settings | null>(null)
  const lastSentRef = useRef('')
  const [hydrating, setHydrating] = useState(true)
  const { i18n } = useTranslation()

  if (!defaultRef.current) {
    defaultRef.current = JSON.parse(JSON.stringify(settings))
  }

  const setHex = (hex: string) => {
    if (!/^#?[0-9a-fA-F]{6}$/.test(hex)) return
    update('accentHex', hex.startsWith('#') ? hex : `#${hex}`)
  }

  const applyVisualMode = () => {
    if (settings.visualMode === 'editorial') {
      update('shellPreset', 'editorial')
      update('componentStyle', 'clean-soft')
      update('glass', false)
    } else if (settings.visualMode === 'cinematic') {
      update('shellPreset', 'creator-luxury')
      update('componentStyle', 'glass')
      update('glass', true)
    } else {
      update('shellPreset', 'creator-luxury')
      update('componentStyle', 'glass')
    }
  }

  const summaryFacts = useMemo(
    () => [
      { label: 'Theme', value: settings.theme === 'dark' ? 'Dark' : 'Light' },
      { label: 'Accent', value: settings.accentHex.toUpperCase() },
      { label: 'Motion', value: settings.motion === 0 ? 'Reduced' : settings.motion === 2 ? 'Expressive' : 'Standard' },
      { label: 'Glass panels', value: settings.glass ? 'On' : 'Off' },
      { label: 'Density', value: settings.density === 'compact' ? 'Compact' : 'Comfortable' },
      {
        label: 'Queue behavior',
        value: `${settings.queue.maxParallel === 1 ? 'Single active' : `${settings.queue.maxParallel} parallel`} · ${
          settings.queue.cancelPrevious ? 'cancel previous' : 'keep previous'
        }`,
      },
      { label: 'History limit', value: String(settings.historyLimit) },
      { label: 'NSFW visibility', value: settings.nsfwHide ? 'Hidden by default' : 'Visible' },
      {
        label: 'Notifications',
        value: [settings.notifyOnDone ? 'Desktop' : null, settings.soundOnDone ? 'sound' : null].filter(Boolean).join(' + ') || 'Off',
      },
      { label: 'Language', value: i18n.language === 'ru' ? 'Russian' : 'English' },
    ],
    [settings, i18n.language],
  )

  const loadFromServer = () => {
    setHydrating(true)
    const defaults = defaultRef.current!

    Object.entries(defaults).forEach(([key, value]) => {
      update(key as keyof typeof defaults, value as never)
    })

    getMySettings()
      .then((response) => {
        const remote = (response?.data as Record<string, unknown>) || {}
        update('theme', (remote.theme as typeof settings.theme) ?? defaults.theme)
        update('accentHex', (remote.accentHex as string) ?? defaults.accentHex)
        update('motion', (remote.motion as typeof settings.motion) ?? defaults.motion)
        update('glass', typeof remote.glass === 'boolean' ? remote.glass : defaults.glass)
        update('density', (remote.density as typeof settings.density) ?? defaults.density)
        update('visualMode', (remote.visualMode as typeof settings.visualMode) ?? defaults.visualMode)
        update('shellPreset', (remote.shellPreset as typeof settings.shellPreset) ?? defaults.shellPreset)
        update('componentStyle', (remote.componentStyle as typeof settings.componentStyle) ?? defaults.componentStyle)
        update('historyLimit', (remote.historyLimit as typeof settings.historyLimit) ?? defaults.historyLimit)
        update('nsfwHide', typeof remote.nsfwHide === 'boolean' ? remote.nsfwHide : defaults.nsfwHide)
        update('notifyOnDone', typeof remote.notifyOnDone === 'boolean' ? remote.notifyOnDone : defaults.notifyOnDone)
        update('soundOnDone', typeof remote.soundOnDone === 'boolean' ? remote.soundOnDone : defaults.soundOnDone)
        update('banlist', (remote.banlist as string) ?? defaults.banlist)
        update('queue', (remote.queue as typeof settings.queue) ?? defaults.queue)
        update('defaultPresetId', (remote.defaultPresetId as string | null) ?? defaults.defaultPresetId)
      })
      .catch(() => {})
      .finally(() => setHydrating(false))
  }

  useEffect(() => {
    loadFromServer()
    const onAuth = () => loadFromServer()
    window.addEventListener('auth:update', onAuth)
    return () => window.removeEventListener('auth:update', onAuth)
  }, [])

  useEffect(() => {
    if (hydrating) return

    const timeout = setTimeout(() => {
      const payload = {
        theme: settings.theme,
        accentHex: settings.accentHex,
        motion: settings.motion,
        glass: settings.glass,
        density: settings.density,
        visualMode: settings.visualMode,
        shellPreset: settings.shellPreset,
        componentStyle: settings.componentStyle,
        historyLimit: settings.historyLimit,
        nsfwHide: settings.nsfwHide,
        notifyOnDone: settings.notifyOnDone,
        soundOnDone: settings.soundOnDone,
        banlist: settings.banlist,
        queue: settings.queue,
        defaultPresetId: settings.defaultPresetId,
      }

      const snapshot = JSON.stringify(payload)
      if (snapshot !== lastSentRef.current) {
        lastSentRef.current = snapshot
        patchMySettings(payload).catch(() => {})
      }
    }, 400)

    return () => clearTimeout(timeout)
  }, [settings, hydrating])

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="page-shell space-y-6 py-8 xl:py-10"
    >
      <SurfacePanel glass className="space-y-5 p-6 md:p-8">
        <SectionEyebrow>Settings</SectionEyebrow>
        <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr] xl:items-end">
          <div className="space-y-4">
            <h1 className="font-display text-4xl font-semibold tracking-[-0.06em] text-foreground sm:text-5xl">
              Serious control center with visual lab and live shell preview.
            </h1>
            <p className="max-w-3xl text-base leading-7 text-muted-foreground">
              Theme, accent, motion, glass, queue behavior, history limit, NSFW visibility, notifications, language,
              banlist, presets, density, and visual mode selector all stay visible in one place.
            </p>
          </div>
          <div className="flex flex-wrap gap-2 xl:justify-end">
            <MetaPill>Theme</MetaPill>
            <MetaPill>Queue</MetaPill>
            <MetaPill>Safety</MetaPill>
            <MetaPill>Visual lab</MetaPill>
          </div>
        </div>
      </SurfacePanel>

      <div className="grid gap-6 xl:grid-cols-[260px_minmax(0,1fr)_320px]">
        <SurfacePanel className="space-y-3 p-4">
          <div className="text-sm font-semibold text-foreground">Control groups</div>
          {CONTROL_GROUPS.map((group) => (
            <a
              key={group.id}
              href={`#${group.id}`}
              className="flex min-h-[60px] items-center rounded-[22px] border border-border/60 bg-card/60 px-4 text-sm font-semibold text-foreground/80 transition-colors hover:bg-card"
            >
              {group.label}
            </a>
          ))}
        </SurfacePanel>

        <div className="space-y-6">
          <SurfacePanel className="space-y-6 p-6 md:p-8">
            <div className="space-y-1">
              <div className="text-sm font-semibold text-foreground">Settings / Default / Dark</div>
              <div className="text-sm text-muted-foreground">{settings.shellPreset === 'creator-luxury' ? 'Creator-Luxury' : 'Editorial'}</div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              {summaryFacts.map((fact) => (
                <div key={fact.label} className="rounded-[22px] border border-border/60 bg-card/60 px-4 py-4">
                  <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">{fact.label}</div>
                  <div className="mt-2 text-base font-semibold text-foreground">{fact.value}</div>
                </div>
              ))}
            </div>

            <div className="space-y-2">
              <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Banlist</div>
              <div className="rounded-[22px] border border-border/60 bg-card/60 px-4 py-4 text-sm leading-6 text-muted-foreground">
                {settings.banlist}
              </div>
            </div>
          </SurfacePanel>

          <div className="grid gap-6 xl:grid-cols-2">
            <Card glass={settings.glass} id="appearance">
              <CardHeader>
                <CardTitle>Appearance</CardTitle>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <Label>Theme</Label>
                    <div className="text-sm text-muted-foreground">{settings.theme === 'dark' ? 'Dark shell' : 'Light editorial shell'}</div>
                  </div>
                  <Switch checked={settings.theme === 'dark'} onCheckedChange={() => update('theme', settings.theme === 'dark' ? 'light' : 'dark')} />
                </div>

                <div className="space-y-3">
                  <Label>Accent palette</Label>
                  <div className="flex flex-wrap items-center gap-2">
                    {PRESETS_ACCENT.map((color) => (
                      <button
                        key={color}
                        type="button"
                        onClick={() => update('accentHex', color)}
                        className="h-9 w-9 rounded-full border border-white/10 shadow-panel"
                        style={{ backgroundColor: color }}
                        aria-label={`Use accent ${color}`}
                      />
                    ))}
                    <Input value={settings.accentHex} onChange={(event) => setHex(event.target.value)} className="w-36" />
                  </div>
                </div>

                <div className="space-y-3">
                  <Label>Motion</Label>
                  <div className="flex flex-wrap gap-2">
                    {[0, 1, 2].map((value) => (
                      <Button key={value} variant={settings.motion === value ? 'default' : 'secondary'} onClick={() => update('motion', value as 0 | 1 | 2)}>
                        {value === 0 ? 'Reduced' : value === 1 ? 'Standard' : 'Expressive'}
                      </Button>
                    ))}
                  </div>
                </div>

                <div className="flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <Label>Glass panels</Label>
                    <div className="text-sm text-muted-foreground">Enable translucent cards in the main product shell.</div>
                  </div>
                  <Switch checked={settings.glass} onCheckedChange={(checked) => update('glass', !!checked)} />
                </div>

                <div className="space-y-3">
                  <Label>Density</Label>
                  <div className="flex flex-wrap gap-2">
                    <Button variant={settings.density === 'comfortable' ? 'default' : 'secondary'} onClick={() => update('density', 'comfortable')}>
                      Comfortable
                    </Button>
                    <Button variant={settings.density === 'compact' ? 'default' : 'secondary'} onClick={() => update('density', 'compact')}>
                      Compact
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card glass={settings.glass} id="generation-shell">
              <CardHeader>
                <CardTitle>Generation shell</CardTitle>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="space-y-3">
                  <Label>Shell preset</Label>
                  <div className="flex flex-wrap gap-2">
                    <Button variant={settings.shellPreset === 'creator-luxury' ? 'default' : 'secondary'} onClick={() => update('shellPreset', 'creator-luxury')}>
                      Creator-Luxury
                    </Button>
                    <Button variant={settings.shellPreset === 'editorial' ? 'default' : 'secondary'} onClick={() => update('shellPreset', 'editorial')}>
                      Editorial
                    </Button>
                  </div>
                </div>

                <div className="space-y-3">
                  <Label>Component style</Label>
                  <div className="flex flex-wrap gap-2">
                    <Button variant={settings.componentStyle === 'glass' ? 'default' : 'secondary'} onClick={() => update('componentStyle', 'glass')}>
                      Glass
                    </Button>
                    <Button variant={settings.componentStyle === 'clean-soft' ? 'default' : 'secondary'} onClick={() => update('componentStyle', 'clean-soft')}>
                      Clean soft
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Default preset</Label>
                  <select
                    value={settings.defaultPresetId ?? ''}
                    onChange={(event) => update('defaultPresetId', event.target.value || null)}
                    className="h-12 w-full rounded-[18px] border border-border/70 bg-card/85 px-4 text-sm shadow-panel"
                  >
                    {settings.presets.map((preset) => (
                      <option key={preset.id} value={preset.id}>
                        {preset.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-3">
                  <Label>Visual mode</Label>
                  <div className="flex flex-wrap gap-2">
                    <Button variant={settings.visualMode === 'dashboard' ? 'default' : 'secondary'} onClick={() => update('visualMode', 'dashboard')}>
                      Dashboard
                    </Button>
                    <Button variant={settings.visualMode === 'editorial' ? 'default' : 'secondary'} onClick={() => update('visualMode', 'editorial')}>
                      Editorial
                    </Button>
                    <Button variant={settings.visualMode === 'cinematic' ? 'default' : 'secondary'} onClick={() => update('visualMode', 'cinematic')}>
                      Cinematic
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card glass={settings.glass} id="queue-history">
              <CardHeader>
                <CardTitle>Queue &amp; history</CardTitle>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="space-y-2">
                  <Label>Parallel jobs</Label>
                  <select
                    value={settings.queue.maxParallel}
                    onChange={(event) => update('queue', { ...settings.queue, maxParallel: Number(event.target.value) as 1 | 2 | 3 })}
                    className="h-12 w-full rounded-[18px] border border-border/70 bg-card/85 px-4 text-sm shadow-panel"
                  >
                    <option value={1}>Single active</option>
                    <option value={2}>2 parallel</option>
                    <option value={3}>3 parallel</option>
                  </select>
                </div>

                <div className="flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <Label>Cancel previous</Label>
                    <div className="text-sm text-muted-foreground">Cancel older requests when a new one starts.</div>
                  </div>
                  <Switch checked={settings.queue.cancelPrevious} onCheckedChange={(checked) => update('queue', { ...settings.queue, cancelPrevious: !!checked })} />
                </div>

                <div className="space-y-2">
                  <Label>History limit</Label>
                  <select
                    value={settings.historyLimit}
                    onChange={(event) => update('historyLimit', Number(event.target.value) as 50 | 100 | 500)}
                    className="h-12 w-full rounded-[18px] border border-border/70 bg-card/85 px-4 text-sm shadow-panel"
                  >
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                    <option value={500}>500</option>
                  </select>
                </div>
              </CardContent>
            </Card>

            <Card glass={settings.glass} id="notifications">
              <CardHeader>
                <CardTitle>Notifications</CardTitle>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <Label>Desktop notifications</Label>
                    <div className="text-sm text-muted-foreground">Notify when a generation completes.</div>
                  </div>
                  <Switch checked={settings.notifyOnDone} onCheckedChange={(checked) => update('notifyOnDone', !!checked)} />
                </div>

                <div className="flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <Label>Sound</Label>
                    <div className="text-sm text-muted-foreground">Play a tone when the runtime returns an artifact.</div>
                  </div>
                  <Switch checked={settings.soundOnDone} onCheckedChange={(checked) => update('soundOnDone', !!checked)} />
                </div>
              </CardContent>
            </Card>

            <Card glass={settings.glass} id="safety-language">
              <CardHeader>
                <CardTitle>Safety &amp; language</CardTitle>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <Label>NSFW visibility</Label>
                    <div className="text-sm text-muted-foreground">Hide explicit archive results by default.</div>
                  </div>
                  <Switch checked={settings.nsfwHide} onCheckedChange={(checked) => update('nsfwHide', !!checked)} />
                </div>

                <div className="flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <Label>Language</Label>
                    <div className="text-sm text-muted-foreground">English and Russian remain available from the shell.</div>
                  </div>
                  <LanguageSwitcher />
                </div>

                <div className="space-y-3">
                  <Label>Banlist</Label>
                  <textarea
                    className="min-h-[140px] w-full rounded-[18px] border border-border/70 bg-card/85 px-4 py-3 text-sm shadow-panel"
                    value={settings.banlist}
                    onChange={(event) => update('banlist', event.target.value)}
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <SurfacePanel className="space-y-5 p-6" id="visual-lab">
          <div className="space-y-1">
            <div className="text-sm font-semibold text-foreground">Settings / Visual Lab Open / Dark</div>
            <div className="text-sm text-muted-foreground">Live preview</div>
          </div>

          <div className="overflow-hidden rounded-[28px] border border-border/60 bg-[radial-gradient(circle_at_top_left,rgba(14,165,233,0.22),transparent_32%),radial-gradient(circle_at_top_right,rgba(45,212,191,0.16),transparent_28%),linear-gradient(180deg,#08121d,#09111a)]">
            <div className="h-[260px]" />
          </div>

          <div className="flex flex-wrap gap-2">
            <MetaPill>Main product</MetaPill>
            <MetaPill>{settings.componentStyle === 'glass' ? 'Glass' : 'Clean soft'}</MetaPill>
            <MetaPill>{settings.visualMode === 'cinematic' ? 'Cinematic' : settings.visualMode === 'editorial' ? 'Editorial' : 'Dashboard'}</MetaPill>
          </div>

          <Button onClick={applyVisualMode}>Apply visual mode</Button>
          <Button asChild variant="ghost">
            <Link to={appRoutes.modes}>Open Modes study</Link>
          </Button>
        </SurfacePanel>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <SurfacePanel className="space-y-5 p-6 md:p-8">
          <div className="space-y-1">
            <div className="text-sm font-semibold text-foreground">Settings / Accent Changed / Light</div>
            <div className="text-sm text-muted-foreground">Shell adjustments stay visible.</div>
          </div>
          <div className="flex flex-wrap gap-2">
            <MetaPill>Shell preset: {settings.shellPreset === 'editorial' ? 'Editorial' : 'Creator-Luxury'}</MetaPill>
            <MetaPill>Component style: {settings.componentStyle === 'clean-soft' ? 'Clean soft' : 'Glass'}</MetaPill>
            <MetaPill>Density: {settings.density === 'compact' ? 'Compact' : 'Comfortable'}</MetaPill>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-[22px] border border-border/60 bg-card/60 px-4 py-4">
              <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Accent palette</div>
              <div className="mt-2 font-semibold text-foreground">{settings.accentHex.toUpperCase()}</div>
            </div>
            <div className="rounded-[22px] border border-border/60 bg-card/60 px-4 py-4">
              <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Visual mode</div>
              <div className="mt-2 font-semibold text-foreground">
                {settings.visualMode === 'dashboard' ? 'Dashboard' : settings.visualMode === 'editorial' ? 'Editorial' : 'Cinematic'}
              </div>
            </div>
          </div>
        </SurfacePanel>

        <SurfacePanel className="space-y-5 p-6 md:p-8">
          <div className="space-y-1">
            <div className="text-sm font-semibold text-foreground">Settings / Compact Density / Dark</div>
            <div className="text-sm text-muted-foreground">Density reshapes shell spacing without hiding controls.</div>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-[22px] border border-border/60 bg-card/60 px-4 py-4">
              <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Surface radius</div>
              <div className="mt-2 font-semibold text-foreground">{settings.density === 'compact' ? 'Reduced' : 'Standard'}</div>
            </div>
            <div className="rounded-[22px] border border-border/60 bg-card/60 px-4 py-4">
              <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Panel padding</div>
              <div className="mt-2 font-semibold text-foreground">{settings.density === 'compact' ? '16' : '24'}</div>
            </div>
            <div className="rounded-[22px] border border-border/60 bg-card/60 px-4 py-4">
              <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Metadata pill size</div>
              <div className="mt-2 font-semibold text-foreground">{settings.density === 'compact' ? 'Small' : 'Standard'}</div>
            </div>
          </div>
        </SurfacePanel>
      </div>
    </motion.section>
  )
}
