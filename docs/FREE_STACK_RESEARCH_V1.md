# CineVault — Free/Low-Cost Stack Research (V1)

**Status:** Research only — nothing in this document is an approved decision. Every `CANDIDATE-NEEDS-LEGAL-REVIEW` item requires an explicit owner sign-off before use; every `RECOMMENDED` item is a research conclusion, not an ADR.

**Date:** 2026-09-04
**Purpose:** Answer "what free/open-source options actually exist for each CineVault problem, and what are their real current (2026) terms?" — grounded against the existing canonical docs (`DATA_SOURCE_REGISTRY_V1.md`, `CINEVAULT_OS_MASTER_CONCEPT.md`, `CINEVAULT_OS_TECHNICAL_REQUIREMENTS.md`, `INGESTION_ARCHITECTURE_V1.md`, `INFRASTRUCTURE_ARCHITECTURE_V1.md`, `CACHE_QUEUE_INFRASTRUCTURE_SPECIFICATION_V1.md`) rather than re-deriving architecture from scratch. Produced via 4 parallel live-web-research passes (Sept 2026).

**Origin:** This followed from a discussion about whether FMHY (a link-hub of mostly piracy-adjacent resources) could help CineVault. Conclusion reached before this research: FMHY-style discovery is useful as a *resource-discovery layer* only — every candidate it (or any other discovery method) surfaces still requires independent license/ToS/reliability verification before use. Piracy-oriented resources are categorically excluded per CineVault's own product definition (not a piracy platform).

---

## 🚨 Immediate action item (independent of everything else below)

**MinIO was archived by its maintainer on GitHub Apr 25, 2026** (repo now read-only, branding pushed toward the commercial "AIStor" product, no new Docker images published since Oct 2025). `docs/storage_cdn.md` currently specifies MinIO for local dev S3 emulation. This is a live supply-chain risk, not a someday-item.

- **Replace with: SeaweedFS** (Apache-2.0, actively maintained 12+ yrs, drop-in S3-API compatible, excels at many-small-files which matches poster/backdrop caching).
- **No change needed to production**: Cloudflare R2 (already `OWNER APPROVED` per `DEC-ING-PRP-05`) is unaffected — free tier (10GB storage, 1M Class-A + 10M Class-B ops/mo, zero egress) remains generous and current.

---

## 1. Metadata & catalog data sources

Grounded against `DATA_SOURCE_REGISTRY_V1.md` (DS-01…DS-07). Does not contradict existing decisions — extends with newly-verified terms and net-new candidates.

### Comparison table

