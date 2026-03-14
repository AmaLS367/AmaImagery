import { useEffect, useState } from 'react'
import { MoonStar, Sun, LogOut } from 'lucide-react'
import { NavLink, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'

import LanguageSwitcher from '../components/LanguageSwitcher'
import { appRoutes } from '../lib/routes'
import { useAuth } from '../providers/AuthProvider'
import { useSettings } from '../providers/SettingsProvider'
import { Button } from './ui/button'
import { cn } from '../lib/utils'

type Theme = 'light' | 'dark'

const productLinks = [
  { href: appRoutes.generate, labelKey: 'navtop:gen' },
  { href: appRoutes.history, labelKey: 'navtop:history' },
  { href: appRoutes.settings, labelKey: 'navtop:settings' },
] as const

export function Topbar({ theme, toggleTheme }: { theme: Theme; toggleTheme: () => void }) {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { status: authStatus, logout } = useAuth()
  const { settings } = useSettings()
  const [loggingOut, setLoggingOut] = useState(false)
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 10)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const handleLogout = async () => {
    if (loggingOut) return
    setLoggingOut(true)

    try {
      await logout()
    } finally {
      navigate(appRoutes.generate, { replace: true })
      setLoggingOut(false)
    }
  }

  const isLoggedIn = authStatus === 'authenticated'
  const authReady = authStatus !== 'loading'

  return (
    <header className={cn(
      "sticky top-0 z-50 w-full transition-all duration-300",
      isScrolled ? "py-3" : "py-5"
    )}>
      <div className="page-shell">
        <div className={cn(
          "runtime-topbar-shell flex items-center justify-between gap-4 px-6 py-3 transition-all duration-300",
          settings.visualMode === 'cinematic' && "rounded-[30px]",
          settings.visualMode === 'editorial' && "rounded-[24px]",
          settings.visualMode === 'dashboard' && "rounded-[34px]",
          !isScrolled && "bg-transparent border-transparent shadow-none backdrop-blur-0"
        )}>
          <div className="flex min-w-0 items-center gap-10">
            <NavLink to={appRoutes.landing} className="group flex min-w-0 items-center gap-3">
              <div className="relative flex h-10 w-10 shrink-0 items-center justify-center">
                <div className="absolute inset-0 rounded-xl bg-primary/20 opacity-0 transition-opacity group-hover:opacity-100" />
                <div className="h-4 w-4 rounded-full bg-primary shadow-[0_0_20px_theme(colors.primary.DEFAULT)] transition-transform group-hover:scale-110" />
              </div>
              <div className="flex min-w-0 flex-col">
                <span className="truncate font-display text-xl font-bold leading-none tracking-tight text-foreground">{t('appName')}</span>
                <span className="hidden text-[10px] font-black uppercase tracking-[0.3em] text-primary md:inline">{t('appSubtitle')}</span>
              </div>
            </NavLink>

            <nav className="hidden items-center gap-1 md:flex" aria-label="Primary">
              {productLinks.map((link) => (
                <NavLink
                  key={link.href}
                  to={link.href}
                  className={({ isActive }) =>
                    cn(
                      'relative rounded-full px-5 py-2 text-sm font-bold tracking-tight transition-all duration-200',
                      isActive
                        ? 'text-primary'
                        : 'text-foreground/60 hover:text-foreground hover:bg-black/5 dark:text-white/60 dark:hover:text-white dark:hover:bg-white/5',
                    )
                  }
                >
                  {({ isActive }) => (
                    <>
                      {t(link.labelKey)}
                      {isActive && (
                        <motion.div 
                          layoutId="nav-pill"
                          className="absolute inset-0 -z-10 rounded-full bg-primary/10"
                          transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                        />
                      )}
                    </>
                  )}
                </NavLink>
              ))}
            </nav>
          </div>

          <div className="flex shrink-0 items-center gap-3">
            <div className="hidden h-8 w-px bg-border sm:block" />
            
            <AnimatePresence mode="wait">
              {!authReady ? null : !isLoggedIn ? (
                <motion.div
                  key="auth-buttons"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="flex items-center gap-2"
                >
                  <Button variant="ghost" size="sm" onClick={() => navigate(appRoutes.login)} className="h-10 text-xs font-bold uppercase tracking-widest text-foreground/70 hover:text-foreground">
                    {t('nav.login')}
                  </Button>
                  <Button size="sm" onClick={() => navigate(appRoutes.register)} className="h-10 rounded-full bg-foreground px-6 text-xs font-black uppercase tracking-widest text-background hover:bg-foreground/90">
                    {t('nav.register')}
                  </Button>
                </motion.div>
              ) : (
                <motion.div
                  key="user-menu"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="flex items-center gap-2"
                >
                  <Button variant="ghost" size="sm" onClick={handleLogout} disabled={loggingOut} className="h-10 gap-2 rounded-full border border-border text-xs font-bold text-foreground hover:bg-black/5 dark:hover:bg-white/5">
                    <LogOut className="h-3.5 w-3.5" />
                    <span>{loggingOut ? t('nav.loggingOut') : t('nav.logout')}</span>
                  </Button>
                </motion.div>
              )}
            </AnimatePresence>

            <div className="flex items-center gap-1.5 rounded-full border border-border bg-secondary/50 p-1 backdrop-blur-md">
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={toggleTheme} 
                className="h-8 w-8 rounded-full text-foreground/70 hover:bg-black/5 hover:text-foreground dark:text-white/70 dark:hover:bg-white/10 dark:hover:text-white"
              >
                {theme === 'dark' ? <Sun className="h-4 w-4" /> : <MoonStar className="h-4 w-4" />}
              </Button>
              <div className="h-4 w-px bg-border" />
              <LanguageSwitcher compact />
            </div>
          </div>
        </div>

        {/* Mobile Navigation */}
        <nav
          className="mt-4 flex gap-2 overflow-x-auto pb-2 md:hidden no-scrollbar"
          aria-label="Primary mobile"
        >
          {productLinks.map((link) => (
            <NavLink
              key={link.href}
              to={link.href}
              className={({ isActive }) =>
                cn(
                  'shrink-0 rounded-full border px-5 py-2 text-xs font-bold uppercase tracking-widest transition-all duration-200',
                  isActive
                    ? 'border-primary/40 bg-primary/10 text-primary shadow-glow'
                    : 'border-border bg-secondary/50 text-foreground/60',
                )
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
