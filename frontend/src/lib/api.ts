type ApiRequestOptions = {
  retryOn401?: boolean
}

type AuthUserRecord = {
  id: string
  email: string
  username: string
  settings: Record<string, unknown>
}

type ApiErrorObject = {
  message?: unknown
  code?: unknown
  details?: unknown
}

const API_BASE =
  typeof import.meta !== 'undefined' && typeof import.meta.env?.VITE_API_URL === 'string'
    ? import.meta.env.VITE_API_URL.trim()
    : ''

let headerProvider: (() => Record<string, string>) | null = null
let compatibilityAccessToken: string | null = null
let refreshPromise: Promise<boolean> | null = null

function normalizeBaseUrl(url: string): string {
  return url.replace(/\/+$/, '')
}

function normalizePath(path: string): string {
  if (/^[a-z]+:\/\//i.test(path) || path.startsWith('blob:') || path.startsWith('data:')) {
    return path
  }

  if (!path.startsWith('/')) {
    return `/${path}`
  }

  return path
}

function hasJsonBody(body: BodyInit | null | undefined): boolean {
  if (!body) return false
  if (typeof body === 'string') return false
  if (typeof FormData !== 'undefined' && body instanceof FormData) return false
  if (typeof URLSearchParams !== 'undefined' && body instanceof URLSearchParams) return false
  if (typeof Blob !== 'undefined' && body instanceof Blob) return false
  if (typeof ArrayBuffer !== 'undefined' && body instanceof ArrayBuffer) return false
  if (typeof ReadableStream !== 'undefined' && body instanceof ReadableStream) return false
  return true
}

function readLegacyStoredToken(): string | null {
  try {
    const direct = localStorage.getItem('access_token')
    if (direct) return direct

    const raw = localStorage.getItem('auth')
    if (!raw) return null

    const parsed = JSON.parse(raw)
    return parsed?.user?.access_token || parsed?.access_token || parsed?.token || null
  } catch {
    return null
  }
}

function getCompatibilityToken(): string | null {
  return compatibilityAccessToken ?? readLegacyStoredToken()
}

function buildRequestHeaders(init: RequestInit = {}): Headers {
  const headers = new Headers()

  const provided = headerProvider ? headerProvider() : {}
  for (const [key, value] of Object.entries(provided)) {
    headers.set(key, value)
  }

  const fromInit = new Headers(init.headers || {})
  fromInit.forEach((value, key) => headers.set(key, value))

  if (!headers.has('Content-Type') && hasJsonBody(init.body)) {
    headers.set('Content-Type', 'application/json')
  }

  if (!headers.has('Authorization')) {
    const token = getCompatibilityToken()
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }
  }

  return headers
}

function validationMessages(input: unknown): string[] {
  if (!input) return []

  if (Array.isArray(input)) {
    return input
      .flatMap((item) => {
        if (!item || typeof item !== 'object') return []
        const record = item as Record<string, unknown>
        const location = Array.isArray(record.loc) ? record.loc.join('.') : null
        const message =
          typeof record.msg === 'string'
            ? record.msg
            : typeof record.message === 'string'
              ? record.message
              : null

        if (!message) return []
        return location ? [`${location}: ${message}`] : [message]
      })
      .filter(Boolean)
  }

  if (typeof input === 'object') {
    const record = input as Record<string, unknown>
    if (Array.isArray(record.fields)) {
      return validationMessages(record.fields)
    }
  }

  return []
}

function firstString(values: unknown[]): string | null {
  for (const value of values) {
    if (typeof value === 'string' && value.trim()) {
      return value.trim()
    }
  }

  return null
}

async function readErrorPayload(response: Response): Promise<unknown> {
  const clone = response.clone()
  const contentType = clone.headers.get('content-type')?.toLowerCase() ?? ''

  if (contentType.includes('application/json')) {
    return clone.json().catch(() => null)
  }

  return clone.text().catch(() => '')
}

