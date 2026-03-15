import { motion } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'
import {
  Bell,
  Check,
  Cpu,
  Layers,
  Palette,
  Settings as SettingsIcon,
  Shield,
} from 'lucide-react'

import LanguageSwitcher from '../components/LanguageSwitcher'
import { MetaPill, SurfacePanel } from '../components/ui/foundation'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Switch } from '../components/ui/switch'
import { Textarea } from '../components/ui/textarea'
import { getMySettings, patchMySettings } from '../lib/api'
import { localSettingsSections } from '../lib/settingsInventory'
import { cn } from '../lib/utils'
import { useAuth } from '../providers/AuthProvider'
import { useSettings } from '../providers/SettingsProvider'
import { useTranslation } from 'react-i18next'

const PRESETS_ACCENT = [
  '#06B6D4',
  '#0EA5E9',
  '#3B82F6',
  '#2DD4BF',
  '#10B981',
  '#F59E0B',
  '#F97316',
  '#EF4444',
] as const

type Tone = 'dashboard' | 'editorial' | 'cinematic'

function toneCard(tone: Tone) {
  if (tone === 'editorial') return 'border-foreground/10 bg-card/40'
  if (tone === 'cinematic') return 'border-white/10 bg-white/5 text-white backdrop-blur-2xl'
  return 'border-border/50 bg-card/75'
}

function SettingsSection({
  tone,
  title,
  description,
  action,
  children,
  className,
}: {
  tone: Tone
  title: string
  description: string
  action?: React.ReactNode
  children: React.ReactNode
  className?: string
}) {
  return (
    <SurfacePanel className={cn('p-6 md:p-8 space-y-6', toneCard(tone), className)}>
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="space-y-2">
          <h3 className={cn(
            'font-black uppercase tracking-[0.2em] text-xs text-primary',
            tone === 'editorial' && 'font-serif normal-case tracking-normal text-3xl font-light',
            tone === 'cinematic' && 'text-[10px] tracking-[0.35em]',
          )}>
            {title}
          </h3>
          <p className={cn('max-w-2xl text-sm leading-relaxed', tone === 'cinematic' ? 'text-white/60' : 'text-foreground/60')}>
            {description}
          </p>
        </div>
        {action}
      </div>
      {children}
    </SurfacePanel>
  )
}

function ToggleRow({
  tone,
  label,
  description,
  checked,
  onChange,
}: {
  tone: Tone
  label: string
  description?: string
  checked: boolean
  onChange: (checked: boolean) => void
}) {
  return (
    <div className="flex items-start justify-between gap-4 rounded-[24px] border border-border/30 bg-secondary/10 p-4 dark:border-white/10">
      <div className="space-y-1">
        <div className={cn('text-sm font-bold', tone === 'cinematic' ? 'text-white' : 'text-foreground')}>{label}</div>
        {description ? (
          <div className={cn('text-xs leading-relaxed', tone === 'cinematic' ? 'text-white/50' : 'text-foreground/50')}>
            {description}
          </div>
        ) : null}
      </div>
      <Switch checked={checked} onCheckedChange={onChange} />
    </div>
  )
}

