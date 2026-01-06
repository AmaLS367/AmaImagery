const API_BASE =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL) ||
  'http://127.0.0.1:8000'

function getAccessToken(): string | null {
  try { return localStorage.getItem('access_token') } catch { return null }
}
export function setAccessToken(token: string | null) {
  try {
    if (token) localStorage.setItem('access_token', token)
    else localStorage.removeItem('access_token')
    window.dispatchEvent(new Event('auth:update'))
  } catch {}
}

let refreshPromise: Promise<boolean> | null = null

async function refreshAccessToken(): Promise<boolean> {
  if (refreshPromise) return refreshPromise
  refreshPromise = (async () => {
    const resp = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
    })
    if (!resp.ok) return false
    const data = await resp.json().catch(() => null)
    const token = data && (data.access_token || data.token)
    if (typeof token !== 'string' || token.length === 0) return false

    setAccessToken(token)

    try {
      const raw = localStorage.getItem('auth')
      if (raw) {
        const auth = JSON.parse(raw)
        if (auth && auth.user) {
          auth.user.access_token = token
          auth.user.expires_in = 900
          localStorage.setItem('auth', JSON.stringify(auth))
          window.dispatchEvent(new Event('auth:update'))
        }
      }
    } catch {}

    return true
  })()
  try {
    return await refreshPromise
  } finally {
    refreshPromise = null
  }
}


async function request(path: string, init: RequestInit = {}, retry = true): Promise<Response> {
  const headers = new Headers(init.headers || {})
  const tok = getAccessToken()
  if (tok && !headers.has('Authorization')) headers.set('Authorization', `Bearer ${tok}`)
  if (!headers.has('Content-Type') && init.body && typeof init.body !== 'string') {
    headers.set('Content-Type', 'application/json')
  }

  const url = path.startsWith('http') ? path : `${API_BASE}${path}`

  const resp = await fetch(url, {
    ...init,
    headers,
    credentials: 'include',
  })
  if (resp.status !== 401 || !retry) return resp

  const ok = await refreshAccessToken()
  if (!ok) return resp

  const headers2 = new Headers(init.headers || {})
  const tok2 = getAccessToken()
  if (tok2 && !headers2.has('Authorization')) headers2.set('Authorization', `Bearer ${tok2}`)
  if (!headers2.has('Content-Type') && init.body && typeof init.body !== 'string') {
    headers2.set('Content-Type', 'application/json')
  }

  return fetch(url, {
    ...init,
    headers: headers2,
    credentials: 'include',
  })
}

export const Auth = { setAccessToken }

export type GeneratePayload = {
  prompt: string
  negative_prompt?: string | null
  steps: number
  guidance_scale: number
  width: number
  height: number
  seed: number | null
  ref_image_b64?: string | null
  ip_scale?: number
  style?: 'realistic' | 'anime'
}

export type TaskResp = {
  task_id: string
  status: string
}

export type TaskStatusResp = {
  task_id: string
  status: string
  image_path?: string | null
  image_filename?: string | null
  image_url?: string | null
  exp?: number | null
  sig?: string | null
  metadata?: Record<string, any> | null
  error?: string | null
  created_at?: number | null
  started_at?: number | null
  completed_at?: number | null
}

let headerProvider: (() => Record<string, string>) | null = null

export function configureApiHeaders(fn: () => Record<string, string>) {
  headerProvider = fn
}

function readToken(): string | null {
  try {
    const raw = localStorage.getItem('auth')
    if (!raw) return null
    const obj = JSON.parse(raw)
    return obj?.user?.access_token || obj?.access_token || obj?.token || null
  } catch { return null }
}


// Helper - token
export function getToken(): string | null {
  try {
    const raw = localStorage.getItem('auth')
    if (!raw) return null
    const obj = JSON.parse(raw)
    return obj?.user?.access_token || obj?.access_token || obj?.token || null
  } catch { return null }
}

export function buildHeaders(init?: HeadersInit): HeadersInit {
  const base: Record<string, string> = { 'Content-Type': 'application/json' }

  // нормализуем init → объект
  let fromInit: Record<string, string> = {}
  if (init instanceof Headers) {
    fromInit = Object.fromEntries(init.entries())
  } else if (Array.isArray(init)) {
    fromInit = Object.fromEntries(init)
  } else if (init) {
    fromInit = init as Record<string, string>
  }

  const provided = headerProvider ? headerProvider() : {}
  const token = provided?.Authorization ? null : (getAccessToken() ?? readToken())

  return {
    ...base,
    ...fromInit,
    ...provided,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

export async function api(input: string, init: RequestInit = {}) {
  return request(input, init, true)
}

export async function health(): Promise<boolean> {
  try {
    const r = await fetch(`${API_BASE}/api/v1/health`, { cache: 'no-store', headers: buildHeaders() })
    return r.ok
  } catch { return false }
}

export async function generateJSON(body: GeneratePayload, signal?: AbortSignal): Promise<TaskResp> {
  try {
    const r = await request('/api/v1/images/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal,
    }, true)
    
    if (!r.ok) {
      console.error('Response not OK:', r.status, r.statusText);
      let msg = `HTTP ${r.status}`;
      try { 
        const text = await r.text();
        console.error('Raw error response:', text);
        try {
          const j = JSON.parse(text);
          msg = j.detail || msg;
          console.error('Parsed error response:', j);
        } catch (parseError) {
          console.error('Error parsing JSON response:', parseError);
        }
      } catch (e) {
        console.error('Error reading response:', e);
      }
      throw new Error(msg);
    }
    
    const data = await r.json();
    return data as TaskResp;
  } catch (e) {
    console.error('Request failed:', e);
    throw e;
  }
}

export async function getTaskStatus(task_id: string, signal?: AbortSignal): Promise<TaskStatusResp> {
  try {
    const r = await request(`/api/v1/images/status/${encodeURIComponent(task_id)}`, {
      method: 'GET',
      signal,
    }, true)
    
    if (!r.ok) {
      let msg = `HTTP ${r.status}`;
      try {
        const text = await r.text();
        const j = JSON.parse(text);
        msg = j.detail || msg;
      } catch {
        // ignore parsing errors
      }
      throw new Error(msg);
    }
    
    const data = await r.json().catch(() => null)
    if (!data) {
      throw new Error('Invalid response format')
    }
    
    // Debug logging
    if (data.status === 'queued') {
      const age = data.created_at ? Date.now() - (data.created_at * 1000) : 0
      console.warn(`Task ${task_id} still queued after ${age}ms`, data)
    }
    
    return data as TaskStatusResp
  } catch (e) {
    console.error('Failed to get task status:', e);
    throw e;
  }
}

// Экспорт функций под личные ручки
export type GenerationItem = {
  id: string
  image_path: string
  prompt: any
  params: any
  created_at: string
  exp?: number
  sig?: string
}

export async function listMyGenerations(limit = 50, offset = 0) {
  const q = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  const r = await request(`/api/v1/users/me/generations?${q.toString()}`)
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  return r.json()
}

export async function getMySettings() {
  const r = await request(`/api/v1/users/me/settings`)
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  return r.json()
}

export async function patchMySettings(payload: any) {
  const r = await request(`/api/v1/users/me/settings`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: payload }),
  })
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  return r.json()
}




