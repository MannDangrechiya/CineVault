# CineVault OS --- Technical Requirements & Architecture Specification

**Document type:** Technical Requirements\
**Status:** Architecture baseline --- implementation phases
intentionally excluded\
**Companion document:** `CINEVAULT_OS_MASTER_CONCEPT.md`

------------------------------------------------------------------------

## 1. Technical Objective

Build a scalable entertainment data platform whose canonical data layer
can grow from thousands to potentially millions of title-related records
without redesign.

The architecture must support:

-   relational metadata
-   knowledge-graph-like relationships
-   personal user data
-   temporal streaming availability
-   search
-   recommendations
-   analytics
-   AI integrations
-   imports/exports
-   mobile/web clients
-   future multi-user support

------------------------------------------------------------------------

# 2. Recommended Stack

## Primary

  ----------------------------------------------------------------------------
  Layer                   Recommended Technology   Purpose
  ----------------------- ------------------------ ---------------------------
  Database                PostgreSQL               Canonical relational data

  Backend                 Python + FastAPI         REST API / business logic

  ORM                     SQLAlchemy 2.x           Database access

  Validation              Pydantic                 API/domain validation

  Migrations              Alembic                  Schema migrations

  Search                  PostgreSQL FTS initially Search foundation

  Cache                   Redis                    Cache / queues / rate
                                                   limiting

  Background jobs         Celery or Arq            Metadata refreshes

  Object storage          S3-compatible storage    User exports / optional
                                                   media assets

  Mobile/Web/Desktop      Flutter                  Cross-platform client

  Local mobile DB         Drift/SQLite             Offline-first cache

  Auth                    OAuth2/OIDC-compatible   Authentication
                          provider or self-hosted  
                          auth                     

  API docs                OpenAPI                  Machine-readable API
                                                   contract

  Containers              Docker                   Reproducible environments

  CI/CD                   GitHub Actions           Automated tests/builds

  Observability           OpenTelemetry +          Monitoring
                          structured logging       

  Search upgrade          OpenSearch/Meilisearch   Advanced/fuzzy/high-scale
                          only when required       search

  AI layer                Provider-agnostic        LLM/recommendation
                          service                  integration
  ----------------------------------------------------------------------------

------------------------------------------------------------------------

# 3. Why PostgreSQL

PostgreSQL should be the canonical database because the project is
fundamentally relational.

It supports:

-   strong relational constraints
-   foreign keys
-   transactions
-   indexing
-   JSON/JSONB
-   arrays where appropriate
-   full-text search
-   materialized views
-   window functions
-   recursive queries
-   analytical SQL
-   extensions

PostgreSQL's native full-text search supports indexes, ranking,
highlighting and query processing, reducing the need to introduce a
separate search system immediately.

Do not prematurely introduce a distributed database.

------------------------------------------------------------------------

# 4. Database Architecture

Use a normalized relational model with carefully selected denormalized
read models.

Suggested logical schemas:

``` text
core
metadata
people
taxonomy
availability
ratings
awards
collections
franchises
user_data
recommendation
ingestion
audit
analytics
```

Logical separation is preferable to one enormous schema.

------------------------------------------------------------------------

# 5. Core Tables

Suggested initial entities:

``` text
titles
title_aliases
title_releases
title_external_ids
title_parent_relationships
seasons
episodes
people
characters
title_people
production_companies
networks
distributors
studios
countries
languages
genres
subgenres
themes
keywords
certifications
platforms
platform_offers
awards
award_categories
award_results
festivals
franchises
franchise_entries
collections
collection_items
```

------------------------------------------------------------------------

# 6. User Tables

``` text
users
user_profiles
user_title_status
user_watch_events
user_episode_progress
user_ratings
user_reviews
user_notes
user_tags
user_favorites
user_collections
user_collection_items
user_preferences
user_devices
```

Do not store personal fields directly inside `titles`.

------------------------------------------------------------------------

# 7. Ingestion Tables

``` text
data_sources
source_credentials
ingestion_jobs
ingestion_runs
ingestion_items
raw_source_records
normalized_records
conflicts
merge_candidates
field_provenance
```

This creates a safe pipeline between external APIs and production data.

------------------------------------------------------------------------

# 8. Audit Tables

Every important mutation should be auditable.

``` text
audit_events
metadata_change_log
availability_change_log
user_data_change_log
```

Store:

-   who/what changed it
-   when
-   previous value
-   new value
-   source
-   reason
-   request/job ID

