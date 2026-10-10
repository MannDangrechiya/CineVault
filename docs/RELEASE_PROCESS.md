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

1. **Pre-flight check**: Take a fresh backup and verify it restores — `scripts/backup_postgres.sh` then a test restore into a disposable database, per [docs/backup-recovery.md](backup-recovery.md). Do not proceed on an unverified or stale backup.
2. **Schema validation**: Run `flyway -url=jdbc:postgresql://<host>:5432/<db> -user=<user> -password=<password> -locations=filesystem:db/migrations validate` to confirm applied migration checksums match what's on disk before applying anything new. (There is no `scripts/validate_migrations.py` — an earlier version of this doc referenced one that was never actually written; this is the real, existing equivalent.)
3. **Apply migration**: Let the `flyway` service in `docker-compose.prod.yml` run `migrate` (each migration executes in its own transaction, Flyway's default) — do not hand-run SQL against production outside of it.
4. **Post-migration reconciliation**: Run `python scripts/audit_db_integrity.py` and compare canonical title/duplicate/orphan counts against the pre-migration baseline.

---

## 4. Rollback Execution Plan

Flyway migrations in this project are **forward-only** (see [docs/backup-recovery.md §5](backup-recovery.md)) — there is no supported down-migration. Do not hand-write reverse DDL against a live production database.

If a release encounters critical health degradation (e.g. error rate > 1% or p99 > 500ms):
1. **Traffic reroute**: Point Caddy/gateway traffic back to the previous known-good container deployment (previous image tag / previous commit — see the rollback procedure this doc's release checklist links to).
2. **Schema rollback, if the migration itself is the problem**: Do not attempt manual reverse DDL. Restore the pre-migration backup taken in §3 step 1 into production, per [docs/backup-recovery.md](backup-recovery.md), then fix the migration in source control and re-apply the corrected forward migration in a later release.
3. **Cache flush**: Invalidate Valkey application caches.
4. **Health check**: Verify `/health/readiness` on the rolled-back instances.
