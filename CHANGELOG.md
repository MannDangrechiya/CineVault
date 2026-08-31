# Changelog

All notable changes to CineVault OS are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0-rc14] - 2026-08-31 (W14 — Media & Image Pipeline Completeness)

### Added
- **Canonical Media Resolver (`services/api/media_resolver.py`)**:
  - Unified normalization layer (`normalize_media_url`, `resolve_poster_url`, `resolve_backdrop_url`) resolving relative TMDB paths (`/abc.jpg` -> `https://image.tmdb.org/t/p/w500/abc.jpg`), Amazon CDN, and CineVault storage.
  - Automatically filters placeholder/stock images (Unsplash) and enforces HTTPS canonical format.
- **Provider Ingestion Media Normalization (`services/api/ingestion/adapters.py`)**:
  - TMDB, TVDB, AniList, and MyAnimeList adapters now extract and expand raw relative paths into fully qualified image URLs.
- **Showcase Artwork Database Migration (`db/migrations/V3.8__populate_canonical_showcase_artwork.sql`)**:
  - Populated verified TMDB poster and backdrop paths across showcase canonical movies and series in PostgreSQL.
- **Frontend Media Architecture (`apps/web/src/lib/media.ts`, `components/media/`)**:
  - `MediaPoster`: Standardized 2:3 aspect ratio poster component with automatic error recovery and honest cinematic SVG placeholder (zero fake artwork, zero stock photos).
  - `MediaBackdrop`: Standardized 16:9 hero backdrop component with gradient scrim overlay.
- **Dedicated Search Route (`apps/web/src/app/search/page.tsx`)**:
  - Full-featured search interface with debounced queries, content type toggles ("ALL", "MOVIE", "TV_SERIES"), popular quick search tags, and responsive `TitleCard` grid.
- **Media Resolution Unit & E2E Test Suites**:
  - `tests/test_media_url_resolution.py`: 10 unit tests covering URL normalization, TMDB path expansion, stock image rejection, and provider adapters.
  - `apps/web/e2e/test_media_image_rendering.js`: 16 browser tests verifying poster decoding (`naturalWidth > 0`), hero backdrops, poster isolation, dedicated search, and 375px mobile responsiveness.

### Changed
- **Next.js Image Whitelist (`apps/web/next.config.ts`)**:
  - Configured `remotePatterns` for `image.tmdb.org`, `m.media-amazon.com`, `cdn.cinevault.org`, `cdn.myanimelist.net`.
- **Consumer Pages Refactored**:
  - Replaced ad-hoc `<img>` elements with `MediaPoster` and `MediaBackdrop` across `movies/[id]`, `series/[id]`, `TitleCard`, `collections`, `history`, `library`, `watchlist`, `social`, `oracle`, `pick/[slug]`.

## [1.0.0-rc13] - 2026-08-30 (W13 — Web Production Release & Deployment Readiness)

### Added
- **Operational Health Probes (`services/api/routers/health.py`)**:
  - `/health/liveness`: Lightweight probe returning ISO timestamp and service status.
  - `/health/readiness`: Multi-dependency check verifying PostgreSQL via real SQL `SELECT 1`, Valkey cache, and RabbitMQ broker; returns sanitized responses with zero internal topology leakage.
  - `/health/startup`: Startup probe for container orchestrators.
- **Automated Backup & Restore Automation**:
  - Shell and PowerShell scripts for automated custom binary dumps with retention pruning (`scripts/backup_postgres.sh`, `scripts/backup_postgres.ps1`).
  - Shell and PowerShell restore scripts (`scripts/restore_postgres.sh`, `scripts/restore_postgres.ps1`).
- **Comprehensive Operator Documentation**:
  - `docs/deployment.md`: Architecture blueprint, system requirements, Docker Compose guide, non-Docker / bare-metal steps.
  - `docs/operations.md`: Daily monitoring, log inspection, log rotation, container lifecycle, and troubleshooting guide.
  - `docs/backup-recovery.md`: Operator runbook for automated backups, disaster recovery, pgvector integrity verification, and forward-only migration policy.
  - `docs/release-checklist.md`: Step-by-step pre-deployment, execution, verification, and rollback checklist.
