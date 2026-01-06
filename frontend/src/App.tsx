import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'

import { configureApiHeaders } from './lib/api'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs'
import Generate from './pages/Generate'
import History from './pages/History'
import Settings from './pages/Settings'
import PromptGuide from './pages/PromptGuide'
import Register from './pages/Register'
import Login from './pages/Login'
import { Topbar } from './components/Topbar'
import { Footbar } from './components/Footbar'
import About from './pages/About'
import FAQ from './pages/FAQ'
import Reset from './pages/Reset'
import Privacy from './pages/Privacy'
import './i18n/i18n'
import Error404 from './pages/Error404'

type Tab = 'gen' | 'history' | 'settings' | 'guide' | 'about' | 'faq' | 'privacy' | 'register' | 'login' | 'reset' | 'error404'

// глобальная установка заголовков Authorization для всех API-вызовов
function setAuthHeaders() {
  configureApiHeaders((): Record<string, string> => {
    try {
      const raw = localStorage.getItem('auth')
      if (!raw) return {}
      const obj = JSON.parse(raw)
      const token = obj?.user?.access_token || obj?.access_token || obj?.token
      const h: Record<string, string> = {}
      if (token) h.Authorization = `Bearer ${token}`
      return h
    } catch {
      return {}
    }
  })
}

export default function App() {
  const [tab, setTab] = useState<Tab>('gen')
  const [theme, setTheme] = useState<'light' | 'dark'>(
    () => (localStorage.getItem('theme') as any) ?? 'light'
  )

  useEffect(() => {
    localStorage.setItem('theme', theme)
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])
  const toggleTheme = () => setTheme(t => (t === 'light' ? 'dark' : 'light'))

  // скрытые вкладки переключаются через глобальное событие
  useEffect(() => {
    const handler = (e: any) => setTab(e.detail as Tab)
    window.addEventListener('goto-tab', handler)
    return () => window.removeEventListener('goto-tab', handler)
  }, [])

  // первичная навигация по path -> tab, иначе 404
  useEffect(() => {
    try {
      const path = window.location.pathname.replace(/\/+$/, '') || '/'
      const routes: Record<string, Tab> = {
        '/': 'gen',
        '/gen': 'gen',
        '/history': 'history',
        '/settings': 'settings',
        '/guide': 'guide',
        '/about': 'about',
        '/faq': 'faq',
        '/privacy': 'privacy',
        '/register': 'register',
        '/login': 'login',
        '/reset': 'reset',
      }
      setTab(routes[path] ?? 'error404')
    } catch {}
  }, [])


  // обновлять заголовки и мягко перерисовывать при логине/логауте
  useEffect(() => {
    const onAuth = () => {
      setAuthHeaders()
      setTab(t => t)
    }
    window.addEventListener('auth:update', onAuth)
    return () => window.removeEventListener('auth:update', onAuth)
  }, [])

  // первичная установка Authorization
  useEffect(() => {
    setAuthHeaders()
    
    // Check if user has valid tokens, if not clear them
    // Only check once on mount, not on every render
    let mounted = true
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('access_token')
        if (!token) {
          // No token, no need to check
          return
        }
        
        const response = await fetch('/api/v1/auth/me', {
          credentials: 'include',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (!mounted) return
        
        if (!response.ok && response.status === 401) {
          // Only clear on 401, not on other errors
          localStorage.removeItem('access_token')
          const authData = localStorage.getItem('auth')
          if (authData) {
            try {
              const auth = JSON.parse(authData)
              if (auth && auth.user) {
                delete auth.user.access_token
                localStorage.setItem('auth', JSON.stringify(auth))
              }
            } catch {}
          }
          window.dispatchEvent(new Event('auth:update'))
        }
      } catch (e) {
        // Ignore network errors on initial check
        if (mounted) {
          console.warn('Auth check failed:', e)
        }
      }
    }
    
    checkAuth()
    
    return () => {
      mounted = false
    }
  }, [])

  const { t } = useTranslation()
  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground overflow-x-hidden">
      <Topbar theme={theme} toggleTheme={toggleTheme} />

      <div className="container pt-0 flex-1">
        {tab === 'error404' ? (
          <Error404 />
        ) : tab === 'register' ? (
          <Register />
        ) : tab === 'login' ? (
          <Login />
        ) : tab === 'reset' ? (
          <Reset />
        ) : (
          <Tabs value={tab} onValueChange={(v) => setTab(v as Tab)}>
            <div className="flex items-center justify-center pb-3">
            <TabsList>
              <TabsTrigger value="gen">{t('navtop:gen')}</TabsTrigger>
              <TabsTrigger value="history">{t('navtop:history')}</TabsTrigger>
              <TabsTrigger value="settings">{t('navtop:settings')}</TabsTrigger>
            </TabsList>
            </div>

            <AnimatePresence mode="wait">
              <motion.div
                key={tab}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.25 }}
              >
                <TabsContent value="gen" className="focus-visible:outline-none">
                  {tab === 'gen' && <Generate />}
                </TabsContent>
                <TabsContent value="history" className="focus-visible:outline-none">
                  {tab === 'history' && <History />}
                </TabsContent>
                <TabsContent value="guide" className="focus-visible:outline-none">
                  {tab === 'guide' && <PromptGuide />}
                </TabsContent>
                <TabsContent value="about" className="focus-visible:outline-none">
                  {tab === 'about' && <About />}
                </TabsContent>
                <TabsContent value="faq" className="focus-visible:outline-none">
                  {tab === 'faq' && <FAQ />}
                </TabsContent>
                <TabsContent value="privacy" className="focus-visible:outline-none">
                  {tab === 'privacy' && <Privacy />}
                </TabsContent>
                <TabsContent value="settings" className="focus-visible:outline-none">
                  {tab === 'settings' && <Settings theme={theme} toggleTheme={toggleTheme} />}
                </TabsContent>
              </motion.div>
            </AnimatePresence>
          </Tabs>
        )}
        {tab !== 'register' && tab !== 'login' && tab !== 'reset' && tab !== 'error404' && <Footbar />}
      </div>

      <AnimatePresence>
        <motion.div
          key={tab + '-overlay'}
          initial={{ opacity: 0 }}
          animate={{ opacity: 0 }}
          exit={{ opacity: 0.8 }}
          transition={{ duration: 0.25 }}
          className="pointer-events-none fixed inset-0 -z-10 bg-primary"
        />
      </AnimatePresence>
    </div>
  )
}
