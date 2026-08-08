# CineVault OS — Data Model Architecture Consistency Check

**Document Type:** Pre-Modeling Architectural Verification & Consistency Audit  
**Status:** Complete  
**Date:** 2026-08-08  
**Scope:** Canonical Documents, Accepted ADRs (ADR-001 through ADR-004), Master Concept, Technical Requirements, and AI Handoff Context  

---

## 1. Executive Summary

Before constructing the conceptual and logical data model specifications and ERD for CineVault OS, this Architecture Consistency Check verifies that the approved baseline architecture is fully coherent and free of unresolvable internal contradictions.

All canonical baseline materials in `docs/canonical/` and accepted Architecture Decision Records in `docs/adr/` have been audited.

The primary rule of governance applied during this check is:

```text
Accepted ADR > Older Proposed Architecture / Draft Concept
```

---

## 2. Confirmed Architecture Concepts

The following fundamental architectural decisions are confirmed as **Accepted Baseline Constraints**:

### A. Canonical Identity & Classification
1. **Canonical Identity:** Permanent internal identity uses **UUIDv7**, generated internally, immutable, never reused, independent of external providers, independent of content type, and independent of display IDs (`ADR-001`).
2. **Human-Readable Display ID:** Secondary display identifiers (e.g., `MOV-000001`, `SER-000001`, `ANI-000001`) are assigned once upon creation. Their prefix reflects historical classification at creation time.
3. **Content Classification:** `content_type` is the single authoritative current classification. Reclassification updates `content_type` but **never** alters the canonical UUIDv7 or human-readable display ID (`ADR-001`).

