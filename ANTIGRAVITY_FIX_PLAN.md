# CineVault — Phase-Wise Remediation Plan (for Antigravity)

Source: `Full Stack Reality Audit` performed 2026-08-09 on commit `42e370c` ("09/08 morning fixes").
This document turns every gap found in that audit into standalone, executable phase prompts.

**How to use this file**
- Each phase below is self-contained — paste its "PROMPT" block directly into Antigravity as a task.
- Run phases in order within a track; tracks (A/B/C) can run in parallel if you have multiple Antigravity sessions.
- Every phase ends with its own git branch + PR. Never commit directly to `master`.
- Do not skip the "Acceptance Criteria" — a phase is not done until they're all green.

---

## 0. Global Rules (apply to every phase)

1. **Repo**: `C:\Desktop\flutter_projects\CineVault`, remote `origin` = `https://github.com/MannDangrechiya/CineVault.git`, default branch `master`.
2. **Branching**: one branch per phase, named `fix/<phase-id>-<short-slug>` (e.g. `fix/9.1-api-contract-year-country`). Branch from latest `master`, never from another feature branch.
3. **Commits**: small, atomic, imperative subject line ≤72 chars, body explains *why* (reference the audit gap number). No `--no-verify`, no forced pushes to `master`.
4. **Tests before PR**: run and paste results into the PR description —
   - Backend: `python -m pytest -v` (from `services/api`)
   - Flutter: `flutter test` and `flutter analyze` (from `client/`)
   - Add/extend tests for whatever you changed — no phase is "done" on a code change with zero new test coverage.
5. **PRs**: open with `gh pr create --base master --head fix/<phase-id>-<slug> --title "<phase-id>: <title>" --body-file <phase>.md`. Body must include: what gap this closes (quote the audit line), what changed, test evidence, and any follow-up left for a later phase.
6. **Merging**: squash-merge only after CI/tests are green and you've re-run `flutter analyze` + `pytest` locally. Delete the branch after merge (`gh pr merge --squash --delete-branch`).
7. **No scope creep**: each phase touches only the files listed under it. If you discover an unrelated bug, log it in `ANTIGRAVITY_FIX_PLAN.md` under a new "Discovered" section at the bottom — do not fix it inline.
8. **Never** commit secrets, API keys, or `.env` files. Real provider keys (OpenAI, Gemini, KOBIS, TVDB) go in `.env.local` / CI secrets, never in git.

---

## Track A — Correctness & Contract Fixes (do these first, they're small and unblock everything else)

### Phase 9.1 — Fix `/v1/titles` query parameter mismatch

**Severity**: High (silent filter failure, no error surfaced to user)
**Branch**: `fix/9.1-api-contract-year-country`

**PROMPT:**
```
Fix the CineVault API contract mismatch on GET /v1/titles.

Context: client/lib/data/remote/titles_remote_datasource.dart sends query params
`year` and `country`, but services/api/routers/titles.py (and its Pydantic query
schema) expects `production_year` and `origin_country`. Because FastAPI ignores
unknown query params by default, the year/country filters silently no-op instead
of erroring — catalog filtering appears broken with no visible cause.

Task:
1. Decide the canonical param names (recommend keeping backend names
   `production_year` / `origin_country` since they match the DB columns in
   canonical.title — see sql/migrations/V1.2__create_canonical_tables.sql).
2. Update client/lib/data/remote/titles_remote_datasource.dart to send
   `production_year` and `origin_country`.
3. Update any Dart models/entities and the CatalogScreen filter UI that
   reference the old names.
4. Add a backend contract test in services/api/tests that asserts a
   GET /v1/titles?production_year=2024&origin_country=KR request actually
   narrows results (not just 200 OK).
5. Add a Flutter widget/unit test that asserts TitlesRemoteDatasource builds
   the request with the corrected param names.
6. Run `flutter analyze`, `flutter test`, and `python -m pytest -v`. Fix any
   regressions.
7. Commit, push branch fix/9.1-api-contract-year-country, open a PR against
   master with test evidence pasted in the description.

Acceptance criteria:
- Filtering catalog by year/country in the Flutter app actually changes results.
- New backend + Flutter tests pass and fail if the param names are reverted.
- No other endpoints' contracts were touched.
```

