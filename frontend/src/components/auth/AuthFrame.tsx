import type { ReactNode } from 'react'
import { motion } from 'framer-motion'
import { ShieldCheck } from 'lucide-react'

import { SurfacePanel } from '../ui/foundation'
import { cn } from '../../lib/utils'
import { useSettings } from '../../providers/SettingsProvider'

type AuthFrameProps = {
  eyebrow: string
  title: string
  note: string
  leftTitle: string
  leftSubtitle: string
  leftContent: ReactNode
  rightTitle: string
  rightContent: ReactNode
}

export function AuthFrame({
  eyebrow,
  title,
  note,
  leftTitle,
  leftSubtitle,
  leftContent,
  rightTitle,
  rightContent,
}: AuthFrameProps) {
  const { settings } = useSettings()

  return (
    <section className="page-shell py-12 xl:py-24">
      <motion.div 
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      >
        <SurfacePanel
          glass={settings.componentStyle === 'glass' || settings.glass}
          className={cn(
            "overflow-hidden rounded-[48px] border-border shadow-glow",
            settings.visualMode === 'editorial' && "rounded-[36px]",
            settings.visualMode === 'cinematic' && "shadow-[0_36px_120px_-36px_rgba(0,0,0,0.55)]",
          )}
        >
          {/* Header */}
          <div className="grid gap-6 border-b border-border p-8 md:p-12 xl:grid-cols-[1fr_auto] items-center dark:border-white/10">
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
                <ShieldCheck className="h-3 w-3" />
                {eyebrow}
              </div>
              <h1 className="font-display text-4xl font-bold tracking-tight text-foreground dark:text-white sm:text-5xl leading-tight">
                {title}
              </h1>
            </div>
            <div className="text-base leading-relaxed text-foreground/60 dark:text-white/50 max-w-sm xl:text-right font-medium italic">
              {note}
            </div>
          </div>

          {/* Content */}
          <div className="grid gap-8 p-8 md:p-12 xl:grid-cols-[1.1fr_0.9fr]">
            <div className="space-y-10">
              <div className="space-y-4">
                <h2 className="font-display text-4xl font-bold tracking-tight text-foreground dark:text-white sm:text-6xl leading-[1.1]">
                  {leftTitle}
                </h2>
                <p className="max-w-xl text-lg leading-relaxed text-foreground/60 dark:text-white/60 font-medium">
                  {leftSubtitle}
                </p>
              </div>
              <div className="relative">
                {leftContent}
              </div>
            </div>

            <div className="space-y-8 lg:pl-12 xl:border-l xl:border-border dark:xl:border-white/10">
              <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">
                {rightTitle}
              </h3>
              <div className="space-y-6">
                {rightContent}
              </div>
            </div>
          </div>
        </SurfacePanel>
      </motion.div>
    </section>
  )
}
