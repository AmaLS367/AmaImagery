# Development Documentation

## Overview

Complete guide for developers to set up, develop, and contribute to the AI Image Generator project.

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git
- Docker (optional but recommended)
- NVIDIA GPU with CUDA 11.8+ (for local development)

### Quick Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd genai
```

2. **Set up backend**
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. **Set up frontend**
```bash
cd frontend
npm install
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Run migrations**
```bash
python -m alembic upgrade head
```

6. **Start development servers**
```bash
# Terminal 1 - Backend
python run_dev.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## Documentation Sections

- [Getting Started](./getting-started.md) - Detailed setup guide
- [Setup](./setup/) - Platform-specific setup
  - [Windows](./setup/windows.md)
  - [Linux](./setup/linux.md)
  - [macOS](./setup/macos.md)
- [Project Structure](./project-structure.md) - Codebase overview
- [Coding Standards](./coding-standards.md) - Code style and conventions
- [Git Workflow](./git-workflow.md) - Branching and commits
- [Debugging](./debugging.md) - Debugging techniques
- [Contributing](./contributing.md) - How to contribute
- [Code Review](./code-review.md) - Code review process

## Development Tools

### Code Quality
- **Linting:** ruff, eslint
- **Formatting:** black, prettier
- **Type Checking:** mypy, TypeScript
- **Testing:** pytest, vitest

### IDE Setup
- VSCode (recommended)
- PyCharm
- Recommended extensions/plugins

## Project Structure

```
genai/
├── app/              # Backend application
│   ├── api/         # API routes
│   ├── core/        # Core functionality
│   ├── services/    # Business logic
│   └── ...
├── frontend/         # React frontend
│   ├── src/
│   └── ...
├── tests/           # Backend tests
├── migrations/      # Database migrations
├── models/          # ML models
├── docker/          # Docker configs
└── scripts/         # Utility scripts
```

See [Project Structure](./project-structure.md) for details.

## Common Tasks

### Running Tests
```bash
pytest tests/
cd frontend_tests && npm test
```

### Creating Migrations
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Building for Production
```bash
# Backend
docker build -t genai-backend .

# Frontend
cd frontend && npm run build
```

## Getting Help

- Check [Troubleshooting](../troubleshooting/README.md)
- Review existing issues
- Ask in discussions

