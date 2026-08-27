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

**2026-08-27 session 4:** closed out most of the remaining "Known gaps" list
from session 3 — the ones that didn't strictly need a paid/rate-limited
external service. Replaced the dead local-Ollama dependency for taste-vector
embeddings with a self-hosted `sentence-transformers` model (no external API,
no ongoing cost); wired Groq (OpenAI-compatible, generous free tier) into the
existing `AIProviderFactory` as a first-class provider alongside OpenAI/
Gemini; and along the way found and fixed two foundational bugs that would
have silently defeated the "just paste a key into `.env`" instructions in
this very doc — see "Fixed this session (session 4)" below. Also addressed
the two documented infra-flakiness items (Postgres/WSL2 restarts, uvicorn
`--reload` silently not reloading) and started the IMDb country-data
backfill. Marked the technical-specs gap "won't fix" — confirmed via
research that no free API carries this data at catalog scale.

**2026-08-26 session 3:** built the missing Pick Room "Create"
entry point, verified the Import wizard's file-upload path for real, then did
a genuine, feature-by-feature click-through of every page — including using
a *second real account* (`curator@cinevault.local`) to actually exercise the
multiplayer flows (friend requests, recommendations, club joins, challenge
progress) that a single-account pass can't reach. Found and fixed 12 real
bugs across the session: a second major fabricated-data bug on the movie/
series detail pages that survived the previous session's fabrication sweep;
five separate "the backend works but nothing in the UI ever calls it" gaps
(Add/Remove Library, badge unlocking, a dead `/friends` link, a missing
`/clubs/[slug]` join-by-link route); a Group Matchmaker feature that always
502'd (hardcoded to a local Ollama server that isn't running) and returned
fake candidate titles; and two data-correctness bugs in Watch Clubs/
Challenges (member names never resolved, participant counts and progress
bars never computed as anything but 0%/blank). Root-caused (but did not fix,
scope/architecture reasons documented below) one systemic backend pattern
and one more Ollama-dependent dead endpoint. See "Fixed this session
(session 3)" below for the full list. The website is now fully verified
working end-to-end across every page and every real user action reachable
from the UI; only the TMDB/LLM API keys remain as external dependencies.

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

## Fixed this session (session 3, 2026-08-26)

- [x] **Pick Rooms had no "Create" UI** — decided this belongs on the Social
  page (movie-night voting is a friend-group activity, same audience as
  Invite Friends/Recommendations). Added a "Create Pick Room" button to
  `apps/web/src/app/social/page.tsx` opening a modal: ballot title, voting
  window (hours), and a debounced catalog search to nominate 2–12 titles.
  Submits to the real `POST /social/pick-rooms` and redirects to the new
  `/pick/{slug}` ballot. Verified live end-to-end: created a room with 2
  nominees, cast a vote, saw the tally update in real time.
- [x] **Import wizard file-upload path — now verified for real.** The
  previous session's "full end-to-end verified" claim only ever exercised
  the paste-text path; the file input was untested. Simulated a real
  `File`/`DataTransfer` drop on the hidden `<input type="file">` with a
  Letterboxd-format CSV: parsed correctly, auto-detected the CSV format
  hint from the `.csv` extension, matched both titles EXACT, applied to the
  vault, and the real `watch_event` rows appeared on Watch History
  afterward.
- [x] **CRITICAL — fabricated genre/country/synopsis/poster data on movie
  & series detail pages, missed by the previous session's fabrication
  sweep.** `apps/web/src/app/movies/[id]/page.tsx` and
  `apps/web/src/app/series/[id]/page.tsx` had a `"Fallback cinematic
  metadata if direct API backend isn't populated"` block that substituted
  **hardcoded Blade Runner 2049 / Sacred Games data** (title, year, country,
  synopsis, genres, backdrop, poster, runtime, edition name) for any title
  missing that field. Since `origin_country` is null for virtually the
  entire catalog (a still-open gap, see below) and many titles have empty
  `genres`, this meant most movie/series pages on the site were showing a
  **fabricated "USA" origin** and, for titles the genre backfill script
  didn't reach, fake genre tags — for real, correctly-empty API responses
  (confirmed via direct `curl` against `/v1/titles/{id}`: API returns
  `genres: []`, `origin_country: null`; the page rendered "Sci-Fi, Mystery,
  Cyberpunk, Drama" and "USA" anyway). Removed every fabricated fallback;
  fields now render conditionally (badges/rows only appear when real data
  exists) or show an honest "No genre data available" / "No synopsis
  available" / "Not available" note, matching the pattern already used
  correctly elsewhere on the same page for edition metadata. Missing
  poster/backdrop images now render a plain icon placeholder instead of an
  external Unsplash stock photo. Verified against both an empty-data title
  (honest "No genre data available", no country badge) and a real-data
  title (genres render correctly, no regression).
- [x] **Personal Media Library had no way to add anything.** The backend
  (`POST /v1/personal/library`) and the `addToLibrary()` API client
  function both existed and worked, but were never called from anywhere in
  the UI — the Library page's "Add New Title" button just links to
  `/movies` (browse), and no movie/series detail page had an "Add to
  Library" action. Added one to both detail pages next to "Add to
  Watchlist". Also fixed the Library grid's poster `<img src="">` (rendered
  a broken-image icon for any item with no poster) to use the same
  icon-placeholder pattern as `TitleCard`. Verified live: added a title,
  confirmed it appears on `/library`.
