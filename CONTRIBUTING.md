# Contributing to AmaImagery

Thank you for contributing. This repository is maintained as a production-minded codebase, so changes should improve clarity, correctness, and operational confidence rather than just make tests pass.

## Before You Start

- Read the top-level [README](./README.md) for the current project shape
- Check open issues and existing pull requests before starting overlapping work
- For security issues, do not open a public issue. Use [SECURITY.md](./SECURITY.md)

## Development Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
```

If you are working on the frontend:

```bash
cd frontend
npm ci
```

## Branching and Pull Requests

- Keep branches focused on one problem or one coherent batch of changes
- Prefer small, reviewable commits
- Update tests and docs when behavior changes
- Do not mix unrelated refactors into a bug fix or feature PR

## Quality Gates

Run the same core checks expected by CI:

```bash
python -m ruff check app tests
python -m mypy app
python -m pytest tests -q
```

Frontend changes should also pass:

```bash
cd frontend
npm run typecheck
npm run build
```

## Coding Expectations

- Keep module responsibilities clear
- Prefer incremental changes over broad rewrites
- Preserve public API contracts unless a change is required and documented
- Use English for code comments, commit messages, and public project docs
- Add tests for real behavior changes, not just implementation details

## Provider and Runtime Changes

Changes touching generation providers, worker lifecycle, health, or readiness should include:

- a clear terminal-state story
- updated smoke or verification steps when relevant
- documentation changes if operational behavior changes

## Documentation

If you change setup, runtime behavior, licensing, security contact, or admin behavior, update the relevant docs in the same change.

## License

By contributing, you agree that your contributions may be distributed under the repository's dual-license model:

- `AGPL-3.0-only` for open-source use
- commercial licensing by separate agreement with the maintainer
