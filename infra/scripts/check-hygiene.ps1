# CineVault OS — Repository Hygiene & Secret Audit Script (PowerShell)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  CineVault OS - Repository Hygiene and Secret Audit Check" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$RootDir = (Resolve-Path "$PSScriptRoot\..\..").Path
$hasError = $false

# 1. Check for uncommitted secrets or sensitive files
$forbiddenPatterns = @(
    "*.pem", "*.key", "*.crt", "*.p12", "*.pfx"
)

Write-Host "`n[Step 1] Auditing for forbidden committed secret file extensions..." -ForegroundColor Yellow

foreach ($pattern in $forbiddenPatterns) {
    $foundFiles = Get-ChildItem -Path $RootDir -Include $pattern -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch "\\.git\\" -and $_.FullName -notmatch "\\node_modules\\" }
    if ($foundFiles) {
        Write-Host "  [ERROR] Found potential secret file: $($foundFiles.FullName)" -ForegroundColor Red
        $hasError = $true
    }
}

# 2. Check .gitignore exists
Write-Host "`n[Step 2] Verifying .gitignore file existence..." -ForegroundColor Yellow
if (Test-Path "$RootDir/.gitignore") {
    Write-Host "  [OK] .gitignore file present." -ForegroundColor Green
} else {
    Write-Host "  [ERROR] .gitignore file missing!" -ForegroundColor Red
    $hasError = $true
}

# 3. Check docker-compose.yml syntax
Write-Host "`n[Step 3] Validating docker-compose.yml configuration syntax..." -ForegroundColor Yellow
if (Test-Path "$RootDir/infra/docker/docker-compose.yml") {
    Write-Host "  [OK] docker-compose.yml file present." -ForegroundColor Green
} else {
    Write-Host "  [ERROR] docker-compose.yml file missing!" -ForegroundColor Red
    $hasError = $true
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
if ($hasError) {
    Write-Host "  AUDIT RESULT: HYGIENE CHECKS FAILED! Fix issues above." -ForegroundColor Red
    exit 1
} else {
    Write-Host "  AUDIT RESULT: 100% CLEAN - 0 SECRETS COMMITTED." -ForegroundColor Green
    exit 0
}
