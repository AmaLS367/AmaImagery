import { Outlet } from 'react-router-dom'

import { Footbar } from '../components/Footbar'
import { Topbar } from '../components/Topbar'

type ProductLayoutProps = {
  theme: 'light' | 'dark'
  toggleTheme: () => void
}

export function ProductLayout({ theme, toggleTheme }: ProductLayoutProps) {
  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground overflow-x-hidden">
      <Topbar theme={theme} toggleTheme={toggleTheme} />
      <main className="container flex-1 pt-0">
        <Outlet />
      </main>
      <Footbar />
    </div>
  )
}
