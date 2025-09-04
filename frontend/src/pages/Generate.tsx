import { useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Textarea } from '../components/ui/textarea'
import { generateJSON, type GeneratePayload } from '../lib/api'
import { addHistory, loadForm, saveForm } from '../lib/storage'
import { ImageUp, Loader2, RotateCcw } from 'lucide-react'
import { cn } from '../lib/utils'

type Corr = [string, string]
export default function Generate() {
  const [prompt, setPrompt] = useState(loadForm()?.prompt ?? '')
  const [neg, setNeg] = useState(loadForm()?.neg ?? '')
  const [steps, setSteps] = useState(loadForm()?.steps ?? 28)
  const [guidance, setGuidance] = useState(loadForm()?.guidance ?? 7)
  const [width, setWidth] = useState(loadForm()?.width ?? 896)
  const [height, setHeight] = useState(loadForm()?.height ?? 1152)
  const [seed, setSeed] = useState<number | null>(loadForm()?.seed ?? null)
  const [ipScale, setIpScale] = useState(loadForm()?.ipScale ?? 0.6)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [imgUrl, setImgUrl] = useState<string | null>(null)
  const [hash, setHash] = useState<string | null>(null)
  const [corr, setCorr] = useState<Corr[] | null>(null)
  const [refPreview, setRefPreview] = useState<string | null>(null)
  const refBase64 = useRef<string | null>(null)
  const [progress, setProgress] = useState(0)

  async function onFilePicked(file: File) {
    if (!file.type.startsWith('image/')) { setError('Нужен файл изображения'); return }
    if (file.size > 8 * 1024 * 1024) { setError('Слишком большой файл (до 8 МБ)'); return }
    setError(null); setRefPreview(URL.createObjectURL(file)); refBase64.current = await fileToBase64(file)
  }
  function onDrop(e: React.DragEvent) { e.preventDefault(); const f = e.dataTransfer.files?.[0]; if (f) onFilePicked(f) }

  const doClear = () => {
    setPrompt(''); setNeg(''); setSteps(28); setGuidance(7); setWidth(896); setHeight(1152); setSeed(null); setIpScale(0.6)
    setRefPreview(null); refBase64.current = null; setImgUrl(null); setHash(null); setCorr(null); setError(null)
  }
  const seedRandom = () => setSeed(Math.floor(Math.random() * 2_147_483_647))

  async function gen() {
    if (!prompt || prompt.trim().length < 3) { setError('Промпт слишком короткий'); return }
    setBusy(true); setError(null)
    try {
      const payload = {
        prompt: prompt.trim(),
        negative_prompt: neg.trim() || null,
        steps,
        guidance_scale: guidance,
        width, height,
        seed: seed ?? null,
        ref_image_b64: refBase64.current,
        ip_scale: ipScale,
      }
      const res = await generateJSON(payload)   // ← отправка на /generate
      const url = `/file?path=${encodeURIComponent(res.path)}`
      setImgUrl(url)
      setHash(res.prompt_hash ?? null)
      setCorr(res.corrections ?? null)
      addHistory({ prompt: payload.prompt, path: res.path, ts: Date.now() })
    } catch (e: any) {
      setError(e.message || String(e))
    } finally {
      setBusy(false)
    }
  }


  // Persist form
  saveForm({ prompt, neg, steps, guidance, width, height, seed, ipScale })

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }} transition={{ duration: 0.35, ease: 'easeOut' }} className="container grid grid-cols-1 gap-4 py-4 lg:grid-cols-[420px_1fr]">
      <div className="space-y-4">
        <Card>
          <CardHeader><CardTitle>Параметры генерации</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor="prompt">Промпт</Label>
              <Textarea id="prompt" value={prompt} onChange={e=>setPrompt(e.target.value)} placeholder="anime art, ..."/>
            </div>
            <div className="space-y-2">
              <Label htmlFor="neg">Негативный промпт</Label>
              <Textarea id="neg" value={neg} onChange={e=>setNeg(e.target.value)} placeholder="low quality, ..."/>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2"><Label htmlFor="steps">Шаги</Label><Input id="steps" type="number" min={1} max={200} value={steps} onChange={e=>setSteps(Number(e.target.value))} /></div>
              <div className="space-y-2"><Label htmlFor="guidance">CFG</Label><Input id="guidance" type="number" step={0.5} min={0} max={30} value={guidance} onChange={e=>setGuidance(Number(e.target.value))} /></div>
              <div className="space-y-2"><Label htmlFor="width">Ширина</Label><Input id="width" type="number" min={256} step={64} value={width} onChange={e=>setWidth(Number(e.target.value))} /></div>
              <div className="space-y-2"><Label htmlFor="height">Высота</Label><Input id="height" type="number" min={256} step={64} value={height} onChange={e=>setHeight(Number(e.target.value))} /></div>
              <div className="space-y-2"><Label htmlFor="seed">Seed</Label><Input id="seed" type="number" value={seed ?? ''} onChange={e=>setSeed(e.target.value === '' ? null : Number(e.target.value))} placeholder="пусто = случайный" /></div>
              <div className="space-y-2"><Label>Random seed</Label><Button variant="secondary" onClick={seedRandom}>Случайный</Button></div>
            </div>

            <div className="space-y-2">
              <Label>Пример для нейросети (ref image)</Label>
              <div onDrop={onDrop} onDragOver={(e)=>e.preventDefault()} className={cn('rounded-lg border border-dashed p-4 text-sm text-muted-foreground', refPreview ? 'bg-muted/50' : 'bg-muted/20')}>
                <div className="flex items-center gap-2">
                  <input id="ref" type="file" accept="image/*" className="hidden" onChange={async (e)=>{ const f = e.target.files?.[0]; if (f) onFilePicked(f) }}/>
                  <Button variant="outline" onClick={()=>document.getElementById('ref')?.click()}><ImageUp className="mr-2 h-4 w-4"/>Выбрать файл</Button>
                  <div>или перетащи сюда</div>
                </div>
                {refPreview && <div className="mt-3"><img src={refPreview} alt="" className="max-h-64 rounded-md border"/></div>}
              </div>
            </div>

            <div className="grid grid-cols-[1fr_auto] items-center gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="ipScale">IP Scale: <b>{ipScale.toFixed(2)}</b></Label>
                <input id="ipScale" type="range" min={0} max={1.5} step={0.05} value={ipScale} onChange={(e)=>setIpScale(Number(e.target.value))} className="w-full accent-primary"/>
              </div>
              <Button variant="ghost" onClick={()=>setIpScale(0.6)}><RotateCcw className="h-4 w-4 mr-2"/>Сброс</Button>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <Button onClick={gen} disabled={busy} className="min-w-[160px]">{busy ? <><Loader2 className="mr-2 h-4 w-4 animate-spin"/>Генерация…</> : 'Сгенерировать'}</Button>
              <Button variant="ghost" onClick={doClear} disabled={busy}>Очистить</Button>
            </div>
            {progress > 0 && <div className="h-2 overflow-hidden rounded bg-muted"><div className="h-full bg-primary transition-all" style={{ width: `${progress}%` }} /></div>}
            {error && <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        <Card>
          <CardHeader><CardTitle>Результат</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="relative flex min-h-[340px] items-center justify-center overflow-hidden rounded-lg border bg-muted/20">
              {imgUrl ? <img src={imgUrl} alt="result" className="max-h-[560px] w-full object-contain" /> : <div className="text-sm text-muted-foreground">Жду генерацию</div>}
              {busy && <div className="absolute inset-0 grid place-items-center bg-background/60 backdrop-blur"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>}
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <a className={cn('underline underline-offset-4', imgUrl ? 'opacity-100' : 'opacity-50 pointer-events-none')} href={imgUrl ?? '#'} target="_blank" rel="noreferrer">Открыть</a>
              <a className={cn('underline underline-offset-4', imgUrl ? 'opacity-100' : 'opacity-50 pointer-events-none')} href={imgUrl ?? '#'} download>Скачать</a>
              {hash && <span className="ml-auto text-xs">hash: {hash}</span>}
            </div>
            {corr?.length ? <div><div className="mb-1 text-sm text-muted-foreground">Исправления промпта (автокоррект):</div><div className="overflow-hidden rounded-md border"><table className="w-full text-sm"><tbody>{corr.map(([a,b], i)=>(<tr key={i} className="border-t first:border-t-0"><td className="p-2 text-red-500">{a}</td><td className="p-2 text-emerald-600">{b}</td></tr>))}</tbody></table></div></div> : null}
          </CardContent>
        </Card>
      </div>
    </motion.div>
  )
}
async function fileToBase64(file: File): Promise<string> { return new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => { const res = String(reader.result || ''); const idx = res.indexOf(','); resolve(idx >= 0 ? res.slice(idx + 1) : res) }; reader.onerror = reject; reader.readAsDataURL(file) }) }