For sensitive user data, avoid storing unnecessary copies.

------------------------------------------------------------------------

# 9. Stable IDs

Use UUID/ULID internally or another collision-safe permanent ID
strategy.

Readable external IDs can still exist:

``` text
MOV-000001
SER-000001
ANI-000001
```

Recommendation:

-   database primary key: UUID/UUIDv7 or equivalent
-   human-readable identifier: separate unique field

Never make a human-readable sequential ID the only primary key.

------------------------------------------------------------------------

# 10. External IDs

Create a generic mapping:

``` text
title_external_ids
------------------
title_id
source
external_id
is_primary
url
last_verified
```

This allows new providers to be added without altering `titles`.

Example sources:

-   imdb
-   tmdb
-   anilist
-   myanimelist
-   tvdb
-   justwatch
-   wikidata

------------------------------------------------------------------------

# 11. Release Model

Do not use one `release_date` for everything.

Use:

``` text
title_releases
--------------
title_id
release_type
country
date
territory
platform
source
```

Release types:

-   festival
-   world_premiere
-   theatrical
-   television
-   streaming
-   digital_purchase
-   digital_rental
-   physical
-   re_release
-   season
-   episode

------------------------------------------------------------------------

# 12. Availability Model

Use temporal offers:

``` text
platform_offers
----------------
title_id
platform_id
country
offer_type
quality
language
subtitle_languages
url
valid_from
valid_until
last_verified_at
source_id
confidence
status
```

Offer types:

-   subscription
-   rent
-   buy
-   free
-   free_with_ads
-   broadcast
-   physical

Availability must be region-specific.

------------------------------------------------------------------------

# 13. Search Requirements

### Minimum

-   exact title search
-   prefix search
-   alias search
-   original-title search
-   person search
-   genre filter
-   country filter
-   language filter
-   year filter

### Advanced

-   typo tolerance
-   transliteration
-   Unicode search
-   weighted fields
-   relevance ranking
-   phrase search
-   synonym handling

Start with PostgreSQL FTS and trigram indexing.

Introduce a dedicated search engine only after measured requirements
justify it.

------------------------------------------------------------------------

# 14. Multilingual Search

The system must support:

-   Unicode
-   original scripts
-   transliteration
-   alternate titles
-   English titles
-   localized titles

Example:

``` text
Kimi no Na wa
君の名は。
Your Name
```

All should resolve to the same title entity.

------------------------------------------------------------------------

# 15. API Architecture

Use REST initially.

Base:

``` text
/api/v1/
```

Example endpoints:

``` text
GET    /titles
GET    /titles/{id}
POST   /titles
PATCH  /titles/{id}

GET    /search
GET    /people/{id}
GET    /franchises/{id}
GET    /collections/{id}

GET    /user/library
POST   /user/library/{title_id}
PATCH  /user/library/{title_id}

GET    /user/history
POST   /user/history

GET    /user/recommendations
GET    /availability/{title_id}
```

Use OpenAPI as the contract.

------------------------------------------------------------------------

# 16. API Rules

All endpoints must have:

-   request validation
-   response schemas
-   authentication where needed
-   authorization
-   pagination
-   filtering
-   sorting
-   structured errors
-   correlation/request IDs
-   rate limiting
-   logging

Never return unrestricted database models directly.

------------------------------------------------------------------------

# 17. Pagination

Use cursor pagination for large datasets.

Offset pagination can remain for small administrative queries.

Avoid:

``` text
?page=500000
```

for large production tables.

------------------------------------------------------------------------

# 18. Caching

Redis may cache:

-   popular searches
-   title details
-   platform catalogs
-   recommendations
-   configuration
-   API responses

Do not cache personal/private data without clear invalidation rules.

------------------------------------------------------------------------

# 19. Background Jobs

Use a worker system for:

-   metadata refresh
-   availability refresh
-   award refresh
-   new release discovery
-   duplicate detection
-   recommendation recalculation
-   analytics aggregation
-   export generation

Jobs must be:

-   idempotent
-   retryable
-   observable
-   rate-limit aware

------------------------------------------------------------------------

# 20. Ingestion Pipeline

Required flow:

``` text
External Source
      ↓
Raw Record
      ↓
Schema Validation
      ↓
Normalization
      ↓
Identifier Matching
      ↓
Duplicate Detection
      ↓
Conflict Resolution
      ↓
Human/Rule Approval
      ↓
Canonical Database
      ↓
Search Index / Read Models
```

