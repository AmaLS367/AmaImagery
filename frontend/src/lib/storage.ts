const FORM_KEY = 'genai.form.v1'
const HIST_KEY = 'genai.history.v1'
export type FormState = { prompt: string; neg: string; steps: number; guidance: number; width: number; height: number; seed: number | null; ipScale: number }
export type HistoryItem = { prompt: string; path: string; ts: number }
export function saveForm(s: FormState) { try { localStorage.setItem(FORM_KEY, JSON.stringify(s)) } catch {} }
export function loadForm(): Partial<FormState> | null { try { const raw = localStorage.getItem(FORM_KEY); return raw ? JSON.parse(raw) : null } catch { return null } }
export function addHistory(item: HistoryItem) { try { const items = getHistory(); items.unshift(item); localStorage.setItem(HIST_KEY, JSON.stringify(items.slice(0, 500))) } catch {} }
export function getHistory(): HistoryItem[] { try { const raw = localStorage.getItem(HIST_KEY); return raw ? JSON.parse(raw) : [] } catch { return [] } }
