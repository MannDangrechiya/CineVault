# CineVault OS — Release Notes v1.0.0

**Release Version:** `1.0.0`  
**Release Date:** 2026-08-16  
**Status:** General Availability (Release Candidate Validated)  

---

## 1. Product Overview

CineVault OS is an authoritative, privacy-first, self-hostable entertainment operating system and personal media catalog. It unifies canonical global cinema and television metadata, robust personal library tracking, event-based watch history, explainable recommendations, and AI assistance under strict data governance and security guarantees.

---

## 2. Major Capabilities

### 2.1. Canonical Catalog & Data Foundation (CAT-1)
- Strict relational hierarchy separating **Titles**, **Editions** (e.g. Director's Cut, Theatrical), and **Releases** (Theatrical, Digital, Physical, Festival).
- First-class TV series modeling: **Series** $\rightarrow$ **Seasons** $\rightarrow$ **Episodes** $\rightarrow$ **Regional Episode Orders**.
- Rich relational metadata: Cast & Crew with billing order and roles, Studios, Production Companies, Networks, Distributors, Content Certifications, Awards, Festivals, Universes, and Franchises with chronological/narrative viewing orders.
- Streaming availability engine tracking regional provider offers, monetization types (Subscription, Free, Rent, Buy, Ads), validity windows, and price metadata.

### 2.2. Multilingual Search & Discovery
- High-performance search indexed across canonical titles, original titles, aliases, transliterated names, people, and franchises.
- Native multi-script support for Latin, East Asian (CJK / Korean Hangul / Japanese Kanji & Kana), and Indic scripts (Devanagari).
- Comprehensive faceted filtering by release year, country of origin, genres, themes, and content types.

### 2.3. Personal Media Library & Watch History (CAT-2)
- Zero-leakage personal user library managing Watchlist, Watched, Currently Watching, Completed, Dropped, Plan to Watch, and Favorites.
- Append-only, immutable watch event logging with timestamps, progress percentages, device metadata, and rewatch cycle tracking.
- Dynamic user dashboard computing lifetime watch hours, completion rates, country/language distributions, monthly velocity, and rating distributions.
- User-authored ratings (1–10 scale), notes, and markdown reviews with spoiler flags.

### 2.4. Recommendation Engine
- Layered multi-attribute recommendation engine blending content similarity (genres, themes, directors, cast) with learned personal taste profile vectors.
- Cold-start preference onboarding for new users.
- Maximal Marginal Relevance (MMR) diversity reranking to avoid echo-chamber recommendations.
- Seen-title exclusion and negative preference penalty filters.
- Factually grounded, deterministic explanations for every recommended item.

### 2.5. AI Assistant & Security Governance
- Vendor-agnostic natural language conversational assistant with pluggable providers (OpenAI, Google Gemini, and resilient offline fallback).
- **Non-authoritative proposal staging:** AI cannot directly mutate canonical catalog records or merge identities; all proposals stage to `quality.ai_proposal_staging` for curator review.
- Multi-layer prompt injection defense neutralizing 11 attack families, redacting PII, and encapsulating untrusted external payloads within strict data boundaries.

### 2.6. Offline-First Library & Synchronization
- Local SQLite / Drift storage models on client devices for complete offline library access.
- Outbox mutation queuing with client-generated UUIDv7 timestamps for idempotency.
- Reliable sync protocol (`/v1/sync/push` and `/v1/sync/pull`) with delta change detection and server reconciliation.

### 2.7. Data Ingestion & Quality Control Room
- Multi-provider ingestion pipeline (KOBIS, TVDB, TMDB, AniList, MyAnimeList, Wikidata) with licensing verification gates.
- Multi-level identity resolution (External IDs, Canonical UUIDs, Multi-signal deterministic matching, and Transliteration matching).
- Quarantine triage and curator reconciliation tools for resolving metadata conflicts with full field-level provenance tracking.

---

## 3. Supported Clients

| Client | Platform | Framework / Engine | Production Readiness |
|---|---|---|:---:|
| **Web Portal** | Web / Desktop Browser | Next.js 15 (App Router, Server Components) | **READY** |
| **Mobile & Desktop** | Android, iOS, Windows, macOS, Linux | Flutter 3.12+ (Drift SQLite, Riverpod, GoRouter) | **READY** |
| **HTTP / REST API** | Cross-platform | FastAPI (OpenAPI 3.1, OpenAPI JSON/Redoc) | **READY** |

---

## 4. Security, Privacy & Operations

- **Authentication:** Keycloak OIDC with PKCE S256, secure HTTP-only session cookies on Web, and strict RS256 JWT signature verification.
- **Privacy & GDPR:** Right to Erasure implementation with irreversible field zeroing, export data portability (JSON/CSV), and tamper-evident deletion logging.
- **Observability:** OpenTelemetry-compatible W3C traceparent context, Prometheus metrics exposition (`/v1/observability/metrics`), and vendor-neutral signal router (Audit, Security, Business, Quality, System).
- **Disaster Recovery:** Automated backup manifests with SHA-256 integrity verification, recovery runbooks, and restore verification gates meeting RPO < 5 min and RTO < 1 hr.

---

## 5. Production vs. Development Configuration

| Feature / Setting | Development Profile (`local_development`) | Production Profile (`production`) |
|---|---|---|
| **Catalog Fallback** | Allowed (10 baseline seed titles when DB empty) | **FORBIDDEN** (Requires live PostgreSQL) |
| **Database Pooler** | PgBouncer local transaction pool (`6432`) | PgBouncer managed cluster with TLS |
| **JWT Verification** | Permissive test token validation permitted | **STRICT RS256 signature verification only** |
| **TLS / HTTPS** | Plaintext allowed for local ports | **STRICT TLS Required** |
| **Debug Mode** | Active (`DEBUG=true`) | **DISABLED (`DEBUG=false`)** |
| **Default Secrets** | Dev secrets permitted in `.env.local` | **BLOCKED (Startup auditor halts on dev secrets)** |

---

## 6. Known Non-Blocking Maintenance Items

The following items have been verified as non-blocking for the v1.0.0 release:

1. **Next.js Edge Runtime Crypto Warning:**
   - *Detail:* `./src/lib/auth/session.ts` imports Node.js `crypto` at build time.
   - *Impact:* Generates a build warning in Next.js Edge Runtime. The build succeeds and server-side rendering is unaffected.
   - *Target:* Refactor to `globalThis.crypto.subtle` during scheduled v1.1 maintenance.

2. **SQLAlchemy UTC Timestamp Deprecation Warnings:**
   - *Detail:* Test logs show `datetime.datetime.utcnow()` deprecation notices in Python 3.12.
   - *Impact:* Non-breaking warnings emitted during test executions.
   - *Target:* Migrate to `datetime.datetime.now(datetime.timezone.utc)` during routine dependency update.

---

## 7. Rollback Plan

In the event of an operational anomaly in production:
1. Revert application containers to previous immutable image tag.
2. In the event of schema rollback, restore PostgreSQL snapshot from the pre-deployment backup manifest (`backup_manager.get_backup_manifest()`).
3. Flush Valkey cache keys (`valkey-cli FLUSHDB`) to eliminate stale cache items.