- **Deployment Readiness & Smoke Test Suites**:
  - `tests/test_w13_deployment_readiness.py`: 10/10 tests verifying health probes, production config refusal on default secrets, CORS handling, security headers, pgvector cosine distance, and DB outage 503 safety.
  - `apps/web/e2e/test_w13_production_smoke.js`: 15/15 tests verifying homepage, catalog, search, auth session, personal vault, settings, import/export, Oracle, social, and mobile responsive layouts against Next.js standalone runner.

### Changed
- **API Service Configuration (`services/api/config.py`)**:
  - Added configurable `CORS_ALLOWED_ORIGINS` and `DOCS_ENABLED` toggles.
  - Hardened `_refuse_unsafe_defaults_outside_local_dev` validator to automatically ensure `allow_seed_fallback=False` outside `local_development`.
- **Next.js BFF API Proxy (`apps/web/src/app/api/proxy/[...path]/route.ts`)**:
  - Added support for `API_BASE_URL` alongside `NEXT_PUBLIC_API_BASE_URL` to enable server-to-server container communication.
- **Production Container Stack (`infra/docker/docker-compose.prod.yml`)**:
  - Injected `API_BASE_URL` for `nextjs-web` service.
  - Verified Caddy edge gateway routing, compression, and security headers.
- **CI Pipeline (`.github/workflows/ci.yml`)**:
  - Added `master` branch triggers for continuous integration and automated release testing.

## [1.0.0-rc12] - 2026-08-30 (W12 — Web Product Completeness & Real-World Launch Readiness)

### Added
- **Web Product Completeness Backend Integration Suite (`tests/test_w12_web_product_completeness.py`)**:
  - Catalog search & Display ID resolution across all canonical ID formats (`imdb-`, `tmdb-`, `tt`, `mov-`, `ani-`, `tv-`, `kobis-`, `tvdb-`).
  - Movie and Series detail provenance verification against real PostgreSQL catalog (~89,000 titles).
  - Complete personal vault lifecycle: Library, Watchlist, Watch Events, Ratings, Private Notes, Reviews.
  - Collections CRUD with item curation and lifecycle management.
  - Social multiplayer: Friendships, Peer Recommendations, Pick Room live voting and host-only close.
  - Import/Export data portability across 4 formats (JSON, CSV ZIP, Excel, Markdown).
  - Multi-account strict data isolation verification.
- **E2E Browser Journey Suite (`apps/web/e2e/test_w12_web_product_completeness.js`)**:
  - Journey 1: Discovery to Personal Vault (authentication, catalog browse, search, movie detail, watchlist/library toggles, all personal vault pages).
  - Journey 2: Series Episodic Tracking (series catalog, series detail navigation).
  - Journey 3: Social & Multiplayer (Social Hub, Friends, Watch Clubs).
  - Journey 4: Import & Export Hub (Import Wizard, Settings Export Hub).
  - Journey 5: Responsive & Accessibility (mobile bottom nav, slide-out drawer, Escape key dismissal, launch-ready screenshot).

### Changed
- **Search Repository (`services/api/repositories/search.py`)**: Expanded exact Display ID resolution to support all canonical ID prefix formats for comprehensive catalog lookups.
- **History Page (`apps/web/src/app/history/page.tsx`)**: Replaced `window.location.href` with `router.push('/movies')` for SPA-consistent empty state navigation.

## [1.0.0-rc11] - 2026-08-30 (W11 — Production Security & Disaster Recovery Hardening)

### Added
- **Real PostgreSQL Backup & Disaster Recovery Verification (`tests/test_phase30_backup_disaster_recovery.py`)**:
  - Live PostgreSQL backup execution using `pg_dump -F c` inside container.
  - Complete drop/loss simulation of source database.
  - Clean recovery database provisioning and binary `pg_restore` execution.
  - End-to-end integrity verification across all 6 logical schemas (`canonical`, `personal`, `social`, `quality`, `ingestion`, `audit`).
  - Restored data verification for multi-table relationships, 384-dimensional `pgvector` embeddings (`taste_vector <=> target_vector` cosine distance), and foreign key constraint enforcement.
