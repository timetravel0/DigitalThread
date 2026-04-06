$ErrorActionPreference = "Stop"

function Get-FreePort {
  $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
  $listener.Start()
  try {
    return ([System.Net.IPEndPoint]$listener.LocalEndpoint).Port
  } finally {
    $listener.Stop()
  }
}

function Wait-Url {
  param(
    [Parameter(Mandatory = $true)][string]$Url,
    [Parameter(Mandatory = $true)][scriptblock]$Predicate,
    [int]$TimeoutSeconds = 120
  )

  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  $lastError = $null
  while ((Get-Date) -lt $deadline) {
    try {
      $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
      if (& $Predicate $response) {
        return $response
      }
      $lastError = "Unexpected status $($response.StatusCode) for $Url"
    } catch {
      $lastError = $_.Exception.Message
    }
    Start-Sleep -Seconds 1
  }

  throw "Timed out waiting for $Url. $lastError"
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$apiRoot = Join-Path $repoRoot "apps\api"
$webRoot = Join-Path $repoRoot "apps\web"
$tempDir = Join-Path $env:TEMP ("threadlite-web-smoke-" + ([guid]::NewGuid().ToString("N")))
New-Item -ItemType Directory -Path $tempDir | Out-Null
$dbPath = Join-Path $tempDir "smoke.db"
$dbUrl = "sqlite:///" + ($dbPath -replace "\\", "/")
$apiPort = Get-FreePort
$webPort = Get-FreePort
$apiUrl = "http://127.0.0.1:$apiPort"
$webUrl = "http://127.0.0.1:$webPort"
$apiOut = Join-Path $tempDir "api.out.log"
$apiErr = Join-Path $tempDir "api.err.log"
$buildOut = Join-Path $tempDir "build.out.log"
$buildErr = Join-Path $tempDir "build.err.log"
$webOut = Join-Path $tempDir "web.out.log"
$webErr = Join-Path $tempDir "web.err.log"

$oldDatabaseUrl = $env:DATABASE_URL
$oldApiBaseUrl = $env:NEXT_PUBLIC_API_BASE_URL
$oldPort = $env:PORT
$oldHostname = $env:HOSTNAME
$env:DATABASE_URL = $dbUrl
$apiProc = $null
$webProc = $null

try {
  $apiProc = Start-Process -FilePath "python" -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$apiPort") -WorkingDirectory $apiRoot -PassThru -RedirectStandardOutput $apiOut -RedirectStandardError $apiErr
  Wait-Url -Url "$apiUrl/api/health" -Predicate { param($r) $r.StatusCode -eq 200 -and ($r.Content | ConvertFrom-Json).status -eq "ok" } | Out-Null

  $manufacturing = Invoke-RestMethod -Method Post -Uri "$apiUrl/api/seed/manufacturing-demo" -ContentType "application/json" -Body "{}"
  $personal = Invoke-RestMethod -Method Post -Uri "$apiUrl/api/seed/personal-demo" -ContentType "application/json" -Body "{}"

  $env:NEXT_PUBLIC_API_BASE_URL = $apiUrl
  & cmd /c npm run build *> $buildOut
  if ($LASTEXITCODE -ne 0) {
    throw "Frontend build failed with exit code $LASTEXITCODE."
  }

  $env:PORT = "$webPort"
  $env:HOSTNAME = "127.0.0.1"
  $standaloneServer = Join-Path $webRoot ".next\standalone\server.js"
  $webProc = Start-Process -FilePath "node" -ArgumentList @($standaloneServer) -WorkingDirectory $webRoot -PassThru -RedirectStandardOutput $webOut -RedirectStandardError $webErr
  Wait-Url -Url "$webUrl/dashboard" -Predicate { param($r) $r.StatusCode -eq 200 } | Out-Null

  $env:SMOKE_API_URL = $apiUrl
  $env:SMOKE_WEB_URL = $webUrl

  & node (Join-Path $webRoot "tests\smoke.test.mjs")
  if ($LASTEXITCODE -ne 0) {
    throw "Frontend smoke assertions failed."
  }
}
finally {
  if (Test-Path $apiOut) { Get-Content $apiOut -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "[api] $_" } }
  if (Test-Path $apiErr) { Get-Content $apiErr -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "[api] $_" } }
  if (Test-Path $buildOut) { Get-Content $buildOut -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "[build] $_" } }
  if (Test-Path $buildErr) { Get-Content $buildErr -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "[build] $_" } }
  if (Test-Path $webOut) { Get-Content $webOut -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "[web] $_" } }
  if (Test-Path $webErr) { Get-Content $webErr -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "[web] $_" } }
  if ($webProc) {
    try { Stop-Process -Id $webProc.Id -Force -ErrorAction SilentlyContinue } catch {}
  }
  if ($apiProc) {
    try { Stop-Process -Id $apiProc.Id -Force -ErrorAction SilentlyContinue } catch {}
  }
  $env:DATABASE_URL = $oldDatabaseUrl
  $env:NEXT_PUBLIC_API_BASE_URL = $oldApiBaseUrl
  $env:PORT = $oldPort
  $env:HOSTNAME = $oldHostname
  if (Test-Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
  }
}
