param(
    [string]$BackendUrl = "sqlite:///./threadlite.db",
    [string]$FrontendOrigin = "http://localhost:3000"
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot "apps/api"

Set-Location $backendDir
$env:DATABASE_URL = $BackendUrl
$env:CORS_ORIGINS = $FrontendOrigin

python -m alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
