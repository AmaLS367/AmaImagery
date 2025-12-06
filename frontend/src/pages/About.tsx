import '../styles/about.css'
import { useTranslation } from 'react-i18next'

export default function About() {

  const { t } = useTranslation()

  return (
    <main className="about">
      {/* Hero */}
      <section className="about__hero">
        <div className="about__container">
          <span className="about__badge">{t('nav.about')}</span>
          <h1 className="about__title">{t('appName')}</h1>
          <p className="about__subtitle">
            {t('about:hero.subtitle')}
          </p>

          <div className="about__cta">
            <button
              className="about__btn about__btn--primary"
              onClick={() => window.dispatchEvent(new CustomEvent('goto-tab', { detail: 'guide' }))}
            >
              {t('actions.guide')}
            </button>
            <button
              className="about__btn"
              onClick={() => window.dispatchEvent(new CustomEvent('goto-tab', { detail: 'history' }))}
            >
              {t('nav.history')}
            </button>
            <button
              className="about__btn"
              onClick={() => window.dispatchEvent(new CustomEvent('goto-tab', { detail: 'settings' }))}
            >
              {t('nav.settings')}
            </button>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="about__section">
        <div className="about__container">
          <h2 className="about__h2">{t('about:features.title')}</h2>
          <div className="about__grid">
            <article className="about__card">
              <h3 className="about__h3">{t('about:features.cards.control.title')}</h3> 
              <p className="about__p">
                {t('about:features.cards.control.text')}
              </p>
            </article>
            <article className="about__card">
              <h3 className="about__h3">{t('about:features.cards.stable.title')}</h3>
              <p className="about__p">
                {t('about:features.cards.stable.text')}
              </p>
            </article>
            <article className="about__card">
              <h3 className="about__h3">{t('about:features.cards.guide.title')}</h3>
              <p className="about__p">
                {t('about:features.cards.guide.text')}
              </p>
            </article>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="about__section">
        <div className="about__container">
          <h2 className="about__h2">{t('about:how.title')}</h2>
          <ol className="about__steps">
            <li className="about__step">
              <span className="about__stepnum">1</span>
              <div>
                <div className="about__h4">{t('about:how.steps.0.title')}</div>
                <p className="about__p">{t('about:how.steps.0.text')}</p>
              </div>
            </li>
            <li className="about__step">
              <span className="about__stepnum">2</span>
              <div>
                <div className="about__h4">{t('about:how.steps.1.title')}</div>
                <p className="about__p">{t('about:how.steps.1.text')}</p>
              </div>
            </li>
            <li className="about__step">
              <span className="about__stepnum">3</span>
              <div>
                <div className="about__h4">{t('about:how.steps.2.title')}</div>
                <p className="about__p">{t('about:how.steps.2.text')}</p>
              </div>
            </li>
          </ol>
        </div>
      </section>

      {/* Compact help strip */}
      <hr className="about__divider" />
      <section className="about__quick">
        <div className="about__container about__links">
          <button className="about__link" onClick={() => window.dispatchEvent(new CustomEvent('goto-tab', { detail: 'faq' }))}>
            {t('nav.faq')}
          </button>
          <a className="about__link" href="mailto:support@amaimagery.local">{t('footbar.support')}</a>
        </div>
      </section>
    </main>
  )
}
