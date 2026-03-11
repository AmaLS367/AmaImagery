$ErrorActionPreference='Stop'
docker build -t amaimagery-api:local -f Dockerfile .
Write-Host "[build_images] built amaimagery-api:local"
