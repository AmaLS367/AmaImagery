# Справочная документация

## Обзор

Быстрый справочник по текущему контракту AmaImagery: реальные endpoints, реальные команды, реальные env-файлы и порты/сервисы, которые существуют сейчас.

## Разделы справочника

| Раздел | Статус |
|--------|--------|
| Deep-dive страницы по API | 🚧 Coming soon |
| Deep-dive страницы по конфигурации | 🚧 Coming soon |
| Deep-dive страницы по CLI | 🚧 Coming soon |
| Расширенный env reference | 🚧 Coming soon |
| Глоссарий | 🚧 Coming soon |

Пока эта README остаётся каноническим quick reference.

## API Endpoints

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/v1/auth/register` | `POST` | Регистрация нового пользователя |
| `/api/v1/auth/login` | `POST` | Вход пользователя |
| `/api/v1/auth/logout` | `POST` | Выход |
| `/api/v1/auth/refresh` | `POST` | Обновление токена |
| `/api/v1/auth/me` | `GET` | Текущий пользователь |
| `/api/v1/auth/forgot-password` | `POST` | Старт reset-password flow |
| `/api/v1/auth/reset-password` | `POST` | Завершение reset-password flow |
| `/api/v1/auth/change-password` | `POST` | Смена пароля в авторизованной сессии |
| `/api/v1/images/generate` | `POST` | Отправка generation job |
| `/api/v1/images/status/{task_id}` | `GET` | Polling статуса генерации |
| `/api/v1/users/me/settings` | `GET`, `PATCH` | Чтение/обновление пользовательских настроек |
| `/api/v1/users/me/generations` | `GET` | История генераций |
| `/api/v1/users/me/hygiene-mode` | `GET`, `PATCH` | Чтение/обновление hygiene mode |
| `/api/v1/file` | `GET` | Скачивание signed artifact |
| `/api/v1/nsfw/users/me/nsfw` | `PATCH` | Переключение NSFW preference |
| `/api/v1/nsfw/check` | `POST` | Проверка moderation rules |
| `/api/v1/nsfw/rules` | `GET` | Просмотр загруженных правил |
| `/api/v1/nsfw/reload` | `POST` | Перезагрузка rules cache |
| `/api/v1/health` | `GET` | Liveness |
| `/api/v1/healthz` | `GET` | Readiness |
| `/admin/` | `GET` | Admin landing page |

## Ключевые переменные окружения

| Переменная | Описание |
|------------|----------|
| `DATABASE_URL` | Основная строка подключения к БД |
| `REDIS_URL` | Подключение Redis для очереди и лимитов |
| `SECRET_KEY` | Критически важный секрет приложения |
| `FRONTEND_ORIGIN` | Frontend origin для браузера и email flow |
| `PROVIDERS_ENABLED` | Список включённых provider-ов |
| `PROVIDERS_DEFAULT_NAME` | Имя default provider-а |
| `MODEL_ID` | Локальный model path или identifier |
| `COMFYUI_BASE_URL` | HTTP endpoint ComfyUI |
| `COMFYUI_WEBSOCKET_URL` | WebSocket endpoint ComfyUI |
| `NO_REDIS` | Redis-off режим для local/test |
| `NO_NETWORK` | Переключатель network guard |
| `REFRESH_COOKIE_SECURE` | Переключатель secure cookie |
| `FILE_SIGNING_ENABLED` | Переключатель signed file delivery |

## Частые команды

```bash
# Backend
python run.py
python -m app.entrypoints.generation_worker
alembic upgrade head
pytest -q
python -m ruff check app tests
python -m mypy app

# Frontend
cd frontend
npm ci
npm run dev
npm run typecheck
npm run build

# Docker
docker compose --env-file docker/.env.docker -f docker/compose.local.yml up -d --build
docker compose --env-file docker/.env.docker -f docker/compose.local.yml -f docker/compose.local.diffusers.yml up -d --build
docker compose --env-file docker/.env.prod -f docker/compose.prod.yml up -d --build
```

## Конфигурационные файлы

| Файл | Назначение |
|------|------------|
| `.env.example` | Пример app env |
| `alembic.ini` | Конфигурация Alembic |
| `docker/.env.docker.example` | Пример локального Docker env |
| `docker/.env.verify.comfyui.example` | Профиль верификации ComfyUI |
| `docker/.env.verify.diffusers.example` | Профиль верификации Diffusers |
| `docker/compose.*.yml` | Compose-конфигурации |
| `docker/nginx.conf` | Конфиг Nginx |
| `frontend/vite.config.ts` | Конфиг frontend build/dev |

## Справочник портов

| Сервис | Порт | Описание |
|--------|------|----------|
| Backend API | `8000` | FastAPI приложение |
| Frontend Dev | `5173` | Vite dev server |
| PostgreSQL | `5432` | База данных |
| Redis | `6379` | Backend для очереди и лимитов |
| Nginx | `80` / `443` / `8080` | Reverse proxy в зависимости от стека |

Публичный `/metrics` endpoint по умолчанию в текущем приложении не смонтирован.
