# Документация миграций

## Обзор

Заметки по миграциям и эволюции схемы для **AmaImagery**.

## Текущая реальность миграций

Репозиторий использует Alembic и актуальное дерево миграций в `migrations/`.

Известные ревизии в репозитории:
- `506057d97046_init`
- `91c0d4413c57_generation_lifecycle_and_is_superuser`
- `b4655aadfa03_security_indexes_and_checks`

## Ключевые темы

### 📋 Заметки по рефакторингу
- refactor-ы, влияющие на схему
- изменения lifecycle данных
- schema changes для auth/admin

### 🔄 Руководства по миграции
- запуск `alembic upgrade head`
- создание новых ревизий
- синхронизация env/config с ожиданиями БД

### 🏗️ Архитектурные изменения
- persistence lifecycle очереди
- поддержка superuser/admin
- security indexes и checks

## Для разработчиков

- держите migration changes в том же PR, что и model/code changes
- лучше документировать реальные ревизии, чем aspirational migration guides

## Для операторов

- применяйте миграции до того, как ожидать parity между API и worker после deploy
- для документированного production path используйте PostgreSQL
