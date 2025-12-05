# Документация разработки

## Обзор

Полное руководство для разработчиков по настройке, разработке и внесению вклада в проект AI Image Generator.

## Начало работы

### Предварительные требования
- Python 3.11+
- Node.js 18+
- Git
- Docker (опционально, но рекомендуется)
- NVIDIA GPU с CUDA 11.8+ (для локальной разработки)

### Быстрая настройка

1. **Клонировать репозиторий**
```bash
git clone <repository-url>
cd genai
```

2. **Настроить бэкенд**
```bash
python -m venv .venv
.venv\Scripts\activate  # Linux: source .venv/bin/activate
pip install -r requirements.txt
```

3. **Настроить фронтенд**
```bash
cd frontend
npm install
```

4. **Настроить окружение**
```bash
cp .env.example .env
# Отредактируйте .env с вашими настройками
```

5. **Запустить миграции**
```bash
python -m alembic upgrade head
```

6. **Запустить dev серверы**
```bash
# Терминал 1 - Бэкенд
python run_dev.py

# Терминал 2 - Фронтенд
cd frontend
npm run dev
```

## Разделы документации

- [Начало работы](./getting-started.md) - Детальное руководство по установке
- [Настройка](./setup/) - Установка под конкретные платформы
  - [Windows](./setup/windows.md)
  - [Linux](./setup/linux.md)
  - [macOS](./setup/macos.md)
- [Структура проекта](./project-structure.md) - Обзор кодовой базы
- [Стандарты кодирования](./coding-standards.md) - Стиль кода и соглашения
- [Git workflow](./git-workflow.md) - Ветвление и коммиты
- [Отладка](./debugging.md) - Техники отладки
- [Contributing](./contributing.md) - Как внести вклад
- [Code review](./code-review.md) - Процесс ревью кода

## Инструменты разработки

### Качество кода
- **Линтинг:** ruff, eslint
- **Форматирование:** black, prettier
- **Проверка типов:** mypy, TypeScript
- **Тестирование:** pytest, vitest

### Настройка IDE
- VSCode (рекомендуется)
- PyCharm
- Рекомендуемые расширения/плагины

## Структура проекта

```
genai/
├── app/              # Бэкенд приложение
│   ├── api/         # API роуты
│   ├── core/        # Основной функционал
│   ├── services/    # Бизнес-логика
│   └── ...
├── frontend/         # React фронтенд
│   ├── src/
│   └── ...
├── tests/           # Бэкенд тесты
├── migrations/      # Миграции БД
├── models/          # ML модели
├── docker/          # Docker конфиги
└── scripts/         # Утилитарные скрипты
```

См. [Структура проекта](./project-structure.md) для подробностей.

## Частые задачи

### Запуск тестов
```bash
pytest tests/
cd frontend_tests && npm test
```

### Создание миграций
```bash
alembic revision --autogenerate -m "описание"
alembic upgrade head
```

### Сборка для Production
```bash
# Бэкенд
docker build -t genai-backend .

# Фронтенд
cd frontend && npm run build
```

## Получение помощи

- Проверьте [Устранение неполадок](../troubleshooting/README.md)
- Просмотрите существующие issues
- Спросите в discussions

