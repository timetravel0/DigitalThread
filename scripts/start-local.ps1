param(
    [string]$BackendUrl = "sqlite:///./threadlite.db",
    [string]$ApiBaseUrl = "http://localhost:8000",
    [string]$FrontendOrigin = "http://localhost:3000"
)

Start-Process powershell.exe -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    (Join-Path $PSScriptRoot "start-backend.ps1"),
    "-BackendUrl",
    $BackendUrl,
    "-FrontendOrigin",
    $FrontendOrigin
)

Start-Process powershell.exe -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    (Join-Path $PSScriptRoot "start-frontend.ps1"),
    "-ApiBaseUrl",
    $ApiBaseUrl
)

$ready = $false
$deadline = (Get-Date).AddSeconds(90)
while ((Get-Date) -lt $deadline) {
    try {
        $response = Invoke-RestMethod -Uri "$ApiBaseUrl/api/health" -Method Get -TimeoutSec 2
        if ($response.status -eq "ok") {
            $ready = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

if (-not $ready) {
    Write-Host "Warning: backend health check did not respond within 90 seconds."
    Write-Host "The frontend was started anyway; refresh once the API window is ready."
}

Write-Host "ThreadLite local dev started."
Write-Host "Backend:  $ApiBaseUrl"
Write-Host "Frontend: http://localhost:3000"
Write-Host "Local mode uses SQLite and creates apps/api/threadlite.db automatically."