async function request(path: string, init: RequestInit = {}, options: ApiRequestOptions = {}): Promise<Response> {
  const retryOn401 = options.retryOn401 ?? true
  const url = /^[a-z]+:\/\//i.test(path) ? path : toApiUrl(path)

  const execute = () =>
    fetch(url, {
      ...init,
      headers: buildRequestHeaders(init),
      credentials: 'include',
    })

  const response = await execute()
  if (response.status !== 401 || !retryOn401) {
    return response
  }

  const refreshed = await refreshAccessToken()
  if (!refreshed) {
    return response
  }

  return execute()
}

export function resolveApiBase(): string {
  return API_BASE ? normalizeBaseUrl(API_BASE) : ''
}

export function toApiUrl(path: string): string {
  const normalizedPath = normalizePath(path)
  if (/^[a-z]+:\/\//i.test(normalizedPath) || normalizedPath.startsWith('blob:') || normalizedPath.startsWith('data:')) {
    return normalizedPath
  }

  const base = resolveApiBase()
  return base ? `${base}${normalizedPath}` : normalizedPath
}

export function toAssetUrl(pathOrUrl: string | null | undefined): string | null {
  if (!pathOrUrl) return null

  if (/^[a-z]+:\/\//i.test(pathOrUrl) || pathOrUrl.startsWith('blob:') || pathOrUrl.startsWith('data:')) {
    return pathOrUrl
  }

  return toApiUrl(pathOrUrl)
}

export async function parseApiError(response: Response): Promise<string> {
  const payload = await readErrorPayload(response)
  const fallback = `HTTP ${response.status}`

  if (typeof payload === 'string') {
    return payload.trim() || fallback
  }

  if (!payload || typeof payload !== 'object') {
    return fallback
  }

  const record = payload as Record<string, unknown>
  const errorObject = typeof record.error === 'object' && record.error !== null
    ? (record.error as ApiErrorObject)
    : null

  const validation = [
    ...validationMessages(record.detail),
    ...validationMessages(errorObject?.details),
  ]
  if (validation.length) {
    return validation.join('; ')
  }

  return (
    firstString([
      record.detail,
      record.message,
      errorObject?.message,
      errorObject?.code,
    ]) ?? fallback
  )
}

export function configureApiHeaders(fn: () => Record<string, string>) {
  headerProvider = fn
}

export function setAccessToken(token: string | null, options: { persistLegacy?: boolean } = {}) {
  compatibilityAccessToken = token

  if (!options.persistLegacy) {
    return
  }

  try {
    if (token) {
      localStorage.setItem('access_token', token)
    } else {
      localStorage.removeItem('access_token')
    }
  } catch {
    // ignore legacy storage failures
  }
}

export function clearLegacyAuthStorage() {
  compatibilityAccessToken = null

  try {
    localStorage.removeItem('auth')
    localStorage.removeItem('access_token')
  } catch {
    // ignore legacy storage failures
  }
}

export async function refreshAccessToken(): Promise<boolean> {
  if (refreshPromise) return refreshPromise

  refreshPromise = (async () => {
    const response = await request(
      '/api/v1/auth/refresh',
      {
        method: 'POST',
      },
      { retryOn401: false },
    )

    if (!response.ok) {
      return false
    }

    const data = (await response.json().catch(() => null)) as Record<string, unknown> | null
    const token =
      typeof data?.access_token === 'string'
        ? data.access_token
        : typeof data?.token === 'string'
          ? data.token
          : null

    if (token) {
      setAccessToken(token)
    }

    return true
  })()

  try {
    return await refreshPromise
  } finally {
    refreshPromise = null
  }
}

export async function api(input: string, init: RequestInit = {}, options: ApiRequestOptions = {}) {
  return request(input, init, options)
}

export async function apiJson<T>(input: string, init: RequestInit = {}, options: ApiRequestOptions = {}): Promise<T> {
  const response = await api(input, init, options)
  if (!response.ok) {
    throw new Error(await parseApiError(response))
  }

  if (response.status === 204) {
    return undefined as T
  }

  const data = await response.json().catch(() => null)
  if (data === null) {
    throw new Error('Invalid response format')
  }

  return data as T
}

export async function apiVoid(input: string, init: RequestInit = {}, options: ApiRequestOptions = {}) {
  const response = await api(input, init, options)
  if (!response.ok) {
    throw new Error(await parseApiError(response))
  }
}