| Source | Data | License / ToS | Free tier limits | Verdict |
|---|---|---|---|---|
| TMDB | Movie/TV/person/image metadata | Non-commercial free w/ attribution; **commercial requires written license**, $149/mo under $1M revenue, negotiated above; cannot cache >6mo without re-sync; images require attribution too | ~40 req/s/IP, no hard cap | **CANDIDATE-NEEDS-LEGAL-REVIEW** (confirms existing DS-02) |
| OMDb | Movie/TV metadata, ratings, posters | **CC BY-NC 4.0 — commercial use prohibited at every tier**, incl. paid Patreon tiers. Posters resolve to real Amazon-hosted copyrighted images regardless of OMDb's own license framing | 1,000 req/day free | **AVOID / add to registry as EXCLUDED** — not currently in the registry at all |
| Wikidata | Structured entity data, cross-ID mapping | **CC0** — commercial + redistribution + persistent storage all clear | SPARQL: 60s query-time/min, 5 parallel/IP; bulk JSON dumps available | **RECOMMENDED** — best free/open foundation layer |
| DBpedia (new) | Structured Wikipedia extraction (director, cast, tags) | CC BY-SA 3.0 — commercial OK w/ attribution, **ShareAlike applies to derivatives** | No hard published cap | **CANDIDATE-NEEDS-LEGAL-REVIEW** — useful cross-check, ShareAlike needs sign-off before use beyond read-time enrichment |
| Fanart.tv (new) | High-res artwork | **Commercial use requires written consent** | No hard limit for most keys; visibility-delay tiers | **CANDIDATE-NEEDS-LEGAL-REVIEW** — obtain written commercial consent before production use |
| Kaggle "Movies Dataset" / MovieLens (new) | Bulk historical dumps | Movies Dataset inherits TMDB's restrictions (derived from TMDB, doesn't bypass license); MovieLens free for research, **commercial use needs separate written GroupLens/UMN permission** | Static download | **AVOID** as live catalog feed; fine only as offline ML/threshold-calibration corpus (already anticipated in `DATA_QUALITY_RECONCILIATION_ARCHITECTURE_V1.md`) |
| AniList | Anime/manga | **Persistent storage prohibited**; commercial apps free under $150/mo revenue; **bans "competing" list/tracker services** | 90 req/min nominal, currently throttled to ~30 req/min | **RESTRICTED** (confirms registry) — real risk: CineVault as a cataloging app may trip the "competing service" clause |
| Jikan (unofficial MAL) | MAL data via wrapper | Its own docs admit: persisting data **breaches MyAnimeList's ToS** | ~60 req/min shared | **AVOID** for persistent ingestion |
| TVmaze (new) | TV show/episode/cast data | **CC BY-SA — free for any purpose incl. commercial**, with attribution | 20 calls/10s/IP | **RECOMMENDED** as a usable-today, zero-cost secondary TV source |
| TheTVDB v4 | TV series/episode/artwork | <$50k/yr free w/ attribution (confirms registry); tiered above | Not explicitly rate-limited | **CANDIDATE** (confirms registry) |
| Anime News Network Encyclopedia | Historical anime/manga metadata | Free, mandatory attribution | 1 req/s/IP (5/5s via nodelay) | **CANDIDATE** (confirms registry) — secondary/verification only |
| JustWatch | Streaming/VOD availability | **No self-serve tier exists in 2026** — official partner contract required, scraping explicitly prohibited | N/A | **AVOID for now** — future enterprise negotiation only |
| LinkedMDB (new) | RDF-linked movie data | Was open, but **effectively dead/unmaintained** since ~2020 | N/A | **AVOID** |
| Wikimedia Commons | Film/TV images | **Per-file licensing** (CC-BY/CC-BY-SA/GFDL/public domain) — must check per image via `imageinfo` API | Generous, WMF API norms | **CANDIDATE** — requires storing per-image license metadata, not a blanket policy |

### Recommended build order

1. **Wikidata (CC0)** — identity/reference backbone, zero legal gate.
2. **TVmaze (CC BY-SA)** — usable today while TMDB/TheTVDB commercial terms are negotiated.
3. **TMDB** — proceed with commercial license negotiation (already flagged DS-02).
4. **TheTVDB** — activate at <$50k/yr free tier now.
5. **AniList** — enrichment/lookup-only; pursue written authorization (DS-03) before any persistence.
6. **DBpedia + Anime News Network** — secondary cross-validation.
7. **Wikimedia Commons** — for images, with per-item license metadata storage.
8. **Reject**: OMDb, Kaggle movie dumps, Jikan (production ingestion), LinkedMDB.

**Registry gaps to file:** TVmaze, DBpedia, Fanart.tv, explicit OMDb `EXCLUDED` entry — none currently in `DATA_SOURCE_REGISTRY_V1.md`.

---

## 2. Anime, international cinema, awards/festivals, multilingual search

Grounded against `DATA_SOURCE_REGISTRY_V1.md`, `CINEVAULT_OS_MASTER_CONCEPT.md` (Award/Festival entity types), `CINEVAULT_OS_TECHNICAL_REQUIREMENTS.md` (Postgres FTS + trigram mandate).

### Anime

| Source | License/ToS | Verdict |
|---|---|---|
| AniList GraphQL | Free <$150/mo revenue; **prohibits use "as backup/data storage"**, "hoarding," and **competing services** | **CANDIDATE-NEEDS-LEGAL-REVIEW** — enrichment/lookup only |
| MyAnimeList Official API v2 | Binding click-through Developer Agreement (rev. 2019) + ToS (rev. Dec 2025); storage terms not published in plain language | **CANDIDATE-NEEDS-LEGAL-REVIEW** — must actually read/archive the agreement text |
| Jikan (unofficial) | Own docs: persisting data breaches MAL ToS | **AVOID** for production ingestion |
| Kitsu API | No clearly published formal ToS; "heavy commercial use should check with Kitsu" | **CANDIDATE-NEEDS-LEGAL-REVIEW** |
| AniDB | Data licensed **CC BY-NC-SA 4.0 — commercial use blocked outright**; API also bans bulk downloading | **AVOID** — NC license disqualifies regardless of ToS enforcement |

