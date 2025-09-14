#!/usr/bin/env bash
set -euo pipefail
docker build -t genai-api:local -f Dockerfile .
echo "[build_images] built genai-api:local"
