import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowUpRight,
  CheckCircle2,
  Clock3,
  Download,
  ImageUp,
  Loader2,
  RefreshCw,
  RotateCcw,
  Sparkles,
  TriangleAlert,
  Settings2,
  Zap,
  Maximize2,
  Trash2,
  Layers
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'

import { Button } from '../components/ui/button'
import { MetaPill, SurfacePanel } from '../components/ui/foundation'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Textarea } from '../components/ui/textarea'
import { appRoutes } from '../lib/routes'
import { toAssetUrl, type GeneratePayload, type TaskStatusResp } from '../lib/api'
import { loadForm, saveForm } from '../lib/storage'
import { cn } from '../lib/utils'
import { useSettings } from '../providers/SettingsProvider'
import { useJobs } from '../providers/JobProvider'

const ACTIVE_KEY = 'amaimagery.activeJobId'

const styleOptions = [
  { value: 'realistic', labelKey: 'generate:style_options.realistic' },
  { value: 'anime', labelKey: 'generate:style_options.anime' },
] as const

function buildGeneratedImageUrl(result: TaskStatusResp): string | null {
  if (result.image_url) {
    return toAssetUrl(result.image_url)
  }

  const filename = result.image_filename || String(result.image_path || '').split(/[\\/]/).pop() || ''
  if (!filename) {
    return null
  }

  const query = new URLSearchParams({ path: filename })
  if (typeof result.exp === 'number') {
    query.set('exp', String(result.exp))
  }
  if (typeof result.sig === 'string' && result.sig.length > 0) {
    query.set('sig', result.sig)
  }

  return toAssetUrl(`/api/v1/file?${query.toString()}`)
}

