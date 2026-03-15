# Development Documentation

## Overview

Practical guide for setting up, developing, and contributing to **AmaImagery**.

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git
- Docker (optional but recommended for full-stack local runs)
- NVIDIA GPU only if you want local GPU-backed Diffusers work

### Quick Setup

1. **Clone the repository**
```bash
git clone https://github.com/AmaLS367/AmaImagery
cd AmaImagery
```

2. **Set up backend**
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
# Add ML dependencies only when you need local Diffusers runtime
pip install -e ".[ml]"
```

3. **Set up frontend**
```bash
cd frontend
npm ci
cd ..
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Run migrations**
```bash
alembic upgrade head
```

6. **Start development processes**
```bash
# Terminal 1 - Backend API
python run.py

# Terminal 2 - Generation worker
python -m app.entrypoints.generation_worker

# Terminal 3 - Frontend
cd frontend
npm run dev
```

## Documentation Sections

| Topic | Status |
|------|--------|
| Getting Started deep-dive | 🚧 Coming soon |
| Platform-specific setup pages | 🚧 Coming soon |
| Project structure deep-dive | 🚧 Coming soon |
| Coding standards page | 🚧 Coming soon |
| Git workflow page | 🚧 Coming soon |
| Debugging page | 🚧 Coming soon |
| Code review page | 🚧 Coming soon |
| [Contributing](../../../CONTRIBUTING.md) | ✅ Available |


## Development Tools

### Code Quality
- **Linting:** ruff
- **Formatting:** repo-specific workflow, optional black for Python formatting
- **Type Checking:** mypy, TypeScript
- **Testing:** pytest, frontend typecheck/build, Playwright-based frontend tests in the repo test tree

### IDE Setup
- VSCode
- PyCharm
- Any editor that handles Python + TypeScript cleanly

## Project Structure

```
amaimagery/
├── app/              # Backend application
├── frontend/         # React frontend
├── tests/            # Backend and integration tests
├── migrations/       # Alembic migrations
├── models/           # Local model assets and metadata
├── docker/           # Docker configs and env templates
└── scripts/          # Utility scripts
```

## Common Tasks

### Running Tests
```bash
pytest -q
python -m ruff check app tests
python -m mypy app

cd frontend
npm run typecheck
npm run build
```

### Creating Migrations
```bash
alembic revision -m "description"
alembic upgrade head
```

### Running Docker Locally
```bash
docker compose --env-file docker/.env.docker -f docker/compose.local.yml up -d --build
```

## Getting Help

- Check [Troubleshooting](../troubleshooting/README.md)
- Review existing issues and discussions
- Use [Reference](../reference/README.md) for endpoints, commands, and env variables
