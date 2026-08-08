# CineVault OS — Data Source Registry V1

**Document Type:** Authoritative Candidate & Source-Strategy Registry  
**Status:** Architecture Baseline Specification (Post-Owner Approval Pass)  
**Date:** 2026-08-08  
**Scope:** Metadata Providers, Licensing Boundaries, Source Authority Matrix, and Ingestion Policies  

> [!IMPORTANT]
> **GOVERNANCE & SOURCE SELECTION PRINCIPLES**  
> 1. **No Universal Global Provider:** CineVault will NOT designate one global external provider as the universal primary source (`DS-01`).  
> 2. **Domain-Specific Authority:** Source authority is determined per domain/entity based on quality, licensing, coverage, and provenance (`DS-01`).  
> 3. **Licensing Before Ingestion:** Licensing terms must be verified prior to production ingestion. Public APIs or websites do NOT imply warehousing or commercial rights.  
> 4. **External Identity Mapping:** Provider IDs are mappings (`External Identity Mapping`), NEVER canonical identity (`ADR-001`).  
> 5. **Media Licensing Separation:** Metadata licensing and image/media licensing are separate concerns.  
> 6. **Scraping Prohibition:** Scraping public websites is explicitly prohibited as an ingestion strategy (`DS-05`).  

---

## 1. Provider Status Taxonomy Legend

Every provider record in this registry is classified using exactly one of the following statuses:

* `CANDIDATE`: Potentially usable, pending detailed validation and project owner approval.
* `CONDITIONAL`: Usable only if a specific licensing, contract, or permission condition is satisfied.
* `RESTRICTED`: Potentially useful, but current public terms materially restrict intended CineVault persistent use.
* `EXCLUDED`: Known public or legal terms make it unsuitable for CineVault's intended production use.
* `DEFERRED`: Insufficient verified evidence or not currently required for initial phases.
* `VERIFICATION-ONLY`: Useful as an authoritative verification source, but not intended for bulk catalog ingestion.

---

## 2. Domain-Level Authority Matrix

| Domain | Candidate Source | Authority Role | Strength | Major Risk / Barrier | Status |
|---|---|---|---|---|---|
| **Knowledge / Reference / Identity** | Wikidata | Reference | Strong structured CC0 graph data | Coverage depth consistency | `CANDIDATE` |
| **Film & Television Metadata** | TMDb | Candidate Primary | Excellent catalog depth | Commercial licensing terms | `CONDITIONAL` |
| **Film & Television (Commercial)** | IMDb Commercial | Candidate Commercial Feed | Industry standard breadth | License cost & contract requirements | `CONDITIONAL` |
| **Film & Television (Public Data)** | IMDb Public Datasets | Excluded | High name recognition | Non-commercial restriction conflicts | `EXCLUDED` |
| **Television & Episodic Structure** | TheTVDB | `SECONDARY TV AUTHORITY` | Exceptional episode metadata | Revenue-tier licensing (`DEC-SRC-PRP-02` Approved) | `CANDIDATE` (Authority Role Approved) |
| **Anime & Japanese Animation** | AniList | Candidate Enrichment | High community quality | ToS persistent storage restriction | `RESTRICTED` |
| **Anime Catalog (Secondary)** | Anime News Network | Candidate Secondary | Deep historical accuracy | Rate limits & attribution rules | `CANDIDATE` |
| **Anime Catalog (Alternative)** | MyAnimeList | Deferred | High popularity | Insufficient storage terms evidence | `DEFERRED` |
| **Streaming Availability** | JustWatch | Candidate Primary | Comprehensive global offers | Official partner contract required | `CONDITIONAL` |
| **Korean Cinema / Box Office** | KOBIS / KOFIC | `PRIMARY KOREAN-DOMAIN AUTHORITY` | Official national registry | Unverified licensing terms (`DEC-SRC-PRP-01` Approved) | `CANDIDATE` (Authority Role Approved) |
| **Cultural Heritage & Archives** | Library of Congress / Europeana | Reference | High historical authority | Per-item rights variability | `CANDIDATE` |

---

## 3. Core Metadata Provider Registries

---

### Provider: Wikidata

