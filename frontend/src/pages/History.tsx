import { useEffect, useMemo, useState } from 'react'
import { listMyGenerations, type GenerationItem } from '../lib/api'
import { Button } from '../components/ui/button'
import { useTranslation } from 'react-i18next'

type RatioKey = 'any' | '1:1' | '3:4' | '4:3' | '9:16' | '16:9'
type CfgKey = 'any' | 'lt6' | '6-8' | 'gt8'

const LIMIT = 50

function ratioMatch(it: GenerationItem, r: RatioKey) {
  if (r === 'any') return true
  const w = Number(it.params?.width ?? 0)
  const h = Number(it.params?.height ?? 1)
  const norm = (a: number, b: number) => (a / b).toFixed(3)
  const map: Record<Exclude<RatioKey, 'any'>, string> = {
    '1:1': norm(1, 1),
    '3:4': norm(3, 4),
    '4:3': norm(4, 3),
    '9:16': norm(9, 16),
    '16:9': norm(16, 9),
  }
  return norm(w, h) === map[r]
}

function cfgMatch(it: GenerationItem, cfg: CfgKey) {
  if (cfg === 'any') return true
  const g = Number(it.params?.guidance_scale ?? 7)
  if (cfg === 'lt6') return g < 6
  if (cfg === '6-8') return g >= 6 && g <= 8
  return g > 8
}

export default function History() {
  const [items, setItems] = useState<GenerationItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [broken, setBroken] = useState<Record<string, true>>({})

  // Фильтры
  const [q, setQ] = useState('')
  const [ratio, setRatio] = useState<RatioKey>('any')
  const [cfg, setCfg] = useState<CfgKey>('any')

  // Translate
  const { t } = useTranslation()

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const { items } = await listMyGenerations(LIMIT, 0)
      setItems(items)
    } catch (e: any) {
      setError(e?.message || t('history:errorLoading'))
      setItems([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const filtered = useMemo(() => {
    const query = q.trim().toLowerCase()
    const byText = (it: GenerationItem) => {
      if (!query) return true
      const txt = String(it.prompt?.prompt ?? '')
      return txt.toLowerCase().includes(query)
    }
    return items.filter((it) => byText(it) && ratioMatch(it, ratio) && cfgMatch(it, cfg))
  }, [items, q, ratio, cfg])

  return (
    <div className="space-y-4">
      {/* Панель фильтров */}
      <div className="flex flex-wrap items-center gap-3">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={t('history:filterPlaceholder')}
          className="h-10 w-full sm:w-72 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />

        <select
          value={ratio}
          onChange={(e) => setRatio(e.target.value as RatioKey)}
          className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <option value="any">{t('history:ratioAny')}</option>
          <option value="1:1">1:1</option>
          <option value="3:4">3:4</option>
          <option value="4:3">4:3</option>
          <option value="9:16">9:16</option>
          <option value="16:9">16:9</option>
        </select>

        <select
          value={cfg}
          onChange={(e) => setCfg(e.target.value as CfgKey)}
          className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <option value="any">{t('history:cfgAny')}</option>
          <option value="lt6">CFG &lt; 6</option>
          <option value="6-8">CFG 6–8</option>
          <option value="gt8">CFG &gt; 8</option>
        </select>

        <Button
          onClick={load}
          variant="secondary"
          className="ml-auto h-10"
          disabled={loading}
        >
          {loading ? t('history:refreshing') : t('history:refresh')}
        </Button>
      </div>

      {/* Состояния */}
      {error && (
        <div className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      {loading && !items.length && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-72 animate-pulse rounded-xl bg-muted/30" />
          ))}
        </div>
      )}

      {/* Список */}
      {!loading && !filtered.length ? (
        <div className="text-sm text-muted-foreground">{t('history:empty')}</div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((it) => {
            if (broken[it.id]) return null

            const direct = (it as any).image_url
            const name = String(it.image_path || '').split(/[\\/]/).pop() || ''
            const hasSig = typeof (it as any).exp === 'number' && typeof (it as any).sig === 'string' && (it as any).sig.length > 0

            const imgUrl =
              (typeof direct === 'string' && direct.length > 0)
                ? direct
                : (hasSig
                    ? `/api/v1/file?path=${encodeURIComponent(name)}&exp=${String((it as any).exp)}&sig=${encodeURIComponent(String((it as any).sig))}`
                    : `/api/v1/file?path=${encodeURIComponent(name)}`)
            const promptTxt = String(it.prompt?.prompt ?? '')
            const p = it.params || {}

            return (
              <div key={it.id} className="overflow-hidden rounded-xl border bg-card text-card-foreground">
                {imgUrl ? (
                  <a href={imgUrl} target="_blank" rel="noreferrer">
                    <img
                      src={imgUrl}
                      alt=""
                      className="h-56 w-full object-cover"
                      loading="lazy"
                      decoding="async"
                      onError={() => setBroken((prev) => ({ ...prev, [it.id]: true }))}
                    />
                  </a>
                ) : null}

                <div className="space-y-2 p-3">
                  <div className="line-clamp-3 text-sm text-muted-foreground">{promptTxt}</div>

                  <div className="flex flex-wrap gap-2 text-xs">
                    <span className="rounded-md bg-muted/50 px-2 py-1">{t('history:badges.wxh')} {p.width}×{p.height}</span>
                    {'guidance_scale' in p && <span className="rounded-md bg-muted/50 px-2 py-1">CFG: {p.guidance_scale}</span>}
                    {'steps' in p && <span className="rounded-md bg-muted/50 px-2 py-1">{t('history:badges.steps')} {p.steps}</span>}
                    {'seed' in p && p.seed != null && <span className="rounded-md bg-muted/50 px-2 py-1">{t('history:badges.seed')} {p.seed}</span>}
                    {'model_id' in p && p.model_id && <span className="rounded-md bg-muted/50 px-2 py-1">{t('history:badges.model')} {String(p.model_id).split('/').pop() || String(p.model_id)}</span>}
                  </div>

                  <div className="text-[11px] text-muted-foreground/80">
                    {new Date(it.created_at).toLocaleString()}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
