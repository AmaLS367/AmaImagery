# Application Layer (Use Cases)

## Overview

The Application Layer orchestrates business scenarios by coordinating between domain logic, repositories, and external services. Use cases represent complete business operations and provide a clear boundary between the API layer and domain logic.

## Architecture Flow

```
HTTP Handler → DTO → Use Case → UoW → Repositories → Providers → Queue
```

### Detailed Flow

1. **HTTP Handler** (`app/api/v1/`) - Receives HTTP request, validates input
2. **DTO** (`app/domain/schemas.py`) - Request/response data transfer objects
3. **Use Case** (`app/application/use_cases/`) - Orchestrates business operation
4. **Unit of Work** (`app/infra/uow.py`) - Manages transaction boundaries
5. **Repositories** (`app/infra/repositories/`) - Data access abstraction
6. **Providers** (`app/infra/providers/`) - External service integration
7. **Queue** (`app/infra/queue/`) - Asynchronous task processing

## Use Case Structure

### Base Classes

All use cases follow a consistent structure:

- **`Command`** - Input data for the use case (dataclass)
- **`UseCaseResult[TData]`** - Output with `success`, `data`, and `error` fields
- **`UseCase`** - Protocol defining the use case contract

### Example Use Case

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
            # Business logic here
            async with self.uow:
                # Use repositories, providers, etc.
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

## Use Cases

### GenerateImageUseCase

**Location:** `app/application/use_cases/generate_image.py`

**Purpose:** Orchestrates asynchronous image generation workflow.

**Dependencies:**
- `UnitOfWork` - For database access
- `ProviderRegistry` - For image generation providers
- `TaskQueue` - For asynchronous task processing

**Flow:**
1. Validates request parameters
2. Checks safety policies
3. Enqueues task to queue
4. Returns task ID

**Usage:**
```python
command = GenerateImageCommand(
    user_id="user-123",
    prompt="a beautiful landscape",
    width=768,
    height=1152,
    # ... other parameters
)

use_case = GenerateImageUseCase(uow=get_uow())
result = await use_case(command)

if result.success:
    task_id = result.data.task_id
else:
    error = result.error
```

### GetGenerationStatusUseCase

**Location:** `app/application/use_cases/get_generation_status.py`

**Purpose:** Retrieves status of a generation task.

**Dependencies:**
- `UnitOfWork` - For loading the persisted generation record
- `ArtifactService` - For building download metadata when an artifact exists

**Flow:**
1. Loads generation state from PostgreSQL
2. Builds the public payload from the persisted lifecycle record
3. Returns status data or error

**Usage:**
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

## Adding New Use Cases

### Step 1: Create Command

Define the input data structure:

```python
# app/application/use_cases/my_use_case.py
from dataclasses import dataclass
from app.application.use_cases.base import Command

@dataclass
class MyCommand(Command):
    param1: str
    param2: int
```

### Step 2: Create Result Data

Define the output data structure:

```python
@dataclass
class MyResult:
    result_id: str
    data: dict
```

### Step 3: Implement Use Case

Implement the use case class:

```python
from app.application.use_cases.base import UseCaseResult
from app.infra.uow import SqlAlchemyUnitOfWork

class MyUseCase:
    def __init__(self, uow: SqlAlchemyUnitOfWork):
        self.uow = uow
    
    async def __call__(self, command: MyCommand) -> UseCaseResult[MyResult]:
        try:
            async with self.uow:
                # Business logic
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
        # Implementation details
        pass
```

### Step 4: Export from Package

Add to `app/application/use_cases/__init__.py`:

```python
from app.application.use_cases.my_use_case import (
    MyCommand,
    MyUseCase,
    MyResult,
)

__all__ = [
    # ... existing exports
    "MyCommand",
    "MyUseCase",
    "MyResult",
]
```

### Step 5: Use in API Handler

Create dependency injection function and use in handler:

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

## Best Practices

### ✅ Do

- Keep use cases focused on a single business operation
- Use `UnitOfWork` for all database operations
- Return `UseCaseResult` with clear success/error states
- Keep orchestration logic in use cases, not in handlers
- Use domain services for pure business rules

### ❌ Don't

- **Don't** access repositories directly in handlers
- **Don't** put business logic in handlers
- **Don't** mix infrastructure concerns with business logic
- **Don't** create use cases that are too broad or do multiple things
- **Don't** use `Session` directly in use cases

## Benefits

1. **Separation of Concerns** - Clear boundaries between layers
2. **Testability** - Easy to test use cases in isolation
3. **Reusability** - Use cases can be called from different entry points
4. **Maintainability** - Business logic is centralized and easy to find
5. **Flexibility** - Easy to change implementation without affecting API

## Relationship with Other Layers

- **Domain Layer** - Use cases use domain models and services
- **Infrastructure Layer** - Use cases depend on repositories, providers, queues
- **API Layer** - Handlers call use cases, never access repositories directly
- **Services** - Use cases may use domain services for business rules