* **Status:** `CANDIDATE`
* **Source Role:** Reference / Discovery / Identity Mapping
* **Source Type:** Knowledge Graph / Structured Open Data
* **Domain Coverage:** Global Film, Television, Anime, People, Awards, Organizations, Geography, Language
* **Entity Coverage:** `Title`, `Person`, `Award`, `Festival`, `Country`, `Language`, `ProductionCompany`
* **Supported Fields:** `canonical_title`, `original_title`, `production_year`, `birth_date`, Wikidata Q-ID cross-references

#### Licensing Matrix
* **Commercial Use:** `Confirmed` (Structured data published under CC0 1.0 Universal)
* **Non-Commercial Use:** `Confirmed`
* **Attribution Requirement:** `Confirmed` (CC0 does not legally mandate attribution, but best practice retained)
* **Redistribution:** `Confirmed`
* **Persistent Storage:** `Confirmed`
* **Caching:** `Confirmed`
* **Derived Data:** `Confirmed`
* **Provider ID Usage:** `Confirmed` (Wikidata Q-IDs mapped via `TitleExternalId`)
* **Image / Media Licensing:** `Conditional` (Linked media on Wikimedia Commons carries independent licenses: CC-BY, CC-BY-SA, Public Domain)
* **Geographic Restrictions:** None
* **Contract Requirements:** None for CC0 structured data

#### Access & Operational Limits
* **API Availability:** Public SPARQL Endpoint & Wikidata REST API
* **Dataset Availability:** Complete JSON/RDF dumps available
* **Authentication:** Optional User-Agent header requirement
* **Rate Limits:** SPARQL endpoint query execution limits (60s timeout per query)
* **Pagination / Batch Capability:** Supported via SPARQL offset/limit and dump processing
* **Update Frequency:** Real-time community edits
* **Reliability:** High infrastructure uptime; community edit variance

#### Quality & Provenance
* **Strengths:** Open CC0 license; unrivaled identity cross-linking across global databases.
* **Weaknesses:** Inconsistent field completeness for niche titles; schema variability.
* **Provenance Requirement:** Required (`provider = "Wikidata"`, Q-ID, retrieval timestamp).

---

### Provider: TMDb (The Movie Database)

* **Status:** `CONDITIONAL`
* **Source Role:** Candidate Primary (Film & Television Metadata)
* **Source Type:** API / Catalog Data Feed
* **Domain Coverage:** Film, Television Series, Seasons, Episodes, People, Credits, Genres, Posters
* **Entity Coverage:** `Title`, `Edition`, `Season`, `Episode`, `Person`, `Credit`, `Genre`
* **Supported Fields:** `canonical_title`, `synopsis`, `runtime_minutes`, `release_date`, `poster_path`, TMDb ID

#### Licensing Matrix
* **Commercial Use:** `Conditional` (Requires explicit TMDb commercial license agreement per `DS-02`)
* **Non-Commercial Use:** `Confirmed` (API key required)
* **Attribution Requirement:** `Confirmed` (TMDb attribution logo and text required)
* **Redistribution:** `Conditional` (Subject to API terms)
* **Persistent Storage:** `Conditional` (Caching permitted; local warehousing requires commercial terms)
* **Caching:** `Confirmed`
* **Derived Data:** `Conditional`
* **Provider ID Usage:** `Confirmed` (TMDb IDs mapped via `TitleExternalId`)
* **Image / Media Licensing:** `Conditional` (TMDb image API subject to attribution and Terms of Use)
* **Geographic Restrictions:** Global catalog
* **Contract Requirements:** Commercial licensing agreement required before production use (`DS-02`)

#### Access & Operational Limits
* **API Availability:** REST API v3 / v4
* **Dataset Availability:** Daily export files for ID cross-reference
* **Authentication:** Bearer Token / API Key
* **Rate Limits:** 
  > No fixed published rate limit. TMDb states that the legacy 40 requests / 10 seconds limit was disabled in 2019. TMDb currently describes an upper limit somewhere around 40 requests per second, subject to change. HTTP 429 responses must be respected.
* **Pagination:** 20 results per page
* **Update Frequency:** Daily bulk exports; real-time API updates

#### Quality & Provenance
* **Strengths:** Industry-standard metadata structure, global localization, excellent image coverage.
* **Weaknesses:** Commercial licensing requirement for production systems; occasional user-submitted errors.

---

### Provider: IMDb Public Datasets

