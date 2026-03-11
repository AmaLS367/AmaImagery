# AI Image Generator

> **Powerful self-hosted image generation platform based on Stable Diffusion**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](https://www.docker.com)
[![Ruff](https://img.shields.io/badge/ruff-enabled-FFDB4D.svg?logo=ruff)](https://github.com/astral-sh/ruff)
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![MyPy](https://img.shields.io/badge/type%20checker-mypy-blue.svg)](https://mypy.readthedocs.io/)

AI Image Generator is a production-ready platform for generating, editing, and upscaling images using Stable Diffusion models. Features enterprise-grade security, content moderation, and comprehensive monitoring.

The generation runtime supports both `diffusers` and `comfyui` through the same asynchronous API and worker lifecycle. The rollout target is `ComfyUI` as the default provider with `Diffusers` kept as fallback.

---

## 📚 Documentation

**Multi-language comprehensive documentation is available:**

| Language | Documentation | Status |
|----------|--------------|--------|
| 🇬🇧 English | [English Documentation](./docs/en/README.md) | ✅ Complete |
| 🇷🇺 Русский | [Русская документация](./docs/ru/README.md) | ✅ Complete |
| 🇨🇳 中文 | Coming soon | 🚧 Planned |
| 🇪🇸 Español | Coming soon | 🚧 Planned |
| 🇫🇷 Français | Coming soon | 🚧 Planned |

📖 **[Browse all documentation →](./docs/README.md)**

---

## ✨ Features

- 🎨 **High-Quality Generation** - Stable Diffusion 1.5, AmaFusion V1, DreamShaper v6
- ✏️ **Image Editing** - Inpainting, outpainting, image-to-image with IP-Adapter
- 🔍 **AI Upscaling** - Enhance resolution up to 4x
- 🛡️ **Content Safety** - Built-in NSFW detection and prompt hygiene system
- 🔒 **Enterprise Security** - JWT authentication, rate limiting, input validation
- 📊 **Monitoring** - Prometheus metrics, structured logging, GPU monitoring
- 🌐 **Modern UI** - React frontend with multi-language support
- 🐳 **Docker Ready** - Production-ready containerization
- 🚀 **RESTful API** - Comprehensive API with OpenAPI documentation

---

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/AmaLS367/AmaImagery
cd amaimagery

# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Start with Docker Compose
docker compose -f docker/compose.local.yml up
```

Provider verification profiles are available in `docker/.env.verify.diffusers.example` and `docker/.env.verify.comfyui.example`.

Access the application:
- **Frontend:** http://localhost:80
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Manual Installation

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install project with dependencies
pip install -e .

# Run migrations
alembic upgrade head

# Start the API server
python run.py

# Start the generation worker in a separate process
python -m app.entrypoints.generation_worker
```

**Note:** The project uses `pyproject.toml` for modern dependency management. For legacy systems, `requirements.txt` is also available.

📖 **For detailed setup instructions, see:**
- [English Setup Guide](./docs/en/development/getting-started.md)
- [Русское руководство по установке](./docs/ru/development/getting-started.md)

---

## 🏗️ Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Frontend      │◄────►│    Backend       │◄────►│   PostgreSQL    │
│   React + TS    │      │   FastAPI        │      │   Database      │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                 │
                                 ├─────► Redis (Cache)
                                 │
                                 ▼
                         ┌──────────────────┐
                         │   ML Pipeline    │
                         │ Stable Diffusion │
                         │   + GPU (CUDA)   │
                         └──────────────────┘
```

---

## 📦 Technology Stack

**Backend:**
- FastAPI 0.116.1, Python 3.11+
- PyTorch 2.2.2 with CUDA 12.1
- Diffusers 0.29.2
- PostgreSQL + SQLAlchemy 2.0
- Redis 5.0
- Alembic (migrations)

**Frontend:**
- React 18 + TypeScript
- Vite build tool
- Tailwind CSS
- i18next (multi-language)

**ML Models:**
- Stable Diffusion v1.5
- AmaFusion V1 (custom)
- DreamShaper v6
- IP-Adapter
- VAE (sd-vae-ft-mse)

**Infrastructure:**
- Docker & Docker Compose
- Nginx (reverse proxy)
- Prometheus metrics

---

## 📖 Documentation Sections

- [📘 Backend](./docs/en/backend/README.md) - API, services, inference pipeline
- [🎨 Frontend](./docs/en/frontend/README.md) - React components, UI, styling
- [🐳 Docker](./docs/en/docker/README.md) - Containerization and deployment
- [🧪 Tests](./docs/en/tests/README.md) - Testing strategy and guides
- [🤖 Models](./docs/en/models/README.md) - ML models documentation
- [🚀 Deployment](./docs/en/deployment/README.md) - Production deployment
- [🔒 Security](./docs/en/security/README.md) - Security best practices
- [⚡ Features](./docs/en/features/README.md) - Feature documentation
- [🔍 Troubleshooting](./docs/en/troubleshooting/README.md) - Common issues

---

## 🔑 System Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 16GB
- GPU: NVIDIA with 6GB+ VRAM
- Storage: 50GB SSD
- OS: Linux (Ubuntu 20.04+) or Windows 10+

**Recommended:**
- CPU: 8+ cores
- RAM: 32GB+
- GPU: NVIDIA RTX 3060+ (8GB+ VRAM)
- Storage: 100GB+ NVMe SSD

---

## ⚖️ Legal and Licensing

This repository contains model weights and code with different licenses:

### Application Code
- See [LICENSE](./LICENSE) file for application code license

### ML Models

**Stable Diffusion v1.5, AmaFusion V1, DreamShaper v6:**
- **License:** CreativeML Open RAIL-M
- **File:** `models/AmaFusion_V1/LICENSES/OpenRAIL-M.txt`

**VAE (sd-vae-ft-mse):**
- **License:** MIT
- **File:** `models/AmaFusion_V1/LICENSES/VAE_LICENSE.txt`

### Important Notice

When distributing weights or providing model access as a service:
1. ✅ Include CreativeML Open RAIL-M license notice
2. ✅ Link to full license text
3. ✅ Provide model attributions
4. ✅ Review and comply with use-based restrictions

**See complete legal documentation:**
- [Legal Information (English)](./docs/en/legal/README.md)
- [Юридическая информация (Русский)](./docs/ru/legal/README.md)
- [ATTRIBUTIONS.md](./ATTRIBUTIONS.md) - Consolidated provenance
- [NOTICE.txt](./NOTICE.txt) - Third-party licenses

### Files Map

```
models/AmaFusion_V1/LICENSES/
├── OpenRAIL-M.txt                      # Full OpenRAIL-M text
├── Upstream_DreamShaper_LICENSE.txt    # DreamShaper license
└── VAE_LICENSE.txt                     # MIT license for VAE

models/AmaFusion_V1/
├── DATA_SOURCES.md                     # Training datasets
└── MODEL_CARD.md                       # Model card with legal info
```

---

## 🤝 Contributing

Contributions are welcome! See our contributing guides:
- [English Contributing Guide](./docs/en/development/contributing.md)
- [Руководство для контрибьюторов](./docs/ru/development/contributing.md)

---

## 📞 Support & Community

- 📖 **Documentation:** [docs/](./docs/README.md)
- 🐛 **Issues:** Use GitHub Issues
- 💬 **Discussions:** Use GitHub Discussions
- 🔍 **Troubleshooting:** [Troubleshooting Guide](./docs/en/troubleshooting/README.md)

---

## 🛣️ Roadmap

- [ ] Additional language support (Chinese, Spanish, French)
- [ ] Stable Diffusion XL support
- [ ] LoRA model integration
- [ ] Batch processing improvements
- [ ] Web UI enhancements
- [ ] Kubernetes deployment guides

---
