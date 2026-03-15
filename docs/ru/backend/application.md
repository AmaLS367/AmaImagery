# Слой приложения (Use Cases)

## Обзор

Слой приложения оркестрирует бизнес-сценарии, координируя работу между доменной логикой, репозиториями и внешними сервисами. Use cases представляют полные бизнес-операции и обеспечивают четкую границу между API-слоем и доменной логикой.

## Архитектурный поток

```
HTTP Handler → DTO → Use Case → UoW → Repositories → Providers → Queue
```

### Детальный поток

1. **HTTP Handler** (`app/api/v1/`) - Получает HTTP запрос, валидирует входные данные
2. **DTO** (`app/domain/schemas.py`) - Объекты передачи данных для запросов/ответов
3. **Use Case** (`app/application/use_cases/`) - Оркестрирует бизнес-операцию
4. **Unit of Work** (`app/infra/uow.py`) - Управляет границами транзакций
5. **Repositories** (`app/infra/repositories/`) - Абстракция доступа к данным
6. **Providers** (`app/infra/providers/`) - Интеграция с внешними сервисами
7. **Queue** (`app/infra/queue/`) - Асинхронная обработка задач

## Структура Use Case

### Базовые классы

Все use cases следуют единой структуре:

- **`Command`** - Входные данные для use case (dataclass)
- **`UseCaseResult[TData]`** - Выходные данные с полями `success`, `data` и `error`
- **`UseCase`** - Протокол, определяющий контракт use case

### Пример Use Case

```python
from app.application.use_cases.base import Command, UseCaseResult, UseCase
from dataclasses import dataclass

@dataclass
class MyCommand(Command):
    field1: str
    field2: int

@dataclass
class MyResult:
    result_id: str
    status: str

class MyUseCase:
    def __init__(self, uow: SqlAlchemyUnitOfWork):
        self.uow = uow
    
    async def __call__(self, command: MyCommand) -> UseCaseResult[MyResult]:
        try:
            # Бизнес-логика здесь
            async with self.uow:
                # Использование репозиториев, провайдеров и т.д.
                pass
            
            return UseCaseResult(
                success=True,
                data=MyResult(result_id="123", status="ok"),
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
            )
```

## Текущие Use Cases

### GenerateImageUseCase

**Расположение:** `app/application/use_cases/generate_image.py`

**Назначение:** Оркестрирует асинхронный процесс генерации изображений.

**Зависимости:**
- `UnitOfWork` - Для доступа к базе данных
- `ProviderRegistry` - Для провайдеров генерации изображений
- `TaskQueue` - Для асинхронной обработки задач

**Поток:**
1. Валидирует параметры запроса
2. Проверяет политики безопасности
3. Ставит задачу в очередь
4. Возвращает ID задачи

**Использование:**
```python
command = GenerateImageCommand(
    user_id="user-123",
    prompt="красивый пейзаж",
    width=768,
    height=1152,
    # ... другие параметры
)

use_case = GenerateImageUseCase(uow=get_uow())
result = await use_case(command)

if result.success:
    task_id = result.data.task_id
else:
    error = result.error
```

### GetGenerationStatusUseCase

**Расположение:** `app/application/use_cases/get_generation_status.py`

**Назначение:** Получает статус задачи генерации.

**Зависимости:**
- `UnitOfWork` - Для загрузки сохранённой записи генерации
- `ArtifactService` - Для сборки download metadata, когда артефакт уже существует

**Поток:**
1. Загружает состояние генерации из PostgreSQL
2. Строит публичный payload из сохранённого lifecycle record
3. Возвращает данные статуса или ошибку

**Использование:**
```python
command = GetGenerationStatusCommand(task_id="task-123")
use_case = GetGenerationStatusUseCase()
result = await use_case(command)

if result.success:
    status = result.data.status
    image_path = result.data.image_path
else:
    error = result.error
```

## Добавление новых Use Cases

### Шаг 1: Создать Command

Определите структуру входных данных:

```python
# app/application/use_cases/my_use_case.py
from dataclasses import dataclass
from app.application.use_cases.base import Command

@dataclass
class MyCommand(Command):
    param1: str
    param2: int
```

### Шаг 2: Создать Result Data

Определите структуру выходных данных:

```python
@dataclass
class MyResult:
    result_id: str
    data: dict
```

### Шаг 3: Реализовать Use Case

Реализуйте класс use case:

```python
from app.application.use_cases.base import UseCaseResult
from app.infra.uow import SqlAlchemyUnitOfWork

class MyUseCase:
    def __init__(self, uow: SqlAlchemyUnitOfWork):
        self.uow = uow
    
    async def __call__(self, command: MyCommand) -> UseCaseResult[MyResult]:
        try:
            async with self.uow:
                # Бизнес-логика
                result_data = await self._do_work(command)
            
            return UseCaseResult(
                success=True,
                data=MyResult(result_id="123", data=result_data),
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
            )
    
    async def _do_work(self, command: MyCommand):
        # Детали реализации
        pass
```

### Шаг 4: Экспортировать из пакета

Добавьте в `app/application/use_cases/__init__.py`:

```python
from app.application.use_cases.my_use_case import (
    MyCommand,
    MyUseCase,
    MyResult,
)

__all__ = [
    # ... существующие экспорты
    "MyCommand",
    "MyUseCase",
    "MyResult",
]
```

### Шаг 5: Использовать в API Handler

Создайте функцию dependency injection и используйте в обработчике:

```python
# app/api/v1/my_endpoint.py
from app.application.use_cases.my_use_case import MyCommand, MyUseCase
from app.infra.uow import get_uow

def get_my_use_case() -> MyUseCase:
    return MyUseCase(uow=get_uow())

@router.post("/my-endpoint")
async def my_handler(
    request: MyRequest,
    use_case: MyUseCase = Depends(get_my_use_case),
):
    command = MyCommand(
        param1=request.param1,
        param2=request.param2,
    )
    
    result = await use_case(command)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return MyResponse(data=result.data)
```

## Лучшие практики

### ✅ Можно

- Держать use cases сфокусированными на одной бизнес-операции
- Использовать `UnitOfWork` для всех операций с БД
- Возвращать `UseCaseResult` с четкими состояниями успех/ошибка
- Держать оркестрационную логику в use cases, а не в handlers
- Использовать доменные сервисы для чистых бизнес-правил

### ❌ Нельзя

- **Не** обращайтесь к репозиториям напрямую в handlers
- **Не** размещайте бизнес-логику в handlers
- **Не** смешивайте инфраструктурные заботы с бизнес-логикой
- **Не** создавайте use cases, которые слишком широки или делают несколько вещей
- **Не** используйте `Session` напрямую в use cases

## Преимущества

1. **Разделение ответственности** - Четкие границы между слоями
2. **Тестируемость** - Легко тестировать use cases изолированно
3. **Переиспользование** - Use cases можно вызывать из разных точек входа
4. **Поддерживаемость** - Бизнес-логика централизована и легко найти
5. **Гибкость** - Легко изменить реализацию без влияния на API

## Связь с другими слоями

- **Доменный слой** - Use cases используют доменные модели и сервисы
- **Инфраструктурный слой** - Use cases зависят от репозиториев, провайдеров, очередей
- **API слой** - Handlers вызывают use cases, никогда не обращаются к репозиториям напрямую
- **Сервисы** - Use cases могут использовать доменные сервисы для бизнес-правил

