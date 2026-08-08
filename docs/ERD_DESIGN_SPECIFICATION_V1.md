# CineVault OS — ERD Design Specification v1.0

**Document Type:** Relationship Structural Specification Precursor to Logical/Conceptual ERD  
**Status:** Architecture Baseline  
**Date:** 2026-08-08  
**Scope:** Relationship Definitions, Cardinalities, Optionalities, Ownership Boundaries, Lifecycle Behaviors  

---

## 1. Governance & Relationship Principles

This ERD Design Specification establishes the precise structural mechanics, cardinalities, optionalities, ownership boundaries, and operational lifecycle rules for every relationship in the CineVault OS data model prior to ERD diagrammatic rendering.

### Lifecycle Behaviors Defined
* **Delete Behavior:**
  * `CASCADE`: Deleting parent automatically removes dependent child entities.
  * `RESTRICT`: Parent deletion blocked if dependent child entities exist.
  * `SET_NULL`: Foreign key reference cleared to `NULL` upon parent deletion.
  * `TOMBSTONE`: Parent soft-deleted; historical tombstone audit record created.
* **Merge Behavior:**
  * `REPARENT`: Re-point child foreign key from retired parent entity to surviving parent entity.
  * `MERGE_ENTITIES`: Combine duplicate child entities into a single canonical entity.
  * `PRESERVE_CONFLICT`: Retain both child records in a conflict resolution queue for human review.
* **Split Behavior:**
  * `REPARENT_EXPLICIT`: Assign child to designated target split entity.
  * `AMBIGUITY_REVIEW`: Place child in user/administrator resolution queue; do NOT guess assignment or duplicate automatically.

---

## 2. Structural Relationship Inventory

### A. Canonical Content Hierarchy Relationships

| Relationship ID | Entity A | Relationship Name | Entity B | Cardinality | Optionality | Ownership Boundary | Delete Behavior | Merge Behavior | Split Behavior | Constraint Requirements |
|---|---|---|---|---|---|---|---|---|---|---|
| `REL-01` | **Title** | HAS_PRIMARY_EDITION | **Edition** | 1 : 1 | Required (Title MUST have primary edition) | Canonical Platform | RESTRICT | REPARENT | REPARENT_EXPLICIT | Exactly 1 Edition with `is_primary = true` per Title. |
| `REL-02` | **Title** | HAS_ADDITIONAL_EDITION | **Edition** | 1 : N | Optional (0 to N non-primary editions) | Canonical Platform | CASCADE | MERGE_ENTITIES / REPARENT | REPARENT_EXPLICIT | Non-primary editions exist ONLY for material content cuts (`ADR-002`). |
| `REL-03` | **Edition** | HAS_RELEASE | **Release** | 1 : N | Optional (0 to N distribution releases) | Canonical Platform | CASCADE | REPARENT | REPARENT_EXPLICIT | Release represents distribution event, NOT subscription interval. |
| `REL-04` | **Title** | HAS_SEASON | **Season** | 1 : N | Optional (Only for episodic titles) | Canonical Platform | CASCADE | REPARENT | REPARENT_EXPLICIT | `season_number` must be unique per Title. |
| `REL-05` | **Season** | HAS_EPISODE | **Episode** | 1 : N | Optional (0 to N episodes per season) | Canonical Platform | CASCADE | REPARENT | REPARENT_EXPLICIT | `episode_number` default order; display sequence independent of `episode_id`. |
| `REL-06` | **Title** | HAS_EPISODE_DIRECT | **Episode** | 1 : N | Required (Episode belongs to Title) | Canonical Platform | RESTRICT | REPARENT | REPARENT_EXPLICIT | Denormalized FK `title_id` on Episode for query optimization. |

---

### B. Franchise & Universe Relationships

| Relationship ID | Entity A | Relationship Name | Entity B | Cardinality | Optionality | Ownership Boundary | Delete Behavior | Merge Behavior | Split Behavior | Constraint Requirements |
|---|---|---|---|---|---|---|---|---|---|---|
| `REL-07` | **Universe** | CONTAINS_FRANCHISE | **Franchise** | 1 : N | Optional (0 to N franchises per universe) | Canonical Platform | SET_NULL | REPARENT | REPARENT_EXPLICIT | Universe represents overarching IP. |
| `REL-08` | **Franchise** | HAS_ENTRY | **FranchiseEntry** | 1 : N | Optional | Canonical Platform | CASCADE | REPARENT | REPARENT_EXPLICIT | `FranchiseEntry` encapsulates order type + position. |
| `REL-09` | **Title** | INCLUDED_IN_FRANCHISE | **FranchiseEntry** | 1 : N | Optional (Title can belong to N franchises) | Canonical Platform | CASCADE | REPARENT | AMBIGUITY_REVIEW | Hard-coded order columns on Title prohibited (`ADR-002`). |