- **Production Security Hardening & Zero-Trust Authentication (`tests/test_w11_production_security.py`)**:
  - Unauthenticated request rejection (401 Unauthorized) across all personal, administrative, and automation endpoints.
  - JWT signature verification and strict rejection of `alg=none` and dev mock tokens in staging/production mode.
  - RBAC authorization boundaries: Curator access on `/internal/v1/control-room/*` (403 for standard users); System Admin access on `/admin/*` (403 for standard and curator users).
  - IDOR immunity: personal data access exclusively bound to token `sub` claims.
  - Next.js BFF Proxy CSRF Protection: `Origin`/`Referer` header validation against `Host` on state-changing methods (`POST`, `PUT`, `PATCH`, `DELETE`).
  - Standard production security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`, `Content-Security-Policy: default-src 'self'`).
  - SQL Injection and Formula Injection defense across search and export engines.
- Canonical Documentation:
  - `docs/security.md` (Zero-trust architecture, threat modeling, and defensive controls).
  - `docs/backup-recovery.md` (Disaster recovery runbook, automated backup validation, and RPO/RTO invariants).

## [1.0.0-rc10] - 2026-08-30 (W10 — Web UX, Accessibility & Responsive Reliability)

### Added
- Integrated Playwright and axe-core to ensure responsive E2E test coverage and accessibility audits (`tests/a11y.spec.ts`).
- Semantic HTML and Accessible Labels: Migrated non-semantic `<div onClick={...}>` patterns (like the upload dropzone in `/import`) to native `<button>` tags for improved screen reader experiences.
- Universal Modals Accessibility: Attached custom `useFocusTrap` hook to all modals (dashboard, collections, movies, series, clubs, social, and import pages) preventing outside clicks or keyboard tabs while open. Added required `role="dialog"`, `aria-modal="true"`, and `aria-labelledby` semantics.
- Accessible Mobile Drawer: Enforced `role="dialog"` and `aria-hidden` attributes inside the mobile sidebar for robust native-like drawer behavior on touch and screen readers.

## [1.0.0-rc7] - 2026-08-30 (W8 — Import / Export & Personal Data Portability)

### Added
- Multi-Format Personal Data Exporter (`services/api/personal/export_service.py`):
  - **Lossless JSON v2.0**: Full relational export encompassing profile, library, watchlist, watch history, ratings, user title states, private notes, reviews, custom collections, and streaks.
  - **Relational CSV ZIP**: Structured archive containing `manifest.json`, `library.csv`, `watch_history.csv`, `ratings.csv`, `notes.csv`, `reviews.csv`, `custom_lists.csv`.
  - **Multi-Sheet Excel Workbook (`.xlsx`)**: Formatted workbook with distinct sheets for `Overview`, `Library & Watchlist`, `Watch Events`, `Ratings`, `Notes & Reviews`, `Collections`.
  - **Human-Readable Markdown (`.md`)**: Formatted document archive for offline personal reading.
- Spreadsheet Formula Injection Defense (`services/api/personal/mapping.py`):
  - Neutralizes dangerous formulas starting with `=`, `+`, `-`, `@`, `\t`, `\r` during CSV and XLSX export by prefixing with `'`.
  - Automatically unescapes safe prefixes during file ingestion.
- Four-Tier Deterministic Identity Resolution:
  - Tier 1: Canonical Title UUID match (confidence 1.0).
  - Tier 2: External Identifier / Display ID match (IMDb, TMDb, Display ID) (confidence 1.0).
  - Tier 3: Exact Canonical Title + Production Year match (confidence 0.95).
  - Tier 4: Disambiguation candidate cards with `REVIEW_REQUIRED` verdict (prevents arbitrary catalog misattributions).
- Idempotent Ingestion Engine:
  - Append-only watch history deduplicates identical event uploads within 2 minutes while preserving legitimate re-watches (ADR-003).
  - Notes, ratings, and library records deduplicated idempotently.
- Conflict Resolution Strategies:
  - `KEEP_EXISTING` (preserves existing database records).
  - `OVERWRITE` (updates database with imported records).
  - `MERGE` (fills missing attributes without wiping existing non-null fields).
- Web UI & Import Wizard (`apps/web`):
  - Interactive 3-step Import Wizard (`/import`) supporting Excel `.xlsx`, Letterboxd/Trakt CSV, JSON, and plain text notes.
  - Candidate review and disambiguation modal with 1-click candidate selection.
  - 1-click personal data export hub on `/settings` with direct download buttons for all 4 formats.
