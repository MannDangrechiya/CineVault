## Summary

R1 production-deployment-readiness fixes for CineVault OS. A prior release-readiness audit found the database/catalog layer solid but the deployment layer had several real blockers — this PR fixes them one at a time, each investigated, fixed, and verified live (not just written and trusted) before moving to the next.

## What's in this PR

1. **W18 IPv6 fix, finally committed** — a Windows IPv6/localhost fix for the Next.js BFF was sitting uncommitted in a prior session; this PR actually commits it.
2. **DB audit scripts** — read-only integrity/table-listing scripts.
3. **Seed-migration isolation** — `db/dev-seed/R__seed_development_taxonomy.sql` was reachable by production Flyway despite being marked dev-only. Reproduced the leak live against a disposable database, then isolated it so `docker-compose.prod.yml`'s Flyway service can no longer see the file at all.
4. **Keycloak + TLS + env-var forwarding + MinIO** — `docker-compose.prod.yml` had no auth service, no working TLS (bare `:80`, no domain), and `fastapi-backend`'s env vars didn't match what the app actually reads. Added Keycloak, three real HTTPS sites via Caddy (app/auth/CDN), forwarded the correct env vars, and added self-hosted MinIO for artwork storage. Every required var fails closed (`docker compose up` refuses to start and names exactly what's missing) — verified both directions.
5. **Rate limiter: Valkey-backed** — the old limiter was per-process in-memory, silently multiplying the effective quota by replica count. Rewrote it as a Valkey-backed atomic fixed-window counter. Full-suite triage after this surfaced 22 test failures; root-caused via controlled before/after runs to a test-isolation issue (`TestClient` shares one identity across the whole suite) — fixed by exempting `local_development`/`test` from enforcement at the dependency layer only, with production enforcement independently verified intact.
6. **Dependency pinning** — both `requirements.txt` files went from open-ended `>=` to exact pins. Along the way, found and fixed two dependencies that were used directly in code but never declared (`redis`, `openpyxl`) — the latter caused the **entire backend to fail to start** in a real Docker build, masked in dev only because it happened to already be installed there.
7. **Doc fixes** — stale version references, a reference to a script that never existed, corrupted markdown formatting, contradictory rollback guidance reconciled.
8. **Multi-stage Dockerfiles + a real crash-loop fix** — rewrote both Dockerfiles to keep build tools out of the runtime image and copy only the source each service needs. While verifying the rebuilt `ai-worker` image against this project's real RabbitMQ 4.x broker, found it crash-loops immediately (RabbitMQ 4.x deprecated a legacy queue pattern Celery's remote-control/peer-discovery features rely on) — a real, severe, pre-existing bug nobody had caught because that container had never actually been run end-to-end before. Fixed and verified `(healthy)`, `RestartCount: 0`.

## Verification performed

- Full pytest suite run before/after the rate-limiter fix: 22→11 (different sets, proving non-determinism) → **10 failed, 617 passed** consistently after the fix, all 10 independently root-caused as pre-existing and unrelated to this PR.
- Previously-flaky test files re-run 3× back-to-back post-fix: 24/24/24 passed.
- Rate limiter: verified atomic and correctly shared across process boundaries via a 20-process concurrency script; verified production enforcement is untouched (blocks at exactly the configured limit with `ENVIRONMENT=production`).
- Both Docker images built from their real Dockerfiles and booted against live Postgres/Valkey/RabbitMQ: `fastapi-backend` — liveness 200, readiness READY (database/cache/queue all `ok`); `ai-worker` — `(healthy)`, stable.
- `docker compose config` validated for `docker-compose.prod.yml` both fully configured and with required vars unset (fails closed as intended).

## Not in this PR (explicitly deferred)

CSP headers (needs testing against the real Next.js build first), the CI/CD pipeline (`release-gate.yml` is currently non-functional — out of scope here), release version-number consistency across web/mobile/backend (needs a product decision), mobile app signing, and the actual production deployment itself (needs a real host + DNS). A handful of pre-existing, unrelated bugs were found and documented but not fixed here (a dead fallback stub in search, a search-scoring gap, two admin-endpoint auth test failures, a health-readiness response-shape mismatch) — none touch anything in this PR.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
