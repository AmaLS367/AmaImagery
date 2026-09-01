# Документация разработки

## Обзор

Практическое руководство по настройке, разработке и внесению вклада в **AmaImagery**.

## Начало работы

### Предварительные требования
- Python 3.11+
- Node.js 18+
- Git
- Docker (опционально, но удобно для full-stack local runs)
- NVIDIA GPU нужен только если вы хотите локально работать с Diffusers на GPU

### Быстрая настройка

1. **Клонировать репозиторий**
```bash
git clone https://github.com/AmaLS367/AmaImagery
cd AmaImagery
```

2. **Настроить backend**
```bash
python -m venv .venv
.venv\Scripts\activate  # Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
# ML-зависимости нужны только для локального Diffusers runtime
pip install -e ".[ml]"
```

3. **Настроить frontend**
```bash
cd frontend
npm ci
cd ..
```

4. **Настроить окружение**
```bash
cp .env.example .env
# Отредактируйте .env под своё окружение
```

5. **Запустить миграции**
```bash
alembic upgrade head
```

6. **Запустить процессы разработки**
```bash
# Терминал 1 - Backend API
python run.py

# Терминал 2 - Generation worker
python -m app.entrypoints.generation_worker

# Терминал 3 - Frontend
cd frontend
npm run dev
```

## Разделы документации

| Тема | Статус |
|------|--------|
| Deep-dive по Getting Started | 🚧 Coming soon |
| Platform-specific setup pages | 🚧 Coming soon |
| Детальный разбор структуры проекта | 🚧 Coming soon |
| Отдельная страница coding standards | 🚧 Coming soon |
| Отдельная страница git workflow | 🚧 Coming soon |
| Отдельная страница debugging | 🚧 Coming soon |
| Отдельная страница code review | 🚧 Coming soon |
| [Contributing](../../CONTRIBUTING.md) | ✅ Доступно |

## Инструменты разработки

### Качество кода
- **Линтинг:** ruff
- **Форматирование:** repo-specific workflow, при необходимости black для Python
- **Проверка типов:** mypy, TypeScript
- **Тестирование:** pytest, frontend typecheck/build, Playwright-based frontend tests из дерева тестов

### IDE Setup
- VSCode
- PyCharm
- Любой редактор, в котором удобно вести Python + TypeScript

## Структура проекта

```
amaimagery/
├── app/              # Backend application
├── frontend/         # React frontend
├── tests/            # Backend и integration tests
├── migrations/       # Alembic migrations
├── models/           # Local model assets и metadata
├── docker/           # Docker configs и env templates
└── scripts/          # Utility scripts
```

## Частые задачи

### Запуск тестов
```bash
pytest -q
python -m ruff check app tests
python -m mypy app

cd frontend
npm run typecheck
npm run build
```

### Создание миграций
```bash
alembic revision -m "описание"
alembic upgrade head
```

### Локальный запуск через Docker
```bash
docker compose --env-file docker/.env.docker -f docker/compose.local.yml up -d --build
```

## Получение помощи

- Смотрите [Troubleshooting](../troubleshooting/README.md)
- Проверяйте существующие issues и discussions
- Используйте [Reference](../reference/README.md) для endpoint-ов, команд и env-переменных
