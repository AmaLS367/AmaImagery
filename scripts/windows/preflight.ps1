$ErrorActionPreference='Stop'

Write-Host "[preflight] tools"
& docker --version | Out-Null
& docker compose version | Out-Null

if ($Profile -ne 'cpu') {
  if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    Write-Host "[preflight] GPU OK:"; & nvidia-smi -L
  } else {
    Write-Host "[preflight] nvidia-smi not found (OK for cpu/local)"
  }
}

Write-Host "[preflight] env files"
if (-not (Test-Path docker/.env.local)) { Copy-Item docker/.env.local.example docker/.env.local }
if (-not (Test-Path docker/.env.prod))  { Copy-Item docker/.env.prod.example  docker/.env.prod }

Write-Host "[preflight] frontend dist"
$hasRoot = Test-Path frontend/dist
if (-not $hasRoot) {
  Write-Warning "dist missing, run scripts/windows/build_frontend.ps1"
}
Write-Host "[preflight] ok"