- [x] **`/friends` was a dead link — 404.** The Social page's "Manage (N)"
  button has always pointed to `href="/friends"`, but no such route existed
  anywhere in `apps/web/src/app`. Built `apps/web/src/app/friends/page.tsx`:
  lists accepted friends, pending-received requests (Accept/Decline via the
  real `PATCH /social/friendships/{id}`, decline maps to the backend's
  `BLOCKED` status since there's no separate "rejected" state), and
  pending-sent requests awaiting a response. No "search for a user to add"
  form was built — the backend has no user-directory/search endpoint at
  all, so the invite-link flow on the Social page is the only real path to
  a new friendship; the page says so honestly instead of shipping a search
  box that would have nothing to search. Added `updateFriendshipStatus()`
  and `requester_id`/`addressee_id` to `src/lib/api/ai.ts`. Verified live:
  navigated via the Social page's "Manage" link, page loads correctly.
- [x] **Group Taste Matchmaker (Oracle page, "Group Taste Matchmaker" tab)
  was completely broken — every request 502'd.** `POST /ai/group-matchmaking`
  (`services/api/routers/ai.py`) called a local **Ollama** server directly
  (`http://localhost:11434`) instead of the same `AIProviderFactory`
  (mock/openai/gemini) abstraction the Conversational Oracle chat correctly
  uses — Ollama isn't installed/running in this environment, so this would
  have stayed broken even after adding the OpenAI/Gemini key. Confirmed via
  server log: `httpx.ConnectError: All connection attempts failed` →
  `502 Bad Gateway` on every call. Separately, the same endpoint's candidate
  titles were **hardcoded** (`["Inception", "Interstellar", "Blade Runner
  2049"]`, byte-identical for every group regardless of mood or members —
  the same fabrication pattern this whole audit has been hunting, just not
  yet caught here). Fixed both: candidate titles now come from the real
  `recommendation_repository.get_recommendations()` pipeline (the same one
  powering the Dashboard's "Top AI Taste Recommendations" and already
  cold-start aware for members with no watch history), and the AI response
  now goes through `AIProviderFactory.get_provider().generate_assistant_response()`
  like the rest of the app. Verified end-to-end in the browser: selected a
  real accepted friend, generated a real consensus with 3 real catalog
  titles and a real grounded explanation (currently via the Mock provider
  pending the LLM key, degrading the same honest way the Conversational
  Oracle chat does).
- [x] **Verified the friendship request Accept/Decline flow for real** —
  used a second real account (`curator@cinevault.local` /
  `curatorpass`, from `services/api/auth/user_directory.py`) to send `dev`
  an actual `PENDING` friendship via the API, confirmed it renders correctly
  on the new `/friends` page ("curator wants to connect"), clicked Accept,
  confirmed it moved to "Your Circle." Also used the resulting real
  friendship to verify "Recommend to a Friend" (movie detail page → Social
  "Sent" tab, real `201 Created`), the AI Taste Match compatibility modal
  (honest 0.0% / "No common genres watched yet" for a friend with zero
  watch history — no fabrication), and the Leaderboard (correctly showed
  both real users, `dev` at 4 titles / 8.0h from the earlier Import-wizard
  test data, `curator` honestly at 0).
- [x] **Achievement badges could never actually unlock.** `GET
  /social/badges` only lists already-persisted earned rows; the actual
  criteria check that grants a badge lives behind a separate
  `POST /social/badges/evaluate`, which — like Pick Room creation and Add to
  Library before this session's fixes — existed as a working API client
  function (`evaluateUserBadges()`) that nothing in the UI ever called. Real
  users could rack up real watch history, collections, and friends forever
  and never see a single 🏆, only 🔒. Swapped the Dashboard's badges query
  from `getUserBadges()` (read-only) to `evaluateUserBadges()` (evaluates
  then returns the same shape, so it's a one-line change with no extra
  request) — badges now self-heal on every dashboard visit rather than
  needing every earning action individually wired to re-evaluate. Verified
  live: went from "0 of 6 Unlocked" to "2 of 6 Unlocked" (First Reel,
  Curator Elite) on the very next load, both with real unlock timestamps.
- [x] **A shared Watch Club link had nowhere to land — no `/clubs/[slug]`
  route existed at all.** `GET /social/clubs` (used for the clubs list page)
  only ever returns clubs the caller already belongs to, so the only way to
  reach a club's detail view was to already be a member — a link to a club
  a friend wanted you to join (`POST /social/clubs/{slug}/join` and
  `GET /social/clubs/{slug}` both already work for any authenticated user,
  no membership required) had no page to open. Same shape as the Pick Rooms
  create gap fixed earlier this session, just the mirror image — join
  already worked, discovery didn't. Built
  `apps/web/src/app/clubs/[slug]/page.tsx` (standalone club view: header,
  Join button, members, live activity feed, honest empty states) and added
  a "Share Club" copy-link button next to the existing embedded Join button
  on `/clubs`. Verified end-to-end with two real accounts: logged in as
  `curator` (not a member of `dev`'s "Test Club"), opened the shared
  `/clubs/test-club-7fce01` link, saw the club, clicked Join, member count
  went from 1 to 2 in real time.
- [x] **Every watch club's creator and member names were always blank,
  every club, always.** Found while verifying the join-by-link fix above —
  the club UI fell back to generic "CineVault Member" / "Club Member" text
  for literally every club because `services/api/routers/social.py`'s three
  club endpoints (`create_watch_club`, `get_watch_club`, `list_my_clubs`)
  never called `resolve_display_names()`, unlike every other social
  endpoint in the same file (recap, pick-rooms, recommendations, invites
  all do). Added the same resolution pattern used elsewhere in this file to
  all three. Verified live: "Curated by dev" and real member names/roles
  ("dev @dev OWNER", "curator @curator MEMBER") now render correctly.
- [x] **Two more challenge bugs found joining/logging a challenge as a
  second real account:** (1) `GET /social/challenges` never computed
  `participant_count` on the real-DB path at all (unlike the single-
  challenge detail endpoint, which does) — every challenge showed
  "0 Cinephiles" on the browse view no matter how many people had actually
  joined. Fixed with one grouped count query for the whole page (not N+1).
  (2) The goal-progress bar was **hardcoded** — literally
  `w-2/5` (fixed 40% width) on a div explicitly commented `{/* Progress Bar
  Demo */}`, same for every challenge and every user regardless of anyone's
  real progress; the "Join" button was also always shown even for
  challenges you'd already joined, and "+1 Log" was clickable whether or
  not you'd joined at all (the backend correctly 404s "not a participant"
  for that case, so it was a real no-op dead click, not a crash). Added
  `my_progress`/`my_completed` (caller-relative, `None` distinct from `0`)
  to `ChallengeResponse` computed in the same list query, and made the UI
  honest: real progress bar width, "Join" only shown pre-join, "+1 Log" +
  "Joined"/"Completed!" shown after. Verified live with the real `curator`
  account across a server restart: joined → "Not Joined Yet" flipped to
  "1 / 5 Logged" with a real 20%-width bar; clicked "+1 Log" again → live
  update to "2 / 5 Logged" with no page reload.
- [x] **Personal Media Library had no way to remove anything, either.**
  Same shape as the missing "Add to Library" gap fixed earlier this
  session, just the other direction: `removeFromLibrary()` existed in the
  API client and the backend `DELETE /v1/personal/library/{title_id}`
  worked, but the Library grid was a plain `<Link>` card with no remove
  action anywhere. Restructured the card (outer `<div>` + inner `Link`s, so
  a remove click doesn't also navigate) and added a "Remove from Library"
  button matching the Watchlist page's existing pattern. Verified live:
  removed a title, grid went from "All Media (1)" to "All Media (0)".
- [x] **Cleaned up cross-session test residue while verifying deletes**:
  removed the two duplicate Watch History entries from the double-tested
  Import file-upload flow, removed the leftover Watchlist entry from
  earlier testing.
- [x] **"Mark as Watched" (the heart button on movie/series detail pages)
  had no `onClick` at all — a fully dead button.** `POST /v1/me/watch-events`
  already works and powers the real Watch History page, but nothing in the
  frontend API client even wrapped it. Added `logWatchEvent()` to
  `src/lib/api/personal.ts` and wired it into both detail pages (fills icon
  red + disables once logged, invalidates history/analytics/badges so they
  all update immediately). Verified live: clicked it on "100 Days Love
  Story", got a real `201 Created`, the title appeared on Watch History at
  the exact click timestamp.
- [x] **CRITICAL — Collections could be created and deleted, but never
  actually populated with a single title.** `personal.user_list_item` (the
  join table for "which titles are in this collection") has existed in the
  data model the whole time — `list_collections` was even already loading
  it (`selectinload(UserListModel.items)`) to compute `item_count` — but
  there was no endpoint anywhere to add an item, remove an item, or view a
  collection's contents. "Explore Collection" on the Collections page just
  linked to `/movies` (the generic catalog browse), for every collection,
  same link regardless of which collection you clicked. This made the
  entire "Collections & Franchises" feature a dead end: create one, and it
  stays at 0 items forever. Built the missing surface: backend —
  `GET /v1/personal/collections/{id}` (real items joined against
  `canonical.title`), `POST .../items`, `DELETE .../items/{title_id}`;
  frontend — `apps/web/src/app/collections/[id]/page.tsx` (standalone
  detail view, same pattern as the Pick Room/Watch Club standalone pages),
  an "Add to Collection" button + picker modal on both movie and series
  detail pages (mirrors the existing "Recommend to a Friend" modal), and
  fixed "Explore Collection" to link to the real collection instead of the
  generic catalog. Verified live end-to-end: added "100 Days Love Story" to
  "A24 Modern Classics" from its movie page (2 titles), confirmed both
  titles render on the real collection page with real posters/years/notes,
  removed one via its own remove button (back to 1 title, correct item
  still present).
- [x] **Import wizard's plain-text parser broke matching for otherwise-real,
  otherwise-exact titles whose line ended in " - <rating>" with no note
  text after the dash** — a very common real-world format ("Parasite (2019)
  - 5/5"). Once the year and the rating were both parsed out, `"Parasite
  (2019) -"` had no `" - "` (space-dash-space) left to split into a note,
  so the bare trailing `-` was never stripped and survived into the parsed
  `canonical_title` — `"Parasite -"` fails both the exact-match and the
  `ILIKE` fallback lookup against a catalog that has plain `"Parasite"`.
  Found by testing a real title through the parser and getting an honest
  "Unmatched" verdict for a title that plainly exists. Fixed
  `apps/web/src/lib/api/import.ts`'s trailing-punctuation strip regex to
  also catch a dangling `-`. Verified: the same input now matches
  `Parasite` at `Exact (100%)`. Also verified the Disambiguation modal
  itself (never previously clicked through end-to-end): typed a real title
  into a genuinely-unmatched fake entry, saved, watched it re-run the match
  and correctly report `Probable (80%)` plus a real conflict (against
  watch-history data logged earlier this session) — not applied to the
  vault, to avoid adding more test residue.
- [x] **The notification bell's dot indicator was hardcoded, permanently
  visible on every page for every user regardless of whether anything was
  actually pending** (`components/layout/Header.tsx` — a plain `<span>`
  with no conditional at all). Found via a systematic sweep for "exported
  API function nothing calls" — this wasn't that pattern, but was caught by
  the same kind of check on hardcoded UI. Wired it to real data: pending
  received recommendations (`status === "SENT"`) + pending-received friend
  requests, shared query cache with the Social/Friends pages so it costs no
  extra request on pages that already loaded them. Verified live both
  ways: no dot with an empty inbox, dot appears the instant `curator` sends
  `dev` a real recommendation via the API, gone again after dismissing it.
  Also exercised the Social inbox's "Dismiss" button for the first time
  this session (only "Accept" had been tested before) — works correctly.

## Fixed this session (session 4, 2026-08-27)

- [x] **CRITICAL — the root `.env` file was never actually loaded anywhere in
  the backend.** `services/api/config.py`'s `APIConfig` is a plain
  `pydantic.BaseModel` reading `os.getenv(...)` at class-definition time —
  there was no `python-dotenv` call (or any other loader) anywhere in the
  codebase. This meant every instruction in this doc to "add `TMDB_API_KEY`/
  `OPENAI_API_KEY`/`GEMINI_API_KEY` to `.env`" would have silently done
  nothing: those values only ever reached `os.getenv()` if they happened to
  already be exported in the shell before Python started, which none of the
  documented restart commands do. `python-dotenv` was present only as an
  incidental transitive dependency of another package, never invoked. Fixed
  by calling `load_dotenv()` at the top of `config.py`, before any
  `os.getenv()` call in the module executes, pointed at the repo-root `.env`
  regardless of the working directory uvicorn is launched from. An explicit
  shell-exported variable still wins over the file (standard `load_dotenv()`
  behavior, `override=False`), so nothing that worked before regresses.
- [x] **`AIProviderFactory.get_provider()` never used the auto-detect logic
  that already existed for it.** `config.effective_ai_provider` (resolves to
  whichever of `openai`/`gemini`/etc. has a real key set, falling back to
  `mock` only when none do) was fully implemented but never called from
  anywhere — the factory read `os.getenv("AI_PROVIDER", "mock")` directly
  instead, meaning setting an API key alone did nothing without *also*
  explicitly setting `AI_PROVIDER=<name>`. Wired `get_provider()`'s default
  path through `config.effective_ai_provider` so "set one API key" is
  actually sufficient, matching what the property's own docstring always
  claimed it did.
- [x] **`POST /social/taste-profile/compute` no longer depends on a local
  Ollama server.** Replaced the `OllamaClient().generate_embedding()` call
  (dead on arrival — nothing runs Ollama in this environment) with a
  self-hosted `sentence-transformers/all-MiniLM-L6-v2` model
  (`services/api/ai/embedding_service.py`), the same model family Ollama's
  `all-minilm` was already wrapping, so the output shape (384-dim,
  L2-normalized) is unchanged. Runs in-process via `asyncio.to_thread` (no
  external network call after the first model download), so this closes the
  gap with zero ongoing cost and zero new API key. Deleted the now-fully-dead
  `services/api/ai/ollama_client.py` (its only other caller, group
  matchmaking, was already moved off Ollama in session 3) and rewrote
  `tests/test_v2_ai_brain.py` accordingly — including two tests
  (`test_group_matchmaking_end_to_end_lifecycle`,
  `test_group_matchmaking_*_failure_returns_502`) that had gone stale in
  session 3's Ollama removal and were mocking a code path
  (`OllamaClient.generate_chat`) the group-matchmaking endpoint no longer
  calls at all.
- [x] **Wired Groq in as a first-class `AI_PROVIDER` option.** Groq exposes
  an OpenAI-compatible endpoint, so `GroqProviderAdapter` in
  `services/api/ai/provider.py` subclasses `OpenAIProviderAdapter` and only
  overrides the base URL/key/model/display-name/enum — every actual method
  (`extract_intent`, `generate_assistant_response`, `generate_proposal`) is
  inherited unchanged. Set `GROQ_API_KEY` (and optionally `GROQ_MODEL`,
  defaults to `llama-3.3-70b-versatile`) in `.env` to activate it for the
  Oracle chat and Group Matchmaker — same honest Mock-provider degradation
  as OpenAI/Gemini when no key is present.
- [x] **uvicorn `--reload` Windows flakiness — root-caused further and
  fixed.** Found that `watchfiles` (the reliable file-watcher backend
  `uvicorn[standard]` normally provides) wasn't actually installed — the
  bare `uvicorn` in `requirements.txt` meant `--reload` was silently running
  on Python's polling-based `StatReload` fallback the whole time, which is
  the likely root cause of the "logs Reloading... but never actually
  reloads" behavior documented in session 2/3. Fixed the requirements pin to
  `uvicorn[standard]` and added `infra/scripts/run_api_dev.py`, a small
  launcher that also sets `asyncio.WindowsSelectorEventLoopPolicy()` before
  uvicorn's reload supervisor creates its event loop (setting it inside
  `services/api/main.py` itself would be too late — the supervisor process
  starts before it ever imports the app). `infra/scripts/start-dev.ps1` /
  `start-dev.sh` now launch the API through this script instead of calling
  `uvicorn` directly. Not yet verified end-to-end across a real multi-edit
  session — worth confirming next time `--reload` is relied on for a while.
- [x] **Postgres/WSL2 stability — applied the two standard mitigations.**
  Added `restart: unless-stopped` to the `postgres` and `pgbouncer` services
  in `infra/docker/docker-compose.yml` so an unexplained "fast shutdown"
  self-heals instead of silently falling back to seed data until someone
  notices. Created `%UserProfile%\.wslconfig` with `memory=8GB`/`swap=4GB`
  (this machine has ~16GB total RAM) — unbounded WSL2 memory growth is a
  documented trigger for VM-level instability that can kill containers
  running inside it. **Requires a `wsl --shutdown` + Docker Desktop restart
  to take effect** — not done automatically since it would kill whatever's
  currently running; do this before your next dev session.
- [x] **Country-of-origin backfill from IMDb's `title.akas.tsv.gz`** —
  complete. Ran `services/api/scripts/backfill_country_from_imdb.py` against
  the live catalog: **88,960 of 88,977 IMDb-sourced titles (99.98%) now have
  a real `canonical.title_country` row**, up from 0. Verified directly
  against the DB (join matches the exact derivation
  `services/api/repositories/canonical.py` uses for `origin_country` /
  `countries`) — e.g. `IMDB-tt0000574` ("The Story of the Kelly Gang") →
  `AU`, `IMDB-tt0002199` ("From the Manger to the Cross") → `BR`. Scanned all
  59,104,906 rows of the 511MB akas dataset. The 17 titles without a country
  either had no valid (non-`\N`, 2-letter) region anywhere in their akas
  entries, or no akas entries at all — both real, honest gaps, not a bug.
  Fixed a real parsing bug found along the way: Python's default
  `csv.reader` quote handling (`QUOTE_MINIMAL`) treats a literal `"` in an
  IMDb title as an opening quote and swallows everything up to the next
  matching `"` — sometimes megabytes later — into one field, which exceeds
  the default `field_size_limit` and crashes with `_csv.Error: field larger
  than field limit`. Fixed by passing `quoting=csv.QUOTE_NONE` (IMDb's TSVs
  aren't CSV-quoted; tab is the only real delimiter). Also fixed the same
  latent bug in the existing `backfill_genres_from_imdb.py`, which had it
  too and had just gotten lucky not hitting it. The script safely resumes on
  re-run (`ON CONFLICT DO NOTHING` + skips already-backfilled title_ids), so
  the crash mid-run cost only time, not data correctness.

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
- [x] **Pick Rooms — full create/view/vote path confirmed working**
  end-to-end (create UI added this session, see above), degrades correctly
  to a "Ballot Not Found" page for an invalid/expired slug.

## Known gaps / requires your input (not fixed — needs a decision or a key)

- [ ] **No real poster images anywhere** — `poster_sync_status` is `PENDING`
  for 88,979/88,979 titles; the `services/api/ingestion/tmdb_worker.py`
  poster-sync worker exists and works, but needs a `TMDB_API_KEY` in `.env`
  (free key from themoviedb.org — now actually loaded, see session 4's
  `.env`-loading fix above). Once set, run:
  `python services/api/ingestion/tmdb_worker.py` — rate-limited to 20 req/s,
  will take a long time for 89k titles (consider `--max-batches` to test
  first). Frontend already handles missing posters gracefully in the
  meantime (shows a placeholder icon, not a broken image).
- [ ] **AI Oracle chat has no LLM behind it** — needs `GROQ_API_KEY` (now
  wired in, session 4 — recommended: free tier is fast and generous),
  `OPENAI_API_KEY`, or `GEMINI_API_KEY` in `.env` to actually answer
  questions instead of showing the graceful-degradation error message.
- [x] ~~Technical specs (audio/aspect ratio/color grading) show "Not
  available" for virtually the whole catalog~~ — **won't fix.** Confirmed via
  research (session 4) that TMDB's `release_dates` endpoint, OMDb, and the
  IMDb bulk datasets all lack audio-format/aspect-ratio/HDR data — no free
  API carries edition-level technical specs at this catalog's scale. Only 2
  rows exist in `canonical.edition` total; this is honest, correctly-empty
  data, not a bug. Leaving the "Not available" fallback as-is; would need
  either a paid data source (Gracenote/Rovi-class) or manual curation to
  close, neither of which is a quick fix.
- [x] ~~`POST /social/taste-profile/compute` still calls Ollama directly and
  will 502`~~ — **fixed, session 4.** Now backed by a self-hosted
  `sentence-transformers` embedding model, see "Fixed this session (session
  4)" above. Still not called from anywhere in the frontend (grepped again to
  confirm) — the same "wire into onboarding, or leave as a working-but-unused
  endpoint" decision from session 3 still stands, now moot from a
  reliability standpoint since it no longer 502s.
- [ ] **`origin_country` is `null` for virtually every title** —
  `canonical.title_country` is empty (0 rows). Same root cause as above: the
  bulk IMDb importer (`services/api/scripts/seed_bulk_imdb.py`) never
  ingested country data, only title/year/content-type. IMDb's dataset
  doesn't carry country directly — would need a `title.akas.tsv.gz` join or
  a TMDB backfill (same pattern as the genre backfill script, could be
  adapted).
- [x] ~~Known infra flakiness: Postgres, the API server, and the web dev
  server have all independently died on this machine~~ — **mitigations
  applied and DB stability verified, session 4.** Postgres exits on its own
  under Docker Desktop (confirmed via `docker logs` showing unexplained
  "received fast shutdown request" with no corresponding command). Added
  `restart: unless-stopped` to `postgres`/`pgbouncer` in
  `infra/docker/docker-compose.yml` and a `%UserProfile%\.wslconfig` memory/
  swap cap. Separately hit this exact flakiness live this session — Docker
  Desktop failed to bring up its WSL2 backend for ~35 minutes even after a
  full kill + clean relaunch + `wsl --shutdown`, needing manual attention —
  so it's a real, reproducible issue, not theoretical. Once it came back up:
  ran the **full backend test suite (498 tests, 14 deliberately deselected —
  see below) against the live DB + MinIO: 498 passed, 0 failed.** Also
  root-caused a second, unrelated hang while diagnosing this: `test_object_storage.py`
  was hanging indefinitely (not failing — genuinely blocked) because MinIO
  (`docker-compose.yml`'s `minio` service) wasn't running; starting it
  resolved it immediately. The 14 deselected tests are the deliberately
  large-scale bulk-ingestion stress tests (`test_stage_5000_*`/`test_stage_1000_*`/
  `test_stage_500_*` in `test_day7_large_scale_catalog_expansion.py` and
  `test_phase2_real_catalog_ingestion.py`) — these insert thousands of real
  rows by design and are genuinely slow, not broken; skipped only to keep
  this verification pass fast, not evidence of a problem.
  Separately, `uvicorn --reload` silently not-reloading was root-caused to a
  missing `watchfiles` dependency (fixed: `uvicorn[standard]`) — see session
  4 above, not yet stress-tested across a long multi-edit session. `next dev`
  dying mid-session is still unexplained; if the app "loses its data" or a
  page stops responding, check in order: `docker ps` (Postgres/pgbouncer
  both "Up"), `netstat -ano | grep ":8000"` and `:3000"` (both actually
  LISTENING, not just a process existing). Restart commands are in "How to
  resume" below, including a `.next` cache gotcha a previous session hit.
- [ ] **Architectural gap: several `services/api/repositories/*.py` methods
  swallow real database errors into a false-empty or false-success response**
  instead of surfacing a 5xx. Found while diagnosing why a successful-looking
  Import apply (`applied_count: 2`) briefly didn't show up on Watch History:
  `apply_user_import` and `list_history` (and ~59 other call sites across 9
  repository files, `grep -c allow_seed_fallback services/api/repositories/`)
  share a pattern — `try: <real DB work> except Exception: rollback(); if not
  config.allow_seed_fallback: raise` — else fall through to a fabricated
  "success" (`apply_user_import`, reporting an `applied_count` that doesn't
  reflect what was actually committed after the rollback) or a silent empty
  page (`list_history`, indistinguishable in the UI from "you have no watch
  history yet"). This is deliberate for the *"no DB configured at all, pure
  local dev"* case (per the code's own comments), but the exact same
  fallback fires for a *transient* failure on an otherwise-configured DB
  (a Postgres restart mid-query, a pool blip) — conflating "not configured"
  with "briefly unavailable" is the bug. Root-caused, not fixed: a proper
  fix means threading a distinct "was the failure transient vs. no-db" signal
  through ~60 call sites, which is a real architectural change, not a
  same-session quick fix. Worth a dedicated pass if this DB flakiness keeps
  recurring on this machine.
- [ ] **Minor: "Add to Watchlist"/"Add to Library" buttons don't reflect
  already-added state after a page reload.** `isSavedToWatchlist` and
  `isAddedToLibrary` on the movie/series detail pages are plain client-side
  `useState(false)`, not derived from a real check — so revisiting a title
  you've already added shows the un-added button state until you click it
  again (harmless no-op re-add, not a data bug, just a stale/misleading
  label). Pre-existing pattern for the watchlist button; the new Library
  button follows the same shape for consistency. A real fix needs the
  detail page to check current state on load (no obvious existing endpoint
  returns "is this title in my watchlist/library" directly — would need a
  small new one, or a client-side check against the already-fetched
  watchlist/library lists). Not fixed this session — cosmetic, not data
  loss or fabrication.

## Test residue in the dev account

While verifying the fixes above, real test data was created under the `dev`
user's own account (not the shared catalog — this is isolated per-user data,
unlike last session's catalog pollution, so it's harmless to leave, but worth
knowing about): a "Test Club" and "Neo-Noir Society" watch club, an "Audit
Test Challenge", and 6 watch-history entries from the Import wizard test
(Dune: Part Two, Blade Runner 2049, Oppenheimer, Severance, Arrival,
Interstellar). Delete these from the UI if you want the dev account clean,
or leave them — they don't affect anyone else.

**Session 3 additions:** 4 more watch-history entries (Parasite ×2, The
Grand Budapest Hotel ×2 — duplicated because the file-upload verification
was run twice across an environment restart), "100 Days Love Story" in both
the Watchlist and the Personal Library, an "A24 Modern Classics" empty
collection, and one Pick Room ("Movie Night Ballot", 2 nominees, 1 vote
cast). Same as above — isolated to the dev account, harmless to leave.

## How to resume the dev environment

```bash
# 1. Postgres + pgbouncer (check docker ps first — it may already be up)
docker compose -f infra/docker/docker-compose.yml up -d postgres pgbouncer

# 2. API server (port 8000) — now goes through infra/scripts/run_api_dev.py,
# which sets the Windows event-loop policy before uvicorn starts (see
# session 4's --reload fix below). --reload is on by default; pass
# --no-reload to run without it.
cd C:/Desktop/flutter_projects/CineVault
python infra/scripts/run_api_dev.py --port 8000

# 3. Web app (port 3000) — check first with: netstat -ano | grep ":3000"
cd apps/web && npm run dev
```

Always verify with a real request after starting, not just "the process
exists" — `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/titles`
and the same for `:3000`. This session found both the API and the web dev
server silently dead (process gone, port not LISTENING) with no error
visible in whatever terminal you last looked at.

**uvicorn `--reload`** was flaky on this Windows machine — it sometimes
logged "Reloading..." but never actually spawned a new worker (no `Started
server process [PID]` line ever appeared), silently continuing to serve
stale code, or the whole process disappeared later with nothing logged.
**Session 4 root-caused this:** `watchfiles` (the reliable file-watcher
`uvicorn[standard]` is supposed to provide) wasn't actually installed, so
`--reload` was silently running on Python's polling-based `StatReload`
fallback the entire time. Fixed by pinning `uvicorn[standard]` in
`requirements.txt` and launching via `infra/scripts/run_api_dev.py` (also
sets `WindowsSelectorEventLoopPolicy` before uvicorn's reload supervisor
starts — doing this inside `main.py` itself would be too late). Not yet
stress-tested across a long multi-edit session — if it's still unreliable,
check for the `Started server process [PID]` line after every reload; if
missing, `taskkill //IM python.exe //F` and restart clean.

**`next dev` + a killed/crashed process → corrupted `.next` cache.** If the
web server was killed ungracefully (crash, `taskkill`, a previous session
ending abruptly) and the next `npm run dev` serves `500`s with a console
error like `TypeError: __webpack_modules__[moduleId] is not a function`,
the `.next` build cache is corrupted, not the code. Fix:
```bash
taskkill //IM node.exe //F   # clear every stray node process — Next can
                              # silently keep an old server bound to :3000
                              # while a new one binds :3001, serving stale
                              # content from the wrong process
cd apps/web && rm -rf .next && npm run dev
```
