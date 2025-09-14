#!/usr/bin/env bash
set -euo pipefail
SCR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCR_DIR/../.." && pwd)"
if [ -f "$SCR_DIR/preflight.sh" ]; then bash "$SCR_DIR/preflight.sh" || true; fi
if [ -f "$SCR_DIR/build_frontend.sh" ]; then bash "$SCR_DIR/build_frontend.sh"; fi
if [ -f "$SCR_DIR/migrate.sh" ]; then bash "$SCR_DIR/migrate.sh"; fi
if [ -f "$SCR_DIR/seed.sh" ]; then bash "$SCR_DIR/seed.sh" || true; fi
if [ -f "$SCR_DIR/run_local.sh" ]; then exec bash "$SCR_DIR/run_local.sh"; fi
echo "run_local.sh not found in $SCR_DIR" >&2
exit 1
