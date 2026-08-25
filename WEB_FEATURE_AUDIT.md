# Web App Feature Audit — 2026-08-25

Session goal: user reported the web app showing only 9 movies / 1 series, broken
filters, and missing images. This audit found the root cause (a dead DB
connection silently falling back to 10-row seed data) plus several deeper bugs
uncovered while verifying every page. Fixed items are checked; remaining gaps
are listed with exact fix paths so the next session can pick up immediately.

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
- [x] Import wizard — loads and renders its 3-step UI correctly (not
  exhaustively tested end-to-end with a real file upload)

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
- [ ] **Import wizard** was only smoke-tested (page loads, 3-step UI
  renders) — not exercised end-to-end with a real file upload/parse/apply
  cycle in this session.
- [ ] **Invite flow / Pick rooms / Watch Club creation / Challenges** — not
  clicked through in this session (ran out of time); the backend for all of
  these was built and regression-tested in earlier sessions per PLAN.md
  Part 2, but wasn't re-verified against the live UI in this pass.

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
