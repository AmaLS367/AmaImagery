import { motion } from 'framer-motion'
import { useEffect, useState, useRef} from 'react'

import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Label } from '../components/ui/label'
import { Switch } from '../components/ui/switch'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { useSettings } from '../providers/SettingsProvider'
import { getMySettings, patchMySettings } from '../lib/api'
import { useTranslation } from 'react-i18next'
import LanguageSwitcher from '../components/LanguageSwitcher'

// Хелпер для чтение юзер id
function readUserId(): string | null {
  try {
    const raw = localStorage.getItem('auth')
    if (!raw) return null
    const obj = JSON.parse(raw)
    return obj?.user?.id || obj?.id || null
  } catch { return null }
}

const PRESETS_ACCENT = [
  '#06B6D4','#0EA5E9','#3B82F6','#6366F1',
  '#8B5CF6','#A855F7','#EC4899','#F43F5E',
  '#EF4444','#F97316','#F59E0B','#10B981'
]

export default function Settings({
  theme, toggleTheme,
}: { theme: 'light'|'dark', toggleTheme: () => void }) {
  const { settings, update } = useSettings()
  const defaultRef = useRef<typeof settings | null>(null)
  if (!defaultRef.current) {
    // глубокая копия дефолтов стора при первом монтировании страницы
    defaultRef.current = JSON.parse(JSON.stringify(settings))
  }
  const [hydrating, setHydrating] = useState(true)
  const [userId, setUserId] = useState<string | null>(readUserId())
  const { t } = useTranslation()
  const lastSentRef = useRef<string>('')  // JSON последней отправки

  const setHex = (hex: string) => {
    if (!/^#?[0-9a-fA-F]{6}$/.test(hex)) return
    if (!hex.startsWith('#')) hex = '#' + hex
    update('accentHex', hex)
  }

  const loadFromServer = () => {
    setHydrating(true)
    setUserId(readUserId())
  
    // 1) мгновенно сбрасываем к дефолтам — устраняет «перенос» до прихода ответа
    const d = defaultRef.current!
    update('accentHex', d.accentHex)
    update('motion', d.motion)
    update('glass', !!d.glass)
    update('historyLimit', d.historyLimit)
    update('nsfwHide', !!d.nsfwHide)
    update('notifyOnDone', !!d.notifyOnDone)
    update('soundOnDone', !!d.soundOnDone)
    update('banlist', String(d.banlist))
    update('queue', d.queue)
  
    // 2) подтягиваем сервер и накрываем поверх; отсутствующие ключи оставляем дефолтными
    getMySettings()
      .then((res) => {
        const s = (res?.data as any) || {}
        update('accentHex',    'accentHex'    in s ? s.accentHex : d.accentHex)
        update('motion',       'motion'       in s ? s.motion    : d.motion)
        update('glass',        'glass'        in s ? !!s.glass   : !!d.glass)
        update('historyLimit', 'historyLimit' in s ? s.historyLimit : d.historyLimit)
        update('nsfwHide',     'nsfwHide'     in s ? !!s.nsfwHide : !!d.nsfwHide)
        update('notifyOnDone', 'notifyOnDone' in s ? !!s.notifyOnDone : !!d.notifyOnDone)
        update('soundOnDone',  'soundOnDone'  in s ? !!s.soundOnDone : !!d.soundOnDone)
        update('banlist',      'banlist'      in s ? String(s.banlist) : String(d.banlist))
        update('queue',        'queue'        in s && s.queue ? s.queue : d.queue)
      })
      .catch(() => {})
      .finally(() => { setTimeout(() => setHydrating(false), 0) })
  }  
  
  useEffect(() => {
    loadFromServer()
    const onAuth = () => loadFromServer()
    window.addEventListener('auth:update', onAuth)
    return () => window.removeEventListener('auth:update', onAuth)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])  

  useEffect(() => {
    if (hydrating) return
    const t = setTimeout(() => {
      const payload = {
        accentHex: settings.accentHex,
        motion: settings.motion,
        glass: settings.glass,
        historyLimit: settings.historyLimit,
        nsfwHide: settings.nsfwHide,
        notifyOnDone: settings.notifyOnDone,
        soundOnDone: settings.soundOnDone,
        banlist: settings.banlist,
        queue: settings.queue,
      }
      const snap = JSON.stringify(payload)
      if (snap !== lastSentRef.current) {
        lastSentRef.current = snap
        patchMySettings(payload).catch(()=>{})
      }
    }, 400)
    return () => clearTimeout(t)
  }, [settings, hydrating])
 

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="container py-4 space-y-6"
    >
      {/* Тема + акцент */}
      <Card glass={true}>
        <CardHeader><CardTitle>{t('settings:theme.title')}</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label className="text-foreground">{t('settings:theme.dark.label')}</Label>
              <div className="text-sm text-muted-foreground">{t('settings:theme.dark.desc')}</div>
            </div>
            <Switch checked={theme === 'dark'} onCheckedChange={toggleTheme} />
          </div>

          <div className="space-y-2">
            <Label>{t('settings:accent.title')}</Label>
            <div className="flex flex-wrap items-center gap-2">
              {PRESETS_ACCENT.map((c) => (
                <button
                  key={c}
                  className="h-8 w-8 rounded-md border"
                  style={{ background: c }}
                  onClick={()=>update('accentHex', c)}
                />
              ))}
              <div className="flex items-center gap-2">
                <Input className="w-36" value={settings.accentHex} onChange={e=>setHex(e.target.value)} placeholder="#06B6D4" />
                <input
                  type="color"
                  value={settings.accentHex}
                  onChange={(e)=>update('accentHex', e.target.value)}
                  className="h-10 w-10 rounded-md border p-1"
                />
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label>{t('settings:motion.title')}</Label>
              <div className="text-sm text-muted-foreground">{t('settings:motion.desc')}</div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant={settings.motion===0?'default':'outline'} onClick={()=>update('motion',0)}>0</Button>
              <Button variant={settings.motion===1?'default':'outline'} onClick={()=>update('motion',1)}>1</Button>
              <Button variant={settings.motion===2?'default':'outline'} onClick={()=>update('motion',2)}>2</Button>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label>{t('settings:glass.title')}</Label>
              <div className="text-sm text-muted-foreground">{t('settings:glass.desc')}</div>
            </div>
            <Switch checked={settings.glass} onCheckedChange={(v)=>update('glass', !!v)} />
          </div>
        </CardContent>
      </Card>

      {/* Очередь + история + NSFW */}
      <Card glass={true}>
        <CardHeader><CardTitle>{t('settings:queueHistory.title')}</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label>{t('settings:queue.cancel.label')}</Label>
              <div className="text-sm text-muted-foreground">{t('settings:queue.cancel.desc')}</div>
            </div>
            <Switch
              checked={settings.queue.cancelPrevious}
              onCheckedChange={(v)=>update('queue', { ...settings.queue, cancelPrevious: !!v })}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label>{t('settings:history.limit.label')}</Label>
              <div className="text-sm text-muted-foreground">{t('settings:history.limit.desc')}</div>
            </div>
            <select
              className="rounded-md border bg-background p-2 text-sm"
              value={settings.historyLimit}
              onChange={(e)=>update('historyLimit', Number(e.target.value) as any)}
            >
              <option value={50}>50</option><option value={100}>100</option><option value={500}>500</option>
            </select>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label>{t('settings:nsfw.show.label')}</Label>
              <div className="text-sm text-muted-foreground">{t('settings:nsfw.show.desc')}</div>
            </div>
            <Switch checked={!settings.nsfwHide} onCheckedChange={(v)=>update('nsfwHide', !v)} />
          </div>
        </CardContent>
      </Card>

      {/* Уведомления */}
      <Card glass={true}>
        <CardHeader><CardTitle>{t('settings:notifications.title')}</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label>{t('settings:notifications.desktop.label')}</Label>
              <div className="text-sm text-muted-foreground">{t('settings:notifications.desktop.desc')}</div>
            </div>
            <Switch checked={settings.notifyOnDone} onCheckedChange={(v)=>update('notifyOnDone', !!v)} />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label>{t('settings:notifications.sound.label')}</Label>
              <div className="text-sm text-muted-foreground">{t('settings:notifications.sound.desc')}</div>
            </div>
            <Switch checked={settings.soundOnDone} onCheckedChange={(v)=>update('soundOnDone', !!v)} />
          </div>
        </CardContent>
      </Card>
 
      <Card glass={true}>
        <CardHeader><CardTitle>{t('settings:language.cardTitle')}</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label>{t('language.title')}</Label>
              <div className="text-sm text-muted-foreground">RU / EN</div>
            </div>
            <LanguageSwitcher />
          </div>
        </CardContent>
      </Card>

      {/* Бан-лист */}
      <Card glass={true}>
        <CardHeader><CardTitle>{t('settings:banlist.title')}</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          <div className="text-sm text-muted-foreground">
            {t('settings:banlist.hint')}
          </div>
          <textarea
            className="min-h-[120px] w-full rounded-md border bg-background p-2 text-sm"
            value={settings.banlist}
            onChange={e=>update('banlist', e.target.value)}
          />
        </CardContent>
      </Card>
    </motion.div>
  )
}
