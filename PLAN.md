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

### 1.5 Import wizard per-item confidence
- [ ] Backend: extend `ImportPreviewResponse` to include a per-item match
      verdict/confidence (currently only aggregate counts + a conflicts list).
- [ ] Frontend: replace the always-"Matched" badge in
      [import/page.tsx](apps/web/src/app/import/page.tsx) with the real
      per-item value.
- **Effort:** medium (schema change) · **Priority:** low — defer past 1.1–1.4.

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
- [x] **Full regression pass completed** against live Postgres (478 tests,
      3650s / ~61 min — `python -m pytest tests/ -v --tb=short`, unbuffered
      + live-streamed after an earlier piped/buffered attempt gave zero
      visibility into progress): **452 passed, 26 failed.** None of the 26
      are flaky/infra-timing issues — every one has a concrete, reproducible
      root cause, grouped below. **Full audit of every `test_phase*.py` for
      the same class of bug done proactively** (see below) — two more files
      had the identical pattern and are now confirmed failing for exactly
      that reason.

  **Root cause A — `TitleModel` is missing the `status_flag` ORM column
  entirely (12 of 26 failures + likely live bugs beyond tests).** The
  column genuinely exists in the DB (`db/migrations/V1.2__create_canonical_tables.sql:44`,
  `VARCHAR(32) NOT NULL DEFAULT 'ACTIVE'`, indexed in `V1.9`), but
  `services/api/models/canonical.py`'s `TitleModel` class never declares it
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
  caught by the original 1.6 fix.** Found via the proactive `test_phase*.py`
  audit; both are now confirmed failing for exactly this reason:
  - [tests/test_phase1_canonical_foundation.py](tests/test_phase1_canonical_foundation.py) —
    unconditional insert of "Blade Runner 2049" (2017), "Succession" (2018),
    "Attack on Titan" (2013), "Planet Earth II" (2016), all of which exist in
    the real 89k-row seeded catalog. `test_representative_movie_hierarchy_and_editions`
    fails with `UniqueViolationError` on `uq_canonical_title_year_type`.
  - [tests/test_phase6_watch_history.py](tests/test_phase6_watch_history.py) —
    same pattern for "Dune: Part Two" (2024) / "Severance" (2022); breaks
    all 4 tests in the class (shared `asyncSetUp`).
  - **Fix:** apply the identical look-up-or-create-by-natural-key pattern
    already used in `test_phase4_search_discovery.py` /
    `test_phase7_collections_franchises.py` / `test_phase8_streaming_availability.py`
    / `test_phase9_release_calendar.py`.
  - **Related but distinct:** `test_phase4_search_discovery.py`, one of the
    *already-guarded* files, still fails
    (`test_multilingual_benchmark_your_name`) — `AssertionError: 'In Your
    Name' != 'Your Name.'`. The look-up-or-create guard prevents the insert
    collision, but then binds to the **real** pre-existing seeded row, whose
    `canonical_title` is actually `"In Your Name"` in the live catalog, not
    the pretty official `"Your Name."` the test hardcodes and asserts
    against. Guarding against the collision isn't sufficient by itself —
    these tests need to either assert against whatever the looked-up row
    actually contains, or use a natural key that's guaranteed not to
    pre-exist.

  **Root cause C — real, standalone bugs (not test data collisions):**
  - `test_identity_resolver_pipeline_integration.py::test_resolve_identity_is_invoked_during_a_real_pipeline_run` —
    `AssertionError: ...identity_resolver.resolve_identity was never called
    — the pipeline is still deciding matches without the real identity
    resolution engine.` Sounds like a real wiring regression, not test data.
  - `test_identity_resolver_pipeline_integration.py::test_cross_script_duplicate_no_longer_reproduces_end_to_end` —
    `UniqueViolationError` on `unique_provider_title_mapping`,
    `(IMDB, tt1856101)` already exists — same collision-with-real-seed-data
    class of bug as Root Cause B, but on `canonical.title_external_id`
    instead of `canonical.title`. Needs the same look-up-or-create treatment
    for a hardcoded IMDB ID.
  - `test_hierarchy_ingestion.py` (all 3 tests) — `AssertionError: 0 != 1`.
    Not yet root-caused past the assertion itself — needs a closer look at
    what `test_movie_ingestion_has_no_seasons` /
    `test_tv_series_flat_episodes_fallback` /
    `test_tv_series_multi_season_ingestion` are actually asserting; didn't
    have time to trace this one before the session ended.
  - `test_phase4_cache_queue.py::test_kong_valkey_rate_limiting_config_verification` —
    `PermissionError: [Errno 13] Permission denied: 'config/kong/kong.yml'`.
    Likely environment-specific (this session only brought up
    `postgres`+`flyway` via docker compose, not the full stack incl.
    Kong/Valkey containers — see HANDOFF.md's Docker section) rather than a
    code regression, but confirm the file-permission angle specifically
    before dismissing it as infra-only.
  - `test_production_config_validation.py` (both tests) —
    `test_system_admin_absent_without_explicit_opt_in`: `AssertionError: 2
    != 0 : No system_admin account should exist unless
    DEV_ADMIN_PASSWORD_HASH is explicitly set.` **Security-relevant** — 2
    `system_admin` accounts exist in this DB when the test expects 0 absent
    an explicit opt-in env var. Could be genuine residual/leftover admin
    accounts from earlier seeding in this session, or a real gap in the
    opt-in gate — **do not assume test-order pollution without checking**,
    given this touches admin credential provisioning. Treat as
    security-priority for the next session, per this project's mandatory
    security-response protocol.

  **Not yet investigated at all** (ran out of session time): none — every
  one of the 26 failures above has at least a first-pass root cause. What's
  missing is: applying the Root-Cause-A fix and re-running its 12-test
  blast radius, applying the Root-Cause-B look-up-or-create fix to the 2
  newly-found files, root-causing `test_hierarchy_ingestion.py`'s 3
  failures past the bare assertion, and treating the `system_admin` count
  finding as a security item rather than closing it as "probably test
  pollution."

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

**2.1 Taste Match Head-to-Head** — *promoted to first, not third: the vector
infra already exists.*
- Backend: `GET /social/friendships/{friend_id}/compatibility` → load both
  users' `UserTasteProfileModel.taste_vector`, compute
  `1 - cosine_distance` as a 0–100 score, plus shared top genres/directors
  (join `watch_event`/`user_title_state` for both users, intersect).
- No new schema. New repository method in `social_repository`, new response
  schema `CompatibilityResponse`.
- Frontend: a shareable card component (used on the friend's profile and
  the Social page), reusing this same score to finally give `tasteMatch` in
  1.2 real data instead of a hardcoded `95`.
- **Effort:** small · **Depends on:** nothing new.

**2.2 Trust Score → "Taste Tier" display**
- Pure UI: map `FriendshipItem.trust_score` (already returned by
  `GET /social/friendships`) to a labeled tier (Curious/Regular/Critic/Oracle)
  with a progress bar.
- Note from research correction: `trust_score` is a manual/default-50 field,
  *not* a computed taste metric — label it accordingly in the UI copy
  ("Trust" not "Compatibility"; compatibility is 2.1).
- **Effort:** small · **Depends on:** nothing new.

**2.3 Streak tracking**
- New table (Flyway migration, `personal` schema):
  `personal.user_streak (user_id UUID PRIMARY KEY, current_streak INT,
  longest_streak INT, last_watch_date DATE, updated_at TIMESTAMPTZ)`.
- Update on every `create_watch_event` call in `personal_repository` (extend
  the existing "automatically maintain user title state" side-effect block to
  also update the streak row) — avoid a separate nightly job if this hook is
  cheap enough; only add a scheduled job if streak-breaking (missed a day)
  needs off-cycle detection.
- Endpoint: extend `GET /v1/personal/analytics` response with
  `current_streak`/`longest_streak`, or a dedicated
  `GET /v1/personal/streak`.
- **Effort:** small · **Depends on:** nothing new.

**2.4 Weekly friend leaderboard**
- No new schema needed for v1 — compute on read: `GROUP BY user_id` over
  `watch_event` for the last 7 days, scoped to the caller's accepted
  friendships (`social_repository.list_friendships`).
- New endpoint: `GET /social/leaderboard?period=weekly`.
- Only add the `leaderboard_snapshots` cache table later if the live query
  becomes too slow at scale — don't build caching pre-emptively.
- **Effort:** small · **Depends on:** nothing new.

**2.5 Core badge system**
- New tables: `social.badge_definition (id, slug, name, description,
  icon_url, criteria_json)`, `social.user_badge (user_id UUID, badge_id UUID,
  earned_at, context_json, PRIMARY KEY (user_id, badge_id))`.
- Ship with 6–8 seeded badges computable from existing data only (first
  watch, 100 watches, 7-day streak, 5 friends, genre explorer). Evaluate
  badge criteria in a small backend job or lazily on relevant write paths
  (after `create_watch_event`, after `add_friendship`) rather than a cron,
  to start.
- **Effort:** small–medium · **Depends on:** 2.3 (for the streak badge).

### Phase 2 — Viral loop

**2.6 Taste preview invite links**
- New table: `social.invite_token (token TEXT PRIMARY KEY, inviter_id UUID,
  preview_data_json JSONB, expires_at, converted_user_id UUID)`.
- Endpoint to generate a token + snapshot of the inviter's public stats
  (top genres, recent watches) baked into `preview_data_json` at creation
  time (cheap read, no live join needed when the link is opened by a
  non-authenticated visitor).
- **Effort:** small.

**2.7 Invite streak rewards**
- New table: `social.referral (id, inviter_id, invitee_id, status, milestone_reached_at, reward_issued)`.
- Hook into signup flow (wherever a new Keycloak-authenticated user first
  hits the API) to mark `status='signed_up'`, then a milestone check (e.g.
  5 watch events logged) to mark `reward_issued` and award a badge (reuse 2.5's
  tables — add a `referral_reward` badge).
- **Effort:** small–medium · **Depends on:** 2.5, 2.6.

**2.8 Shareable group-pick room (MVP, async voting — no real-time)**
- New tables: `social.pick_room (id, host_id UUID, slug, constraints_json,
  status, winning_title_id, created_at, expires_at)`,
  `social.pick_vote (id, room_id, user_id UUID NULL, guest_name TEXT NULL,
  title_id, vote_type, created_at)`.
- Ballot curation: reuse the AI group-matchmaking recommendation logic
  (`services/api/routers/ai.py`) to generate 5–10 candidate titles from the
  host's (or combined guests') taste vectors, instead of a generic popular
  list.