Never allow an external API response to overwrite production records
blindly.

------------------------------------------------------------------------

# 21. Data Source Registry

Create a registry containing:

-   provider
-   API/dataset
-   license
-   attribution requirement
-   commercial use allowed?
-   redistribution allowed?
-   rate limit
-   update frequency
-   authentication
-   regions
-   fields available
-   reliability
-   last reviewed

This is mandatory because APIs and licensing terms can change.

------------------------------------------------------------------------

# 22. Current Source Strategy

### TMDb

Useful for:

-   movie metadata
-   TV metadata
-   people
-   images
-   genres
-   translations

Its current API documentation describes movie/TV/person/image APIs and
rate limiting; API terms must be accepted before obtaining credentials.

### IMDb

Useful as a high-value metadata/rating source where licensing permits.

IMDb currently provides licensed bulk datasets/API products through AWS
Data Exchange. Its documentation describes stable title/name IDs,
versioned datasets and daily updates.

Do not assume IMDb data is free for arbitrary redistribution.

### JustWatch

Useful for legal streaming/VOD availability.

Current partner documentation describes country-specific offers and
frequent updates.

Treat this as a licensed/partner integration, not as a scraping target.

### AniList / MyAnimeList

Useful for anime-specific metadata and community data.

Anime records should have anime-native identifiers rather than forcing
all anime metadata through movie/TV schemas.

### Official Sources

Use official studio, distributor, festival and award sources for:

-   release announcements
-   awards
-   festival results
-   official availability
-   corrections

------------------------------------------------------------------------

# 23. Data Quality

Every external field should ideally carry provenance.

Example:

``` text
field: runtime_minutes
value: 142
source: tmdb
retrieved_at: 2026-08-08T...
confidence: high
```

When sources disagree:

``` text
Source A: 142
Source B: 140
Source C: 142
```

do not silently overwrite.

Create a conflict record.

------------------------------------------------------------------------

# 24. Confidence System

Suggested:

``` text
HIGH
MEDIUM
LOW
UNKNOWN
CONFLICT
```

Rules can be source-specific.

Example:

Official festival result \> reputable secondary article \> community
edit.

Do not blindly assume one provider is always correct.

------------------------------------------------------------------------

# 25. Recommendation Architecture

Use a hybrid system.

``` text
Candidate Generation
        ↓
Hard Filters
        ↓
Content Similarity
        ↓
Personal Taste
        ↓
Context
        ↓
Ranking
        ↓
Explanation
```

Possible scoring:

``` text
score =
  content_similarity
+ personal_preference
+ genre_affinity
+ director_affinity
+ actor_affinity
+ novelty
+ availability
+ context_fit
- repetition_penalty
```

Weights must be configurable.

------------------------------------------------------------------------

# 26. Embeddings / Vector Search

Do not start with a vector database automatically.

Initial option:

-   PostgreSQL + pgvector

Potential embeddings:

-   title synopsis
-   themes
-   genres
-   user review
-   keywords

Vector similarity can complement, not replace, structured filtering.

------------------------------------------------------------------------

# 27. AI Architecture

Create a provider abstraction:

``` text
AIProvider
├── OpenAI
├── Gemini
├── Claude
├── DeepSeek
└── Other
```

The application should not depend on one model vendor.

AI tasks:

-   natural-language search parsing
-   recommendation explanation
-   taste analysis
-   metadata conflict assistance
-   summarization
-   classification
-   tag generation
-   collection generation

AI must not be the canonical source for factual metadata.

------------------------------------------------------------------------

# 28. AI Safety / Reliability

AI-generated fields must be marked:

``` text
ai_generated = true
model
prompt_version
generated_at
confidence
review_status
```

No high-impact metadata should be automatically published solely because
an LLM generated it.

------------------------------------------------------------------------

# 29. Flutter Architecture

Recommended:

``` text
Flutter
├── Presentation
├── Application
├── Domain
├── Data
│   ├── Remote
│   └── Local
└── Core
```

Use a clean/feature-oriented architecture.

Potential state management:

-   Riverpod

Potential networking:

-   Dio

Potential local database:

-   Drift

Potential serialization:

-   json_serializable / freezed where useful

The exact package choices should be locked only after a small technical
spike.

------------------------------------------------------------------------

# 30. Offline-First

The app should remain useful without a network connection.

Local storage should support:

-   library
-   watch status
-   ratings
-   notes
-   recent searches
-   cached title metadata

Sync strategy:

