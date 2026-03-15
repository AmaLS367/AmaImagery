import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Clock3, RefreshCw, Search, TriangleAlert, Layers } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

import { listMyGenerations, toAssetUrl, type GenerationItem } from '../lib/api'
import { appRoutes } from '../lib/routes'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { MetaPill, SurfacePanel } from '../components/ui/foundation'
import { EditorialFrame } from '../components/editorial/EditorialFrame'
import { cn } from '../lib/utils'
import { useSettings } from '../providers/SettingsProvider'
import { useAuth } from '../providers/AuthProvider'
import { getHistory, type HistoryItem } from '../lib/storage'

type RatioKey = 'any' | '1:1' | '3:4' | '4:3' | '9:16' | '16:9' | '4:5'
type CfgKey = 'any' | 'lt6' | '6-8' | 'gt8'
type HistoryRecord = {
  id: string
  imageUrl: string | null
  promptText: string
  guidance: number | null
  steps: number | null
  providerName: string | null
  createdAtLabel: string
  createdAtSource: number
  ratio: string
}

const LIMIT = 50

function ratioMatch(item: HistoryRecord, ratio: RatioKey) {
  if (ratio === 'any') return true
  return item.ratio === ratio
}

function cfgMatch(item: HistoryRecord, cfg: CfgKey) {
  if (cfg === 'any') return true
  const guidance = Number(item.guidance ?? 7)
  if (cfg === 'lt6') return guidance < 6
  if (cfg === '6-8') return guidance >= 6 && guidance <= 8
  return guidance > 8
}

function formatRatio(width: number, height: number) {
  if (!width || !height) return 'Unknown'

  const gcd = (left: number, right: number): number => (right === 0 ? left : gcd(right, left % right))
  const divisor = gcd(width, height)
  const ratio = `${width / divisor}:${height / divisor}`

  if (ratio === '5:4') return '4:5'
  return ratio
}

function buildBackendImageUrl(item: GenerationItem) {
  if (item.image_url) return toAssetUrl(item.image_url)

  const filename = item.image_filename || String(item.image_path || '').split(/[\\/]/).pop() || ''
  if (!filename) return null

  const query = new URLSearchParams({ path: filename })
  if (typeof item.exp === 'number') {
    query.set('exp', String(item.exp))
  }
  if (typeof item.sig === 'string' && item.sig.length > 0) {
    query.set('sig', item.sig)
  }

  return toAssetUrl(`/api/v1/file?${query.toString()}`)
}

