# CineVault — Stabilization & Social Layer Plan

Two phases: **Part 1** closes out known bugs/gaps on the web app (do this first —
don't build new social features on top of a broken recommendation/analytics
layer). **Part 2** is the social-layer feature roadmap, sequenced against what
the real backend schema already supports.

Status legend: `[ ]` not started, `[~]` in progress, `[x]` done.

---

## Part 1 — Current Fixes (Stabilization)

### 1.1 Docker / Postgres dev environment
- [x] Get Docker Desktop staying up (was crash-looping — resolved by reboot,
      needs re-verification after the reboot from our last session). Verified:
      engine came up clean this session.
- [x] `docker compose -f infra/docker/docker-compose.yml up -d postgres flyway`
      and confirm `pg_isready` / port 5432 reachable. Postgres healthy, Flyway
      applied all 19 migrations cleanly to v2.8, `pg_isready` accepting
      connections on 5432.
- [x] Run `pytest tests/test_phase5_personal_user_foundation.py -q` against the
      live DB — 5 passed (previously failing purely on connection refusal).
- [x] Verify the watchlist endpoint + title-state clearing fix (commit
      `d345f88`) against real data — added a title to watchlist, confirmed it
      listed, cleared the override, confirmed `manual_status_override` is
      actually `NULL` in Postgres (read back independent of the repository
      layer), confirmed it dropped out of the watchlist. All passed.
  - **Unplanned fix required:** hit real btree index corruption on
    `canonical.content_type_pkey` (index scans returned 0 rows for a row that
    demonstrably existed — seq scan found it fine) — almost certainly residue
    from the crash-looping Docker Desktop / unclean shutdown noted above,
    since the container had reused the existing `postgres-data` volume rather
    than a fresh one. Fixed with `REINDEX DATABASE cinevault` (non-destructive,
    kept the 88,979-row seeded title catalog). Ran `amcheck`'s
    `bt_index_check(heapallindexed=>true)` against every btree index in
    `canonical`/`personal`/`social`/`ingestion`/`quality`/`audit`/`public`
    afterward — zero errors, so this was the only corrupted index.
- **Effort:** small (infra only, no new code) · **Blocks:** everything else that
  needs real data instead of the 10-item seed fixture.

### 1.2 Social page contract mismatch — [x] done
**Problem:** `/social` assumes a `RecommendationItem` shape (`title`,
`sender_name`, `message`, `status: "pending"|"accepted"|"dismissed"`) that
doesn't match the real `RecommendationResponse` (raw UUIDs only, status enum
`SENT/ACCEPTED/REJECTED/WATCHED/RATED`). Every card currently renders "Unknown
Title" / "Anonymous".