- Verification & Test Suites:
  - `test_w8_import_export.py` (7 tests, 100% pass rate).
  - Playwright E2E suite `test_w8_import_export.js` (8 tests, 100% pass rate).
  - Canonical format specification `docs/export-format.md`.

### Fixed
- Fixed Next.js `/api/proxy` endpoint routing for personal watch-events and title-states by adding dual `@personal_router` decorators in `services/api/routers/personal.py`.
- Fixed async connection lifecycle in integration tests for deterministic repeatability.

## [1.0.0-rc6] - 2026-08-30 (W7 — Social & Multiplayer Reliability)

### Added
- Flyway Migration `V3.6__harden_social_constraints.sql`:
  - Enforced pairwise friendship uniqueness via unique index `uq_friendship_pairwise` on `social.friendship (LEAST(requester_id, addressee_id), GREATEST(requester_id, addressee_id))`.
  - Added query performance indexes on `social.recommendation`, `social.pick_vote`, and `social.challenge`.
- Friendship Authorization & Lifecycle Hardening:
  - Strict self-friendship rejection (`400 Bad Request`).
  - Status mutation authorization: `ACCEPTED` requires addressee; `BLOCKED` requires participant; status downgrades from `ACCEPTED` prevented.
  - Added participant-only `DELETE /social/friendships/{id}` endpoint for friendship unlinking.
- Peer Recommendations Security (IDOR & State Machine):
  - Strict recipient-only authorization for recommendation state transitions (`ACCEPTED`, `REJECTED`, `WATCHED`, `RATED`). Non-recipients receive `403 Forbidden`.
  - Sender/recipient-only access on `GET /social/recommendations/{id}`.
  - Rejected self-recommendations (`400 Bad Request`).
- Watch Clubs & Challenges Hardening:
  - Idempotent `join_watch_club` and `join_challenge` operations preventing duplicate member rows and counter inflation.
  - Added `POST /social/clubs/{slug}/activities` endpoint for club activity stream logging.
  - Active challenge window validation: `update_challenge_progress` rejects increments on expired challenges with `400 Bad Request`.
- Pick Rooms Concurrency & Deduplication:
  - Unique voter constraint `uq_pick_vote_voter_candidate (room_id, voter_fingerprint, title_id)` ensuring atomic 1-voter-1-candidate tallying.
  - Host-only ballot closure with deterministic winner resolution.
- `test_w7_social_and_multiplayer.py` — 12 comprehensive real PostgreSQL integration tests across User A, User B, and User C (Attacker).
- Playwright Multi-User E2E suite (`node e2e/test_social_multiplayer.js`) — 10 tests across Dev and Curator browser contexts.

### Fixed
- Fixed unhandled `select` import and 404 vs 400 error handling in `routers/social.py`.
- Fixed Playwright E2E invite generation async waiting and club creation flows.

## [1.0.0-rc5] - 2026-08-30 (W6 — Recommendations + AI / Oracle Reliability)

### Added
- Targeted candidate generation across 89k+ titles in PostgreSQL: pushes down SQL filters for seed similarity (shared genres/directors), preferred genres, and release year bounds.
- Episodic watched-title exclusion policy: completed movies are excluded from candidate pools, while in-progress TV series remain eligible for continue-watching discovery.
- Seed self-exclusion: target seed titles are automatically excluded from their own "Because You Liked" and similar title recommendations.
- Enhanced personal taste scoring: integrates positive ratings (>=8), negative ratings (<=3), explicit favorites (+3), dropped penalties (-5), preferred directors, actors, and thematic keywords.
- Deterministic ranking: enforces strict tie-breaking on `(recommendation_score DESC, title_id DESC)`.
- Grounded transparent explanations: provides factually accurate matched genres, directors, actors, and seed title names without hallucination.
- AI Provider Abstraction (`AIProviderFactory`): unified adapter interface supporting Mock, OpenAI, Gemini, Groq, and Grok with free-first offline safety.
- Prompt injection defense & PII redaction (`PromptSanitizer`): neutralizes instruction overrides and redacts emails, API keys, bearer tokens, and credentials.
- CAT-6 AI proposal staging (`quality.ai_proposal_staging`): AI generated metadata updates staged for curator review with HMAC SHA-256 integrity audit logs.
- Group taste matchmaking: multi-user cosine distance consensus with mathematical mean vector aggregation.
- `test_w6_recommendations_and_ai.py` — 13 real PostgreSQL integration tests covering the complete recommendations, cold start, taste profiling, determinism, AI provider, and CAT-6 governance surfaces.
- `test_w6_recommendations_and_oracle.js` — Playwright E2E browser tests for dashboard recommendations shelf, Oracle AI chat, and group taste matchmaking.

