import { useEffect, useMemo, useRef, useState } from 'react'
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
  SlidersHorizontal,
  Sparkles,
  TriangleAlert,
} from 'lucide-react'
import { motion } from 'framer-motion'

import { Button } from '../components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { MetaPill, SectionEyebrow, SurfacePanel } from '../components/ui/foundation'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Textarea } from '../components/ui/textarea'
import { appRoutes } from '../lib/routes'
import { type GeneratePayload } from '../lib/api'
import { loadForm, saveForm } from '../lib/storage'
import { cn } from '../lib/utils'
import { normalizeError } from '../lib/errors'
import { useSettings } from '../providers/SettingsProvider'
import { useJobs } from '../providers/JobProvider'

const ACTIVE_KEY = 'amaimagery.activeJobId'

type VisualMode = 'work-product' | 'mood-board'
type Density = 'constrained' | 'expanded'
type ShotPreset = 'creator-portrait' | 'product-crop' | 'wide-frame'

const styleOptions = [
  { value: 'realistic', label: 'Editorial' },
  { value: 'anime', label: 'Illustration' },
] as const

const shotPresets: { value: ShotPreset; label: string }[] = [
  { value: 'creator-portrait', label: 'Creator portrait' },
  { value: 'product-crop', label: 'Product crop' },
  { value: 'wide-frame', label: 'Wide frame' },
]

