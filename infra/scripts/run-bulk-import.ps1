# CineVault OS v2.0 — High-Speed Bulk IMDb Ingestion Launcher
# Usage:
#   .\infra\scripts\run-bulk-import.ps1
#   .\infra\scripts\run-bulk-import.ps1 --min-votes 1000
#   .\infra\scripts\run-bulk-import.ps1 --dry-run
#   .\infra\scripts\run-bulk-import.ps1 --skip-download

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ScriptArgs
)

$RootDir = (Resolve-Path "$PSScriptRoot\..\..").Path
$env:PYTHONPATH = "$RootDir"

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "       [CineVault OS] High-Speed IMDb Bulk Ingestion" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " Root Directory: $RootDir" -ForegroundColor DarkGray
Write-Host " Script:         services/api/scripts/seed_bulk_imdb.py" -ForegroundColor DarkGray
Write-Host " Arguments:      $ScriptArgs" -ForegroundColor DarkGray
Write-Host ""

Push-Location "$RootDir"
try {
    python services/api/scripts/seed_bulk_imdb.py @ScriptArgs
}
finally {
    Pop-Location
}
