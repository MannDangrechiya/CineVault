# CineVault OS — Release & Migration Process

This document formalizes the release engineering, environment management, migration protocol, and rollback procedures for CineVault OS.

---

## 1. Environments

| Environment | Purpose | Auth Strictness | TLS Required | Log Level |
|-------------|---------|-----------------|--------------|-----------|
| `local_development` | Local engineering & iteration | Mock / dev tokens allowed | No | DEBUG |
| `test` | Automated CI & unit/integration test suites | Mock / dev tokens allowed | No | INFO |
| `staging` | Pre-production testing & curator dry-runs | Cryptographic RS256 JWKS | Yes | INFO |
| `production` | Public & canonical client traffic | Cryptographic RS256 JWKS | Yes | WARNING |

---

## 2. Mandatory Release Criteria

Every release manifest (`ReleaseManifest`) must satisfy all 5 quality criteria before promotion:

1. **Automated Tests Passed**: All unit, regression, and integration tests passed.
2. **Database Migration Applied**: Schema migrations verified up to target migration version.
3. **Security Audit Passed**: Security check verified (PKCE, SSRF, injection, user isolation).
4. **Known Issues Documented**: Any known edge cases or non-blocking issues explicitly recorded.
5. **Rollback Plan Documented**: Tested step-by-step rollback procedures.

---

## 3. Migration Protocol

1. **Pre-flight check**: Verify database backup manifest exists and is marked `RESTORE_TESTED`.
2. **Schema validation**: Run `python scripts/validate_migrations.py`.
3. **Apply migration**: Execute forward SQL scripts within an atomic transaction.
4. **Post-migration reconciliation**: Verify title count and table row count parity.

---

## 4. Rollback Execution Plan

If a release encounters critical health degradation (e.g. error rate > 1% or p99 > 500ms):
1. **Traffic reroute**: Point gateway traffic back to previous green container deployment.
2. **Down-migration**: Execute reverse SQL migration if schema changes were non-destructive.
3. **Cache flush**: Invalidate Valkey application caches.
4. **Health check**: Verify `/health/readiness` on rolled-back instances.
