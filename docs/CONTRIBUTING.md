# 🌘 Contributing to AmaImagery

> Bring changes that leave the system clearer, safer, and more durable than you found it.

AmaImagery is maintained like infrastructure. The bar is not only whether the code works, but whether the runtime, contracts, and maintenance story become easier to trust.

---

## 🧭 Before You Start

<table>
  <tr>
    <td width="33%">
      <strong>📖 Read the shape</strong><br/>
      Start with <a href="./README.md">README</a> so your change fits the actual product surface.
    </td>
    <td width="33%">
      <strong>🧩 Check overlap</strong><br/>
      Look for active issues and adjacent pull requests before starting overlapping work.
    </td>
    <td width="33%">
      <strong>🔒 Route security privately</strong><br/>
      If the topic is security-sensitive, use <a href="./SECURITY.md">SECURITY.md</a> rather than a public issue.
    </td>
  </tr>
</table>

---

## ✅ Get To Green

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
# install the ML extra only for local diffusers/provider work
pip install -e ".[ml]"
alembic upgrade head
```

Frontend work:

```bash
cd frontend
npm ci
```

---

## ✦ The Standard

| Area | Expectation |
| --- | --- |
| Scope | One coherent problem per PR |
| Code quality | Minimal incidental churn, clear responsibilities |
| Contracts | Public behavior stays stable unless a change is intentional and documented |
| Tests | Behavior changes get verification, not just implementation churn |
| Docs | Setup, runtime, and policy changes are updated in the same PR |

## 🧪 Quality Gates

```bash
python -m ruff check app tests
python -m mypy app
python -m pytest tests -q
```

Frontend:

```bash
cd frontend
npm run typecheck
npm run build
```

---

## 🧱 Special Care Areas

<details open>
  <summary><strong>⚙️ Provider and worker changes</strong></summary>
  <br/>

  Be explicit about:

  - provider lifecycle and failure semantics
  - worker terminal-state updates
  - artifact persistence and download behavior
  - readiness and health contracts
</details>

<details>
  <summary><strong>🛡️ Auth and admin changes</strong></summary>
  <br/>

  Protect:

  - auth and session boundaries
  - cookies and token handling
  - superuser-only access rules
  - user-visible contract consistency
</details>

<details>
  <summary><strong>✂️ Refactors</strong></summary>
  <br/>

  Do not hide broad rewrites inside a bug fix. If a refactor is the point, make it the point.
</details>

---

## ✍️ Contribution Style

- Prefer small, reviewable commits
- Avoid mixing unrelated refactors into a fix
- Keep comments and public docs in English
- Do not bury important tradeoffs in code alone

## ⚖️ License

By contributing, you agree that contributions may be distributed under the repository's dual-license model:

- `AGPL-3.0-only` for open-source use
- a separate commercial license by written agreement with the maintainer

The fastest way to contribute is to be precise. The best way is to improve the system's operating shape while you are there.
