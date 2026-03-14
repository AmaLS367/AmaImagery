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
        className="inline-flex h-10 items-center rounded-full border border-border/70 bg-card/80 px-3 text-xs font-semibold uppercase tracking-[0.18em] text-foreground/75 shadow-panel hover:bg-card"
        aria-label="Switch language"
        title={lang === 'ru' ? 'Switch to English' : 'Переключить на русский'}
      >
        {lang.toUpperCase()}
      </button>
    )
  }

  return (
    <select
      className="h-11 rounded-[18px] border border-border/70 bg-card/80 px-4 text-sm shadow-panel"
      value={lang}
      onChange={(e)=>setLang(e.target.value as 'en'|'ru')}
      aria-label="Language"
    >
      <option value="ru">Русский</option>
      <option value="en">English</option>
    </select>
  )
}
