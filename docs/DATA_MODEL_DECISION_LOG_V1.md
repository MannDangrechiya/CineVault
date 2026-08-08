# CineVault OS — Data Model Decision Log v1.0

**Document Type:** Mandatory Architectural Decision Categorization Log  
**Status:** Complete  
**Date:** 2026-08-08  
**Scope:** Approved, Derived, Proposed, Deferred, and Blocked Architectural Modeling Decisions  

---

## 1. Executive Summary

This Data Model Decision Log categorizes all technical choices made during the Data Model Specification & ERD Phase according to project governance rule Phase 17.

The decisions are strictly divided into five mandatory governance categories:
* **APPROVED:** Explicitly approved by the project owner in accepted ADRs (`ADR-001` through `ADR-004`).
* **DERIVED:** Direct mathematical or logical consequences of approved baseline decisions.
* **PROPOSED:** Technical modeling recommendations requiring project owner review & approval.
* **DEFERRED:** Intentionally postponed technical decisions.
* **BLOCKED:** Decisions awaiting upstream architectural resolution.

---

## 2. Decision Log Matrix

### A. APPROVED DECISIONS (Project Owner Approved in ADRs)

| Decision ID | Decision Title | Architectural Baseline Source | Summary of Decision |
|---|---|---|---|
| `DEC-APP-01` | **UUIDv7 Canonical Identity** | `ADR-001` | Permanent internal primary key generated internally using UUIDv7. Independent of external IDs, content type, or display IDs. |
| `DEC-APP-02` | **Historical Display ID Prefix** | `ADR-001` | Secondary display IDs (e.g., `MOV-000001`) assigned once. Prefix is historical at creation; current classification determined solely by `content_type`. |
| `DEC-APP-03` | **Title / Edition / Release Model** | `ADR-002` | Adopt `Title -> Edition -> Release`. Every Title has 1 Primary Edition. Additional Editions created ONLY for material content cuts. |
| `DEC-APP-04` | **Episodic Structure Independence** | `ADR-002` | `Title -> Season -> Episode`. Episode identity independent of sequence numbering. |
| `DEC-APP-05` | **Extensible Franchise Model** | `ADR-002` | `Universe -> Franchise -> Title` via `FranchiseEntry`. Extensible order type + position. Hard-coded order columns prohibited. |
| `DEC-APP-06` | **Append-Only Watch History** | `ADR-003` | Watch Events are append-only. No silent overwrites or duplicate deletion via time-proximity heuristics. |
| `DEC-APP-07` | **Unknown Edition Semantics** | `ADR-003` | `WatchEvent.edition_id = NULL` means Edition is unknown, NOT Primary Edition. |
| `DEC-APP-08` | **Derived Read Models** | `ADR-003` | `UserProgress` and rewatch statistics are cached read models derived from Watch Events. |
| `DEC-APP-09` | **Personal Rating Conflicts** | `ADR-003` | Ratings are Title-scoped. Conflicting personal ratings during merges MUST NOT be silently averaged or overwritten. |
| `DEC-APP-10` | **Separate Notes & Reviews** | `ADR-003` | `UserNote` (private) and `UserReview` (publishable) are strictly separate entities. |
| `DEC-APP-11` | **Durable Offline Outbox** | `ADR-004` | Flutter sync uses outbox with client `MutationID` for idempotency safety. |
| `DEC-APP-12` | **No Blind LWW Conflict Handling** | `ADR-004` | LWW prohibited for Watch Events, Ratings, Reviews, Notes, Canonical metadata, and Merges. |
| `DEC-APP-13` | **Data Ownership Classes** | `ADR-004` | 6 distinct data ownership classes governing modification, deletion, and retention rights. |
| `DEC-APP-14` | **Entity-Scoped External Mappings** | `ADR-001`, Prompt | Entity-scoped mapping tables (`TitleExternalId`, etc.) preferred over generic polymorphic foreign keys. |

---

### B. DERIVED DECISIONS (Direct Consequences of Approved Architecture)

