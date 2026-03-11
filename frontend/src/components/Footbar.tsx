import { memo } from 'react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'

type Props = { className?: string }

function goTab(name: string) {
  try { window.dispatchEvent(new CustomEvent('goto-tab', { detail: name })) } catch {}
}

export const Footbar = memo(function Footbar({ className }: Props) {

  const { t } = useTranslation()

  return (
    <div className="w-[calc(100vw-(100vw-110%))] overflow-x-hidden mt-auto shrink-0 mt-10">
      <motion.footer
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.18 }}
        className={[
          // Цвет как у страницы (без затемнения)
          'border-t border-border/60 bg-background w-full',
          'text-sm text-muted-foreground',
          className || '',
        ].join(' ')}
        aria-label="Нижний информационный блок"
      >
        <div className="mx-auto max-w-6xl px-3 md:px-6 py-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
            {/* Brand */}
            <div className="space-y-2">
              <div className="text-lg font-semibold tracking-tight text-foreground">AmaImagery</div>
              <p className="text-xs leading-relaxed text-foreground/70">
                {t('footbar.brandTag')}
              </p>
            </div>

            {/* О AmaImagery */}
            <div>
              <div className="mb-2 font-semibold text-foreground">{t('nav.about')}</div>
              <ul className="space-y-1">
                <li>
                  <button onClick={() => goTab('about')} className="hover:text-foreground underline-offset-4 hover:underline">
                    {t('nav.about')}
                  </button>
                </li>
                <li>
                <button onClick={() => goTab('privacy')} className="hover:text-foreground underline-offset-4 hover:underline">
                  {t('nav.privacy')}
                </button>
                </li>
              </ul>
            </div>

            {/* Полезное */}
            <div>
              <div className="mb-2 font-semibold text-foreground">Полезное</div>
              <ul className="space-y-1">
                <li>
                  <button onClick={() => goTab('guide')} className="hover:text-foreground underline-offset-4 hover:underline">
                    {t('actions.guide')}
                  </button>
                </li>
                <li>
                  <button onClick={() => goTab('history')} className="hover:text-foreground underline-offset-4 hover:underline">
                    {t('nav.history')}
                  </button>
                </li>
                <li>
                  <button onClick={() => goTab('settings')} className="hover:text-foreground underline-offset-4 hover:underline">
                    {t('nav.settings')}
                  </button>
                </li>
              </ul>
            </div>

            {/* Помощь */}
            <div>
              <div className="mb-2 font-semibold text-foreground">Помощь</div>
              <ul className="space-y-1">
                <li>
                  <button onClick={() => goTab('faq')} className="hover:text-foreground underline-offset-4 hover:underline">
                    {t('nav.faq')}
                  </button>
                </li>
                <li>
                  <a href="mailto:support@amaimagery.local" className="hover:text-foreground underline-offset-4 hover:underline">
                    {t('footbar.support')}
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </motion.footer>
    </div>
  )
})
