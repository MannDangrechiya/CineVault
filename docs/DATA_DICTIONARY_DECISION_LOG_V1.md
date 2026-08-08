# CineVault OS — Data Dictionary Decision Log V1

**Document Type:** Mandatory Field-Level Decision Categorization Log  
**Status:** Complete  
**Date:** 2026-08-08  
**Scope:** Approved, Derived, Proposed, Deferred, and Blocked Data Dictionary Decisions  

---

## 1. Executive Summary

This Data Dictionary Decision Log categorizes all field-level choices made during the authoring of `DATA_DICTIONARY_V1.md` according to task governance rule Section 21.

Decisions are strictly divided into five mandatory categories:
* **APPROVED:** Directly approved by project owner in accepted ADRs (`ADR-001`..`ADR-004`) and baseline decisions (`DEC-PRP-01`..`DEC-PRP-04`).
* **DERIVED:** Direct mathematical or logical consequences of approved baseline decisions.
* **PROPOSED:** New field-level recommendations requiring project owner review (if any).
* **DEFERRED:** Intentionally postponed physical implementation details.
* **BLOCKED:** Unresolved architectural dependencies.

---

## 2. Decision Classification Matrix

### A. APPROVED DECISIONS

| Decision ID | Field / Concept Target | Source Baseline | Decision Summary |
|---|---|---|---|
| `DEC-DIC-APP-01` | `Title.title_id`, `Edition.edition_id`, etc. | `ADR-001` | Conceptual `UUIDv7 identifier` used as permanent canonical primary key. |
| `DEC-DIC-APP-02` | `Title.display_id` | `ADR-001` | Conceptual `immutable display identifier`. Prefix is historical at creation; current type determined by `content_type`. |
| `DEC-DIC-APP-03` | `Edition.is_primary` | `ADR-002` | Every Title conceptually possesses exactly one Primary Edition (`is_primary = true`). Additional Editions exist ONLY for material cuts. |
| `DEC-DIC-APP-04` | `TitleExternalId`, `EpisodeExternalId`, etc. | `ADR-001` | Entity-scoped mapping tables replace generic polymorphic foreign keys. External IDs are NEVER canonical identity. |
| `DEC-DIC-APP-05` | `WatchEvent.edition_id` | `ADR-003` | `edition_id = NULL` strictly signifies an unknown/unspecified Edition, NOT Primary Edition. |
| `DEC-DIC-APP-06` | `UserProgress` | `ADR-003` | `UserProgress` is a `CAT-3` derived read model, recomputable from authoritative `WatchEvent` log. |
| `DEC-DIC-APP-07` | `UserNote` vs `UserReview` | `ADR-003` | `UserNote` (private) and `UserReview` (publishable) are strictly separate entities. |
| `DEC-DIC-APP-08` | `Award`, `Festival` Domain | `DEC-PRP-01` | Approved explicit domain entity set for Awards (4 entities) and Festivals (3 entities). |
| `DEC-DIC-APP-09` | `UserTitleState` | `DEC-PRP-02` | Approved explicit separation of `derived_status` and `manual_status_override`. |
| `DEC-DIC-APP-10` | `PersonalDataConflict`, `UserSplitResolution` | `DEC-PRP-03` | Approved conceptual queues to isolate unresolved user data conflicts during merges/splits. |
| `DEC-DIC-APP-11` | `PlatformOffer.valid_from` / `valid_until` | `DEC-PRP-04` | Approved temporal interval model bounds (`valid_from` to `valid_until`) for streaming availability. |

---

### B. DERIVED DECISIONS

| Decision ID | Field / Concept Target | Source Approved Decision | Derived Decision Summary |
|---|---|---|---|
| `DEC-DIC-DER-01` | `Episode.title_id` | `ADR-002` | Denormalized `title_id` FK placed on `Episode` entity alongside `season_id` to optimize Title-level episodic queries. |
| `DEC-DIC-DER-02` | `WatchEventCorrection` | `ADR-003` | `WatchEventCorrection` entity created to track non-destructive event tombstones (Original Event -> Tombstone -> Corrected Event). |
| `DEC-DIC-DER-03` | `TitleCountry`, `EditionLanguage` | Prompt, `ADR-001` | Role-based relationship entities replace overloaded scalar country/language strings. |
| `DEC-DIC-DER-04` | `LibraryEntry.preferred_edition_id` | `ADR-003` | Optional user preference FK on `LibraryEntry` that does NOT alter canonical Title identity. |
| `DEC-DIC-DER-05` | `IdentityRedirect` | `ADR-001`, `ADR-004` | `IdentityRedirect` entity created to preserve historical UUID resolution after canonical Title or Person merges. |

---

### C. PROPOSED DECISIONS (NEW OWNER APPROVAL REQUIRED)

```text
NEW PROPOSED DECISIONS INTRODUCED IN DATA DICTIONARY V1: 0
```

* All field-level recommendations in `DATA_DICTIONARY_V1.md` derive strictly from previously accepted ADRs (`ADR-001`..`ADR-004`) and owner-approved decisions (`DEC-PRP-01`..`DEC-PRP-04`). No new unapproved proposed decisions were introduced.

---

### D. DEFERRED DECISIONS (Intentionally Postponed)

| Decision ID | Field / Topic Target | Reason for Deferral | Target Phase |
|---|---|---|---|
| `DEC-DIC-DEF-01` | **Physical Database DDL & Data Types** | Data Dictionary uses conceptual data types exclusively. Physical SQL types (`VARCHAR`, `TIMESTAMPTZ`, `JSONB`) strictly deferred. | Physical Database Phase |
| `DEC-DIC-DEF-02` | **PostgreSQL Indexing & Partial Unique Index DDL** | Physical partial unique index DDL for `Edition.is_primary` and `TitleExternalId` deferred. | Performance & DB Phase |
| `DEC-DIC-DEF-03` | **CJK / Indic Script Normalization Engine** | Unicode script normalization algorithms for `original_title` deferred. | Ingestion Pipeline Phase |
| `DEC-DIC-DEF-04` | **Status Transition State Machine** | Exact state machine rules for `UserTitleState` transitions deferred. | Domain Service Phase |
| `DEC-DIC-DEF-05` | **Conflict & Split Resolution Queue Algorithms** | Queue resolution algorithms for `PersonalDataConflict` deferred. | Conflict Engine Phase |
| `DEC-DIC-DEF-06` | **Physical Provenance Table DDL** | Marked as `DEFERRED — INGESTION / PROVENANCE REVIEW`. | Ingestion Review Phase |
| `DEC-DIC-DEF-07` | **Physical System Audit DDL** | Marked as `DEFERRED — AUDIT / SECURITY REVIEW`. | Audit & Security Phase |
| `DEC-DIC-DEF-08` | **Personal Data Purge Retention Policies** | User data backup retention timeline & purge execution rules deferred. | Privacy Policy Phase |

---

### E. BLOCKED DECISIONS

```text
BLOCKED DECISIONS: 0
```
* No field-level choices are currently blocked by unresolvable architectural dependencies.
