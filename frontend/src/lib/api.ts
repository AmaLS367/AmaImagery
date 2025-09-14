const API_BASE =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL) ||
  (typeof window !== 'undefined' ? `${window.location.origin}` : 'http://127.0.0.1:8000')

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

async function refreshAccessToken(): Promise<boolean> {
  const resp = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    credentials: 'include',
  })
  if (!resp.ok) return false
  try {
    const data = await resp.json()
    const token = (data && (data.access_token || data.token)) || null
    if (typeof token === 'string' && token.length > 0) {
      setAccessToken(token)
      return true
    }
  } catch {}
  return false
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

export type GenerateResponse = {
  path: string
  prompt_hash?: string
  corrections?: Array<[string, string]>
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
    const r = await fetch(`${API_BASE}/health`, { cache: 'no-store', headers: buildHeaders() })
    return r.ok
  } catch { return false }
}

export async function generateJSON(body: GeneratePayload, signal?: AbortSignal): Promise<GenerateResponse> {
  const url = `${API_BASE}/generate`;
  const headers = buildHeaders();
  const requestBody = JSON.stringify(body);
  
  console.log('Making request to:', url);
  console.log('With headers:', headers);
  console.log('With body:', requestBody);
  
  try {
    console.log('Starting fetch request...');
    const r = await request('/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }, true)
    
    console.log('Response status:', r.status);
    
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
    console.log('Response data:', data);
    return data;
  } catch (e) {
    console.error('Request failed:', e);
    throw e;
  }
}

// Экспорт функций под личные ручки
export type GenerationItem = { id: string; image_path: string; prompt: any; params: any; created_at: string }

export async function listMyGenerations(limit = 50, offset = 0) {
  const q = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  const r = await request(`/users/me/generations?${q.toString()}`)
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  return r.json()
}

export async function getMySettings() {
  const r = await request(`/users/me/settings`)
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  return r.json()
}

export async function patchMySettings(payload: any) {
  const r = await request(`/users/me/settings`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  return r.json()
}



