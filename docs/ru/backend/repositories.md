# Репозитории и Unit of Work

## Обзор

Бэкенд использует паттерны **Repository** и **Unit of Work** для абстракции доступа к данным и управления транзакциями базы данных. Эта архитектура изолирует доменную логику от инфраструктурных деталей, делая код более поддерживаемым и тестируемым.

## Архитектура

```
API Handler → Service/Use Case → UnitOfWork → Repositories → Database
```

### Поток данных

1. **API Handler** получает HTTP запрос
2. **Service/Use Case** оркестрирует бизнес-логику
3. **UnitOfWork** управляет границами транзакций и предоставляет доступ к репозиториям
4. **Repositories** выполняют операции доступа к данным
5. **Database** хранит и извлекает данные

## Слой репозиториев

### Интерфейсы

Интерфейсы репозиториев определены в `app/domain/repositories/base.py`:

- **`IRepository[T]`** - Базовый протокол репозитория с CRUD операциями:
  - `add(entity)` - Добавить сущность в репозиторий
  - `get(id)` - Получить сущность по ID
  - `list(**filters)` - Список сущностей по фильтрам
  - `delete(id)` - Удалить сущность по ID

- **`IGenerationRepository`** - Репозиторий для сущностей Generation:
  - Расширяет `IRepository[Generation]`
  - `list_by_user(user_id, limit, offset)` - Список генераций пользователя с пагинацией
  - `count_by_user(user_id)` - Подсчет генераций пользователя

- **`IUserRepository`** - Репозиторий для сущностей User:
  - Расширяет `IRepository[User]`
  - `get_by_email(email)` - Получить пользователя по email
  - `get_by_username(username)` - Получить пользователя по username
  - `get_by_email_or_username(email, username)` - Получить пользователя по email или username
  - `get_settings(user_id)` - Получить настройки пользователя
  - `save_settings(settings)` - Сохранить настройки пользователя

### Реализации

Реализации на SQLAlchemy находятся в `app/infra/repositories/`:

- **`SqlAlchemyGenerationRepository`** - Реализует `IGenerationRepository`
- **`SqlAlchemyUserRepository`** - Реализует `IUserRepository`

Репозитории используют синхронный SQLAlchemy Session внутри, оборачивая вызовы БД в `asyncio.to_thread` для избежания блокировки event loop.

## Unit of Work

### Назначение

**UnitOfWork** управляет границами транзакций и координирует работу нескольких репозиториев в рамках одной транзакции.

### Использование

```python
from app.infra.uow import get_uow

# В сервисе или обработчике
uow = get_uow()
async with uow:
    user = await uow.users.get(user_id)
    generation = await uow.generations.get(generation_id)
    # Транзакция автоматически коммитится при успешном выходе
    # Откатывается при исключениях
```

### Свойства

- **`uow.users`** - Доступ к `IUserRepository`
- **`uow.generations`** - Доступ к `IGenerationRepository`

### Управление транзакциями

- **Commit**: Автоматически коммитит при успешном выходе из блока `async with`
- **Rollback**: Автоматически откатывает при исключениях
- **Управление сессией**: Создает и закрывает сессию, если не предоставлена

## Правила

### ✅ Можно

- Использовать `UnitOfWork` для всех операций с БД
- Обращаться к репозиториям через `uow.users` и `uow.generations`
- Оборачивать операции в блоки `async with uow:`
- Позволять UnitOfWork управлять границами транзакций

### ❌ Нельзя

- **НЕ** использовать `Session` напрямую в обработчиках или сервисах
- **НЕ** вызывать `db.add()`, `db.commit()`, `db.rollback()` напрямую
- **НЕ** использовать `db.query()` или `db.get()` напрямую
- **НЕ** создавать репозитории вручную - использовать UnitOfWork

## Примеры

### Создание пользователя

```python
from app.infra.uow import get_uow
from app.domain.models import User, UserSettings

uow = get_uow()
async with uow:
    user = User(email=email, username=username, password_hash=hash)
    await uow.users.add(user)
    await uow.users.save_settings(UserSettings(user_id=user.id, data={}))
# Транзакция автоматически коммитится
```

### Запрос генераций

```python
from app.infra.uow import get_uow

uow = get_uow()
async with uow:
    total = await uow.generations.count_by_user(user_id)
    generations = await uow.generations.list_by_user(
        user_id, 
        limit=20, 
        offset=0
    )
```

### Обновление настроек пользователя

```python
from app.infra.uow import get_uow

uow = get_uow()
async with uow:
    settings = await uow.users.get_settings(user_id)
    if not settings:
        settings = UserSettings(user_id=user_id, data={})
    settings.data.update(new_data)
    await uow.users.save_settings(settings)
```

## Преимущества

1. **Тестируемость**: Легко мокировать репозитории для unit-тестов
2. **Гибкость**: Можно переключаться между разными реализациями доступа к данным
3. **Безопасность транзакций**: UnitOfWork обеспечивает атомарность операций
4. **Разделение ответственности**: Доменная логика не зависит от SQLAlchemy
5. **Поддерживаемость**: Четкие границы между слоями

## Заметки по миграции

При миграции существующего кода:

1. Заменить `db: Session = Depends(get_db)` на `uow = get_uow()`
2. Оборачивать операции в `async with uow:`
3. Заменить `db.query(Model)` на `await uow.repositories.method()`
4. Удалить прямые вызовы `db.add()`, `db.commit()`, `db.rollback()`

