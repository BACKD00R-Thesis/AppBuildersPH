$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$server = Join-Path $root "server"
$python = Join-Path $server ".venv\Scripts\python.exe"
$webIndex = Join-Path $root "apps\web\dist\index.html"

Set-Location $root

if (-not (Test-Path $python)) {
    Write-Host "Backend virtual environment is missing." -ForegroundColor Red
    Write-Host "Run this first:"
    Write-Host "  py -3.12 -m venv server\.venv"
    Write-Host "  server\.venv\Scripts\python.exe -m pip install -r server\requirements.txt"
    exit 1
}

if (-not (Test-Path $webIndex)) {
    Write-Host "Web app build is missing." -ForegroundColor Yellow
    Write-Host "Building apps\web\dist now..."
    Push-Location (Join-Path $root "apps\web")
    npm install
    npm run build
    Pop-Location
}

$listener = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($listener) {
    Write-Host "Port 8000 is already in use." -ForegroundColor Red
    Write-Host "That usually means an older Brainrot Study server is still running."
    Write-Host "Stop the old VS Code/PowerShell terminal with Ctrl+C, then run this script again."
    Write-Host ""
    Write-Host "Process id using the port:"
    $listener | Select-Object -ExpandProperty OwningProcess | Sort-Object -Unique
    exit 1
}

Write-Host "Starting Brainrot Study at http://localhost:8000" -ForegroundColor Green
Write-Host "Keep this terminal open while using the app. Press Ctrl+C to stop it."
Write-Host ""

Start-Process "http://localhost:8000"
Set-Location $server
& $python -m app
