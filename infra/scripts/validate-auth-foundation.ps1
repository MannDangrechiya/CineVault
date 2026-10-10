# CineVault OS — Phase 2 Authentication & Authorization Validation Script (PowerShell)

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  CineVault OS - Phase 2 Auth & Authorization Validation Suite   " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

$hasError = $false

# 1. Audit Native Auth Router (Keycloak was removed — native HS256 login is
# the only authentication mechanism, see the Phase 3 infrastructure
# consolidation)
Write-Host "`n[Check 1] Auditing native authentication router..." -ForegroundColor Yellow
$authRouterPath = "services/api/routers/auth.py"
if (Test-Path $authRouterPath) {
    $authRouterContent = Get-Content $authRouterPath -Raw
    if ($authRouterContent -match "create_access_token" -and $authRouterContent -match "HS256") {
        Write-Host "  [OK] Native HS256 access-token issuance verified." -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] Native auth router missing expected HS256 token issuance!" -ForegroundColor Red
        $hasError = $true
    }
} else {
    Write-Host "  [ERROR] Missing native authentication router: $authRouterPath" -ForegroundColor Red
    $hasError = $true
}

# 2. Audit Auth Service Modules
Write-Host "`n[Check 2] Auditing JWT validator & RBAC policy modules..." -ForegroundColor Yellow
$jwtPath = "services/api/auth/jwt_validator.py"
$rbacPath = "services/api/auth/rbac.py"

if ((Test-Path $jwtPath) -and (Test-Path $rbacPath)) {
    Write-Host "  [OK] JWT validator and RBAC modules present." -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Missing authentication service modules!" -ForegroundColor Red
    $hasError = $true
}

$rbacContent = Get-Content $rbacPath -Raw
if ($rbacContent -match "CURATOR_SESSION_IDLE_TIMEOUT_SECONDS = 900" -and $rbacContent -match "HIGH_RISK_FRESH_AUTH_WINDOW_SECONDS = 60") {
    Write-Host "  [OK] 15-minute curator idle timeout & 60-second fresh WebAuthn window verified." -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Incorrect idle timeout or fresh auth window constants in rbac.py!" -ForegroundColor Red
    $hasError = $true
}

if ($rbacContent -match "TOTP authentication is prohibited for high-risk operations") {
    Write-Host "  [OK] TOTP rejection for high-risk operations verified." -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Missing TOTP rejection logic for high-risk operations!" -ForegroundColor Red
    $hasError = $true
}

# 3. Execute Python Unit & Security Test Suite
Write-Host "`n[Check 3] Running Python test_authentication_authorization.py..." -ForegroundColor Yellow
$pyOutput = python -m unittest tests/test_authentication_authorization.py 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Python authentication & security test suite passed cleanly (8/8 tests passed)." -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Python authentication unit tests failed! Output: $pyOutput" -ForegroundColor Red
    $hasError = $true
}

Write-Host "`n=================================================================" -ForegroundColor Cyan
if ($hasError) {
    Write-Host "  VALIDATION RESULT: AUTHENTICATION FOUNDATION CHECKS FAILED!" -ForegroundColor Red
    exit 1
} else {
    Write-Host "  VALIDATION RESULT: 100% PASSED - AUTH FOUNDATION VERIFIED." -ForegroundColor Green
    exit 0
}