---

### C. Distribution & Platform Availability Relationships

| Relationship ID | Entity A | Relationship Name | Entity B | Cardinality | Optionality | Ownership Boundary | Delete Behavior | Merge Behavior | Split Behavior | Constraint Requirements |
|---|---|---|---|---|---|---|---|---|---|---|
| `REL-10` | **Release** | DISTRIBUTED_VIA | **PlatformOffer** | 1 : N | Optional | Canonical / External | CASCADE | REPARENT | REPARENT_EXPLICIT | `PlatformOffer` is temporal & regional. |
| `REL-11` | **Platform** | PROVIDES_OFFER | **PlatformOffer** | 1 : N | Optional | Canonical Platform | RESTRICT | MERGE_ENTITIES | REPARENT_EXPLICIT | `platform_id` must reference valid Platform. |
| `REL-12` | **Country** | OFFER_REGION | **PlatformOffer** | 1 : N | Optional | Canonical Platform | RESTRICT | REPARENT | REPARENT_EXPLICIT | Country role = Availability Region. |

---

### D. People & Credit Relationships

| Relationship ID | Entity A | Relationship Name | Entity B | Cardinality | Optionality | Ownership Boundary | Delete Behavior | Merge Behavior | Split Behavior | Constraint Requirements |
|---|---|---|---|---|---|---|---|---|---|---|
| `REL-13` | **Person** | HAS_CREDIT | **Credit** | 1 : N | Optional | Canonical Platform | RESTRICT | REPARENT | REPARENT_EXPLICIT | Person primary key = UUIDv7. |
| `REL-14` | **Title** | HAS_CREDIT_TITLE | **Credit** | 1 : N | Optional | Canonical Platform | CASCADE | REPARENT | REPARENT_EXPLICIT | Credit MUST reference Title, Edition, or Episode. |
| `REL-15` | **Character** | PORTRAYED_IN | **Credit** | 1 : N | Optional | Canonical Platform | SET_NULL | MERGE_ENTITIES | REPARENT_EXPLICIT | Character reference optional on cast credits. |

---

### E. External Identity Mapping Relationships

| Relationship ID | Entity A | Relationship Name | Entity B | Cardinality | Optionality | Ownership Boundary | Delete Behavior | Merge Behavior | Split Behavior | Constraint Requirements |
|---|---|---|---|---|---|---|---|---|---|---|
| `REL-16` | **Title** | MAPPED_TO_EXTERNAL | **TitleExternalId** | 1 : N | Optional | Canonical / External | CASCADE | REPARENT | REPARENT_EXPLICIT | `(provider, external_id)` unique constraint (`ADR-001`). |
| `REL-17` | **Episode** | MAPPED_TO_EXTERNAL | **EpisodeExternalId** | 1 : N | Optional | Canonical / External | CASCADE | REPARENT | REPARENT_EXPLICIT | Entity-scoped mapping table (`ADR-001`). |
| `REL-18` | **Person** | MAPPED_TO_EXTERNAL | **PersonExternalId** | 1 : N | Optional | Canonical / External | CASCADE | REPARENT | REPARENT_EXPLICIT | Entity-scoped mapping table (`ADR-001`). |
| `REL-19` | **Franchise** | MAPPED_TO_EXTERNAL | **FranchiseExternalId** | 1 : N | Optional | Canonical / External | CASCADE | REPARENT | REPARENT_EXPLICIT | Entity-scoped mapping table (`ADR-001`). |

---

### F. Taxonomy & Geographic/Language Role Relationships

| Relationship ID | Entity A | Relationship Name | Entity B | Cardinality | Optionality | Ownership Boundary | Delete Behavior | Merge Behavior | Split Behavior | Constraint Requirements |
|---|---|---|---|---|---|---|---|---|---|---|
| `REL-20` | **Title** | PRODUCTION_COUNTRY | **TitleCountry** | 1 : N | Optional | Canonical Platform | CASCADE | REPARENT | REPARENT_EXPLICIT | Role = Production, Filming, or Origin. Scalar country prohibited. |
| `REL-21` | **Title** | ORIGINAL_LANGUAGE | **TitleLanguage** | 1 : N | Optional | Canonical Platform | CASCADE | REPARENT | REPARENT_EXPLICIT | Role = Original Language. Scalar language prohibited. |
| `REL-22` | **Edition** | AUDIO_SUB_DUB_LANG | **EditionLanguage** | 1 : N | Optional | Canonical Platform | CASCADE | REPARENT | REPARENT_EXPLICIT | Role = Audio, Subtitle, or Dubbed. |

