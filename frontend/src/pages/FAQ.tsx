import { useMemo, useState } from 'react'
import '../styles/faq.css'
import { useTranslation } from 'react-i18next'

type QA = { q: string; a: string; cat: string }

const CATEGORIES = [
  { slug: 'start', name: 'Начало' },
  { slug: 'quality', name: 'Качество' },
  { slug: 'speed', name: 'Скорость' },
  { slug: 'history', name: 'История' },
  { slug: 'files', name: 'Файлы' },
  { slug: 'errors', name: 'Ошибки' },
  { slug: 'other', name: 'Разное' },
]

const DATA: QA[] = [
  { cat: 'start', q: 'С чего начать?', a: 'Откройте «Гайд по промптам», возьмите базовый пример и запустите генерацию. Для первого запуска не усложняйте запрос.' },
  { cat: 'start', q: 'Как быстро понять, что работает?', a: 'Делайте 2–3 коротких варианта запроса, меняя только один фактор: стиль, освещение или композицию.' },
  { cat: 'quality', q: 'Как повысить качество изображения?', a: 'Добавьте референс, пропишите освещение и композицию. Увеличивайте размер кадра только при реальной необходимости.' },
  { cat: 'quality', q: 'Нужно ли писать длинные описания?', a: 'Нет. Четкий стиль + сцена + свет работают лучше длинных полотен.' },
  { cat: 'quality', q: 'Результат меняется при повторах — почему?', a: 'В генерации есть доля случайности. Чтобы приблизить повтор, используйте те же параметры и формулировки.' },
  { cat: 'speed', q: 'Почему генерация идёт долго?', a: 'Из‑за очереди запросов и ограничений на стороне прокси. Подождите завершения или уменьшите размер кадра.' },
  { cat: 'speed', q: 'Как ускорить работу?', a: 'Снижайте размер кадра, избегайте бесконечных повторов, не запускайте десятки одинаковых задач подряд.' },
  { cat: 'history', q: 'Где найти прошлые результаты?', a: 'Во вкладке «История». Там же можно запустить повтор и немного скорректировать параметры.' },
  { cat: 'history', q: 'Как быстро повторить удачную картинку?', a: 'Откройте её в «Истории» и нажмите повтор. Меняйте на минимуме только нужные поля.' },
  { cat: 'files', q: 'Как скачать итог?', a: 'Откройте карточку результата в «Истории» и жмите кнопку скачивания.' },
  { cat: 'files', q: 'Где хранятся мои картинки?', a: 'В «Истории» вашего интерфейса. Локальный путь/срок хранения зависит от вашей сборки.' },
  { cat: 'errors', q: 'Пишет «слишком много запросов» (429)', a: 'Вы уткнулись в ограничение частоты. Подождите несколько секунд и повторите. Серии кликов подряд только ухудшают ситуацию.' },
  { cat: 'errors', q: 'Ошибка сети или пустой ответ', a: 'Проверьте интернет/ВПН. Если повторяется — напишите в поддержку и уточните время и шаги.' },
  { cat: 'other', q: 'Можно ли использовать на телефоне?', a: 'Да. Интерфейс адаптивный, но на слабых устройствах большие кадры считаются медленнее.' },
  { cat: 'other', q: 'Где смотреть новости и изменения?', a: 'Загляните сюда позже — раздел дополняется. При срочном вопросе — напишите в поддержку.' },
]

export default function FAQ() {
  const [query, setQuery] = useState('')
  const [active, setActive] = useState<string>('start')
  const { t } = useTranslation()

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return DATA.filter(item => {
      const byCat = item.cat === active
      if (!q) return byCat
      const t = (item.q + ' ' + item.a).toLowerCase()
      return byCat && t.includes(q)
    })
  }, [query, active])

  return (
    <main className="faq">
      {/* Hero */}
      <section className="faq__hero">
        <div className="faq__container">
          <span className="faq__badge">{t('nav.faq')}</span>
          <h1 className="faq__title">{t('nav.faq')}</h1>
          <p className="faq__subtitle">Короткие решения типовых задач. Пройдитесь по вкладкам — нужное найдёте быстрее.</p>

          <div className="faq__search">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Поиск по вопросам"
              className="faq__searchInput"
              aria-label="Поиск по FAQ"
            />
            <button
              className="faq__searchBtn"
              onClick={() => window.dispatchEvent(new CustomEvent('goto-tab', { detail: 'guide' }))}
            >
              {t('actions.guide')}
            </button>
          </div>

          <div className="faq__tabs" role="tablist" aria-label="Категории вопросов">
            {CATEGORIES.map(cat => (
              <button
                key={cat.slug}
                role="tab"
                aria-selected={active === cat.slug}
                className={['faq__tab', active === cat.slug ? 'is-active' : ''].join(' ')}
                onClick={() => setActive(cat.slug)}
              >
                {cat.name}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* List */}
      <section className="faq__section">
        <div className="faq__container">
          <div className="faq__list">
            {filtered.map((item, i) => (
              <details key={i} className="faq__item">
                <summary><span className="faq__q">{item.q}</span></summary>
                <div className="faq__a">{item.a}</div>
              </details>
            ))}
            {!filtered.length && (
              <div className="faq__empty">Пусто. Попробуйте другую вкладку или измените запрос.</div>
            )}
          </div>
        </div>
      </section>

      {/* Contact */}
      <section className="faq__section faq__section--muted">
        <div className="faq__container faq__contact">
          <div className="faq__contactText">Не нашли ответ?</div>
          <a className="faq__btn" href="mailto:support@genai.local">Написать в поддержку</a>
        </div>
      </section>
    </main>
  )
}
