# CineVault OS — Data Model Specification v1.0

**Document Type:** Master Conceptual & Logical Data Model Specification  
**Status:** Architecture Baseline Specification  
**Date:** 2026-08-08  
**Scope:** Universal Entertainment Domain, User Domain, External Identity, Taxonomies, Governance & Lifecycle  

---

## 1. Executive & Architecture Overview

This Data Model Specification defines the conceptual and logical entities, relationships, invariants, ownership rules, and lifecycle behaviors for **CineVault OS**.

### Core Structural Principles

1. **Identity:** All canonical domain entities receive a permanent internal **UUIDv7** primary key. Human-readable display IDs (`MOV-000001`, etc.) are historical secondary identifiers. External provider IDs exist exclusively in entity-scoped mapping tables (`ADR-001`).
2. **Classification:** `content_type` is the authoritative classification. Reclassification preserves UUIDv7 and display IDs (`ADR-001`).
3. **Content Hierarchy:** `Title -> Edition -> Release`. Every Title possesses exactly one persisted **Primary Edition**. Additional Editions represent material content variations (`ADR-002`).
4. **Episodic Structure:** `Title -> Season -> Episode`. Episodic sequence is independent of Episode identity (`ADR-002`).
5. **Franchise Hierarchy:** `Universe -> Franchise -> Title`. Extensible ordering uses `FranchiseEntry + OrderType + Position` (`ADR-002`).
6. **Data Ownership:** Strict boundaries separate Canonical Platform Data, User-Owned Personal Data, Derived Data, Operational/Audit Data, External-Source Data, and AI-Generated Proposals (`ADR-004`).
7. **Personal Data Safety:** Append-only Watch Events, title-scoped Ratings, distinct Notes vs Reviews. Zero silent merges, zero silent concatenations, zero destructive LWW conflict resolution (`ADR-003`, `ADR-004`).

---

## 2. Data Ownership Classes Matrix

| Category ID | Ownership Class | Authoritative vs Derived | Retention / Deletion Policy | Modification Rules |
|---|---|---|---|---|
| `CAT-1` | **Canonical Platform Data** | Authoritative | Permanent platform catalog; soft-delete via Tombstone on merge/split | Governance & Ingestion pipeline with validation |
| `CAT-2` | **User-Owned Personal Data** | Authoritative | Subject to full user export & deletion rights | User-driven via durable offline sync mutations |
| `CAT-3` | **Derived Data** | Derived (Read Model) | Rebuildable at any time from CAT-1 & CAT-2 | Automated background processing / triggers |
| `CAT-4` | **Operational / Audit Data** | Operational | Time-bounded; redacted upon personal data deletion | Append-only system logging |
| `CAT-5` | **External-Source Data** | Staged / Reference | Refreshable from external providers | Ingestion pipeline updates |
| `CAT-6` | **AI-Generated Proposals** | Proposal | Expirable; requires review before promotion to CAT-1 | Human review or confidence-gated pipeline |

---

## 3. Canonical Content Domain Entities

---

### Entity: Title
* **Purpose:** Represents the abstract creative work (e.g., *The Dark Knight*, *Breaking Bad*, *Spirited Away*).
* **Ownership Category:** `CAT-1` (Canonical Platform Data)
* **Authoritative / Derived:** Authoritative
* **Canonical Identity:** UUIDv7 (`title_id`)
* **Display Identity:** `display_id` (e.g., `MOV-000001`, `SER-000001`; historical prefix, immutable)
* **Required Attributes:** `title_id` (UUIDv7), `display_id` (String, Unique), `content_type` (Enum/Ref), `canonical_title` (String), `original_title` (String), `created_at` (Timestamp), `updated_at` (Timestamp).
* **Optional Attributes:** `tagline` (String), `synopsis` (Text), `production_year` (Integer).
* **Required Relationships:**
  * Has 1:N `Edition` (Minimum 1, exactly one flagged `is_primary = true`).
  * Belongs to 1 `ContentType`.
