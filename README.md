# AmaImagery

> Image generation infrastructure for teams that want a real backend, not a toy demo.

[![Version](https://img.shields.io/badge/version-0.1.0-black.svg)](./pyproject.toml)
[![Python](https://img.shields.io/badge/python-3.11+-306998.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/frontend-React-61DAFB.svg)](https://react.dev/)
[![Ruff](https://img.shields.io/badge/lint-ruff-FFDB4D.svg?logo=ruff)](https://github.com/astral-sh/ruff)
[![MyPy](https://img.shields.io/badge/types-mypy-0E6EB8.svg)](https://mypy.readthedocs.io/)

AmaImagery is a self-hosted image generation platform built around a FastAPI backend, a React frontend, and an asynchronous worker pipeline. It exposes one operational contract across multiple generation providers, with `ComfyUI` as the practical primary runtime and `Diffusers` still available where local model management makes sense.

---

## At A Glance

| Surface | What it does |
| --- | --- |
| Async generation API | Accepts jobs, persists state, exposes status and history |
| Provider runtime | Boots providers, tracks readiness, reports failures clearly |
| Worker lifecycle | Executes jobs, persists terminal states, stores artifacts |
| Admin surface | Gives superusers a real operational view of users and generations |
| Quality gates | Enforced through CI, `ruff`, `mypy`, and backend tests |

> The project is designed to be operationally legible. Health, readiness, queue behavior, provider state, and artifact visibility are all part of the product surface, not hidden implementation detail.

## What Makes It Interesting

- One backend contract across provider implementations
- Queue-backed generation flow with durable status and history
- Provider-aware health and readiness instead of empty "ok" endpoints
- Superuser admin pages for runtime inspection
- Signed artifact delivery for completed generations
- A codebase already wired for linting, typing, and CI enforcement

## Reality Check

AmaImagery is credible, usable, and actively maintained. It is also honest about its current shape.

- `ComfyUI` is the strongest end-to-end path today
- the Docker runtime is still CUDA-oriented and heavy
- `Diffusers` support exists, but large local model handling remains a real operational cost
- the repository is closer to a serious self-hosted platform than to a shrink-wrapped appliance

That is intentional. The project optimizes for correctness, visibility, and control before pretending to be lightweight magic.

---

## The Shape

The repository is organized around a few clear surfaces:

- `app/` for the backend, domain logic, providers, repositories, and worker code
- `frontend/` for the React client
- `tests/` for unit, integration, worker, security, and performance coverage
- `migrations/` for Alembic
- `docker/` for local compose flows and provider verification environments
- `docs/` for English and Russian documentation

The runtime path is straightforward:

1. The API accepts a generation request.
2. PostgreSQL becomes the source of truth for lifecycle state.
3. The worker submits to a provider and observes execution.
4. The provider result becomes an artifact or an explicit failure.
5. Status, history, admin, and download endpoints reflect the same final state.

---

## Run The Stack

### Docker

```bash
git clone https://github.com/AmaLS367/AmaImagery
cd AmaImagery
docker compose --env-file docker/.env.docker -f docker/compose.local.yml up -d --build
```

Useful provider verification presets:

- `docker/.env.verify.comfyui.example`
- `docker/.env.verify.diffusers.example`

### Local Development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
python run.py
python -m app.entrypoints.generation_worker
```

### Fast Confidence Checks

```bash
python -m ruff check app tests
python -m mypy app
python -m pytest tests -q
```

Core operational endpoints:

- `GET /api/v1/health`
- `GET /api/v1/healthz`
- `GET /admin/`

---

## The Trust Surface

AmaImagery is built to be inspectable in motion.

- provider boot state is visible
- readiness distinguishes "alive" from "able to generate"
- terminal generation states are coherent across status, history, admin, and artifact delivery
- authentication and superuser-only admin access are first-class, not afterthoughts

If a provider fails, the system should say so clearly. If a generation completes, the artifact contract should be consistent everywhere. That philosophy runs through the repository.

---

## Read Further

Primary docs:

- [Documentation Index](./docs/README.md)
- [English Documentation](./docs/en/README.md)
- [Backend Admin and Readiness](./docs/en/backend/admin-and-readiness.md)
- [Provider Rollout Notes](./docs/en/deployment/provider-rollout.md)

Project policies:

- [Contributing](./CONTRIBUTING.md)
- [Security](./SECURITY.md)
- [Support](./SUPPORT.md)
- [Code of Conduct](./CODE_OF_CONDUCT.md)
- [Commercial Licensing](./COMMERCIAL_LICENSE.md)

---

## Open Source And Commercial

AmaImagery application code is dual-licensed:

- open-source use under `AGPL-3.0-only`
- commercial licensing by direct agreement via `amalsdev367@gmail.com`

Third-party models, datasets, and assets may carry separate obligations. Review:

- [LICENSE](./LICENSE)
- [NOTICE.txt](./NOTICE.txt)
- [ATTRIBUTIONS.md](./ATTRIBUTIONS.md)
- [Legal Docs](./docs/en/legal/README.md)

---

## Contact Paths

| Need | Path |
| --- | --- |
| Bugs and defects | GitHub Issues |
| Product or usage discussion | GitHub Discussions |
| Security disclosure | `amalsdev367@gmail.com` |
| Commercial licensing | `amalsdev367@gmail.com` |

AmaImagery is meant to feel sharp, controlled, and inspectable. The docs should set that tone before the code ever runs.
