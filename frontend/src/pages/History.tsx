import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Clock3, RefreshCw, Search, TriangleAlert } from 'lucide-react'

import { listMyGenerations, type GenerationItem } from '../lib/api'
import { appRoutes } from '../lib/routes'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { MetaPill, SectionEyebrow, SurfacePanel } from '../components/ui/foundation'

type RatioKey = 'any' | '1:1' | '3:4' | '4:3' | '9:16' | '16:9' | '4:5'
type CfgKey = 'any' | 'lt6' | '6-8' | 'gt8'

const LIMIT = 50

function ratioMatch(item: GenerationItem, ratio: RatioKey) {
  if (ratio === 'any') return true
  return formatRatio(item) === ratio
}

function cfgMatch(item: GenerationItem, cfg: CfgKey) {
  if (cfg === 'any') return true
  const guidance = Number(item.params?.guidance_scale ?? 7)
  if (cfg === 'lt6') return guidance < 6
  if (cfg === '6-8') return guidance >= 6 && guidance <= 8
  return guidance > 8
}

function formatRatio(item: GenerationItem) {
  const width = Number(item.params?.width ?? 0)
  const height = Number(item.params?.height ?? 0)
  if (!width || !height) return 'Unknown'

  const gcd = (left: number, right: number): number => (right === 0 ? left : gcd(right, left % right))
  const divisor = gcd(width, height)
  const ratio = `${width / divisor}:${height / divisor}`

  if (ratio === '5:4') return '4:5'
  return ratio
}

function buildImageUrl(item: GenerationItem) {
  if (item.image_url) return item.image_url
  const name = String(item.image_path || '').split(/[\\/]/).pop() || ''
  if (!name || typeof item.exp !== 'number' || typeof item.sig !== 'string' || item.sig.length === 0) return null
  return `/api/v1/file?path=${encodeURIComponent(name)}&exp=${String(item.exp)}&sig=${encodeURIComponent(item.sig)}`
}

