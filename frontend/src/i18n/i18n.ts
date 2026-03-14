import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import en_common from './resources/en/common.json'
import en_errors from './resources/en/errors.json'
import en_generate from './resources/en/generate.json'
import ru_common from './resources/ru/common.json'
import ru_errors from './resources/ru/errors.json'
import ru_generate from './resources/ru/generate.json'
import en_settings from './resources/en/settings.json'
import ru_settings from './resources/ru/settings.json'
import en_history from './resources/en/history.json'
import ru_history from './resources/ru/history.json'
import en_about from './resources/en/about.json'
import ru_about from './resources/ru/about.json'
import en_privacy from './resources/en/privacy.json'
import ru_privacy from './resources/ru/privacy.json'
import en_promptGuide from './resources/en/promptGuide.json'
import ru_promptGuide from './resources/ru/promptGuide.json'
import en_login from './resources/en/login.json'
import ru_login from './resources/ru/login.json'
import en_register from './resources/en/register.json'
import ru_register from './resources/ru/register.json'
import en_reset from './resources/en/reset.json'
import ru_reset from './resources/ru/reset.json'
import en_error404 from './resources/en/error404.json'
import ru_error404 from './resources/ru/error404.json'
import en_navtop from './resources/en/navtop.json'
import ru_navtop from './resources/ru/navtop.json'
import en_landing from './resources/en/landing.json'
import ru_landing from './resources/ru/landing.json'

function detectLang(): string {
  try {
    const qs = new URLSearchParams(window.location.search)
    const q = qs.get('lang')
    if (q) { localStorage.setItem('locale', q); return q }
  } catch {}
  try {
    const ls = localStorage.getItem('locale')
    if (ls) return ls
  } catch {}
  const nav = (navigator.language || 'en').slice(0,2)
  return (nav === 'ru' ? 'ru' : 'en')
}

void i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { common: en_common, errors: en_errors, generate: en_generate, settings: en_settings, history: en_history, about: en_about,
            privacy: en_privacy, promptGuide: en_promptGuide, login: en_login, register: en_register, reset: en_reset, error404: en_error404,
            navtop: en_navtop, landing: en_landing,
       },
      ru: { common: ru_common, errors: ru_errors, generate: ru_generate, settings: ru_settings, history: ru_history, about: ru_about,
            privacy: ru_privacy, promptGuide: ru_promptGuide, login: ru_login, register: ru_register, reset: ru_reset, error404: ru_error404,
            navtop: ru_navtop, landing: ru_landing
       },
    },
    lng: detectLang(),
    fallbackLng: 'en',
    ns: ['common', 'errors', 'generate', 'settings', 
        'history', 'about', 'privacy', 'promptGuide',
        'login', 'register', 'reset', 'error404', 'navtop', 'landing'
      ],
    defaultNS: 'common',
    interpolation: { escapeValue: false },
  })

export default i18n
export function setLang(l: 'en'|'ru') {
  i18n.changeLanguage(l)
  try { localStorage.setItem('locale', l) } catch {}
}
