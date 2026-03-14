import { useEffect, useState } from 'react'
import { MoonStar, Sun, LogIn, UserPlus, LogOut } from 'lucide-react'
import { NavLink, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'

import LanguageSwitcher from '../components/LanguageSwitcher'
import { appRoutes } from '../lib/routes'
import { Button } from './ui/button'

type Theme = 'light' | 'dark'

function readAuthFlag(): boolean {
  try {
    const raw = localStorage.getItem('auth')
    if (!raw) return false
    const value = JSON.parse(raw)
    return !!value?.loggedIn
  } catch {
    return false
  }
}

function getToken(): string | null {
  try {
    const raw = localStorage.getItem('auth')
    if (!raw) return null
    const obj = JSON.parse(raw)
    return obj?.user?.access_token || obj?.access_token || obj?.token || null
  } catch {
    return null
  }
}

const productLinks = [
  { href: appRoutes.generate, labelKey: 'navtop:gen' },
  { href: appRoutes.history, labelKey: 'navtop:history' },
  { href: appRoutes.settings, labelKey: 'navtop:settings' },
] as const

export function Topbar({ theme, toggleTheme }: { theme: Theme; toggleTheme: () => void }) {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(() => readAuthFlag())
  const [loggingOut, setLoggingOut] = useState(false)

  useEffect(() => {
    const apply = () => setIsLoggedIn(readAuthFlag())
    window.addEventListener('auth:update', apply)
    apply()
    return () => window.removeEventListener('auth:update', apply)
  }, [])

  const handleLogout = async () => {
    if (loggingOut) return
    setLoggingOut(true)

    try {
      const token = getToken()
      await fetch('/api/v1/auth/logout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      }).catch(() => {})
    } finally {
      try {
        localStorage.removeItem('auth')
        localStorage.removeItem('access_token')
      } catch {
        // ignore storage failures during logout
      }

      setIsLoggedIn(false)
      window.dispatchEvent(new CustomEvent('auth:update'))
      navigate(appRoutes.generate, { replace: true })
      setLoggingOut(false)
    }
  }

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border/60 bg-background/72 backdrop-blur-xl">
      <div className="page-shell py-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex min-w-0 items-center gap-6">
            <NavLink to={appRoutes.landing} className="flex min-w-0 items-center gap-3 font-semibold">
              <div className="h-3 w-3 shrink-0 rounded-full bg-primary shadow-[0_0_24px_theme(colors.primary.DEFAULT)]" />
              <div className="flex min-w-0 flex-col">
                <span className="truncate font-display text-lg leading-none tracking-[-0.06em]">{t('appName')}</span>
                <span className="hidden text-[11px] uppercase tracking-[0.32em] text-muted-foreground md:inline">Creative image system</span>
              </div>
            </NavLink>

            <nav className="hidden items-center gap-2 rounded-full border border-border/70 bg-card/70 p-1.5 shadow-panel md:flex" aria-label="Primary">
              {productLinks.map((link) => (
                <NavLink
                  key={link.href}
                  to={link.href}
                  className={({ isActive }) =>
                    [
                      'rounded-full px-4 py-2 text-sm font-semibold tracking-[-0.02em] transition-colors',
                      isActive
                        ? 'bg-primary text-primary-foreground shadow-glow'
                        : 'text-muted-foreground hover:bg-card hover:text-foreground',
                    ].join(' ')
                  }
                >
                  {t(link.labelKey)}
                </NavLink>
              ))}
            </nav>
          </div>

          <div className="flex shrink-0 items-center gap-2">
            <AnimatePresence mode="wait">
              {!isLoggedIn ? (
                <motion.div
                  key="auth-buttons"
                  initial={{ opacity: 0, x: 12 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -12 }}
                  transition={{ duration: 0.2, ease: 'easeOut' }}
                  className="flex items-center gap-2"
                >
                  <Button variant="ghost" size="sm" onClick={() => navigate(appRoutes.login)} className="gap-2 max-sm:px-3">
                    <LogIn className="h-4 w-4" />
                    <span className="hidden sm:inline">{t('nav.login')}</span>
                  </Button>
                  <Button variant="default" size="sm" onClick={() => navigate(appRoutes.register)} className="gap-2 max-sm:px-3">
                    <UserPlus className="h-4 w-4" />
                    <span className="hidden sm:inline">{t('nav.register')}</span>
                  </Button>
                </motion.div>
              ) : (
                <motion.div
                  key="user-menu"
                  initial={{ opacity: 0, x: 12 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -12 }}
                  transition={{ duration: 0.2, ease: 'easeOut' }}
                  className="flex items-center gap-2"
                >
                  <span className="hidden text-sm text-muted-foreground sm:inline">{t('nav.profile')}</span>
                  <Button variant="ghost" size="sm" onClick={handleLogout} disabled={loggingOut} className="gap-2 max-sm:px-3">
                    <LogOut className="h-4 w-4" />
                    <span className="hidden sm:inline">{loggingOut ? t('nav.loggingOut') : t('nav.logout')}</span>
                  </Button>
                </motion.div>
              )}
            </AnimatePresence>

            <Button variant="secondary" size="icon" onClick={toggleTheme} aria-label="Toggle theme">
              {theme === 'dark' ? <Sun className="h-4 w-4" /> : <MoonStar className="h-4 w-4" />}
            </Button>
            <LanguageSwitcher compact />
          </div>
        </div>

        <nav
          className="mt-4 flex gap-2 overflow-x-auto pb-1 md:hidden"
          aria-label="Primary mobile"
        >
          {productLinks.map((link) => (
            <NavLink
              key={link.href}
              to={link.href}
              className={({ isActive }) =>
                [
                  'shrink-0 rounded-full border border-border/70 bg-card/70 px-4 py-2 text-sm font-semibold tracking-[-0.02em] shadow-panel transition-colors',
                  isActive
                    ? 'border-primary/30 bg-primary text-primary-foreground shadow-glow'
                    : 'text-muted-foreground hover:bg-card hover:text-foreground',
                ].join(' ')
              }
            >
              {t(link.labelKey)}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  )
}
