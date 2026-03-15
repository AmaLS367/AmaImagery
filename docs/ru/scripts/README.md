# Документация скриптов

## Обзор

Коллекция utility scripts для bootstrap, build, migration, запуска, smoke-проверок и поддержки **AmaImagery**. Скрипты доступны для Linux, Windows и Python helper flows.

## Категории скриптов

### 🚀 Bootstrap scripts
Инициализация development и deployment prerequisites.

**Linux:** `scripts/linux/bootstrap.sh`
**Windows:** `scripts/windows/bootstrap.ps1`

### 🔨 Build scripts
Сборка Docker images и frontend assets.

**Linux:** `scripts/linux/build_images.sh`, `scripts/linux/build_frontend.sh`
**Windows:** `scripts/windows/build_images.ps1`, `scripts/windows/build_frontend.ps1`

### 🗄️ Migration scripts
Запуск миграций базы данных.

**Linux:** `scripts/linux/migrate.sh`
**Windows:** `scripts/windows/migrate.ps1`

### ⚙️ Run scripts
Запуск local и production Docker flows.

**Linux:** `scripts/linux/run_local.sh`, `scripts/linux/run_prod.sh`
**Windows:** `scripts/windows/run_local.ps1`, `scripts/windows/run_prod.ps1`

### 🧪 Validation scripts
Smoke и helper checks.

**Linux:** `scripts/linux/smoketest.sh`, `scripts/linux/preflight.sh`
**Windows:** `scripts/windows/smoketest.ps1`, `scripts/windows/preflight.ps1`

### 🌱 Seed scripts
Заполнение начальными данными.

**Linux:** `scripts/linux/seed.sh`
**Windows:** `scripts/windows/seed.ps1`

### 🐍 Python utilities

- `generate_context.py` - Генерация компактного project snapshot
- `generate_secret_key.py` - Генерация secret keys
- `warm_cache.py` - Прогрев model cache
- `test_generate.py` - Реальный generation request с polling результата
- `delete_cache.py` - Очистка Python cache artifacts
- `Checkdoubles.py` - Проверка duplicate FastAPI routes

## Разделы документации

| Тема | Статус |
|------|--------|
| Bootstrap deep-dive | 🚧 Coming soon |
| Build deep-dive | 🚧 Coming soon |
| Migration deep-dive | 🚧 Coming soon |
| Utilities deep-dive | 🚧 Coming soon |
| Windows vs Linux comparison | 🚧 Coming soon |

## Краткий справочник

### Первый запуск
```bash
# Linux
./scripts/linux/bootstrap.sh

# Windows
.\scripts\windows\bootstrap.ps1
```

### Локальный запуск
```bash
# Linux
./scripts/linux/run_local.sh

# Windows
.\scripts\windows\run_local.ps1
```

### Сборка фронтенда
```bash
# Linux
./scripts/linux/build_frontend.sh

# Windows
.\scripts\windows\build_frontend.ps1
```

## Требования к скриптам

- **Linux:** Bash 4.0+
- **Windows:** PowerShell 5.1+
- **Python:** 3.11+ для Python utilities
