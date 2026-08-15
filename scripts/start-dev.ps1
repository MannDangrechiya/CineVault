# CineVault OS — Automated Development Environment Startup Script
# Usage: .\scripts\start-dev.ps1 [-OpenBrowser] [-WithFlutter]

param (
    [switch]$OpenBrowser = $true,
    [switch]$WithFlutter = $false
)

$ErrorActionPreference = "Stop"
$RootDir = Resolve-Path "$PSScriptRoot\.."

Write-Host "`n===============================================" -ForegroundColor Cyan
Write-Host "       🎬 Starting CineVault Development Stack" -ForegroundColor Cyan
Write-Host "===============================================`n" -ForegroundColor Cyan

# 1. Start Docker Infrastructure
Write-Host "[1/3] Starting Docker containers..." -ForegroundColor Yellow
Push-Location $RootDir
try {
    docker compose up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Docker compose returned an error. Ensure Docker Desktop is running."
    }
} catch {
    Write-Error "Failed to start Docker. Is Docker Desktop running?"
}
Pop-Location

Write-Host "      ✓ Infrastructure containers started." -ForegroundColor Green

# 2. Launch FastAPI Backend Service in a new window
Write-Host "`n[2/3] Launching FastAPI Backend (port 8002)..." -ForegroundColor Yellow
$BackendCmd = "cd '$RootDir'; Write-Host '--- CineVault Backend API (Port 8002) ---' -ForegroundColor Cyan; python -m services.api.main"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $BackendCmd

# 3. Launch Next.js Web App in a new window
Write-Host "`n[3/3] Launching Next.js Web App (port 3000)..." -ForegroundColor Yellow
$WebCmd = "cd '$RootDir\web'; Write-Host '--- CineVault Web Frontend (Port 3000) ---' -ForegroundColor Cyan; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $WebCmd

# 4. Optional Flutter Client
if ($WithFlutter) {
    Write-Host "`n[+] Launching Flutter Client..." -ForegroundColor Yellow
    $FlutterCmd = "cd '$RootDir\client'; Write-Host '--- CineVault Flutter Client ---' -ForegroundColor Cyan; flutter run -d chrome"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $FlutterCmd
}

Write-Host "`n===============================================" -ForegroundColor Green
Write-Host "       🎉 All CineVault services launched!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host "  • Web App:         http://localhost:3000" -ForegroundColor White
Write-Host "  • Kong Gateway:    http://localhost:8000" -ForegroundColor White
Write-Host "  • API Docs:        http://localhost:8002/docs" -ForegroundColor White
Write-Host "  • Keycloak:        http://localhost:8080" -ForegroundColor White
Write-Host "  • RabbitMQ:        http://localhost:15672" -ForegroundColor White
Write-Host "  • MinIO Console:   http://localhost:9001" -ForegroundColor White
Write-Host "  • Grafana:         http://localhost:3002" -ForegroundColor White
Write-Host "===============================================`n" -ForegroundColor Green

if ($OpenBrowser) {
    Start-Sleep -Seconds 3
    Start-Process "http://localhost:3000"
}
