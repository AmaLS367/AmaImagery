Param([string]$Api='http://localhost:8000')
$ErrorActionPreference='Stop'

Write-Host "[smoke] healthz"
Invoke-RestMethod -Uri "$Api/api/v1/healthz" -Method GET | Out-Null

Write-Host "[smoke] generate"
$body = @{
  prompt="a cat"; steps=5; guidance_scale=4; width=256; height=256; seed=1
}
$resp = Invoke-RestMethod -Uri "$Api/api/v1/images/generate" -Method POST -Body ($body | ConvertTo-Json) -ContentType 'application/json'
$taskId = $resp.task_id
if (-not $taskId) {
  throw "No task_id returned: $($resp | ConvertTo-Json -Depth 5)"
}

$url = $null
for ($i = 0; $i -lt 60; $i++) {
  $status = Invoke-RestMethod -Uri "$Api/api/v1/images/status/$taskId" -Method GET
  if ($status.status -eq "completed" -and $status.image_url) {
    $url = "$Api$($status.image_url)"
    break
  }
  if ($status.status -eq "failed") {
    throw "Generation failed: $($status | ConvertTo-Json -Depth 5)"
  }
  Start-Sleep -Seconds 2
}

if (-not $url) {
  throw "Timed out waiting for generation $taskId"
}

Write-Host "[smoke] file $url"
Invoke-WebRequest -Uri $url -OutFile "$env:TEMP\amaimagery_smoke.bin" | Out-Null
Write-Host "[smoke] ok"
