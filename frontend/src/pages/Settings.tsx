import { motion } from 'framer-motion'
import { useEffect, useMemo, useRef, useState } from 'react'
import { 
  Palette, 
  Cpu, 
  History as HistoryIcon, 
  Bell, 
  Shield, 
  FlaskConical, 
  ChevronRight,
  Settings as SettingsIcon,
  Monitor,
  Layout,
  User,
  Zap
} from 'lucide-react'

import { Button } from '../components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { MetaPill, SectionEyebrow, SurfacePanel } from '../components/ui/foundation'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Switch } from '../components/ui/switch'
import LanguageSwitcher from '../components/LanguageSwitcher'
import { getMySettings, patchMySettings } from '../lib/api'
import { useAuth } from '../providers/AuthProvider'
import { useSettings } from '../providers/SettingsProvider'
import { useTranslation } from 'react-i18next'
import { cn } from '../lib/utils'
import { EditorialFrame } from '../components/editorial/EditorialFrame'

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

export default function Settings() {
  const { t, i18n } = useTranslation(['settings', 'common'])
  const { settings, update } = useSettings()
  const { status: authStatus, isAuthenticated } = useAuth()
  const defaultRef = useRef<typeof settings | null>(null)
  const lastSentRef = useRef('')
  const [hydrating, setHydrating] = useState(true)
  const [activeGroup, setActiveGroup] = useState('appearance')

  const CONTROL_GROUPS = [
    { id: 'appearance', label: t('settings:groups.appearance'), icon: <Palette className="h-4 w-4" /> },
    { id: 'generation-shell', label: t('settings:groups.generation'), icon: <Cpu className="h-4 w-4" /> },
    { id: 'queue-history', label: t('settings:groups.queue'), icon: <HistoryIcon className="h-4 w-4" /> },
    { id: 'notifications', label: t('settings:groups.notifications'), icon: <Bell className="h-4 w-4" /> },
    { id: 'safety-language', label: t('settings:groups.safety'), icon: <Shield className="h-4 w-4" /> },
    { id: 'visual-lab', label: t('settings:groups.lab'), icon: <FlaskConical className="h-4 w-4" /> },
  ] as const

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
      { label: t('settings:config.facts.theme'), value: settings.theme === 'dark' ? t('settings:appearance.theme.dark') : t('settings:appearance.theme.light') },
      { label: t('settings:config.facts.accent'), value: settings.accentHex.toUpperCase() },
      { label: t('settings:config.facts.motion'), value: settings.motion === 0 ? t('settings:appearance.motion.reduced') : settings.motion === 2 ? t('settings:appearance.motion.expressive') : t('settings:appearance.motion.standard') },
      { label: t('settings:config.facts.glass'), value: settings.glass ? 'On' : 'Off' },
      { label: t('settings:config.facts.density'), value: settings.density === 'compact' ? t('settings:appearance.density.compact') : t('settings:appearance.density.comfortable') },
      { label: t('settings:config.facts.history'), value: String(settings.historyLimit) },
    ],
    [settings, i18n.language, t],
  )

  const applySnapshot = (payload: Record<string, unknown>) => {
    const defaults = defaultRef.current!
    update('theme', (payload.theme as typeof settings.theme) ?? defaults.theme)
    update('accentHex', (payload.accentHex as string) ?? defaults.accentHex)
    update('motion', (payload.motion as typeof settings.motion) ?? defaults.motion)
    update('glass', typeof payload.glass === 'boolean' ? payload.glass : defaults.glass)
    update('density', (payload.density as typeof settings.density) ?? defaults.density)
    update('visualMode', (payload.visualMode as typeof settings.visualMode) ?? defaults.visualMode)
    update('shellPreset', (payload.shellPreset as typeof settings.shellPreset) ?? defaults.shellPreset)
    update('componentStyle', (payload.componentStyle as typeof settings.componentStyle) ?? defaults.componentStyle)
    update('historyLimit', (payload.historyLimit as typeof settings.historyLimit) ?? defaults.historyLimit)
    update('nsfwHide', typeof payload.nsfwHide === 'boolean' ? payload.nsfwHide : defaults.nsfwHide)
    update('notifyOnDone', typeof payload.notifyOnDone === 'boolean' ? payload.notifyOnDone : defaults.notifyOnDone)
    update('soundOnDone', typeof payload.soundOnDone === 'boolean' ? payload.soundOnDone : defaults.soundOnDone)
    update('banlist', (payload.banlist as string) ?? defaults.banlist)
    update('queue', (payload.queue as typeof settings.queue) ?? defaults.queue)
    update('defaultPresetId', (payload.defaultPresetId as string | null) ?? defaults.defaultPresetId)
  }

  const buildSettingsPayload = () => ({
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
  })

  const loadFromServer = () => {
    setHydrating(true)
    const defaults = defaultRef.current!
    applySnapshot(defaults as unknown as Record<string, unknown>)

    getMySettings()
      .then((response) => {
        const remote = (response?.data as Record<string, unknown>) || {}
        applySnapshot(remote)
        lastSentRef.current = JSON.stringify({
          ...defaults,
          ...remote,
        })
      })
      .catch(() => {
        lastSentRef.current = JSON.stringify(defaults)
      })
      .finally(() => setHydrating(false))
  }

  useEffect(() => {
    const defaults = defaultRef.current!

    if (authStatus === 'loading') {
      setHydrating(true)
      return
    }

    if (!isAuthenticated) {
      applySnapshot(defaults as unknown as Record<string, unknown>)
      lastSentRef.current = JSON.stringify(defaults)
      setHydrating(false)
      return
    }

    loadFromServer()
  }, [authStatus, isAuthenticated])

  useEffect(() => {
    if (hydrating || !isAuthenticated) return

    const timeout = setTimeout(() => {
      const payload = buildSettingsPayload()
      const snapshot = JSON.stringify(payload)
      if (snapshot !== lastSentRef.current) {
        lastSentRef.current = snapshot
        patchMySettings(payload).catch(() => {})
      }
    }, 400)

    return () => clearTimeout(timeout)
  }, [settings, hydrating, isAuthenticated])

  return (
    <EditorialFrame
      eyebrow="Settings"
      title="Personalize your studio experience."
      summary="Control how the interface responds, manage your generation queue, and set your preferences for a professional creative workflow."
      pills={['v1.0.4-stable', 'Cloud Sync', 'Real-time Updates']}
    >
      <div className="grid gap-12 xl:grid-cols-[280px_1fr_340px] items-start">
        {/* Navigation Sidebar */}
        <aside className="space-y-8 sticky top-24">
          <SurfacePanel className="p-6 space-y-2">
            <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-primary px-3 mb-4">Command Center</h4>
            <nav className="space-y-1">
              {CONTROL_GROUPS.map((group) => (
                <a
                  key={group.id}
                  href={`#${group.id}`}
                  onClick={() => setActiveGroup(group.id)}
                  className={cn(
                    "flex items-center gap-3 rounded-full px-4 py-3 text-sm font-bold transition-all",
                    activeGroup === group.id 
                      ? "bg-primary text-primary-foreground shadow-glow" 
                      : "text-foreground/60 hover:bg-black/5 dark:text-white/60 dark:hover:bg-white/5"
                  )}
                >
                  <span className={cn(activeGroup === group.id ? "text-primary-foreground" : "text-primary")}>{group.icon}</span>
                  {group.label}
                </a>
              ))}
            </nav>
          </SurfacePanel>

          <SurfacePanel className="p-8 space-y-6">
             <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-2xl bg-secondary flex items-center justify-center dark:bg-white/5">
                   <User className="h-5 w-5 text-primary" />
                </div>
                <div>
                   <div className="text-[10px] font-black uppercase tracking-widest text-foreground/40 dark:text-white/40">Connected as</div>
                   <div className="text-sm font-bold text-foreground dark:text-white">Studio Operator</div>
                </div>
             </div>
             <Button variant="outline" className="w-full rounded-full font-bold border-border">Account Portal</Button>
          </SurfacePanel>
        </aside>

        {/* Main Controls */}
        <div className="space-y-10">
          <SurfacePanel className="p-10 space-y-10">
            <div className="space-y-2 border-b border-border pb-8 dark:border-white/10">
               <h2 className="font-display text-3xl font-bold tracking-tight text-foreground dark:text-white">{t('settings:config.title')}</h2>
               <p className="text-foreground/60 dark:text-white/60 font-medium">{t('settings:config.preset')}: <span className="text-primary">{settings.shellPreset === 'creator-luxury' ? 'Creator-Luxury' : 'Editorial'}</span></p>
            </div>

            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {summaryFacts.map((fact) => (
                <div key={fact.label} className="p-6 rounded-3xl border border-border bg-secondary/30 dark:border-white/10 dark:bg-white/5">
                  <div className="text-[10px] font-black uppercase tracking-[0.2em] text-primary">{fact.label}</div>
                  <div className="mt-3 text-sm font-bold text-foreground dark:text-white/90">{fact.value}</div>
                </div>
              ))}
            </div>
          </SurfacePanel>

          <div className="space-y-12">
            {/* Appearance Section */}
            <section id="appearance" className="scroll-mt-32 space-y-8">
              <div className="flex items-center gap-4">
                 <div className="h-px flex-1 bg-border dark:border-white/10" />
                 <h3 className="text-[10px] font-black uppercase tracking-[0.4em] text-primary">{t('settings:appearance.title')}</h3>
                 <div className="h-px flex-1 bg-border dark:border-white/10" />
              </div>

              <SurfacePanel className="p-10 space-y-10">
                <ControlRow 
                  label={t('settings:appearance.theme.label')} 
                  description={settings.theme === 'dark' ? t('settings:appearance.theme.dark') : t('settings:appearance.theme.light')}
                >
                  <Switch checked={settings.theme === 'dark'} onCheckedChange={() => update('theme', settings.theme === 'dark' ? 'light' : 'dark')} />
                </ControlRow>

                <div className="space-y-6">
                  <Label className="text-lg font-bold tracking-tight text-foreground dark:text-white">{t('settings:appearance.accent')}</Label>
                  <div className="flex flex-wrap items-center gap-4 p-6 rounded-3xl bg-secondary/30 border border-border dark:border-white/10 dark:bg-white/5">
                    {PRESETS_ACCENT.map((color) => (
                      <button
                        key={color}
                        type="button"
                        onClick={() => update('accentHex', color)}
                        className={cn(
                          "h-10 w-10 rounded-full transition-all hover:scale-110 shadow-glow",
                          settings.accentHex === color ? "ring-4 ring-primary/20 scale-110" : ""
                        )}
                        style={{ backgroundColor: color }}
                      />
                    ))}
                    <div className="h-8 w-px bg-border mx-2 dark:border-white/10" />
                    <Input 
                      value={settings.accentHex} 
                      onChange={(event) => setHex(event.target.value)} 
                      className="w-32 h-12 rounded-xl border-border bg-background font-mono font-bold text-center" 
                    />
                  </div>
                </div>

                <div className="space-y-6">
                  <Label className="text-lg font-bold tracking-tight text-foreground dark:text-white">{t('settings:appearance.motion.label')}</Label>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { id: 0, label: t('settings:appearance.motion.reduced') },
                      { id: 1, label: t('settings:appearance.motion.standard') },
                      { id: 2, label: t('settings:appearance.motion.expressive') }
                    ].map((m) => (
                      <Button 
                        key={m.id} 
                        variant={settings.motion === m.id ? 'default' : 'outline'} 
                        className={cn("h-12 rounded-xl font-bold border-border", settings.motion === m.id && "shadow-glow")}
                        onClick={() => update('motion', m.id as any)}
                      >
                        {m.label}
                      </Button>
                    ))}
                  </div>
                </div>

                <ControlRow 
                  label={t('settings:appearance.glass.label')} 
                  description={t('settings:appearance.glass.desc')}
                >
                  <Switch checked={settings.glass} onCheckedChange={(checked) => update('glass', !!checked)} />
                </ControlRow>
              </SurfacePanel>
            </section>

            {/* Generation Shell Section */}
            <section id="generation-shell" className="scroll-mt-32 space-y-8">
              <div className="flex items-center gap-4">
                 <div className="h-px flex-1 bg-border dark:border-white/10" />
                 <h3 className="text-[10px] font-black uppercase tracking-[0.4em] text-primary">{t('settings:generation.title')}</h3>
                 <div className="h-px flex-1 bg-border dark:border-white/10" />
              </div>

              <SurfacePanel className="p-10 space-y-10">
                <div className="grid gap-10 sm:grid-cols-2">
                  <div className="space-y-6">
                    <Label className="text-lg font-bold tracking-tight text-foreground dark:text-white">{t('settings:generation.preset')}</Label>
                    <div className="flex gap-3">
                      <Button 
                        variant={settings.shellPreset === 'creator-luxury' ? 'default' : 'outline'} 
                        className="flex-1 h-12 rounded-xl font-bold border-border" 
                        onClick={() => update('shellPreset', 'creator-luxury')}
                      >
                        Luxury
                      </Button>
                      <Button 
                        variant={settings.shellPreset === 'editorial' ? 'default' : 'outline'} 
                        className="flex-1 h-12 rounded-xl font-bold border-border" 
                        onClick={() => update('shellPreset', 'editorial')}
                      >
                        Editorial
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-6">
                    <Label className="text-lg font-bold tracking-tight text-foreground dark:text-white">{t('settings:generation.component')}</Label>
                    <div className="flex gap-3">
                      <Button 
                        variant={settings.componentStyle === 'glass' ? 'default' : 'outline'} 
                        className="flex-1 h-12 rounded-xl font-bold border-border" 
                        onClick={() => update('componentStyle', 'glass')}
                      >
                        Glass
                      </Button>
                      <Button 
                        variant={settings.componentStyle === 'clean-soft' ? 'default' : 'outline'} 
                        className="flex-1 h-12 rounded-xl font-bold border-border" 
                        onClick={() => update('componentStyle', 'clean-soft')}
                      >
                        Soft
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="space-y-6">
                  <Label className="text-lg font-bold tracking-tight text-foreground dark:text-white">{t('settings:generation.visual_mode.label')}</Label>
                  <div className="grid grid-cols-3 gap-3">
                    {['dashboard', 'editorial', 'cinematic'].map((mode) => (
                      <Button 
                        key={mode} 
                        variant={settings.visualMode === mode ? 'default' : 'outline'} 
                        className="h-12 rounded-xl font-bold border-border capitalize" 
                        onClick={() => update('visualMode', mode as any)}
                      >
                        {t(`settings:generation.visual_mode.${mode}`)}
                      </Button>
                    ))}
                  </div>
                </div>
              </SurfacePanel>
            </section>

            {/* Safety & Language Section */}
            <section id="safety-language" className="scroll-mt-32 space-y-8">
              <div className="flex items-center gap-4">
                 <div className="h-px flex-1 bg-border dark:border-white/10" />
                 <h3 className="text-[10px] font-black uppercase tracking-[0.4em] text-primary">{t('settings:safety.title')}</h3>
                 <div className="h-px flex-1 bg-border dark:border-white/10" />
              </div>

              <SurfacePanel className="p-10 space-y-10">
                <ControlRow 
                  label={t('settings:safety.nsfw.label')} 
                  description={t('settings:safety.nsfw.desc')}
                >
                  <Switch checked={settings.nsfwHide} onCheckedChange={(checked) => update('nsfwHide', !!checked)} />
                </ControlRow>

                <ControlRow 
                  label={t('settings:safety.language.label')} 
                  description={t('settings:safety.language.desc')}
                >
                  <LanguageSwitcher />
                </ControlRow>

                <div className="space-y-6">
                  <Label className="text-lg font-bold tracking-tight text-foreground dark:text-white">{t('settings:safety.banlist.label')}</Label>
                  <textarea
                    className="min-h-[160px] w-full rounded-[32px] border border-border bg-secondary/30 px-8 py-6 text-base font-medium leading-relaxed outline-none focus:border-primary/50 transition-all dark:border-white/10 dark:bg-white/5 dark:text-white font-mono"
                    value={settings.banlist}
                    placeholder={t('settings:safety.banlist.desc')}
                    onChange={(event) => update('banlist', event.target.value)}
                  />
                </div>
              </SurfacePanel>
            </section>
          </div>
        </div>

        {/* Status Aside */}
        <aside className="space-y-8 sticky top-24">
          <SurfacePanel className="p-8 space-y-8" id="visual-lab">
            <div className="space-y-3">
              <div className="inline-flex items-center gap-2 text-primary">
                 <FlaskConical className="h-5 w-5" />
                 <h3 className="font-display text-xl font-bold">{t('settings:lab.title')}</h3>
              </div>
              <p className="text-sm text-foreground/60 dark:text-white/60 font-medium leading-relaxed">
                {t('settings:lab.desc')}
              </p>
            </div>

            <div className="relative aspect-square w-full overflow-hidden rounded-[32px] border border-border bg-secondary shadow-inner dark:bg-black/40 dark:border-white/10">
               <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(14,165,233,0.15),transparent_50%),radial-gradient(circle_at_bottom_right,rgba(45,212,191,0.1),transparent_50%)]" />
               <div className="absolute inset-0 flex items-center justify-center p-8">
                  <div className="flex flex-col gap-3 w-full">
                    <MetaPill className="justify-center bg-background/80 backdrop-blur-md border-border">{settings.shellPreset.toUpperCase()}</MetaPill>
                    <MetaPill className="justify-center bg-background/80 backdrop-blur-md border-border">{settings.visualMode.toUpperCase()}</MetaPill>
                    <MetaPill className="justify-center bg-background/80 backdrop-blur-md border-border">{settings.density.toUpperCase()}</MetaPill>
                  </div>
               </div>
            </div>

            <Button onClick={applyVisualMode} size="lg" className="w-full h-14 rounded-full font-bold shadow-glow">
               {t('settings:lab.apply')}
            </Button>
          </SurfacePanel>

          <SurfacePanel className="p-8 space-y-6">
             <div className="flex items-center gap-3">
                <Monitor className="h-5 w-5 text-primary" />
                <h3 className="font-display text-xl font-bold text-foreground dark:text-white">Sync Status</h3>
             </div>
             <div className="space-y-4">
                <StatusRow label="API Latency" value="24ms" />
                <StatusRow label="Cloud Archive" value="Stable" />
                <StatusRow label="Local Presets" value={`${settings.presets.length} active`} />
             </div>
          </SurfacePanel>
        </aside>
      </div>
    </EditorialFrame>
  )
}

function ControlRow({ label, description, children }: { label: string, description: string, children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-8 p-8 rounded-3xl bg-secondary/30 border border-border dark:border-white/10 dark:bg-white/5 transition-all hover:bg-secondary/50 dark:hover:bg-white/8">
      <div className="space-y-1">
        <Label className="text-lg font-bold tracking-tight text-foreground dark:text-white">{label}</Label>
        <div className="text-sm text-foreground/60 dark:text-white/60 font-medium">{description}</div>
      </div>
      <div className="shrink-0">
        {children}
      </div>
    </div>
  )
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-[10px] font-black uppercase tracking-widest border-b border-border pb-3 dark:border-white/5 last:border-0 last:pb-0">
      <span className="text-foreground/40 dark:text-white/40">{label}</span>
      <span className="text-primary">{value}</span>
    </div>
  )
}

function FactRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-sm py-1">
      <span className="text-muted-foreground font-medium">{label}</span>
      <span className="font-bold text-foreground/90 dark:text-white">{value}</span>
    </div>
  )
}
