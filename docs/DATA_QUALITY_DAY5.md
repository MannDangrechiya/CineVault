# CineVault OS — Day 5 Data Quality, Deduplication & Conflict Resolution Architecture

## 1. Overview

Day 5 introduces the comprehensive Data Quality, Normalization, Deduplication, and Conflict Resolution Engine for CineVault OS. It guarantees that external provider data is treated as candidate observation payloads, requiring multi-layered validation, deterministic normalization, multi-level identity matching, and domain authority conflict resolution prior to controlled canonical mutation.

---

## 2. Ingestion & Quality Lifecycle Pipeline

```text
External Data Source Payload
            ↓
Day 4 Ingestion Pipeline (Source Licensing Gate & Raw Checksum Capture)
            ↓
Layer 1: Schema Validation (Data types, required fields, enum bounds)
            ↓
Layer 2: Referential Validation (FK integrity: episode→season, season→title, release→edition)
            ↓
Layer 3: Semantic Validation (Numeric bounds, date bounds, runtime bounds)
            ↓
Layer 4: Cross-Field Validation (Structural coherence: MOVIE vs TV season_count, episode season_id)
            ↓
Deterministic Normalization (NFKC, whitespace, lowercasing, comparison keys; original title preserved)
            ↓
Identity Matching Engine (Level 1: Exact External ID → Level 2: Canonical ID → Level 3: Deterministic → Level 4: Probabilistic)
            ↓
Duplicate & False-Match Prevention (ADR-002 Title vs Edition vs Release distinction, Multilingual signals, External ID collisions)
            ↓
Conflict Detection & Provenance Logging (Field-level provenance & quality.metadata_conflict creation)
            ↓
Confidence & Quality State Evaluation (HIGH, MEDIUM, LOW, UNKNOWN, CONFLICT)
            ↓
Review Queue / Controlled Apply (Auto-Match / Human Curation Gate / Dry-Run summary)
            ↓
Canonical Database (CAT-1) [Immutable UUIDv7 & CAT-2 Personal Data Protection]
```

---

## 3. The 4 Validation Layers

1. **Schema Validation**: Verify data types, non-null mandatory fields, valid enum values, UUID format. Payload with invalid types (e.g. `production_year = "abc"`) is immediately quarantined (`SCHEMA_VALIDATION_ERROR`).
2. **Referential Validation**: Check graph relationship integrity before canonical linking (`episode -> season`, `season -> title`, `release -> edition`, `edition -> title`, `external_id -> title`). Orphan entities are rejected.
3. **Semantic Validation**: Sanity checks on attribute values:
   - `runtime_minutes` must be integer > 0; runtime > 300 minutes flagged.
   - `production_year` must be between 1888 and current_year + 5.
   - Person `birth_date` must precede `death_date`.
4. **Cross-Field Validation**: Evaluates structural consistency across entity properties:
   - Content type `MOVIE` with `season_count > 0` or season fields is flagged as invalid classification.
   - `TV_SERIES` or `EPISODE` missing `season_id` / `season_number` fails validation.
   - Release date preceding production year by > 2 years is flagged.

---

## 4. Multi-Level Identity Matching & Deduplication

- **Level 1 — Exact External ID**: Direct lookup in `canonical.title_external_id` (e.g., TMDb ID `12345`). Yields `MATCH_EXACT` / `AUTO_MATCH` (score 1.000).
- **Level 2 — Canonical Identity**: Direct match on CineVault `title_id` (UUIDv7) or `display_id`.
- **Level 3 — Deterministic Signals**: Normalized title + original title + release year + production country + runtime + director overlap. Title alone is NEVER sufficient.
- **Level 4 — Probabilistic Matching**:
  - Score >= 0.90 -> `AUTO_MATCH`
  - 0.50 <= Score < 0.90 -> `REQUIRES_REVIEW` (Staged in candidate review queue)
  - Score < 0.50 -> `NO_MATCH`

### ADR-002 Boundaries & Multilingual Identity

1. **Title vs Edition**: Re-releases, Director's Cuts, Theatrical Cuts, Extended Cuts are mapped as `EditionModel` entries under an existing `TitleModel`, NOT duplicated as separate canonical titles.
2. **Release vs Edition**: Streaming platform offers (Netflix, Prime, theatrical runs) are mapped to `ReleaseModel` or `PlatformOfferModel` under the primary `EditionModel`.
3. **Multilingual Identity**: Titles in Japanese, Korean, Chinese, Indic, or European languages (e.g. "Your Name" / "君の名は。" / "Kimi no Na wa") require external ID mapping or strong multi-signal correlation before canonical merging. Soft text similarity alone never auto-merges multilingual titles.
4. **External ID Collisions**: If an incoming provider ID (e.g. TMDb 12345) matches two distinct existing canonical titles, an `EXTERNAL_ID_COLLISION` conflict is logged and routed for human curation.

---

## 5. Metadata Conflict Lifecycle & Provenance

When observations disagree across providers (e.g., TMDb runtime = 140 vs Official runtime = 142):
- A record is created in `quality.metadata_conflict` with `entity_type`, `field_name`, `candidate_value`, `existing_value`, `source_provider`, `confidence`, and `status = 'OPEN'`.
- Status lifecycle: `OPEN` -> `UNDER_REVIEW` -> `RESOLVED` / `REJECTED` / `DEFERRED`.
- Provenance is fully preserved in `quality.field_provenance` recording every source observation timestamp, confidence, and winning rule rationale.

---

## 6. Personal Data & Canonical Merge Protection (ADR-003, ADR-004)

- Ingestion and data quality services NEVER alter, re-parent, or delete user personal data (`watch_history`, ratings, reviews, notes, favorites, custom lists).
- In the event of a canonical title merge, user personal data remains attached to original entity IDs or generates a `personal_data_conflict` for user-directed resolution.

---

## 7. Verification Baseline

- **Catalog Baseline**: 9 Movies + 1 TV Series = 10 Total real catalog titles strictly preserved.
- **Dry-Run Safety**: Running ingestion with `dry_run=True` stages candidates and calculates quality counters without mutating `canonical.title`.
- **Idempotency**: Executing an identical ingestion run twice produces 0 duplicate canonical titles or editions.
