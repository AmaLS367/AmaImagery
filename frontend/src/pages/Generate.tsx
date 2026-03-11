import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Textarea } from '../components/ui/textarea'
import { type GeneratePayload } from '../lib/api'
import { loadForm, saveForm } from '../lib/storage'
import { ImageUp, Loader2, RotateCcw } from 'lucide-react'
import { cn } from '../lib/utils'
import { useSettings } from '../providers/SettingsProvider'
import { useJobs } from '../providers/JobProvider'
import { useTranslation } from 'react-i18next'
import { normalizeError } from '../lib/errors'

type Corr = [string, string]
type AnyResult = Record<string, unknown>;
const ACTIVE_KEY = 'amaimagery.activeJobId'

export default function Generate() {
  const { settings } = useSettings()
  const { t } = useTranslation()
  const { start, get } = useJobs()

  const [prompt, setPrompt] = useState(loadForm()?.prompt ?? '')
  const [neg, setNeg] = useState(loadForm()?.neg ?? '')
  const [steps, setSteps] = useState(loadForm()?.steps ?? 28)
  const [guidance, setGuidance] = useState(loadForm()?.guidance ?? 7)
  const [width, setWidth] = useState(loadForm()?.width ?? 896)
  const [height, setHeight] = useState(loadForm()?.height ?? 1152)
  const [seed, setSeed] = useState<number | null>(loadForm()?.seed ?? null)
  const [ipScale, setIpScale] = useState(loadForm()?.ipScale ?? 0.6)
  const [style, setStyle] = useState<'realistic'|'anime'>(loadForm()?.style ?? 'anime')

  const [error, setError] = useState<string | null>(null)
  const [imgUrl, setImgUrl] = useState<string | null>(null)
  const [hash, setHash] = useState<string | null>(null)
  const [corr, setCorr] = useState<Corr[] | null>(null)
  const [refPreview, setRefPreview] = useState<string | null>(null)
  const refBase64 = useRef<string | null>(null)

  const [activeId, setActiveId] = useState<string | null>(() => {
    try { return localStorage.getItem(ACTIVE_KEY) } catch { return null }
  })
  const activeJob = get(activeId || null)
  const busy = !!activeJob && (activeJob.status === 'running' || activeJob.status === 'queued')


  useEffect(() => {
    saveForm({ prompt, neg, steps, guidance, width, height, seed, ipScale, style })
  }, [prompt, neg, steps, guidance, width, height, seed, ipScale, style])

  function asCorrArray(x: unknown): Corr[] | null {
    if (Array.isArray(x)) return x as Corr[];
    if (x && typeof x === "object" && Array.isArray((x as any).items)) {
      return (x as any).items as Corr[];
    }
    return null;
  }
  
  useEffect(() => {
    if (!activeJob) return;
  
    if (activeJob.status === 'done' && activeJob.result) {
      const res = activeJob.result;
      
      console.log('Job completed, result:', res);
  
      // Используем image_url если доступен (уже содержит полный путь с подписью)
      if (res.image_url) {
        console.log('Using image_url:', res.image_url);
        setImgUrl(res.image_url);
      } else if (res.image_filename && res.exp && res.sig) {
        // Строим URL с подписью если есть все необходимые данные
        const name = res.image_filename;
        const url = `/api/v1/file?path=${encodeURIComponent(name)}&exp=${String(res.exp)}&sig=${encodeURIComponent(res.sig)}`;
        console.log('Built signed URL:', url);
        setImgUrl(url);
      } else if (res.image_filename) {
        // Fallback без подписи (может не работать, но попробуем)
        const name = res.image_filename;
        const base = `/api/v1/file?path=${encodeURIComponent(name)}`;
        console.warn('Using URL without signature:', base);
        setImgUrl(base);
      } else if (res.image_path) {
        // Последний fallback - извлекаем имя файла из пути
        const raw = String(res.image_path);
        const name = raw.split(/[\\/]/).pop() || raw;
        const base = `/api/v1/file?path=${encodeURIComponent(name)}`;
        console.warn('Using image_path fallback:', base);
        setImgUrl(base);
      } else {
        console.error('No image data available in result:', res);
        setError('Изображение не найдено в ответе сервера');
      }
  
      // prompt_hash и corrections больше не возвращаются в новом API
      setHash(null);
      setCorr(null);
  
      try { localStorage.removeItem(ACTIVE_KEY) } catch {}
      setActiveId(null);
    }
  
    if (activeJob.status === 'error') {
      setError(activeJob.error || 'Ошибка сервера');
      try { localStorage.removeItem(ACTIVE_KEY) } catch {}
      setActiveId(null);
    }
  }, [activeJob?.status, activeJob?.result, activeJob?.error]);
  
  
  function goGuide() {
    window.dispatchEvent(new CustomEvent('goto-tab', { detail: 'guide' }))
  }

  async function onFilePicked(file: File) {
    if (!file.type.startsWith('image/')) { setError(t('errors.unsupported_media')); return }
    if (file.size > 8 * 1024 * 1024) { setError(t('errors.payload_too_large')); return }
    setError(null); setRefPreview(URL.createObjectURL(file)); refBase64.current = await fileToBase64(file)
  }
  function onDrop(e: React.DragEvent) { e.preventDefault(); const f = e.dataTransfer.files?.[0]; if (f) onFilePicked(f) }

  async function gen() {
    if (!prompt || prompt.trim().length < 3) { setError(t('errors.validation')); return }
    setError(null)

    const ban = (settings.banlist || '').split(/,|\n/).map(s=>s.trim()).filter(Boolean)
    const finalNeg = [neg, ...ban].filter(Boolean).join(', ')

    const payload: GeneratePayload = {
      prompt: prompt.trim(),
      negative_prompt: finalNeg || null,
      steps, guidance_scale: guidance,
      width, height, seed: seed ?? null,
      ref_image_b64: refBase64.current,
      ip_scale: ipScale,
      style,
    }

    const id = start(payload)
    try { localStorage.setItem(ACTIVE_KEY, id) } catch {}
    setActiveId(id)
  }

  const seedRandom = () => setSeed(Math.floor(Math.random() * 2_147_483_647))

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }} transition={{ duration: 0.35, ease: 'easeOut' }} className="container grid grid-cols-1 gap-4 py-4 lg:grid-cols-[420px_1fr]">
      <div className="space-y-4">
        <Card glass={settings.glass}>
          <CardHeader><CardTitle>{t('generate:title')}</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="prompt">{t('generate:prompt')}</Label>
                <Button variant="ghost" size="sm" onClick={goGuide}>{t('actions.guide')}</Button>
              </div>
              <Textarea id="prompt" value={prompt} onChange={e=>setPrompt(e.target.value)} placeholder="anime art, ..." />
            </div>

            <div className="space-y-2">
              <Label htmlFor="neg">{t('generate:neg')}</Label>
              <Textarea id="neg" value={neg} onChange={e=>setNeg(e.target.value)} placeholder="low quality, ..." />
            </div>

            <div className="space-y-2">
              <Label>{t('generate:style')}</Label>
              <div className="flex gap-2">
                <Button type="button"
                  variant={style==='realistic' ? 'default' : 'outline'}
                  onClick={()=>setStyle('realistic')}
                >{t('generate:style_real')}</Button>
                <Button type="button"
                  variant={style==='anime' ? 'default' : 'outline'}
                  onClick={()=>setStyle('anime')}
                >{t('generate:style_anime')}</Button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2"><Label htmlFor="steps">{t('generate:steps')}</Label><Input id="steps" type="number" min={1} max={200} value={steps} onChange={e=>setSteps(Number(e.target.value))} /></div>
              <div className="space-y-2"><Label htmlFor="guidance">CFG</Label><Input id="guidance" type="number" step={0.5} min={0} max={30} value={guidance} onChange={e=>setGuidance(Number(e.target.value))} /></div>
              <div className="space-y-2"><Label htmlFor="width">{t('generate:width')}</Label><Input id="width" type="number" min={256} step={64} value={width} onChange={e=>setWidth(Number(e.target.value))} /></div>
              <div className="space-y-2"><Label htmlFor="height">{t('generate:height')}</Label><Input id="height" type="number" min={256} step={64} value={height} onChange={e=>setHeight(Number(e.target.value))} /></div>
              <div className="space-y-2">
                <Label htmlFor="seed">{t('generate:seed')}</Label>
                <Input 
                  id="seed" 
                  type="number" 
                  value={seed ?? ''} 
                  onChange={e=>setSeed(e.target.value === '' ? null : Number(e.target.value))} placeholder={t('generate:seed')}
                />
              </div>
              <div className="self-end">
                <Button variant="secondary" className="h-10" onClick={seedRandom} aria-label={t('generate:seed_random')}>
                  {t('generate:seed_random')}
                </Button>
                </div>
            </div>

            <div className="space-y-2">
              <Label>{t('generate:ref')}</Label>
              <div onDrop={onDrop} onDragOver={(e)=>e.preventDefault()} className={cn('rounded-lg border border-dashed p-4 text-sm text-muted-foreground', refPreview ? 'bg-muted/50' : 'bg-muted/20')}>
                <div className="flex items-center gap-2">
                  <input id="ref" type="file" accept="image/*" className="hidden" onChange={async (e)=>{ const f = e.target.files?.[0]; if (f) onFilePicked(f) }}/>
                  <Button variant="outline" onClick={()=>document.getElementById('ref')?.click()}><ImageUp className="mr-2 h-4 w-4"/>{t('generate:ref_ex')}</Button>
                  <div>{t('generate:ref_drop')}</div>
                </div>
                {refPreview && <div className="mt-3"><img src={refPreview} alt="" className="max-h-64 rounded-md border"/></div>}
              </div>
            </div>

            <div className="grid grid-cols-[1fr_auto] items-center gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="ipScale">IP Scale: <b>{ipScale.toFixed(2)}</b></Label>
                <input id="ipScale" type="range" min={0} max={1.5} step={0.05} value={ipScale} onChange={(e)=>setIpScale(Number(e.target.value))} className="w-full accent-primary"/>
              </div>
              <Button variant="ghost" onClick={()=>setIpScale(0.6)}><RotateCcw className="h-4 w-4 mr-2"/>{t('actions.reset')}</Button>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <Button onClick={gen} disabled={busy} className="min-w-[160px]">
                {busy ? <><Loader2 className="mr-2 h-4 w-4 animate-spin"/>{t('generate:waiting')}</> : t('actions.generate')}
              </Button>
            </div>

            {error && <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        <Card glass={settings.glass}>
          <CardHeader><CardTitle>{t('generate:result')}</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="relative flex min-h-[340px] items-center justify-center overflow-hidden rounded-lg border bg-muted/20">
              {imgUrl ? <img src={imgUrl} alt={t('generate:result')} className="max-h-[560px] w-full object-contain" /> : <div className="text-sm text-muted-foreground">{t('generate:waiting')}</div>}
              {busy && <div className="absolute inset-0 grid place-items-center bg-background/60 backdrop-blur"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>}
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <a className={cn('underline underline-offset-4', imgUrl ? 'opacity-100' : 'opacity-50 pointer-events-none')} href={imgUrl ?? '#'} target="_blank" rel="noreferrer">{t('actions.open')}</a>
              <a className={cn('underline underline-offset-4', imgUrl ? 'opacity-100' : 'opacity-50 pointer-events-none')} href={imgUrl ?? '#'} download>{t('actions.download')}</a>
              {hash && <span className="ml-auto text-xs">hash: {hash}</span>}
            </div>
            {corr?.length ? (
              <div>
                <div className="mb-1 text-sm text-muted-foreground">{t('generate:fixes')}:
                </div>
                <div className="overflow-hidden rounded-md border">
                  <table className="w-full text-sm">
                    <tbody>{corr.map(([a,b], i)=>(<tr key={i} className="border-t first:border-t-0"><td className="p-2 text-red-500">{a}</td><td className="p-2 text-emerald-600">{b}</td></tr>))}</tbody>
                  </table>
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </motion.div>
  )
}

async function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const res = String(reader.result || '')
      const idx = res.indexOf(',')
      resolve(idx >= 0 ? res.slice(idx + 1) : res)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}
