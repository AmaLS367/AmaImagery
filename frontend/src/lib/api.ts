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
}

export type GenerateResponse = {
  path: string
  prompt_hash?: string
  corrections?: Array<[string, string]>
}

const API_BASE = import.meta.env.VITE_API_BASE || ''

export async function health(): Promise<boolean> {
  try {
    const r = await fetch(`${API_BASE}/health`, { cache: 'no-store' })
    return r.ok
  } catch { return false }
}

export async function generateJSON(body: GeneratePayload): Promise<GenerateResponse> {
  const r = await fetch(`${API_BASE}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) {
    let msg = `HTTP ${r.status}`
    try {
      const j = await r.json() as any
      msg = j.detail || msg
    } catch {}
    throw new Error(msg)
  }
  return r.json()
}
