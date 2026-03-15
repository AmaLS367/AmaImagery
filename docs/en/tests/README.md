# Testing Documentation

## Overview

Current testing and validation strategy for backend, frontend, and runtime behavior in **AmaImagery**.

## Test Types

### ✅ Backend Tests
- pytest-based unit and integration coverage
- API and repository tests
- service and use-case coverage

### 🌐 Frontend Validation
- TypeScript typecheck
- production build verification
- Playwright-based frontend tests live in the repository test tree

### 🔒 Security / Limits Coverage
- auth coverage
- authorization checks
- input validation
- rate limiting and signed file tests

### ⚡ Performance / Runtime Checks
- smoke tests
- generation latency/perf tests where the environment supports them

## Documentation Sections

| Topic | Status |
|------|--------|
| Unit test deep-dive | 🚧 Coming soon |
| Integration deep-dive | 🚧 Coming soon |
| E2E deep-dive | 🚧 Coming soon |
| Security test deep-dive | 🚧 Coming soon |
| Performance deep-dive | 🚧 Coming soon |
| Running tests page | 🚧 Coming soon |
| CI/CD deep-dive | 🚧 Coming soon |
| [Testing Strategy](./testing-strategy.md) | ✅ Available |

## Quick Start

### Backend
```bash
pytest -q
python -m ruff check app tests
python -m mypy app
```

### Frontend
```bash
cd frontend
npm ci
npm run typecheck
npm run build
```

## Test Coverage

Current enforced Python coverage threshold in the repo config:
- **60% minimum** for the `app/` package

Coverage outputs:
- terminal
- HTML
- XML

See [Testing Strategy](./testing-strategy.md) for more context.
