# Changelog

All notable changes to CineVault OS are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