### Fixed
- Fixed candidate generation bottleneck: replaced arbitrary 200 newest title loading with targeted SQL candidate generation across the 89,141+ catalog.
- Fixed mock provider enum casing in AI tests.
- Fixed `PersonModel`, `SeasonModel`, and `EpisodeModel` test instantiation attributes to match canonical schema.

## [1.0.0-rc4] - 2026-08-30 (W5 — Data Completeness & Ingestion Reliability)

### Added
- Source registry and licensing gates: enforced per-provider access control and data license verification before any ingestion.
- Provider normalization hardening across 6 data sources (KOBIS, TVDB, TMDB, AniList, MAL, Wikidata) — no fabricated default values (`N/A`, `Unknown`, etc.) injected into canonical records.
- 4-level identity resolution engine: exact external ID → fuzzy title match → year+type constraint → external ID cross-reference.
- Pipeline Level-1 preload failure resilience: graceful SQL fallback when cache initialization fails on large catalogs.
- Truthful ingestion run reporting: quarantine schema validation failures properly buffered to prevent foreign key errors; runs return truthful `PARTIAL` status instead of false `COMPLETED`.
- Duplicate prevention on re-ingestion: metadata updates are idempotent without creating duplicate canonical records.
- Series hierarchy ingestion: season/episode upserting handles refreshes and new episodes without duplicate rows.
- Provenance tracking and conflict handling: domain authority resolved per field, metadata conflicts persisted for curator review.
- Personal data preservation guarantee: library, watchlist, watch events, ratings, notes, and reviews remain 100% intact across catalog re-ingestion.
- Control room operational endpoints verified: health, sources, candidate review, conflicts, provenance, and trigger endpoints.
- `test_w5_data_completeness.py` — 10 real PostgreSQL integration tests covering the full data quality and pipeline reliability surface.
- `test_w5_catalog_completeness.js` — 7 Playwright E2E browser tests verifying catalog navigation, episodic explorer, personal pages, and Oracle AI interface after ingestion hardening.

### Fixed
- Fixed scaling bottleneck on 89k+ title databases: eliminated eager `length(display_id)` table scans on pipeline startup, replaced with lazy per-prefix count resolution for sub-second initialization.
- Capped `CATALOG_SNAPSHOT_LIMIT` to 5,000 for rapid initialization while providing full-fidelity SQL candidate lookups enriched with provider external IDs.
- Fixed multi-phase database flush ordering: parent rows (`raw_payload_capture`, `titles`) now flush before referencing rows (`quarantine_record`, `ingestion_items`, `title_genre`) to prevent foreign key constraint violations.
- Hardened `list_ingestion_runs` to query `IngestionRunModel` directly for truthful run statistics instead of potentially stale aggregates.

## [1.0.0-rc3] - 2026-08-30 (W4 — Series & Advanced Watch Tracking)

### Added
- Deterministic canonical sorting `(season_number ASC, episode_number ASC)` across all season and episode listings.
- `title_id` query filtering for watch events repository and `/v1/me/watch-events` / `/v1/personal/watch-events` endpoints.
- Enriched `HistoryItemResponse` schema and history repository queries with `season_number`, `episode_number`, and `episode_name`.
- Series Detail page enhancements: Continue Watching hero card, Series & Season watch progress indicators, episode watched state checkmarks, and rewatch count badges.
- History Page UI enhancement: `S{season}:E{episode}` badges and episode names for episodic watch logs.
- `test_w4_series_and_advanced_tracking.py` — 8 real PostgreSQL integration tests covering series lookups, episode watch events, status transitions, rewatch counts, streak evaluation, and user isolation.
- `test_series_watch_tracking.js` — 7 Playwright E2E browser tests for the series episodic experience.

