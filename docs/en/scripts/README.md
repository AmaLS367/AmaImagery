# Scripts Documentation

## Overview

Collection of utility scripts for bootstrapping, building, migrating, running, testing, and maintaining **AmaImagery**. Scripts are available for both Linux and Windows, plus Python utilities.

## Script Categories

### 🚀 Bootstrap Scripts
Initialize development or deployment prerequisites.

**Linux:** `scripts/linux/bootstrap.sh`
**Windows:** `scripts/windows/bootstrap.ps1`

### 🔨 Build Scripts
Build Docker images and frontend assets.

**Linux:** `scripts/linux/build_images.sh`, `scripts/linux/build_frontend.sh`
**Windows:** `scripts/windows/build_images.ps1`, `scripts/windows/build_frontend.ps1`

### 🗄️ Migration Scripts
Run database migrations.

**Linux:** `scripts/linux/migrate.sh`
**Windows:** `scripts/windows/migrate.ps1`

### ⚙️ Run Scripts
Start local or production Docker flows.

**Linux:** `scripts/linux/run_local.sh`, `scripts/linux/run_prod.sh`
**Windows:** `scripts/windows/run_local.ps1`, `scripts/windows/run_prod.ps1`

### 🧪 Validation Scripts
Run smoke and helper checks.

**Linux:** `scripts/linux/smoketest.sh`, `scripts/linux/preflight.sh`
**Windows:** `scripts/windows/smoketest.ps1`, `scripts/windows/preflight.ps1`

### 🌱 Seed Scripts
Seed initial data.

**Linux:** `scripts/linux/seed.sh`
**Windows:** `scripts/windows/seed.ps1`

### 🐍 Python Utilities

- `generate_context.py` - Generate a compact project snapshot
- `generate_secret_key.py` - Generate secret keys
- `warm_cache.py` - Warm model cache
- `test_generate.py` - Submit a real generation request and poll result
- `delete_cache.py` - Remove Python cache artifacts
- `Checkdoubles.py` - Check for duplicate FastAPI routes

## Documentation Sections

| Topic | Status |
|------|--------|
| Bootstrap deep-dive | 🚧 Coming soon |
| Build deep-dive | 🚧 Coming soon |
| Migration deep-dive | 🚧 Coming soon |
| Utilities deep-dive | 🚧 Coming soon |
| Windows vs Linux comparison | 🚧 Coming soon |

## Quick Reference

### First Time Setup
```bash
# Linux
./scripts/linux/bootstrap.sh

# Windows
.\scripts\windows\bootstrap.ps1
```

### Run Locally
```bash
# Linux
./scripts/linux/run_local.sh

# Windows
.\scripts\windows\run_local.ps1
```

### Build Frontend
```bash
# Linux
./scripts/linux/build_frontend.sh

# Windows
.\scripts\windows\build_frontend.ps1
```

## Script Requirements

- **Linux:** Bash 4.0+
- **Windows:** PowerShell 5.1+
- **Python:** 3.11+ for Python utilities
