# genai — Руководство по проекту (Русский)

## Обзор

Проект — генератор изображений (NSFW). Содержит:
- Бэкенд: Python + FastAPI, слушает порт 8000 и предоставляет эндпоинты `/health`, `/generate`, `/file`.
- Фронтенд: React + TypeScript + Vite, dev-сервер на 5173, страницы: Генерация, История, Настройки.

В этом руководстве: как запускать, архитектура, логи, процесс генерации и отладка.

---

## Быстрый старт (разработка)

Требования:
- Python 3.11+ (используйте venv)
- Node.js 18+ и npm

Команды (PowerShell):

```powershell
# Активировать виртуальное окружение (в репозитории):
.\.venv\Scripts\Activate.ps1

# Установить зависимости (если не установлены):
pip install -r requirements.txt

# Запустить бэкенд:
python run.py

# Фронтенд:
cd frontend
npm install
npm run dev
# Открыть http://localhost:5173
```

Важно: фронтенд использует прокси в `vite.config.ts`, поэтому запросы с клиента делайте относительными (`/generate`).

---

## Структура проекта (важные файлы)

- `run.py` — точка входа бекенда
- `app/` — пакет бекенда
  - `server.py` — маршруты и API
  - `inference/pipeline.py` — пайплайн генерации
  - `logging_setup.py` — конфиг логов
- `frontend/` — React приложение
  - `src/lib/api.ts` — функции для fetch
  - `src/pages/Generate.tsx` — UI генерации
  - `src/lib/queue.ts` — RequestQueue
  - `vite.config.ts` — dev сервер и proxy
- `logs/` — логи приложения

---

## Процесс генерации

1. Юзер нажимает «Сгенерировать» в `Generate.tsx`.
2. Формируется payload и ставится задача в `RequestQueue`.
3. `generateJSON` делает fetch на `/generate` (POST).
4. Vite прокси перенаправляет `/generate` на `http://localhost:8000/generate`.
5. Бэкенд запускает пайплайн, сохраняет результат и возвращает `{path, prompt_hash, corrections}`.
6. Фронтенд показывает картинку через `/file?path=...`.

---

## Логи

- Backend: структурированные JSON записи в `logs/app`, `logs/errors`, `logs/generations`.
- Frontend: используйте DevTools Console и Network для проверки отправки запросов и ответов.

---

## Отладка: кнопка не отправляет запрос

1. Проверьте Console — должны быть логи `Button clicked` и `gen() function called`.
2. Если логов нет — обработчик клика не вызывается (overlay, disabled button).
3. Если лог есть, но в Network нет запроса на `/generate` — проверьте `generateJSON` и `RequestQueue`.
4. Протестируйте напрямую через curl к `http://localhost:8000/generate`.

---

## Docker

- `Dockerfile` собирает образ и запускает `python run.py`. Для продакшна нужно донастроить экспорт портов и тома с моделями.

---
