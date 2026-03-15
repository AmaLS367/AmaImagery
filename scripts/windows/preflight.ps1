param(
  [ValidateSet('local', 'prod', 'cpu')]
  [string]$Mode = 'local'
)
$ErrorActionPreference='Stop'

Write-Host "[preflight] tools"
& docker --version | Out-Null
& docker compose version | Out-Null

if ($Mode -ne 'cpu') {
  if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    Write-Host "[preflight] GPU OK:"; & nvidia-smi -L
  } else {
    Write-Host "[preflight] nvidia-smi not found (OK for cpu/local)"
  }
}

Write-Host "[preflight] env files"
switch ($Mode) {
  'local' {
    if (-not (Test-Path docker/.env.docker)) { Copy-Item docker/.env.docker.example docker/.env.docker }
  }
  'cpu' {
    if (-not (Test-Path docker/.env.docker)) { Copy-Item docker/.env.docker.example docker/.env.docker }
  }
  'prod' {
    if (-not (Test-Path docker/.env.prod)) { Copy-Item docker/.env.prod.example docker/.env.prod }
  }
}

Write-Host "[preflight] frontend dist"
$hasRoot = Test-Path frontend/dist
if (-not $hasRoot) {
  Write-Warning "dist missing, run scripts/windows/build_frontend.ps1"
}
Write-Host "[preflight] ok"
