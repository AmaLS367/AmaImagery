# Скрипты деплоя — как пользоваться

Пакет даёт кросс‑ОС скрипты для локального запуска и прод‑похожего окружения.

## Зависимости
- Docker + Docker Compose
- Node.js (npm или pnpm) — для сборки фронта
- Драйверы NVIDIA + `nvidia-smi` (для GPU‑профиля)

## Структура
- `docker/compose.local.yml` — дев-стек (api + redis + postgres + nginx)
- `docker/compose.prod.yml` — прод‑профиль (GPU‑резервация)
- `docker/compose.cpu.yml` — CPU‑фоллбек
- `docker/.env.*.example` — шаблоны окружения
- `docker/nginx.conf` — статика + прокси на API
- `scripts/linux/*` — Bash‑скрипты (Linux)
- `scripts/macos/*` — Bash‑скрипты (macOS)
- `scripts/windows/*` — PowerShell‑скрипты (Windows)

## Типовой запуск (Linux/macOS)
```bash
scripts/linux/build_frontend.sh
scripts/linux/preflight.sh local
scripts/linux/run_local.sh
# (когда добавишь Alembic)
scripts/linux/migrate.sh && scripts/linux/seed.sh
scripts/linux/smoketest.sh
```

## Типовой запуск (Windows)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/build_frontend.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/preflight.ps1 -Profile local
powershell -ExecutionPolicy Bypass -File scripts/windows/run_local.ps1
# (когда добавишь Alembic)
powershell -ExecutionPolicy Bypass -File scripts/windows/migrate.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/seed.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/smoketest.ps1
```

## Прод‑профиль
- Заполни `docker/.env.prod` на основе `.env.prod.example`
- Собери фронт: `build_frontend` (linux/windows)
- Запуск: `run_prod` (linux/windows)
- Дымовой тест: `smoketest` по публичному URL или `http://host:80`

## Примечания
- Фронт **должен** раздаваться из `frontend/dist` (в образе — `/app/static`).
- `SECRET_KEY`, `MODEL_ID`, `REDIS_URL`, `DATABASE_URL` — обязательны.
- GPU: `compose.prod.yml`; CPU‑фоллбек: `compose.cpu.yml`.
