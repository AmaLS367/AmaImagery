import '../styles/privacy.css'
import { useTranslation } from 'react-i18next'

export default function Privacy() {

  const { t } = useTranslation()

  return (
    <main className="pp">
      {/* Hero */}
      <section className="pp__hero">
        <div className="pp__container">
          <span className="pp__badge">{t('privacy:hero.badge')}</span>
          <h1 className="pp__title">{t('nav.privacy')}</h1>
          <p className="pp__subtitle">{t('privacy:hero.subtitle')}</p>

          <div className="pp__meta">
            <div className="pp__updated">{t('privacy:meta.dateLabel')} [YYYY‑MM‑DD]</div>
            <div className="pp__entity">{t('privacy:meta.ownerLabel')} {t('privacy:meta.owner')}</div>
          </div>

          <div className="pp__cta">
            <button
              className="pp__btn"
              onClick={() => window.dispatchEvent(new CustomEvent('goto-tab', { detail: 'faq' }))}
            >
              {t('nav.faq')}
            </button>
            <button
              className="pp__btn"
              onClick={() => window.dispatchEvent(new CustomEvent('goto-tab', { detail: 'guide' }))}
            >
              {t('actions.guide')}
            </button>
          </div>
        </div>
      </section>

      {/* Contents */}
      <section className="pp__section">
        <div className="pp__container">
          <h2 className="pp__h2">{t('privacy:s1.title').replace('1. ','')}</h2>
          <ol className="pp__toc">
            <li><a href="#pp1">{t('privacy:s1.title')}</a></li>
            <li><a href="#pp2">{t('privacy:s2.title')}</a></li>
            <li><a href="#pp3">{t('privacy:s3.title')}</a></li>
            <li><a href="#pp4">{t('privacy:s4.title')}</a></li>
            <li><a href="#pp5">{t('privacy:s5.title')}</a></li>
            <li><a href="#pp6">{t('privacy:s6.title')}</a></li>
            <li><a href="#pp7">{t('privacy:s7.title')}</a></li>
            <li><a href="#pp8">{t('privacy:s8.title')}</a></li>
            <li><a href="#pp9">{t('privacy:s9.title')}</a></li>
            <li><a href="#pp10">{t('privacy:s10.title')}</a></li>
            <li><a href="#pp11">{t('privacy:s11.title')}</a></li>
            <li><a href="#pp12">{t('privacy:s12.title')}</a></li>
          </ol>
        </div>
      </section>

      <section id="pp1" className="pp__section">
        <div className="pp__container">
          <h2 className="pp__h2">{t('privacy:s1.title')}</h2>
          <ul className="pp__list">
            <li><b>{t('privacy:s1.account_label')}</b> {t('privacy:s1.account_text')}</li>
            <li><b>{t('privacy:s1.work_label')}</b> {t('privacy:s1.work_text')}</li>
            <li><b>{t('privacy:s1.tech_label')}</b> {t('privacy:s1.tech_text')}</li>
            <li><b>{t('privacy:s1.storage_label')}</b> {t('privacy:s1.storage_text')}</li>
            <li><b>{t('privacy:s1.support_label')}</b> {t('privacy:s1.support_text')}</li>
            <li><b>{t('privacy:s1.payments_label')}</b> {t('privacy:s1.payments_text')}</li>
          </ul>
        </div>
      </section>

      <section id="pp2" className="pp__section">
        <div className="pp__container">
          <h2 className="pp__h2">{t('privacy:s2.title')}</h2>
          <ul className="pp__list">
            <li>{t('privacy:s2.service')}</li>
            <li>{t('privacy:s2.security')}</li>
            <li>{t('privacy:s2.improve')}</li>
            <li>{t('privacy:s2.support')}</li>
            <li>{t('privacy:s2.legal')}</li>
          </ul>
        </div>
      </section>

      <section id="pp3" className="pp__section">
        <div className="pp__container">
          <h2 className="pp__h2">{t('privacy:s3.title')}</h2>
          <p className="pp__p">{t('privacy:s3.euNote')}</p>
          <ul className="pp__list">
            <li>{t('privacy:s3.contract')}</li>
            <li>{t('privacy:s3.legitimate')}</li>
            <li>{t('privacy:s3.consent')}</li>
            <li>{t('privacy:s3.obligation')}</li>
          </ul>
        </div>
      </section>

      <section id="pp4" className="pp__section">
        <div className="pp__container">
          <h2 className="pp__h2">{t('privacy:s4.title')}</h2>
          <ul className="pp__list">
            <li>{t('privacy:s4.hosting')}</li>
            <li>{t('privacy:s4.mail')}</li>
            <li>{t('privacy:s4.analytics')}</li>
            <li>{t('privacy:s4.payments')}</li>
          </ul>
            <p className="pp__p">{t('privacy:s4.note')}</p>
        </div>
      </section>

      <section id="pp5" className="pp__section">
        <div className="pp__container">
          <h2 className="pp__h2">{t('privacy:s5.title')}</h2>
          <ul className="pp__list">
            <li>{t('privacy:s5.account')}</li>
            <li>{t('privacy:s5.history')}</li>
            <li>{t('privacy:s5.logs')}</li>
            <li>{t('privacy:s5.support')}</li>
            <li>{t('privacy:s5.backups')}</li>
          </ul>
        </div>
      </section>

      <section id="pp6" className="pp__section">
        <div className="pp__container">
          <h2 className="pp__h2">{t('privacy:s6.title')}</h2>
          <ul className="pp__list">
            <li>{t('privacy:s6.list1')}</li>
            <li>{t('privacy:s6.list2')}</li>
            <li>{t('privacy:s6.list3')}</li>
            <li>{t('privacy:s6.list4')}</li>
          </ul>
          <p className="pp__p">{t('privacy:s6.contactIntro')} <a className="pp__link" href="mailto:[privacy@домен]">[privacy@домен]</a>.</p>
        </div>
      </section>

      <section id="pp7" className="pp__section">
        <div className="pp__container">
          <h2 className="pp__h2">{t('privacy:s7.title')}</h2>
          <ul className="pp__list">
            <li>{t('privacy:s7.enc')}</li>
            <li>{t('privacy:s7.access')}</li>
            <li>{t('privacy:s7.updates')}</li>
          </ul>
          <p className="pp__p">{t('privacy:s7.note')}</p>
        </div>
      </section>

      <section id="pp8" className="pp__section">
        <div className="pp__container">
          <h2 className="pp__h2">{t('privacy:s8.title')}</h2>
          <p className="pp__p">{t('privacy:s8.text')}</p>
        </div>
      </section>

      <section id="pp9" className="pp__section">
        <div className="pp__container">
          <h2 className="pp__h2">{t('privacy:s9.title')}</h2>
          <p className="pp__p">{t('privacy:s9.text')}</p>
        </div>
      </section>

      <section id="pp10" className="pp__section">
        <div className="pp__container">
          <h2 className="pp__h2">{t('privacy:s10.title')}</h2>
          <ul className="pp__list">
            <li>{t('privacy:s10.strict')}</li>
            <li>{t('privacy:s10.optional')}</li>
          </ul>
        </div>
      </section>

      <section id="pp11" className="pp__section">
        <div className="pp__container">
          <h2 className="pp__h2">{t('privacy:s11.title')}</h2>
          <p className="pp__p">{t('privacy:s11.text')}</p>
        </div>
      </section>

      <section id="pp12" className="pp__section pp__section--muted">
        <div className="pp__container">
          <h2 className="pp__h2">{t('privacy:s12.title')}</h2>
          <ul className="pp__list">
            <li>{t('privacy:s12.company')}</li>
            <li>{t('privacy:s12.emailLabel')} <a className="pp__link" href="mailto:[privacy@домен]">{t('privacy:s12.emailValue')}</a></li>
            <li>{t('privacy:s12.dpo')}</li>
          </ul>
        </div>
      </section>
    </main>
  )
}
