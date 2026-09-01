import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router'
import {
  Activity,
  Box,
  Clock3,
  Cpu,
  Download,
  Eye,
  Film,
  History as HistoryIcon,
  ImageUp,
  Layers,
  Loader2,
  RefreshCw,
  RotateCcw,
  Sparkles,
  Trash2,
  TriangleAlert,
  Upload,
  WandSparkles,
  Zap,
} from 'lucide-react'
import { AnimatePresence, motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'

import { Button } from '../components/ui/button'
import { MetaPill, SurfacePanel } from '../components/ui/foundation'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Textarea } from '../components/ui/textarea'
import { GenerationErrorState } from '../components/GenerationErrorState'
import { toAssetUrl, type GeneratePayload, type TaskStatusResp } from '../lib/api'
import { clampToConstraint, generationConstraints } from '../lib/generationConstraints'
import { appRoutes } from '../lib/routes'
import { loadForm, saveForm, type FormState } from '../lib/storage'
import { cn } from '../lib/utils'
import { useJobs } from '../providers/JobProvider'
import { useSettings } from '../providers/SettingsProvider'

const ACTIVE_KEY = 'amaimagery.activeJobId'

type GenerateFormState = FormState
type SectionTone = 'dashboard' | 'editorial' | 'cinematic'

function buildGeneratedImageUrl(result: TaskStatusResp): string | null {
  if (result.image_url) return toAssetUrl(result.image_url)

  const filename = result.image_filename || String(result.image_path || '').split(/[\\/]/).pop() || ''
  if (!filename) return null

  const query = new URLSearchParams({ path: filename })
  if (typeof result.exp === 'number') query.set('exp', String(result.exp))
  if (typeof result.sig === 'string' && result.sig.length > 0) query.set('sig', result.sig)
  return toAssetUrl(`/api/v1/file?${query.toString()}`)
}

