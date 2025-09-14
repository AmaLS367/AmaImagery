$ErrorActionPreference='Stop'
docker build -t genai-api:local -f Dockerfile .
Write-Host "[build_images] built genai-api:local"
