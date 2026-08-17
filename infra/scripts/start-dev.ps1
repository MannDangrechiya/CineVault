# CineVault OS v2.0 — Automated Development Environment Startup Script
# Usage:
#   .\scripts\start-dev.ps1
#   .\scripts\start-dev.ps1 -NoBrowser
#   .\scripts\start-dev.ps1 -NoDocker
#   .\scripts\start-dev.ps1 -WithFlutter

param (
    [switch]$NoDocker,
    [switch]$NoBrowser,
    [switch]$WithFlutter,
    [int]$ApiPort = 8000,
    [int]$WebPort = 3000
)

$ErrorActionPreference = "Continue"
$RootDir = (Resolve-Path "$PSScriptRoot\..\..").Path

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "       [CineVault OS v2.0] Development Stack Launcher" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " Root Directory: $RootDir" -ForegroundColor DarkGray
Write-Host " API Port:       $ApiPort" -ForegroundColor DarkGray
Write-Host " Web UI Port:    $WebPort" -ForegroundColor DarkGray
Write-Host ""

# 1. Start Docker Infrastructure (PostgreSQL 16 pgvector, Valkey, RabbitMQ, MinIO, PgBouncer)
if (-not $NoDocker) {
    Write-Host "[1/4] Checking Docker Infrastructure..." -ForegroundColor Yellow
    Push-Location "$RootDir\infra\docker"
    try {
        $dockerCheck = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "      Starting containers via docker compose..." -ForegroundColor DarkGray
            docker compose up -d
            if ($LASTEXITCODE -eq 0) {
                Write-Host "      [OK] Docker infrastructure online (Postgres/pgvector, Valkey, RabbitMQ, MinIO)." -ForegroundColor Green
            } else {
                Write-Warning "Docker compose encountered an issue. Starting standalone mode."
            }
        } else {
            Write-Warning "Docker Desktop is not currently running. Continuing in standalone/offline mode."
        }
    } catch {
        Write-Warning "Docker command unavailable. Running in standalone local mode."
    }
    Pop-Location
} else {
    Write-Host "[1/4] Skipping Docker containers (-NoDocker specified)." -ForegroundColor DarkGray
}

# 2. Check Ollama AI Engine (v2.0 Module 3)
Write-Host ""
Write-Host "[2/4] Checking Ollama AI Neural Engine (Port 11434)..." -ForegroundColor Yellow
try {
    $ollamaReq = [System.Net.WebRequest]::Create("http://localhost:11434/api/tags")
    $ollamaReq.Timeout = 1500
    $ollamaRes = $ollamaReq.GetResponse()
    Write-Host "      [OK] Ollama AI Brain active on http://localhost:11434 (LLM and Embeddings ready)." -ForegroundColor Green
    $ollamaRes.Close()
} catch {
    Write-Host "      [INFO] Ollama is not active on port 11434 (Optional for local AI matchmaking)." -ForegroundColor DarkGray
    Write-Host "             To enable local AI embeddings: run 'ollama serve' in another terminal." -ForegroundColor DarkGray
}

# 3. Launch FastAPI Backend Service
Write-Host ""
Write-Host "[3/4] Launching FastAPI Backend Service (Port $ApiPort)..." -ForegroundColor Yellow
$BackendCmd = "cd '$RootDir'; `$env:PORT = '$ApiPort'; `$env:ENVIRONMENT = 'local_development'; Write-Host '--- CineVault OS v2.0 API Service (Port $ApiPort) ---' -ForegroundColor Cyan; python -m uvicorn services.api.main:app --host 0.0.0.0 --port $ApiPort --reload"
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $BackendCmd
Write-Host "      [OK] Backend process started in dedicated window." -ForegroundColor Green

# 4. Launch Next.js Web Client
Write-Host ""
Write-Host "[4/4] Launching Next.js OLED Web Client (Port $WebPort)..." -ForegroundColor Yellow
$WebCmd = "cd '$RootDir\apps\web'; Write-Host '--- CineVault OS v2.0 Web UI (Port $WebPort) ---' -ForegroundColor Magenta; npm run dev"
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $WebCmd
Write-Host "      [OK] Web client process started in dedicated window." -ForegroundColor Green

# 5. Optional Flutter Client
if ($WithFlutter) {
    Write-Host ""
    Write-Host "[+] Launching Flutter Client..." -ForegroundColor Yellow
    $FlutterCmd = "cd '$RootDir\apps\mobile'; flutter run -d chrome"
    Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $FlutterCmd
    Write-Host "      [OK] Flutter client launched." -ForegroundColor Green
}

# Summary Dashboard
Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "       [READY] CineVault OS v2.0 Services Active!" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "  * Web Application:     http://localhost:$WebPort" -ForegroundColor White
Write-Host "  * Backend API & Docs:  http://localhost:$ApiPort/docs" -ForegroundColor White
Write-Host "  * Social & AI Route:   http://localhost:$WebPort/social" -ForegroundColor White
Write-Host "  * Movies Catalog:      http://localhost:$WebPort/movies" -ForegroundColor White
Write-Host "  * TV Series Catalog:   http://localhost:$WebPort/series" -ForegroundColor White
Write-Host "  * Personal Dashboard:  http://localhost:$WebPort/dashboard" -ForegroundColor White
if (-not $NoDocker) {
    Write-Host "  ---------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "  * RabbitMQ Dashboard:  http://localhost:15672 (guest/guest)" -ForegroundColor DarkGray
    Write-Host "  * MinIO S3 Console:    http://localhost:9001 (minioadmin)" -ForegroundColor DarkGray
    Write-Host "  * Keycloak SSO Console:http://localhost:8080" -ForegroundColor DarkGray
    Write-Host "  * Grafana Metrics:     http://localhost:3002" -ForegroundColor DarkGray
}
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""

if (-not $NoBrowser) {
    Write-Host "Opening web application in default browser..." -ForegroundColor Cyan
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:$WebPort"
}