function formatTimestamp(value: string) {
  const date = new Date(value)
  return date.toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function History() {
  const [items, setItems] = useState<GenerationItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [broken, setBroken] = useState<Record<string, true>>({})

  const [query, setQuery] = useState('')
  const [ratio, setRatio] = useState<RatioKey>('any')
  const [cfg, setCfg] = useState<CfgKey>('6-8')

  async function load() {
    setLoading(true)
    setError(null)

    try {
      const response = await listMyGenerations(LIMIT, 0)
      setItems(response.items)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to load history.')
      setItems([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const filtered = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()

    return items.filter((item) => {
      const promptText = String(item.prompt?.prompt ?? '').toLowerCase()
      return (
        (!normalizedQuery || promptText.includes(normalizedQuery)) &&
        ratioMatch(item, ratio) &&
        cfgMatch(item, cfg)
      )
    })
  }, [items, query, ratio, cfg])

  const filteredRows = filtered.slice(0, 5)
  const empty = !loading && !error && items.length === 0
  const filteredEmpty = !loading && !error && items.length > 0 && filtered.length === 0

  return (
    <section className="page-shell space-y-6 py-8 xl:py-10">
      <SurfacePanel glass className="space-y-5 p-6 md:p-8">
        <SectionEyebrow>History</SectionEyebrow>
        <div className="space-y-4">
          <h1 className="font-display text-4xl font-semibold tracking-[-0.06em] text-foreground sm:text-5xl">
            Searchable history with filters, metadata, and explicit state handling.
          </h1>
          <p className="max-w-3xl text-base leading-7 text-muted-foreground">
            Search by prompt excerpt, filter by ratio and CFG band, and keep loading, empty, error, and filtered
            feedback readable inside the same archive screen.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <MetaPill>Search</MetaPill>
          <MetaPill>Ratio</MetaPill>
          <MetaPill>CFG</MetaPill>
          <MetaPill>Refresh</MetaPill>
        </div>
      </SurfacePanel>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.05fr)_420px]">
        <SurfacePanel className="space-y-6 p-6 md:p-8">
          <div className="text-sm font-semibold text-foreground">History / Populated / Dark</div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="relative min-w-[260px] flex-1">
              <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search prompt text"
                className="pl-11"
              />
            </div>

            <select
              value={ratio}
              onChange={(event) => setRatio(event.target.value as RatioKey)}
              className="h-12 rounded-[18px] border border-border/70 bg-card/85 px-4 text-sm shadow-panel"
            >
              <option value="any">Any ratio</option>
              <option value="1:1">1:1</option>
              <option value="3:4">3:4</option>
              <option value="4:3">4:3</option>
              <option value="4:5">4:5</option>
              <option value="9:16">9:16</option>
              <option value="16:9">16:9</option>
            </select>

            <select
              value={cfg}
              onChange={(event) => setCfg(event.target.value as CfgKey)}
              className="h-12 rounded-[18px] border border-border/70 bg-card/85 px-4 text-sm shadow-panel"
            >
              <option value="any">Any CFG</option>
              <option value="lt6">CFG &lt; 6</option>
              <option value="6-8">CFG 6-8</option>
              <option value="gt8">CFG &gt; 8</option>
            </select>

            <Button variant="secondary" onClick={load} disabled={loading}>
              {loading ? 'Refreshing…' : 'Refresh'}
            </Button>
          </div>

          {loading && !items.length ? (
            <div className="grid gap-4 md:grid-cols-3">
              {Array.from({ length: 3 }).map((_, index) => (
                <div key={index} className="h-[320px] animate-pulse rounded-[28px] bg-card/55" />
              ))}
            </div>
          ) : null}

          {empty ? (
            <SurfacePanel className="rounded-[28px] p-6 shadow-none">
              <div className="space-y-3">
                <h2 className="font-display text-[28px] font-semibold tracking-[-0.05em]">No generations yet</h2>
                <p className="text-sm leading-6 text-muted-foreground">
                  Your history will appear here after the first completed run. You can search, filter by ratio, and
                  revisit metadata later.
                </p>
                <Button asChild>
                  <Link to={appRoutes.generate}>Create your first image</Link>
                </Button>
              </div>
            </SurfacePanel>
          ) : null}

          {filteredEmpty ? (
            <SurfacePanel className="rounded-[28px] p-6 shadow-none">
              <div className="space-y-3">
                <h2 className="font-display text-[28px] font-semibold tracking-[-0.05em]">No results for current filters</h2>
                <p className="text-sm leading-6 text-muted-foreground">
                  Clear the prompt query or broaden the ratio and CFG filters to bring archive items back into view.
                </p>
              </div>
            </SurfacePanel>
          ) : null}

          {!loading && filtered.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-3">
              {filtered.slice(0, 6).map((item) => {
                if (broken[item.id]) return null

                const imageUrl = buildImageUrl(item)
                const promptText = String(item.prompt?.prompt ?? '')
                const params = item.params || {}

                return (
                  <article key={item.id} className="overflow-hidden rounded-[28px] border border-border/60 bg-[#09121c] text-white shadow-panel">
                    <div className="relative h-52 overflow-hidden border-b border-white/5 bg-[radial-gradient(circle_at_top_left,rgba(250,204,21,0.12),transparent_25%),radial-gradient(circle_at_top_right,rgba(14,165,233,0.12),transparent_24%),linear-gradient(180deg,#0a1624,#08111a)]">
                      {imageUrl ? (
                        <img
                          src={imageUrl}
                          alt=""
                          className="h-full w-full object-cover"
                          loading="lazy"
                          decoding="async"
                          onError={() => setBroken((current) => ({ ...current, [item.id]: true }))}
                        />
                      ) : null}
                    </div>
                    <div className="space-y-3 p-4">
                      <div className="font-medium text-white/90">{promptText || 'Untitled result'}</div>
                      <div className="space-y-1 text-xs leading-5 text-white/58">
                        <div>
                          {formatRatio(item)} · CFG {Number(params.guidance_scale ?? 0).toFixed(1)} · {String(params.steps ?? '—')} steps · Seed{' '}
                          {String(params.seed ?? 'Auto')}
                        </div>
                        <div>
                          Model {item.provider_name || 'AmaFusion'} · {formatTimestamp(item.created_at)}
                        </div>
                      </div>
                    </div>
                  </article>
                )
              })}
            </div>
          ) : null}
        </SurfacePanel>

        <div className="space-y-6">
          <SurfacePanel className="space-y-4 p-6">
            <div className="text-sm font-semibold text-foreground">History / Loading / Light</div>
            <p className="text-sm leading-6 text-muted-foreground">
              {loading ? 'Refreshing generation records and metadata…' : 'Search, filter, and refresh remain visible while the archive changes state.'}
            </p>
          </SurfacePanel>

          <SurfacePanel className="space-y-4 p-6">
            <div className="text-sm font-semibold text-foreground">History / Empty / Dark</div>
            <h2 className="font-display text-[28px] font-semibold tracking-[-0.05em]">No generations yet</h2>
            <p className="text-sm leading-6 text-muted-foreground">
              Your history will appear here after the first completed run. You can search, filter by ratio, and revisit
              metadata later.
            </p>
            <Button asChild>
              <Link to={appRoutes.generate}>Create your first image</Link>
            </Button>
          </SurfacePanel>

          <SurfacePanel className="space-y-4 p-6">
            <div className="text-sm font-semibold text-foreground">History / Error / Dark</div>
            <div className="flex items-center gap-3">
              <TriangleAlert className="h-5 w-5 text-danger" />
              <h2 className="font-display text-[28px] font-semibold tracking-[-0.05em]">Failed to load history</h2>
            </div>
            <p className="text-sm leading-6 text-muted-foreground">
              {error || 'The request could not complete. Retry now or verify your session.'}
            </p>
            <div className="flex flex-wrap gap-3">
              <Button variant="secondary" onClick={load}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh again
              </Button>
              <Button asChild variant="outline">
                <Link to={appRoutes.login}>Sign in again</Link>
              </Button>
            </div>
          </SurfacePanel>

          <SurfacePanel className="space-y-4 p-6">
            <div className="text-sm font-semibold text-foreground">History / Filtered Results / Light</div>
            {filteredRows.length ? (
              <div className="overflow-hidden rounded-[24px] border border-border/60">
                <table className="w-full text-left text-sm">
                  <thead className="bg-card/70 text-xs uppercase tracking-[0.22em] text-muted-foreground">
                    <tr>
                      <th className="px-4 py-3">Prompt excerpt</th>
                      <th className="px-4 py-3">Ratio</th>
                      <th className="px-4 py-3">CFG</th>
                      <th className="px-4 py-3">Steps</th>
                      <th className="px-4 py-3">Seed</th>
                      <th className="px-4 py-3">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRows.map((item) => (
                      <tr key={item.id} className="border-t border-border/60">
                        <td className="px-4 py-3 text-foreground">{String(item.prompt?.prompt ?? '').slice(0, 48) || 'Untitled prompt'}</td>
                        <td className="px-4 py-3 text-muted-foreground">{formatRatio(item)}</td>
                        <td className="px-4 py-3 text-muted-foreground">{Number(item.params?.guidance_scale ?? 0).toFixed(1)}</td>
                        <td className="px-4 py-3 text-muted-foreground">{String(item.params?.steps ?? '—')}</td>
                        <td className="px-4 py-3 text-muted-foreground">{String(item.params?.seed ?? 'Auto')}</td>
                        <td className="px-4 py-3 text-muted-foreground">{formatTimestamp(item.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="flex items-center gap-3 rounded-[24px] border border-border/60 bg-card/55 px-4 py-5 text-sm text-muted-foreground">
                <Clock3 className="h-4 w-4" />
                Filtered metadata will appear here once results match the current search.
              </div>
            )}
          </SurfacePanel>
        </div>
      </div>
    </section>
  )
}