export default function Generate() {
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
  const [shotPreset, setShotPreset] = useState<ShotPreset>('creator-portrait')
  const [density, setDensity] = useState<Density>('constrained')
  const [visualMode, setVisualMode] = useState<VisualMode>('work-product')

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
  const orderedRuntimeJobs = useMemo(
    () =>
      [...jobs]
        .filter((job) => job.status === 'queued' || job.status === 'running')
        .sort((left, right) => left.startedAt - right.startedAt),
    [jobs],
  )

  const queuePosition = activeId ? orderedRuntimeJobs.findIndex((job) => job.id === activeId) + 1 : 0
  const busy = activeJob?.status === 'running' || activeJob?.status === 'queued'
  const stage = busy ? activeJob.status : error ? 'error' : imgUrl ? 'done' : 'idle'
  const styleLabel = styleOptions.find((option) => option.value === style)?.label ?? 'Editorial'

  useEffect(() => {
    saveForm({ prompt, neg, steps, guidance, width, height, seed, ipScale, style })
  }, [prompt, neg, steps, guidance, width, height, seed, ipScale, style])

  useEffect(() => {
    if (!activeJob) return

    if (activeJob.status === 'done' && activeJob.result) {
      const result = activeJob.result

      if (result.image_url) {
        setImgUrl(result.image_url)
      } else if (result.image_filename && result.exp && result.sig) {
        setImgUrl(
          `/api/v1/file?path=${encodeURIComponent(result.image_filename)}&exp=${String(result.exp)}&sig=${encodeURIComponent(result.sig)}`,
        )
      } else if (result.image_filename) {
        setImgUrl(`/api/v1/file?path=${encodeURIComponent(result.image_filename)}`)
      } else if (result.image_path) {
        const name = String(result.image_path).split(/[\\/]/).pop() || String(result.image_path)
        setImgUrl(`/api/v1/file?path=${encodeURIComponent(name)}`)
      } else {
        setError('Image artifact was not returned by the provider.')
      }

      try {
        localStorage.removeItem(ACTIVE_KEY)
      } catch {
        // ignore storage failures
      }
      setActiveId(null)
    }

    if (activeJob.status === 'error') {
      setError(activeJob.error || 'Generation failed.')
      try {
        localStorage.removeItem(ACTIVE_KEY)
      } catch {
        // ignore storage failures
      }
      setActiveId(null)
    }
  }, [activeJob])

  async function onFilePicked(file: File) {
    if (!file.type.startsWith('image/')) {
      setError('Reference upload accepts image files only.')
      return
    }
    if (file.size > 8 * 1024 * 1024) {
      setError('Reference upload is limited to 8 MB.')
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
      setError('Prompt needs at least three characters.')
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
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="page-shell space-y-6 py-8 xl:py-10"
    >
      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <SurfacePanel glass className="space-y-5 p-6 md:p-8">
          <SectionEyebrow>Generate</SectionEyebrow>
          <div className="space-y-4">
            <h1 className="font-display text-4xl font-semibold tracking-[-0.06em] text-foreground sm:text-5xl lg:text-6xl">
              Main product shell with preserved IA and internal state variants.
            </h1>
            <p className="max-w-3xl text-base leading-7 text-muted-foreground">
              Desktop-first composer with result stage, visible advanced controls, and explicit queued, running,
              completed, and error feedback inside the same workspace.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <MetaPill>Generate / Default / Dark</MetaPill>
            <MetaPill>Advanced controls visible</MetaPill>
            <MetaPill>Reference upload + runtime status</MetaPill>
          </div>
        </SurfacePanel>

        <SurfacePanel className="space-y-5 p-6 md:p-8">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/12 text-primary">
              <SlidersHorizontal className="h-5 w-5" />
            </div>
            <div>
              <h2 className="font-display text-[28px] font-semibold tracking-[-0.05em]">Advanced controls in view</h2>
              <p className="text-sm leading-6 text-muted-foreground">
                IP scale, shot preset, density, and visual mode stay readable instead of hiding behind a secondary route.
              </p>
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <SurfacePanel className="rounded-[24px] p-4 shadow-none">
              <div className="text-xs uppercase tracking-[0.26em] text-muted-foreground">IP scale</div>
              <div className="mt-2 font-display text-2xl font-semibold tracking-[-0.05em]">{ipScale.toFixed(2)}</div>
            </SurfacePanel>
            <SurfacePanel className="rounded-[24px] p-4 shadow-none">
              <div className="text-xs uppercase tracking-[0.26em] text-muted-foreground">Shot preset</div>
              <div className="mt-2 font-display text-2xl font-semibold tracking-[-0.05em]">
                {shotPresets.find((preset) => preset.value === shotPreset)?.label}
              </div>
            </SurfacePanel>
            <SurfacePanel className="rounded-[24px] p-4 shadow-none">
              <div className="text-xs uppercase tracking-[0.26em] text-muted-foreground">Component density</div>
              <div className="mt-2 font-display text-2xl font-semibold tracking-[-0.05em]">
                {density === 'constrained' ? 'Constrained' : 'Expanded'}
              </div>
            </SurfacePanel>
            <SurfacePanel className="rounded-[24px] p-4 shadow-none">
              <div className="text-xs uppercase tracking-[0.26em] text-muted-foreground">Visual mode</div>
              <div className="mt-2 font-display text-2xl font-semibold tracking-[-0.05em]">
                {visualMode === 'work-product' ? 'Work product' : 'Mood board'}
              </div>
            </SurfacePanel>
          </div>
        </SurfacePanel>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.05fr)_380px]">
        <Card glass={settings.glass} className="overflow-visible">
          <CardHeader className="space-y-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="space-y-2">
                <CardTitle>Generate / Default</CardTitle>
                <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
                  Compose the prompt, keep negative guidance explicit, and prepare reference input before committing the
                  run.
                </p>
              </div>
              <Button asChild variant="ghost" size="sm">
                <Link to={appRoutes.promptGuide}>Prompt Guide</Link>
              </Button>
            </div>

            <div className="grid gap-3 sm:grid-cols-4">
              <MetaPill>Style {styleLabel}</MetaPill>
              <MetaPill>CFG {guidance.toFixed(1)}</MetaPill>
              <MetaPill>
                Size {width}×{height}
              </MetaPill>
              <MetaPill>Seed {seed ?? 'Auto'}</MetaPill>
            </div>
          </CardHeader>

          <CardContent className="space-y-5">
            <div className="space-y-3">
              <Label htmlFor="prompt">Prompt</Label>
              <Textarea
                id="prompt"
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                placeholder="Fashion portrait in editorial midnight studio, precise eyes, quiet confidence, polished chrome accents."
              />
            </div>

            <div className="space-y-3">
              <Label htmlFor="neg">Negative prompt</Label>
              <Textarea
                id="neg"
                value={neg}
                onChange={(event) => setNeg(event.target.value)}
                placeholder="blurry, extra digits, distorted face, low contrast, noisy skin"
              />
            </div>

            <div className="space-y-3">
              <Label>Style</Label>
              <div className="flex flex-wrap gap-3">
                {styleOptions.map((option) => (
                  <Button
                    key={option.value}
                    type="button"
                    variant={style === option.value ? 'default' : 'secondary'}
                    onClick={() => setStyle(option.value)}
                  >
                    {option.label}
                  </Button>
                ))}
              </div>
            </div>

            <div
              onDrop={onDrop}
              onDragOver={(event) => event.preventDefault()}
              className={cn(
                'rounded-[28px] border border-dashed border-border/70 p-5 transition-colors',
                refPreview ? 'bg-primary/8' : 'bg-card/55',
              )}
            >
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="space-y-2">
                  <div className="text-sm font-semibold">Reference upload</div>
                  <p className="max-w-md text-sm leading-6 text-muted-foreground">
                    Use an image to guide pose, composition, or lighting before the run starts.
                  </p>
                </div>
                <input
                  ref={fileInputRef}
                  id="reference-upload"
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={async (event) => {
                    const file = event.target.files?.[0]
                    if (file) await onFilePicked(file)
                  }}
                />
                <Button variant="secondary" onClick={() => fileInputRef.current?.click()}>
                  <ImageUp className="mr-2 h-4 w-4" />
                  Choose image
                </Button>
              </div>

              {refPreview ? (
                <div className="mt-4 overflow-hidden rounded-[24px] border border-border/60">
                  <img src={refPreview} alt="Reference preview" className="h-56 w-full object-cover" />
                </div>
              ) : (
                <div className="mt-4 rounded-[24px] border border-border/50 bg-background/40 px-4 py-5 text-sm text-muted-foreground">
                  Drop image here or browse to add pose, lighting, or style guidance.
                </div>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Button onClick={runGeneration} disabled={busy} size="lg">
                {busy ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Working
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate
                  </>
                )}
              </Button>
              {busy && activeId ? (
                <Button variant="outline" onClick={() => cancel(activeId)}>
                  Cancel run
                </Button>
              ) : null}
              <Button variant="ghost" onClick={() => setRefPreview(null)}>
                Clear reference
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card glass={settings.glass}>
          <CardHeader>
            <CardTitle>Advanced controls</CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1">
              <div className="space-y-2">
                <Label htmlFor="steps">Steps</Label>
                <Input id="steps" type="number" min={1} max={200} value={steps} onChange={(event) => setSteps(Number(event.target.value))} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="guidance">CFG scale</Label>
                <Input
                  id="guidance"
                  type="number"
                  min={0}
                  max={30}
                  step={0.5}
                  value={guidance}
                  onChange={(event) => setGuidance(Number(event.target.value))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="width">Width</Label>
                <Input id="width" type="number" min={256} step={64} value={width} onChange={(event) => setWidth(Number(event.target.value))} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="height">Height</Label>
                <Input id="height" type="number" min={256} step={64} value={height} onChange={(event) => setHeight(Number(event.target.value))} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="seed">Seed</Label>
                <Input
                  id="seed"
                  type="number"
                  value={seed ?? ''}
                  onChange={(event) => setSeed(event.target.value === '' ? null : Number(event.target.value))}
                  placeholder="Auto"
                />
              </div>
              <div className="self-end">
                <Button variant="secondary" className="w-full" onClick={seedRandom}>
                  Randomize seed
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <Label htmlFor="ipScale">IP scale</Label>
                <span className="font-semibold">{ipScale.toFixed(2)}</span>
              </div>
              <input
                id="ipScale"
                type="range"
                min={0}
                max={1.5}
                step={0.05}
                value={ipScale}
                onChange={(event) => setIpScale(Number(event.target.value))}
                className="w-full accent-primary"
              />
            </div>

            <div className="space-y-3">
              <Label>Shot preset</Label>
              <div className="grid gap-2">
                {shotPresets.map((preset) => (
                  <Button
                    key={preset.value}
                    variant={shotPreset === preset.value ? 'default' : 'secondary'}
                    className="justify-start"
                    onClick={() => setShotPreset(preset.value)}
                  >
                    {preset.label}
                  </Button>
                ))}
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1">
              <div className="space-y-3">
                <Label>Component density</Label>
                <div className="flex flex-wrap gap-2">
                  <Button variant={density === 'constrained' ? 'default' : 'secondary'} onClick={() => setDensity('constrained')}>
                    Constrained
                  </Button>
                  <Button variant={density === 'expanded' ? 'default' : 'secondary'} onClick={() => setDensity('expanded')}>
                    Expanded
                  </Button>
                </div>
              </div>

              <div className="space-y-3">
                <Label>Visual mode</Label>
                <div className="flex flex-wrap gap-2">
                  <Button variant={visualMode === 'work-product' ? 'default' : 'secondary'} onClick={() => setVisualMode('work-product')}>
                    Work product
                  </Button>
                  <Button variant={visualMode === 'mood-board' ? 'default' : 'secondary'} onClick={() => setVisualMode('mood-board')}>
                    Mood board
                  </Button>
                </div>
              </div>
            </div>

            <Button variant="ghost" onClick={() => setIpScale(0.65)}>
              <RotateCcw className="mr-2 h-4 w-4" />
              Reset advanced controls
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <Card glass={settings.glass}>
          <CardHeader className="space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="space-y-2">
                <CardTitle>Result</CardTitle>
                <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
                  Result stage stays in the same shell and reflects the exact runtime state instead of moving the user
                  into a separate screen.
                </p>
              </div>
              <MetaPill>
                {stage === 'queued'
                  ? 'Queued'
                  : stage === 'running'
                    ? 'Running'
                    : stage === 'done'
                      ? 'Completed'
                      : stage === 'error'
                        ? 'Error'
                        : 'Ready'}
              </MetaPill>
            </div>

            <div className="flex flex-wrap gap-2">
              <MetaPill>{styleLabel}</MetaPill>
              <MetaPill>
                {width}×{height}
              </MetaPill>
              <MetaPill>CFG {guidance.toFixed(1)}</MetaPill>
              <MetaPill>Seed {seed ?? 'Auto'}</MetaPill>
            </div>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="relative overflow-hidden rounded-[32px] border border-border/60 bg-[#07101a]">
              {imgUrl ? (
                <img src={imgUrl} alt="Generated result" className="h-[520px] w-full object-contain" />
              ) : (
                <div className="relative flex h-[520px] items-center justify-center">
                  <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(13,148,255,0.18),transparent_28%),radial-gradient(circle_at_bottom_right,rgba(52,211,153,0.16),transparent_24%)]" />
                  <div className="relative space-y-3 text-center text-white/72">
                    <div className="font-display text-3xl font-semibold tracking-[-0.05em]">Ready for a new run</div>
                    <p className="max-w-sm text-sm leading-6 text-white/55">
                      Result previews, queue status, and final actions stay in this stage once a generation starts.
                    </p>
                  </div>
                </div>
              )}

              {busy ? (
                <div className="absolute inset-0 flex items-center justify-center bg-[#07101a]/60 backdrop-blur">
                  <div className="flex items-center gap-3 rounded-full border border-white/10 bg-white/8 px-5 py-3 text-sm font-semibold text-white">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    {stage === 'queued' ? 'Preparing queue state' : 'Rendering with provider'}
                  </div>
                </div>
              ) : null}
            </div>

            <div className="flex flex-wrap gap-3">
              <Button asChild variant="secondary" disabled={!imgUrl}>
                <a href={imgUrl ?? '#'} target="_blank" rel="noreferrer">
                  <ArrowUpRight className="mr-2 h-4 w-4" />
                  Open result
                </a>
              </Button>
              <Button asChild variant="outline" disabled={!imgUrl}>
                <a href={imgUrl ?? '#'} download>
                  <Download className="mr-2 h-4 w-4" />
                  Download image
                </a>
              </Button>
              <Button asChild variant="ghost">
                <Link to={appRoutes.history}>View history</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <SurfacePanel className="space-y-4 p-6">
            {stage === 'queued' ? (
              <>
                <div className="flex items-center gap-3 text-foreground">
                  <Clock3 className="h-5 w-5 text-primary" />
                  <h3 className="font-display text-[28px] font-semibold tracking-[-0.05em]">Queue position #{queuePosition || 1}</h3>
                </div>
                <p className="text-sm leading-6 text-muted-foreground">
                  Preparing task payload. Prompt, negative prompt, and reference data are locked for this run.
                </p>
                <p className="text-sm leading-6 text-muted-foreground">
                  Waiting for worker availability. The runtime will move to active generation as soon as a worker is
                  free.
                </p>
              </>
            ) : null}

            {stage === 'running' ? (
              <>
                <div className="flex items-center gap-3 text-foreground">
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                  <h3 className="font-display text-[28px] font-semibold tracking-[-0.05em]">Provider status: Generating</h3>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-secondary">
                  <div className="h-full w-2/3 rounded-full bg-primary animate-pulse" />
                </div>
                <p className="text-sm leading-6 text-muted-foreground">
                  Active generation is running. Result actions will unlock as soon as the provider returns an artifact.
                </p>
              </>
            ) : null}

            {stage === 'done' ? (
              <>
                <div className="flex items-center gap-3 text-foreground">
                  <CheckCircle2 className="h-5 w-5 text-success" />
                  <h3 className="font-display text-[28px] font-semibold tracking-[-0.05em]">Generation completed</h3>
                </div>
                <p className="text-sm leading-6 text-muted-foreground">
                  Result is ready for review, download, and traceable follow-up in history.
                </p>
                <div className="grid gap-3">
                  <MetaPill>Open result</MetaPill>
                  <MetaPill>Download image</MetaPill>
                  <MetaPill>View history</MetaPill>
                </div>
              </>
            ) : null}

            {stage === 'error' ? (
              <>
                <div className="flex items-center gap-3 text-foreground">
                  <TriangleAlert className="h-5 w-5 text-danger" />
                  <h3 className="font-display text-[28px] font-semibold tracking-[-0.05em]">Generation could not complete</h3>
                </div>
                <p className="text-sm leading-6 text-muted-foreground">
                  {error || 'The source timed out before returning an artifact. Keep your prompt and retry, or adjust size and CFG.'}
                </p>
                <div className="flex flex-wrap gap-3">
                  <Button variant="secondary" onClick={retryCurrentSettings}>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Retry with same settings
                  </Button>
                  <Button variant="outline" onClick={() => setError(null)}>
                    Edit controls
                  </Button>
                  <Button asChild variant="ghost">
                    <Link to={appRoutes.faq}>Open FAQ</Link>
                  </Button>
                </div>
              </>
            ) : null}

            {stage === 'idle' ? (
              <>
                <div className="flex items-center gap-3 text-foreground">
                  <Sparkles className="h-5 w-5 text-primary" />
                  <h3 className="font-display text-[28px] font-semibold tracking-[-0.05em]">Ready for a new run</h3>
                </div>
                <p className="text-sm leading-6 text-muted-foreground">
                  Use the prompt composer, reference guidance, and advanced controls before generating a new artifact.
                </p>
              </>
            ) : null}
          </SurfacePanel>

          <SurfacePanel className="space-y-4 p-6">
            <div className="text-xs uppercase tracking-[0.26em] text-muted-foreground">Run facts</div>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
              <FactRow label="Style" value={styleLabel} />
              <FactRow label="Aspect" value={`${width}×${height}`} />
              <FactRow label="Seed" value={seed ? String(seed) : 'Auto'} />
              <FactRow label="Queue" value={busy ? `${queuePosition || 1} active` : 'Idle'} />
            </div>
          </SurfacePanel>
        </div>
      </div>
    </motion.section>
  )
}

function FactRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-[20px] border border-border/60 bg-card/65 px-4 py-3 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-semibold text-foreground">{value}</span>
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
