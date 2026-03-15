# Документация фронтенда

## Обзор

Фронтенд — это React-приложение на TypeScript и Vite. Его текущая UI-поверхность сосредоточена на генерации, истории, настройках, auth и информационных product pages.

## Ключевые возможности

### 🎨 Пользовательский интерфейс
- адаптивный product UI
- стилизация на Tailwind CSS
- поддержка light/dark theme
- доступные UI primitives

### 🌐 Интернационализация
- multi-language support на i18next
- сейчас активны English и Russian
- дополнительные языки запланированы

### 🔄 Управление состоянием
- React Context API
- кастомные хуки
- route-based composition страниц

### 📡 Интеграция с API
- auth flows
- отправка generation и polling статуса
- интеграция history/settings
- обработка ошибок в текущем app shell

## Текущая Route Surface

Текущие маршруты включают:

- `/`
- `/generate`
- `/history`
- `/settings`
- `/login`
- `/register`
- `/forgot-password`
- `/reset-password`
- `/about`
- `/faq`
- `/prompt-guide`
- `/privacy`
- `/404`

Legacy redirects:
- `/gen`
- `/guide`
- `/reset`

## Разделы документации

| Тема | Статус |
|------|--------|
| Architecture page | 🚧 Coming soon |
| Setup page | 🚧 Coming soon |
| Components deep-dive | 🚧 Coming soon |
| Pages deep-dive | 🚧 Coming soon |
| State management deep-dive | 🚧 Coming soon |
| API integration deep-dive | 🚧 Coming soon |
| i18n deep-dive | 🚧 Coming soon |
| Styling guide | 🚧 Coming soon |
| Build & deploy guide | 🚧 Coming soon |
| Frontend testing guide | 🚧 Coming soon |

## Быстрый старт

```bash
cd frontend
npm ci
npm run dev
```

## Технологический стек

- **Framework:** React 18
- **Язык:** TypeScript
- **Инструмент сборки:** Vite
- **Стилизация:** Tailwind CSS
- **i18n:** i18next
- **Роутинг:** React Router