**Bottom line:** no anime source is both free and clean for persistent commercial storage. Wikidata is the one CC0 fallback that can be stored, at materially thinner depth than AniList/MAL/AniDB.

### International/regional cinema

| Source | License/ToS | Verdict |
|---|---|---|
| Wikidata SPARQL | CC0, queryable by country/language | **RECOMMENDED** |
| KOBIS/KOFIC (Korean) | REST API live; license terms not confirmed in English (Korea Open Government License framework exists but applicability unconfirmed) | **CANDIDATE-NEEDS-LEGAL-REVIEW** (confirms registry `UNVERIFIED`) |
| Japan Media Arts Database | Official government DB; **no API found** | **CANDIDATE-NEEDS-LEGAL-REVIEW** — manual enrichment only, or pursue direct licensing conversation |
| BFI Filmography | 800k+ UK titles; **no public API found** | **AVOID for automated ingestion** — direct licensing inquiry needed |
| Europeana | Metadata is **CC0**; per-item media rights vary widely | **CANDIDATE** — metadata only, check media rights per item |
| Internet Archive | Item-by-item license | **CANDIDATE**, item-level verification required |
| FilmAffinity | **No official API**, site blocks non-JS clients; only unofficial scrapers exist | **AVOID** — scraping is prohibited by CineVault's own governance (DS-05) |
| Letterboxd API | **Invitation-only** access, no guaranteed approval | **CANDIDATE-NEEDS-LEGAL-REVIEW** — apply, don't scrape the public site as substitute |

### Awards/festivals

| Source | License/ToS | Verdict |
|---|---|---|
| Academy Awards Database (official) | **No public API** | **AVOID for automated ingestion** — manual spot-verification only |
| DLu/oscar_data (community, GitHub) | **BSD-2-Clause**, cross-referenced with IMDb IDs | **RECOMMENDED** as Oscar bootstrap/backfill dataset |
| Wikidata award properties (P166/P1411) | CC0 | **RECOMMENDED** — best normalized, storable, multi-award/festival source; documented SPARQL methodology exists |
| Cannes / Berlinale / BAFTA official sites | **No public API or open-data terms found for any of them** | **AVOID for automated ingestion** — manual/Wikidata-mediated only |

### Multilingual search/transliteration

| Resource | License | Verdict |
|---|---|---|
| PostgreSQL `pg_trgm` | PostgreSQL License (permissive) | **RECOMMENDED** — matches technical-requirements Stage A plan |
| PostgreSQL `unaccent` | PostgreSQL License | **RECOMMENDED** — pair with pg_trgm |
| `pg_bigm` | BSD-style | **CANDIDATE** — better than trigram for CJK short/dense scripts |
| ICU | Unicode License (permissive) | **RECOMMENDED** — standard for cross-script collation/transliteration |
| CLDR | Unicode License | **RECOMMENDED** — data layer under ICU |
| Wikidata labels/aliases | CC0 | **RECOMMENDED** — directly solves the AKA/alternate-title example in the technical requirements doc (e.g. *Kimi no Na wa* / 君の名は。/ *Your Name*) |
| pypinyin (Chinese) | **MIT** confirmed | **RECOMMENDED** |
| pykakasi / kuroshiro (Japanese) | License unclear (older pykakasi releases used GPL) — **verify current PyPI package metadata before adoption** | **CANDIDATE** |
| korean-romanizer / hangul-romanize | Open source, license/maintenance not fully verified | **CANDIDATE** |

---

## 3. Free/OSS tooling for the ingestion & infrastructure pipeline

Grounded against `INGESTION_ARCHITECTURE_V1.md`, `INGESTION_ARCHITECTURE_DAY4.md`, `CACHE_QUEUE_INFRASTRUCTURE_SPECIFICATION_V1.md`, `storage_cdn.md`, `TECHNOLOGY_BASELINE_V1.md`.

### Ingestion adapters

Your existing `BaseProviderAdapter` ABC (`discover / fetch_raw_payload / normalize_payload / validate_normalized`) already correctly encodes licensing-gate + CAT-5 capture + reconciliation logic that no generic framework models.