* **Optional Relationships:**
  * Has 0:N `Season` (For episodic titles).
  * Has 0:N `Credit`.
  * Has 0:N `TitleCountry` (Role-based: Production, Filming, Origin).
  * Has 0:N `TitleLanguage` (Role-based: Original Language).
  * Has 0:N `TitleExternalId`.
  * Participates in 0:N `FranchiseEntry`.
  * Has 0:N `TitleGenre`, `TitleTheme`, `TitleKeyword`.
* **Cardinalities:** Title (1) ── (1..N) Edition; Title (1) ── (0..N) Season.
* **Invariants:**
  * Must have exactly one Primary Edition (`is_primary = true`).
  * Changing `content_type` must never alter `title_id` or `display_id`.
* **External ID Support:** Supported via `TitleExternalId`.
* **Provenance Requirement:** Field-level provenance required for external metadata fields.
* **Audit Requirement:** All structural updates and reclassifications logged in `CanonicalAuditLog`.
* **Merge Behavior:** Surviving Title retains identity. Retiring Title receives `IdentityRedirect`. Personal data remains isolated.
* **Split Behavior:** New Titles created. Personal data flagged for human review if ambiguous.
* **Deletion Behavior:** Soft delete / Tombstone only. Never hard deleted if referenced by User data.
* **Deferred Decisions:** None.

---

