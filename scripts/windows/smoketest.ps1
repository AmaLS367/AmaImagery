Param(
  [string]$Api='http://localhost:8000',
  [string]$ExpectedProvider=$env:SMOKE_EXPECT_PROVIDER
)
$ErrorActionPreference='Stop'
$stamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$SmokeEmail = if ($env:SMOKE_EMAIL) { $env:SMOKE_EMAIL } else { "smoke-$stamp@example.com" }
$SmokePassword = if ($env:SMOKE_PASSWORD) { $env:SMOKE_PASSWORD } else { "pass12345" }
$SmokeUsername = if ($env:SMOKE_USERNAME) { $env:SMOKE_USERNAME } else { "smoke$stamp" }

Write-Host "[smoke] healthz"
$health = Invoke-RestMethod -Uri "$Api/api/v1/health" -Method GET
Write-Host "[smoke] health default provider: $($health.providers.default_provider)"
$readiness = Invoke-RestMethod -Uri "$Api/api/v1/healthz" -Method GET
if (-not $readiness.generation_ready) {
  throw "Generation readiness is false: $($readiness | ConvertTo-Json -Depth 6)"
}
if (-not $readiness.default_provider_usable) {
  throw "Default provider is not usable: $($readiness | ConvertTo-Json -Depth 6)"
}

Write-Host "[smoke] register"
try {
  Invoke-RestMethod -Uri "$Api/api/v1/auth/register" -Method POST -Body (@{
    email = $SmokeEmail
    password = $SmokePassword
    username = $SmokeUsername
  } | ConvertTo-Json) -ContentType 'application/json' | Out-Null
} catch {
  $status = $_.Exception.Response.StatusCode.value__
  if ($status -ne 409) {
    throw
  }
}

Write-Host "[smoke] login"
$login = Invoke-RestMethod -Uri "$Api/api/v1/auth/login" -Method POST -Body (@{
  identifier = $SmokeEmail
  password = $SmokePassword
} | ConvertTo-Json) -ContentType 'application/json'
$token = $login.access_token
if (-not $token) {
  throw "Login response missing access_token"
}
$headers = @{ Authorization = "Bearer $token" }

Write-Host "[smoke] generate"
$body = @{
  prompt="a cat"; steps=5; guidance_scale=4; width=256; height=256; seed=1
}
$resp = Invoke-RestMethod -Uri "$Api/api/v1/images/generate" -Method POST -Body ($body | ConvertTo-Json) -ContentType 'application/json' -Headers $headers
$taskId = $resp.task_id
if (-not $taskId) {
  throw "No task_id returned: $($resp | ConvertTo-Json -Depth 5)"
}

$url = $null
$terminalProvider = $null
for ($i = 0; $i -lt 60; $i++) {
  $status = Invoke-RestMethod -Uri "$Api/api/v1/images/status/$taskId" -Method GET -Headers $headers
  if ($status.status -eq "completed" -and $status.image_url) {
    $url = "$Api$($status.image_url)"
    $terminalProvider = $status.provider_name
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
if ($ExpectedProvider -and $terminalProvider -ne $ExpectedProvider) {
  throw "Expected provider '$ExpectedProvider' but got '$terminalProvider'"
}

Write-Host "[smoke] file $url"
Invoke-WebRequest -Uri $url -OutFile "$env:TEMP\amaimagery_smoke.bin" -Headers $headers | Out-Null

Write-Host "[smoke] history"
$history = Invoke-RestMethod -Uri "$Api/api/v1/users/me/generations?limit=20&offset=0" -Method GET -Headers $headers
$item = $history.items | Where-Object { "$($_.task_id)" -eq "$taskId" } | Select-Object -First 1
if (-not $item) {
  throw "History did not include task $taskId"
}
if ($ExpectedProvider -and $item.provider_name -ne $ExpectedProvider) {
  throw "History provider mismatch: expected '$ExpectedProvider', got '$($item.provider_name)'"
}
Write-Host "[smoke] ok"
