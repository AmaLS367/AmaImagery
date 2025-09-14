#!/usr/bin/env bash
set -euo pipefail
docker compose -f docker/compose.local.yml exec -T api bash -lc 'alembic upgrade head'
echo "[migrate] done"
