import { lazy, Suspense } from 'react'
import { MotionConfig } from 'framer-motion'
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
} from 'react-router'

import { LegacyNavigationBridge } from './components/LegacyNavigationBridge'
import { Footbar } from './components/Footbar'
import { Topbar } from './components/Topbar'
import { appRoutes } from './lib/routes'
import { ProductLayout } from './layouts/ProductLayout'
import { useSettings } from './providers/SettingsProvider'
import './i18n/i18n'

const About = lazy(() => import('./pages/About'))
const Error404 = lazy(() => import('./pages/Error404'))
const FAQ = lazy(() => import('./pages/FAQ'))
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'))
const Generate = lazy(() => import('./pages/Generate'))
const History = lazy(() => import('./pages/History'))
const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))

const Privacy = lazy(() => import('./pages/Privacy'))
const PromptGuide = lazy(() => import('./pages/PromptGuide'))

const Register = lazy(() => import('./pages/Register'))
const Reset = lazy(() => import('./pages/Reset'))
const Settings = lazy(() => import('./pages/Settings'))

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
      <main className="flex-1">{children}</main>
      {showFooter ? <Footbar /> : null}
    </div>
  )
}

function PreserveQueryRedirect({ to }: { to: string }) {
  const location = useLocation()
  return <Navigate replace to={{ pathname: to, search: location.search }} />
}

function PageMarker({
  pageId,
  children,
}: {
  pageId: string
  children: React.ReactNode
}) {
  return <div data-page-id={pageId}>{children}</div>
}

function AppShell() {
  const { settings, update } = useSettings()
  const theme = settings.theme

  const toggleTheme = () => update('theme', theme === 'light' ? 'dark' : 'light')

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
            <Route
              path={appRoutes.generate}
              element={
                <PageMarker pageId="generate">
                  <Generate />
                </PageMarker>
              }
            />
            <Route
              path={appRoutes.history}
              element={
                <PageMarker pageId="history">
                  <History />
                </PageMarker>
              }
            />
            <Route
              path={appRoutes.settings}
              element={
                <PageMarker pageId="settings">
                  <Settings />
                </PageMarker>
              }
            />
          </Route>

          <Route
            path={appRoutes.landing}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme}>
                <PageMarker pageId="landing">
                  <Landing />
                </PageMarker>
              </PageFrame>
            }
          />
          <Route
            path={appRoutes.about}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme}>
                <PageMarker pageId="about">
                  <About />
                </PageMarker>
              </PageFrame>
            }
          />
          <Route
            path={appRoutes.faq}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme}>
                <PageMarker pageId="faq">
                  <FAQ />
                </PageMarker>
              </PageFrame>
            }
          />
          <Route
            path={appRoutes.promptGuide}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme}>
                <PageMarker pageId="prompt-guide">
                  <PromptGuide />
                </PageMarker>
              </PageFrame>
            }
          />
          <Route
            path={appRoutes.privacy}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme}>
                <PageMarker pageId="privacy">
                  <Privacy />
                </PageMarker>
              </PageFrame>
            }
          />


          <Route
            path={appRoutes.login}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme} showFooter={false}>
                <PageMarker pageId="login">
                  <Login />
                </PageMarker>
              </PageFrame>
            }
          />
          <Route
            path={appRoutes.register}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme} showFooter={false}>
                <PageMarker pageId="register">
                  <Register />
                </PageMarker>
              </PageFrame>
            }
          />
          <Route
            path={appRoutes.forgotPassword}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme} showFooter={false}>
                <PageMarker pageId="forgot-password">
                  <ForgotPassword />
                </PageMarker>
              </PageFrame>
            }
          />
          <Route
            path={appRoutes.resetPassword}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme} showFooter={false}>
                <PageMarker pageId="reset-password">
                  <Reset />
                </PageMarker>
              </PageFrame>
            }
          />

          <Route
            path={appRoutes.notFound}
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme} showFooter={false}>
                <PageMarker pageId="not-found">
                  <Error404 />
                </PageMarker>
              </PageFrame>
            }
          />
          <Route
            path="*"
            element={
              <PageFrame theme={theme} toggleTheme={toggleTheme} showFooter={false}>
                <PageMarker pageId="not-found">
                  <Error404 />
                </PageMarker>
              </PageFrame>
            }
          />
        </Routes>
      </Suspense>
    </>
  )
}

export default function App() {
  const { settings } = useSettings()

  return (
    <MotionConfig
      reducedMotion={settings.motion === 0 ? 'always' : 'never'}
      transition={{
        duration: settings.motion === 2 ? 0.55 : 0.3,
        ease: [0.22, 1, 0.36, 1],
      }}
    >
      <BrowserRouter>
        <AppShell />
      </BrowserRouter>
    </MotionConfig>
  )
}
