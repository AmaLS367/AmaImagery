import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'

import {
  api,
  clearLegacyAuthStorage,
  loginRequest,
  logoutRequest,
  refreshAccessToken,
  registerRequest,
  setAccessToken,
  type LoginInput,
  type LoginResponse,
  type MeResponse,
  type RegisterInput,
} from '../lib/api'

export type AuthStatus = 'loading' | 'authenticated' | 'anonymous'

type AuthContextValue = {
  status: AuthStatus
  user: MeResponse | null
  isAuthenticated: boolean
  login: (payload: LoginInput) => Promise<LoginResponse>
  register: (payload: RegisterInput) => Promise<void>
  logout: () => Promise<void>
  refreshIfNeeded: () => Promise<boolean>
  loadMe: (options?: { allowRefresh?: boolean }) => Promise<MeResponse | null>
}

const AuthContext = createContext<AuthContextValue | null>(null)

function toUserRecord(record: { id: string; email: string; username: string; settings?: Record<string, unknown> }): MeResponse {
  return {
    id: record.id,
    email: record.email,
    username: record.username,
    settings: record.settings ?? {},
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>('loading')
  const [user, setUser] = useState<MeResponse | null>(null)

  const setAnonymous = () => {
    clearLegacyAuthStorage()
    setUser(null)
    setStatus('anonymous')
  }

  const setAuthenticated = (nextUser: MeResponse) => {
    setUser(nextUser)
    setStatus('authenticated')
  }

  const loadMe = async ({ allowRefresh = true }: { allowRefresh?: boolean } = {}): Promise<MeResponse | null> => {
    const response = await api('/api/v1/auth/me', { method: 'GET' }, { retryOn401: false })

    if (response.ok) {
      const payload = (await response.json()) as MeResponse
      setAuthenticated(payload)
      return payload
    }

    if (response.status === 401 && allowRefresh) {
      const refreshed = await refreshAccessToken()
      if (refreshed) {
        return loadMe({ allowRefresh: false })
      }
    }

    setAnonymous()
    return null
  }

  const login = async (payload: LoginInput): Promise<LoginResponse> => {
    const response = await loginRequest(payload)
    clearLegacyAuthStorage()
    setAccessToken(response.access_token)
    setAuthenticated(toUserRecord(response))
    return response
  }

  const register = async (payload: RegisterInput): Promise<void> => {
    const response = await registerRequest(payload)
    clearLegacyAuthStorage()
    setAccessToken(response.access_token)

    const loadedUser = await loadMe({ allowRefresh: false })
    if (!loadedUser) {
      setAuthenticated(
        toUserRecord({
          id: response.id,
          email: response.email,
          username: response.username,
        }),
      )
    }
  }

  const logout = async () => {
    try {
      await logoutRequest()
    } catch {
      // clear local auth state even if the server-side logout call fails
    } finally {
      setAnonymous()
    }
  }

  const refreshIfNeeded = async () => refreshAccessToken()

  useEffect(() => {
    let active = true

    const bootstrap = async () => {
      try {
        await loadMe()
      } catch (error) {
        if (!active) return

        console.warn('Auth bootstrap failed:', error)
        setAnonymous()
      }
    }

    bootstrap()

    return () => {
      active = false
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      user,
      isAuthenticated: status === 'authenticated',
      login,
      register,
      logout,
      refreshIfNeeded,
      loadMe,
    }),
    [status, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) {
    throw new Error('AuthProvider is missing')
  }

  return value
}