### Entity: Edition
* **Purpose:** Represents a materially distinct content version of a Title (e.g., Theatrical Cut, Director's Cut, Extended Cut, Uncensored Version).
* **Ownership Category:** `CAT-1` (Canonical Platform Data)
* **Authoritative / Derived:** Authoritative
* **Canonical Identity:** UUIDv7 (`edition_id`)
* **Required Attributes:** `edition_id` (UUIDv7), `title_id` (UUIDv7, FK), `edition_name` (String, e.g., "Theatrical Cut"), `is_primary` (Boolean), `created_at` (Timestamp).
* **Optional Attributes:** `runtime_minutes` (Integer), `aspect_ratio` (String), `color_format` (String), `sound_mix` (String), `edition_notes` (Text).
* **Required Relationships:**
  * Belongs to 1 `Title`.
  * Has 0:N `Release`.
* **Optional Relationships:**
  * Has 0:N `EditionLanguage` (Audio, Subtitle, Dubbed).
  * Has 0:N `Credit` (Edition-specific cast/crew variations).
* **Cardinalities:** Title (1) ── (1..N) Edition; Edition (1) ── (0..N) Release.
* **Invariants:**
  * Pure distribution differences (e.g., 4K vs 1080p stream) MUST NOT create a new Edition.
  * Every Title MUST have exactly one Edition where `is_primary = true`.
* **External ID Support:** Supported via `EditionExternalId` if provider supports cut-level IDs.
* **Provenance Requirement:** Provenance required on non-primary editions.
* **Audit Requirement:** Audit required on edition creation/modification.
* **Merge Behavior:** Editions merged if determined identical; otherwise re-parented to surviving Title.
* **Split Behavior:** Re-parented to appropriate split Title.
* **Deletion Behavior:** Primary Edition cannot be deleted unless the parent Title is retired.
* **Deferred Decisions:** Alternate cut scene-by-scene delta modeling deferred.

---

### Entity: Release
* **Purpose:** Represents a real-world distribution event for a specific Edition (e.g., Festival Premiere, Regional Theatrical Release, Streaming Launch, Physical 4K UHD release).
* **Ownership Category:** `CAT-1` (Canonical Platform Data)
* **Authoritative / Derived:** Authoritative
* **Canonical Identity:** UUIDv7 (`release_id`)
* **Required Attributes:** `release_id` (UUIDv7), `edition_id` (UUIDv7, FK), `release_type` (Enum: Festival, Theatrical, TV, Streaming, Physical, Digital, ReRelease), `created_at` (Timestamp).
* **Optional Attributes:** `release_date` (Date), `release_name` (String), `certification_id` (UUIDv7, FK).
* **Required Relationships:**
  * Belongs to 1 `Edition`.
* **Optional Relationships:**
  * Has 0:N `ReleaseTerritory` (Country/Region).
  * Has 0:N `Distributor` (Organization).
  * Has 0:N `PlatformOffer`.
* **Cardinalities:** Edition (1) ── (0..N) Release.
* **Invariants:**
  * Release represents a distribution event, NOT a time-bounded subscription availability window (`PlatformOffer`).
* **External ID Support:** Supported where provider links directly to release events.
* **Provenance Requirement:** Required for release dates and territory information.
* **Audit Requirement:** Audit required for release updates.
* **Merge Behavior:** Re-parented to surviving Edition.
* **Split Behavior:** Re-parented to corresponding Edition.
* **Deletion Behavior:** Soft delete.
* **Deferred Decisions:** None.

---

### Entity: Season
* **Purpose:** Represents an episodic grouping/season for an episodic Title.
* **Ownership Category:** `CAT-1` (Canonical Platform Data)
* **Authoritative / Derived:** Authoritative
* **Canonical Identity:** UUIDv7 (`season_id`)
* **Required Attributes:** `season_id` (UUIDv7), `title_id` (UUIDv7, FK), `season_number` (Integer), `canonical_name` (String), `created_at` (Timestamp).
* **Optional Attributes:** `synopsis` (Text), `air_date_start` (Date), `air_date_end` (Date), `poster_path` (String).
* **Required Relationships:**
  * Belongs to 1 `Title`.
  * Has 0:N `Episode`.
* **Cardinalities:** Title (1) ── (0..N) Season; Season (1) ── (0..N) Episode.
* **Invariants:**
  * `season_number` is canonical default ordering, but display ordering can be overridden by `RegionalEpisodeOrder`.
* **External ID Support:** Supported via `SeasonExternalId`.
* **Provenance Requirement:** Required for air dates and episode counts.
* **Audit Requirement:** Audit required on season modifications.
* **Merge Behavior:** Merged with target Season or re-parented to surviving Title.
* **Split Behavior:** Re-parented to appropriate split Title.
* **Deletion Behavior:** Soft delete.
* **Deferred Decisions:** Alternate season groupings (e.g., story arc vs broadcast season) deferred.

---

### Entity: Episode
* **Purpose:** Represents an individual episode within an episodic Title.
* **Ownership Category:** `CAT-1` (Canonical Platform Data)
* **Authoritative / Derived:** Authoritative
* **Canonical Identity:** UUIDv7 (`episode_id`)
* **Required Attributes:** `episode_id` (UUIDv7), `season_id` (UUIDv7, FK), `title_id` (UUIDv7, FK), `episode_number` (Integer), `canonical_title` (String), `created_at` (Timestamp).
* **Optional Attributes:** `synopsis` (Text), `air_date` (Date), `runtime_minutes` (Integer), `production_code` (String).
* **Required Relationships:**
  * Belongs to 1 `Season` and 1 `Title`.
* **Optional Relationships:**
  * Has 0:N `EpisodeExternalId`.
  * Has 0:N `Credit` (Episode-specific cast/crew).
* **Cardinalities:** Season (1) ── (0..N) Episode.
* **Invariants:**
  * Episode identity (`episode_id`) is strictly independent of episode display number. Alternate regional/platform numbers do NOT change `episode_id`.
* **External ID Support:** Supported via `EpisodeExternalId`.
* **Provenance Requirement:** Required for air dates and runtimes.
* **Audit Requirement:** Audit required on episode modification.
* **Merge Behavior:** Merged if identical; re-parented if season is merged.
* **Split Behavior:** Re-parented to target Title/Season.
* **Deletion Behavior:** Soft delete.
* **Deferred Decisions:** `RegionalEpisodeOrder` physical schema deferred.

---

### Entity: Franchise & Universe
* **Purpose:**
  * `Universe`: Broad intellectual property universe (e.g., Marvel Cinematic Universe, Star Wars Universe).
  * `Franchise`: Specific sub-franchise or film series (e.g., *The Avengers Series*, *Star Wars Original Trilogy*).
* **Ownership Category:** `CAT-1` (Canonical Platform Data)
* **Authoritative / Derived:** Authoritative
* **Canonical Identity:** UUIDv7 (`universe_id`, `franchise_id`)
* **Required Relationships:**
  * `Universe` (1) ── (0..N) `Franchise`.
  * `Franchise` (1) ── (0..N) `FranchiseEntry` ── (1) `Title`.
* **Invariants:**
  * Titles participate in Franchises via `FranchiseEntry`. A Title may belong to multiple Franchises.
* **External ID Support:** Supported via `FranchiseExternalId`.
* **Merge/Split Behavior:** Franchises merged or split without altering Title identity.
* **Deferred Decisions:** None.

---

### Entity: FranchiseEntry
* **Purpose:** Represents the M:N relationship between a `Franchise` and a `Title` with extensible viewing order positions.
* **Ownership Category:** `CAT-1` (Canonical Platform Data)
* **Authoritative / Derived:** Authoritative
* **Canonical Identity:** UUIDv7 (`franchise_entry_id`)
* **Required Attributes:** `franchise_entry_id` (UUIDv7), `franchise_id` (UUIDv7, FK), `title_id` (UUIDv7, FK), `order_type` (Enum/Ref: ReleaseOrder, ChronologicalOrder, StoryOrder, RecommendedOrder, CompletionistOrder), `position` (Decimal/Integer).
* **Invariants:** Hard-coded order columns on `Title` or `Franchise` are prohibited.
* **Deferred Decisions:** Custom user-defined franchise ordering deferred to future extensions.

---

### Entity: Platform & PlatformOffer
* **Purpose:**
  * `Platform`: Streaming or distribution platform (e.g., Netflix, Criterion Channel, Apple TV).
  * `PlatformOffer`: Time-bounded, region-specific availability of a Release on a Platform.
* **Ownership Category:** `CAT-1` / `CAT-5` (Canonical / External Source)
* **Authoritative / Derived:** Authoritative availability record
* **Canonical Identity:** UUIDv7 (`platform_id`, `platform_offer_id`)
* **Required Attributes (`PlatformOffer`):** `platform_offer_id` (UUIDv7), `platform_id` (UUIDv7, FK), `release_id` (UUIDv7, FK), `country_id` (UUIDv7, FK), `offer_type` (Enum: Subscription, Rental, Purchase, FreeWithAds), `valid_from` (Timestamp, Optional), `valid_until` (Timestamp, Optional), `last_verified_at` (Timestamp).
* **Invariants:** Availability is temporal and regional. `valid_until = NULL` means currently active / unbounded.
* **Deferred Decisions:** Deep-link URI schema deferred.

---

## 4. People & Credits Domain Entities

---

### Entity: Person
* **Purpose:** Represents a real-world person (actor, director, writer, composer, producer, etc.).
* **Ownership Category:** `CAT-1` (Canonical Platform Data)
* **Canonical Identity:** UUIDv7 (`person_id`)
* **Required Attributes:** `person_id` (UUIDv7), `primary_name` (String), `created_at` (Timestamp).
* **Optional Attributes:** `birth_date` (Date), `death_date` (Date), `birth_place` (String), `bio` (Text).
* **Relationships:** Has 0:N `Credit`, 0:N `PersonExternalId`.
* **Merge/Split:** Merged with `IdentityRedirect` for duplicate persons. Credits reassociated.
* **Deferred Decisions:** None.

---

### Entity: Character
* **Purpose:** Represents a fictional or non-fictional character portrayed in a Title (e.g., *Bruce Wayne / Batman*).
* **Ownership Category:** `CAT-1` (Canonical Platform Data)
* **Canonical Identity:** UUIDv7 (`character_id`)
* **Required Attributes:** `character_id` (UUIDv7), `character_name` (String).
* **Relationships:** Belongs to 0:N `Credit`.
* **Deferred Decisions:** None.

---

### Entity: Credit
* **Purpose:** Represents a contribution by a `Person` to a `Title`, `Edition`, or `Episode`.
* **Ownership Category:** `CAT-1` (Canonical Platform Data)
* **Canonical Identity:** UUIDv7 (`credit_id`)
* **Required Attributes:** `credit_id` (UUIDv7), `person_id` (UUIDv7, FK), `credit_category` (Enum: Cast, Director, Writer, Producer, Composer, Cinematographer, Editor, ProductionDesign, Sound), `billing_order` (Integer, Optional).
* **Optional FKs:** `title_id` (UUIDv7, FK), `edition_id` (UUIDv7, FK), `episode_id` (UUIDv7, FK), `character_id` (UUIDv7, FK).
* **Invariants:** Must reference at least one target entity (`title_id`, `edition_id`, or `episode_id`).
* **Deferred Decisions:** Crew departmental hierarchy deferred.

---

## 5. Classification & Taxonomy Domain Entities

---

### Entities: Genre, Theme, Keyword, ContentType, Certification
* **Purpose:** Standardized taxonomy lookup entities.
* **Ownership Category:** `CAT-1` (Canonical Platform Data)
* **Canonical Identity:** UUIDv7
* **Attributes:** `id` (UUIDv7), `code`/`slug` (String, Unique), `name` (String), `description` (Text, Optional).
* **Invariants:** Managed via governed platform taxonomy updates.

---

### Evaluation: Geographic Model (Country Roles)
* **Entities:** `Country`, `TitleCountry`, `ReleaseTerritory`, `PlatformOfferRegion`.
* **Role Semantics:**
  * `TitleCountry`: Role = `ProductionCountry`, `FilmingCountry`, or `CountryOfOrigin`.
  * `ReleaseTerritory`: Role = `ReleaseTerritory`.
  * `PlatformOfferRegion`: Role = `AvailabilityRegion`.
* **Invariants:** Country MUST NOT be stored as a scalar string on `Title`.

---

### Evaluation: Language Model (Language Roles)
* **Entities:** `Language`, `TitleLanguage`, `EditionLanguage`.
* **Role Semantics:**
  * `TitleLanguage`: Role = `OriginalLanguage` (Title level).
  * `EditionLanguage`: Role = `AudioLanguage`, `SubtitleLanguage`, `DubbedLanguage` (Edition level).
* **Invariants:** Language MUST NOT be stored as a scalar string on `Title`. Distribution languages belong conceptually to `Edition` or `Release`, not `Title`.

---

## 6. Organizations Domain Entities

---

### Entities: ProductionCompany, Network, Distributor
* **Purpose:** Represents industry corporate entities.
* **Ownership Category:** `CAT-1` (Canonical Platform Data)
* **Canonical Identity:** UUIDv7
* **Relationships:** Connected to `Title` (ProductionCompany), `Season`/`Title` (Network), or `Release` (Distributor).

---

## 7. Evaluation: Awards & Festivals Domain

---

### Entity Architectural Evaluation

| Entity Candidate | Domain Role Evaluation | Recommended Conceptual Representation |
|---|---|---|
| `Award` | Domain Entity | **Entity** (`award_id`): Represents the awarding body (e.g., Academy Awards, BAFTA, Cannes Film Festival Palms). |
| `AwardCategory` | Domain Entity | **Entity** (`award_category_id`): Category within an Award (e.g., Best Picture, Best Director). |
| `AwardEvent` | Domain Entity | **Entity** (`award_event_id`): Specific annual instance (e.g., 96th Academy Awards, 2024). |
| `AwardResult` | Relationship Entity | **Entity** (`award_result_id`): Connects `AwardEvent` + `AwardCategory` + `Title`/`Person`/`Credit` with `status` (Nominee, Winner, Honoree). |
| `Festival` | Domain Entity | **Entity** (`festival_id`): Film festival organization (e.g., Venice Film Festival, Sundance). |
| `FestivalEdition` | Domain Entity | **Entity** (`festival_edition_id`): Specific annual festival edition (e.g., 81st Venice International Film Festival). |
| `FestivalParticipation` | Relationship Entity | **Entity** (`festival_participation_id`): Connects `FestivalEdition` + `Title` + `section` (e.g., In Competition, Out of Competition, Premieres). |

* **Reasoning:** Awards and Festivals carry significant cultural and recommendation weight. Modeling results and participations as explicit relationship entities preserves historical precision and prevents data duplication.

---

## 8. User Domain Entities

---

### Entity: User & UserProfile
* **Purpose:** Represents an individual CineVault user account and user display profile settings.
* **Ownership Category:** `CAT-2` (User-Owned Personal Data)
* **Canonical Identity:** UUIDv7 (`user_id`)
* **Required Attributes:** `user_id` (UUIDv7), `username` (String, Unique), `email` (String, Unique), `created_at` (Timestamp).

---

### Entity: LibraryEntry
* **Purpose:** Connects a `User` to a `Title` in their personal collection/library.
* **Ownership Category:** `CAT-2` (User-Owned Personal Data)
* **Authoritative / Derived:** Authoritative
* **Canonical Identity:** UUIDv7 (`library_entry_id`)
* **Required Attributes:** `library_entry_id` (UUIDv7), `user_id` (UUIDv7, FK), `title_id` (UUIDv7, FK), `added_at` (Timestamp).
* **Optional Attributes:** `preferred_edition_id` (UUIDv7, FK, Optional User Preference), `acquisition_type` (Enum: Digital, Physical, Subscription, None).
* **Invariants:**
  * Library membership is **Title-scoped**.
  * `preferred_edition_id` is purely a user display/tracking preference and does NOT change the canonical identity of the Title (`ADR-003`).

---

### Entity: WatchEvent
* **Purpose:** Append-only historical record of a user viewing activity.
* **Ownership Category:** `CAT-2` (User-Owned Personal Data)
* **Authoritative / Derived:** Authoritative (Append-only Event Log)
* **Canonical Identity:** UUIDv7 (`watch_event_id`)
* **Required Attributes:** `watch_event_id` (UUIDv7), `user_id` (UUIDv7, FK), `title_id` (UUIDv7, FK), `watched_at` (Timestamp), `created_at` (Timestamp).
* **Optional FKs:** `edition_id` (UUIDv7, FK, Optional), `season_id` (UUIDv7, FK, Optional), `episode_id` (UUIDv7, FK, Optional).
* **Optional Attributes:** `viewing_medium` (Enum: Cinema, TV, Streaming, Physical, Mobile), `device_id` (UUIDv7, FK, Optional), `notes_summary` (String, Optional).
* **Invariants:**
  * `edition_id = NULL` strictly signifies that the Edition was **unknown / unspecified**, NOT Primary Edition (`ADR-003`).
  * Watch Events are immutable. They are NEVER silently overwritten or deleted based on time-proximity heuristics (`ADR-003`, `ADR-004`).
* **Correction Model:** Corrected via `WatchEventCorrection` (Original Event -> Tombstone / Correction -> Corrected Event).
* **Deletion Behavior:** Purged only upon explicit user request or account deletion.

---

### Entity: WatchEventCorrection
* **Purpose:** Preserves historical audit integrity when a user corrects or invalidates a Watch Event.
* **Ownership Category:** `CAT-2` / `CAT-4`
* **Attributes:** `correction_id` (UUIDv7), `original_watch_event_id` (UUIDv7, FK), `corrected_watch_event_id` (UUIDv7, FK, Optional), `reason` (Enum: UserEdit, IngestionFix, DuplicateTombstone), `created_at` (Timestamp).

---

### Entity: UserProgress (Derived Read Model)
* **Purpose:** Cached read model representing a user's current watching progress in series/episodes or movies.
* **Ownership Category:** `CAT-3` (Derived Data)
* **Authoritative / Derived:** **DERIVED** (Not an independent authoritative source of truth)
* **Canonical Identity:** UUIDv7 (`progress_id`)
* **Invariants:**
  * Rebuildable at any time by executing progress calculation logic over authoritative `WatchEvent` history (`ADR-003`).

---

### Entity: UserRating
* **Purpose:** Represents a user's explicit rating of a Title.
* **Ownership Category:** `CAT-2` (User-Owned Personal Data)
* **Authoritative / Derived:** Authoritative
* **Canonical Identity:** UUIDv7 (`rating_id`)
* **Required Attributes:** `rating_id` (UUIDv7), `user_id` (UUIDv7, FK), `title_id` (UUIDv7, FK), `rating_value` (Decimal/Integer), `rated_at` (Timestamp), `updated_at` (Timestamp).
* **Invariants:**
  * Title-scoped by default (`ADR-003`).
  * Conflicting personal ratings during canonical title merges must NEVER be silently averaged or overwritten (`ADR-003`).

---

### Entity: UserReview & UserNote
* **Purpose:**
  * `UserReview`: Potentially publishable opinion/review with distinct privacy and public visibility semantics.
  * `UserNote`: Strictly private personal note.
* **Ownership Category:** `CAT-2` (User-Owned Personal Data)
* **Authoritative / Derived:** Authoritative
* **Canonical Identity:** UUIDv7 (`review_id`, `note_id`)
* **Invariants:** `UserReview` and `UserNote` are strictly **separate entities** and must NOT be merged into a single generic text field (`ADR-003`).

---

### Entity: UserTitleState
* **Purpose:** Tracks current watching status (e.g., PlanToWatch, Watching, Completed, OnHold, Dropped) and Favorite status.
* **Ownership Category:** `CAT-2` / `CAT-3`
* **Attributes:** `user_title_state_id` (UUIDv7), `user_id` (UUIDv7, FK), `title_id` (UUIDv7, FK), `derived_status` (Enum), `manual_status_override` (Enum, Optional), `is_favorite` (Boolean), `updated_at` (Timestamp).
* **Invariants:** Explicit separation between `derived_status` (calculated from Watch Events) and `manual_status_override` (`ADR-003`).

---

### Entities: UserCollection, UserCollectionItem, UserTag, UserPreference, UserDevice
* **Purpose:** Personal organization, custom lists, custom tags, application settings, and registered user offline sync devices.
* **Ownership Category:** `CAT-2` (User-Owned Personal Data)
* **Canonical Identity:** UUIDv7

---

## 9. External Identity Model

---

### Entity-Scoped Mapping Model

To preserve strict foreign key referential integrity without polymorphic foreign keys, external provider identifiers are stored in entity-scoped mapping tables (`ADR-001`):

#### 1. `TitleExternalId`
* `title_external_id` (UUIDv7, PK)
* `title_id` (UUIDv7, FK -> `Title.title_id`)
* `provider` (Enum: IMDb, TMDb, AniList, MyAnimeList, TVDB, JustWatch, Wikidata, ISAN)
* `external_id` (String)
* `is_primary_for_provider` (Boolean)
* `last_verified_at` (Timestamp)
* `provenance_source` (String)

#### 2. `EpisodeExternalId`
* `episode_external_id` (UUIDv7, PK)
* `episode_id` (UUIDv7, FK -> `Episode.episode_id`)
* `provider` (Enum)
* `external_id` (String)
* `is_primary_for_provider` (Boolean)
* `last_verified_at` (Timestamp)

#### 3. `PersonExternalId`
* `person_external_id` (UUIDv7, PK)
* `person_id` (UUIDv7, FK -> `Person.person_id`)
* `provider` (Enum)
* `external_id` (String)
* `is_primary_for_provider` (Boolean)
* `last_verified_at` (Timestamp)

#### 4. `FranchiseExternalId`
* `franchise_external_id` (UUIDv7, PK)
* `franchise_id` (UUIDv7, FK -> `Franchise.franchise_id`)
* `provider` (Enum)
* `external_id` (String)
* `is_primary_for_provider` (Boolean)
* `last_verified_at` (Timestamp)

* **Uniqueness Constraints:** `(provider, external_id)` MUST be unique within each mapping table.
* **Invariants:** External IDs are links/mappings ONLY. They are NEVER used as canonical primary keys.

---

## 10. Temporal Model

| Temporal Class | Concept Definition | Target Entities | Representation |
|---|---|---|---|
| **Point-in-Time Event** | Discrete historical occurrence | `WatchEvent`, `AwardEvent`, `Release` | `Timestamp` / `Date` |
| **Time Interval** | Bounded or unbounded valid duration | `PlatformOffer` (`valid_from` to `valid_until`) | Dual `Timestamp` fields |
| **Current State** | Mutable current status | `UserTitleState`, `UserPreference` | Single state field with `updated_at` |
| **Derived State** | Recomputable snapshot | `UserProgress` | Derived read model with `recalculated_at` |

---

## 11. Merge / Split / Identity Preservation Model

### Merge Operations
When canonical Title B is merged into Title A:
1. `Title B` status is set to `Merged` / `SoftDeleted`.
2. An `IdentityRedirect` record (`from_id: Title B`, `to_id: Title A`, `type: TitleMerge`) is created.
3. Personal `WatchEvent` records attached to Title B are safely reassociated with Title A.
4. **Conflicting Personal Data Protection:**
   * If User rated Title A = 7 and Title B = 9, both ratings are preserved in a `PersonalDataConflict` queue. NO automatic averaging occurs (`ADR-003`).
   * If User authored `Note A` and `Note B`, both notes remain distinct. NO string concatenation (`Note A + Note B`) occurs (`ADR-003`).

### Split Operations
When canonical Title A is split into Title A1 and Title A2:
1. New Titles `Title A1` and `Title A2` are created.
2. `SplitRecord` logs the historical provenance.
3. Personal data (Watch Events, Ratings, Notes) whose target is ambiguous MUST NOT be automatically duplicated onto both child titles. Ambiguous items are flagged in a `UserSplitResolution` queue for user confirmation (`ADR-003`).

---

## 12. Provenance & Audit Frameworks

> [!NOTE]
> **Status:** `DEFERRED — INGESTION / PROVENANCE REVIEW` & `DEFERRED — AUDIT / SECURITY REVIEW`

### Minimum Provenance Requirements
* External metadata ingestion records source provider, payload hash, retrieval timestamp, and confidence score.
* Field-level provenance required for critical canonical attributes (e.g., runtime, release date, synopsis).

### Audit & Privacy Boundary
* Operational/audit logs (`CanonicalAuditLog`, `SystemOperationLog`) record administrative and system actions.
* **Privacy Boundary:** When a user executes a personal data deletion request, all personal content (`WatchEvent`, `UserRating`, `UserNote`, `UserReview`) is purged. Audit logs retain ONLY anonymized transaction metadata (e.g., "User account X executed data purge at timestamp T"), and MUST NOT retain copies of deleted notes or reviews (`ADR-004`).

---

## 13. Summary of Deferred Decisions

1. Physical PostgreSQL DDL, data types, indexes, and partitioning keys.
2. Alternate cut scene-by-scene delta schema.
3. Physical schema for `RegionalEpisodeOrder`.
4. Offline sync outbox mutation payload schema.
5. Ingestion pipeline field-level provenance table DDL (`DEFERRED — INGESTION / PROVENANCE REVIEW`).
6. System audit DDL (`DEFERRED — AUDIT / SECURITY REVIEW`).
