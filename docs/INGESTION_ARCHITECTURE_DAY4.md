# CineVault OS — Day 4 Ingestion Architecture & Data Source Adapters

## 1. Overview

Day 4 establishes the scalable ingestion foundation for CineVault OS. This architecture enables CineVault to acquire, normalize, match, stage, and apply external metadata from multiple domain providers (TMDb, TVDB, KOBIS, AniList, MyAnimeList, Wikidata, IMDb Datasets) while guaranteeing:

1. **Provider Independence**: Canonical titles are completely decoupled from external provider IDs.
2. **Canonical & User Data Protection**: Ingestion services never mutate user personal data (`watch_history`, ratings, user lists) or overwrite immutable UUIDv7 identity keys.
3. **Data Source Licensing Governance**: Every source is registered with explicit licensing, rate limits, commercial usage terms, and a strict ban on unauthorized web scraping.
4. **Candidate Staging & Controlled Apply**: External payloads are treated as input data (not commands) and staged in `quality.candidate_title` before controlled canonical application.

---

## 2. Ingestion Lifecycle Pipeline

```text
External Provider Response
          ↓
  Source Licensing Gate (verify_source_access)
          ↓
  Raw Source Record (ingestion.raw_payload_capture with SHA-256 Checksum)
          ↓
  Schema Validation (Failure → quality.quarantine_record)
          ↓
  Normalization (Controlled content_type: MOVIE, TV_SERIES, ANIME, etc.)
          ↓
  Identifier Matching (1. Exact External ID → 2. Title+Year → 3. Probabilistic → 4. Review)
          ↓
  Conflict Detection & Provenance (Field Mismatch → quality.field_provenance CONFLICT)
          ↓
  Candidate Staging (quality.candidate_title)
          ↓
  Controlled Apply / Dry Run (mutates canonical only upon validation & approval)
          ↓
  Canonical PostgreSQL Catalog
```

---

## 3. Data Source Registry Specs

| Provider ID | Source Type | License / Terms | Rate Limit / Min | Access Status | Scraping Permitted |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **KOBIS** | Official Box Office API | Public Data License (Type 1) | 300 | `PERMITTED` | ❌ Blocked |
| **TVDB** | Commercial Metadata API | TVDB v4 Commercial API | 1200 | `PERMITTED` | ❌ Blocked |
| **TMDB** | Global Community API | TMDb API Terms of Use | 2400 | `PERMITTED_SERVER_ONLY` | ❌ Blocked |
| **ANILIST** | GraphQL Community API | MIT / AniList API | 90 | `PERMITTED` | ❌ Blocked |
| **MYANIMELIST**| Commercial REST API v2 | MAL API Terms | 180 | `PERMITTED` | ❌ Blocked |
| **WIKIDATA** | Open SPARQL Graph | CC0 1.0 Public Domain | 600 | `PERMITTED` | ❌ Blocked |
| **OFFICIAL_STUDIO**| Direct Press Kits | Direct Studio License | 1000 | `PERMITTED` | ❌ Blocked |
| **OFFICIAL_FESTIVAL**| Festival Program Archive | Public Festival Archive | 500 | `PERMITTED` | ❌ Blocked |
| **JUSTWATCH**| Availability Scraper | Unauthorized Scraping | 0 | `PROHIBITED` | ❌ Blocked |
| **IMDB_DATASETS**| Non-Commercial TSV | IMDb Non-Commercial License | 60 | `PROHIBITED` (Commercial) | ❌ Blocked |
| **UNKNOWN** | Unverified External | Legal Review Required | 0 | `NEEDS_REVIEW` | ❌ Blocked |

---

## 4. Provider Adapter Interface Standard

All adapters inherit from `BaseProviderAdapter` in `services/api/ingestion/adapters.py` enforcing:

```python
class BaseProviderAdapter(ABC):
    async def discover(query: str, entity_type: str) -> List[Dict[str, Any]]: ...
    async def fetch_raw_payload(external_entity_type: str, external_entity_id: str) -> Dict[str, Any]: ...
    def normalize_payload(raw_payload: Dict[str, Any]) -> Dict[str, Any]: ...
    def validate_normalized(normalized_payload: Dict[str, Any]) -> Tuple[bool, List[str]]: ...
```

Adapters support exponential backoff, rate limiting, and HTTP 429 retry handling.

---

## 5. Candidate Staging & Controlled Apply Rules

1. **Dry-Run Execution**: Setting `dry_run=True` runs raw capture, normalization, matching, conflict detection, candidate staging, and returns summary counters without mutating `canonical.title`.
2. **Field Provenance**: Every incoming property is logged in `quality.field_provenance` with provider attribution, timestamp, and confidence status (`HIGH`, `MEDIUM`, `LOW`, `UNKNOWN`, `CONFLICT`).
3. **Immutability Protection**: `canonical.title.title_id` (UUIDv7) and `display_id` are strictly immutable. External provider IDs map exclusively to `canonical.title_external_ids`.
4. **Personal Data Isolation**: Ingestion services have zero touch points with personal user tables (`watch_history`, ratings, user lists).

---

## 6. Verification Results

- **Backend Pytest**: 178 passed, 0 failed.
- **Web TypeScript**: 0 errors (`npx tsc --noEmit`).
- **Catalog Baseline**: 9 Movies + 1 TV Series = 10 Total real catalog titles preserved.
