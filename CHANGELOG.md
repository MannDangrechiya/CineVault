# Changelog

All notable changes to CineVault OS are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
