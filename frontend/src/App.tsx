import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs'
import Generate from './pages/Generate'
import History from './pages/History'
import Settings from './pages/Settings'
import { Topbar } from './components/Topbar'
type Tab = 'gen' | 'history' | 'settings'
export default function App() {
  const [tab, setTab] = useState<Tab>('gen')
  const [theme, setTheme] = useState<'light'|'dark'>(() => (localStorage.getItem('theme') as any) ?? 'light')
  useEffect(() => { localStorage.setItem('theme', theme); document.documentElement.classList.toggle('dark', theme === 'dark') }, [theme])
  const toggleTheme = () => setTheme(t => t === 'light' ? 'dark' : 'light')
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Topbar theme={theme} toggleTheme={toggleTheme} />
      <div className="container py-3">
        <Tabs value={tab} onValueChange={(v)=>setTab(v as Tab)}>
          <div className="flex items-center justify-center pb-3">
            <TabsList>
              <TabsTrigger value="gen">Генерация</TabsTrigger>
              <TabsTrigger value="history">История</TabsTrigger>
              <TabsTrigger value="settings">Настройки</TabsTrigger>
            </TabsList>
          </div>
          <AnimatePresence mode="wait">
            <motion.div key={tab} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.25 }}>
              <TabsContent value="gen" className="focus-visible:outline-none">{tab === 'gen' && <Generate />}</TabsContent>
              <TabsContent value="history" className="focus-visible:outline-none">{tab === 'history' && <History />}</TabsContent>
              <TabsContent value="settings" className="focus-visible:outline-none">{tab === 'settings' && <Settings theme={theme} toggleTheme={toggleTheme} />}</TabsContent>
            </motion.div>
          </AnimatePresence>
        </Tabs>
      </div>
      <AnimatePresence>
        <motion.div key={tab + '-overlay'} initial={{ opacity: 0 }} animate={{ opacity: 0 }} exit={{ opacity: 0.8 }} transition={{ duration: 0.25 }} className="pointer-events-none fixed inset-0 -z-10 bg-primary" />
      </AnimatePresence>
    </div>
  )
}