function formatTimestamp(value: string | number) {
  const date = typeof value === 'number' ? new Date(value) : new Date(value)
  return date.toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function adaptBackendItem(item: GenerationItem): HistoryRecord {
  const width = Number(item.params?.width ?? 0)
  const height = Number(item.params?.height ?? 0)

  return {
    id: item.id,
    imageUrl: buildBackendImageUrl(item),
    promptText: typeof item.prompt?.prompt === 'string' ? item.prompt.prompt : 'Untitled Result',
    guidance: Number.isFinite(Number(item.params?.guidance_scale)) ? Number(item.params?.guidance_scale) : null,
    steps: Number.isFinite(Number(item.params?.steps)) ? Number(item.params?.steps) : null,
    providerName: typeof item.provider_name === 'string' && item.provider_name.length > 0 ? item.provider_name : 'Unknown provider',
    createdAtLabel: formatTimestamp(item.created_at),
    createdAtSource: new Date(item.created_at).getTime(),
    ratio: formatRatio(width, height),
  }
}

function adaptLocalItem(item: HistoryItem, index: number): HistoryRecord {
  const filename = String(item.path || '').split(/[\\/]/).pop() || ''
  const query = new URLSearchParams({ path: filename })
  if (typeof item.exp === 'number') query.set('exp', String(item.exp))
  if (typeof item.sig === 'string' && item.sig.length > 0) query.set('sig', item.sig)

  return {
    id: `${item.path}-${item.ts}-${index}`,
    imageUrl: filename ? toAssetUrl(`/api/v1/file?${query.toString()}`) : null,
    promptText: item.prompt || 'Untitled Result',
    guidance: item.guidance,
    steps: item.steps,
    providerName: 'Local session',
    createdAtLabel: formatTimestamp(item.ts),
    createdAtSource: item.ts,
    ratio: formatRatio(item.width, item.height),
  }
}

export default function History() {
  const { settings } = useSettings()
  const { status: authStatus, isAuthenticated } = useAuth()
  const [items, setItems] = useState<HistoryRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [broken, setBroken] = useState<Record<string, true>>({})

  const [query, setQuery] = useState('')
  const [ratio, setRatio] = useState<RatioKey>('any')
  const [cfg, setCfg] = useState<CfgKey>('any')

  async function load() {
    if (authStatus === 'loading') return

    setLoading(true)
    setError(null)

    try {
      if (isAuthenticated) {
        const response = await listMyGenerations(LIMIT, 0)
        setItems(response.items.map(adaptBackendItem))
      } else {
        const localItems = getHistory()
          .slice(0, LIMIT)
          .map(adaptLocalItem)
          .sort((left, right) => right.createdAtSource - left.createdAtSource)
        setItems(localItems)
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to load history.')
      setItems([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [authStatus, isAuthenticated])

  const filtered = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()

    return items.filter((item) => {
      const promptText = item.promptText.toLowerCase()
      return (
        (!normalizedQuery || promptText.includes(normalizedQuery)) &&
        ratioMatch(item, ratio) &&
        cfgMatch(item, cfg)
      )
    })
  }, [items, query, ratio, cfg])

  const empty = !loading && !error && items.length === 0
  const filteredEmpty = !loading && !error && items.length > 0 && filtered.length === 0

  return (
    <EditorialFrame
      eyebrow="History"
      title={settings.visualMode === 'cinematic' ? 'A runtime archive with every decision still visible.' : 'A deep archive of your creative evolution.'}
      summary={settings.visualMode === 'editorial'
        ? 'Search by prompt, ratio, and CFG while the archive stays spacious, readable, and metadata-rich.'
        : 'Search by prompt, filter by metadata, and reconstruct past results with pixel-perfect fidelity.'}
      pills={[`${items.length} Generations`, 'Searchable', 'Metadata-rich']}
    >
      <div className="history-mode-shell grid gap-12 xl:grid-cols-[1fr_380px] items-start">
        <div className="space-y-10">
          {/* Controls */}
          <SurfacePanel className="p-6 flex flex-wrap items-center gap-4">
            <div className="relative min-w-[260px] flex-1">
              <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/40" />
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search generations..."
                className="pl-11 h-12 rounded-full border-border bg-secondary/50"
              />
            </div>

            <div className="flex items-center gap-3">
              <select
                value={ratio}
                onChange={(event) => setRatio(event.target.value as RatioKey)}
                className="h-12 rounded-full border border-border bg-secondary/50 px-6 text-sm font-bold text-foreground/70 outline-none focus:border-primary/50 transition-colors"
              >
                <option value="any">Any Ratio</option>
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
                className="h-12 rounded-full border border-border bg-secondary/50 px-6 text-sm font-bold text-foreground/70 outline-none focus:border-primary/50 transition-colors"
              >
                <option value="any">Any CFG</option>
                <option value="lt6">CFG &lt; 6</option>
                <option value="6-8">CFG 6-8</option>
                <option value="gt8">CFG &gt; 8</option>
              </select>

              <Button variant="outline" size="icon" className="h-12 w-12 rounded-full border-border" onClick={load} disabled={loading}>
                <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
              </Button>
            </div>
          </SurfacePanel>

          {/* Grid */}
          <div className="space-y-6">
            <AnimatePresence mode="popLayout">
              {loading && !items.length ? (
                <motion.div 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="grid gap-6 md:grid-cols-2 lg:grid-cols-3"
                >
                  {Array.from({ length: 6 }).map((_, index) => (
                    <div key={index} className="h-[400px] animate-pulse rounded-[32px] bg-secondary/50 border border-border" />
                  ))}
                </motion.div>
              ) : empty ? (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="py-20"
                >
                  <SurfacePanel className="p-12 text-center space-y-6 max-w-lg mx-auto">
                    <div className="h-20 w-20 rounded-3xl bg-primary/10 flex items-center justify-center text-primary mx-auto">
                      <Layers className="h-10 w-10" />
                    </div>
                    <div className="space-y-2">
                      <h2 className="font-display text-3xl font-bold tracking-tight text-foreground dark:text-white">No generations yet</h2>
                      <p className="text-foreground/60 dark:text-white/60 font-medium">Your creative journey starts here. Launch the studio to create your first masterpiece.</p>
                    </div>
                    <Button asChild size="lg" className="h-14 px-10 rounded-full font-bold">
                      <Link to={appRoutes.generate}>Create your first image</Link>
                    </Button>
                  </SurfacePanel>
                </motion.div>
              ) : filteredEmpty ? (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="py-20"
                >
                  <SurfacePanel className="p-12 text-center space-y-4 max-w-lg mx-auto">
                    <div className="h-16 w-16 rounded-full bg-secondary flex items-center justify-center mx-auto dark:bg-white/5">
                      <Search className="h-8 w-8 text-foreground/20" />
                    </div>
                    <h2 className="font-display text-2xl font-bold text-foreground dark:text-white">No results found</h2>
                    <p className="text-foreground/60 dark:text-white/60 font-medium">Try adjusting your search query or filters.</p>
                    <Button variant="ghost" onClick={() => { setQuery(''); setRatio('any'); setCfg('any'); }} className="font-bold">
                      Clear all filters
                    </Button>
                  </SurfacePanel>
                </motion.div>
              ) : (
                <motion.div 
                  layout
                  className="grid gap-6 md:grid-cols-2 lg:grid-cols-3"
                >
                  {filtered.map((item) => {
                    if (broken[item.id]) return null
                    const stepsText = item.steps == null ? '—' : String(item.steps)
                    const modelText = item.providerName || 'Unknown provider'
                    const imageUrl = item.imageUrl

                    return (
                      <motion.article 
                        key={item.id} 
                        layout
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                        className="group overflow-hidden rounded-[32px] border border-border bg-card shadow-sm hover:border-primary/30 transition-all dark:border-white/10 dark:bg-white/5"
                      >
                        <div className="relative h-64 overflow-hidden bg-secondary dark:bg-black/20">
                          {imageUrl ? (
                            <img
                              src={item.imageUrl || undefined}
                              alt=""
                              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
                              loading="lazy"
                              onError={() => setBroken((current) => ({ ...current, [item.id]: true }))}
                            />
                          ) : (
                            <div className="flex h-full items-center justify-center">
                               <Layers className="h-10 w-10 text-foreground/10" />
                            </div>
                          )}
                          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                          <div className="absolute bottom-4 left-4 right-4 flex justify-between items-end opacity-0 group-hover:opacity-100 transition-all translate-y-2 group-hover:translate-y-0">
                             <div className="flex gap-2">
                                <MetaPill className="bg-black/40 border-white/10 text-white backdrop-blur-md">{item.ratio}</MetaPill>
                             </div>
                          </div>
                        </div>
                        <div className="p-6 space-y-4">
                          <div className="font-bold text-foreground line-clamp-2 leading-relaxed dark:text-white group-hover:text-primary transition-colors">
                            {item.promptText}
                          </div>
                          <div className="grid grid-cols-2 gap-4 text-[10px] font-black uppercase tracking-widest text-foreground/40 dark:text-white/40">
                            <div className="space-y-1">
                               <div className="text-primary/60">Guidance</div>
                               <div className="text-foreground dark:text-white/70">{item.guidance == null ? '—' : item.guidance.toFixed(1)}</div>
                            </div>
                            <div className="space-y-1">
                               <div className="text-primary/60">Steps</div>
                               <div className="text-foreground dark:text-white/70">{stepsText}</div>
                            </div>
                            <div className="space-y-1">
                               <div className="text-primary/60">Model</div>
                               <div className="text-foreground dark:text-white/70 truncate">{modelText}</div>
                            </div>
                            <div className="space-y-1">
                               <div className="text-primary/60">Date</div>
                               <div className="text-foreground dark:text-white/70">{item.createdAtLabel}</div>
                            </div>
                          </div>
                        </div>
                      </motion.article>
                    )
                  })}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Sidebar */}
        <aside className="space-y-8 sticky top-24">
          <SurfacePanel className="p-8 space-y-6">
            <div className="space-y-2">
              <h3 className="font-display text-2xl font-bold tracking-tight text-foreground dark:text-white">Archive Status</h3>
              <p className="text-sm text-foreground/60 dark:text-white/60 font-medium leading-relaxed">
                Your history is currently synchronized with the studio runtime.
              </p>
            </div>
            
            <div className="space-y-4">
               <div className="flex items-center justify-between p-4 rounded-2xl bg-secondary/50 border border-border dark:bg-white/5 dark:border-white/10">
                  <div className="flex items-center gap-3">
                     <div className="h-2 w-2 rounded-full bg-success shadow-[0_0_10px_theme(colors.success.DEFAULT)]" />
                     <span className="text-xs font-bold uppercase tracking-widest text-foreground/70 dark:text-white/70">Connected</span>
                  </div>
                  <RefreshCw className={cn("h-3.5 w-3.5 text-foreground/30", loading && "animate-spin")} />
               </div>
               
               <div className="space-y-2">
                  <div className="flex justify-between text-[10px] font-black uppercase tracking-[0.2em] text-foreground/40 dark:text-white/40 px-1">
                     <span>Storage Capacity</span>
                     <span>{Math.min(100, Math.round((items.length / LIMIT) * 100))}%</span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-secondary overflow-hidden dark:bg-white/5">
                     <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: `${(items.length / LIMIT) * 100}%` }}
                        className="h-full bg-primary rounded-full shadow-glow" 
                     />
                  </div>
               </div>
            </div>
          </SurfacePanel>

          {error && (
            <SurfacePanel className="p-8 border-danger/20 bg-danger/5 space-y-6">
              <div className="flex items-center gap-3 text-danger">
                <TriangleAlert className="h-6 w-6" />
                <h3 className="font-display text-xl font-bold">Sync Error</h3>
              </div>
              <p className="text-sm text-danger/80 font-medium leading-relaxed">
                {error}
              </p>
              <Button variant="outline" onClick={load} className="w-full rounded-full border-danger/30 text-danger hover:bg-danger/10">
                Retry Connection
              </Button>
            </SurfacePanel>
          )}

          <SurfacePanel className="p-8 space-y-6">
             <div className="flex items-center gap-3">
                <Clock3 className="h-5 w-5 text-primary" />
                <h3 className="font-display text-xl font-bold text-foreground dark:text-white">Sync Metadata</h3>
             </div>
             <div className="space-y-4">
                {filtered.slice(0, 4).map(item => (
                  <div key={item.id} className="flex items-center justify-between gap-4 text-[10px] font-bold border-b border-border pb-3 dark:border-white/5 last:border-0 last:pb-0">
                    <span className="text-foreground/40 dark:text-white/40 truncate flex-1">{item.promptText}</span>
                    <span className="text-primary shrink-0">{item.createdAtLabel}</span>
                  </div>
                ))}
                {filtered.length === 0 && (
                  <p className="text-[10px] font-bold text-foreground/30 uppercase tracking-widest italic">No matching metadata</p>
                )}
             </div>
          </SurfacePanel>
        </aside>
      </div>
    </EditorialFrame>
  )
}