---

### Phase 9.2 — Real artwork instead of placeholder icons

**Severity**: Medium (visual/product gap, not functional)
**Branch**: `fix/9.2-poster-artwork`

**PROMPT:**
```
Replace placeholder vector icons with real poster/backdrop images across the
CineVault Flutter client.

Context: CatalogScreen, SearchScreen, and TitleDetailScreen currently render
Icon(Icons.movie) / Icon(Icons.tv) inside grey containers instead of loading
artwork. canonical.edition (or wherever poster_url/backdrop_url lives — check
sql/migrations/V1.2__create_canonical_tables.sql and the TitleDetail schema in
services/api) should already carry an image URL field; confirm this.

Task:
1. Confirm the canonical schema/API actually returns a poster/backdrop URL
   field end-to-end (repository -> schema -> Flutter entity). If the column
   or field is missing, add it via a NEW Flyway migration (do not edit
   existing migrations) and thread it through the repository, Pydantic
   schema, and Flutter entity/fromJson.
2. Replace the Icon(Icons.movie)/Icon(Icons.tv) placeholders in
   client/lib/presentation/screens/catalog_screen.dart,
   search_screen.dart, and title_detail_screen.dart with
   Image.network(posterUrl, ...) using a loading placeholder
   (shimmer or grey box) and an errorBuilder that falls back to the
   current icon (never show a broken-image glyph).
3. Add caching via cached_network_image (check pubspec.yaml — add the
   dependency only if not already present) to avoid re-downloading on
   every scroll.
4. Add a widget test that verifies the fallback icon renders when the
   image URL is null/empty, and that Image.network is used when a URL
   is present.
5. Run flutter analyze / flutter test.
6. Commit, push, open PR.

Acceptance criteria:
- Titles with a poster URL show a real image; titles without one show the
  existing icon fallback (no broken-image UI).
- No change to any API route contract other than an additive field.
```

---

### Phase 9.3 — Control Room UI gap: mark scope, don't silently skip

**Severity**: N/A — informational, folds into Track B Phase 9.7 below. (Left here as a pointer so the track list stays complete.)

---

## Track B — Real External Integrations (each is independent; can run in parallel across separate Antigravity sessions)

### Phase 9.4 — Live OpenAI provider adapter

**Severity**: High (AI Assistant is currently 100% mock in a path presented to users as real)
**Branch**: `fix/9.4-openai-live-provider`

**PROMPT:**
```
Implement a real OpenAI-backed AIProviderAdapter for CineVault's AI Assistant.

Context: services/api/ai/provider.py defines OpenAIProviderAdapter and
GeminiProviderAdapter as stub classes that just delegate to
MockAIProviderAdapter. No live HTTP call is made. This must change WITHOUT
weakening the existing safety rails (prompt sanitization, no arbitrary SQL,
grounded-only responses, proposal staging into quality.ai_proposal_staging
rather than direct canonical writes).

Task:
1. Read the existing AIProviderAdapter interface/base class and
   MockAIProviderAdapter to understand the exact contract (input, output
   shape, grounding requirements) — the real adapter must return the same
   shape.
2. Implement OpenAIProviderAdapter using the official OpenAI SDK (add as a
   dependency in the appropriate requirements/pyproject file). Read the API
   key from an environment variable (e.g. OPENAI_API_KEY) via the existing
   config loader — never hardcode a key, never commit one.
3. Preserve prompt sanitization and secret redaction that already exists in
   the assistant pipeline — the live adapter must go through the same
   sanitize step as the mock path, not bypass it.
4. Add a feature flag / config toggle (e.g. AI_PROVIDER=mock|openai|gemini)
   so mock remains available for local dev/tests without a real API key.
5. Add error handling: on provider timeout/error, fail gracefully to a
   clear error response — do NOT silently fall back to mock output and
   present it as if it were the live provider (that would reintroduce the
   exact problem this phase fixes).
6. Write tests that mock the OpenAI HTTP client (do not hit the real API in
   CI) to verify: request shape, sanitization is applied, grounded response
   parsing, and error-path behavior.
7. Document required env vars in README/`.env.example`.
8. Run pytest, commit, push, open PR. Note in the PR description that this
   was tested with MOCK http responses only — flag that a real end-to-end
   smoke test against the live OpenAI API should be run manually before
   merge, and paste that manual result too if you have a key available.

Acceptance criteria:
- With AI_PROVIDER=mock, existing behavior unchanged (regression-safe).
- With AI_PROVIDER=openai and a valid key, a real HTTP call is made and a
  grounded response is returned.
- No secret is ever logged, committed, or exposed in an error message.
```