function fileToBase64(file: File): Promise<string> {
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

function deriveInitialForm(saved: Partial<FormState> | null, defaults: Partial<FormState>): GenerateFormState {
  return {
    prompt: saved?.prompt ?? '',
    neg: saved?.neg ?? '',
    steps: clampToConstraint('steps', saved?.steps ?? defaults.steps ?? generationConstraints.steps.default),
    guidance: clampToConstraint('guidance', saved?.guidance ?? defaults.guidance ?? generationConstraints.guidance.default),
    width: clampToConstraint('width', saved?.width ?? defaults.width ?? generationConstraints.width.default),
    height: clampToConstraint('height', saved?.height ?? defaults.height ?? generationConstraints.height.default),
    seed: saved?.seed ?? defaults.seed ?? null,
    ipScale: clampToConstraint('ipScale', saved?.ipScale ?? defaults.ipScale ?? generationConstraints.ipScale.default),
    style: 'realistic',
  }
}

function sectionToneClasses(tone: SectionTone) {
  if (tone === 'editorial') return 'border-foreground/10 bg-card/40'
  if (tone === 'cinematic') return 'border-white/10 bg-white/5 text-white backdrop-blur-2xl'
  return 'border-border/50 bg-card/75'
}

function SectionCard({
  tone,
  title,
  description,
  action,
  children,
  className,
}: {
  tone: SectionTone
  title: string
  description?: string
  action?: React.ReactNode
  children: React.ReactNode
  className?: string
}) {
  return (
    <SurfacePanel className={cn('p-6 md:p-8 space-y-6', sectionToneClasses(tone), className)}>
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="space-y-2">
          <h3 className={cn(
            'font-black uppercase tracking-[0.2em] text-xs',
            tone === 'editorial' ? 'font-serif normal-case tracking-normal text-3xl font-light' : '',
            tone === 'cinematic' ? 'text-primary text-[10px] tracking-[0.35em]' : 'text-primary',
          )}>
            {title}
          </h3>
          {description ? (
            <p className={cn('max-w-2xl text-sm leading-relaxed', tone === 'cinematic' ? 'text-white/60' : 'text-foreground/60')}>
              {description}
            </p>
          ) : null}
        </div>
        {action}
      </div>
      {children}
    </SurfacePanel>
  )
}

function NumericField({
  label,
  value,
  onChange,
  min,
  max,
  step,
  tone,
}: {
  label: string
  value: number
  onChange: (value: number) => void
  min: number
  max: number
  step: number
  tone: SectionTone
}) {
  return (
    <label className="space-y-2">
      <span className={cn('text-[10px] font-black uppercase tracking-[0.22em]', tone === 'cinematic' ? 'text-white/40' : 'text-foreground/40')}>
        {label}
      </span>
      <Input
        type="number"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className={cn('h-11 rounded-2xl border font-semibold', tone === 'cinematic' ? 'border-white/10 bg-white/5 text-white' : 'border-border bg-secondary/30')}
      />
    </label>
  )
}

function StatusMessage({
  tone,
  title,
  description,
  state,
}: {
  tone: SectionTone
  title: string
  description: string
  state: 'idle' | 'queued' | 'running' | 'completed' | 'error'
}) {
  const palette =
    state === 'error'
      ? 'border-danger/20 bg-danger/5 text-danger'
      : state === 'completed'
        ? 'border-success/20 bg-success/5 text-success'
        : state === 'idle'
          ? tone === 'cinematic'
            ? 'border-white/10 bg-white/5 text-white/70'
            : 'border-border/50 bg-secondary/20 text-foreground/70'
          : 'border-primary/20 bg-primary/5 text-primary'

  return (
    <div className={cn('rounded-3xl border p-5 space-y-3 break-words overflow-hidden', palette)}>
      <div className="flex items-center gap-3">
        {state === 'error' ? <TriangleAlert className="h-5 w-5 shrink-0" /> : state === 'completed' ? <Sparkles className="h-5 w-5 shrink-0" /> : <Activity className="h-5 w-5 shrink-0" />}
        <div className="font-bold tracking-tight">{title}</div>
      </div>
      <p className={cn('text-sm leading-relaxed break-words line-clamp-3', state === 'idle' ? '' : 'opacity-90')}>{description}</p>
    </div>
  )
}

export default function Generate() {
  const { t } = useTranslation(['generate', 'common'])
  const { settings } = useSettings()
  const { jobs, start, cancel, get } = useJobs()

  const defaultPreset = useMemo(
    () => settings.presets.find((preset) => preset.id === settings.defaultPresetId) ?? settings.presets[0] ?? null,
    [settings.defaultPresetId, settings.presets],
  )

  const initialForm = useMemo(
    () =>
      deriveInitialForm(loadForm(), defaultPreset
        ? {
            steps: defaultPreset.steps,
            guidance: defaultPreset.guidance,
            width: defaultPreset.width,
            height: defaultPreset.height,
            seed: defaultPreset.seed,
            ipScale: defaultPreset.ipScale,
          }
        : {}),
    [defaultPreset],
  )

  const [prompt, setPrompt] = useState(initialForm.prompt)
  const [neg, setNeg] = useState(initialForm.neg)
  const [steps, setSteps] = useState(initialForm.steps)
  const [guidance, setGuidance] = useState(initialForm.guidance)
  const [width, setWidth] = useState(initialForm.width)
  const [height, setHeight] = useState(initialForm.height)
  const [seed, setSeed] = useState<number | null>(initialForm.seed)
  const [ipScale, setIpScale] = useState(initialForm.ipScale)
  const style: 'realistic' = 'realistic'
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
  const stage: 'idle' | 'queued' | 'running' | 'completed' | 'error' =
    busy && activeJob
      ? activeJob.status === 'queued'
        ? 'queued'
        : 'running'
      : error
        ? 'error'
        : imgUrl
          ? 'completed'
          : 'idle'
  const styleLabel = t('generate:style_options.realistic')

  useEffect(() => {
    saveForm({ prompt, neg, steps, guidance, width, height, seed, ipScale, style })
  }, [prompt, neg, steps, guidance, width, height, seed, ipScale, style])

  useEffect(() => {
    if (!activeJob) return

    if (activeJob.status === 'completed' && activeJob.result) {
      const nextImgUrl = buildGeneratedImageUrl(activeJob.result)
      if (nextImgUrl) setImgUrl(nextImgUrl)
      else setError(t('generate:errors.no_artifact'))
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

  function applyPreset(presetId: string) {
    const preset = settings.presets.find((item) => item.id === presetId)
    if (!preset) return

    setSteps(clampToConstraint('steps', preset.steps))
    setGuidance(clampToConstraint('guidance', preset.guidance))
    setWidth(clampToConstraint('width', preset.width))
    setHeight(clampToConstraint('height', preset.height))
    setSeed(preset.seed)
    setIpScale(clampToConstraint('ipScale', preset.ipScale))
    setNeg(preset.neg)
  }

  function resetToDefaults() {
    if (defaultPreset) {
      applyPreset(defaultPreset.id)
      return
    }
    setSteps(generationConstraints.steps.default)
    setGuidance(generationConstraints.guidance.default)
    setWidth(generationConstraints.width.default)
    setHeight(generationConstraints.height.default)
    setSeed(null)
    setIpScale(generationConstraints.ipScale.default)
  }

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

  function clearReference() {
    if (refPreview?.startsWith('blob:')) URL.revokeObjectURL(refPreview)
    setRefPreview(null)
    refBase64.current = null
  }

  const onDrop = (event: React.DragEvent) => {
    event.preventDefault()
    const file = event.dataTransfer.files?.[0]
    if (file) void onFilePicked(file)
  }

  async function runGeneration() {
    if (!prompt || prompt.trim().length < 3) {
      setError(t('generate:errors.prompt_short'))
      return
    }

    setError(null)
    const banlist = (settings.banlist || '').split(/,|\n/).map((item) => item.trim()).filter(Boolean)
    const payload: GeneratePayload = {
      prompt: prompt.trim(),
      negative_prompt: [neg, ...banlist].filter(Boolean).join(', ') || null,
      steps: clampToConstraint('steps', steps),
      guidance_scale: clampToConstraint('guidance', guidance),
      width: clampToConstraint('width', width),
      height: clampToConstraint('height', height),
      seed: seed ?? null,
      ref_image_b64: refBase64.current,
      ip_scale: clampToConstraint('ipScale', ipScale),
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

  const retryCurrentSettings = () => {
    setError(null)
    void runGeneration()
  }

  const seedRandom = () => setSeed(Math.floor(Math.random() * 2_147_483_647))

  const statusTitle =
    stage === 'queued'
      ? t('generate:status.queued.title', { position: queuePosition || 1 })
      : stage === 'running'
        ? t('generate:status.running.title')
        : stage === 'completed'
          ? t('generate:status.completed.title')
          : stage === 'error'
            ? t('generate:status.error.title')
            : t('generate:status.idle.title')

  const statusDescription =
    stage === 'queued'
      ? t('generate:status.queued.desc1')
      : stage === 'running'
        ? t('generate:status.running.desc')
        : stage === 'completed'
          ? t('generate:status.completed.desc')
          : stage === 'error'
            ? error || t('generate:status.error.desc')
            : t('generate:status.idle.desc')

  const promptSection = (tone: SectionTone) => (
    <SectionCard
      tone={tone}
      title={t('generate:prompt')}
      description={t('generate:subtitle')}
      action={
        <div className="flex flex-wrap gap-2">
          {settings.presets.map((preset) => (
            <button
              key={preset.id}
              onClick={() => applyPreset(preset.id)}
              className={cn(
                'rounded-full border px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.18em] transition-colors',
                tone === 'cinematic'
                  ? 'border-white/10 bg-white/5 text-white/70 hover:border-primary/30 hover:text-primary'
                  : 'border-border bg-secondary/20 text-foreground/60 hover:border-primary/20 hover:text-primary',
              )}
            >
              {preset.name}
            </button>
          ))}
        </div>
      }
    >
      <Textarea
        value={prompt}
        onChange={(event) => setPrompt(event.target.value)}
        placeholder={t('generate:prompt_placeholder')}
        className={cn(
          'min-h-[180px] resize-none rounded-[28px] border p-6 text-lg leading-relaxed',
          tone === 'editorial' ? 'bg-secondary/10 text-xl font-light italic' : '',
          tone === 'cinematic'
            ? 'border-white/10 bg-black/30 text-white placeholder:text-white/20'
            : 'border-border bg-secondary/20',
        )}
      />
    </SectionCard>
  )

  const negativeSection = (tone: SectionTone) => (
    <SectionCard tone={tone} title={t('generate:neg')} description={t('generate:neg_placeholder')}>
      <Textarea
        value={neg}
        onChange={(event) => setNeg(event.target.value)}
        placeholder={t('generate:neg_placeholder')}
        className={cn(
          'min-h-[120px] resize-none rounded-[28px] border p-5 text-base',
          tone === 'cinematic'
            ? 'border-white/10 bg-black/30 text-white placeholder:text-white/20'
            : 'border-border bg-secondary/20',
        )}
      />
    </SectionCard>
  )

  const dimensionsSection = (tone: SectionTone) => (
    <SectionCard tone={tone} title={t('generate:sections.dimensions')} description={t('generate:sections.dimensions_description')}>
      <div className="grid gap-4 sm:grid-cols-2">
        <NumericField
          label={t('generate:advanced.width')}
          value={width}
          onChange={(value) => setWidth(clampToConstraint('width', value))}
          min={generationConstraints.width.min}
          max={generationConstraints.width.max}
          step={generationConstraints.width.step}
          tone={tone}
        />
        <NumericField
          label={t('generate:advanced.height')}
          value={height}
          onChange={(value) => setHeight(clampToConstraint('height', value))}
          min={generationConstraints.height.min}
          max={generationConstraints.height.max}
          step={generationConstraints.height.step}
          tone={tone}
        />
      </div>
      <div className={cn(
        'flex items-center gap-2 rounded-2xl px-4 py-3 text-sm',
        tone === 'cinematic' ? 'bg-white/5 text-white/60' : 'bg-secondary/20 text-foreground/60',
      )}>
        <Box className="h-4 w-4 text-primary" />
        <span>{width} × {height}</span>
      </div>
    </SectionCard>
  )

  const samplingSection = (tone: SectionTone) => (
    <SectionCard
      tone={tone}
      title={t('generate:advanced.title')}
      description={t('generate:sections.sampling_description')}
      action={
        <Button variant="ghost" size="sm" onClick={resetToDefaults} className="rounded-full">
          <RotateCcw className="mr-2 h-4 w-4" />
          {t('generate:advanced.reset')}
        </Button>
      }
    >
      <div className="grid gap-4 md:grid-cols-2">
        <NumericField
          label={t('generate:advanced.steps')}
          value={steps}
          onChange={(value) => setSteps(clampToConstraint('steps', value))}
          min={generationConstraints.steps.min}
          max={generationConstraints.steps.max}
          step={generationConstraints.steps.step}
          tone={tone}
        />
        <NumericField
          label={t('generate:advanced.cfg')}
          value={guidance}
          onChange={(value) => setGuidance(clampToConstraint('guidance', value))}
          min={generationConstraints.guidance.min}
          max={generationConstraints.guidance.max}
          step={generationConstraints.guidance.step}
          tone={tone}
        />
        <NumericField
          label={t('generate:advanced.ip_scale')}
          value={ipScale}
          onChange={(value) => setIpScale(clampToConstraint('ipScale', value))}
          min={generationConstraints.ipScale.min}
          max={generationConstraints.ipScale.max}
          step={generationConstraints.ipScale.step}
          tone={tone}
        />
        <div className="space-y-2">
          <Label className={cn('text-[10px] font-black uppercase tracking-[0.22em]', tone === 'cinematic' ? 'text-white/40' : 'text-foreground/40')}>
            {t('generate:advanced.seed')}
          </Label>
          <div className="flex gap-2">
            <Input
              type="number"
              value={seed ?? ''}
              placeholder={t('generate:advanced.seed_auto')}
              onChange={(event) => setSeed(event.target.value ? Number(event.target.value) : null)}
              className={cn('h-11 rounded-2xl border font-semibold', tone === 'cinematic' ? 'border-white/10 bg-white/5 text-white' : 'border-border bg-secondary/30')}
            />
            <Button variant="secondary" size="icon" onClick={seedRandom} className="rounded-2xl">
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </SectionCard>
  )

  const referenceSection = (tone: SectionTone) => (
    <SectionCard
      tone={tone}
      title={t('generate:ref.title')}
      description={t('generate:ref.description')}
      action={
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()} className="rounded-full">
            <Upload className="mr-2 h-4 w-4" />
            {t('generate:ref.button')}
          </Button>
          {refPreview ? (
            <Button variant="ghost" size="icon" onClick={clearReference} className="rounded-full">
              <Trash2 className="h-4 w-4" />
            </Button>
          ) : null}
        </div>
      }
    >
      <div
        onDrop={onDrop}
        onDragOver={(event) => event.preventDefault()}
        className={cn(
          'relative overflow-hidden rounded-[28px] border-2 border-dashed p-4 transition-all',
          refPreview ? 'min-h-[240px] border-primary/25' : 'min-h-[220px]',
          tone === 'cinematic' ? 'border-white/10 bg-black/30' : 'border-border/70 bg-secondary/20',
        )}
      >
        {refPreview ? (
          <>
            <img src={refPreview} alt={t('generate:ref.title')} className="h-full w-full rounded-[20px] object-cover" />
            <div className="absolute inset-x-6 bottom-6 flex gap-3">
              <Button variant="secondary" onClick={() => fileInputRef.current?.click()} className="rounded-full">
                {t('generate:ref.button')}
              </Button>
              <Button variant="outline" onClick={clearReference} className="rounded-full">
                {t('generate:ref.clear')}
              </Button>
            </div>
          </>
        ) : (
          <div className="flex h-full flex-col items-center justify-center gap-5 text-center">
            <div className={cn(
              'flex h-16 w-16 items-center justify-center rounded-3xl border',
              tone === 'cinematic' ? 'border-white/10 bg-white/5 text-primary' : 'border-primary/20 bg-primary/10 text-primary',
            )}>
              <ImageUp className="h-7 w-7" />
            </div>
            <div className="space-y-2">
              <p className={cn('text-sm font-semibold', tone === 'cinematic' ? 'text-white/70' : 'text-foreground/70')}>
                {t('generate:ref.drop')}
              </p>
              <p className={cn('text-xs', tone === 'cinematic' ? 'text-white/40' : 'text-foreground/45')}>
                {t('generate:sections.reference_hint')}
              </p>
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
    </SectionCard>
  )

  const resultSection = (tone: SectionTone) => (
    <SectionCard tone={tone} title={t('generate:result.title')} description={t('generate:result.description')}>
      <div className={cn(
        'relative flex min-h-[360px] items-center justify-center overflow-hidden rounded-[32px] border',
        tone === 'cinematic' ? 'border-white/10 bg-black/40' : 'border-border/50 bg-secondary/20',
      )}>
        <AnimatePresence mode="wait">
          {error ? (
            <GenerationErrorState
              key="generation-error"
              error={error}
              tone={tone}
              onRetry={retryCurrentSettings}
              onDismiss={() => setError(null)}
            />
          ) : imgUrl ? (
            <motion.img
              key={imgUrl}
              initial={{ opacity: 0, scale: 1.02 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              src={imgUrl}
              alt={t('generate:result.title')}
              className="max-h-[70vh] max-w-full rounded-[24px] object-contain shadow-2xl"
            />
          ) : (
            <motion.div key="placeholder" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4 text-center">
              <div className={cn('mx-auto flex h-20 w-20 items-center justify-center rounded-full', tone === 'cinematic' ? 'bg-white/5 text-primary' : 'bg-primary/10 text-primary')}>
                {tone === 'cinematic' ? <Film className="h-8 w-8" /> : <Eye className="h-8 w-8" />}
              </div>
              <div className="space-y-1">
                <div className={cn('font-bold', tone === 'cinematic' ? 'text-white' : 'text-foreground')}>
                  {t('generate:result.ready_title')}
                </div>
                <div className={cn('text-sm', tone === 'cinematic' ? 'text-white/50' : 'text-foreground/50')}>
                  {t('generate:result.ready_desc')}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="flex flex-wrap gap-3">
        <MetaPill>{styleLabel}</MetaPill>
        <MetaPill>{width}×{height}</MetaPill>
        <MetaPill>{steps} {t('generate:advanced.steps')}</MetaPill>
      </div>

      {imgUrl && !error ? (
        <div className="flex flex-wrap gap-3">
          <Button asChild size="lg" className="rounded-full">
            <a href={imgUrl} download>
              <Download className="mr-2 h-4 w-4" />
              {t('generate:actions.download')}
            </a>
          </Button>
          <Button asChild variant="outline" size="lg" className="rounded-full">
            <Link to={appRoutes.history}>
              <HistoryIcon className="mr-2 h-4 w-4" />
              {t('generate:actions.history')}
            </Link>
          </Button>
        </div>
      ) : null}
    </SectionCard>
  )

  const statusSection = (tone: SectionTone) => (
    <div className="space-y-4">
      <StatusMessage tone={tone} title={statusTitle} description={statusDescription} state={stage} />
      {busy ? (
        <div className={cn('overflow-hidden rounded-full', tone === 'cinematic' ? 'bg-white/10' : 'bg-primary/10')}>
          <motion.div initial={{ width: 0 }} animate={{ width: stage === 'queued' ? '18%' : '72%' }} className="h-2 bg-primary" />
        </div>
      ) : null}
      <div className="grid gap-3 sm:grid-cols-3">
        {[
          { icon: Layers, label: t('generate:facts.aspect'), value: `${width}:${height}` },
          { icon: Cpu, label: t('generate:facts.style'), value: styleLabel },
          { icon: Clock3, label: t('generate:facts.queue'), value: busy ? `${queuePosition || 1}` : t('generate:facts.idle') },
        ].map((fact) => (
          <div key={fact.label} className={cn('rounded-3xl border p-4', tone === 'cinematic' ? 'border-white/10 bg-white/5 text-white' : 'border-border/50 bg-secondary/20')}>
            <div className={cn('flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em]', tone === 'cinematic' ? 'text-white/40' : 'text-foreground/40')}>
              <fact.icon className="h-3.5 w-3.5 text-primary" />
              {fact.label}
            </div>
            <div className="mt-3 text-sm font-bold">{fact.value}</div>
          </div>
        ))}
      </div>
    </div>
  )

  const actionsSection = (tone: SectionTone) => (
    <SectionCard tone={tone} title={t('generate:sections.run_title')} description={t('generate:sections.run_description')}>
      <div className="flex flex-wrap gap-3">
        <Button onClick={() => void runGeneration()} disabled={busy} size="lg" className="rounded-full">
          {busy ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              {t('generate:actions.working')}
            </>
          ) : (
            <>
              <WandSparkles className="mr-2 h-5 w-5" />
              {t('generate:actions.generate')}
            </>
          )}
        </Button>
        {busy && activeId ? (
          <Button variant="outline" size="lg" onClick={() => cancel(activeId)} className="rounded-full">
            {t('generate:actions.cancel')}
          </Button>
        ) : null}
        {error ? (
          <Button variant="secondary" size="lg" onClick={retryCurrentSettings} className="rounded-full">
            <RefreshCw className="mr-2 h-4 w-4" />
            {t('generate:actions.retry')}
          </Button>
        ) : null}
        <Button asChild variant="ghost" size="lg" className="rounded-full">
          <Link to={appRoutes.promptGuide}>{t('common:actions.guide')}</Link>
        </Button>
      </div>
    </SectionCard>
  )

  const renderDashboard = () => (
    <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr] items-start">
      <div className="space-y-6">
        {promptSection('dashboard')}
        {negativeSection('dashboard')}
        <div className="grid gap-6 lg:grid-cols-2">
          {dimensionsSection('dashboard')}
          {samplingSection('dashboard')}
        </div>
        {actionsSection('dashboard')}
      </div>
      <div className="space-y-6 xl:sticky xl:top-24">
        {resultSection('dashboard')}
        {referenceSection('dashboard')}
        {statusSection('dashboard')}
      </div>
    </div>
  )

  const renderEditorial = () => (
    <div className="mx-auto max-w-6xl space-y-10">
      <div className="grid gap-8 xl:grid-cols-[1.15fr_0.85fr] items-start">
        <div className="space-y-8">
          {promptSection('editorial')}
          {negativeSection('editorial')}
          {dimensionsSection('editorial')}
        </div>
        <div className="space-y-8 xl:sticky xl:top-24">
          {resultSection('editorial')}
          {statusSection('editorial')}
        </div>
      </div>
      <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
        {samplingSection('editorial')}
        {referenceSection('editorial')}
      </div>
      {actionsSection('editorial')}
    </div>
  )

  const renderCinematic = () => (
    <div className="relative -mx-4 overflow-hidden rounded-[40px] border border-white/10 bg-black px-4 py-6 md:-mx-6 md:px-6 md:py-8">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(14,165,233,0.16),transparent_40%),radial-gradient(circle_at_bottom,rgba(249,115,22,0.12),transparent_35%)]" />
      <div className="relative z-10 grid gap-6 xl:grid-cols-[1.1fr_0.9fr] items-start">
        <div className="space-y-6">
          {resultSection('cinematic')}
          {promptSection('cinematic')}
          <div className="grid gap-6 lg:grid-cols-2">
            {negativeSection('cinematic')}
            {referenceSection('cinematic')}
          </div>
        </div>
        <div className="space-y-6 xl:sticky xl:top-24">
          {statusSection('cinematic')}
          {dimensionsSection('cinematic')}
          {samplingSection('cinematic')}
          {actionsSection('cinematic')}
        </div>
      </div>
    </div>
  )

  return (
    <section className={cn('page-shell transition-all duration-500', settings.visualMode === 'cinematic' ? 'py-4 md:py-6' : 'py-8 md:py-12 space-y-8')}>
      {settings.visualMode !== 'cinematic' ? (
        <SurfacePanel className={cn('mode-hero-panel p-6 md:p-8', settings.visualMode === 'editorial' && 'mode-hero-panel--editorial text-center')}>
          <div className={cn('flex flex-col gap-6 md:flex-row md:items-end md:justify-between', settings.visualMode === 'editorial' && 'items-center')}>
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-[10px] font-black uppercase tracking-[0.24em] text-primary">
                <Zap className="h-3.5 w-3.5" />
                {t('generate:title')}
              </div>
              <div className="space-y-2">
                <h1 className={cn('font-black tracking-tight', settings.visualMode === 'editorial' ? 'font-serif text-5xl font-light italic md:text-7xl' : 'text-3xl md:text-5xl')}>
                  {t('generate:hero.title')}
                </h1>
                <p className={cn('max-w-3xl text-base leading-relaxed', settings.visualMode === 'editorial' ? 'mx-auto text-lg' : 'text-foreground/60')}>
                  {t('generate:hero.description')}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button asChild variant="outline" className="rounded-full">
                <Link to={appRoutes.promptGuide}>{t('common:actions.guide')}</Link>
              </Button>
              <Button asChild variant="outline" className="rounded-full">
                <Link to={appRoutes.history}>{t('generate:actions.history')}</Link>
              </Button>
            </div>
          </div>
        </SurfacePanel>
      ) : null}

      <motion.div key={settings.visualMode} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}>
        {settings.visualMode === 'dashboard'
          ? renderDashboard()
          : settings.visualMode === 'editorial'
            ? renderEditorial()
            : renderCinematic()}
      </motion.div>
    </section>
  )
}
