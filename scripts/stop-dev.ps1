# CineVault OS v2.0 — Automated Development Environment Shutdown Script
# Usage:
#   .\scripts\stop-dev.ps1
#   .\scripts\stop-dev.ps1 -DockerDown  # Also remove containers and networks

param (
    [switch]$DockerDown
)

$RootDir = (Resolve-Path "$PSScriptRoot\..").Path

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Yellow
Write-Host "       🛑 CineVault OS v2.0 — Development Stack Shutdown" -ForegroundColor Yellow
Write-Host "=================================================================" -ForegroundColor Yellow
Write-Host ""

# 1. Stop Docker Infrastructure
Write-Host "[1/2] Stopping Docker containers..." -ForegroundColor Yellow
Push-Location $RootDir
try {
    if ($DockerDown) {
        docker compose down
        Write-Host "      ✓ Docker containers and networks removed." -ForegroundColor Green
    } else {
        docker compose stop
        Write-Host "      ✓ Docker containers stopped safely." -ForegroundColor Green
    }
} catch {
    Write-Host "      ℹ Docker daemon not reachable or already stopped." -ForegroundColor DarkGray
}
Pop-Location

# 2. Terminate background node / python dev server instances by port binding
Write-Host ""
Write-Host "[2/2] Releasing network ports and terminating processes..." -ForegroundColor Yellow

function Stop-PortProcess([int]$Port) {
    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        if ($connections) {
            foreach ($conn in $connections) {
                $pidToKill = $conn.OwningProcess
                if ($pidToKill -gt 4) { # Avoid system processes
                    Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
                    Write-Host "      ✓ Stopped process listening on port $Port (PID: $pidToKill)" -ForegroundColor Green
                }
            }
        } else {
            Write-Host "      • Port $Port is clear." -ForegroundColor DarkGray
        }
    } catch {
        Write-Host "      • Port $Port is clear." -ForegroundColor DarkGray
    }
}

Stop-PortProcess -Port 3000 # Next.js Web Client
Stop-PortProcess -Port 8000 # FastAPI Backend (Default)
Stop-PortProcess -Port 8002 # FastAPI Backend (Secondary)
Stop-PortProcess -Port 5000 # Flutter Web Server (if running)

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "       💤 CineVault OS v2.0 environment successfully stopped." -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""
