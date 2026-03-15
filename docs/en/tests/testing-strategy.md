# Testing Strategy

## Overview

This document describes the testing strategy for the backend, including test levels, coverage targets, and guidelines for writing and running tests.

## Test Levels

### Unit Tests

**Location:** `tests/unit/`

**Purpose:** Test individual components in isolation with mocked dependencies.

**Characteristics:**
- Fast execution (no external dependencies)
- Mock external services (database, Redis, HTTP clients)
- Test business logic, utilities, and domain models
- Should be deterministic and repeatable

**When to write:**
- Testing pure functions and utilities
- Testing domain logic and business rules
- Testing service methods with mocked dependencies
- Testing validation and transformation logic

**Examples:**
- `test_safety_blocklist.py` - Safety filtering logic
- `test_settings_failfast.py` - Configuration validation
- `test_utils_prompt_hash.py` - Utility functions

### Integration Tests

**Location:** `tests/integration/` and `tests/infra/`

**Purpose:** Test components working together with real dependencies (database, Redis, etc.).

**Characteristics:**
- Use real database (in-memory SQLite or test PostgreSQL)
- Use real Redis or mocked Redis client
- Test repository implementations
- Test API endpoints with test client
- Slower than unit tests but more realistic

**When to write:**
- Testing repository implementations with real database
- Testing API endpoints end-to-end
- Testing service integration with external systems
- Testing database migrations

**Examples:**
- `test_auth_flow.py` - Authentication API flow
- `test_db_migrations_alembic.py` - Database migrations
- `test_rate_limit_redis.py` - Redis-based rate limiting
- `tests/infra/repositories/` - Repository integration tests

### Application Layer Tests

**Location:** `tests/application/`

**Purpose:** Test use cases and application orchestration logic.

**Characteristics:**
- Test use case classes with mocked dependencies
- Verify business workflow and error handling
- Test command/result patterns
- Fast execution with mocked infrastructure

**Examples:**
- `test_generate_image_use_case.py` - Image generation use case

### E2E Tests

**Location:** `tests/e2e/`

**Purpose:** Test complete user workflows through the API.

**Characteristics:**
- Use real application server (must be running)
- Test full request/response cycles
- Verify end-to-end functionality
- May require external services (database, Redis)

**When to write:**
- Testing critical user workflows
- Testing API contracts
- Smoke tests for deployment verification

**Examples:**
- `test_health_and_generate.py` - Health check and generation flow
- `test_file_access_signed_url.py` - File access with signed URLs

## Coverage Targets

### Minimum Coverage Threshold

**Target: 60%** for the `app/` package.

The CI pipeline will fail if coverage falls below 60%. This ensures that:
- Critical business logic is tested
- New features include tests
- Refactoring is safer with test coverage

### Coverage Configuration

Coverage is configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = [
    "--cov=app",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-fail-under=60",
]

[tool.coverage.report]
fail_under = 60
```

### Excluded from Coverage

The following are excluded from coverage calculations:
- Test files (`tests/`)
- Migration files (`migrations/`)
- Cache directories (`__pycache__/`)
- Protocol definitions and abstract methods
- Type checking blocks (`if TYPE_CHECKING:`)

## Test Organization

### Directory Structure

```
tests/
├── unit/              # Unit tests (mocked dependencies)
├── integration/       # Integration tests (real dependencies)
├── application/       # Use case tests
├── infra/            # Infrastructure tests (repositories, queue, providers)
│   ├── repositories/ # Repository integration tests
│   ├── queue/        # Task queue tests
│   └── providers/    # Provider tests
├── workers/          # Worker tests
├── e2e/              # End-to-end tests
├── security/         # Security tests
└── perf/             # Performance tests
```

### Test Naming Conventions

- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`
- Fixtures: `*_fixture` or descriptive names

## Writing Tests

### Unit Test Guidelines

1. **Mock external dependencies:**
   ```python
   @patch('app.infra.queue.get_task_queue')
   async def test_use_case(mock_queue):
       # Test implementation
   ```

2. **Use fixtures for common setup:**
   ```python
   @pytest.fixture
   def mock_provider():
       provider = AsyncMock()
       provider.generate = AsyncMock(return_value=result)
       return provider
   ```

3. **Test one thing per test:**
   - One assertion or related assertions
   - Clear test name describing what is tested

4. **Follow AAA pattern:**
   - Arrange: Set up test data and mocks
   - Act: Execute the code under test
   - Assert: Verify the results

