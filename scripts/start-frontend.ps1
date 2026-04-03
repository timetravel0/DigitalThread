param(
    [string]$ApiBaseUrl = "http://localhost:8000"
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$webDir = Join-Path $repoRoot "apps/web"

Set-Location $webDir
$env:NEXT_PUBLIC_API_BASE_URL = $ApiBaseUrl

npm run dev
