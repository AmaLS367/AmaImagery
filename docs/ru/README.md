# Документация AmaImagery (Русский)

Добро пожаловать в документацию **AmaImagery**. Это руководство сохраняет визуальный стиль документации, но приводит тексты, ссылки и обещания в соответствие с текущим репозиторием.

## 🎯 Что такое AmaImagery?

AmaImagery — это self-hosted платформа генерации изображений, в которой сейчас реально есть:

- 🎨 **Генерация изображений** через текущий маршрут `/api/v1/images/generate`
- 🔄 **Асинхронный lifecycle worker-а** с сохранением состояния задач
- 🔌 **Абстракция provider-ов** для `comfyui` и `diffusers`
- 🛡️ **Auth, admin и moderation surface** в backend
- 🌐 **React + Vite фронтенд** со страницами генерации, истории, настроек и auth
- 🐳 **Docker-сценарии развертывания** для local и production режимов

Планируемые или ещё не опубликованные публично возможности вроде edit, upscale и resize остаются видимыми в roadmap/tutorial секциях, но больше не описываются как уже готовые public API.

## 📚 Разделы документации

### [🔧 Бэкенд](./backend/README.md)
Текущая архитектура backend, реальные маршруты, providers, очереди, repositories, observability и admin/readiness.

### [🎨 Фронтенд](./frontend/README.md)
Текущая структура React/Vite фронтенда, маршруты и точки интеграции.

### [🐳 Docker](./docker/README.md)
Compose-файлы, runtime targets, env templates и container flows, которые реально существуют.

### [🧪 Тесты](./tests/README.md)
Стратегия backend-тестов, frontend проверки и актуальные validation-команды.

### [🤖 Модели](./models/README.md)
Текущие model assets, ожидания от provider/runtime и licensing context.

### [🚀 Развертывание](./deployment/README.md)
Production-oriented deployment notes и provider rollout guidance.

### [📜 Скрипты](./scripts/README.md)
Реальные shell, PowerShell и Python helper scripts из репозитория.

### [💻 Разработка](./development/README.md)
Локальная установка, запуск API + worker и текущий developer workflow.

### [🔄 Миграции](./migrations/README.md)
Текущий путь Alembic migration и заметки по эволюции схемы.

### [🔒 Безопасность](./security/README.md)
Security posture, путь для disclosure и чувствительные runtime поверхности.

### [⚡ Функции](./features/README.md)
Текущие функции, provider-specific возможности и planned surfaces.

### [🔍 Устранение неполадок](./troubleshooting/README.md)
Текущие operational issues и debugging notes.

### [⚖️ Юридическая информация](./legal/README.md)
Лицензирование проекта, лицензирование моделей и атрибуция.

### [📚 Справочник](./reference/README.md)
Текущие endpoints, команды, env-переменные и порты.

### [🎓 Учебные материалы](./tutorials/README.md)
Guided material и planned tutorials. Часть пунктов там намеренно остаётся roadmap placeholder-ами.

## 🚀 Быстрый старт

### Для разработчиков
1. Прочитайте [Development](./development/README.md)
2. Изучите [Backend](./backend/README.md)
3. Прогоните проверки из [Tests](./tests/README.md)

### Для операторов / DevOps
1. Откройте [Docker](./docker/README.md)
2. Следуйте [Deployment](./deployment/README.md)
3. Используйте [Provider Rollout](./deployment/provider-rollout.md) при переключении runtime

### Для пользователей API
1. Начните со [Reference](./reference/README.md)
2. Затем откройте [Backend](./backend/README.md)
3. Если окружение ведёт себя не так, как ожидается, проверьте [Troubleshooting](./troubleshooting/README.md)

## 🏗️ Обзор архитектуры

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │◄────►│    Backend   │◄────►│ PostgreSQL  │
│   (React)   │      │   (FastAPI)  │      │ lifecycle   │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  Worker +    │
                     │  Providers   │
                     └──────────────┘
```

Текущая runtime-правда такая:

- PostgreSQL хранит lifecycle state генераций
- Redis — это инфраструктура очереди и лимитов, а не главный источник истины о задаче
- `comfyui` и `diffusers` — реальные provider modes
- admin pages живут под `/admin/*`

## 📦 Технологический стек

**Бэкенд:**
- FastAPI
- Python 3.11+
- PostgreSQL
- Redis
- SQLAlchemy + Alembic

**Фронтенд:**
- React + TypeScript
- Vite
- Tailwind CSS
- i18next

**Инфраструктура:**
- Docker & Docker Compose
- Nginx
- Async generation worker
- Опциональный локальный Diffusers runtime или внешний ComfyUI runtime

## 🔗 Быстрые ссылки

- [Руководство по разработке](./development/README.md)
- [Справочник](./reference/README.md)
- [Docker Setup](./docker/README.md)
- [Contributing](../../CONTRIBUTING.md)
- [Устранение неполадок](./troubleshooting/README.md)

## 📞 Получение помощи

- Начните с [Troubleshooting](./troubleshooting/README.md)
- Смотрите section README для своей области
- Используйте roadmap/tutorial страницы как план, а не как доказательство существования уже готового public API

## 📄 Лицензия

Проект использует несколько лицензий. Подробности в [Legal](./legal/README.md):

- лицензирование кода приложения в корне репозитория
- обязательства по моделям и датасетам в `models/`, `NOTICE.txt` и `ATTRIBUTIONS.md`

---

**Версия:** 0.1.0 | **Последнее обновление:** 15 марта 2026