---

### Phase 9.5 — Live Gemini provider adapter

**Severity**: High
**Branch**: `fix/9.5-gemini-live-provider`

**PROMPT:**
```
Same as Phase 9.4, but for GeminiProviderAdapter using the Google Gemini API
(GEMINI_API_KEY env var). Reuse the AI_PROVIDER toggle added in 9.4 — extend
it to accept `gemini` as a value rather than inventing a second toggle.
If Phase 9.4 hasn't merged yet, branch from master and expect a merge
conflict resolution on provider.py when both land — call this out explicitly
in the PR description so the human reviewer knows to check the merge.

Acceptance criteria: identical to Phase 9.4, mirrored for Gemini.
```

---

### Phase 9.6 — Live KOBIS + TVDB ingestion adapters

**Severity**: High (ingestion currently returns two hardcoded sample titles only)
**Branch**: `fix/9.6-live-ingestion-adapters`

**PROMPT:**
```
Replace the hardcoded sample-payload ingestion adapters with real HTTP
clients against KOBIS (Korean Box Office Information System) and TheTVDB.

Context: services/api/ingestion/adapters.py — KobisProviderAdapter and
TvdbProviderAdapter currently return static JSON for 기생충 (Parasite) and
Squid Game instead of calling the real provider APIs.

Task:
1. Implement real HTTP calls (httpx/aiohttp, matching whatever async HTTP
   client the rest of the backend already uses) for both providers, reading
   API keys/tokens from env vars (KOBIS_API_KEY, TVDB_API_KEY).
2. Preserve the existing adapter interface/return shape exactly — downstream
   normalization, quality, and reconciliation code must not need to change.
3. Respect whatever rate-limit / licensing constraints the audit flagged
   (services/api/repositories/quality.py and the ADR docs, if any, on
   licensing gates) — do not bypass them.
4. Add retry/backoff and clear error surfacing on provider failure (raw
   ingestion should land in ingestion.raw_payload_capture with a failure
   status, not silently produce empty/fake data).
5. Add tests using recorded/mocked HTTP fixtures (e.g. respx or
   responses) — do not hit the live provider in CI.
6. Confirm the existing governed pipeline is untouched: ingestion ->
   normalization -> quality -> reconciliation -> Control Room curation ->
   canonical promotion. No new direct-to-canonical path should be created.
7. Run pytest, commit, push, open PR.

Acceptance criteria:
- Real HTTP calls are made when API keys are configured; adapters fail
  loudly (not with fake data) when keys are missing or the call errors.
- No path exists from raw ingestion straight into canonical tables —
  everything still passes through Control Room promotion.
```

---

## Track C — Missing Flutter Screens & Flows

### Phase 9.7 — Control Room curator screen in Flutter

**Severity**: Medium-High (feature exists on backend, fully untested from a real UI)
**Branch**: `fix/9.7-control-room-screen`

