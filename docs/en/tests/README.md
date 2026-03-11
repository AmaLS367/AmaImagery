# Testing Documentation

## Overview

Comprehensive testing strategy including unit tests, integration tests, E2E tests, security tests, and performance tests for both backend and frontend.

## Test Types

### ✅ Unit Tests
- Backend: pytest
- Frontend: Vitest
- Component isolation
- Mock dependencies

### 🔗 Integration Tests
- API integration
- Database integration
- Service integration
- External service mocks

### 🌐 E2E Tests
- Full user workflows
- Browser automation
- API contract testing
- Smoke tests

### 🔒 Security Tests
- Authentication tests
- Authorization tests
- Input validation
- SQL injection prevention

### ⚡ Performance Tests
- API latency tests
- Load testing
- Memory profiling
- GPU utilization

## Documentation Sections

- [Unit Tests](./unit-tests/) - Unit testing guides
- [Integration Tests](./integration-tests/) - Integration testing
- [E2E Tests](./e2e-tests/) - End-to-end testing
- [Security Tests](./security-tests/) - Security testing
- [Performance Tests](./performance-tests/) - Performance testing
- [Writing Tests](./writing-tests.md) - How to write tests
- [Running Tests](./running-tests.md) - How to run tests
- [CI/CD](./ci-cd.md) - Continuous integration

## Quick Start

### Backend Tests
```bash
pytest tests/
```

### Frontend Tests
```bash
cd frontend_tests
npm test
```

See [Running Tests](./running-tests.md) for details.

## Test Coverage

Current test coverage:
- Backend: Unit tests, integration, E2E, security
- Frontend: Unit tests, E2E tests
- Target: **80% minimum coverage** for `app/` package

### Coverage Configuration

Coverage is enforced in CI and local development:
- Minimum threshold: **80%**
- CI fails if coverage drops below threshold
- Coverage reports: terminal, HTML, XML

See [Testing Strategy](./testing-strategy.md) for detailed coverage guidelines.

## Documentation

- [Testing Strategy](./testing-strategy.md) - Comprehensive testing strategy, coverage targets, and best practices