### Integration Test Guidelines

1. **Use test database:**
   - In-memory SQLite for repository tests
   - Test PostgreSQL for full integration tests

2. **Clean up after tests:**
   - Use fixtures with automatic cleanup
   - Rollback transactions in database tests

3. **Use real dependencies when possible:**
   - Real Redis client (or mocked but realistic)
   - Real database connections
   - Real HTTP clients for external APIs

### Test Fixtures

Common fixtures are defined in `tests/conftest.py`:

- `app_client` - FastAPI test client
- `async_session` - Async database session
- `async_db_engine` - Async database engine
- `uow` - UnitOfWork with automatic rollback
- `test_db_session` - Test database session for repositories

## Running Tests

### Local Development

**Run all tests:**
```bash
pytest tests/
```

**Run with coverage:**
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

**Run specific test level:**
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Application layer tests
pytest tests/application/
```

**Run specific test file:**
```bash
pytest tests/application/test_generate_image_use_case.py
```

**Run with markers:**
```bash
# Skip slow tests
pytest tests/ -m "not slow"

# Run only async tests
pytest tests/ -m asyncio
```

### Test Database Setup

**For repository tests:**
- Uses in-memory SQLite (automatic)
- No setup required

**For integration tests:**
- Requires PostgreSQL running
- Set `DATABASE_URL` environment variable:
  ```bash
  export DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/testdb
  ```

**For E2E tests:**
- Requires application server running
- Start server: `python run.py`
- Run tests in separate terminal

### CI/CD

Tests run automatically in GitHub Actions on:
- Push to `main` or `develop` branches
- Pull requests

**CI Configuration:**
- PostgreSQL service container
- Redis service container
- Coverage threshold: 60%
- Fails if coverage below threshold

See `.github/workflows/ci.yml` for details.

## Best Practices

### When to Write Unit Tests

- ✅ Pure functions and utilities
- ✅ Domain logic and business rules
- ✅ Service methods with mocked dependencies
- ✅ Validation and transformation logic
- ❌ Don't test framework code (FastAPI, SQLAlchemy internals)
- ❌ Don't test third-party library code

### When to Write Integration Tests

- ✅ Repository implementations
- ✅ API endpoints
- ✅ Service integration with external systems
- ✅ Database migrations
- ✅ Queue and worker interactions
- ❌ Don't duplicate unit test coverage
- ❌ Don't test external services (use mocks)

### When to Write E2E Tests

- ✅ Critical user workflows
- ✅ API contracts
- ✅ Smoke tests for deployment
- ❌ Don't test every endpoint (use integration tests)
- ❌ Don't test edge cases (use unit tests)

### Test Quality Guidelines

1. **Tests should be fast:**
   - Unit tests: < 1 second each
   - Integration tests: < 10 seconds each
   - E2E tests: < 30 seconds each

2. **Tests should be independent:**
   - No shared state between tests
   - Each test can run in isolation
   - Tests can run in any order

3. **Tests should be deterministic:**
   - Same input always produces same output
   - No random data (use fixed seeds)
   - No time-dependent logic (mock time)

4. **Tests should be readable:**
   - Clear test names
   - Minimal setup code
   - Obvious assertions

5. **Tests should be maintainable:**
   - Use fixtures for common setup
   - Extract helper functions
   - Keep tests DRY (but readable)

## Troubleshooting

### Tests Failing Locally

1. **Check environment variables:**
   ```bash
   export DATABASE_URL=postgresql+psycopg2://...
   export REDIS_URL=redis://localhost:6379/0
   export SECRET_KEY=test-secret-key
   ```

2. **Check dependencies:**
   ```bash
   pip install -e .
   pip install pytest pytest-cov pytest-asyncio
   ```

3. **Check database:**
   - Ensure PostgreSQL is running
   - Database exists and is accessible

4. **Check Redis:**
   - Ensure Redis is running
   - Connection string is correct

### Coverage Below Threshold

1. **Check coverage report:**
   ```bash
   pytest tests/ --cov=app --cov-report=html
   # Open htmlcov/index.html
   ```

2. **Identify uncovered code:**
   - Review HTML report
   - Add tests for uncovered paths
   - Exclude non-testable code (protocols, abstract methods)

3. **Temporary exclusion:**
   ```python
   # pragma: no cover
   def untestable_function():
       ...
   ```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