export async function health(): Promise<boolean> {
  try {
    const response = await api('/api/v1/health', { cache: 'no-store' }, { retryOn401: false })
    return response.ok
  } catch {
    return false
  }
}

export type LoginInput = {
  identifier: string
  password: string
}

export type RegisterInput = {
  email: string
  password: string
  username: string
}

export type ForgotPasswordInput = {
  identifier: string
}

export type ResetPasswordInput = {
  token: string
  new_password: string
}

export type LoginResponse = AuthUserRecord & {
  access_token: string
  token_type: 'bearer'
  expires_in: number
}

export type RegisterResponse = {
  id: string
  email: string
  username: string
  access_token: string
  token_type: 'bearer'
  expires_in: number
}

export type MeResponse = AuthUserRecord

export async function loginRequest(payload: LoginInput): Promise<LoginResponse> {
  return apiJson<LoginResponse>(
    '/api/v1/auth/login',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
    { retryOn401: false },
  )
}

export async function registerRequest(payload: RegisterInput): Promise<RegisterResponse> {
  return apiJson<RegisterResponse>(
    '/api/v1/auth/register',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
    { retryOn401: false },
  )
}

export async function requestPasswordReset(payload: ForgotPasswordInput) {
  return apiVoid(
    '/api/v1/auth/forgot-password',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
    { retryOn401: false },
  )
}

export async function resetPasswordRequest(payload: ResetPasswordInput) {
  return apiVoid(
    '/api/v1/auth/reset-password',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
    { retryOn401: false },
  )
}

export async function logoutRequest() {
  return apiVoid(
    '/api/v1/auth/logout',
    {
      method: 'POST',
    },
    { retryOn401: false },
  )
}

export async function getCurrentUser(options: ApiRequestOptions = {}): Promise<MeResponse> {
  return apiJson<MeResponse>('/api/v1/auth/me', undefined, options)
}

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
  provider_name?: string | null
  provider_state?: Record<string, unknown> | null
  image_path?: string | null
  image_filename?: string | null
  image_url?: string | null
  exp?: number | null
  sig?: string | null
  metadata?: Record<string, unknown> | null
  error?: string | null
  created_at?: number | null
  started_at?: number | null
  completed_at?: number | null
}

export async function generateJSON(body: GeneratePayload, signal?: AbortSignal): Promise<TaskResp> {
  return apiJson<TaskResp>('/api/v1/images/generate', {
    method: 'POST',
    body: JSON.stringify(body),
    signal,
  })
}

export async function getTaskStatus(taskId: string, signal?: AbortSignal): Promise<TaskStatusResp> {
  return apiJson<TaskStatusResp>(`/api/v1/images/status/${encodeURIComponent(taskId)}`, {
    method: 'GET',
    signal,
  })
}

export type GenerationItem = {
  id: string
  task_id?: string
  status?: string
  provider_name?: string | null
  provider_state?: Record<string, unknown> | null
  image_path: string
  image_filename?: string | null
  metadata?: Record<string, unknown> | null
  error?: string | null
  prompt: Record<string, unknown>
  params: Record<string, unknown>
  created_at: string
  started_at?: string | null
  completed_at?: string | null
  image_url?: string | null
  exp?: number
  sig?: string
}

export type GenerationListResponse = {
  total: number
  items: GenerationItem[]
}

export async function listMyGenerations(limit = 50, offset = 0): Promise<GenerationListResponse> {
  const query = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  return apiJson<GenerationListResponse>(`/api/v1/users/me/generations?${query.toString()}`)
}

export type SettingsResponse = {
  data: Record<string, unknown>
}

export async function getMySettings(): Promise<SettingsResponse> {
  return apiJson<SettingsResponse>('/api/v1/users/me/settings')
}

export async function patchMySettings(payload: Record<string, unknown>): Promise<SettingsResponse> {
  return apiJson<SettingsResponse>('/api/v1/users/me/settings', {
    method: 'PATCH',
    body: JSON.stringify({ data: payload }),
  })
}
