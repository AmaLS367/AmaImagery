import { useEffect, useState } from 'react'
import { MoonStar, Sun, Activity } from 'lucide-react'
import { Button } from './ui/button'
import { health } from '../lib/api'
export function Topbar({ theme, toggleTheme }: { theme: 'light'|'dark', toggleTheme: () => void }) {
  const [ok, setOk] = useState<boolean | null>(null)
  useEffect(() => {
    let mounted = true
    const ping = async () => { try { const res = await health(); if (mounted) setOk(res) } catch { if (mounted) setOk(false) } }
    ping(); const id = setInterval(ping, 8000); return () => { mounted = false; clearInterval(id) }
  }, [])
  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/80 backdrop-blur">
      <div className="container flex h-14 items-center justify-between">
        <div className="flex items-center gap-2 font-semibold">
          <div className="h-2.5 w-2.5 rounded-full bg-primary shadow-[0_0_16px_theme(colors.primary.DEFAULT)]" />
          GenAI Studio
        </div>
        <div className="flex items-center gap-3">
          <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-1 text-xs ${ok ? 'border-emerald-400 text-emerald-700 dark:text-emerald-300' : 'border-red-400 text-red-700 dark:text-red-300'}`}>
            <Activity className="h-3.5 w-3.5" />
            {ok === null ? 'проверка…' : ok ? 'онлайн' : 'нет ответа'}
          </span>
          <Button variant="secondary" size="sm" onClick={toggleTheme} aria-label="Toggle theme">
            {theme === 'dark' ? <Sun className="h-4 w-4" /> : <MoonStar className="h-4 w-4" />}
          </Button>
        </div>
      </div>
    </header>
  )
}
