$ErrorActionPreference='Stop'
./scripts/windows/preflight.ps1 -Profile local
docker compose -f docker/compose.local.yml up -d --build
Write-Host "[run_local] UI http://localhost:8080 / API :8000"
