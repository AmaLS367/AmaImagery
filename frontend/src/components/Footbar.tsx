import { memo } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Zap, Cpu, Fingerprint, ArrowRight } from 'lucide-react'

import { appRoutes } from '../lib/routes'

type Props = { className?: string }

const footerColumns = [
  {
    headingKey: 'nav.about',
    links: [
      { href: appRoutes.about, labelKey: 'nav.about' },
      { href: appRoutes.privacy, labelKey: 'nav.privacy' },
    ],
  },
  {
    headingKey: 'nav.resources',
    links: [
      { href: appRoutes.promptGuide, labelKey: 'actions.guide' },
      { href: appRoutes.history, labelKey: 'nav.history' },
      { href: appRoutes.settings, labelKey: 'nav.settings' },
    ],
  },
  {
    headingKey: 'nav.help',
    links: [
      { href: appRoutes.faq, labelKey: 'nav.faq' },
      { href: 'mailto:support@amaimagery.com', labelKey: 'footbar.support', external: true },
    ],
  },
] as const

export const Footbar = memo(function Footbar({ className }: Props) {
  const { t } = useTranslation()

  return (
    <footer className={cn("runtime-footer-shell w-full pt-20 pb-10", className)}>
      <div className="page-shell">
        <div className="grid gap-12 lg:grid-cols-[1fr_repeat(3,auto)] lg:gap-24">
          <div className="space-y-8 max-w-sm">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="h-4 w-4 rounded-full bg-primary shadow-[0_0_15px_theme(colors.primary.DEFAULT)]" />
                <span className="font-display text-2xl font-bold tracking-tight text-foreground">{t('appName')}</span>
              </div>
              <p className="text-sm leading-relaxed text-foreground/50 font-medium italic dark:text-white/50">
                {t('footbar.brandTag')}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="h-10 w-10 rounded-full border border-border bg-background flex items-center justify-center text-foreground/40 hover:text-primary hover:border-primary/30 transition-all cursor-pointer dark:border-white/10 dark:bg-white/5 dark:text-white/40">
                <Zap className="h-4 w-4" />
              </div>
              <div className="h-10 w-10 rounded-full border border-border bg-background flex items-center justify-center text-foreground/40 hover:text-primary hover:border-primary/30 transition-all cursor-pointer dark:border-white/10 dark:bg-white/5 dark:text-white/40">
                <Cpu className="h-4 w-4" />
              </div>
              <div className="h-10 w-10 rounded-full border border-border bg-background flex items-center justify-center text-foreground/40 hover:text-primary hover:border-primary/30 transition-all cursor-pointer dark:border-white/10 dark:bg-white/5 dark:text-white/40">
                <Fingerprint className="h-4 w-4" />
              </div>
            </div>
          </div>

          {footerColumns.map((column) => (
            <div key={column.headingKey} className="space-y-6">
              <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">
                {t(column.headingKey)}
              </h4>
              <ul className="space-y-3">
                {column.links.map((link) => (
                  <li key={link.href}>
                    {'external' in link && link.external ? (
                      <a 
                        href={link.href} 
                        className="text-sm font-bold text-foreground/60 hover:text-foreground transition-colors flex items-center gap-2 group dark:text-white/60 dark:hover:text-white"
                      >
                        {t(link.labelKey)}
                        <ArrowRight className="h-3 w-3 -rotate-45 opacity-0 group-hover:opacity-100 transition-all" />
                      </a>
                    ) : (
                      <Link 
                        to={link.href} 
                        className="text-sm font-bold text-foreground/60 hover:text-foreground transition-colors dark:text-white/60 dark:hover:text-white"
                      >
                        {t(link.labelKey)}
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-20 pt-10 border-t border-border flex flex-col md:flex-row items-center justify-between gap-6 dark:border-white/5">
          <div className="text-[10px] font-bold uppercase tracking-widest text-foreground/30 dark:text-white/30">
            © {new Date().getFullYear()} AmaImagery Studio. All rights reserved.
          </div>
          <div className="flex items-center gap-8">
             <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-foreground/30 dark:text-white/30">
                <div className="h-1 w-1 rounded-full bg-success" />
                System Operational
             </div>
             <div className="text-[10px] font-bold uppercase tracking-widest text-foreground/30 dark:text-white/30">
                v1.0.4-stable
             </div>
          </div>
        </div>
      </div>
    </footer>
  )
})

function cn(...classes: (string | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}