export default function Settings() {
  const { t } = useTranslation(['settings', 'common'])
  const { settings, update } = useSettings()
  const { status: authStatus, isAuthenticated } = useAuth()
  const defaultRef = useRef<typeof settings | null>(null)
  const [hydrating, setHydrating] = useState(true)

  if (!defaultRef.current) defaultRef.current = JSON.parse(JSON.stringify(settings))

  const tone = settings.visualMode

  const setHex = (hex: string) => {
    if (!/^#?[0-9a-fA-F]{6}$/.test(hex)) return
    update('accentHex', hex.startsWith('#') ? hex : `#${hex}`)
  }

  const applySnapshot = (payload: Record<string, unknown>) => {
    const defaults = defaultRef.current!
    Object.keys(defaults).forEach((key) => {
      if (payload[key] !== undefined) update(key as never, payload[key] as never)
    })
  }

  useEffect(() => {
    if (authStatus === 'loading') return
    if (!isAuthenticated) {
      setHydrating(false)
      return
    }

    setHydrating(true)
    getMySettings().then((res) => {
      if (res?.data) applySnapshot(res.data)
    }).finally(() => setHydrating(false))
  }, [authStatus, isAuthenticated])

  useEffect(() => {
    if (hydrating || !isAuthenticated) return
    const timeout = setTimeout(() => {
      patchMySettings(settings).catch(() => {})
    }, 1000)
    return () => clearTimeout(timeout)
  }, [settings, hydrating, isAuthenticated])

  const appearanceSection = (
    <SettingsSection
      tone={tone}
      title={t('settings:sections.appearance.title')}
      description={t('settings:sections.appearance.description')}
    >
      <div className="space-y-4">
        <div className="space-y-2">
          <Label className={cn('text-[10px] font-black uppercase tracking-[0.22em]', tone === 'cinematic' ? 'text-white/40' : 'text-foreground/40')}>
            {t('settings:appearance.accent')}
          </Label>
          <div className="flex flex-wrap items-center gap-3">
            {PRESETS_ACCENT.map((color) => (
              <button
                key={color}
                onClick={() => update('accentHex', color)}
                className={cn('h-10 w-10 rounded-2xl transition-transform', settings.accentHex === color ? 'scale-110 ring-2 ring-primary ring-offset-2' : 'opacity-70')}
                style={{ backgroundColor: color }}
              />
            ))}
            <Input value={settings.accentHex} onChange={(event) => setHex(event.target.value)} className="w-32 rounded-2xl font-mono uppercase" />
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <ToggleRow
            tone={tone}
            label={t('settings:appearance.theme.label')}
            description={settings.theme === 'dark' ? t('settings:appearance.theme.dark') : t('settings:appearance.theme.light')}
            checked={settings.theme === 'dark'}
            onChange={() => update('theme', settings.theme === 'dark' ? 'light' : 'dark')}
          />
          <ToggleRow
            tone={tone}
            label={t('settings:appearance.glass.label')}
            description={t('settings:appearance.glass.desc')}
            checked={settings.glass}
            onChange={(checked) => update('glass', !!checked)}
          />
          <ToggleRow
            tone={tone}
            label={t('settings:appearance.density.label')}
            description={settings.density === 'compact' ? t('settings:appearance.density.compact') : t('settings:appearance.density.comfortable')}
            checked={settings.density === 'compact'}
            onChange={(checked) => update('density', checked ? 'compact' : 'comfortable')}
          />
        </div>

        <div className="space-y-3">
          <Label className={cn('text-[10px] font-black uppercase tracking-[0.22em]', tone === 'cinematic' ? 'text-white/40' : 'text-foreground/40')}>
            {t('settings:appearance.motion.label')}
          </Label>
          <div className="grid gap-3 sm:grid-cols-3">
            {[
              { value: 0, label: t('settings:appearance.motion.reduced') },
              { value: 1, label: t('settings:appearance.motion.standard') },
              { value: 2, label: t('settings:appearance.motion.expressive') },
            ].map((option) => (
              <button
                key={option.value}
                onClick={() => update('motion', option.value as 0 | 1 | 2)}
                className={cn(
                  'rounded-[24px] border px-4 py-3 text-sm font-bold transition-all',
                  settings.motion === option.value
                    ? 'border-primary bg-primary/10 text-primary'
                    : tone === 'cinematic'
                      ? 'border-white/10 bg-white/5 text-white/70'
                      : 'border-border bg-secondary/20 text-foreground/70',
                )}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <Label className={cn('text-[10px] font-black uppercase tracking-[0.22em]', tone === 'cinematic' ? 'text-white/40' : 'text-foreground/40')}>
            {t('settings:safety.language.label')}
          </Label>
          <div className="rounded-[24px] border border-border/40 bg-secondary/20 p-4 dark:border-white/10">
            <LanguageSwitcher />
          </div>
        </div>
      </div>
    </SettingsSection>
  )

  const modeSection = (
    <SettingsSection
      tone={tone}
      title={t('settings:sections.mode.title')}
      description={t('settings:sections.mode.description')}
    >
      <div className="space-y-5">
        <div className="space-y-3">
          <Label className={cn('text-[10px] font-black uppercase tracking-[0.22em]', tone === 'cinematic' ? 'text-white/40' : 'text-foreground/40')}>
            {t('settings:generation.visual_mode.label')}
          </Label>
          <div className="grid gap-3 sm:grid-cols-3">
            {(['dashboard', 'editorial', 'cinematic'] as const).map((modeOption) => (
              <button
                key={modeOption}
                onClick={() => update('visualMode', modeOption)}
                className={cn(
                  'rounded-[24px] border px-4 py-4 text-left transition-all',
                  settings.visualMode === modeOption
                    ? 'border-primary bg-primary/10 text-primary shadow-glow-sm'
                    : tone === 'cinematic'
                      ? 'border-white/10 bg-white/5 text-white/70'
                      : 'border-border bg-secondary/20 text-foreground/70',
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-black uppercase tracking-[0.22em]">{t(`settings:generation.visual_mode.${modeOption}`)}</span>
                  {settings.visualMode === modeOption ? <Check className="h-4 w-4" /> : null}
                </div>
                <div className="mt-2 text-xs leading-relaxed opacity-80">
                  {t(`settings:visual_mode_descriptions.${modeOption}`)}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <div className="space-y-3">
            <Label className={cn('text-[10px] font-black uppercase tracking-[0.22em]', tone === 'cinematic' ? 'text-white/40' : 'text-foreground/40')}>
              {t('settings:generation.preset')}
            </Label>
            <div className="grid gap-3 sm:grid-cols-2">
              {(['creator-luxury', 'editorial'] as const).map((shell) => (
                <button
                  key={shell}
                  onClick={() => update('shellPreset', shell)}
                  className={cn(
                    'rounded-[24px] border px-4 py-4 text-sm font-bold transition-all',
                    settings.shellPreset === shell
                      ? 'border-primary bg-primary/10 text-primary'
                      : tone === 'cinematic'
                        ? 'border-white/10 bg-white/5 text-white/70'
                        : 'border-border bg-secondary/20 text-foreground/70',
                  )}
                >
                  {shell}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <Label className={cn('text-[10px] font-black uppercase tracking-[0.22em]', tone === 'cinematic' ? 'text-white/40' : 'text-foreground/40')}>
              {t('settings:generation.component')}
            </Label>
            <div className="grid gap-3 sm:grid-cols-2">
              {(['glass', 'clean-soft'] as const).map((styleOption) => (
                <button
                  key={styleOption}
                  onClick={() => update('componentStyle', styleOption)}
                  className={cn(
                    'rounded-[24px] border px-4 py-4 text-sm font-bold transition-all',
                    settings.componentStyle === styleOption
                      ? 'border-primary bg-primary/10 text-primary'
                      : tone === 'cinematic'
                        ? 'border-white/10 bg-white/5 text-white/70'
                        : 'border-border bg-secondary/20 text-foreground/70',
                  )}
                >
                  {styleOption}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </SettingsSection>
  )

  const queueSection = (
    <SettingsSection tone={tone} title={t('settings:sections.queue.title')} description={t('settings:sections.queue.description')}>
      <div className="space-y-5">
        <div className="space-y-3">
          <Label className={cn('text-[10px] font-black uppercase tracking-[0.22em]', tone === 'cinematic' ? 'text-white/40' : 'text-foreground/40')}>
            {t('settings:queue.parallel.label')}
          </Label>
          <div className="grid gap-3 sm:grid-cols-3">
            {[1, 2, 3].map((count) => (
              <button
                key={count}
                onClick={() => update('queue', { ...settings.queue, maxParallel: count as 1 | 2 | 3 })}
                className={cn(
                  'rounded-[24px] border px-4 py-4 text-sm font-bold transition-all',
                  settings.queue.maxParallel === count
                    ? 'border-primary bg-primary/10 text-primary'
                    : tone === 'cinematic'
                      ? 'border-white/10 bg-white/5 text-white/70'
                      : 'border-border bg-secondary/20 text-foreground/70',
                )}
              >
                {count === 1 ? t('settings:queue.parallel.single') : t('settings:queue.parallel.multi', { count })}
              </button>
            ))}
          </div>
        </div>

        <ToggleRow
          tone={tone}
          label={t('settings:queue.cancel.label')}
          description={t('settings:queue.cancel.desc')}
          checked={settings.queue.cancelPrevious}
          onChange={(checked) => update('queue', { ...settings.queue, cancelPrevious: !!checked })}
        />

        <div className="space-y-3">
          <Label className={cn('text-[10px] font-black uppercase tracking-[0.22em]', tone === 'cinematic' ? 'text-white/40' : 'text-foreground/40')}>
            {t('settings:queue.history')}
          </Label>
          <div className="grid gap-3 sm:grid-cols-3">
            {([50, 100, 500] as const).map((limit) => (
              <button
                key={limit}
                onClick={() => update('historyLimit', limit)}
                className={cn(
                  'rounded-[24px] border px-4 py-4 text-sm font-bold transition-all',
                  settings.historyLimit === limit
                    ? 'border-primary bg-primary/10 text-primary'
                    : tone === 'cinematic'
                      ? 'border-white/10 bg-white/5 text-white/70'
                      : 'border-border bg-secondary/20 text-foreground/70',
                )}
              >
                {limit}
              </button>
            ))}
          </div>
        </div>
      </div>
    </SettingsSection>
  )

  const notificationsSection = (
    <SettingsSection tone={tone} title={t('settings:sections.notifications.title')} description={t('settings:sections.notifications.description')}>
      <div className="grid gap-4 lg:grid-cols-2">
        <ToggleRow
          tone={tone}
          label={t('settings:notifications.desktop.label')}
          description={t('settings:notifications.desktop.desc')}
          checked={settings.notifyOnDone}
          onChange={(checked) => update('notifyOnDone', !!checked)}
        />
        <ToggleRow
          tone={tone}
          label={t('settings:notifications.sound.label')}
          description={t('settings:notifications.sound.desc')}
          checked={settings.soundOnDone}
          onChange={(checked) => update('soundOnDone', !!checked)}
        />
      </div>
    </SettingsSection>
  )

  const safetySection = (
    <SettingsSection tone={tone} title={t('settings:sections.safety.title')} description={t('settings:sections.safety.description')}>
      <div className="space-y-5">
        <ToggleRow
          tone={tone}
          label={t('settings:safety.nsfw.label')}
          description={t('settings:safety.nsfw.desc')}
          checked={settings.nsfwHide}
          onChange={(checked) => update('nsfwHide', !!checked)}
        />
        <div className="space-y-3">
          <Label className={cn('text-[10px] font-black uppercase tracking-[0.22em]', tone === 'cinematic' ? 'text-white/40' : 'text-foreground/40')}>
            {t('settings:safety.banlist.label')}
          </Label>
          <Textarea
            value={settings.banlist}
            onChange={(event) => update('banlist', event.target.value)}
            placeholder={t('settings:safety.banlist.desc')}
            className={cn(
              'min-h-[140px] rounded-[28px] border p-5',
              tone === 'cinematic'
                ? 'border-white/10 bg-black/30 text-white placeholder:text-white/20'
                : 'border-border bg-secondary/20',
            )}
          />
        </div>
      </div>
    </SettingsSection>
  )

  const sectionsMap = {
    appearance: appearanceSection,
    mode: modeSection,
    queue: queueSection,
    notifications: notificationsSection,
    safety: safetySection,
  }

  const orderedSections = localSettingsSections.map((section) => (
    <div key={section.id}>{sectionsMap[section.id]}</div>
  ))

  const renderDashboard = () => (
    <div className="grid gap-6 xl:grid-cols-2 items-start">
      {orderedSections}
    </div>
  )

  const renderEditorial = () => (
    <div className="mx-auto max-w-5xl space-y-8">
      {orderedSections}
    </div>
  )

  const renderCinematic = () => (
    <div className="relative -mx-4 overflow-hidden rounded-[40px] border border-white/10 bg-black px-4 py-6 md:-mx-6 md:px-6 md:py-8">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(14,165,233,0.16),transparent_40%),radial-gradient(circle_at_bottom,rgba(249,115,22,0.12),transparent_35%)]" />
      <div className="relative z-10 grid gap-6 xl:grid-cols-2 items-start">
        {orderedSections}
      </div>
    </div>
  )

  return (
    <section className={cn('page-shell transition-all duration-500', tone === 'cinematic' ? 'py-4 md:py-6' : 'py-8 md:py-12 space-y-8')}>
      {tone !== 'cinematic' ? (
        <SurfacePanel className={cn('mode-hero-panel p-6 md:p-8', tone === 'editorial' && 'mode-hero-panel--editorial text-center')}>
          <div className={cn('flex flex-col gap-6 md:flex-row md:items-end md:justify-between', tone === 'editorial' && 'items-center')}>
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-[10px] font-black uppercase tracking-[0.24em] text-primary">
                <SettingsIcon className="h-3.5 w-3.5" />
                {t('settings:title')}
              </div>
              <div className="space-y-2">
                <h1 className={cn('font-black tracking-tight', tone === 'editorial' ? 'font-serif text-5xl font-light italic md:text-7xl' : 'text-3xl md:text-5xl')}>
                  {t('settings:hero.title')}
                </h1>
                <p className={cn('max-w-3xl text-base leading-relaxed', tone === 'editorial' ? 'mx-auto text-lg' : 'text-foreground/60')}>
                  {t('settings:hero.description')}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <MetaPill>{t(`settings:generation.visual_mode.${settings.visualMode}`)}</MetaPill>
              <MetaPill>{settings.shellPreset}</MetaPill>
              <MetaPill>{settings.componentStyle}</MetaPill>
            </div>
          </div>
        </SurfacePanel>
      ) : null}

      <motion.div key={settings.visualMode} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}>
        {tone === 'dashboard' ? renderDashboard() : tone === 'editorial' ? renderEditorial() : renderCinematic()}
      </motion.div>
    </section>
  )
}