**PROMPT:**
```
Build a Flutter Control Room screen so curators can actually use the backend
/internal/v1/control-room/* endpoints (candidate review, evidence, promote,
reject, audit) instead of only via raw HTTP.

Task:
1. Read services/api/routers/control_room.py end-to-end to enumerate every
   endpoint, request/response schema, and the curator RBAC requirement.
2. Add a new route + screen (e.g. client/lib/presentation/screens/
   control_room_screen.dart) following the same Clean Architecture +
   Riverpod pattern as the existing screens (see recommendations_screen.dart
   for the pattern to copy: remote datasource, repository, provider, screen).
3. Minimum viable UI: list of quarantine/candidate records with evidence,
   a detail view, and Promote/Reject actions that call the real endpoints.
   Show the resulting audit log entry after an action.
4. Gate this screen behind curator role — if the current user's JWT claims
   don't include the curator role, don't show the tab/route at all (match
   however role-based UI gating already works elsewhere in the app, or add
   the minimal pattern if none exists yet).
5. Handle loading/empty/error states consistently with other screens.
6. Add widget tests for the new screen (list render, promote action,
   RBAC-gated visibility).
7. Run flutter analyze/test, commit, push, open PR.

Acceptance criteria:
- A curator-role test user can view candidates and successfully promote or
  reject one end-to-end against the real backend, producing a real audit
  log row in audit.canonical_audit_log.
- A non-curator user never sees this screen/tab.
```

---

### Phase 9.8 — Login / authentication screen

**Severity**: Medium (currently relies on pre-generated tokens only)
**Branch**: `fix/9.8-auth-login-screen`

**PROMPT:**
```
Add a real login screen to the Flutter client instead of relying on
pre-generated JWTs.

Task:
1. Confirm what auth flow the backend actually expects in non-mock mode
   (services/api/auth/jwt_validator.py, dependencies.py) — likely OIDC via
   Keycloak once Phase 9.10 lands. For now, build the login UI against
   whatever token-issuing endpoint currently exists (or, if none exists yet,
   coordinate with Phase 9.10 and stub against a documented contract, noting
   that explicitly in the PR).
2. Build a login screen (email/password or OIDC redirect, whichever the
   backend supports) that stores the resulting JWT in flutter_secure_storage
   (already wired for tokens per the audit).
3. Add unauthenticated-state routing: on app start with no/expired token,
   route to login before showing any tab; on 401 from any API call, clear
   the stored token and route back to login.
4. Add a logout action.
5. Add widget tests for: successful login stores token and navigates to
   Catalog; failed login shows an error and stays on the login screen;
   expired-token 401 mid-session bounces back to login.
6. Run flutter analyze/test, commit, push, open PR.

Acceptance criteria:
- App is unusable without a valid session (no more permanently-baked token).
- 401 responses are handled gracefully everywhere, not just on the screen
  that happened to trigger them.
```

---

### Phase 9.9 — Auto-sync on reconnect

**Severity**: Low-Medium (offline sync works, but only via manual button press)
**Branch**: `fix/9.9-auto-sync-reconnect`

**PROMPT:**
```
Make offline sync trigger automatically on network reconnect instead of
requiring a manual button press on SyncStatusScreen.

Task:
1. Add a connectivity listener (connectivity_plus or similar — check
   pubspec.yaml for what's already available before adding a new dep) that
   fires when the device transitions offline -> online.
2. On that transition, automatically invoke the same push/pull flow that
   the manual "Sync now" button on SyncStatusScreen currently triggers.
3. Debounce so a flapping connection doesn't trigger a sync storm.
4. Keep the manual button too (as a fallback / immediate trigger), just add
   the automatic path alongside it.
5. Surface sync status (in progress / success / failure) via the same UI
   state SyncStatusScreen already uses.
6. Add a test that simulates a connectivity transition and asserts the sync
   call fires exactly once (not on every intermediate connectivity event).
7. Run flutter analyze/test, commit, push, open PR.

Acceptance criteria:
- Going offline, creating a mutation, then reconnecting syncs without the
  user touching the Sync screen.
- No duplicate/duplicate-storm syncs on flaky connections.
```

