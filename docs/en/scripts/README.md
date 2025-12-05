# Scripts Documentation

## Overview

Collection of utility scripts for bootstrapping, building, migrating, and managing the AI Image Generator application. Scripts are available for both Linux and Windows platforms.

## Script Categories

### 🚀 Bootstrap Scripts
Initialize the development or production environment with all dependencies and configurations.

**Linux:** `scripts/linux/bootstrap.sh`
**Windows:** `scripts/windows/bootstrap.ps1`

### 🔨 Build Scripts
Build Docker images and frontend assets.

**Linux:** `scripts/linux/build_images.sh`, `build_frontend.sh`
**Windows:** `scripts/windows/build_images.ps1`, `build_frontend.ps1`

### 🗄️ Migration Scripts
Run database migrations.

**Linux:** `scripts/linux/migrate.sh`
**Windows:** `scripts/windows/migrate.ps1`

### ⚙️ Run Scripts
Start the application in different modes.

**Linux:** `scripts/linux/run_local.sh`, `run_prod.sh`
**Windows:** `scripts/windows/run_local.ps1`, `run_prod.ps1`

### 🧪 Testing Scripts
Run smoke tests and validation.

**Linux:** `scripts/linux/smoketest.sh`
**Windows:** `scripts/windows/smoketest.ps1`

### 🌱 Seed Scripts
Seed the database with initial data.

**Linux:** `scripts/linux/seed.sh`
**Windows:** `scripts/windows/seed.ps1`

### 🐍 Python Utilities
Helper scripts in Python.

- `generate_context.py` - Generate project context
- `generate_secret_key.py` - Generate secure keys
- `warm_cache.py` - Warm up model cache
- `Checkdoubles.py` - Check for duplicate code

## Documentation Sections

- [Bootstrap](./bootstrap.md) - Bootstrap scripts
- [Build](./build.md) - Build scripts
- [Migration](./migration.md) - Migration scripts
- [Utilities](./utilities.md) - Utility scripts
- [Windows vs Linux](./windows-vs-linux.md) - Platform differences

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

### Build for Production
```bash
# Linux
./scripts/linux/build_images.sh

# Windows
.\scripts\windows\build_images.ps1
```

## Script Requirements

- **Linux:** Bash 4.0+, standard GNU tools
- **Windows:** PowerShell 5.1+
- **Python:** 3.11+ for Python utilities

