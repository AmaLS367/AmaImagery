# Документация скриптов

## Обзор

Коллекция утилитарных скриптов для инициализации, сборки, миграций и управления приложением AI Image Generator. Скрипты доступны для платформ Linux и Windows.

## Категории скриптов

### 🚀 Bootstrap скрипты
Инициализация среды разработки или production со всеми зависимостями и конфигурациями.

**Linux:** `scripts/linux/bootstrap.sh`
**Windows:** `scripts/windows/bootstrap.ps1`

### 🔨 Build скрипты
Сборка Docker образов и фронтенд ассетов.

**Linux:** `scripts/linux/build_images.sh`, `build_frontend.sh`
**Windows:** `scripts/windows/build_images.ps1`, `build_frontend.ps1`

### 🗄️ Migration скрипты
Запуск миграций базы данных.

**Linux:** `scripts/linux/migrate.sh`
**Windows:** `scripts/windows/migrate.ps1`

### ⚙️ Run скрипты
Запуск приложения в разных режимах.

**Linux:** `scripts/linux/run_local.sh`, `run_prod.sh`
**Windows:** `scripts/windows/run_local.ps1`, `run_prod.ps1`

### 🧪 Тестовые скрипты
Запуск smoke тестов и валидации.

**Linux:** `scripts/linux/smoketest.sh`
**Windows:** `scripts/windows/smoketest.ps1`

### 🌱 Seed скрипты
Наполнение базы данных начальными данными.

**Linux:** `scripts/linux/seed.sh`
**Windows:** `scripts/windows/seed.ps1`

### 🐍 Python утилиты
Вспомогательные скрипты на Python.

- `generate_context.py` - Генерация контекста проекта
- `generate_secret_key.py` - Генерация секретных ключей
- `warm_cache.py` - Прогрев кэша моделей
- `Checkdoubles.py` - Проверка дублирующегося кода

## Разделы документации

- [Bootstrap](./bootstrap.md) - Bootstrap скрипты
- [Build](./build.md) - Build скрипты
- [Migration](./migration.md) - Migration скрипты
- [Utilities](./utilities.md) - Утилитарные скрипты
- [Windows vs Linux](./windows-vs-linux.md) - Различия платформ

## Краткий справочник

### Первоначальная настройка
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

### Сборка для Production
```bash
# Linux
./scripts/linux/build_images.sh

# Windows
.\scripts\windows\build_images.ps1
```

## Требования к скриптам

- **Linux:** Bash 4.0+, стандартные GNU инструменты
- **Windows:** PowerShell 5.1+
- **Python:** 3.11+ для Python утилит

