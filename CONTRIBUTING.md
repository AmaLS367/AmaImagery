# Contributing to AmaImagery

> Bring changes that make the system clearer, safer, or more durable.

AmaImagery is maintained like infrastructure, not like a throwaway experiment. Good contributions improve the operating shape of the project as much as the feature set.

---

## Before You Open A PR

- Read the top-level [README](./README.md)
- Check whether the problem already has an issue or active PR
- If the topic is security-sensitive, stop and use [SECURITY.md](./SECURITY.md) instead of a public issue

## Get To A Working Environment

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
```

Frontend work:

```bash
cd frontend
npm ci
```

## The Standard

Contributions should be:

- focused rather than sprawling
- production-minded rather than demo-minded
- explicit about behavior changes
- backed by tests when behavior changes
- accompanied by doc updates when setup, runtime, or policy changes

## What Good Looks Like

| Area | Expectation |
| --- | --- |
| Scope | One coherent problem per PR |
| Code quality | Clear responsibilities, minimal incidental churn |
| Contracts | Public behavior stays stable unless change is intentional and documented |
| Tests | New behavior gets verification, not just implementation churn |
| Docs | Setup, runtime, licensing, and policy changes are updated in the same PR |

## Quality Gates

Run the same checks the repository expects:

```bash
python -m ruff check app tests
python -m mypy app
python -m pytest tests -q
```

For frontend changes:

```bash
cd frontend
npm run typecheck
npm run build
```

## Contribution Style

- Prefer small, reviewable commits
- Avoid mixing unrelated refactors into a bug fix
- Keep comments and public-facing docs in English
- Do not hide important tradeoffs in implementation details

## Special Care Areas

Changes touching these surfaces deserve extra care:

- provider lifecycle and failure handling
- worker terminal-state updates
- readiness and health contracts
- auth, cookies, tokens, and admin access control
- artifact exposure and download behavior

## License

By contributing, you agree that your contribution may be distributed under the repository's dual-license model:

- `AGPL-3.0-only` for open-source use
- a separate commercial license by written agreement with the maintainer

The goal is not just to merge code. The goal is to leave the system in better shape than you found it.
