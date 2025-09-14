import React from 'react'
import { useTranslation } from 'react-i18next'
import '../styles/error404.css'

export default function Error404() {
  const { t } = useTranslation()

  const quick = [
    { href: '/',            k: 'generator' },
    { href: '/guide',       k: 'guide'     },
    { href: '/faq',         k: 'faq'       },
    { href: '/about',       k: 'about'     },
  ]

  return (
    <div className="e404">
      <section className="e404__hero">
        <div className="e404__container">
          <span className="e404__badge">{t('error404:code')}</span>

          <div className="e404__code" aria-label={t('error404:code') as string}>
            <span className="glitch" data-text={t('error404:code') as string}>
              {t('error404:code')}
            </span>
          </div>

          <h1 className="e404__title">{t('error404:title')}</h1>
          <p className="e404__subtitle">{t('error404:lead')}</p>
          <p className="e404__subtitle">{t('error404:hint')}</p>

          <div className="e404__actions">
            <a href="/" className="e404__btn e404__btn--primary">{t('error404:actions.home')}</a>
            <a href="/faq" className="e404__btn">{t('error404:actions.faq')}</a>
            <button type="button" className="e404__btn" onClick={() => history.back()}>
              {t('error404:actions.back')}
            </button>
            <button type="button" className="e404__btn" onClick={() => window.location.reload()}>
              {t('error404:actions.retry')}
            </button>
          </div>

          <div className="e404__search">
            <input
              className="e404__input"
              placeholder={t('error404:search.placeholder') as string}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  const q = (e.target as HTMLInputElement).value.trim()
                  if (q) window.location.href = `/?q=${encodeURIComponent(q)}`
                }
              }}
            />
          </div>
        </div>
      </section>

      <section className="e404__section">
        <div className="e404__container">
          <h2 className="e404__section-title">{t('error404:quick.title')}</h2>
          <div className="e404__grid">
            {quick.map(({ href, k }) => (
              <a key={k} href={href} className="e404__card">
                <div className="e404__card-title">{t(`error404:quick.items.${k}.title`)}</div>
                <div className="e404__card-desc">{t(`error404:quick.items.${k}.desc`)}</div>
                <span className="e404__card-cta">{t('error404:quick.open')}</span>
              </a>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
