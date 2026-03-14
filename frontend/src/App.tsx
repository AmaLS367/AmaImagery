import { lazy, Suspense, useEffect, useState } from 'react'
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
} from 'react-router-dom'

import { LegacyNavigationBridge } from './components/LegacyNavigationBridge'
import { Footbar } from './components/Footbar'
import { Topbar } from './components/Topbar'
import { configureApiHeaders } from './lib/api'
import { appRoutes } from './lib/routes'
import { ProductLayout } from './layouts/ProductLayout'
import './i18n/i18n'

const About = lazy(() => import('./pages/About'))
const Error404 = lazy(() => import('./pages/Error404'))
const FAQ = lazy(() => import('./pages/FAQ'))
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'))
const Generate = lazy(() => import('./pages/Generate'))
const History = lazy(() => import('./pages/History'))
const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const Modes = lazy(() => import('./pages/Modes'))
const Privacy = lazy(() => import('./pages/Privacy'))
const PromptGuide = lazy(() => import('./pages/PromptGuide'))
const Prototype = lazy(() => import('./pages/Prototype'))
const Register = lazy(() => import('./pages/Register'))
const Reset = lazy(() => import('./pages/Reset'))
const Settings = lazy(() => import('./pages/Settings'))

function setAuthHeaders() {
  configureApiHeaders((): Record<string, string> => {
    try {
      const raw = localStorage.getItem('auth')
      if (!raw) return {}
      const obj = JSON.parse(raw)
      const token = obj?.user?.access_token || obj?.access_token || obj?.token
      const headers: Record<string, string> = {}
      if (token) headers.Authorization = `Bearer ${token}`
      return headers
    } catch {
      return {}
    }
  })
}

function PageFrame({
  children,
  showFooter = true,
  theme,
  toggleTheme,
}: {
  children: React.ReactNode
  showFooter?: boolean
  theme: 'light' | 'dark'
  toggleTheme: () => void
}) {
  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground overflow-x-hidden">
      <Topbar theme={theme} toggleTheme={toggleTheme} />
      <main className="container flex-1 pt-0">{children}</main>
      {showFooter ? <Footbar /> : null}
    </div>
  )
}

function PreserveQueryRedirect({ to }: { to: string }) {
  const location = useLocation()
  return <Navigate replace to={{ pathname: to, search: location.search }} />
}

function AppShell() {
  const [theme, setTheme] = useState<'light' | 'dark'>(
    () => (localStorage.getItem('theme') as 'light' | 'dark' | null) ?? 'light',
  )

  useEffect(() => {
    localStorage.setItem('theme', theme)
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  useEffect(() => {
    const onAuth = () => {
      setAuthHeaders()
    }

    window.addEventListener('auth:update', onAuth)
    return () => window.removeEventListener('auth:update', onAuth)
  }, [])

  useEffect(() => {
    setAuthHeaders()

    let mounted = true
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('access_token')
        if (!token) return

        const response = await fetch('/api/v1/auth/me', {
          credentials: 'include',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })

        if (!mounted) return

        if (!response.ok && response.status === 401) {
          localStorage.removeItem('access_token')
          const authData = localStorage.getItem('auth')
          if (authData) {
            try {
              const auth = JSON.parse(authData)
              if (auth && auth.user) {
                delete auth.user.access_token
                localStorage.setItem('auth', JSON.stringify(auth))
              }
            } catch {
              // ignore auth storage parse errors
            }
          }
          window.dispatchEvent(new Event('auth:update'))
        }
      } catch (error) {
        if (mounted) {
          console.warn('Auth check failed:', error)
        }
      }
    }

    checkAuth()

    return () => {
      mounted = false
    }
  }, [])

  const toggleTheme = () => setTheme((current) => (current === 'light' ? 'dark' : 'light'))

  return (
    <>
      <LegacyNavigationBridge />
      <Suspense fallback={<div className="min-h-screen bg-background text-foreground" />}>
        <Routes>
          <Route path="/gen" element={<Navigate replace to={appRoutes.generate} />} />
          <Route path="/guide" element={<Navigate replace to={appRoutes.promptGuide} />} />
          <Route path="/reset" element={<PreserveQueryRedirect to={appRoutes.resetPassword} />} />

          <Route
            element={<ProductLayout theme={theme} toggleTheme={toggleTheme} />}
          >
            <Route path={appRoutes.generate} element={<Generate />} />
            <Route path={appRoutes.history} element={<History />} />
            <Route path={appRoutes.settings} element={<Settings theme={theme} toggleTheme={toggleTheme} />} />
          </Route>

          <Route
            path={appRoutes.landing}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme}>
                <Landing />
              </PageFrame>
            }
          />
          <Route
            path={appRoutes.about}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme}>
                <About />
              </PageFrame>
            }
          />
          <Route
            path={appRoutes.faq}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme}>
                <FAQ />
              </PageFrame>
            }
          />
          <Route
            path={appRoutes.promptGuide}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme}>
                <PromptGuide />
              </PageFrame>
            }
          />
          <Route
            path={appRoutes.privacy}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme}>
                <Privacy />
              </PageFrame>
            }
          />
          <Route
            path={appRoutes.modes}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme}>
                <Modes />
              </PageFrame>
            }
          />
          <Route
            path={appRoutes.prototype}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme}>
                <Prototype />
              </PageFrame>
            }
          />

          <Route
            path={appRoutes.login}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme} showFooter={false}>
                <Login />
              </PageFrame>
            }
          />
          <Route
            path={appRoutes.register}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme} showFooter={false}>
                <Register />
              </PageFrame>
            }
          />
          <Route
            path={appRoutes.forgotPassword}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme} showFooter={false}>
                <ForgotPassword />
              </PageFrame>
            }
          />
          <Route
            path={appRoutes.resetPassword}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme} showFooter={false}>
                <Reset />
              </PageFrame>
            }
          />

          <Route
            path={appRoutes.notFound}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme} showFooter={false}>
                <Error404 />
              </PageFrame>
            }
          />
          <Route
            path="*"
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme} showFooter={false}>
                <Error404 />
              </PageFrame>
            }
          />
        </Routes>
      </Suspense>
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  )
}