* **Status:** `EXCLUDED`
* **Source Role:** Excluded (`DS-04`)
* **Source Type:** Downloadable TSV Datasets
* **Domain Coverage:** Film, TV, Episodes, People
* **Reason for Exclusion:** IMDb public datasets are explicitly licensed for personal, non-commercial use only. Storing IMDb public dataset fields in CineVault's persistent production catalog violates the non-commercial redistribution terms (`DS-04`).

---

### Provider: IMDb Commercial Products

* **Status:** `CONDITIONAL`
* **Source Role:** Candidate Commercial Feed
* **Source Type:** Commercial Data Feed / API (AWS Data Exchange / IMDb License)
* **Domain Coverage:** Global Cinema, Television, People, Box Office, Awards
* **Entity Coverage:** `Title`, `Episode`, `Person`, `Credit`, `Award`
* **Condition for Use:** Execution of an official commercial licensing contract with IMDb/Amazon Web Services (`DS-04`).

---

### Provider: AniList

* **Status:** `RESTRICTED`
* **Source Role:** Candidate Enrichment / Verification (`DS-03`)
* **Source Type:** GraphQL API
* **Domain Coverage:** Anime, Manga, Voice Actors, Studios, Characters
* **Entity Coverage:** `Title` (Anime), `Season`, `Person` (Seiyuu), `ProductionCompany` (Studio)
* **Condition for Use:** Persistent canonical catalog ingestion is **prohibited** under current public API terms. Permitted ONLY for limited on-demand user lookup or enrichment if explicit authorization is obtained (`DS-03`).

---

### Provider: JustWatch

* **Status:** `CONDITIONAL`
* **Source Role:** Candidate Primary (Streaming Availability)
* **Source Type:** Commercial Partner API / Licensed Feed
* **Domain Coverage:** Subscription (SVOD), Rental (TVOD), Purchase (EST), Free (AVOD) Availability
* **Entity Coverage:** `Platform`, `PlatformOffer`, `Release`
* **Condition for Use:** Official JustWatch Enterprise Partner contract (`DS-05`).
* **Scraping Policy:** **STRICTLY PROHIBITED.** Web scraping of JustWatch public interfaces is explicitly rejected as an architectural strategy (`DS-05`).

---

### Provider: TheTVDB

* **Authority Role:** `SECONDARY TV AUTHORITY`
* **Provider Status:** `CANDIDATE`
* **Licensing:** `CONDITIONAL / tier-dependent`
* **Governance:** `AUTHORITY ROLE APPROVED — PRODUCTION ACCESS SUBJECT TO LICENSING VERIFICATION` (`DEC-SRC-PRP-02` Approved)
* **Source Type:** REST API v4
* **Domain Coverage:** TV Series, Seasons, Episodes, Ordering, Artwork
* **Entity Coverage:** `Title`, `Season`, `Episode`, `Credit`, `Platform`
* **Commercial Tier Structure:**
  * `< $50k/year`: Free with attribution
  * `$50k–$250k/year`: $1,000/year
  * `$250k–$1M/year`: $10,000/year
  * `$1M+`: Custom terms / contact provider
* **Attribution:** Required unless otherwise approved by TheTVDB.
* **Images/Media:** Do not assume API data licensing grants image/trailer rights.

---

### Provider: Anime News Network (ANN) Encyclopedia

* **Status:** `CANDIDATE`
* **Source Role:** Candidate Secondary / Verification (Historical Anime Metadata)
* **Source Type:** XML API / Public Encyclopedia
* **Domain Coverage:** Anime TV, Anime Films, OVAs, ONAs, Japanese Cast & Crew
* **Licensing Status:** `Conditional` (Requires attribution; strict rate limiting)

---

### Provider: MyAnimeList (MAL)

* **Status:** `DEFERRED`
* **Source Role:** Deferred
* **Source Type:** Official REST API
* **Reason for Deferral:** Insufficient verified evidence regarding persistent catalog storage terms for commercial personal knowledge platforms.

---

### Provider: Specialized & Cultural Archives

#### Europeana
* **Status:** `CANDIDATE`
* **Rights:** Per-item rights vary. Do not classify the entire Europeana corpus as CC0. Each item/record must be evaluated according to its stated rights metadata.

#### Internet Archive
* **Status:** `CANDIDATE`
* **Rights:** Item-specific / collection-specific rights must be evaluated. Do not classify the entire archive as CC0/public domain.

