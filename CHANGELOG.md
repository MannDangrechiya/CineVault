# Changelog

All notable changes to CineVault OS are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
