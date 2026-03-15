# Документация тестирования

## Обзор

Текущая стратегия тестирования и валидации backend, frontend и runtime-поведения в **AmaImagery**.

## Типы проверок

### ✅ Backend tests
- pytest-based unit и integration coverage
- API и repository tests
- coverage сервисов и use cases

### 🌐 Frontend validation
- TypeScript typecheck
- production build verification
- Playwright-based frontend tests живут в дереве тестов репозитория

### 🔒 Security / Limits coverage
- покрытие auth
- проверки authorization
- валидация ввода
- тесты rate limiting и signed files

### ⚡ Performance / Runtime checks
- smoke tests
- generation latency/perf tests там, где окружение это позволяет

## Разделы документации

| Тема | Статус |
|------|--------|
| Unit test deep-dive | 🚧 Coming soon |
| Integration deep-dive | 🚧 Coming soon |
| E2E deep-dive | 🚧 Coming soon |
| Security test deep-dive | 🚧 Coming soon |
| Performance deep-dive | 🚧 Coming soon |
| Running tests page | 🚧 Coming soon |
| CI/CD deep-dive | 🚧 Coming soon |
| [Testing Strategy](./testing-strategy.md) | ✅ Доступно |

## Быстрый старт

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

## Покрытие тестами

Текущий enforced Python coverage threshold в конфиге репозитория:
- **60% minimum** для пакета `app/`

Форматы coverage outputs:
- terminal
- HTML
- XML

Больше контекста в [Testing Strategy](./testing-strategy.md).
