<p align="center">
  <img src="./docs/_shared/assets/readme-hero.svg" alt="AmaImagery hero" width="100%" />
</p>

<div align="center">

# AmaImagery

### Image generation infrastructure for teams that want a real backend, not a toy demo.

[![Version](https://img.shields.io/badge/version-0.1.0-black.svg)](./pyproject.toml)
[![Python](https://img.shields.io/badge/python-3.11+-306998.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/frontend-React-61DAFB.svg)](https://react.dev/)
[![Ruff](https://img.shields.io/badge/lint-ruff-FFDB4D.svg?logo=ruff)](https://github.com/astral-sh/ruff)
[![MyPy](https://img.shields.io/badge/types-mypy-0E6EB8.svg)](https://mypy.readthedocs.io/)

[Read the docs](./docs/README.md) • [Explore backend notes](./docs/en/backend/README.md) • [Commercial licensing](./COMMERCIAL_LICENSE.md)

</div>

AmaImagery is a self-hosted image generation platform built around a FastAPI backend, a React frontend, and an asynchronous worker pipeline. It exposes one operational contract across multiple generation providers, with `ComfyUI` as the practical primary runtime and `Diffusers` still available where local model management makes sense.

---

## The Frame

<table>
  <tr>
    <td width="33%">
      <strong>One generation contract</strong><br/>
      Async job submission, status, history, artifacts, and terminal-state consistency.
    </td>
    <td width="33%">
      <strong>One operational story</strong><br/>
      Health, readiness, queue state, provider state, and admin visibility line up.
    </td>
    <td width="33%">
      <strong>One honest runtime</strong><br/>
      Not pretending to be lightweight magic. Built for inspectability and control.
    </td>
  </tr>
</table>

> AmaImagery is designed to be legible in motion. If a provider fails, the system should say so clearly. If a generation completes, every public surface should tell the same story.

---

## What Lives Here

| Surface | What it is for |
| --- | --- |
| Async generation API | Accepts jobs, persists state, exposes status and history |
| Provider runtime | Boots providers, classifies failures, reports readiness clearly |
| Worker lifecycle | Executes jobs, updates terminal state, stores artifacts |
| Admin surface | Gives superusers a live view of users and generations |
| CI quality gates | Enforces linting, typing, and backend verification |

---

## Runtime Mood

AmaImagery is credible, usable, and actively maintained. It is also explicit about its current shape.

- `ComfyUI` is the strongest end-to-end path today
- the Docker image is still CUDA-oriented and heavy
- `Diffusers` support exists, but large local model handling remains a real operational cost
- the repository is closer to a serious self-hosted platform than to a shrink-wrapped appliance

That tradeoff is deliberate. The project optimizes for correctness, visibility, and control before pretending to be effortless.

---

## System Rhythm

<p align="center">
  <img src="./docs/_shared/assets/architecture-rhythm.svg" alt="AmaImagery runtime rhythm" width="100%" />
</p>

The runtime path is intentionally coherent:

1. The API accepts a generation request.
2. PostgreSQL becomes the source of truth for lifecycle state.
3. The worker submits to a provider and watches execution.
4. The provider result becomes either an artifact or an explicit failure.
5. Status, history, admin, and download endpoints reflect the same final state.

---

## Choose Your Lane

<details open>
  <summary><strong>🚀 I want to run the stack</strong></summary>
  <br/>

  <strong>Docker</strong>

  ```bash
  git clone https://github.com/AmaLS367/AmaImagery
  cd AmaImagery
  docker compose --env-file docker/.env.docker -f docker/compose.local.yml up -d --build
  ```

  Provider verification presets:

  - `docker/.env.verify.comfyui.example`
  - `docker/.env.verify.diffusers.example`
</details>

<details>
  <summary><strong>🛠️ I want to develop locally</strong></summary>
  <br/>

  ```bash
  python -m venv .venv
  .venv\Scripts\activate
  pip install -e ".[dev]"
  alembic upgrade head
  python run.py
  python -m app.entrypoints.generation_worker
  ```
</details>

<details>
  <summary><strong>✅ I want confidence fast</strong></summary>
  <br/>

  ```bash
  python -m ruff check app tests
  python -m mypy app
  python -m pytest tests -q
  ```

  Core operational endpoints:

  - `GET /api/v1/health`
  - `GET /api/v1/healthz`
  - `GET /admin/`
</details>

---

## Why It Feels Different

- provider boot state is visible, not hidden in logs
- readiness distinguishes "alive" from "able to generate"
- terminal generation states stay coherent across status, history, admin, and download flows
- authentication and superuser-only admin access are first-class surfaces, not bolted-on details
- signed artifact delivery is part of the product contract, not an afterthought

---

## Continue Reading

<table>
  <tr>
    <td width="50%">
      <strong>📚 Core docs</strong><br/><br/>
      <a href="./docs/README.md">Documentation Index</a><br/>
      <a href="./docs/en/README.md">English Documentation</a><br/>
      <a href="./docs/en/backend/admin-and-readiness.md">Backend Admin and Readiness</a><br/>
      <a href="./docs/en/deployment/provider-rollout.md">Provider Rollout Notes</a>
    </td>
    <td width="50%">
      <strong>🧭 Project policies</strong><br/><br/>
      <a href="./CONTRIBUTING.md">Contributing</a><br/>
      <a href="./SECURITY.md">Security</a><br/>
      <a href="./SUPPORT.md">Support</a><br/>
      <a href="./COMMERCIAL_LICENSE.md">Commercial Licensing</a>
    </td>
  </tr>
</table>

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
| 🐞 Bugs and defects | GitHub Issues |
| 💬 Product or usage discussion | GitHub Discussions |
| 🔒 Security disclosure | `amalsdev367@gmail.com` |
| 💼 Commercial licensing | `amalsdev367@gmail.com` |

AmaImagery is meant to feel sharp, controlled, and inspectable. The docs should set that tone before the code ever runs.
