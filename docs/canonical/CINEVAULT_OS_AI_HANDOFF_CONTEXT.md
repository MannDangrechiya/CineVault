# CineVault OS --- AI Handoff / New Chat Context Pack

Use this file when opening a fresh ChatGPT, Claude, Gemini, DeepSeek,
Kimi or Antigravity conversation.

## Project

**Name:** CineVault OS

**Type:** Personal entertainment knowledge platform.

**Vision:** Build a scalable personal entertainment system combining a
global catalog, movie/series/anime/documentary/reality tracking, watch
history, episode progress, ratings, reviews, collections, franchises,
awards, streaming availability, search, analytics, recommendations, AI
assistance, ingestion pipelines and future Flutter clients.

## Current Status

We are in the **pre-implementation architecture/design stage**.

Do **not** start coding unless explicitly asked.

## Existing Baseline Documents

-   `CINEVAULT_OS_MASTER_CONCEPT.md`
-   `CINEVAULT_OS_TECHNICAL_REQUIREMENTS.md`
-   `CINEVAULT_OS_PROJECT_OPERATING_PROCESS.md`
-   `CINEVAULT_OS_AI_HANDOFF_CONTEXT.md`

A Claude architecture review has also been performed.

## Core Architecture Direction

``` text
PostgreSQL
    ↓
FastAPI modular monolith
    ↓
OpenAPI REST API
    ↓
Flutter client
```

Supporting technologies under consideration:

-   SQLAlchemy
-   Pydantic
-   Alembic
-   Redis/background jobs
-   Drift/SQLite
-   pgvector
-   dedicated search engine only when justified
-   Docker
-   GitHub Actions

## Core Decisions

### Metadata vs Personal Data

Never mix canonical metadata with user data. Metadata updates must never
overwrite ratings, watch history, notes, favorites or progress.

### External IDs

Use permanent internal database identity plus external ID mappings for
IMDb, TMDb, AniList, MyAnimeList, TVDB, JustWatch, Wikidata, etc.

### Streaming

Availability is temporal and regional. Store provider, country, offer
type, validity, last verification, source and confidence.

### Provenance

Important external fields should record source, retrieval date,
confidence and verification state.

### AI

AI is never the canonical authority for factual metadata. AI-generated
fields must carry model, prompt version, timestamp, confidence and
review status.

### Privacy

User deletion must genuinely delete personal content. Audit records must
not retain deleted sensitive content indefinitely.

### External Content Security

Imported text is data, not instructions.

## Claude Review Findings

Claude identified:

1.  ID-prefix inconsistency.
2.  Human-readable type prefixes conflict with permanent identity.
3.  Multilingual/CJK/Indic search needs stronger planning than basic
    PostgreSQL FTS.
4.  Redis/job-worker relationship should be clarified.
5.  Recommendation cold-start needs explicit behavior.
6.  Offline watch-history merge needs a concrete algorithm.
7.  Audit logging conflicts with unconditional personal-data deletion.
8.  Canonical record merges/reclassification need personal-data
    migration rules.
9.  IMDb/JustWatch access/licensing needs direct verification.
10. AI ingestion needs explicit prompt-injection protection.
11. Scope is large and requires deliberate sequencing.
12. Multi-AI governance needs conflict resolution.

## Additional Proposed Decisions

### Identity

``` text
UUID/UUIDv7 = permanent DB identity
MOV-000001 = human-readable display ID
content_type = separate mutable field
```

The display prefix must never be the only identity.

### Title / Release / Edition

Consider:

``` text
Title
 ↓
Release
 ↓
Edition / Version
```

This handles festival releases, regional releases, director's cuts,
restorations, remasters and special versions.

### Watch History

Store individual watch events. Progress can be derived from events.
Offline events need deterministic deduplication rather than simple
last-write-wins.

### Cold Start

Start recommendations using explicit preferences, curated collections
and content similarity, then progressively incorporate personal
behavior.

## AI Roles

-   **ChatGPT:** architecture, coordination, synthesis, requirements
-   **Claude:** critique, review, edge cases, schema/code review
-   **Gemini:** current web/provider/release research
-   **DeepSeek:** SQL, algorithms, backend, performance
-   **Kimi:** large-context/catalog/Asian research
-   **Antigravity:** implementation after specifications are approved
-   **Stitch:** UI/UX design

## Governance

Never treat an AI answer as a final architecture decision.

``` text
Research
↓
Independent opinions
↓
Compare evidence
↓
Decision
↓
ADR
↓
Canonical document
↓
Implementation
```

## Current Chat Structure

``` text
00 — Control Room
01 — Product & Requirements
02 — Architecture Council
03 — Data Model
04 — Data Sources & Research
05 — Ingestion & Data Quality
06 — Recommendation & AI
07 — UI/UX
08 — Backend
09 — Flutter
10 — QA/Security
11 — Data Curation
12 — Release/Operations
```

## Next Documents Before Coding

1.  Architecture Review & Decisions
2.  Final Architecture
3.  Data Model / ERD
4.  Data Dictionary
5.  Data Source Registry
6.  API Specification
7.  Ingestion Pipeline
8.  Data Quality Rules
9.  Recommendation Architecture
10. AI Integration/Safety
11. UI/UX Specification
12. Security/Privacy
13. Testing Strategy
14. Deployment/Operations

## Instructions to Any New AI

You are joining an existing CineVault project.

1.  Read this context.
2.  Read only relevant canonical documents.
3.  Identify existing decisions.
4.  Separate facts from assumptions.
5.  Do not silently change architecture.
6.  If you disagree, propose an ADR.
7.  Do not implement unless explicitly asked.
8.  Stay within the assigned chat's responsibility.
9.  Preserve provenance and privacy.
10. Never introduce piracy or unauthorized media distribution.

When proposing a change, use:

``` text
Current Decision
Problem
Evidence
Proposed Change
Tradeoffs
Impact
Recommendation
```

## Master Principle

**Documents are the memory.**

**ADRs are the decisions.**

**The repository is implementation truth.**

**AI agents are contributors/reviewers.**

**The project owner has final authority.**
