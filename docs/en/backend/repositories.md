# Repositories and Unit of Work

## Overview

The backend uses the **Repository pattern** and **Unit of Work pattern** to abstract data access and manage database transactions. This architecture isolates domain logic from infrastructure concerns, making the codebase more maintainable and testable.

## Architecture

```
API Handler → Service/Use Case → UnitOfWork → Repositories → Database
```

### Flow

1. **API Handler** receives HTTP request
2. **Service/Use Case** orchestrates business logic
3. **UnitOfWork** manages transaction boundaries and provides access to repositories
4. **Repositories** perform data access operations
5. **Database** stores and retrieves data

## Repository Layer

### Interfaces

Repository interfaces are defined in `app/domain/repositories/base.py`:

- **`IRepository[T]`** - Base repository protocol with CRUD operations:
  - `add(entity)` - Add entity to repository
  - `get(id)` - Retrieve entity by ID
  - `list(**filters)` - List entities matching filters
  - `delete(id)` - Delete entity by ID

- **`IGenerationRepository`** - Repository for Generation entities:
  - Extends `IRepository[Generation]`
  - `list_by_user(user_id, limit, offset)` - List generations for a user with pagination
  - `count_by_user(user_id)` - Count generations for a user

- **`IUserRepository`** - Repository for User entities:
  - Extends `IRepository[User]`
  - `get_by_email(email)` - Retrieve user by email
  - `get_by_username(username)` - Retrieve user by username
  - `get_by_email_or_username(email, username)` - Retrieve user by email or username
  - `get_settings(user_id)` - Get user settings
  - `save_settings(settings)` - Save user settings

### Implementations

SQLAlchemy implementations are in `app/infra/repositories/`:

- **`SqlAlchemyGenerationRepository`** - Implements `IGenerationRepository`
- **`SqlAlchemyUserRepository`** - Implements `IUserRepository`

Repositories use synchronous SQLAlchemy Session internally, wrapping DB calls in `asyncio.to_thread` to avoid blocking the event loop.

## Unit of Work

### Purpose

**UnitOfWork** manages transaction boundaries and coordinates multiple repositories within a single transaction.

### Usage

```python
from app.infra.uow import get_uow

# In a service or handler
uow = get_uow()
async with uow:
    user = await uow.users.get(user_id)
    generation = await uow.generations.get(generation_id)
    # Transaction commits automatically on successful exit
    # Rolls back on exceptions
```

### Properties

- **`uow.users`** - Access to `IUserRepository`
- **`uow.generations`** - Access to `IGenerationRepository`

### Transaction Management

- **Commit**: Automatically commits on successful exit from `async with` block
- **Rollback**: Automatically rolls back on exceptions
- **Session Management**: Creates and closes session if not provided

## Rules

### ✅ Do

- Use `UnitOfWork` for all database operations
- Access repositories through `uow.users` and `uow.generations`
- Wrap operations in `async with uow:` blocks
- Let UnitOfWork manage transaction boundaries

### ❌ Don't

- **Do NOT** use `Session` directly in handlers or services
- **Do NOT** call `db.add()`, `db.commit()`, `db.rollback()` directly
- **Do NOT** use `db.query()` or `db.get()` directly
- **Do NOT** create repositories manually - use UnitOfWork

## Examples

### Creating a User

```python
from app.infra.uow import get_uow
from app.domain.models import User, UserSettings

uow = get_uow()
async with uow:
    user = User(email=email, username=username, password_hash=hash)
    await uow.users.add(user)
    await uow.users.save_settings(UserSettings(user_id=user.id, data={}))
# Transaction commits automatically
```

### Querying Generations

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

### Updating User Settings

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

## Benefits

1. **Testability**: Easy to mock repositories for unit tests
2. **Flexibility**: Can switch between different data access implementations
3. **Transaction Safety**: UnitOfWork ensures atomic operations
4. **Separation of Concerns**: Domain logic doesn't depend on SQLAlchemy
5. **Maintainability**: Clear boundaries between layers

## Migration Notes

When migrating existing code:

1. Replace `db: Session = Depends(get_db)` with `uow = get_uow()`
2. Wrap operations in `async with uow:`
3. Replace `db.query(Model)` with `await uow.repositories.method()`
4. Remove direct `db.add()`, `db.commit()`, `db.rollback()` calls