| Tool | License | Verdict |
|---|---|---|
| **dlt (data load tool)** | Apache 2.0 | **CANDIDATE** — reuse only its incremental-load/checkpoint/retry primitives inside your existing pipeline; don't adopt its destination-loading model |
| Singer/Meltano | MIT (mostly) | **AVOID full adoption** — generic extract→load contract doesn't express your license-gate→raw-capture→identity-resolve→reconcile pipeline |
| Airbyte (platform) | Elastic License 2.0 (source-available) | **AVOID** — heavy standalone platform duplicating what RabbitMQ/Valkey/FastAPI workers already do |
| airbyte-python-cdk (library only) | MIT | **CANDIDATE, low priority** — skim for pagination/backoff boilerplate only |

### Object storage

| Tool | License | Verdict |
|---|---|---|
| MinIO (current dev choice) | AGPLv3, **archived Apr 2026** | **AVOID (replace)** |
| **SeaweedFS** | Apache 2.0 | **RECOMMENDED** MinIO replacement |
| Garage | AGPLv3 | **CANDIDATE** — lightest footprint, same AGPL flag as MinIO (fine unmodified/internal) |
| Cloudflare R2 (current prod choice) | Proprietary managed, S3-compatible | **RECOMMENDED, keep as-is** |
| Backblaze B2 | Proprietary managed | **CANDIDATE** — secondary/backup target, free egress to Cloudflare via Bandwidth Alliance |

### Search

Confirms existing ADR-006 "PostgreSQL-first search" is still current best practice, not a compromise.

