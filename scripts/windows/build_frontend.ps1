$ErrorActionPreference='Stop'

$dirs = @("frontend")
$root = $dirs | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $root) { throw "frontend directory not found (checked: $($dirs -join ', '))" }

function Invoke-NpmCleanInstall {
  param([string]$dir)
  Push-Location $dir
  try {
    if (Test-Path "node_modules") { 
      taskkill /F /IM node.exe /IM npm.exe /IM pnpm.exe /IM vite.exe /IM rollup.exe 2>$null
      attrib -R -S -H /S /D .
      Remove-Item .\node_modules -Recurse -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path "package-lock.json") {
      npm ci --no-audit --no-fund --loglevel=error
    } else {
      npm i --no-audit --no-fund --loglevel=error
    }
    npm run build
  } catch {
    Write-Warning "npm install/build failed once: $($_.Exception.Message). Retrying after cache clean..."
    npm cache clean --force
    Start-Sleep -Seconds 2
    if (Test-Path "node_modules") { Remove-Item .\node_modules -Recurse -Force -ErrorAction SilentlyContinue }
    if (Test-Path "package-lock.json") {
      npm ci --no-audit --no-fund --loglevel=error
    } else {
      npm i --no-audit --no-fund --loglevel=error
    }
    npm run build
  } finally {
    Pop-Location
  }
}

Invoke-NpmCleanInstall -dir $root
Write-Host "[build_frontend] dist ready at $root/dist"
