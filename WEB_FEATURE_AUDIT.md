# Web App Feature Audit — 2026-08-25 / 2026-08-26

Session goal: user reported the web app showing only 9 movies / 1 series, broken
filters, and missing images. This audit found the root cause (a dead DB
connection silently falling back to 10-row seed data) plus several deeper bugs
uncovered while verifying every page. Fixed items are checked; remaining gaps
are listed with exact fix paths so the next session can pick up immediately.

**2026-08-26 follow-up session:** resumed the remaining checklist items
(Import wizard, Invite, Pick rooms, Watch Club creation, Challenges) and found
the most severe bug of the whole audit — see "CRITICAL" entry below. All
"Known gaps" from the previous pass that were about untested flows are now
resolved; only the ones needing an external API key or real ingestion source
remain.

## Root cause of the original report

Postgres had gone down (Docker/WSL2 instability — it kept receiving
unexplained "fast shutdown" signals every few minutes; restarting the
container was a temporary fix, not a permanent one — **see "Known
infra issue" below**). With the DB unreachable, the API silently fell back to
a 10-record hardcoded seed list (9 movies + 1 TV series), which explains the
"9 movies / 1 series" the user saw. Fixing Postgres immediately restored the
real 88,979-title catalog.

## Fixed this session

- [x] **Movie/series counts** — Postgres was down; API was silently serving
  10-row seed fallback data. Restarted DB → real catalog now serves
  (70,301 movies / 18,678 series after cleanup below).
- [x] **Genre filters completely broken** — `canonical.title_genre` was 100%
  empty for the real catalog (the bulk IMDb importer never parsed the genres
  column). Wrote `services/api/scripts/backfill_genres_from_imdb.py`, ran it
  against IMDb's public dataset: 199,546 genre links inserted across 88,804
  titles, 28 real genres now populated. Filters work end-to-end (verified:
  Action → 11,601 real results).
- [x] **Test-data pollution in the live catalog** — 123 synthetic test-fixture
  titles ("Inception becc", "Sci-Fi Film 99f0", display_ids `MOV-PK*`/`MOV-REC*`)
  had leaked from earlier regression test runs into the persistent dev DB and
  were visible to real users browsing movies. Deleted (with explicit user
  confirmation): 123 titles, 15 duplicate "Sci-Fi" genre rows, 45 orphaned
  `watch_event` rows.
- [x] **Fabricated `origin_country: "KR"` / `"US"`** — hardcoded on every
  title regardless of real data (the `canonical.title_country` table is
  empty; no real country data was ever ingested). Changed to honest `null`
  in `services/api/repositories/canonical.py` (3 call sites).
- [x] **Fabricated poster/backdrop URLs** — when no real poster existed, the
  API invented a `https://cdn.cinevault.org/...` URL that always 404s
  (that domain doesn't exist). Changed to honest `null` (4 call sites across
  `canonical.py` and `automation.py`); frontend `TitleCard` already handles
  `null` gracefully (shows a placeholder icon, no broken-image flash).
- [x] **Fake "96% AI Taste Match" + fake technical specs** on movie/series
  detail pages (`Dolby Atmos • 5.1 Surround`, `HDR10/SDR`,
  `Licensed TMDB / CineVault Verified`, `Gritty Crime Drama...` — byte-identical
  on every single title, confirmed by comparing two different titles).
  Removed the fabricated AI-match card/badge entirely (no real per-title
  match score exists to compute); technical specs now read from
  `title.primary_edition` with an honest "Not available" fallback (only 2
  edition rows exist in the whole 88,979-title catalog, so this shows "Not
  available" for virtually everything — accurate, not a bug).
- [x] **`/v1/personal/analytics` fabricated data** — `top_genres`,
  `top_directors`, `top_actors`, `monthly_trend`, `pending_recommendations_count`
  were 100% hardcoded literals shown to every user regardless of activity
  (e.g. "Denis Villeneuve (9)" for a brand-new account with zero watch
  history). Now computed for real from the user's actual `watch_event` +
  `credit`/`genre` joins and real `social.recommendation` rows. A fresh user
  now correctly sees all-zero/empty results.
- [x] **Dashboard "Total Catalog Titles" mislabeled** — the number shown was
  actually the user's personal tracked-title count, not catalog size; label
  fixed to "My Tracked Titles", fake "+12 added this week" trend text removed.
- [x] **Watch History (`/v1/personal/history`) was 100% fake** — a hardcoded
  4-event list (Dune: Part Two, Blade Runner 2049, Severance, Oppenheimer)
  shown to every user. Now backed by real `personal.watch_event` rows, joined
  with real titles and the user's real ratings. Delete now really
  soft-deletes the event instead of mutating a shared in-memory list.
- [x] **Collections (`/v1/personal/collections`) was 100% fake** — 3
  hardcoded demo collections shared by every user (mutations touched a
  global Python list, resetting on server restart). Now backed by real
  `personal.user_list` / `user_list_item` tables, scoped per-user.
- [x] **Personal Library had no backend at all** — the page just displayed
  the first 6 movies + 4 series from the general catalog, identical for
  every user, with zero connection to what a user actually added.
  `personal.library_entry` existed as a table but was never queried anywhere
  in the codebase. Built `GET/POST /v1/personal/library` +
  `DELETE /v1/personal/library/{title_id}`, rewired the frontend page to the
  real endpoint.
- [x] **Auth: silent login failures under load** — `apps/web/src/app/api/auth/local-login/route.ts`
  had a 1500ms timeout calling the backend's real auth handshake; if missed
  (e.g. right after a dev-server restart), it silently fell back to a fake,
  unvalidatable token. This made every strictly-authenticated endpoint return
  401 with no visible error (`/v1/recommendations`, `/social/badges`, etc.),
  while endpoints using optional auth silently ran as an anonymous default
  user instead of erroring. Raised the timeout to 8000ms.
- [x] **CRITICAL — the browser never actually sent auth to the backend, at
  all, for anything.** `apiFetch` (`src/lib/api/client.ts`) called the
  FastAPI backend directly from the browser (`http://localhost:8000/...`)
  and never attached an `Authorization` header — it only ever set
  `Content-Type`/`Accept`. This is architecturally impossible to fix by
  attaching a header client-side: the real access token lives only in an
  encrypted, intentionally-HttpOnly session cookie precisely so client JS
  can never read it (see the explicit comment to that effect in
  `src/app/api/auth/me/route.ts`). The result: every `require_authenticated_user`
  endpoint (watch clubs, challenges, recommendations, badges, taste-matches,
  leaderboard, friendships...) 401'd unconditionally, and every
  `get_optional_claims` endpoint (personal history/library/collections/
  analytics) silently ran as the shared anonymous fallback user
  (`00000000-...-000000000001`) regardless of who was actually logged in —
  meaning last session's "watch history now shows real data" verification
  was real, but scoped to that shared anonymous bucket, not actually to the
  logged-in dev user. Root cause confirmed by testing directly: a token
  minted straight from `/v1/auth/login` worked perfectly against
  `/social/clubs` (201 Created), while the browser's own session — for the
  same user — got 401 on the identical call.

  **Fix:** added `src/app/api/proxy/[...path]/route.ts`, a catch-all
  Next.js route handler that runs server-side, reads the real access token
  out of the session cookie, and forwards the request to FastAPI with
  `Authorization: Bearer <token>` attached — the token still never reaches
  client JS, the security boundary is preserved. Changed `apiFetch`'s base
  URL from the FastAPI origin to `/api/proxy`, so every existing call site
  (the entire `src/lib/api/*.ts` surface) is fixed with zero call-site
  changes. Verified via network log: `/social/clubs`, `/social/challenges`,
  `/social/recommendations`, `/social/friendships`, `/social/leaderboard`,
  `/social/taste-matches`, `/social/invites`, `/social/referrals` all now
  return 200/201 through the real logged-in session where they previously
  401'd or silently ran anonymous.
- [x] **Challenge creation sent the wrong field** — the "Challenge Type"
  dropdown (Genre Exploration Marathon / Director Retrospective / etc., a
  scoring *metric*) was being sent as the backend's `challenge_type` field,
  which actually means challenge *scope* (`GLOBAL` vs `CLUB`, validated by a
  strict regex) — every challenge creation 422'd. Fixed
  `apps/web/src/app/clubs/page.tsx`: the metric now goes into
  `criteria_json.metric`, and `challenge_type` is correctly derived as
  `"CLUB"` when created from within a club or `"GLOBAL"` otherwise. Verified
  live: challenge creation now returns 201 and appears in the list.
- [x] **Fake watch-club "Taste DNA" stats** — a brand-new club with zero
  members' worth of watch history showed "12 Logged" watches
  (`member_count * 12`, a literal fabricated formula) and a hardcoded genre
  breakdown (`Sci-Fi/Cyberpunk 88%, Psychological Thriller 76%...`) —
  byte-identical for every club, `ClubDetailResponse` has no backing fields
  for either. Removed the fake breakdown, "Total Watches" now shows the
  real (currently always-zero, since no real aggregation exists yet) count
  with an honest "will appear once members start logging watches" message,
  matching the tone of the already-correct "no activity yet" empty state
  right below it on the same page.

## Verified working, no changes needed

- [x] Movies/Series search (tested "FIFA" → correct 7-result match)
- [x] Movies/Series sort (Newest/Oldest/A–Z/Z–A wired to real API params)
- [x] Movies/Series pagination (infinite scroll via `next_offset`)
- [x] Watchlist page — correctly empty for a new user, no fake data
- [x] Social inbox — correctly empty for a new user, no fake data
- [x] Watch Clubs page — correctly empty for a new user, no fake data
- [x] AI Oracle chat — degrades honestly ("error connecting to the neural
  reasoning backend") when no LLM provider key is configured, rather than
  crashing or faking a response
- [x] Settings page — static config/info display, nothing fabricated found
- [x] **Import wizard — full end-to-end verified.** Parsed the default
  6-item Samsung Notes sample, all 6 titles matched EXACT (100%) against the
  real catalog, applied to the vault, and the 6 real `watch_event` rows
  correctly appeared on the real Watch History page afterward. (My first
  attempt looked broken — turned out to be my own test methodology, not the
  app: I typed into the textarea without clearing its pre-filled sample
  text first, corrupting the input. On a clean run it works correctly.)
- [x] **Invite flow** — "Invite Friends" panel generates a real shareable
  link and referral stats via real `POST /social/invites` +
  `GET /social/referrals` calls (both 200 OK), not hardcoded.
- [x] **Watch Club creation & Monthly Challenges — now fully working** (both
  were silently broken by the auth bug above until this session's fix).
  Created a real club and a real challenge through the UI end-to-end.
- [x] **Pick Rooms — view/vote path confirmed working**, degrades correctly
  to a "Ballot Not Found" page for an invalid/expired slug. Note: there is
  **no UI entry point to create one** — `createPickRoom` exists in
  `src/lib/api/personal.ts` and the backend endpoint works, but no page or
  button in the app actually calls it. Pick rooms can currently only be
  reached via a direct `/pick/{slug}` link if one already exists. Worth a
  product decision: is this an intentional "invite-only via external share"
  design, or a missing "Create Pick Room" button somewhere (e.g. on the
  Social or Clubs page)?

## Known gaps / requires your input (not fixed — needs a decision or a key)

- [ ] **No real poster images anywhere** — `poster_sync_status` is `PENDING`
  for 88,979/88,979 titles; the `services/api/ingestion/tmdb_worker.py`
  poster-sync worker exists and works, but needs a `TMDB_API_KEY` in `.env`
  (free key from themoviedb.org). Once set, run:
  `python services/api/ingestion/tmdb_worker.py` — rate-limited to 20 req/s,
  will take a long time for 89k titles (consider `--max-batches` to test
  first). Frontend already handles missing posters gracefully in the
  meantime (shows a placeholder icon, not a broken image).
- [ ] **AI Oracle chat has no LLM behind it** — needs `OPENAI_API_KEY` or a
  Gemini key configured (`services/api/ai/provider.py`) to actually answer
  questions instead of showing the graceful-degradation error message.
- [ ] **Technical specs (audio/aspect ratio/color grading) show "Not
  available" for virtually the whole catalog** — only 2 rows exist in
  `canonical.edition` total. This is real, honest data — the catalog just
  doesn't have edition-level metadata. Would need a real ingestion source
  for this (not something a quick fix can conjure).
- [ ] **`origin_country` is `null` for virtually every title** —
  `canonical.title_country` is empty (0 rows). Same root cause as above: the
  bulk IMDb importer (`services/api/scripts/seed_bulk_imdb.py`) never
  ingested country data, only title/year/content-type. IMDb's dataset
  doesn't carry country directly — would need a `title.akas.tsv.gz` join or
  a TMDB backfill (same pattern as the genre backfill script, could be
  adapted).
- [ ] **Known infra flakiness: Postgres exits on its own every few minutes**
  under Docker Desktop on this machine (confirmed twice this session via
  `docker logs` showing unexplained "received fast shutdown request" with no
  corresponding command from this session). This is a Docker Desktop/WSL2
  environment issue, not an application bug — if the app "loses its data"
  again after a break, check `docker ps` first; the fix is just
  `docker compose -f infra/docker/docker-compose.yml up -d postgres pgbouncer`.
  Worth investigating Docker Desktop's resource/idle settings if it keeps
  recurring.
- [ ] **Pick Rooms have no "Create" UI** — see note above under Verified
  Working. Needs a product decision on where a "Create Pick Room" entry
  point should live before it's worth building.
- [ ] **Import wizard's file-upload path** (as opposed to paste-text, which
  is fully verified) wasn't exercised with a real file — only the textarea
  input path was tested end-to-end.

## Test residue in the dev account

While verifying the fixes above, real test data was created under the `dev`
user's own account (not the shared catalog — this is isolated per-user data,
unlike last session's catalog pollution, so it's harmless to leave, but worth
knowing about): a "Test Club" and "Neo-Noir Society" watch club, an "Audit
Test Challenge", and 6 watch-history entries from the Import wizard test
(Dune: Part Two, Blade Runner 2049, Oppenheimer, Severance, Arrival,
Interstellar). Delete these from the UI if you want the dev account clean,
or leave them — they don't affect anyone else.

## How to resume the dev environment

```bash
# 1. Postgres + pgbouncer (check docker ps first — it may already be up)
docker compose -f infra/docker/docker-compose.yml up -d postgres pgbouncer

# 2. API server (port 8000)
cd C:/Desktop/flutter_projects/CineVault
python -m uvicorn services.api.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Web app (port 3000) — likely already running; check with:
#    netstat -ano | grep ":3000"
cd apps/web && npm run dev
```

Note: uvicorn's `--reload` has been flaky on this Windows machine — it
sometimes logs "Reloading..." but never actually spawns a new worker,
silently continuing to serve stale code. If a fix doesn't seem to take
effect after saving a file, check the log for a `Started server process
[PID]` line after the reload warning; if it's missing, kill and restart the
server process manually.
