#!/usr/bin/env bash
set -euo pipefail
docker build -t amaimagery-api:local -f Dockerfile .
echo "[build_images] built amaimagery-api:local"
