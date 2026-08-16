# Changelog

All notable changes to CineVault OS are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-08-16

### Added
- **Canonical Catalog & Taxonomy Foundation**: Unified entertainment data model (CAT-1) supporting Titles, Editions, Releases, Seasons, Episodes, Regional Episode Orders, Credits, Roles, Certifications, Studios, Networks, Distributors, Awards, Festivals, Universes, and Franchises.
- **Multilingual Search & Discovery**: High-performance multi-attribute search across original titles, aliases, transliterations, and multi-script alphabets (Korean, Japanese, Indic scripts, Latin).
- **Streaming Availability & Release Calendar**: Provider offers, regional catalog mappings, pricing, validity windows, and release date separation (Theatrical, Digital, Physical, Festival).

### Security
- **Defense in Depth**: PKCE S256 authentication flow, Keycloak OIDC integration, and strict RS256 token verification.
- **API Boundary & Transport**: Ingress security headers (HSTS, CSP, X-Frame-Options, nosniff), SSRF URL allowlisting, and upload format verification.
- **Role-Based Access Control**: RBAC policies enforcing fine-grained scopes for Public, AuthenticatedUser, Curator, and SystemAdmin roles.
- **Zero Secrets in Repository**: Full environment variable substitution across all services and infrastructure manifests.

### Data
- **Controlled Ingestion Pipeline**: Ingestion engine with licensing verification gates, raw payload capture, validation, normalization, multi-signal identity resolution, and candidate staging.
- **Data Quality & Control Room**: Curator reconciliation tools, conflict queues, quarantine management, and field provenance attribution.
- **Tamper-Evident Metadata History**: Immutable change history logging with old/new deltas and SHA-256 integrity verification.

### Personal Library
- **User Foundation (CAT-2)**: Isolated personal records for Watchlist, Watched, Watching, Completed, Dropped, Planned, Favorites, Ratings, Reviews, and Notes.
- **Watch History Engine**: Immutable, event-based watch progress tracking supporting movie and episode progression, pause/resume, and rewatch cycles.
- **Personal Dashboard & Analytics**: Dynamic metrics computation including total titles, watch time, completion rates, country/language distribution, and rating distributions.

### Recommendations
- **Layered Recommendation Engine**: Cold-start heuristics, multi-attribute content similarity vectors, user taste profile affinity learning, and Maximal Marginal Relevance (MMR) diversity reranking.
- **Grounded Explainability**: Transparent, deterministic justification of recommendation rationale without LLM hallucination.

### AI
- **AI Assistant Foundation & Governance**: Vendor-agnostic AI provider abstraction (OpenAI, Gemini, resilient local fallback) with non-authoritative boundary staging proposals for human review.
- **Prompt Injection & Data Defense**: 11-family regex prompt injection protection, untrusted data payload encapsulation, and automatic PII/token redaction.

### Offline Sync
- **Client Offline Storage**: Local SQLite/Drift storage models for personal library entries and outbox mutation queues.
- **Idempotent Sync Protocol**: UUIDv7 mutation idempotency, outbox batch push (`/v1/sync/push`), and delta pull streaming (`/v1/sync/pull`) with conflict reconciliation.

### Clients
- **Flutter Mobile & Desktop**: Complete Flutter client featuring navigation shell, responsive discovery hub, title details, personal library, watch history logging, and offline sync.
- **Next.js Web Portal**: Next.js 15 App Router web application with Server Components, secure cookie session management, and responsive movie/series discovery and dashboard interfaces.

### Operations
- **Observability & Health**: Vendor-neutral signal routing (Audit, Security, Business, Data Quality, System), W3C Trace Context distributed spans, Prometheus metric endpoints, and comprehensive health probes.
- **Background Jobs & Queue**: Asynchronous task processor supporting 8 workload types, backpressure rate limiting, retry backoff, and Dead-Letter Queue (DLQ) recovery.
- **Backup & Disaster Recovery**: Cryptographically verified backup manifests, isolated restore test gates, and recovery runbooks meeting RPO < 5m and RTO < 1h.
- **Privacy & GDPR Compliance**: Full Right to Erasure workflows, field zeroing, audit scrubbing, and export portability.

### Testing
- **End-to-End Test Suite**: 544 backend tests, 33 Flutter widget/unit tests, and 20 Next.js routes verified across all 36 development phases.
- **Formal Verification**: 28/28 Completion Gates independently verified and passed.