export default function Generate() {
  const { t } = useTranslation(['generate', 'common'])
  const { settings } = useSettings()
  const { jobs, start, cancel, get } = useJobs()

  const [prompt, setPrompt] = useState(loadForm()?.prompt ?? '')
  const [neg, setNeg] = useState(loadForm()?.neg ?? '')
  const [steps, setSteps] = useState(loadForm()?.steps ?? 28)
  const [guidance, setGuidance] = useState(loadForm()?.guidance ?? 7.5)
  const [width, setWidth] = useState(loadForm()?.width ?? 896)
  const [height, setHeight] = useState(loadForm()?.height ?? 1152)
  const [seed, setSeed] = useState<number | null>(loadForm()?.seed ?? null)
  const [ipScale, setIpScale] = useState(loadForm()?.ipScale ?? 0.65)
  const [style, setStyle] = useState<'realistic' | 'anime'>(loadForm()?.style ?? 'realistic')

  const [error, setError] = useState<string | null>(null)
  const [imgUrl, setImgUrl] = useState<string | null>(null)
  const [refPreview, setRefPreview] = useState<string | null>(null)

  const refBase64 = useRef<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const [activeId, setActiveId] = useState<string | null>(() => {
    try {
      return localStorage.getItem(ACTIVE_KEY)
    } catch {
      return null
    }
  })

  const activeJob = get(activeId || null)
  const orderedRuntimeJobs = [...jobs]
    .filter((job) => job.status === 'queued' || job.status === 'running')
    .sort((left, right) => left.startedAt - right.startedAt)

  const queuePosition = activeId ? orderedRuntimeJobs.findIndex((job) => job.id === activeId) + 1 : 0
  const busy = activeJob?.status === 'running' || activeJob?.status === 'queued'
  const stage = busy ? activeJob.status : error ? 'error' : imgUrl ? 'completed' : 'idle'
  const styleLabel = t(styleOptions.find((option) => option.value === style)?.labelKey ?? 'generate:style_options.realistic')

  useEffect(() => {
    saveForm({ prompt, neg, steps, guidance, width, height, seed, ipScale, style })
  }, [prompt, neg, steps, guidance, width, height, seed, ipScale, style])

  useEffect(() => {
    if (!activeJob) return

    if (activeJob.status === 'completed' && activeJob.result) {
      const result = activeJob.result
      const nextImgUrl = buildGeneratedImageUrl(result)

      if (nextImgUrl) {
        setImgUrl(nextImgUrl)
      } else {
        setError(t('generate:errors.no_artifact'))
      }

      try {
        localStorage.removeItem(ACTIVE_KEY)
      } catch {
        // ignore storage failures
      }
      setActiveId(null)
    }

    if (activeJob.status === 'error') {
      setError(activeJob.error || t('generate:status.error.title'))
      try {
        localStorage.removeItem(ACTIVE_KEY)
      } catch {
        // ignore storage failures
      }
      setActiveId(null)
    }
  }, [activeJob, t])

  async function onFilePicked(file: File) {
    if (!file.type.startsWith('image/')) {
      setError(t('generate:ref.error_type'))
      return
    }
    if (file.size > 8 * 1024 * 1024) {
      setError(t('generate:ref.error_size'))
      return
    }
    setError(null)
    setRefPreview(URL.createObjectURL(file))
    refBase64.current = await fileToBase64(file)
  }

  function onDrop(event: React.DragEvent) {
    event.preventDefault()
    const file = event.dataTransfer.files?.[0]
    if (file) onFilePicked(file)
  }

  async function runGeneration() {
    if (!prompt || prompt.trim().length < 3) {
      setError(t('generate:errors.prompt_short'))
      return
    }

    setError(null)

    const banlist = (settings.banlist || '')
      .split(/,|\n/)
      .map((item) => item.trim())
      .filter(Boolean)

    const payload: GeneratePayload = {
      prompt: prompt.trim(),
      negative_prompt: [neg, ...banlist].filter(Boolean).join(', ') || null,
      steps,
      guidance_scale: guidance,
      width,
      height,
      seed: seed ?? null,
      ref_image_b64: refBase64.current,
      ip_scale: ipScale,
      style,
    }

    const id = start(payload)
    try {
      localStorage.setItem(ACTIVE_KEY, id)
    } catch {
      // ignore storage failures
    }
    setActiveId(id)
  }

  function seedRandom() {
    setSeed(Math.floor(Math.random() * 2_147_483_647))
  }

  function retryCurrentSettings() {
    setError(null)
    runGeneration()
  }

  return (
    <section className="page-shell py-12 xl:py-20 space-y-10">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
         <div className="space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
              <Sparkles className="h-3 w-3" />
              Creation Studio
            </div>
            <h1 className="font-display text-4xl font-bold tracking-tight text-foreground dark:text-white sm:text-6xl leading-tight">
              {t('generate:title')}
            </h1>
         </div>
         <div className="flex gap-3">
            <Button asChild variant="outline" className="rounded-full font-bold border-border">
              <Link to={appRoutes.promptGuide}>
                <Layers className="mr-2 h-4 w-4" />
                {t('common:actions.guide')}
              </Link>
            </Button>
            <Button asChild variant="outline" className="rounded-full font-bold border-border">
              <Link to={appRoutes.history}>
                <Clock3 className="mr-2 h-4 w-4" />
                Archive
              </Link>
            </Button>
         </div>
      </div>

      <div className="grid gap-12 xl:grid-cols-[1fr_420px] items-start">
        <div className="space-y-10">
          <SurfacePanel className="p-10 space-y-10">
            <div className="space-y-6">
              <Label htmlFor="prompt" className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">{t('generate:prompt')}</Label>
              <Textarea
                id="prompt"
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                placeholder={t('generate:prompt_placeholder')}
                className="min-h-[160px] resize-none text-xl font-medium border-border bg-secondary/30 dark:bg-white/5 dark:border-white/10 rounded-[32px] p-8 focus:border-primary/50 transition-all placeholder:text-foreground/20 dark:placeholder:text-white/10"
              />
            </div>

            <div className="space-y-6">
              <Label htmlFor="neg" className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">{t('generate:neg')}</Label>
              <Textarea
                id="neg"
                value={neg}
                onChange={(event) => setNeg(event.target.value)}
                placeholder={t('generate:neg_placeholder')}
                className="min-h-[100px] resize-none text-base border-border bg-secondary/30 dark:bg-white/5 dark:border-white/10 rounded-[24px] p-6 focus:border-primary/50 transition-all placeholder:text-foreground/20 dark:placeholder:text-white/10"
              />
            </div>

            <div className="grid gap-10 sm:grid-cols-2 pt-4">
              <div className="space-y-6">
                <Label className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">{t('generate:style')}</Label>
                <div className="flex gap-3">
                  {styleOptions.map((option) => (
                    <Button
                      key={option.value}
                      type="button"
                      variant={style === option.value ? 'default' : 'outline'}
                      className={cn(
                        "flex-1 h-12 rounded-xl font-bold border-border transition-all",
                        style === option.value && "shadow-glow"
                      )}
                      onClick={() => setStyle(option.value)}
                    >
                      {t(option.labelKey)}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="space-y-6">
                 <Label className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">{t('generate:ref.title')}</Label>
                 <div
                  onDrop={onDrop}
                  onDragOver={(event) => event.preventDefault()}
                  className={cn(
                    'relative overflow-hidden rounded-[24px] border-2 border-dashed border-border/60 transition-all hover:border-primary/40 bg-secondary/30 dark:bg-white/5 dark:border-white/10',
                    refPreview ? 'aspect-video border-solid border-primary/20 bg-primary/5' : 'p-4 min-h-[100px] flex items-center justify-center'
                  )}
                >
                  {refPreview ? (
                    <>
                      <img src={refPreview} alt="Reference preview" className="h-full w-full object-cover" />
                      <div className="absolute inset-0 bg-black/60 opacity-0 transition-opacity hover:opacity-100 flex items-center justify-center gap-2">
                         <Button variant="secondary" size="sm" className="rounded-full font-bold" onClick={() => fileInputRef.current?.click()}>
                          Replace
                        </Button>
                        <Button variant="secondary" size="icon" className="h-8 w-8 rounded-full border border-danger/20 bg-danger/10 text-danger hover:bg-danger/15" onClick={() => { setRefPreview(null); refBase64.current = null; }}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </>
                  ) : (
                    <div className="flex flex-col items-center justify-center gap-3 text-center">
                      <ImageUp className="h-6 w-6 text-foreground/20 dark:text-white/20" />
                      <div className="space-y-1">
                         <p className="text-[10px] font-bold uppercase tracking-widest text-foreground/40 dark:text-white/40">{t('generate:ref.drop')}</p>
                         <button className="text-xs font-bold text-primary hover:underline" onClick={() => fileInputRef.current?.click()}>
                            {t('generate:ref.button')}
                         </button>
                      </div>
                    </div>
                  )}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={async (event) => {
                      const file = event.target.files?.[0]
                      if (file) await onFilePicked(file)
                    }}
                  />
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-6 border-t border-border pt-10 dark:border-white/10">
              <Button 
                onClick={runGeneration} 
                disabled={busy} 
                size="lg" 
                className="h-16 px-12 text-lg font-bold rounded-full shadow-glow-lg group"
              >
                {busy ? (
                  <>
                    <Loader2 className="mr-3 h-6 w-6 animate-spin" />
                    {t('generate:actions.working')}
                  </>
                ) : (
                  <>
                    <Zap className="mr-3 h-6 w-6 fill-current" />
                    {t('generate:actions.generate')}
                  </>
                )}
              </Button>
              {busy && activeId ? (
                <Button variant="outline" size="lg" className="h-16 px-10 rounded-full font-bold border-border" onClick={() => cancel(activeId)}>
                  {t('generate:actions.cancel')}
                </Button>
              ) : null}
            </div>
          </SurfacePanel>

          <SurfacePanel className="overflow-hidden p-0">
            <div className="border-b border-border p-8 flex items-center justify-between dark:border-white/10">
              <div className="flex items-center gap-3">
                 <div className="h-8 w-8 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                    <Monitor className="h-4 w-4" />
                 </div>
                 <h2 className="font-display text-2xl font-bold tracking-tight text-foreground dark:text-white">{t('generate:result.title')}</h2>
              </div>
              <AnimatePresence mode="wait">
                <motion.div
                  key={stage}
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                >
                  <MetaPill className={cn(
                    "font-bold",
                    stage === 'completed' ? 'border-success/20 bg-success/5 text-success' : 
                    stage === 'error' ? 'border-danger/20 bg-danger/5 text-danger' : 
                    busy ? 'border-primary/20 bg-primary/5 text-primary' : ''
                  )}>
                     {t(`generate:result.status.${stage}`)}
                  </MetaPill>
                </motion.div>
              </AnimatePresence>
            </div>
            
            <div className="p-10">
              <div className="relative aspect-square sm:aspect-[16/10] w-full overflow-hidden rounded-[40px] border border-border bg-secondary shadow-inner dark:bg-black/20 dark:border-white/5">
                <AnimatePresence mode="wait">
                  {imgUrl ? (
                    <motion.img 
                      key={imgUrl}
                      initial={{ opacity: 0, scale: 1.05 }}
                      animate={{ opacity: 1, scale: 1 }}
                      src={imgUrl} 
                      alt="Generated result" 
                      className="h-full w-full object-contain" 
                    />
                  ) : (
                    <motion.div 
                      key="placeholder"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="relative flex h-full items-center justify-center p-8 text-center"
                    >
                      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(13,148,255,0.12),transparent_40%),radial-gradient(circle_at_bottom_right,rgba(52,211,153,0.08),transparent_40%)]" />
                      <div className="relative space-y-6">
                        <div className="mx-auto w-24 h-24 rounded-[32px] bg-secondary/50 flex items-center justify-center dark:bg-white/5 shadow-sm">
                           <Sparkles className="h-10 w-10 text-primary/40" />
                        </div>
                        <div className="space-y-2">
                          <div className="font-display text-3xl font-bold tracking-tight text-foreground/80 dark:text-white/80">
                            {t('generate:result.ready_title')}
                          </div>
                          <p className="mx-auto max-w-sm text-base leading-relaxed text-foreground/40 dark:text-white/40 font-medium">
                            {t('generate:result.ready_desc')}
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {busy ? (
                  <div className="absolute inset-0 flex items-center justify-center bg-background/40 backdrop-blur-3xl dark:bg-black/40">
                    <div className="flex flex-col items-center gap-6 rounded-[48px] border border-white/10 bg-white/5 p-12 text-white shadow-[0_32px_128px_-16px_rgba(0,0,0,0.5)] dark:bg-white/5">
                      <div className="relative h-20 w-24">
                        <div className="absolute inset-0 flex justify-center gap-1.5 items-end h-full">
                           {[0, 1, 2, 3].map(i => (
                             <motion.div 
                                key={i}
                                animate={{ height: ['20%', '100%', '20%'] }}
                                transition={{ duration: 1, repeat: Infinity, delay: i * 0.1 }}
                                className="w-3 rounded-full bg-primary shadow-glow"
                             />
                           ))}
                        </div>
                      </div>
                      <div className="space-y-2 text-center">
                        <div className="text-2xl font-black uppercase tracking-tighter">{t(`generate:result.status.${stage}`)}</div>
                        <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/40">
                          {t(`generate:result.stage.${stage}`)}
                        </div>
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>

              {imgUrl && (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex flex-wrap gap-4 mt-8"
                >
                  <Button asChild size="lg" variant="secondary" className="h-14 px-8 rounded-full font-bold shadow-sm">
                    <a href={imgUrl} target="_blank" rel="noreferrer">
                      <Maximize2 className="mr-2 h-5 w-5" />
                      {t('generate:actions.open')}
                    </a>
                  </Button>
                  <Button asChild size="lg" variant="outline" className="h-14 px-8 rounded-full font-bold border-border">
                    <a href={imgUrl} download>
                      <Download className="mr-2 h-5 w-5" />
                      {t('generate:actions.download')}
                    </a>
                  </Button>
                  <Button asChild size="lg" variant="ghost" className="h-14 px-8 rounded-full font-bold ml-auto text-foreground/60">
                    <Link to={appRoutes.history}>
                      <Clock3 className="mr-2 h-5 w-5" />
                      {t('generate:actions.history')}
                    </Link>
                  </Button>
                </motion.div>
              )}
            </div>
          </SurfacePanel>
        </div>

        {/* Sidebar */}
        <aside className="space-y-8 sticky top-24">
           <SurfacePanel className="p-8 space-y-10">
            <div className="flex items-center gap-3">
               <Settings2 className="h-5 w-5 text-primary" />
               <h3 className="font-display text-xl font-bold text-foreground dark:text-white">{t('generate:advanced.title')}</h3>
            </div>

            <div className="space-y-8">
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                   <Label htmlFor="steps" className="text-[10px] font-black uppercase tracking-[0.2em] text-foreground/40 dark:text-white/40">{t('generate:advanced.steps')}</Label>
                   <span className="text-xs font-bold text-primary">{steps}</span>
                </div>
                <Input 
                  id="steps" 
                  type="number" 
                  min={1} 
                  max={200} 
                  value={steps} 
                  onChange={(event) => setSteps(Number(event.target.value))} 
                  className="h-12 rounded-xl border-border bg-secondary/50 font-bold"
                />
              </div>

              <div className="space-y-4">
                <div className="flex justify-between items-center">
                   <Label htmlFor="guidance" className="text-[10px] font-black uppercase tracking-[0.2em] text-foreground/40 dark:text-white/40">{t('generate:advanced.cfg')}</Label>
                   <span className="text-xs font-bold text-primary">{guidance.toFixed(1)}</span>
                </div>
                <Input
                  id="guidance"
                  type="number"
                  min={0}
                  max={30}
                  step={0.5}
                  value={guidance}
                  onChange={(event) => setGuidance(Number(event.target.value))}
                  className="h-12 rounded-xl border-border bg-secondary/50 font-bold"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-4">
                  <Label htmlFor="width" className="text-[10px] font-black uppercase tracking-[0.2em] text-foreground/40 dark:text-white/40">{t('generate:advanced.width')}</Label>
                  <Input id="width" type="number" min={256} step={64} value={width} onChange={(event) => setWidth(Number(event.target.value))} className="h-12 rounded-xl border-border bg-secondary/50 font-bold" />
                </div>
                <div className="space-y-4">
                  <Label htmlFor="height" className="text-[10px] font-black uppercase tracking-[0.2em] text-foreground/40 dark:text-white/40">{t('generate:advanced.height')}</Label>
                  <Input id="height" type="number" min={256} step={64} value={height} onChange={(event) => setHeight(Number(event.target.value))} className="h-12 rounded-xl border-border bg-secondary/50 font-bold" />
                </div>
              </div>

              <div className="space-y-4">
                <Label htmlFor="seed" className="text-[10px] font-black uppercase tracking-[0.2em] text-foreground/40 dark:text-white/40">{t('generate:advanced.seed')}</Label>
                <div className="flex gap-2">
                  <Input
                    id="seed"
                    type="number"
                    value={seed ?? ''}
                    onChange={(event) => setSeed(event.target.value === '' ? null : Number(event.target.value))}
                    placeholder={t('generate:advanced.seed_auto')}
                    className="h-12 rounded-xl border-border bg-secondary/50 font-bold flex-1"
                  />
                  <Button variant="secondary" size="icon" className="h-12 w-12 rounded-xl" onClick={seedRandom} title={t('generate:advanced.seed_random')}>
                    <RotateCcw className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <div className="space-y-6 pt-4 border-t border-border dark:border-white/5">
                <div className="flex items-center justify-between">
                  <Label htmlFor="ipScale" className="text-[10px] font-black uppercase tracking-[0.2em] text-foreground/40 dark:text-white/40">{t('generate:advanced.ip_scale')}</Label>
                  <span className="text-xs font-bold text-primary">{ipScale.toFixed(2)}</span>
                </div>
                <input
                  id="ipScale"
                  type="range"
                  min={0}
                  max={1.5}
                  step={0.05}
                  value={ipScale}
                  onChange={(event) => setIpScale(Number(event.target.value))}
                  className="w-full h-1.5 bg-secondary dark:bg-white/10 rounded-full appearance-none cursor-pointer accent-primary"
                />
              </div>
            </div>

            <Button variant="ghost" size="sm" className="w-full h-10 rounded-full text-[10px] font-black uppercase tracking-widest text-foreground/40 hover:text-foreground" onClick={() => {
              setSteps(28); setGuidance(7.5); setWidth(896); setHeight(1152); setSeed(null); setIpScale(0.65);
            }}>
              <RotateCcw className="mr-2 h-3.5 w-3.5" />
              {t('generate:advanced.reset')}
            </Button>
          </SurfacePanel>

          <AnimatePresence mode="wait">
            {busy && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
              >
                <SurfacePanel className="p-8 space-y-6 border-primary/20 bg-primary/5">
                  <div className="flex items-center gap-3 text-primary">
                    <div className="rounded-full bg-primary/10 p-2">
                      <Clock3 className="h-5 w-5" />
                    </div>
                    <h3 className="font-display text-xl font-bold tracking-tight">
                      {stage === 'queued' 
                        ? t('generate:status.queued.title', { position: queuePosition || 1 })
                        : t('generate:status.running.title')}
                    </h3>
                  </div>
                  <div className="space-y-4">
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-primary/10">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: stage === 'queued' ? '15%' : '70%' }}
                        className="h-full bg-primary shadow-glow" 
                      />
                    </div>
                    <p className="text-sm leading-relaxed text-foreground/60 dark:text-white/60 font-medium">
                      {stage === 'queued' ? t('generate:status.queued.desc1') : t('generate:status.running.desc')}
                    </p>
                  </div>
                </SurfacePanel>
              </motion.div>
            )}
          </AnimatePresence>

          {error && (
            <SurfacePanel className="p-8 border-danger/20 bg-danger/5 space-y-6">
              <div className="flex items-center gap-3 text-danger">
                <div className="rounded-full bg-danger/10 p-2">
                  <TriangleAlert className="h-5 w-5" />
                </div>
                <h3 className="font-display text-xl font-bold tracking-tight">{t('generate:status.error.title')}</h3>
              </div>
              <p className="text-sm leading-relaxed text-danger/80 font-medium">
                {error || t('generate:status.error.desc')}
              </p>
              <div className="flex flex-col gap-2">
                <Button variant="secondary" onClick={retryCurrentSettings} className="w-full rounded-full font-bold">
                  <RefreshCw className="mr-2 h-4 w-4" />
                  {t('generate:actions.retry')}
                </Button>
              </div>
            </SurfacePanel>
          )}

          <SurfacePanel className="p-8 space-y-6">
             <div className="text-[10px] font-black uppercase tracking-[0.2em] text-primary">{t('generate:facts.title')}</div>
             <div className="space-y-4">
                <StatusRow label={t('generate:facts.style')} value={styleLabel} />
                <StatusRow label={t('generate:facts.aspect')} value={`${width}×${height}`} />
                <StatusRow label={t('generate:facts.seed')} value={seed ? String(seed) : t('generate:facts.idle')} />
                <StatusRow label={t('generate:facts.queue')} value={busy ? `${queuePosition || 1} ${t('generate:facts.active')}` : t('generate:facts.idle')} />
             </div>
          </SurfacePanel>
        </aside>
      </div>
    </section>
  )
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-[10px] font-black uppercase tracking-widest border-b border-border pb-3 dark:border-white/5 last:border-0 last:pb-0">
      <span className="text-foreground/40 dark:text-white/40">{label}</span>
      <span className="text-foreground dark:text-white">{value}</span>
    </div>
  )
}

async function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = String(reader.result || '')
      const index = result.indexOf(',')
      resolve(index >= 0 ? result.slice(index + 1) : result)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

function Monitor(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect width="20" height="14" x="2" y="3" rx="2" />
      <line x1="8" x2="16" y1="21" y2="21" />
      <line x1="12" x2="12" y1="17" y2="21" />
    </svg>
  )
}