---

### G. User Domain Relationships

| Relationship ID | Entity A | Relationship Name | Entity B | Cardinality | Optionality | Ownership Boundary | Delete Behavior | Merge Behavior | Split Behavior | Constraint Requirements |
|---|---|---|---|---|---|---|---|---|---|---|
| `REL-23` | **User** | HAS_LIBRARY_ENTRY | **LibraryEntry** | 1 : N | Optional | User-Owned Personal | CASCADE | REPARENT | AMBIGUITY_REVIEW | Library membership is **Title-scoped** (`ADR-003`). |
| `REL-24` | **LibraryEntry** | PREFERS_EDITION | **Edition** | N : 0..1 | Optional | User Preference | SET_NULL | REPARENT | REPARENT_EXPLICIT | `preferred_edition` does NOT change canonical Title identity. |
| `REL-25` | **User** | LOGGED_WATCH_EVENT | **WatchEvent** | 1 : N | Optional | User-Owned Personal | CASCADE | REPARENT | AMBIGUITY_REVIEW | Append-only event. Immutable (`ADR-003`). |
| `REL-26` | **WatchEvent** | WATCHED_TITLE | **Title** | N : 1 | Required | Personal -> Canonical | RESTRICT | REPARENT | AMBIGUITY_REVIEW | `title_id` required (`ADR-003`). |
| `REL-27` | **WatchEvent** | WATCHED_EDITION | **Edition** | N : 0..1 | Optional | Personal -> Canonical | SET_NULL | REPARENT | AMBIGUITY_REVIEW | `edition_id = NULL` means **unknown edition**, NOT primary (`ADR-003`). |
| `REL-28` | **WatchEvent** | WATCHED_EPISODE | **Episode** | N : 0..1 | Optional | Personal -> Canonical | SET_NULL | REPARENT | AMBIGUITY_REVIEW | Optional reference to specific episode. |
| `REL-29` | **User** | RATED_TITLE | **UserRating** | 1 : N | Optional | User-Owned Personal | CASCADE | PRESERVE_CONFLICT | AMBIGUITY_REVIEW | Title-scoped rating. NO silent averaging on merge (`ADR-003`). |
| `REL-30` | **User** | AUTHORED_REVIEW | **UserReview** | 1 : N | Optional | User-Owned Personal | CASCADE | PRESERVE_CONFLICT | AMBIGUITY_REVIEW | Publishable review. Separate from UserNote (`ADR-003`). |
| `REL-31` | **User** | AUTHORED_NOTE | **UserNote** | 1 : N | Optional | User-Owned Personal | CASCADE | PRESERVE_CONFLICT | AMBIGUITY_REVIEW | Private note. NO silent string concatenation on merge (`ADR-003`). |
| `REL-32` | **User** | HAS_TITLE_STATE | **UserTitleState** | 1 : N | Optional | User-Owned Personal | CASCADE | REPARENT | AMBIGUITY_REVIEW | Explicit separation of derived status vs manual override (`ADR-003`). |

---

## 3. Comprehensive Cardinality Matrix Summary

```text
Title ──────────── (1 : 1) ──────────── Primary Edition
Title ──────────── (1 : 0..N) ───────── Additional Edition
Edition ────────── (1 : 0..N) ───────── Release
Release ────────── (1 : 0..N) ───────── PlatformOffer
Title ──────────── (1 : 0..N) ───────── Season
Season ─────────── (1 : 0..N) ───────── Episode
Universe ───────── (1 : 0..N) ───────── Franchise
Franchise ──────── (1 : 0..N) ───────── FranchiseEntry ──────── (N : 1) ──────── Title
User ───────────── (1 : 0..N) ───────── LibraryEntry ─────────── (N : 1) ──────── Title
User ───────────── (1 : 0..N) ───────── WatchEvent ───────────── (N : 1) ──────── Title
User ───────────── (1 : 0..N) ───────── UserRating ───────────── (N : 1) ──────── Title
User ───────────── (1 : 0..N) ───────── UserNote ─────────────── (N : 1) ──────── Title
User ───────────── (1 : 0..N) ───────── UserReview ───────────── (N : 1) ──────── Title
```
