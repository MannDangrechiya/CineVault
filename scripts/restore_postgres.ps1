# ==============================================================================
# CineVault OS — Automated PostgreSQL Restore Script (Windows PowerShell)
# ==============================================================================
# Restores a custom-format binary dump (pg_restore) into target database.
#
# Usage:
#   .\scripts\restore_postgres.ps1 -BackupFile ".\backups\cinevault_backup_20260830_220000.dump"
# ==============================================================================

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$BackupFile,
    [string]$PostgresUser = $env:POSTGRES_USER,
    [string]$PostgresDb = $env:POSTGRES_DB
)

$ErrorActionPreference = "Stop"

if (-not $PostgresUser) { $PostgresUser = "cinevault_dev" }
if (-not $PostgresDb) { $PostgresDb = "cinevault" }

if (-not (Test-Path $BackupFile)) {
    Write-Error "Backup file not found at: $BackupFile"
    exit 1
}

Write-Host "[INFO] Starting CineVault database restore from $BackupFile at $(Get-Date)..." -ForegroundColor Cyan

# Check if Docker container is available
$DockerContainers = docker ps --format '{{.Names}}' 2>$null
$PgContainer = $DockerContainers | Where-Object { $_ -match "^cinevault-.*postgres" } | Select-Object -First 1

if ($PgContainer) {
    Write-Host "[INFO] Restoring via Docker container: $PgContainer" -ForegroundColor Green
    Get-Content $BackupFile -Raw -Encoding Byte | docker exec -i $PgContainer pg_restore -U $PostgresUser -d $PostgresDb --clean --if-exists --no-owner --no-privileges -v
} else {
    Write-Host "[INFO] Restoring via local pg_restore..." -ForegroundColor Green
    & pg_restore -U $PostgresUser -d $PostgresDb --clean --if-exists --no-owner --no-privileges -v $BackupFile
}

Write-Host "[SUCCESS] Restore process completed." -ForegroundColor Green
