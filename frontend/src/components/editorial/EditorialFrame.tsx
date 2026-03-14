import type { ReactNode } from 'react'
import { motion } from 'framer-motion'
import { Sparkles } from 'lucide-react'

import { MetaPill } from '../ui/foundation'
import { cn } from '../../lib/utils'
import { useSettings } from '../../providers/SettingsProvider'

type EditorialFrameProps = {
  eyebrow: string
  title: string
  summary: string
  pills?: string[]
  children: ReactNode
}

export function EditorialFrame({ eyebrow, title, summary, pills = [], children }: EditorialFrameProps) {
  const { settings } = useSettings()

  return (
    <section className="page-shell space-y-12 py-12 xl:py-20">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="runtime-editorial-hero space-y-8"
      >
        <div className="runtime-editorial-copy space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
            <Sparkles className="h-3 w-3" />
            {eyebrow}
          </div>
          
          <div className="space-y-4">
            <h1 className="font-display text-4xl font-bold tracking-tight text-foreground sm:text-6xl lg:text-7xl leading-[1.1]">
              {title}
            </h1>
            <p className={cn(
              "runtime-editorial-summary text-lg leading-relaxed text-foreground/60 dark:text-white/60 font-medium",
              (settings.visualMode === 'cinematic' || settings.visualMode === 'editorial') && "mx-auto",
            )}>
              {summary}
            </p>
          </div>
        </div>

        {pills.length ? (
          <div className={cn(
            "flex flex-wrap gap-2 pt-2",
            (settings.visualMode === 'cinematic' || settings.visualMode === 'editorial') && "justify-center",
          )}>
            {pills.map((pill) => (
              <MetaPill key={pill}>{pill}</MetaPill>
            ))}
          </div>
        ) : null}
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
      >
        {children}
      </motion.div>
    </section>
  )
}