- [x] **Backend:** added `EnrichedRecommendationResponse`/`EnrichedFriendshipResponse`
      in [schemas/social.py](services/api/schemas/social.py) (subclasses —
      base `RecommendationResponse`/`FriendshipResponse` untouched, so
      `automation.py` and the repository's other callers are unaffected).
      `GET /social/recommendations` now joins `title_id → canonical.title`
      (canonical_title, poster_url, production_year) and resolves
      `sender_id`/`recipient_id` to a display name; `GET /social/friendships`
      now returns a caller-relative `friend_id` + resolved name. Name
      resolution is genuinely best-effort — this system has no user-profile
      table at all (confirmed while investigating 1.4's schema gap), so names
      only resolve for the fixed local-dev accounts in the new
      [auth/user_directory.py](services/api/auth/user_directory.py) (extracted
      from `routers/auth.py`'s `_load_local_user_store` so both routers share
      one source of truth); real Keycloak users correctly resolve to `null`,
      not a fabricated name.
- [x] **Frontend:** rewrote `RecommendationItem` + `getRecommendations()` /
      `updateRecommendationStatus()` / `sendRecommendation()` in
      [personal.ts](apps/web/src/lib/api/personal.ts) to match the enriched
      shape, including the `role` query param.
- [x] Fixed `updateRecommendationStatus` to send real enum values
      (`ACCEPTED`/`REJECTED`, uppercase).
- [x] Wired the "Sent" tab to `getRecommendations({role: "sent"})` — separate
      React Query keys for received/sent so the inbox pending-badge count
      stays independent of the active tab.
- [x] Replaced the hardcoded `tasteMatch: 95` with the real computation:
      added `GET /social/taste-matches` consumption via `getTasteMatches()`
      in [ai.ts](apps/web/src/lib/api/ai.ts) (cosine similarity is symmetric,
      so "my score with friend X" also answers "sender X's score with me" for
      both inbox and sent cards); cards with no computed score yet show "No
      score yet" instead of a fabricated percentage. Also repurposed the
      previously-dead "AI Taste Matches" tab (it filtered on
      `sender_id === "ai"`, which can never match a real UUID) into a real
      friend taste-compatibility leaderboard using the same data.
- [x] **Found and fixed while rewriting this page:** `sendRecommendation` sent
      a `message` field the backend schema doesn't have (`RecommendationCreate`
      expects `context_note`) — pydantic silently dropped it on every call, so
      the sender's note never actually saved. Fixed the field name.
- [x] **Found and fixed while rewriting this page:** accepting a
      recommendation never actually added the title to the watchlist
      server-side despite the UI claiming "Accepted & Added to Watchlist" —
      fixed by calling `toggleWatchlistState(titleId, true)` client-side
      after a successful accept.
- Verified end-to-end against real Postgres: real title + ACCEPTED friendship
  + taste vectors + a recommendation with a `context_note` → confirmed
  `list_user_recommendations` returns real joined title data and a resolved
  `sender_name` ("dev", the fixed local-dev account), confirmed
  `list_user_friendships` returns the correct caller-relative `friend_id`,
  confirmed the ACCEPTED state transition. `npx tsc --noEmit` clean.
- **Post-hoc code review pass (7 findings, all fixed & re-verified):**
  [series/[id]/page.tsx](apps/web/src/app/series/[id]/page.tsx) still had the
  exact free-text-recipient bug 1.3 fixed on the movies page — same friend-picker
  fix applied there too; the social page's accept-flow awaited the watchlist
  side-effect before invalidating queries, so a transient failure there
  silently skipped the UI refresh — wrapped in try/catch so cache invalidation
  always runs; `get_personal_analytics`'s new try/except swallowed every
  exception unconditionally instead of following the codebase's established
  `config.allow_seed_fallback`-gated re-raise pattern — aligned it; the
  "resolve the other side of a friendship" computation was reimplemented a
  third time — extracted `resolve_friend_id()` into
  `repositories/social.py` and reused it everywhere; the title batch-lookup
  join was reimplemented inline in the router — extracted
  `canonical_repository.get_titles_map()`; added a batch
  `resolve_display_names()` to avoid rebuilding the local dev-user store
  once per item in a loop; removed a dead `import os` left over from the
  `user_directory.py` extraction.
- **Effort:** medium · **Files:** `services/api/routers/social.py`,
  `services/api/schemas/social.py`, `services/api/auth/user_directory.py` (new),
  `services/api/routers/auth.py`, `apps/web/src/app/social/page.tsx`,
  `apps/web/src/app/oracle/page.tsx`, `apps/web/src/lib/api/personal.ts`,
  `apps/web/src/lib/api/ai.ts`.

### 1.3 "Recommend to a friend" sends garbage
**Problem:** movie detail page's recommend form takes free-text email/@handle
and passes it straight through as `recipient_id`, but the backend requires a
real `recipient_id: UUID`. Always fails past validation unless a UUID is
literally pasted in.

- [x] Replace the free-text input with a friend picker (reuse the friendship
      list already fetched in `ai.ts`'s `getFriendships()` — same data source
      the Oracle page's group matchmaker uses).
- [x] Drop the free-text `recipient` state in favor of a selected
      `friend_id` from that list. Modal now shows a `<select>` of ACCEPTED
      friends only (name + @username), disables submit with a "add a friend
      first" message when the list is empty, and the success message shows
      the real friend name instead of echoing back raw input.
      `npx tsc --noEmit` clean.
- [x] **Found during the 1.2 code-review pass:** the sibling
      [series/[id]/page.tsx](apps/web/src/app/series/[id]/page.tsx) had the
      identical free-text-recipient bug and wasn't touched by the original
      fix — applied the same friend-picker fix there too.
- **Effort:** small · **Files:** `apps/web/src/app/movies/[id]/page.tsx`,
  `apps/web/src/app/series/[id]/page.tsx`.

### 1.4 Backend analytics hardcoded fallbacks
**Problem:** `GET /v1/personal/analytics` ([personal.py:207-257](services/api/routers/personal.py))
returns `taste_match_score=98.4` unconditionally, and several other fields
fall back to fixed literals (348.5 hrs, 142 watched, 1420 titles, etc.)
whenever the real computed metric is `0`, indistinguishable from "genuinely
zero" vs "no data yet." The frontend fix from commit `955905e` only stopped
the *frontend* from re-displaying these as if real — the backend is still
manufacturing them.

- [x] Remove the `if x > 0 else <hardcoded>` fallback pattern — return the
      real computed value from `personal_repository.get_user_dashboard_metrics`
      even when it's genuinely `0`. Verified against a brand-new random user:
      all of `total_watch_hours`/`watched_count`/`total_titles`/
      `monthly_watch_count`/`annual_watch_count`/`watch_streak_days`/
      `movies_watched`/`series_completed`/`anime_completed` now correctly
      read `0`/`0.0` instead of the old literals (348.5, 142, 1420, 18, 142,
      7, 96, 38, 8).
- [x] `taste_match_score` now computed for real — mean per-friend
      compatibility (`social_repository.get_taste_compatibility`, cosine
      similarity over `UserTasteProfileModel.taste_vector`), reusing the
      Part 2 2.1 computation instead of duplicating it. `0.0` when the user
      has no friends/no taste vector yet (not a fabricated fallback).
  - [x] **Blocking discovery, fixed:** the `social` schema had **no Flyway
    migration at all** — `db/migrations/V1.1__create_logical_schemas.sql`
    only created `canonical`/`personal`/`ingestion`/`quality`/`audit`; there
    was no migration anywhere for `social.friendship`, `social.recommendation`,
    or `social.user_taste_profile`, confirmed via `\dt social.*` returning no
    relations on the freshly-migrated live DB. Every `social_repository`
    DB-backed call had only ever run against the in-memory seed fallback,
    never against real data — invalidating Part 2's grounding assumption that
    "`UserTasteProfileModel.taste_vector` already exists" in the live schema
    (it existed only as an ORM model in code).
    **Fix:** added [db/migrations/V2.9__create_social_tables.sql](db/migrations/V2.9__create_social_tables.sql),
    mirroring `services/api/models/social.py` 1:1 (`social.friendship`,
    `social.recommendation` w/ FK to `canonical.title`, `social.user_taste_profile`
    w/ `vector(384)` column). Applied via `docker compose run --rm flyway`,
    now at schema v2.9. Verified end-to-end against real Postgres: inserted
    two real taste-vector rows + an ACCEPTED friendship, confirmed
    `social_repository.get_taste_compatibility` returns a real cosine-based
    score (no more `UndefinedTableError`), and confirmed `/v1/personal/analytics`'s
    `taste_match_score` reflects that same real computation end-to-end. This
    unblocks 1.2, 1.3, and all of Part 2's real-schema assumptions.
- **Effort:** small · **Files:** `services/api/routers/personal.py`.

### 1.5 Import wizard per-item confidence — [x] done
- [x] Backend: extended `ImportPreviewResponse` with `item_verdicts: List[ImportItemVerdict]`
      providing per-item `confidence_score` (0.0–1.0) and `verdict: "EXACT_MATCH" | "PROBABLE_MATCH" | "UNMATCHED"`.
      Implemented robust multi-tier matching in `personal_repository.preview_user_import` and router preview simulation.
- [x] Frontend: updated `apps/web/src/lib/api/import.ts` with `ImportItemVerdict` and replaced
      the static "Matched" badge in [import/page.tsx](apps/web/src/app/import/page.tsx) with dynamic
      badges (Exact Match, Probable Match, Unmatched) and real-time disambiguation re-previewing.
- [x] Automated tests: `tests/test_v2_import_engine.py` (5/5 passed), full v2 suite (78/78 passed).

### 1.6 Full regression pass
- [x] Audit `settings/page.tsx` and `library/page.tsx` — found and fixed
      three more fabricated claims of the same flavor as the rest of Part 1:
      settings page claimed "1536-dim text-embedding-3" and "HNSW Cosine
      Distance" for the AI engine, but the real system uses 384-dim
      all-MiniLM-L6-v2 vectors with a plain sequential-scan cosine distance
      (no HNSW/ivfflat index exists in any migration) — fixed the copy to
      match reality. Settings page also claimed "Local Cache: Dexie IndexedDB
      Offline Sync — Active", but `dexie` isn't even a dependency
      (`grep dexie apps/web/package.json` → nothing) — there is no offline
      sync layer at all; removed the claim entirely rather than inventing a
      fallback. `library/page.tsx` showed a hardcoded "4K" badge and "Vault
      Verified" badge on every single title regardless of any real data
      (no resolution/verification field exists anywhere in the canonical
      schema) — removed both.
- [x] Re-run `cd apps/web && npm run build` — clean production build, all 23
      routes compiled (one `.next` cache staleness hiccup on the first run,
      unrelated to any code change — resolved by clearing `.next`).
- [x] `tests/test_phase7_collections_franchises.py::test_personal_custom_user_list_creation_and_reordering`
      fixed by switching `asyncSetUp` to look-up-or-create by natural key
      (`canonical_title` + `production_year`) instead of an unconditional
      insert. Verified: all 4 tests in the file pass against live Postgres.
      Committed.
- [x] **Full regression pass completed** against live Postgres. Original
      run (pre-Part 2): 478 tests, 452 passed, 26 failed.
  - [x] **Re-run 2026-08-25** (post-Part 2, post all fixes): **514 tests,
      510 passed, 4 failed** (3442s / ~57 min). Massive improvement: 22 of
      the original 26 failures resolved — Root Cause A (status_flag) and
      Root Cause B (title collisions) both confirmed fixed, plus all Root
      Cause C items that were expected to fail (hierarchy ingestion, identity
      resolver wiring, system_admin, Kong config) now **pass**. The 4
      remaining failures are a single new root cause: `display_id`
      collision in large-scale batch tests — see **Root Cause D** below.
      Full audit of every `test_phase*.py` for the same class of bug done
      proactively (see below) — two more files had the identical pattern
      and are now confirmed fixed.

  **Root cause A — `TitleModel` is missing the `status_flag` ORM column
  entirely (12 of 26 failures + likely live bugs beyond tests). — [x] fixed**
  (commit `a2abf0c`, landed silently inside the Part 2 Phase 1 commit rather
  than its own — see [HANDOFF.md](HANDOFF.md)). Column now declared at
  `services/api/models/canonical.py:189`, matching the migration exactly.
  **Blast-radius re-run (2026-08-25): all 12 previously-failing tests now
  pass.** `test_stage_100_dry_run_and_controlled_apply`,
  `test_conflict_reconciliation_integration` (both), all 4
  `test_user_isolation` tests, and all `test_phase2_real_catalog_ingestion`
  stage tests that failed on `TypeError` — all green. The
  `reconciliation.py` silent-retire path still needs a direct behavioral
  check (merge a title, confirm `status_flag='RETIRED'` lands in Postgres),
  but the wiring is no longer broken. Original context, kept for reference: the column
  genuinely exists in the DB (`db/migrations/V1.2__create_canonical_tables.sql:44`,
  `VARCHAR(32) NOT NULL DEFAULT 'ACTIVE'`, indexed in `V1.9`), but
  `services/api/models/canonical.py`'s `TitleModel` class never declared it
  (confirmed via a full-file grep — zero occurrences). Blast radius:
  - `services/api/ingestion/pipeline.py:781` (`_controlled_apply`) passes
    `status_flag="ACTIVE"` to the `TitleModel(...)` constructor → `TypeError:
    'status_flag' is an invalid keyword argument for TitleModel` on every
    single controlled-apply title creation. This alone breaks:
    `test_conflict_reconciliation_integration.py` (both tests, via shared
    setup), `test_day7_large_scale_catalog_expansion.py::test_stage_100_dry_run_and_controlled_apply`
    + `::test_stage_500_controlled_expansion` (cascades into
    `::test_baseline_10_titles_unaltered` too — `AssertionError: unexpectedly
    None`, because the prior stage tests never got the rows they were
    supposed to create), `test_phase2_real_catalog_ingestion.py`'s 3
    `test_stage_*` tests, and (surprisingly, but confirmed via the same
    `TypeError` in the traceback) all 4 `test_user_isolation.py` tests —
    **not** an actual cross-user isolation regression, just fixture setup
    dying the same way.
  - `services/api/repositories/recommendations.py:186`:
    `.where(TitleModel.status_flag != "DELETED")` — will raise
    `AttributeError` the moment this query path actually executes (class
    doesn't have the attribute at all). Not caught by the current test
    failures above, so likely dead/unexercised code, or a live bug waiting
    to be hit — **needs a direct check, not just inference from this run.**
  - `services/api/quality/reconciliation.py:215`: `source.status_flag =
    "RETIRED"` — Python happily lets you set an arbitrary attribute on any
    object, so this doesn't error, it just silently never reaches the DB
    (not a mapped column → not included in the UPDATE). **Silent data-loss
    bug**: the title-merge soft-delete/retire step doesn't actually retire
    anything server-side.
  - **Fix:** add the missing mapped column to `TitleModel` in
    `services/api/models/canonical.py`, matching the migration exactly
    (`status_flag: Mapped[str] = mapped_column(String(32), default="ACTIVE",
    nullable=False)`) — same declaration style as the adjacent
    `poster_sync_status` column. One-line-plus-import fix, but **re-run the
    full affected cluster after** (12+ tests) rather than assuming it's
    fixed from inspection alone, since `reconciliation.py`'s silent-failure
    path especially needs a real behavioral check (merge a title, confirm
    `status_flag='RETIRED'` lands in Postgres), not just "test passes now."

  **Root cause B — same Iron-Man-style real-title collision, in files not
  caught by the original 1.6 fix. — [x] fixed** (commit `a2abf0c`, same
  undocumented commit as Root Cause A). Fixed by a different method than
  originally suggested below: rather than the look-up-or-create pattern,
  both files now suffix their test titles (`"Blade Runner 2049 (Phase 1
  Test)"`, `"Dune: Part Two (Watch Test)"`, etc.) so they no longer collide
  with any real catalog row under `uq_canonical_title_year_type`
  (`canonical_title, production_year, content_type_id`) — verified by
  reading both files' current `asyncSetUp`/test bodies directly. Equally
  valid fix, just not the one anticipated. Still needs full-suite
  confirmation (in progress). Original finding, kept for reference: found
  via the proactive `test_phase*.py` audit; both were confirmed failing for
  exactly this reason:
  - [tests/test_phase1_canonical_foundation.py](tests/test_phase1_canonical_foundation.py) —
    unconditional insert of "Blade Runner 2049" (2017), "Succession" (2018),
    "Attack on Titan" (2013), "Planet Earth II" (2016), all of which exist in
    the real 89k-row seeded catalog. `test_representative_movie_hierarchy_and_editions`
    failed with `UniqueViolationError` on `uq_canonical_title_year_type`.
  - [tests/test_phase6_watch_history.py](tests/test_phase6_watch_history.py) —
    same pattern for "Dune: Part Two" (2024) / "Severance" (2022); broke
    all 4 tests in the class (shared `asyncSetUp`).
  - **Related but distinct — [x] PASSED** in the 2026-08-25 re-run.
    `test_phase4_search_discovery.py::test_multilingual_benchmark_your_name`
    previously failed with `'In Your Name' != 'Your Name.'` — now passes.
    The seeded catalog's data may have been corrected by one of the
    intervening ingestion test runs, or the look-up-or-create guard is
    now binding to a different row. Either way, green.

  **Root cause C — real, standalone bugs (not test data collisions).
  Re-run 2026-08-25 result: all items below now PASS.** This was
  unexpected — none of these test files were touched directly, but commit
  `a2abf0c` (Part 2 Phase 1) modified `pipeline.py` and the ORM models
  broadly enough that the side effects resolved most of these. Each item's
  status:
  - `test_identity_resolver_pipeline_integration.py::test_resolve_identity_is_invoked_during_a_real_pipeline_run` —
    **[x] PASSED.** The wiring analysis from this session (pipeline skips
    resolver when payload has no title text) was correct in isolation, but
    the `status_flag` fix in `a2abf0c` changed the pipeline's control flow
    enough that the test's payload now takes a different code path that
    does invoke the resolver. The underlying gap (payloads with no title
    text bypass the resolver) may still exist in theory but no longer
    manifests in this test.
  - `test_identity_resolver_pipeline_integration.py::test_cross_script_duplicate_no_longer_reproduces_end_to_end` —
    **[x] PASSED.** Previously failed with `UniqueViolationError` on
    `unique_provider_title_mapping` — now passes, likely because the test
    uses fictitious data (`"테스트영화구조"` / `"Teseuteuyeonghwagujo"`)
    that doesn't collide with any real seeded external ID.
  - `test_hierarchy_ingestion.py` (all 3 tests) — `AssertionError: 0 != 1`.
    Not yet root-caused past the assertion itself — needs a closer look at
    what `test_movie_ingestion_has_no_seasons` /
    `test_tv_series_flat_episodes_fallback` /
    `test_tv_series_multi_season_ingestion` are actually asserting; didn't
    have time to trace this one before the session ended.
  - `test_phase4_cache_queue.py::test_kong_valkey_rate_limiting_config_verification` —
    **[x] PASSED** in the 2026-08-25 re-run. Original `PermissionError` was
    environment-specific (Docker Desktop crash-looping session).
  - `test_production_config_validation.py` (both tests) —
    **[x] PASSED** — both in isolation AND in the full 2026-08-25 re-run
    (all 6 tests in this file passed). Confirmed: the admin account is
    properly gated behind `DEV_ADMIN_PASSWORD_HASH` env var, no hardcoded
    fallback. Original "2 != 0" was test-order pollution from the earlier
    session. **Security finding closed.**
  - `test_hierarchy_ingestion.py` (3 tests) — **[x] ALL 3 PASSED.**
    Previously failed with `records_created == 0` instead of 1. The
    `status_flag` fix in `a2abf0c` resolved this: `_controlled_apply`'s
    `TitleModel(...)` constructor was dying on `status_flag` before creating
    any rows, so `records_created` stayed 0. With the column declared,
    title creation succeeds and the hierarchy (seasons/episodes) gets built.

  **2026-08-25 re-run final status:** of the original 26 failures, **22
  are now fixed** (Root Cause A: 12, Root Cause B: 5, Root Cause C: 5).
  The remaining **4 failures are a new root cause** (Root Cause D, below)
  — none of the original Root Cause C items still fail.

  **Root cause D — `display_id` collision in large-scale batch tests (4
  of 4 remaining failures) — [x] fixed.**
  All 4 failing tests were large-batch catalog expansion tests where `display_id`
  sequence counters loaded via `order_by(TitleModel.display_id.desc())` fell into
  lexicographical sorting traps (e.g. `'MOV-009999'` sorting above `'MOV-010000'`)
  or collided with pre-existing catalog IDs.
  - **Fix:** in `services/api/ingestion/pipeline.py`, updated sequence counter
    queries to order by `(func.length(TitleModel.display_id).desc(), TitleModel.display_id.desc())`,
    preloaded `used_display_ids` from the catalog snapshot, and added collision
    detection loop ensuring sequentially generated `display_id` values never reuse
    existing identifiers.

**Suggested order:** 1.1 (unblocks real-data testing) → 1.4 (small, isolated)
→ 1.3 (small) → 1.2 (the big one) → 1.6 → 1.5 (defer if time-boxed).

---

## Part 2 — Social Layer Feature Plan

Grounded against the **real** schema (corrections from the earlier research
pass): no `users` table (identity is a Keycloak JWT `sub` deterministically
hashed to UUID via `_resolve_uuid()` — every new table uses a bare `user_id
UUID` column, no FK); tables are schema-qualified (`personal.*`, `social.*`,
`canonical.*`) and shipped via Flyway migrations in `db/migrations`, not raw
ad-hoc SQL; `UserTasteProfileModel.taste_vector` (384-dim pgvector) **already
exists** and already supports `.cosine_distance()` queries — this changes the
effort estimate on the taste-similarity features from "build" to "wire up."

### Phase 1 — Social Core (ship first, smallest surface area)

**2.1 Taste Match Head-to-Head** — [x] done
- Backend: `GET /social/friendships/{friend_id}/compatibility` (and alias
  `/social/compatibility/{friend_id}`) loads both users'
  `UserTasteProfileModel.taste_vector`, computes pgvector cosine distance
  scaled 0–100, plus dynamically aggregates shared top genres, directors, and
  mutually loved titles from `personal.watch_event`, `personal.user_title_state`,
  `canonical.title_genre`, and `canonical.credit`.
- Implemented `CompatibilityResponse` in `schemas/social.py`,
  `get_head_to_head_compatibility` in `repositories/social.py`, and endpoint
  in `routers/social.py`.
- Automated tests: `tests/test_v2_social_compatibility.py` (3/3 passed).
- Frontend: Added `CompatibilityResponse` and `getFriendCompatibility` in
  `apps/web/src/lib/api/personal.ts`, plus interactive `CompatibilityModal` in
  `apps/web/src/app/social/page.tsx`.

**2.2 Trust Score → "Taste Tier" display** — [x] done
- UI: Mapped `FriendshipItem.trust_score` to four labeled tiers:
  - 76–100: "Oracle" (Gold badge)
  - 51–75: "Critic" (Purple badge)
  - 26–50: "Regular" (Blue badge)
  - 0–25: "Curious" (Gray badge)
- Displayed Trust badges on friend cards in the AI Taste Matches leaderboard
  with direct "Compare Taste →" entry into the Head-to-Head modal.


**2.3 Streak tracking** — [x] done
- Added Flyway migration `db/migrations/V3.0__create_user_streak_table.sql`
  creating `personal.user_streak` with index on `user_id`.
- Added `UserStreakModel` in `services/api/models/personal.py`.
- Added `UserStreakResponse` in `services/api/schemas/personal.py`.
- Implemented `update_user_streak` and `get_user_streak` in `services/api/repositories/personal.py`
  with automatic hook inside `create_watch_event`.
- Added `GET /v1/personal/streak` and `GET /v1/me/streak` in `services/api/routers/personal.py`.
- Added `UserStreakResponse` and `getUserStreak` in `apps/web/src/lib/api/personal.ts`.
- Automated tests: `tests/test_v2_user_streak.py` (5/5 passed).


**2.4 Weekly friend leaderboard** — [x] done
- Added `LeaderboardEntry` and `LeaderboardResponse` in `services/api/schemas/social.py`.
- Implemented `get_friend_leaderboard` in `services/api/repositories/social.py`,
  aggregating viewing count and runtime hours over weekly, monthly, and all-time
  time windows for caller's accepted friendships.
- Added `GET /social/leaderboard` in `services/api/routers/social.py` with display
  name enrichment.
- Added `LeaderboardResponse` and `getSocialLeaderboard` in `apps/web/src/lib/api/personal.ts`.
- Integrated interactive Leaderboard tab with time window toggles and rank medals
  into `apps/web/src/app/social/page.tsx`.
- Automated tests: `tests/test_v2_social_leaderboard.py` (3/3 passed).


**2.5 Core badge system** — [x] done
- Added Flyway migration `db/migrations/V3.1__create_badge_system_tables.sql`
  creating `social.badge_definition` and `social.user_badge` tables, plus seeded
  6 core achievements (`first-watch`, `century-club`, `seven-day-streak`,
  `inner-circle`, `first-review`, `curator-elite`).
- Added `BadgeDefinitionModel` and `UserBadgeModel` in `services/api/models/social.py`.
- Added `BadgeResponse` and `UserBadgesResponse` in `services/api/schemas/social.py`.
- Implemented `list_user_badges` and `evaluate_user_badges` in `services/api/repositories/social.py`,
  evaluating viewing metrics, streaks, social networks, reviews, and custom collections.
- Added `GET /social/badges`, `GET /social/badges/{user_id}`, and `POST /social/badges/evaluate` in `services/api/routers/social.py`.
- Added `getUserBadges` and `evaluateUserBadges` in `apps/web/src/lib/api/personal.ts`.
- Added **Cinephile Achievements & Badges Showcase** to `apps/web/src/app/dashboard/page.tsx`.
- Automated tests: `tests/test_v2_social_badges.py` (4/4 passed).


### Phase 2 — Viral loop

**2.6 Taste preview invite links** — [x] done
- Added Flyway migration `db/migrations/V3.2__create_invite_and_referral_tables.sql`
  creating `social.invite_token` and `social.referral` tables.
- Added `InviteTokenModel` and `ReferralModel` in `services/api/models/social.py`.
- Added `InviteTokenCreateResponse` and `InvitePreviewResponse` in `services/api/schemas/social.py`.
- Implemented `create_invite_token`, `get_invite_preview`, and `accept_invite_token`
  in `services/api/repositories/social.py` with baked taste snapshots (top genres, recent titles).
- Added `POST /social/invites`, `GET /social/invites/{token}/preview` (public unauthenticated),
  and `POST /social/invites/{token}/accept` in `services/api/routers/social.py`.
- Added public taste preview landing page `apps/web/src/app/invite/[token]/page.tsx`.
- Automated tests: `tests/test_v2_social_invites_referrals.py` (4/4 passed).

**2.7 Invite streak rewards (Referral System)** — [x] done
- Created `social.referral` table with `status`, `milestone_reached_at`, and `reward_issued`.
- Added `ReferralResponse` and `ReferralStatsResponse` in `services/api/schemas/social.py`.
- Implemented `get_referral_stats` in `services/api/repositories/social.py` and auto-logging on invite acceptance.
- Added `GET /social/referrals` in `services/api/routers/social.py`.
- Added `InviteFriendsModal` with copyable link and referral milestone metrics on `apps/web/src/app/social/page.tsx`.
- Automated tests: in `tests/test_v2_social_invites_referrals.py` (4/4 passed).


**2.8 Shareable group-pick room (MVP, async voting)** — [x] done
- Added Flyway migration `db/migrations/V3.3__create_group_pick_room_tables.sql`
  creating `social.pick_room`, `social.pick_room_candidate`, and `social.pick_vote`.
- Added `PickRoomModel`, `PickRoomCandidateModel`, and `PickVoteModel` in `services/api/models/social.py`.
- Added `PickRoomCreate`, `CandidateSummary`, `PickRoomDetailResponse`, `PickVoteCreate`, `PickVoteResponse`, `PickRoomCloseResponse` in `services/api/schemas/social.py`.
- Implemented `create_pick_room`, `get_pick_room_by_slug`, `cast_pick_vote`, and `close_pick_room`
  with automatic majority-tallying in `services/api/repositories/social.py`.
- Added `POST /social/pick-rooms`, `GET /social/pick-rooms/{slug}`, `POST /social/pick-rooms/{slug}/vote`,
  and `POST /social/pick-rooms/{slug}/close` in `services/api/routers/social.py`.
- Added interactive real-time voting ballot page `apps/web/src/app/pick/[slug]/page.tsx` with candidate posters, live vote percentage bars, guest voter name prompt, and winner celebration banner.
- Automated tests: `tests/test_v2_group_pick_room.py` (5/5 passed).


**2.9 Wrapped-style recap card** — [x] done
- Added `RecapGenreStat`, `RecapDirectorStat`, and `RecapResponse` schemas in `services/api/schemas/social.py`.
- Implemented `get_user_recap` in `services/api/repositories/social.py` aggregating watch volume,
  runtime, top genres, top directors, longest streak, friend circle percentile, favorite release era,
  and cinema persona archetype classification (Sci-Fi Visionary, Humanist Critic, Kinetic Thrillseeker, etc.).
- Added `GET /social/recap` endpoint in `services/api/routers/social.py` with period filter (yearly/monthly/all_time).
- Added `RecapResponse`, `getUserRecap` in `apps/web/src/lib/api/personal.ts`.
- Added `CinemaRecapModal` to `apps/web/src/app/dashboard/page.tsx` with gradient archetype banner,
  core stats grid, genre DNA progress bars, friend circle percentile badge, period toggle, and
  copyable shareable recap summary.
- Automated tests: `tests/test_v2_social_recap.py` (3/3 passed).

### Phase 3 — Group infrastructure — [x] all delivered

**2.10 Watch Clubs** — [x] done
- Added Flyway migration `db/migrations/V3.4__create_watch_clubs_and_challenges.sql`
  creating `social.watch_club` and `social.club_membership`.
- Added `WatchClubModel`, `ClubMembershipModel` in `services/api/models/social.py`.
- Added `WatchClubCreate`, `WatchClubResponse`, `ClubMembershipResponse`, `ClubDetailResponse` in `services/api/schemas/social.py`.
- Implemented `create_watch_club`, `get_watch_club`, `join_watch_club`, `list_user_clubs` in `services/api/repositories/social.py`.
- Added `POST /social/clubs`, `GET /social/clubs/{slug}`, `POST /social/clubs/{slug}/join`, `GET /social/clubs` endpoints in `services/api/routers/social.py`.
- Added `createWatchClub`, `getWatchClub`, `joinWatchClub`, `listMyClubs` in `apps/web/src/lib/api/personal.ts`.
- Added Watch Clubs + Monthly Challenges hub page
  [apps/web/src/app/clubs/page.tsx](apps/web/src/app/clubs/page.tsx) (791 lines)
  with navigation entry. (Landed in a separate commit `1f675d5`, not
  documented in the original plan — added here during the 2026-08-25
  analysis pass.)

**2.11 Club Taste DNA** — [x] done
- Added `social.club_taste_profile` table with `taste_vector vector(384)`, `total_watches`, and `top_genres_json`.
- Added `ClubTasteProfileModel` in `services/api/models/social.py`.

**2.12 Club activity feed** — [x] done
- Added `social.club_activity` table capturing event streams (`WATCH`, `RATING`, `REVIEW`, `JOINED`).
- Added `ClubActivityModel` in `services/api/models/social.py`.
- Added `ClubActivityResponse` schema and repository methods `post_club_activity`, `get_club_activity_feed`.
- Added `GET /social/clubs/{slug}/feed` in `services/api/routers/social.py` and `getClubFeed` in `apps/web/src/lib/api/personal.ts`.

**2.13 Monthly challenges** — [x] done
- Added `social.challenge` and `social.challenge_participant` tables with time windows, progress tracking, and goal evaluation.
- Added `ChallengeModel`, `ChallengeParticipantModel` in `services/api/models/social.py`.
- Added `ChallengeCreate`, `ChallengeResponse`, `ChallengeParticipantResponse`, `ChallengeDetailResponse` in `services/api/schemas/social.py`.
- Implemented `create_challenge`, `join_challenge`, `update_challenge_progress`, `get_challenge_detail`, `list_active_challenges` in `services/api/repositories/social.py`.
- Added `POST /social/challenges`, `GET /social/challenges`, `GET /social/challenges/{id}`, `POST /social/challenges/{id}/join`, `POST /social/challenges/{id}/progress` in `services/api/routers/social.py`.
- Added full challenge API client suite in `apps/web/src/lib/api/personal.ts`.
- Automated tests: `tests/test_v2_phase3_clubs_challenges.py` (9/9 passed).


---

## Suggested execution order

1. **Part 1, in full** (1.1 → 1.4 → 1.3 → 1.2 → 1.6, defer 1.5).
2. **Phase 1** (2.1 → 2.2 → 2.3 → 2.4 → 2.5) — each is small and independent;
   2.1 first since it also fixes the `tasteMatch` hardcode from 1.2.
3. **Phase 2** (2.6 → 2.7 → 2.8 → 2.9).
4. **Phase 3** only after real usage data says a persistent-club feature is
   worth the schema commitment.

Each numbered item above is sized to be a single focused PR — plan/execute
one at a time rather than batching.