- Host creates room → shareable link → guests vote (guest voting allowed
  without an account, tracked by `guest_name` + a signed room-scoped
  cookie/token to prevent duplicate votes) → simple majority/ranked-choice
  picks the winner.
- **Effort:** medium · **Depends on:** existing AI matchmaking endpoint.

**2.9 Wrapped-style recap card**
- No new schema — pure aggregation over existing analytics data
  (`get_user_dashboard_metrics`) plus a friend-comparison percentile (needs
  2.4's per-friend aggregation logic).
- Image generation: decide on approach (server-side SVG/Satori render vs.
  client-side `html-to-image` — client-side is far less backend work and
  fine for a v1).
- **Effort:** medium (mostly frontend/design work).

### Phase 3 — Group infrastructure (only once Phase 1–2 prove engagement)

**2.10 Watch Clubs**
- New tables: `social.watch_club (id, name, slug, created_by UUID,
  avatar_url, description, created_at)`, `social.club_membership (club_id,
  user_id UUID, role, joined_at, PRIMARY KEY (club_id, user_id))`.
- **Effort:** medium · **Note:** not a prerequisite for 2.4/2.9's friend-group
  versions — those work off the plain friendship list. Only build this once
  *named, persistent* groups (not just "my friends") are the actual ask.

**2.11 Club Taste DNA** — average member `taste_vector`s + aggregate
`watch_event`/`user_title_state` scoped to `club_membership`. Depends on 2.10.

**2.12 Club activity feed** — new table `social.club_activity (id, club_id,
user_id, activity_type, reference_id, metadata_json, created_at)`, populated
by hooking existing write paths (watch event created, rating set, friend
recommendation accepted) when the acting user belongs to a club. Depends on 2.10.

**2.13 Monthly challenges** — `social.challenge` / `social.challenge_participant`
tables, criteria evaluated against existing watch/rating data. Depends on 2.10
only for club-scoped challenges; global challenges don't need it.

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