| Approach | License | Verdict |
|---|---|---|
| Postgres FTS + pg_trgm (current plan) | N/A, built-in | **RECOMMENDED, confirmed correct** up to low-millions of rows |
| **Meilisearch** | MIT | **RECOMMENDED upgrade path** if/when outgrown — LMDB memory-mapped (doesn't need full dataset in RAM), strong multilingual/typo-tolerance |
| Typesense | Server: **GPLv3** (copyleft); requires entire index in RAM | **CANDIDATE, flagged** — copyleft + RAM-cost concerns |
| OpenSearch | Apache 2.0, but JVM-heavy (2 CPU/4GB min, 16GB+/node for real prod) | **AVOID** — matches project's own stated intent to avoid it until genuinely needed |

Concrete switch trigger: move to Meilisearch when you hit a *named* limit (corpus-wide relevance ranking, many-facet search, sub-50ms SLAs at tens-of-millions of rows) — not preemptively.

### Automation/scheduling

| Tool | License | Verdict |
|---|---|---|
| **APScheduler** | MIT | **RECOMMENDED** — in-process cron trigger publishing onto existing RabbitMQ exchange, zero new infra |
| Celery + Beat | BSD | **AVOID** — needs its own broker, duplicates RabbitMQ workers already built |
| Arq | MIT | **AVOID** — needs Redis/Valkey as its own broker, redundant with RabbitMQ |
| Dagster / Prefect (OSS) | Apache 2.0 | **AVOID (Dagster)** / **CANDIDATE, deferred (Prefect)** — disproportionate for ~5-7 provider sync jobs today |
| Kubernetes CronJob | Already-approved infra | **CANDIDATE** — zero new dependency if K8s is already in use |

### Data source registry tooling

| Tool | Verdict |
|---|---|
| DataHub / OpenMetadata / Amundsen / Backstage | **AVOID, all** — each needs a multi-service cluster (Kafka/Elasticsearch/Neo4j/its-own-DB) for what is currently an 11-row markdown table |
| Markdown/YAML-in-git (current approach) | **RECOMMENDED, keep** — add CI schema validation (JSON Schema/Pydantic) instead of adopting a new tool |
| MkDocs Material | **CANDIDATE** — only if the registry needs a browsable UI for non-engineers later |

### Stack sanity check (flags only, not relitigating already-approved choices)

- Grafana/Loki/OnCall are **AGPLv3** — fine for internal-only self-hosted use; would need a documented compliance boundary only if that functionality is ever re-exposed to external customers.
- Wazuh SIEM (GPLv2) + full Kubernetes/OpenTofu/ArgoCD ops stack are correctly free/OSS but operationally heavy relative to "production not yet authorized" status — not a licensing or cost problem, an operational-load one worth revisiting if the small-team constraint bites.
- No cheaper/free alternative needed for Keycloak, Kong, Valkey, RabbitMQ, Flyway, PgBouncer, pgBackRest, OpenTelemetry/Prometheus — all already correct for their role (see §4 for the separate question of whether Keycloak specifically is worth its *weight*, not its license, given the laptop constraint).

---

## 4. Free/cheap hosting & deployment

Grounded against `INFRASTRUCTURE_ARCHITECTURE_V1.md`, `INFRASTRUCTURE_ARCHITECTURE_DECISION_LOG_V1.md`, `SECURITY_ARCHITECTURE_V1.md`, `deployment.md`.

**Reality check:** your actual current production topology (`docs/deployment.md`) is **9 services** — Caddy, Next.js, FastAPI, Keycloak 24, PgBouncer, PostgreSQL+pgvector, Valkey, RabbitMQ, MinIO — plus Kong Gateway per the cache/queue spec. No free tier anywhere fits that as-is. The constraint isn't "pick a cheap host" — it's that the architecture needs trimming before any free/cheap tier applies at all.

### Compute

| Option | Free tier (2026) | Verdict |
|---|---|---|
| **Oracle Cloud "Always Free"** | 2× AMD micro VMs + Ampere A1 ARM pool **cut from 4 OCPU/24GB to 2 OCPU/12GB** in 2026 (no notice given), 200GB storage, 10TB egress | **RECOMMENDED** — best real "free forever" compute, if account approval/regional ARM capacity cooperates; accept volatility risk (already cut once) |
| Fly.io | **No free tier since Oct 2024** — 7-day trial only | **AVOID** for "free"; ~$5-10/mo candidate otherwise |
| Railway | $5 one-time trial, then $1/mo credit, capped 1vCPU/0.5GB | **AVOID** for production |
| Render | Free web service sleeps after 15min idle; free Postgres **expires after 30 days** | **AVOID for DB**, candidate for throwaway staging API only |
| **Hetzner CX22** | Not free, but €4.35-4.59/mo for 2vCPU/4GB/40GB/~20TB bandwidth | **RECOMMENDED as cheap fallback** once Oracle's volatility becomes a problem |
| GCP `e2-micro` | 1 free VM/mo, but only in 3 US regions, 1GB egress/mo (tight) | **CANDIDATE** as a secondary small node only |
| AWS Free Tier | Time-boxed to 12 months from account creation, not "always free" | **AVOID** for a project meant to sit dormant/cheap long-term |

### Database

| Option | Free tier (2026) | Verdict |
|---|---|---|
| **Neon (Postgres)** | 100 CU-hours/mo, 0.5GB storage, never expires, no card | **RECOMMENDED** while actively developing — solves "laptop can't run Postgres locally" directly |
| Supabase (Postgres) | 500MB DB, **auto-pauses after 7 days idle**, no backups on free plan | **CANDIDATE** — auth bundling is the draw, pause behavior is a real annoyance |
| Railway Postgres | Same expiry problem as compute | **AVOID** |
| ElephantSQL | **Shut down permanently Jan 27, 2025** | **AVOID (defunct)** — don't reference in any current docs |
| Self-hosted on Oracle/Hetzner box | Free (Oracle) / ~$4.50/mo (Hetzner) | **RECOMMENDED long-term** — your ~89k-title dev catalog would exceed every managed free tier's storage cap anyway, so self-hosting is the actual endpoint, not a managed free DB |

### Auth

Keycloak is a **formally approved, locked decision** (`TECHNOLOGY_DECISION_AUTHENTICATION_V1.md`) — this is a cost/fit flag for a future decision doc, not a proposal to silently override it.

| Option | Footprint | Verdict |
|---|---|---|
| Keycloak 24/26 (current approved choice) | JVM-based, ~750MB-1.25GB RAM minimum + its own Postgres DB | Correct **if/when** enterprise-grade OIDC (multi-realm, external IdP federation) is actually needed; heaviest single line item in the resource-starved dev environment today |
| Ory Kratos | ~50MB RAM/service, but headless (must build your own login UI) + multi-service ecosystem for full OIDC | **CANDIDATE** only if hand-building the UI is acceptable |
| Authelia | <20MB, but it's a **forward-auth SSO proxy**, not a full identity provider with registration flows | **AVOID** — wrong shape for "users sign up in a mobile app" |
| Supabase Auth | Hosted, 50k MAU free | **CANDIDATE** only if also adopting Supabase for the DB |
| **fastapi-users + JWT** | Runs inside the existing FastAPI process, zero extra container | **RECOMMENDED for a trimmed/free deployment path specifically** — drops one entire heavy service; frame as a new ADR proposal, not a unilateral reversal |

### CI/CD, backups, monitoring

| Area | Recommendation |
|---|---|
| CI/CD | GitHub Actions free tier (2,000 min/mo private repos) is adequate **with discipline**: cache Docker layers aggressively, gate builds to protected branches only — your branch-heavy workflow + multi-stage Docker builds across 9 services will burn minutes fast otherwise |
| Backups | **Cloudflare R2** (10GB free, zero egress ever) or Backblaze B2 (10GB free) for `pg_dump`/WAL archives, encrypted client-side with `age`/GPG before upload — never rely on managed-DB built-in backups alone (Neon: 6hr time-travel only; Supabase free: no backups at all) |
| Monitoring | **Grafana Cloud free tier** (10k metric series, 50GB logs/traces, 14-day retention, "forever free" as of Aug 2026) fulfills the already-approved Prometheus/OTel direction without adding self-hosted containers; **Better Stack free** (10 monitors/heartbeats) as a lightweight uptime layer alongside it. Skip standing up your own full Prometheus/Grafana/Loki/OTel stack until there's real traffic — that's 3-4 more containers on an already-oversubscribed box |

### Recommended minimal free/cheap path (requires an explicit scope decision from you)

1. Trim the *initial* deployment: drop Kong, Keycloak, RabbitMQ, MinIO → replace with FastAPI's own middleware, `fastapi-users`+JWT, a Postgres-backed job table or Valkey streams, and direct provider-artwork hotlinking respectively.
2. Compute: Oracle Always Free ARM VM running Caddy + FastAPI + Postgres + Valkey; Hetzner CX22 (~€4.50/mo) as the identified fallback if Oracle capacity disappears.
3. Database: Neon free tier while developing → self-hosted Postgres on the same box once catalog size exceeds Neon's 0.5GB.
4. Auth: `fastapi-users`+JWT now; keep Keycloak evaluation open as a documented future ADR if multi-tenant/external-IdP needs appear.
5. Backups: nightly `pg_dump`, `age`-encrypted, to Cloudflare R2.
6. CI/CD: GitHub Actions free tier, cached, gated to protected branches.
7. Monitoring: Grafana Cloud free + Better Stack free heartbeats.
8. Explicitly deferred (matches your own `INFRASTRUCTURE_ARCHITECTURE_DECISION_LOG_V1.md`): Kong, RabbitMQ, MinIO/S3, Keycloak, multi-AZ Postgres, full self-hosted OTel stack.

**This gets to a genuinely running, mostly-$0/mo production deployment — but only after you decide to trim the 9-service architecture down to ~4 services. That trimming is a scope call for you to make explicitly, not something derived automatically from "free tiers are small."**

---

## What this research does NOT solve

Confirmed unchanged from the original problem framing — no amount of resource discovery replaces:

- Database architecture design (PostgreSQL choice itself, schema, ERD) — already decided, this doesn't touch it
- Personal watch-history / append-only event architecture — already correct, untouched
- Offline sync architecture (SQLite/Drift + outbox) — already accepted, untouched
- UUIDv7 identity model — already the permanent identity layer, untouched
- Metadata quality/provenance/conflict resolution logic — still needs your own reconciliation engine; no data source "tells you" a runtime is correct
- Recommendation engine — none of the sources above are a substitute
- Legal verification of any `CANDIDATE-NEEDS-LEGAL-REVIEW` item — every single one above still needs an actual human to read the ToS/license and sign off, not just "it showed up in research as promising"

---

## Consolidated action items

1. **Now, independent of project pause**: swap MinIO → SeaweedFS in `docs/storage_cdn.md` and dev compose files.
2. Add to `DATA_SOURCE_REGISTRY_V1.md`: TVmaze (candidate), DBpedia (candidate), Fanart.tv (candidate), OMDb (**EXCLUDED**), Wikidata award properties + DLu Oscar dataset (candidates for the Awards/Festival domain).
3. File a licensing-review task for each `CANDIDATE-NEEDS-LEGAL-REVIEW` source before any ingestion code is written against it — the highest priority ones are TMDB (commercial license, DS-02) and AniList (competing-service clause risk, DS-03).
4. Decide (new ADR, don't silently change): whether to trim Keycloak/Kong/RabbitMQ/MinIO out of the *near-term* deployment in favor of a free-tier-fitting ~4-service stack, versus keeping the full 9-service architecture and accepting real hosting cost (~Hetzner scale) from day one.
5. Add CI schema validation for the data source registry (JSON Schema/Pydantic in GitHub Actions) rather than adopting a data-catalog product.
