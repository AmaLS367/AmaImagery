# AmaImagery Documentation

📚 **Multi-language Documentation** | Многоязычная документация

Welcome to the **AmaImagery** documentation hub. This project is a self-hosted image generation platform with a FastAPI backend, a React frontend, an async worker pipeline, and Docker-based deployment flows.

---

## 🌍 Available Languages / Доступные языки

| Language | Link | Status |
|----------|------|--------|
| 🇬🇧 English | [English Documentation](./en/README.md) | ✅ Active |
| 🇷🇺 Русский | [Русская документация](./ru/README.md) | ✅ Active |
| 🇨🇳 中文 | Coming soon | 🚧 Planned |
| 🇪🇸 Español | Coming soon | 🚧 Planned |
| 🇫🇷 Français | Coming soon | 🚧 Planned |

---

## 📖 Documentation Structure

Each language keeps the same visual structure, but the docs are aligned to the current repository shape:

### 🔧 **Backend**
FastAPI routes, auth, generation flow, provider integration, admin pages, readiness, repositories, and worker lifecycle.

### 🎨 **Frontend**
React/Vite application, routing, state handling, API integration, and i18n.

### 🐳 **Docker**
Compose files, runtime targets, env templates, and local/production container flows.

### 🧪 **Tests**
Backend test strategy, frontend build/typecheck flow, and runtime verification commands.

### 🤖 **Models**
Current local model assets, provider/runtime expectations, and licensing context.

### 🚀 **Deployment**
Supported deployment shapes, production checklist, provider rollout, and operational notes.

### 📜 **Scripts**
Bootstrap, build, migration, run, smoke, and Python helper scripts that actually exist in the repo.

### 💻 **Development**
How to set up the project today, run API and worker locally, and work against the real runtime.

### 🔒 **Security**
Auth surface, rate limiting, file delivery, admin access, and current security posture.

### ⚡ **Features**
What is available now, what is provider-dependent, and what is still planned rather than publicly shipped.

### 🔍 **Troubleshooting**
Current operational issues, not old or speculative setup paths.

### ⚖️ **Legal**
Project licensing, model licensing, attribution, and usage obligations.

### 📚 **Reference**
Current endpoints, env variables, commands, and ports.

### 🎓 **Tutorials**
Planned guided walk-throughs and learning material. Some tutorial pages are still roadmap items.

---

## 🚀 Quick Start

1. Choose your language above.
2. Start with **Development** for local setup or **Docker** for the fastest end-to-end path.
3. Use **Reference** for real endpoints, commands, and env variables.
4. Treat pages marked `Coming soon` as roadmap/planning material, not shipped functionality.

---

## 🤝 Contributing to Documentation

We welcome contributions to improve and translate documentation.

1. Documentation keeps the same visual structure across languages.
2. Use templates from `_templates/` when adding new pages.
3. Place language-independent assets in `_shared/`.
4. Update `.translation-status.json` when adding new translations.
5. When docs and code disagree, the repo implementation wins.

See [Contributing Guide](../CONTRIBUTING.md) for the repository workflow.

---

## 📝 License

This documentation is part of **AmaImagery**.
See [Legal](./en/legal/README.md) for project and model licensing information.

---

**Last Updated:** March 15, 2026 | **Version:** 0.1.0
