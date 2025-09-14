import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MoonStar, Sun, LogIn, UserPlus, LogOut } from 'lucide-react'
import { Button } from './ui/button'
import { health } from '../lib/api'
import { useTranslation } from 'react-i18next'
import LanguageSwitcher from '../components/LanguageSwitcher'

type Theme = 'light' | 'dark'

function readAuthFlag(): boolean {
  try {
    const raw = localStorage.getItem('auth')
    if (!raw) return false
    const v = JSON.parse(raw)
    return !!v?.loggedIn
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
  } catch { return null }
}

export function Topbar({ theme, toggleTheme }: { theme: Theme; toggleTheme: () => void }) {
  const [ok, setOk] = useState<boolean | null>(null)
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(() => readAuthFlag())
  const [loggingOut, setLoggingOut] = useState(false)
  const { t } = useTranslation()

  const POLL_SEC = Number(import.meta.env.VITE_HEALTH_POLL_SEC ?? '3600') || 3600
  const POLL_MS = Math.max(10, POLL_SEC) * 1000  // защита от мусора

  // Проверка здоровье по интервалу
  useEffect(() => {
    let mounted = true
    const ping = async () => {
      try { const res = await health(); if (mounted) setOk(res) } catch { if (mounted) setOk(false) }
    }
    ping() 
    const id = setInterval(() => {
      if (document.visibilityState === 'visible') ping()
    }, POLL_MS)
    return () => { mounted = false; clearInterval(id) }
  }, [POLL_MS])
  

  // Подписка на глобальные обновления авторизации
  useEffect(() => {
    const apply = () => setIsLoggedIn(readAuthFlag())
    window.addEventListener('auth:update', apply)
    // на случай F5 / первого рендера
    apply()
    return () => window.removeEventListener('auth:update', apply)
  }, [])

  const handleLogin = () => {
    window.dispatchEvent(new CustomEvent('goto-tab', { detail: 'login' }))
  }

  const handleRegister = () => {
    window.dispatchEvent(new CustomEvent('goto-tab', { detail: 'register' }))
  }

  const handleLogout = async () => {
    if (loggingOut) return
    setLoggingOut(true)
    try {
      const token = getToken()
      await fetch('/auth/logout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      }).catch(() => {})
    } finally {
      try { localStorage.removeItem('auth') } catch {}
      setIsLoggedIn(false)
      window.dispatchEvent(new CustomEvent('auth:update'))
      window.dispatchEvent(new CustomEvent('goto-tab', { detail: 'gen' }))
    
      setTimeout(() => {
        window.location.reload() 
      }, 200)
    
      setLoggingOut(false)
    }
  }  

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/80 backdrop-blur">
      <div className="container flex h-14 items-center justify-between">
        <div className="flex items-center gap-2 font-semibold">
          <div className="h-2.5 w-2.5 rounded-full bg-primary shadow-[0_0_16px_theme(colors.primary.DEFAULT)]" />
          {t('appName')}
        </div>

        <div className="flex items-center gap-3">
          <AnimatePresence mode="wait">
            {!isLoggedIn ? (
              <motion.div
                key="auth-buttons"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3, ease: 'easeOut' }}
                className="flex items-center gap-2"
              >
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} transition={{ duration: 0.2 }}>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleLogin}
                    className="gap-2 hover:bg-accent/50 transition-all duration-200"
                  >
                    <LogIn className="h-4 w-4" />
                    {t('nav.login')}
                  </Button>
                </motion.div>
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} transition={{ duration: 0.2 }}>
                  <Button
                    variant="default"
                    size="sm"
                    onClick={handleRegister}
                    className="gap-2 shadow-md hover:shadow-lg transition-all duration-200 bg-gradient-to-r from-primary to-primary/90 hover:from-primary/90 hover:to-primary"
                  >
                    <UserPlus className="h-4 w-4" />
                    {t('nav.register')}
                  </Button>
                </motion.div>
              </motion.div>
            ) : (
              <motion.div
                key="user-menu"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3, ease: 'easeOut' }}
                className="flex items-center gap-2"
              >
                <span className="text-sm text-muted-foreground">{t('nav.profile')}</span>
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} transition={{ duration: 0.2 }}>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleLogout}
                  disabled={loggingOut}
                  className="gap-2 hover:bg-destructive/10 hover:text-destructive transition-all duration-200"
                >
                  <LogOut className="h-4 w-4" />
                  {loggingOut ? t('nav.loggingOut') : t('nav.logout')}
                </Button>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>

          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} transition={{ duration: 0.2 }} className="ml-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={toggleTheme}
              aria-label="Toggle theme"
              className="hover:bg-accent/50 transition-all duration-200"
            >
              <motion.div key={theme} initial={{ rotate: 0, scale: 0.8 }} animate={{ rotate: 0, scale: 1 }} transition={{ duration: 0.3, ease: 'easeOut' }}>
                {theme === 'dark' ? <Sun className="h-4 w-4" /> : <MoonStar className="h-4 w-4" />}
              </motion.div>
            </Button>
          </motion.div>
          <LanguageSwitcher compact />
        </div>
      </div>
    </header>
  )
}