### B. Entertainment Domain Hierarchy
4. **Title / Edition / Release Model:**
   ```text
   Title
     └── Edition [PRIMARY] (Required 1:1 conceptual mapping, additional Editions optional)
           └── Release(s) (0 to N distribution events)
   ```
   * **Title:** Abstract creative work.
   * **Edition:** Materially distinct version of content (e.g., theatrical cut, director's cut, uncensored, extended).
   * **Primary Edition:** Every Title conceptually and structural possesses exactly one persisted Primary Edition. Additional Editions exist only for material content variations (`ADR-002`).
   * **Release:** Real-world distribution event (e.g., festival premiere, theatrical run, streaming launch, physical home video release) for a specific Edition (`ADR-002`).
5. **Episodic Model:**
   ```text
   Title
     └── Season
           └── Episode
   ```
   Episodic structure is conceptually distinct from `Edition -> Release`. Episode identity is strictly independent of human-facing display sequence or episode numbers (`ADR-002`).
6. **Franchise / Universe Model:**
   ```text
   Universe
      └── Franchise (0 to N)
            └── Title (M:N participation via FranchiseEntry)
   ```
   Franchise ordering uses an extensible entry-based model: `FranchiseEntry + OrderType + Position`. Hard-coded columns (e.g., `release_order`, `chronological_order`) are prohibited (`ADR-002`).

### C. External Mappings & Taxonomy
7. **External Identity:** Mappings to external providers (IMDb, TMDb, AniList, MyAnimeList, TVDB, JustWatch, Wikidata) use entity-scoped tables (`TitleExternalId`, `EpisodeExternalId`, `PersonExternalId`, `FranchiseExternalId`). Generic polymorphic foreign keys (`entity_type` + `entity_id`) are prohibited (`ADR-001`).
8. **Country Taxonomy:** Relational roles replace overloaded scalar attributes (`title.country`). Minimum distinct roles: Production Country, Filming Country, Country of Origin, Release Territory, Availability Region.
9. **Language Taxonomy:** Relational roles replace overloaded scalar attributes (`title.language`). Minimum distinct roles: Original Language, Audio Language, Subtitle Language, Dubbed Language.

### D. User Domain & Ownership
10. **Library:** Title-scoped. A `LibraryEntry` connects `User` and `Title`, optionally containing a user `preferred_edition` preference (`ADR-003`).
11. **Watch Events:** Append-only historical viewing records. Linked to `Title`, and optionally to `Edition`, `Season`, `Episode`. An omitted `edition_id` (`NULL`) signifies **unknown/unspecified edition**, NOT automatically Primary Edition (`ADR-003`).
12. **Watch Event Corrections:** Watch events must not be silently overwritten. Corrections use a historical-preserving approach (Original Event -> Tombstone / Correction -> Corrected Event) (`ADR-003`).
13. **Derived Progress & Rewatch:** `UserProgress` and rewatch statistics are computed/cached read models derived from Watch Events, not independent authoritative sources of truth (`ADR-003`).
14. **Ratings, Reviews, Notes:**
    * **Ratings:** Title-scoped by default. Personal conflict resolution requires human or governed intervention (`ADR-003`).
    * **Notes vs Reviews:** `UserNote` (private by default) and `UserReview` (publishable with distinct privacy semantics) are strictly separate entities (`ADR-003`).
15. **Data Ownership Classes:** Six distinct classes governed by different modification, deletion, and retention rules (`ADR-004`):
    1. Canonical platform data
    2. User-owned personal data
    3. Derived data
    4. Operational/audit data
    5. External-source data
    6. AI-generated proposals (never automatically canonical)
16. **Offline Sync & Conflict Resolution:** Client outbox with durable `MutationID`. Last-Write-Wins (LWW) is permitted ONLY for low-risk designated state, and explicitly **prohibited** for Watch Events, Ratings, Reviews, Notes, Canonical metadata, Merge decisions, and Deletion (`ADR-004`).
17. **Privacy & Audit:** User deletion permanently purges personal data. Operational/audit logs retain redacted metadata necessary for accountability, but must never become a permanent copy of deleted personal content (`ADR-004`).

---

## 3. Contradictions & Discrepancies Analyzed

The audit identified four historical discrepancies between early concept drafts (`docs/canonical/`) and accepted ADRs (`docs/adr/`). Per project governance, all discrepancies are resolved in favor of the accepted ADRs.

| # | Topic | Early Concept Draft (`docs/canonical/`) | Accepted ADR Baseline (`docs/adr/`) | Resolution & Action |
|---|---|---|---|---|
| 1 | **Display ID Prefix Authority** | `CINEVAULT_OS_MASTER_CONCEPT.md` Section 5 suggested display ID prefix (`MOV-`, `SER-`) defines entity type. | `ADR-001` Section "Human-Readable Identity": Prefix is historical at creation. Current type is determined exclusively by `content_type`. | **ADR-001 Authoritative:** Display ID prefix is non-semantic after creation. Data model will enforce `content_type` as authoritative classification. |
| 2 | **Hierarchy Ordering Draft** | `CINEVAULT_OS_AI_HANDOFF_CONTEXT.md` Section "Title / Release / Edition" suggested `Title -> Release -> Edition`. | `ADR-002` Section "Decision": Adopted `Title -> Edition -> Release`. Material content difference = Edition; Distribution difference = Release. | **ADR-002 Authoritative:** Conceptual model is strictly `Title -> Edition -> Release`. Releases belong to Editions. |
| 3 | **Scalar Country/Language Fields** | `CINEVAULT_OS_MASTER_CONCEPT.md` Section 9 listed `Country` and `Primary language` as simple title attributes. | Prompt Rule 10 & `ADR-001`/`ADR-002` context: Country and language must be relationship-based concepts with explicit roles. | **Prompt & ADR Authoritative:** Scalar overloaded fields prohibited. Model uses role-based relationship entities. |
| 4 | **Polymorphic Mapping Tables** | `CINEVAULT_OS_TECHNICAL_REQUIREMENTS.md` draft mentioned generic external ID mapping. | Prompt Rule 9 & `ADR-001`: Entity-scoped mappings preferred; polymorphic FKs (`entity_type` + `entity_id`) prohibited if compromising referential integrity. | **Prompt & ADR-001 Authoritative:** Entity-scoped mapping tables (`TitleExternalId`, `EpisodeExternalId`, etc.) specified. |

---

## 4. Deferred Decisions Matrix

The following design aspects are explicitly marked as **DEFERRED** in approved ADRs and must not be silently finalized during conceptual data modeling:

1. **Exact PostgreSQL Types, Indexes, Constraints, & Partitioning:** Deferred to Physical Schema Phase.
2. **Exact Episode Versioning & Alternate Cut Variations:** Deferred to specialized episodic review.
3. **Exact Regional Episode Ordering Schema:** Deferred to ingestion/regional taxonomy review.
4. **Exact Outbox & Synchronization Payload Schema:** Deferred to Offline Sync Protocol phase.
5. **Exact Physical Conflict & Resolution Table Schema:** Deferred to Conflict Engine specification.
6. **Exact Physical Provenance Schema:** Marked as `DEFERRED — INGESTION / PROVENANCE REVIEW`.
7. **Exact Physical Audit Schema:** Marked as `DEFERRED — AUDIT / SECURITY REVIEW`.
8. **Exact Retention Periods & Backup Purge Policy:** Deferred to Privacy & Operational Policy phase.

---

## 5. Negative Invariants (What Must NOT Be Done)

To maintain architectural integrity, the data model design MUST adhere to the following negative invariants:

1. ❌ **DO NOT** use external IDs (IMDb ID, TMDb ID) as canonical primary keys.
2. ❌ **DO NOT** infer `content_type` from human-readable display ID prefixes (`MOV-`, `SER-`).
3. ❌ **DO NOT** create a new `Edition` for pure distribution differences (e.g., 4K Blu-ray vs Netflix stream of the same cut).
4. ❌ **DO NOT** model `WatchEvent.edition_id = NULL` as meaning "Primary Edition". It strictly means "Unknown Edition".
5. ❌ **DO NOT** silently merge or average conflicting user ratings (e.g., Rating 7 and Rating 9 during canonical merge).
6. ❌ **DO NOT** concatenate user notes (e.g., `Note A + "\n" + Note B`) during title merges.
7. ❌ **DO NOT** combine `UserNote` (private) and `UserReview` (publishable) into a single entity.
8. ❌ **DO NOT** use Last-Write-Wins (LWW) conflict resolution for Watch Events, Ratings, Reviews, Notes, or Merges.
9. ❌ **DO NOT** create hard-coded franchise ordering columns (`release_order`, `chronological_order`) on titles or franchises.
10. ❌ **DO NOT** use generic polymorphic foreign keys (`entity_type`, `entity_id`) for core external ID mappings.
