export function getToken(): string | null {
    try {
      const raw = localStorage.getItem('auth')
      if (!raw) return null
      const obj = JSON.parse(raw)
      return obj?.user?.access_token || obj?.token || null
    } catch {
      return null
    }
  }
  
  export async function api(input: string, init: RequestInit = {}) {
    const headers: Record<string, string> = { ...(init.headers as any) }
    const token = getToken()
    if (token) headers['Authorization'] = `Bearer ${token}`
    return fetch(input, { ...init, headers })
  }
  