``` text
Local Change
   ↓
Outbox
   ↓
API
   ↓
Server
   ↓
Conflict Resolution
   ↓
Acknowledgement
```

Never assume the device and server are always online.

------------------------------------------------------------------------

# 31. Sync Conflicts

For personal data:

-   user changes should not silently disappear.

Potential strategy:

-   last-write-wins for simple preferences
-   event-based merge for watch history
-   explicit conflict UI for conflicting ratings/notes

------------------------------------------------------------------------

# 32. Security

Minimum requirements:

-   TLS
-   secure password handling if passwords exist
-   OAuth/OIDC where appropriate
-   refresh-token rotation
-   encrypted secrets
-   server-side authorization
-   least privilege
-   input validation
-   SQL injection protection
-   rate limiting
-   audit logging
-   secure file exports
-   backup encryption

Never store API keys inside the Flutter application.

------------------------------------------------------------------------

# 33. Privacy

Personal data includes:

-   watch history
-   ratings
-   notes
-   preferences
-   potentially location/device data

Therefore:

-   private by default
-   exportable
-   deletable
-   minimal collection
-   clear retention policies

------------------------------------------------------------------------

# 34. Backups

Recommended:

-   automated PostgreSQL backups
-   point-in-time recovery where available
-   encrypted backup storage
-   periodic restore tests

A backup that has never been restored is not considered proven.

------------------------------------------------------------------------

# 35. Observability

Use:

-   structured logs
-   request IDs
-   job IDs
-   metrics
-   traces
-   error tracking

Track:

-   API latency
-   error rate
-   ingestion failures
-   provider failures
-   stale availability data
-   queue backlog
-   database performance

------------------------------------------------------------------------

# 36. Testing

### Unit

-   domain logic
-   scoring
-   validation
-   parsers

### Integration

-   database
-   API
-   ingestion
-   external provider adapters

### Contract

-   OpenAPI
-   provider adapters

### End-to-end

-   search
-   mark watched
-   episode progress
-   rating
-   recommendation

### Data tests

-   duplicate detection
-   foreign key integrity
-   orphan records
-   invalid IDs
-   conflicting metadata

------------------------------------------------------------------------

# 37. CI/CD

GitHub Actions should run:

``` text
lint
format
type-check
unit-tests
integration-tests
migration-check
security-check
build
```

No production deployment if required checks fail.

------------------------------------------------------------------------

# 38. Environment Strategy

Separate:

``` text
local
development
staging
production
```

Never use production credentials locally.

------------------------------------------------------------------------

# 39. Configuration

Use environment variables/secrets for:

-   database URL
-   Redis URL
-   API keys
-   OAuth secrets
-   AI provider keys
-   storage credentials

Maintain `.env.example`.

Never commit real credentials.

------------------------------------------------------------------------

# 40. API Versioning

Use:

``` text
/api/v1/
```

Breaking changes should create a new version.

Do not break mobile clients silently.

------------------------------------------------------------------------

# 41. Database Migration Rules

Every schema change must have:

-   migration
-   rollback strategy where feasible
-   compatibility considerations
-   test coverage

Never edit production schema manually without a migration record.

------------------------------------------------------------------------

# 42. Performance Targets

Initial targets:

-   common title lookup: \<200 ms server-side under normal load
-   common search: \<300 ms
-   personal library page: \<300 ms
-   recommendation response: \<1--2 seconds when cached/precomputed
-   background ingestion should never block user requests

Targets should be measured, not assumed.

------------------------------------------------------------------------

# 43. Scalability

Expected scale:

### Level 1

10,000 titles

### Level 2

100,000 titles

### Level 3

1,000,000+ title/episode/relationship records

### Level 4

Multi-user platform

The architecture should scale primarily through:

-   indexes
-   query optimization
-   caching
-   read models
-   background jobs
-   partitioning only when justified

Do not prematurely introduce microservices.

------------------------------------------------------------------------

# 44. Monolith First

Recommended backend:

``` text
FastAPI modular monolith
```

Not:

``` text
20 microservices
```

Split services only when there is a measurable operational reason.

Potential future services:

-   ingestion
-   search
-   recommendation
-   notification
-   AI gateway

------------------------------------------------------------------------

# 45. Search Engine Evolution

Stage A:

PostgreSQL FTS + trigram.

Stage B:

pgvector for semantic similarity.

Stage C, only if necessary:

OpenSearch / Elasticsearch / Meilisearch.

Search architecture must allow replacement without changing the core
title model.