### Fixed
- Fixed premature series completion bug where watching the first episode marked the entire multi-episode series as `COMPLETED` instead of `IN_PROGRESS`.
- Corrected user dashboard watch time calculation to include exact episodic duration instead of 0 minutes.
- Fixed React Hook ordering in `series/[id]/page.tsx` ensuring `useMemo` hooks execute unconditionally before early return branches.

## [1.0.0-rc2] - 2026-08-30 (W3 — Core Web Reliability)

### Added
- Personal CRUD endpoints: ratings, notes, and reviews now support `DELETE` operations and `title_id` filtering on list endpoints.
- Full canonical detail surface on movie and series detail pages: credits, certifications, awards, provenance, editions, streaming links, seasons/episodes browser.
- 12 new TypeScript interfaces for canonical entity types (aliases, themes, keywords, certifications, credits, companies, awards, festivals, editions, seasons, episodes, streaming links).
- `not-found.tsx` global 404 page (required by Next.js 15 App Router for production builds).
- `test_w3_core_web_reliability.py` — 302-line test suite covering 8 areas: canonical lookups, personal title state, ratings/notes/reviews CRUD, watch-event logging, user isolation, and library operations.

### Fixed
- Movie and series detail pages completely rewritten to render real data from Postgres instead of incomplete stub layouts.
- Library, watchlist, history, and collections pages hardened against empty states and real personal data.
- `test_router_title_provenance_endpoint` assertion fixed (seed data uses `original_title`, not `canonical_title`).

## [1.0.0-rc1] - 2026-08-16

### Added
- **Core Canonical Data Foundation (Phase 01–03)**: Multi-source catalog ingestion (TMDB, IMDb, KOBIS, Letterboxd, JustWatch) with merge reconciliation and provider attribution.
- **Search & Discovery Engine (Phase 04)**: Faceted catalog exploration across movies, series, anime, documentary categories with regional priority ranking.
- **Personal Library & Watch History (Phase 05–07)**: CAT-2 personal data foundation, watch event logging, custom collections, and franchises.
- **Streaming Availability & Release Calendar (Phase 08–09)**: Regional OTT streaming providers, deep-links, and future release tracking.
- **Dashboard & Taste Profiling (Phase 10–11)**: Personal analytics, viewing patterns, genre breakdowns, and dynamic taste vectors.
- **Recommendation Engine (Phase 12–13)**: Content-based, hybrid, and diversity-filtered recommendation models.
- **AI Assistant Foundation & Security (Phase 14–16)**: Prompt-injection defense, tool boundaries, streaming natural language queries.
- **Portability & Sync (Phase 17–19)**: JSON/CSV data export/import, offline-first local SQLite cache, and mutation sync outbox.
- **Cross-Platform Clients (Phase 20–21)**: Flutter mobile/desktop client and Next.js responsive web UI portal.
- **Data Curation & Control Room (Phase 22–24)**: Regional cinema curation (Indian, East Asian, European), conflict reconciliation queues, quarantine triage, and tamper-evident metadata change history.
- **Observability & Telemetry (Phase 25)**: Vendor-neutral signal router (Audit, Security, Business, Data Quality, System), W3C traceparent spans, Prometheus metric families, and health matrix.
- **Background Jobs / Queue (Phase 26)**: Asynchronous task queue supporting 8 workload types, idempotency keys, per-workload backpressure, and DLQ escalation.
- **Performance & Scale (Phase 27)**: Latency histograms (P50/P95/P99), cache-aside metrics, slow-query detector, and query budget enforcer.
- **Security Hardening (Phase 28)**: PKCE S256, SSRF URL allowlisting, 11-family prompt injection defense, upload security, CAT-2 user isolation, and security header verification.
- **Privacy & Data Lifecycle (Phase 29)**: GDPR Right to Erasure, data portability export with field suppression, retention policy evaluator, and audit record scrubbing.
- **Backup & Disaster Recovery (Phase 30)**: Backup manifests with SHA-256 integrity, restore test validity gates, RPO < 5 min and RTO < 1 hr tracking, and multi-subsystem runbooks.
- **CI/CD Automation (Phase 31)**: GitHub Actions pipelines for multi-version matrix tests, linting, SAST, web build, Flutter CI, and gated production release.
- **Release Engineering (Phase 32)**: Release manifests, environment profiles, migration verification, rollback execution plans, and SemVer enforcement.
