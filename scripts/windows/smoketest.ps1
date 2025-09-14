Param([string]$Api='http://localhost:8000')
$ErrorActionPreference='Stop'

Write-Host "[smoke] healthz"
Invoke-RestMethod -Uri "$Api/healthz" -Method GET | Out-Null

Write-Host "[smoke] generate"
$body = @{
  prompt="a cat"; steps=5; guidance_scale=4; width=256; height=256; seed=1
}
$resp = Invoke-RestMethod -Uri "$Api/generate" -Method POST -Body ($body | ConvertTo-Json) -ContentType 'application/json'

if ($resp.sig -and $resp.exp) {
  $url = "$Api/file?path=$($resp.path)&sig=$($resp.sig)&exp=$($resp.exp)"
} elseif ($resp.path) {
  $url = "$Api/file?path=$($resp.path)"
} elseif ($resp.path.path) {
  $p = $resp.path.path; $s=$resp.path.sig; $e=$resp.path.exp
  $url = if ($s -and $e) { "$Api/file?path=$p&sig=$s&exp=$e" } else { "$Api/file?path=$p" }
} else {
  throw "Unexpected response: $($resp | ConvertTo-Json -Depth 5)"
}

Write-Host "[smoke] file $url"
Invoke-WebRequest -Uri $url -OutFile "$env:TEMP\genai_smoke.bin" | Out-Null
Write-Host "[smoke] ok"
