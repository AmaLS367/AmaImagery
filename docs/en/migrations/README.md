# Migrations Documentation

## Overview

Migration and schema-evolution notes for **AmaImagery**.

## Migration Status

The repository currently uses Alembic and the active migration tree under `migrations/`.

Known revisions in the repo:
- `506057d97046_init`
- `91c0d4413c57_generation_lifecycle_and_is_superuser`
- `b4655aadfa03_security_indexes_and_checks`

## Key Topics

### 📋 Refactoring Notes
- schema-affecting refactors
- DB lifecycle changes
- auth/admin related schema changes

### 🔄 Migration Guides
- running `alembic upgrade head`
- creating new revisions
- keeping env/config aligned with DB expectations

### 🏗️ Architectural Changes
- queue lifecycle persistence
- superuser/admin support
- security indexes and checks

## For Developers

- keep migration changes in the same PR as model/code changes
- document schema changes in the same PR as the corresponding code and model changes

## For Operators

- apply migrations before expecting API/worker parity after deploy
- use PostgreSQL for production
