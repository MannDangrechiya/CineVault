# ==============================================================================
# CineVault OS — Production Stack Launcher & Health Verifier (Windows PowerShell)
# ==============================================================================

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "        CineVault OS — Production Deployment Stack    " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

# 1. Dependency Validation
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is not installed or not in PATH."
    exit 1
}

$ComposeFile = "infra/docker/docker-compose.prod.yml"
if (-not (Test-Path $ComposeFile)) {
    Write-Error "Cannot find compose file at: $ComposeFile"
    exit 1
}

# 2. Environment Configuration
if (Test-Path ".env.prod") {
    Write-Host "[INFO] Loading production variables from .env.prod" -ForegroundColor Green
    Get-Content ".env.prod" | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#")) {
            $key, $value = $line.Split("=", 2)
            if ($key -and $value) {
                [System.Environment]::SetEnvironmentVariable($key.Trim(), $value.Trim(), "Process")
            }
        }
    }
} else {
    Write-Host "[WARN] .env.prod not found. Using default hardened environment." -ForegroundColor Yellow
}

# 3. Spin Up Container Stack
Write-Host "[INFO] Building and starting containerized services..." -ForegroundColor Cyan
docker compose -f $ComposeFile up -d --build

# 4. Polling Loop for Core Health
Write-Host "[INFO] Polling core infrastructure health..." -ForegroundColor Cyan

function Wait-ContainerHealth {
    param(
        [string]$ContainerName,
        [int]$MaxRetries = 25
    )

    Write-Host -NoNewline "  -> Polling $ContainerName : "
    for ($i = 0; $i -lt $MaxRetries; $i++) {
        $inspect = docker inspect --format '{{json .State.Health.Status}}' $ContainerName 2>$null
        if ($inspect -eq '"healthy"' -or $inspect -eq '"running"') {
            Write-Host "READY" -ForegroundColor Green
            return $true
        }
        Write-Host -NoNewline "."
        Start-Sleep -Seconds 2
    }
    Write-Host "TIMEOUT" -ForegroundColor Yellow
    return $false
}

Wait-ContainerHealth -ContainerName "cinevault-prod-postgres" -MaxRetries 25 | Out-Null
Wait-ContainerHealth -ContainerName "cinevault-prod-valkey" -MaxRetries 15 | Out-Null
Wait-ContainerHealth -ContainerName "cinevault-prod-rabbitmq" -MaxRetries 20 | Out-Null

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "      CineVault OS Production Deployment Active!     " -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host "  🌐 Web Application:       http://localhost" -ForegroundColor White
Write-Host "  🚀 Core REST API:         http://localhost/v1" -ForegroundColor White
Write-Host "  📚 OpenAPI Documentation: http://localhost/docs (only if DOCS_ENABLED=true)" -ForegroundColor White
# R1 hardening pass: removed the RabbitMQ Management (15672) and PgBouncer
# (6432) lines that used to print here — neither port is actually published
# by docker-compose.prod.yml (RabbitMQ mgmt never was; PgBouncer's host
# mapping was removed as part of this pass, see that file's pgbouncer
# service comment). Both services remain reachable from other containers on
# the internal Docker network; this banner only advertises what's actually
# reachable from the host/browser.
Write-Host "======================================================" -ForegroundColor Green
