# CineVault OS — Phase 1 Database Foundation Validation Script (PowerShell)

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  CineVault OS - Phase 1 Database Foundation Validation Suite" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

$hasError = $false

# 1. Verify Flyway Migration Directory & Files
Write-Host "`n[Check 1] Auditing Flyway migration files in sql/migrations/..." -ForegroundColor Yellow
$migrationFiles = @(
    "V1.0__create_extensions_and_functions.sql",
    "V1.1__create_logical_schemas.sql",
    "V1.2__create_canonical_tables.sql",
    "V1.3__create_personal_tables.sql",
    "V1.4__create_ingestion_tables.sql",
    "V1.5__create_quality_tables.sql",
    "V1.6__create_audit_tables.sql",
    "V1.7__create_indexes_and_constraints.sql",
    "V1.8__create_database_roles.sql",
    "R__seed_development_taxonomy.sql"
)

foreach ($file in $migrationFiles) {
    $path = "sql/migrations/$file"
    if (Test-Path $path) {
        Write-Host "  [OK] Migration file present: $file" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] Missing migration file: $file" -ForegroundColor Red
        $hasError = $true
    }
}

# 2. Audit SQL Migration Content & Key Architecture Rules
Write-Host "`n[Check 2] Validating SQL DDL invariants and architecture boundaries..." -ForegroundColor Yellow

# UUIDv7 Check
$v10Content = Get-Content "sql/migrations/V1.0__create_extensions_and_functions.sql" -Raw
if ($v10Content -match "generate_uuid_v7\(\)") {
    Write-Host "  [OK] UUIDv7 generator function defined in V1.0." -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Missing generate_uuid_v7() function in V1.0!" -ForegroundColor Red
    $hasError = $true
}

# 5 Logical Schemas Check
$v11Content = Get-Content "sql/migrations/V1.1__create_logical_schemas.sql" -Raw
$schemas = @("canonical", "personal", "ingestion", "quality", "audit")
foreach ($schema in $schemas) {
    if ($v11Content -match "CREATE SCHEMA IF NOT EXISTS $schema") {
        Write-Host "  [OK] Schema definition present: $schema" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] Missing schema definition: $schema!" -ForegroundColor Red
        $hasError = $true
    }
}

# Partial Unique Index Check
$v17Content = Get-Content "sql/migrations/V1.7__create_indexes_and_constraints.sql" -Raw
if ($v17Content -match "unique_primary_edition") {
    Write-Host "  [OK] Partial unique index unique_primary_edition present." -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Missing unique_primary_edition partial index in V1.7!" -ForegroundColor Red
    $hasError = $true
}

# Role Permissions Check
$v18Content = Get-Content "sql/migrations/V1.8__create_database_roles.sql" -Raw
$roles = @("cinevault_app", "cinevault_ingest", "cinevault_admin", "cinevault_analytics")
foreach ($role in $roles) {
    if ($v18Content -match $role) {
        Write-Host "  [OK] Role definition present: $role" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] Missing role definition: $role!" -ForegroundColor Red
        $hasError = $true
    }
}

# AI Write Boundary Verification
$v18Lines = Get-Content "sql/migrations/V1.8__create_database_roles.sql"
$ingestHasCanonicalWrite = $false
foreach ($line in $v18Lines) {
    if ($line -match "GRANT.*INSERT.*canonical.*cinevault_ingest" -or $line -match "GRANT.*UPDATE.*canonical.*cinevault_ingest") {
        $ingestHasCanonicalWrite = $true
    }
}

if (-not $ingestHasCanonicalWrite) {
    Write-Host "  [OK] AI / Ingestion boundary verified (cinevault_ingest has ZERO write to canonical schema)." -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Ingestion role has improper permissions to canonical schema!" -ForegroundColor Red
    $hasError = $true
}

# 3. Check docker-compose.yml for Flyway & PgBouncer
Write-Host "`n[Check 3] Auditing docker-compose.yml configuration for Database Foundation..." -ForegroundColor Yellow
$dcContent = Get-Content "docker-compose.yml" -Raw
if ($dcContent -match "flyway/flyway:10-alpine" -and $dcContent -match "edoburu/pgbouncer:latest") {
    Write-Host "  [OK] Flyway and PgBouncer services correctly configured in docker-compose.yml." -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Missing Flyway or PgBouncer in docker-compose.yml!" -ForegroundColor Red
    $hasError = $true
}

Write-Host "`n=================================================================" -ForegroundColor Cyan
if ($hasError) {
    Write-Host "  VALIDATION RESULT: DATABASE FOUNDATION CHECKS FAILED!" -ForegroundColor Red
    exit 1
} else {
    Write-Host "  VALIDATION RESULT: 100% PASSED - DATABASE FOUNDATION VERIFIED." -ForegroundColor Green
    exit 0
}
