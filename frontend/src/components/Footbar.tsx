import { memo } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'

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
    heading: 'Resources',
    links: [
      { href: appRoutes.promptGuide, labelKey: 'actions.guide' },
      { href: appRoutes.history, labelKey: 'nav.history' },
      { href: appRoutes.settings, labelKey: 'nav.settings' },
    ],
  },
  {
    heading: 'Help',
    links: [
      { href: appRoutes.faq, labelKey: 'nav.faq' },
      { href: 'mailto:support@amaimagery.local', labelKey: 'footbar.support', external: true },
    ],
  },
] as const

export const Footbar = memo(function Footbar({ className }: Props) {
  const { t } = useTranslation()

  return (
    <div className="mt-auto w-full shrink-0 overflow-x-hidden">
      <motion.footer
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.18 }}
        className={['mt-10 w-full border-t border-border/60 bg-background/70 text-sm text-muted-foreground backdrop-blur-xl', className || ''].join(' ')}
        aria-label="Footer"
      >
        <div className="page-shell py-8">
          <div className="surface-card grid grid-cols-1 gap-6 p-6 sm:grid-cols-2 md:grid-cols-4 md:p-8">
            <div className="space-y-3">
              <div className="font-display text-2xl font-semibold tracking-[-0.05em] text-foreground">AmaImagery</div>
              <p className="text-xs leading-relaxed text-foreground/70">{t('footbar.brandTag')}</p>
            </div>

            {footerColumns.map((column) => (
              <div key={column.heading ?? column.headingKey}>
                <div className="mb-3 text-xs font-semibold uppercase tracking-[0.24em] text-muted-foreground">
                  {column.heading ? column.heading : t(column.headingKey)}
                </div>
                <ul className="space-y-1">
                  {column.links.map((link) => (
                    <li key={link.href}>
                      {'external' in link && link.external ? (
                        <a href={link.href} className="underline-offset-4 hover:text-foreground hover:underline">
                          {t(link.labelKey)}
                        </a>
                      ) : (
                        <Link to={link.href} className="underline-offset-4 hover:text-foreground hover:underline">
                          {t(link.labelKey)}
                        </Link>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </motion.footer>
    </div>
  )
})