#### Library of Congress
* **Status:** `CANDIDATE` / `VERIFICATION-ONLY`
* **Rights:** Evaluate rights at the collection/item level. Do not assume all catalogued media is public domain merely because the Library is a government institution.

#### KOBIS / KOFIC (Korean Film Council)
* **Authority Role:** `PRIMARY KOREAN-DOMAIN AUTHORITY`
* **Provider Status:** `CANDIDATE`
* **Licensing:** `UNVERIFIED`
* **Governance:** `AUTHORITY ROLE APPROVED — PRODUCTION ACCESS SUBJECT TO LICENSING/ACCESS VERIFICATION` (`DEC-SRC-PRP-01` Approved)
* **API:** Confirmed to exist (REST API).
* **Licensing Rule:** Do not state CC0, CC-BY, public domain, or equivalent unless an official licensing source confirms it.

---

### Provider: Commercial Data Feeds (Gracenote, TiVo/Rovi, Reelgood, Whip Media)

* **Status:** `CANDIDATE` (Candidate Commercial Feed)
* **Source Role:** Candidate Commercial Feed
* **Condition:** Subject to future enterprise licensing evaluation if open/licensed candidates prove insufficient.

---

## 4. Cross-Provider Conflict Matrix

The following table documents known domain conflict areas across candidate data sources:

| Metadata Domain | Potential Source Conflict Areas | Conflict Characteristics | Strategy Requirement |
|---|---|---|---|
| **Title Names** | English localized vs Romanized vs Original Script | TMDb localized vs AniList Romanized vs Wikidata Q-ID | Preserve `canonical_title` and `original_title` separately |
| **Release Dates** | Country premiere vs Festival premiere vs Digital launch | TMDb theatrical vs IMDb festival vs JustWatch digital | Release event entity isolation (`Release.release_type`) |
| **Runtime** | Theatrical cut vs Extended cut vs Censored cut | 120 min theatrical vs 135 min Director's cut | Edition-level runtime tracking (`Edition.runtime_minutes`) |
| **Episode Ordering** | Broadcast order vs DVD order vs Story arc order | TVDB broadcast vs AniList absolute vs TMDb season | Extensible ordering support (`RegionalEpisodeOrder`) |
| **Cast / Crew** | Billing order rank vs Main/Supporting distinction | TMDb billing rank vs TVDB guest star flags | Explicit billing rank and role tagging (`Credit`) |
| **Genres / Themes** | Broad genres vs Specific micro-tags | TMDb broad genres vs AniList granular tags | Hierarchy taxonomy mapping (`Genre` vs `Theme`) |

---

## 5. Commercial Readiness Summary

| Provider | Non-Commercial | Commercial Use | Licensing Action Required |
|---|---|---|---|
| **Wikidata** | Usable | Usable (CC0) | None for structured data; verify image licenses |
| **TMDb** | Usable | Commercial License Required | Execute commercial agreement per `DS-02` |
| **IMDb Public** | Usable | **EXCLUDED** | Do NOT ingest into production catalog (`DS-04`) |
| **IMDb Commercial**| Contract Required | Contract Required | Commercial contract with AWS/IMDb |
| **AniList** | Restricted API | Restricted API | Obtain explicit written authorization (`DS-03`) |
| **JustWatch** | Prohibited (Scraping) | Partner Contract Required | Execute partner agreement (`DS-05`) |
| **TheTVDB** | API License | Tier-dependent ($0–$10k+/yr) | Determine tier & accept terms |

---

## 6. Decision Status Summary

* **APPROVED (DS-01 — DS-07 & DEC-SRC-PRP-01/02):** Domain-specific source authority (`DS-01`), TMDb conditional status (`DS-02`), AniList restricted status (`DS-03`), IMDb public dataset exclusion (`DS-04`), JustWatch official channel conditional status (`DS-05`), Wikidata candidate status (`DS-06`), candidate registry expansion (`DS-07`), KOBIS Primary Korean Authority role (`DEC-SRC-PRP-01`), and TheTVDB Secondary TV Authority role (`DEC-SRC-PRP-02`).
* **DERIVED:** Provenance expectations per candidate, entity-scoped provider ID mapping, image/metadata licensing separation.
* **PROPOSED:** *None.* All source authority proposals have received formal Project Owner approval.
* **DEFERRED:** Physical ingestion adapter code, rate-limiting queue implementation, API client network code, physical provenance table DDL.
