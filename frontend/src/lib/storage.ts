const FORM_KEY = 'amaimagery.form.v1'
const HIST_KEY = 'amaimagery.history.v2'

export type FormState = {
  prompt: string
  neg: string
  steps: number
  guidance: number
  width: number
  height: number
  seed: number | null
  ipScale: number
  style: 'realistic' | 'anime' 
}

export type HistoryItem = {
  prompt: string
  neg: string
  steps: number
  guidance: number
  width: number
  height: number
  seed: number | null
  ipScale: number
  path: string
  ts: number
  tags: string[]
  pinned: boolean
  nsfw: boolean
}

export function saveForm(s: FormState) {
  try { localStorage.setItem(FORM_KEY, JSON.stringify(s)) } catch {}
}

export function loadForm(): Partial<FormState> | null {
  try {
    const raw = localStorage.getItem(FORM_KEY)
    return raw ? JSON.parse(raw) : null
  } catch { return null }
}

function saveHistory(items: HistoryItem[]) {
  try { localStorage.setItem(HIST_KEY, JSON.stringify(items)) } catch {}
}

export function getHistory(): HistoryItem[] {
  try {
    const raw = localStorage.getItem(HIST_KEY)
    if (!raw) return []
    const arr = JSON.parse(raw) as HistoryItem[]
    return Array.isArray(arr) ? arr : []
  } catch { return [] }
}

export function addHistory(item: HistoryItem) {
  const items = getHistory()
  // dedup по пути
  const idx = items.findIndex(x => x.path === item.path)
  if (idx >= 0) items.splice(idx, 1)
  items.unshift(item)
  saveHistory(items.slice(0, 500))
}

export function updateHistory(path: string, patch: Partial<HistoryItem>) {
  const items = getHistory()
  const i = items.findIndex(x => x.path === path)
  if (i < 0) return
  items[i] = { ...items[i], ...patch }
  saveHistory(items)
}

export function togglePin(path: string) {
  const items = getHistory()
  const i = items.findIndex(x => x.path === path)
  if (i < 0) return
  items[i].pinned = !items[i].pinned
  saveHistory(items)
}

export function setTags(path: string, tags: string[]) {
  updateHistory(path, { tags })
}

export function setNSFW(path: string, nsfw: boolean) {
  updateHistory(path, { nsfw })
}