------------------------------------------------------------------------

# 46. Export Formats

Required:

-   CSV
-   JSON
-   Excel
-   Markdown

Future:

-   SQLite
-   JSONL
-   API export

Personal data should always remain portable.

------------------------------------------------------------------------

# 47. Import Formats

Support:

-   CSV
-   JSON
-   Excel
-   external watch-history exports where legally and technically
    possible

Importer should map fields through an explicit mapping layer.

------------------------------------------------------------------------

# 48. Data Validation

Validation categories:

### Schema validation

Correct types.

### Referential validation

IDs exist.

### Semantic validation

Example:

Episode runtime should not normally be 800 minutes.

### Cross-field validation

Example:

A series with zero seasons should be flagged.

### Source validation

External ID should match expected format.

------------------------------------------------------------------------

# 49. Duplicate Matching

Use deterministic matching first:

1.  External ID
2.  Canonical ID

Then probabilistic matching:

-   normalized title
-   year
-   country
-   runtime
-   director

Return:

``` text
AUTO-MATCH
REVIEW
NO MATCH
```

Never merge uncertain records automatically.

------------------------------------------------------------------------

# 50. Data Refresh Strategy

Each source adapter should expose:

``` text
discover()
fetch()
normalize()
validate()
compare()
apply()
```

Every refresh should create an ingestion run.

------------------------------------------------------------------------

# 51. Rate Limiting

Every external provider adapter must have:

-   provider-specific rate limit
-   retry policy
-   exponential backoff
-   429 handling
-   timeout
-   circuit breaker where appropriate
-   request logging

TMDb's current documentation notes upper request limits and asks clients
to respect HTTP 429 responses.

------------------------------------------------------------------------

# 52. Provider Abstraction

Never spread TMDb/IMDb/JustWatch-specific code throughout the
application.

Use:

``` text
providers/
  tmdb/
  imdb/
  justwatch/
  anilist/
  myanimelist/
  wikidata/
```

Each adapter maps provider data into internal canonical models.

------------------------------------------------------------------------

# 53. Legal / Licensing Requirements

Create a `DATA_SOURCE_REGISTRY.md`.

For each source record:

-   official URL
-   API/data product
-   license
-   attribution
-   commercial-use status
-   redistribution restrictions
-   rate limits
-   caching rules
-   required links
-   last legal review

No scraping strategy should be assumed legal merely because a webpage is
publicly accessible.

------------------------------------------------------------------------

# 54. Images / Artwork

Treat artwork separately from factual metadata.

Store:

-   image source
-   image URL/reference
-   width
-   height
-   language
-   artwork type
-   attribution
-   license
-   cache status

Do not assume an image URL grants redistribution rights.

------------------------------------------------------------------------

# 55. Content Safety / Maturity

Store maturity metadata separately by territory.

Example:

``` text
US: R
India: A
UK: 15
```

Do not assume one rating applies globally.

------------------------------------------------------------------------

# 56. Accessibility

Flutter UI should eventually support:

-   screen readers
-   scalable text
-   high contrast
-   keyboard navigation on desktop/web
-   reduced motion
-   semantic labels
-   accessible checkbox controls

------------------------------------------------------------------------

# 57. Internationalization

Application should support localization.

Database must support:

-   original titles
-   localized titles
-   localized descriptions
-   language metadata

Do not translate original titles destructively.

------------------------------------------------------------------------

# 58. Analytics Architecture

Separate operational queries from heavy analytics.

Potential:

-   PostgreSQL materialized views initially
-   scheduled aggregates
-   later warehouse if scale requires

Metrics:

-   titles watched
-   hours watched
-   rating trends
-   genre trends
-   language trends
-   country trends
-   platform usage
-   completion/drop rate

------------------------------------------------------------------------

# 59. Recommendation Evaluation

Do not judge recommendations only by intuition.

Measure:

-   click/open
-   add to watchlist
-   start watching
-   completion
-   personal rating
-   favorite
-   skip
-   hide
-   drop

These signals can improve future recommendations.

------------------------------------------------------------------------

# 60. Explainability

Every recommendation should be able to provide a reason.

Example:

> Recommended because you rated three Korean psychological thrillers
> above 9/10 and this shares the same genre, director style and
> slow-burn profile.

Never claim:

> "You will love this."

Use probabilistic language.

------------------------------------------------------------------------

# 61. Project Repository Structure

Suggested:

``` text
cinevault/
├── backend/
├── app/
├── ingestion/
├── database/
├── docs/
├── scripts/
├── tests/
├── infra/
├── data/
│   ├── raw/
│   ├── staging/
│   └── exports/
├── prompts/
├── .github/
├── docker-compose.yml
├── README.md
└── LICENSE
```

Raw data should not automatically become canonical production data.

------------------------------------------------------------------------

# 62. Documentation Requirements

At minimum:

``` text
docs/
├── PRODUCT_CONCEPT.md
├── TECHNICAL_REQUIREMENTS.md
├── ARCHITECTURE.md
├── DATA_MODEL.md
├── DATA_DICTIONARY.md
├── API_SPEC.md
├── DATA_SOURCES.md
├── INGESTION_PIPELINE.md
├── DATA_QUALITY.md
├── RECOMMENDATION_ENGINE.md
├── AI_INTEGRATION.md
├── SECURITY.md
├── PRIVACY.md
├── TESTING.md
├── DEPLOYMENT.md
├── CHANGELOG.md
└── ADR/
```

------------------------------------------------------------------------

# 63. Architecture Decision Records

Major decisions should be documented.

Example:

``` text
ADR-001 PostgreSQL as canonical database
ADR-002 FastAPI modular monolith
ADR-003 Flutter client
ADR-004 External IDs as mappings
ADR-005 Temporal streaming offers
ADR-006 PostgreSQL-first search
ADR-007 Provider abstraction
ADR-008 AI provider abstraction
```

------------------------------------------------------------------------

# 64. Excel Compatibility Requirements

Exports should preserve:

-   IDs
-   dates
-   boolean values
-   ratings
-   status
-   progress
-   URLs
-   platform regions

Recommended boolean convention:

``` text
TRUE
FALSE
```

Excel UI can convert those into checkboxes.

------------------------------------------------------------------------

# 65. Future Spreadsheet Design

Recommended sheets:

``` text
Dashboard
Master Library
Watch History
Watchlist
Ratings
Collections
Franchises
People
Platforms
Awards
Genres
Countries
Languages
Data Sources
Change Log
```

However, the spreadsheet is an export/view layer, not the canonical
database.

------------------------------------------------------------------------

# 66. Recommended Initial Technology Position

### Use now / foundation

-   PostgreSQL
-   FastAPI
-   SQLAlchemy
-   Alembic
-   Pydantic
-   Docker
-   GitHub Actions
-   Flutter
-   Drift/SQLite for local app data
-   Redis when background/cache requirements begin

### Add when justified

-   pgvector
-   OpenSearch/Meilisearch
-   object storage
-   dedicated analytics warehouse
-   message broker
-   Kubernetes

Do not introduce these merely because they are available.

------------------------------------------------------------------------

# 67. Non-Functional Requirements

The system must be:

-   scalable
-   testable
-   observable
-   secure
-   portable
-   multilingual
-   accessible
-   maintainable
-   API-first
-   provider-independent
-   AI-provider-independent
-   exportable

------------------------------------------------------------------------

# 68. Golden Architectural Rule

The system should survive replacement of any external provider.

If TMDb disappears:

the core database survives.

If JustWatch changes:

availability adapter changes.

If Claude changes:

AI adapter changes.

If Flutter changes:

API and database survive.

If PostgreSQL is eventually replaced:

canonical domain model and exports remain portable.

------------------------------------------------------------------------

# 69. Final Technical Direction

**Canonical backend:** PostgreSQL

**Application backend:** FastAPI modular monolith

**ORM:** SQLAlchemy 2.x

**Validation:** Pydantic

**Migrations:** Alembic

**Caching/jobs:** Redis + worker system when required

**Search:** PostgreSQL FTS initially, pgvector later, dedicated search
engine only when justified

**Client:** Flutter

**Offline DB:** Drift/SQLite

**API contract:** OpenAPI

**Infrastructure:** Docker + GitHub Actions

**AI:** Provider abstraction supporting multiple models

**Data ingestion:** Adapter-based, source-aware, provenance-preserving
pipeline

**Primary design:** Modular monolith + normalized relational core +
temporal availability + personal-data separation

------------------------------------------------------------------------

# 70. Technical Research References

Official sources consulted during architecture research:

-   PostgreSQL documentation --- Full Text Search
-   FastAPI documentation
-   Flutter documentation
-   TMDb API documentation
-   IMDb Developer documentation
-   JustWatch Partner API documentation

These references should be reviewed again before production integration
because API terms, supported versions, pricing, licensing and rate
limits can change.
