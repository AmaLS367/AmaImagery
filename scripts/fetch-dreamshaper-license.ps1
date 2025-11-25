# scripts\fetch-dreamshaper-license.ps1
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$targetDir  = "models\AmaFusion_V1\LICENSES"
$targetFile = Join-Path $targetDir "Upstream_DreamShaper_LICENSE.txt"

# Официальные страницы с пометкой лицензии "creativeml-openrail-m"
$hfPrimary = "https://huggingface.co/Lykon/dreamshaper-6"
$hfAlt     = "https://huggingface.co/stablediffusionapi/dreamshaper-v6"

if (!(Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir | Out-Null
}

$openrailLocal = Join-Path $targetDir "OpenRAIL-M.txt"
$openrailNote = if (Test-Path $openrailLocal) {
    "Full license text is provided locally in: OpenRAIL-M.txt"
} else {
    "Full CreativeML Open RAIL-M text is not found locally. Fetch it first via scripts\fetch-openrail.ps1."
}

$content = @"
Upstream Model: DreamShaper v6 (a derivative of Stable Diffusion v1.5)
Upstream License: CreativeML Open RAIL-M
Upstream Sources (license label on model cards):
- $hfPrimary
- $hfAlt

This file records the upstream licensing state for the base model used in fine-tuning.
The derivative model (AmaFusion_V1) must retain the CreativeML Open RAIL-M notices and use-based restrictions required by upstream.

$openrailNote

Chain of provenance:
- Stable Diffusion v1.5 → CreativeML Open RAIL-M (base)
- DreamShaper v6 → CreativeML Open RAIL-M (upstream derivative)
- AmaFusion_V1 → derivative of DreamShaper v6

Recorded: $(Get-Date -Format s)
Maintainer: <your name or handle>
"@

Set-Content -Path $targetFile -Value $content -Encoding UTF8

Write-Host "Created: $targetFile"
if (!(Test-Path $openrailLocal)) {
    Write-Warning "OpenRAIL-M.txt not found. Run scripts\fetch-openrail.ps1 to fetch the full license text."
}