| Decision ID | Decision Title | Source Approved Decision | Summary of Derived Decision |
|---|---|---|---|
| `DEC-DER-01` | **Persisted Primary Edition Row** | `ADR-002` | Because every Title must have a Primary Edition, every Title row is created with exactly one linked `Edition` row where `is_primary = true`. |
| `DEC-DER-02` | **Denormalized Title FK on Episode** | `ADR-002` | `Episode` entity includes direct `title_id` FK alongside `season_id` to optimize Title-level episodic queries without joining Season. |
| `DEC-DER-03` | **Watch Event Correction Entity** | `ADR-003` | `WatchEventCorrection` entity created to support non-destructive event tombstones (Original Event -> Correction -> Corrected Event). |
| `DEC-DER-04` | **Role-Based Country/Language Tables** | Prompt, `ADR-001` | Created `TitleCountry`, `TitleLanguage`, `EditionLanguage` relationship entities to eliminate overloaded scalar country/language strings. |
| `DEC-DER-05` | **Award & Festival Entity Separation** | Master Concept | Modeled `Award`, `AwardCategory`, `AwardEvent`, `AwardResult`, `Festival`, `FestivalEdition`, and `FestivalParticipation` as explicit domain entities. |
| `DEC-DER-06` | **IdentityRedirect Tombstoning** | `ADR-001`, `ADR-004` | `IdentityRedirect` entity created to preserve historical UUID resolution after canonical Title or Person merges. |
| `DEC-DER-07` | **Title-Scoped Library Membership** | `ADR-003` | `LibraryEntry` connects `User` and `Title`, storing optional `preferred_edition_id` as a non-identifying preference attribute. |

---

### C. PROPOSED DECISIONS (Requiring Project Owner Approval)

| Decision ID | Decision Title | Proposed Recommendation | Rationale & Impact | Owner Action Required |
|---|---|---|---|---|
| `DEC-PRP-01` | **Explicit Award & Festival Entity Set** | Adopt the 7 explicit domain entities for Awards (`Award`, `AwardCategory`, `AwardEvent`, `AwardResult`) and Festivals (`Festival`, `FestivalEdition`, `FestivalParticipation`). | Prevents string duplication and enables structured cultural/historical analytics & recommendation filtering. | **Review & Approve** |
| `DEC-PRP-02` | **Derived Status vs Manual Override Mechanics** | Model `UserTitleState` with both `derived_status` (calculated from Watch Events) and `manual_status_override` (user explicit choice). | Resolves status ambiguity without discarding explicit user preferences. | **Review & Approve** |
| `DEC-PRP-03` | **Conflict & Ambiguity Resolution Queues** | Introduce conceptual `PersonalDataConflict` and `UserSplitResolution` queues for title merge/split operations. | Isolates unresolved personal data conflicts until explicit user resolution occurs. | **Review & Approve** |
| `DEC-PRP-04` | **`PlatformOffer` Validity Bounds** | Use `valid_from` (Timestamp) and `valid_until` (Timestamp, NULL = active) for streaming availability intervals. | Accurately models temporary subscription windows (e.g., leaving Netflix on date X). | **Review & Approve** |

---

### D. DEFERRED DECISIONS (Intentionally Postponed)

| Decision ID | Decision Title | Level / Scope | Reason for Deferral | Target Phase |
|---|---|---|---|---|
| `DEC-DEF-01` | **Physical PostgreSQL DDL & Data Types** | Physical Database | Schema specification is conceptual/logical. DDL creation happens in Physical DB Phase. | Physical Schema Phase |
| `DEC-DEF-02` | **PostgreSQL Indexing & Partitioning Strategy** | Physical Database | Index and table partitioning choices depend on actual query load and dataset scale. | Performance & DB Phase |
| `DEC-DEF-03` | **Alternate Cut Scene-by-Scene Delta Schema** | Detailed Domain | Scene-level video segment diffing is beyond initial MVP catalog requirements. | Advanced Cut Engine Phase |
| `DEC-DEF-04` | **Regional Episode Ordering Schema** | Ingestion / Taxonomy | Regional broadcast vs home video episode ordering variants require provider taxonomy review. | Ingestion Pipeline Phase |
| `DEC-DEF-05` | **Offline Sync Mutation Payload Schema** | Synchronization Protocol | Exact JSON mutation payload schemas belong to Offline Sync protocol specification. | Sync Protocol Phase |
| `DEC-DEF-06` | **Physical Provenance Schema** | Ingestion / Provenance | Marked as `DEFERRED — INGESTION / PROVENANCE REVIEW`. | Ingestion Review Phase |
| `DEC-DEF-07` | **Physical Audit Log DDL** | Audit / Security | Marked as `DEFERRED — AUDIT / SECURITY REVIEW`. | Audit & Security Phase |
| `DEC-DEF-08` | **Personal Data Backup Retention Policy** | Privacy & Operations | Backup purging timeline & legal retention policy requires privacy compliance review. | Privacy Policy Phase |

---

### E. BLOCKED DECISIONS (Awaiting Upstream Resolution)

| Decision ID | Decision Title | Blocking Constraint / Dependency | Required Resolution |
|---|---|---|---|
| *None* | *No decisions are currently blocked.* | *All pre-requisite architecture reviews and ADRs are complete.* | *N/A* |

---

## 3. Approval Request Summary

The project owner is requested to review and approve the four **PROPOSED DECISIONS** (`DEC-PRP-01` through `DEC-PRP-04`) during the Data Model Specification review.
