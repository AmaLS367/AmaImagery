import { Outlet, useLocation } from 'react-router'
import { motion, AnimatePresence } from 'framer-motion'
import { useEffect } from 'react'

import { Footbar } from '../components/Footbar'
import { Topbar } from '../components/Topbar'
import { cn } from '../lib/utils'
import { useSettings } from '../providers/SettingsProvider'

type ProductLayoutProps = {
  theme: 'light' | 'dark'
  toggleTheme: () => void
}

function GridBackground() {
  return (
    <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
      <div 
        className="absolute inset-0" 
        style={{ 
          backgroundImage: `radial-gradient(circle at 2px 2px, currentColor 1px, transparent 0)`,
          backgroundSize: '32px 32px',
          color: 'var(--layout-grid-color)',
          opacity: 'var(--layout-grid-opacity)',
        }} 
      />
      <div className="absolute inset-0 bg-gradient-to-b from-background via-transparent to-background" />
      <div className="absolute top-0 left-1/4 h-1/2 w-1/2 rounded-full blur-[120px]" style={{ background: 'var(--layout-spot-1)' }} />
      <div className="absolute bottom-0 right-1/4 h-1/2 w-1/2 rounded-full blur-[120px]" style={{ background: 'var(--layout-spot-2)' }} />
      <div className="absolute bottom-12 left-[12%] h-56 w-56 rounded-full blur-[90px]" style={{ background: 'var(--layout-spot-3)' }} />
    </div>
  )
}

export function ProductLayout({ theme, toggleTheme }: ProductLayoutProps) {
  const { pathname } = useLocation()
  const { settings } = useSettings()

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])

  return (
    <div
      className={cn(
        "min-h-screen flex flex-col bg-background text-foreground overflow-x-hidden relative selection:bg-primary selection:text-primary-foreground",
        settings.visualMode === 'cinematic' && "bg-black",
      )}
      data-shell={settings.shellPreset}
      data-mode={settings.visualMode}
    >
      <GridBackground />
      
      <Topbar theme={theme} toggleTheme={toggleTheme} />
      
      <main className="flex-1 relative z-10">
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={pathname}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>
      
      <Footbar className="relative z-10" />
    </div>
  )
}
