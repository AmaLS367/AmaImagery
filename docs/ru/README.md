# Документация AI Image Generator (Русский)

Добро пожаловать в документацию **AI Image Generator**! Это полное руководство охватывает все аспекты системы, от установки до развертывания.

## 🎯 Что такое AI Image Generator?

AI Image Generator — это мощная платформа для генерации изображений на базе Stable Diffusion с возможностью самостоятельного развертывания. Возможности:

- 🎨 **Высококачественная генерация изображений** с Stable Diffusion 1.5
- ✏️ **Редактирование изображений** и манипуляция
- 🔍 **Увеличение разрешения** для улучшенного качества
- 🛡️ **Встроенные функции безопасности** и модерация контента
- 🔒 **Корпоративная безопасность** с JWT аутентификацией
- 📊 **Мониторинг и метрики** с Prometheus
- 🌐 **Современный веб-интерфейс** на React
- 🐳 **Готовое развертывание** с Docker

## 📚 Разделы документации

### [🔧 Бэкенд](./backend/README.md)
Полная документация бэкенда включая FastAPI, API endpoints, сервисы, базу данных и ML inference pipeline.

### [🎨 Фронтенд](./frontend/README.md)
Документация фронтенда включая React компоненты, управление состоянием, стилизацию и интеграцию с API.

### [🐳 Docker](./docker/README.md)
Документация Docker и контейнеризации включая конфигурации Docker Compose и развертывание.

### [🧪 Тесты](./tests/README.md)
Документация тестирования включая unit тесты, integration тесты, E2E тесты и лучшие практики.

### [🤖 Модели](./models/README.md)
Документация ML моделей включая Stable Diffusion, AmaFusion, DreamShaper, VAE и IP-Adapter.

### [🚀 Развертывание](./deployment/README.md)
Руководства по production развертыванию включая настройку окружения, облачное развертывание и обслуживание.

### [📜 Скрипты](./scripts/README.md)
Документация для bootstrap, build, migration и утилитарных скриптов.

### [💻 Разработка](./development/README.md)
Руководства для разработчиков включая установку, структуру проекта, стандарты кодирования и contributing.

### [🔄 Миграции](./migrations/README.md)
Заметки о рефакторинге и миграциях документирующие архитектурные изменения и руководства по обновлению.

### [🔒 Безопасность](./security/README.md)
Документация безопасности включая аутентификацию, авторизацию, rate limiting и лучшие практики.

### [⚡ Функции](./features/README.md)
Документация функций объясняющая генерацию изображений, редактирование, увеличение и модерацию контента.

### [🔍 Устранение неполадок](./troubleshooting/README.md)
Частые проблемы, коды ошибок и решения для GPU, памяти и проблем производительности.

### [⚖️ Юридическая информация](./legal/README.md)
Юридическая информация включая лицензии, лицензии моделей, источники данных и ограничения использования.

### [📚 Справочник](./reference/README.md)
Быстрый справочник по API, конфигурации, CLI командам, переменным окружения и глоссарий.

### [🎓 Учебные материалы](./tutorials/README.md)
Пошаговые руководства для частых задач и продвинутых функций.

## 🚀 Быстрый старт

### Для разработчиков
1. Прочитайте [Начало работы](./development/getting-started.md)
2. Настройте [Окружение разработки](./development/setup/windows.md)
3. Изучите [Структуру проекта](./development/project-structure.md)
4. Узнайте о [Тестировании](./tests/README.md)

### Для DevOps
1. Проверьте [Системные требования](./deployment/requirements.md)
2. Следуйте [Руководству по Docker развертыванию](./docker/getting-started.md)
3. Настройте [Переменные окружения](./deployment/environment/environment-variables.md)
4. Настройте [Мониторинг](./deployment/production/monitoring.md)

### Для пользователей API
1. Прочитайте [Обзор API](./backend/api/overview.md)
2. Узнайте об [Аутентификации](./backend/api/authentication.md)
3. Изучите [API Endpoints](./backend/api/endpoints/images.md)
4. Посмотрите [Примеры API](./backend/api/examples.md)

## 🏗️ Обзор архитектуры

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │◄────►│    Backend   │◄────►│  Database   │
│   (React)   │      │   (FastAPI)  │      │ (PostgreSQL)│
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   ML Models  │
                     │ (Stable Diff)│
                     └──────────────┘
```

Подробнее в [Документации архитектуры](./backend/architecture.md).

## 📦 Технологический стек

**Бэкенд:**
- FastAPI 0.116.1
- Python 3.11+
- PyTorch 2.2.2
- Diffusers 0.29.2
- PostgreSQL
- Redis

**Фронтенд:**
- React + TypeScript
- Vite
- Tailwind CSS
- i18next (интернационализация)

**Инфраструктура:**
- Docker & Docker Compose
- Nginx
- Prometheus метрики
- Alembic миграции

## 🔗 Быстрые ссылки

- [Руководство по установке](./development/getting-started.md)
- [Документация API](./backend/api/overview.md)
- [Настройка Docker](./docker/getting-started.md)
- [Contributing](../../CONTRIBUTING.md)
- [Устранение неполадок](./troubleshooting/common-issues.md)

## 📞 Получение помощи

- Проверьте [Устранение неполадок](./troubleshooting/README.md) для частых проблем
- Просмотрите [Коды ошибок](./troubleshooting/error-codes.md)
- Смотрите [FAQ](./troubleshooting/common-issues.md)

## 📄 Лицензия

Этот проект использует несколько лицензий. Подробнее в [Юридическая информация](./legal/README.md):
- Код: См. LICENSE проекта
- Модели Stable Diffusion: CreativeML Open RAIL-M
- VAE: MIT License

---

**Версия:** 0.1.0 | **Последнее обновление:** 11 марта 2026

