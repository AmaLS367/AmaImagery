$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (Test-Path "$ScriptDir\preflight.ps1") { Try { & "$ScriptDir\preflight.ps1" } Catch { } }
if (Test-Path "$ScriptDir\build_frontend.ps1") { & "$ScriptDir\build_frontend.ps1" }
if (Test-Path "$ScriptDir\migrate.ps1") { & "$ScriptDir\migrate.ps1" }
if (Test-Path "$ScriptDir\seed.ps1") { Try { & "$ScriptDir\seed.ps1" } Catch { } }
if (Test-Path "$ScriptDir\run_local.ps1") { & "$ScriptDir\run_local.ps1"; exit 0 }
Write-Error "run_local.ps1 not found in $ScriptDir"
exit 1
