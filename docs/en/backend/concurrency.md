# Async ORM and Concurrency Model

## Overview

The backend uses **async SQLAlchemy** for all database operations to ensure non-blocking I/O and optimal event loop utilization. Heavy operations are delegated to background workers to keep HTTP handlers responsive.

## Async ORM

### Database Operations

All database operations use async SQLAlchemy:

- **Async Engine** - `create_async_engine()` with async drivers (asyncpg for PostgreSQL, aiosqlite for SQLite)
- **Async Session** - `AsyncSession` for all database interactions
- **Async Repositories** - All repository methods are `async def`
- **Async UnitOfWork** - Transaction management through async context managers

### Example

```python
from app.infra.uow import get_uow

# All database operations are async
uow = get_uow()
async with uow:
    user = await uow.users.get(user_id)
    generations = await uow.generations.list_by_user(user_id)
    # Transaction commits automatically
```

### Rules

- ✅ **All database operations MUST be async**
- ✅ **Use `await` for all repository methods**
- ✅ **Use `AsyncSession` in all handlers and services**
- ❌ **Do NOT use sync `Session` in async code**
- ❌ **Do NOT use `asyncio.to_thread` for database operations** (use async API instead)

## Concurrency Model

### Architecture Layers

```
HTTP Handler (FastAPI) → Use Case → UnitOfWork → Repository → Async DB
                                    ↓
                              TaskQueue (Redis)
                                    ↓
                              Worker Process
                                    ↓
                          Heavy Operations (ML, etc.)
```

### Request Flow

1. **HTTP Handler** - FastAPI endpoint receives request
   - **Light operations only**: validation, authentication, request parsing
   - **No blocking operations**: no heavy computation, no long-running tasks
   - **Quick response**: returns immediately or enqueues task

2. **Use Case** - Business logic orchestration
   - Coordinates between repositories, providers, and queues
   - Validates business rules
   - Enqueues heavy tasks if needed

3. **UnitOfWork** - Transaction management
   - Manages async database transactions
   - Coordinates multiple repositories

4. **Repository** - Data access
   - Async database queries
   - Non-blocking I/O operations

5. **TaskQueue** - Asynchronous task processing
   - Heavy operations are enqueued
   - Redis is used as transport queue only

6. **Worker Process** - Background processing
   - Picks up tasks from queue
   - Performs heavy operations (ML inference, image processing)
   - Updates lifecycle state in PostgreSQL

## Heavy Operations

### What Goes to Workers

The following operations **MUST** be performed in background workers:

- **ML Inference** - Image generation, upscaling, editing
- **Image Processing** - Resizing, format conversion, transformations
- **File Operations** - Large file uploads/downloads, batch processing
- **External API Calls** - Long-running external service calls
- **Data Processing** - Large dataset processing, batch operations

### What Stays in Handlers

The following operations are **acceptable** in HTTP handlers:

- **Validation** - Input validation, business rule checks
- **Authentication** - Token verification, user lookup
- **Light Queries** - Simple database lookups (user info, settings)
- **Status Checks** - Task status retrieval from queue
 - **Status Checks** - Task status retrieval from database-backed lifecycle
- **Response Formatting** - Data transformation for API responses

## Rules and Best Practices

### ✅ Do

- **Keep handlers lightweight** - Return quickly, enqueue heavy work
- **Use async for all DB operations** - Never block the event loop
- **Delegate heavy operations** - Use TaskQueue and workers
- **Monitor task status** - Use status endpoints for long operations
- **Handle errors gracefully** - Return appropriate HTTP status codes

### ❌ Don't

- **Do NOT perform heavy operations in handlers** - No ML inference, no long file operations
- **Do NOT use sync database calls** - Always use async API
- **Do NOT block the event loop** - No CPU-intensive work in handlers
- **Do NOT wait for worker results** - Use async task model with status polling
- **Do NOT mix sync and async** - Keep async code consistent

## Queue and Workers

### Task Queue

- **Purpose**: Decouple HTTP requests from heavy processing
- **Implementation**: Redis-based transport queue with DB-backed lifecycle tracking
- **Task Lifecycle**: `queued` → `running` → `completed`/`failed`

### Workers

- **Purpose**: Process heavy tasks asynchronously
- **Deployment**: Separate processes/containers
- **Scaling**: Can run multiple worker instances

### Example Flow

```python
# Handler: Quick response
@router.post("/api/v1/images/generate")
async def generate(request: GenReq):
    use_case = GenerateImageUseCase(uow=get_uow())
    result = await use_case(GenerateImageCommand(...))
    return TaskResp(task_id=result.data.task_id, status="queued")

# Worker: Heavy processing
async def run_worker():
    while True:
        generation_id = await task_queue.dequeue()
        # Heavy ML inference here
        generation = await uow.generations.get(generation_id)
        submission = await provider.submit(...)
        result = await provider.wait_for_result(submission, timeout_sec=...)
        await uow.generations.update_fields(generation_id, status="completed", result=result.metadata)
```

## Event Loop Safety

### Non-Blocking Operations

All I/O operations are non-blocking:

- **Database**: Async SQLAlchemy with asyncpg/aiosqlite
- **Redis**: Async Redis client
- **HTTP**: Async httpx for external calls
- **File I/O**: Async file operations where possible

### Blocking Operations

Some operations are inherently blocking and must be handled carefully:

- **ML Inference**: PyTorch operations (wrapped in `asyncio.to_thread` in providers)
- **CPU-intensive tasks**: Delegated to workers
- **Synchronous libraries**: Wrapped or replaced with async alternatives

## Performance Considerations

### Handler Performance

- **Target**: < 100ms response time for handlers
- **Database queries**: Optimized with indexes, connection pooling
- **Caching**: Redis for frequently accessed data
- **Connection pooling**: Async engine with connection pool

### Worker Performance

- **Throughput**: Process multiple tasks concurrently
- **Resource management**: GPU memory, CPU cores
- **Error handling**: Retry logic, failure tracking
- **Monitoring**: Task duration, success/failure rates

## Migration Notes

When migrating from sync to async:

1. Replace `Session` with `AsyncSession`
2. Replace `session.query()` with `select()` + `await session.execute()`
3. Replace `session.get()` with `await session.get()`
4. Remove `asyncio.to_thread` wrappers for DB operations
5. Update all repository methods to `async def`
6. Update test fixtures to use async sessions

## Testing Async Code

### Test Fixtures

Use async fixtures for database tests:

```python
@pytest_asyncio.fixture
async def uow():
    uow = get_uow()
    async with uow:
        yield uow
        await uow._session.rollback()
```

### Async Test Functions

Mark async test functions appropriately:

```python
@pytest.mark.asyncio
async def test_user_repository(uow):
    user = await uow.users.get(user_id)
    assert user is not None
```