---

## Track D — Infrastructure & Production Readiness (do last — depends on Tracks A–C being stable)

### Phase 9.10 — Bring up Keycloak with real realm config, remove mock JWT path from non-dev environments

**Severity**: High for production readiness
**Branch**: `fix/9.10-keycloak-oidc`

**PROMPT:**
```
Replace the mock JWT signature validation path with real Keycloak OIDC
validation, at least for a staging-equivalent environment.

Task:
1. Bring up the existing cinevault-local-keycloak container (docker-compose)
   and configure a realm/client for CineVault (users, curator role, token
   settings) — script this as a repeatable realm-export JSON checked into
   the repo (e.g. infra/keycloak/realm-export.json) rather than a one-off
   manual click-through, so it's reproducible.
2. Update services/api/auth/jwt_validator.py so that outside of an explicit
   TEST/DEV environment flag, JWT validation MUST use Keycloak's real JWKS
   endpoint — generate_mock_jwt and the mock RSA key path must be
   unreachable when ENVIRONMENT=staging|production.
3. Update client-side login (Phase 9.8) to redirect through Keycloak's OIDC
   flow when not in dev mode.
4. Add an integration test that boots against the real Keycloak container
   (via docker-compose in CI or a documented local-only test) and confirms
   a token issued by Keycloak validates, while a locally-forged mock token
   is rejected once ENVIRONMENT != dev.
5. Document the new required env vars (KEYCLOAK_ISSUER_URL, KEYCLOAK_
   CLIENT_ID, etc.) in `.env.example`.
6. Run pytest, commit, push, open PR.

Acceptance criteria:
- In dev mode, nothing breaks (mock path still available for fast local
  iteration).
- In staging/production mode, a forged/mock JWT is rejected; only tokens
  actually signed by the configured Keycloak realm are accepted.
```

---

### Phase 9.11 — Kong API Gateway wiring

**Severity**: Medium for production readiness
**Branch**: `fix/9.11-kong-gateway`

**PROMPT:**
```
Route traffic through the existing (currently stopped) cinevault-local-kong
container instead of hitting FastAPI on port 8000 directly.

Task:
1. Bring up the Kong container via docker-compose and configure routes/
   services pointing at the FastAPI backend, plus rate-limiting and (for a
   real deployment target) TLS termination — check in the Kong declarative
   config (kong.yml or equivalent) under infra/kong/.
2. Update client/lib/core/config/api_config.dart's base URL logic so the
   "production" build target points at the Kong-fronted URL/port, while
   local dev can still point straight at :8000 if desired.
3. Verify rate limiting actually kicks in (add a test/manual script that
   fires requests past the configured limit and expects a 429).
4. Run pytest/flutter test as relevant, commit, push, open PR.

Acceptance criteria:
- Requests through Kong reach FastAPI and get real responses.
- Exceeding the configured rate limit returns 429 via Kong, not a backend
  crash or silent pass-through.
```

---

### Phase 9.12 — CDN / object storage for poster & backdrop images

