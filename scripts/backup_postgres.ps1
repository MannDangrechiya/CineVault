# ==============================================================================
# CineVault OS — Automated PostgreSQL Backup Script (Windows PowerShell)
# ==============================================================================
# Dumps the entire database using custom-format binary compression (pg_dump -F c).
# Supports retention pruning (defaults to keeping 14 days of backups).
#
# Usage:
#   .\scripts\backup_postgres.ps1 [-BackupDir "C:\backups\cinevault"] [-RetentionDays 14]
# ==============================================================================

[CmdletBinding()]
param(
    [string]$BackupDir = ".\backups",
    [int]$RetentionDays = 14,
    [string]$PostgresUser = $env:POSTGRES_USER,
    [string]$PostgresDb = $env:POSTGRES_DB
)

$ErrorActionPreference = "Stop"

if (-not $PostgresUser) { $PostgresUser = "cinevault_dev" }
if (-not $PostgresDb) { $PostgresDb = "cinevault" }

if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$FileName = "cinevault_backup_${Timestamp}.dump"
$FilePath = Join-Path $BackupDir $FileName

Write-Host "[INFO] Starting CineVault database backup at $(Get-Date)..." -ForegroundColor Cyan
Write-Host "[INFO] Target path: $FilePath" -ForegroundColor Cyan

# Check if Docker container is available
$DockerContainers = docker ps --format '{{.Names}}' 2>$null
$PgContainer = $DockerContainers | Where-Object { $_ -match "^cinevault-.*postgres" } | Select-Object -First 1

if ($PgContainer) {
    Write-Host "[INFO] Executing pg_dump via Docker container: $PgContainer" -ForegroundColor Green
    docker exec $PgContainer pg_dump -U $PostgresUser -d $PostgresDb -F c -b > $FilePath
} else {
    Write-Host "[INFO] Executing local pg_dump..." -ForegroundColor Green
    & pg_dump -U $PostgresUser -d $PostgresDb -F c -b -f $FilePath
}

if (Test-Path $FilePath) {
    $FileSize = (Get-Item $FilePath).Length / 1MB
    Write-Host ("[SUCCESS] Database backup created successfully ({0:N2} MB): {1}" -f $FileSize, $FilePath) -ForegroundColor Green
} else {
    Write-Error "Backup file was not created."
    exit 1
}

# Retention pruning
Write-Host "[INFO] Pruning backups older than $RetentionDays days..." -ForegroundColor Cyan
$Cutoff = (Get-Date).AddDays(-$RetentionDays)
Get-ChildItem -Path $BackupDir -Filter "cinevault_backup_*.dump" | Where-Object { $_.LastWriteTime -lt $Cutoff } | ForEach-Object {
    Write-Host "  -> Removing old backup: $($_.FullName)" -ForegroundColor Yellow
    Remove-Item -Path $_.FullName -Force
}

Write-Host "[SUCCESS] Backup workflow completed." -ForegroundColor Green
