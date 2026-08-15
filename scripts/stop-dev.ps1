# CineVault OS — Automated Development Environment Shutdown Script
# Usage: .\scripts\stop-dev.ps1

$RootDir = Resolve-Path "$PSScriptRoot\.."

Write-Host "`n===============================================" -ForegroundColor Yellow
Write-Host "       🛑 Stopping CineVault Development Stack" -ForegroundColor Yellow
Write-Host "===============================================`n" -ForegroundColor Yellow

# 1. Stop Docker containers safely
Write-Host "[1/2] Stopping Docker containers..." -ForegroundColor Yellow
Push-Location $RootDir
docker compose stop
Pop-Location
Write-Host "      ✓ Docker containers stopped." -ForegroundColor Green

# 2. Terminate background node / python dev server instances if still running
Write-Host "`n[2/2] Cleaning up port bindings (8002 & 3000)..." -ForegroundColor Yellow

function Stop-PortProcess([int]$Port) {
    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        if ($connections) {
            foreach ($conn in $connections) {
                Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
                Write-Host "      ✓ Stopped process on port $Port (PID: $($conn.OwningProcess))" -ForegroundColor Green
            }
        }
    } catch {}
}

Stop-PortProcess -Port 8002
Stop-PortProcess -Port 3000

Write-Host "`n===============================================" -ForegroundColor Green
Write-Host "       💤 CineVault environment shut down." -ForegroundColor Green
Write-Host "===============================================`n" -ForegroundColor Green