**Severity**: Medium for production readiness (depends on Phase 9.2's schema field existing)
**Branch**: `fix/9.12-cdn-object-storage`

**PROMPT:**
```
Stand up real object storage (S3-compatible — e.g. MinIO for local/dev
parity, S3/Cloudfront for actual production) to serve poster/backdrop
images referenced by the poster_url/backdrop_url field added in Phase 9.2.

Task:
1. Add a MinIO service to docker-compose for local dev (S3-compatible),
   matching how the other infra services are already defined.
2. Add an upload path (ingestion or a small admin script) that pushes
   artwork into the bucket and writes the resulting CDN URL into
   canonical.edition (or wherever the field lives).
3. Confirm Flutter's Image.network from Phase 9.2 works against the real
   CDN URLs (CORS, correct content-type, cache headers).
4. Document the production target (real S3 + Cloudfront) config separately
   from the local MinIO dev config — do not conflate the two in code, only
   in environment-specific config.
5. Run tests, commit, push, open PR.

Acceptance criteria:
- Poster/backdrop images actually load from object storage end-to-end in
  local dev via MinIO.
- Production config path is documented but does not require MinIO-specific
  code to run against real S3 (same client interface, different endpoint).
```

---

## GitHub Management Instructions (apply throughout)

Antigravity (or whichever agent executes a phase) should manage GitHub itself, not just local git:

1. **Before starting a phase**: `git checkout master && git pull origin master && git checkout -b fix/<phase-id>-<slug>`.
2. **While working**: commit in small logical chunks, not one giant commit at the end. Push the branch early (`git push -u origin fix/<phase-id>-<slug>`) so work is visible.
3. **Opening the PR**: use `gh pr create` with:
   - Title: `<phase-id>: <short title>` (e.g. `9.1: fix /v1/titles year/country param mismatch`)
   - Body: link back to this file's phase, restate the audit gap being closed, list test commands run and their pass/fail output, and call out any follow-up left for a later phase.
   - Labels (if the repo has label conventions; otherwise skip): `bug`, `backend`/`frontend`/`infra` as appropriate.
4. **CI**: if no GitHub Actions workflow exists yet, the first phase to touch `.github/workflows/` should add one running `pytest` and `flutter test`/`flutter analyze` on every PR — flag this explicitly if you add it, since it's infra shared across all phases.
5. **Review gate**: do not self-merge. If no other reviewer is available, at minimum re-run all test suites locally post-rebase-on-master before merging, and state that explicitly in a PR comment.
6. **Merging**: `gh pr merge --squash --delete-branch` once green. Never merge with failing tests, and never merge a PR whose description is missing the "Acceptance criteria" check-off.
7. **After all Track A–D phases merge**: tag the resulting `master` commit, e.g. `git tag -a v0.9.0-feature-complete -m "..." && git push origin v0.9.0-feature-complete`, and update this file's phases to `DONE` with the merge commit SHA next to each.

---

## Phase Status Tracker

| Phase | Title | Track | Status | Branch | PR |
|-------|-------|-------|--------|--------|----|
| 9.1 | API contract year/country fix | A | DONE | `fix/9.1-api-contract-year-country` | Commit `7d663c5` |
| 9.2 | Real poster/backdrop artwork | A | DONE | `fix/9.2-poster-artwork` | Commit `352ade1` |
| 9.4 | Live OpenAI provider | B | DONE | `fix/9.4-openai-live-provider` | Commit `587211b` |
| 9.5 | Live Gemini provider | B | DONE | `fix/9.5-gemini-live-provider` | Commit `8807367` |
| 9.6 | Live KOBIS + TVDB ingestion | B | DONE | `fix/9.6-ingestion-live-adapters` | Commit `933ec0e` |
| 9.7 | Control Room Flutter screen | C | DONE | `fix/9.7-control-room-screen` | Commit `cad90c1` |
| 9.8 | Login/auth screen | C | DONE | `fix/9.8-auth-login-screen` | Commit `22fa854` |
| 9.9 | Auto-sync on reconnect | C | DONE | `fix/9.9-auto-sync-reconnect` | Commit `99dc84e` |
| 9.10 | Keycloak OIDC live | D | DONE | `fix/9.10-keycloak-oidc` | Commit `af1813b` |
| 9.11 | Kong gateway wiring | D | DONE | `fix/9.11-kong-gateway` | Commit `9c0b765` |
| 9.12 | CDN/object storage for artwork | D | TODO | | |

Update this table as phases complete — that's the single source of truth for "what's actually fixed" going forward, so the next audit isn't starting from scratch.
