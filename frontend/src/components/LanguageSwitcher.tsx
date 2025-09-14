import { useTranslation } from 'react-i18next'
import { setLang } from '../i18n/i18n'

export default function LanguageSwitcher({ compact = false }: { compact?: boolean }) {
  const { i18n } = useTranslation()
  const lang = i18n.language === 'ru' ? 'ru' : 'en'

  if (compact) {
    const toggle = () => setLang(lang === 'ru' ? 'en' : 'ru')
    return (
      <button
        type="button"
        onClick={toggle}
        className="rounded-md border bg-background px-2 h-8 text-xs hover:bg-accent/50"
        aria-label="Switch language"
        title={lang === 'ru' ? 'Switch to English' : 'Переключить на русский'}
      >
        {lang.toUpperCase()}
      </button>
    )
  }

  return (
    <select
      className="rounded-md border bg-background p-2 text-sm"
      value={lang}
      onChange={(e)=>setLang(e.target.value as 'en'|'ru')}
      aria-label="Language"
    >
      <option value="ru">Русский</option>
      <option value="en">English</option>
    </select>
  )
}
