# CineVault OS — Data Dictionary V1

**Document Type:** Authoritative Conceptual & Logical Field Contract  
**Status:** Architecture Baseline Specification  
**Date:** 2026-08-08  
**Scope:** Universal Field Specifications across Canonical, Taxonomy, People, External Identity, User, and Operational Domains  

> [!IMPORTANT]
> **GOVERNANCE RULE — CONCEPTUAL DATA TYPES ONLY**  
> Physical database types (e.g., `VARCHAR`, `TIMESTAMPTZ`, `JSONB`, `BIGINT`) are **prohibited** in this document. All fields use conceptual data types (`UUIDv7 identifier`, `immutable display identifier`, `short text`, `long text`, `timestamp`, `date`, `boolean`, `enum-like controlled vocabulary`, `foreign-key reference`, `ordered integer`, `decimal/rating value`, `interval`, `JSON-like structured payload where explicitly justified`). Physical data types belong exclusively to the subsequent Physical Database Phase.

---

## 1. Executive Summary & Data Ownership Classes

This Data Dictionary defines the field-level data contract for **CineVault OS**. Every entity and field explicitly defines its ownership category, privacy level, provenance requirement, audit policy, and lifecycle merge/split/deletion behaviors.

### Data Ownership Categories
* `CAT-1`: **Canonical Platform Data** (Catalog core, platform taxonomy)
* `CAT-2`: **User-Owned Personal Data** (Watch events, ratings, notes, reviews, library)
* `CAT-3`: **Derived Data** (Cached progress, rewatch stats, calculated status)
* `CAT-4`: **Operational / Audit Data** (System logs, tombstones, audit history)
* `CAT-5`: **External-Source Data** (Provider reference mappings)
* `CAT-6`: **AI-Generated Proposals** (Unvalidated suggestions requiring review)

---

## 2. Canonical Content Domain Entities

---

### Entity: Title

Represents the abstract creative work (e.g., *The Dark Knight*, *Breaking Bad*, *Spirited Away*).

#### Field: `title_id`
* **Purpose:** Permanent internal canonical identifier.
* **Business Meaning:** Unique system identity of the creative work.
* **Entity Ownership:** `Title`
* **Category:** `CAT-1` (Canonical Platform Data)
* **Required / Optional:** Required
* **Conceptual Data Type:** `UUIDv7 identifier`
* **Allowed Values / Domain:** Valid UUIDv7 string/binary format
* **Default Behavior:** Generated internally upon entity creation
* **Validation Rules:** Must be a valid UUIDv7; generated server-side
* **Uniqueness Expectations:** System-wide unique primary key
* **Relationship Target:** Primary key of `Title`
* **Source of Truth:** CineVault System Core
* **Provenance Requirement:** System generated
* **Derived / Calculated?:** No
* **Mutability:** Immutable
* **Audit Requirement:** Logged on entity creation
* **Privacy Classification:** Public
* **Merge Behavior:** Surviving title retains ID; retired title ID logged in `IdentityRedirect`
* **Split Behavior:** New UUIDv7 generated for split child titles
* **Deletion Behavior:** Soft delete / Tombstone only
* **Deferred Details:** Physical DB UUID storage type (Physical DB Phase)

#### Field: `display_id`
* **Purpose:** Human-readable secondary display identifier.
* **Business Meaning:** User-facing reference code (e.g., `MOV-000001`, `SER-000001`).
* **Entity Ownership:** `Title`
* **Category:** `CAT-1` (Canonical Platform Data)
* **Required / Optional:** Required
* **Conceptual Data Type:** `immutable display identifier`
* **Allowed Values / Domain:** Prefix + sequence number string
* **Default Behavior:** Auto-assigned once at creation based on initial classification
* **Validation Rules:** Format regex `^[A-Z]{3,4}-[0-9]{6}$`
* **Uniqueness Expectations:** System-wide unique
* **Relationship Target:** Secondary key
* **Source of Truth:** CineVault Core Identity Service
* **Provenance Requirement:** System generated
* **Derived / Calculated?:** No
* **Mutability:** Immutable (Prefix reflects historical classification at creation; `content_type` is current truth)
* **Audit Requirement:** Audit on assignment
* **Privacy Classification:** Public
* **Merge Behavior:** Surviving display ID retained; retired display ID mapped in `IdentityRedirect`
* **Split Behavior:** Retained on primary child; new display ID generated for secondary child
* **Deletion Behavior:** Retained in tombstone
* **Deferred Details:** Physical sequence generator mechanics (Physical DB Phase)

#### Field: `content_type`
* **Purpose:** Authoritative current content classification.
* **Business Meaning:** Current classification of the work (Movie, Series, Anime, OVA, Documentary, Reality, Special, Short).
* **Entity Ownership:** `Title`
* **Category:** `CAT-1` (Canonical Platform Data)
* **Required / Optional:** Required
* **Conceptual Data Type:** `enum-like controlled vocabulary`
* **Allowed Values / Domain:** `Movie`, `Series`, `Anime`, `OVA`, `ONA`, `Documentary`, `Reality`, `Special`, `Short`, `StandUp`
* **Default Behavior:** Set at creation
* **Validation Rules:** Must exist in `ContentType` taxonomy lookup
* **Uniqueness Expectations:** None
* **Relationship Target:** Refers to `ContentType.code`
* **Source of Truth:** CineVault Governance Pipeline
* **Provenance Requirement:** Required (records source of reclassification)
* **Derived / Calculated?:** No
* **Mutability:** Mutable through governed administrative process (Does NOT alter `title_id` or `display_id`)
* **Audit Requirement:** Full audit log required on reclassification
* **Privacy Classification:** Public
* **Merge Behavior:** Inherited from surviving title
* **Split Behavior:** Evaluated independently for child titles
* **Deletion Behavior:** Soft delete
* **Deferred Details:** None

#### Field: `canonical_title`
* **Purpose:** Primary international display title.
* **Business Meaning:** Official standard name of the creative work.
* **Entity Ownership:** `Title`
* **Category:** `CAT-1` (Canonical Platform Data)
* **Required / Optional:** Required
* **Conceptual Data Type:** `short text`
* **Allowed Values / Domain:** Non-empty text string (1–500 chars)
* **Default Behavior:** None
* **Validation Rules:** Cannot be blank; unicode normalized (NFC)
* **Uniqueness Expectations:** None
* **Relationship Target:** None
* **Source of Truth:** Canonical Ingestion Pipeline
* **Provenance Requirement:** Source, retrieval timestamp, confidence score required
* **Derived / Calculated?:** No
* **Mutability:** Mutable
* **Audit Requirement:** Logged on update
* **Privacy Classification:** Public
* **Merge Behavior:** Surviving title name retained; retired name saved as alternative title
* **Split Behavior:** Specified per child title
* **Deletion Behavior:** Soft delete
* **Deferred Details:** Full-text search index configuration (Physical DB Phase)

#### Field: `original_title`
* **Purpose:** Title in its original language of production.
* **Business Meaning:** Native script name of the creative work (e.g., *千と千尋の神隠し*).
* **Entity Ownership:** `Title`
* **Category:** `CAT-1` (Canonical Platform Data)
* **Required / Optional:** Required
* **Conceptual Data Type:** `short text`
* **Allowed Values / Domain:** Non-empty text string
* **Default Behavior:** Defaults to `canonical_title` if original language is English
* **Validation Rules:** Unicode normalized
* **Uniqueness Expectations:** None
* **Relationship Target:** None
* **Source of Truth:** Ingestion Pipeline
* **Provenance Requirement:** Required
* **Derived / Calculated?:** No
* **Mutability:** Mutable
* **Audit Requirement:** Logged on update
* **Privacy Classification:** Public
* **Merge Behavior:** Retained from surviving title
* **Split Behavior:** Re-assigned per split child title
* **Deletion Behavior:** Soft delete
* **Deferred Details:** CJK/Indic script normalization rules (Ingestion Phase)

---

### Entity: Edition

Represents a materially distinct version of the content (e.g., Theatrical Cut, Director's Cut, Extended Cut, Uncensored Version).

#### Field: `edition_id`
* **Purpose:** Permanent internal canonical identifier of the edition.
* **Business Meaning:** Unique identity of a specific content cut/version.
* **Entity Ownership:** `Edition`
* **Category:** `CAT-1` (Canonical Platform Data)
* **Required / Optional:** Required
* **Conceptual Data Type:** `UUIDv7 identifier`
* **Allowed Values / Domain:** Valid UUIDv7
* **Default Behavior:** Generated internally
* **Validation Rules:** Must be valid UUIDv7
* **Uniqueness Expectations:** System-wide unique primary key
* **Relationship Target:** Primary key of `Edition`
* **Source of Truth:** CineVault System Core
* **Provenance Requirement:** System generated
* **Derived / Calculated?:** No
* **Mutability:** Immutable
* **Audit Requirement:** Logged on creation
* **Privacy Classification:** Public
* **Merge Behavior:** Re-parented or merged if duplicate cut
* **Split Behavior:** Re-parented to target child title
* **Deletion Behavior:** Cannot delete Primary Edition unless Title is retired
* **Deferred Details:** None

#### Field: `title_id`
* **Purpose:** Foreign key link to parent Title.
* **Business Meaning:** Identifies the abstract creative work this edition belongs to.
* **Entity Ownership:** `Edition`
* **Category:** `CAT-1` (Canonical Platform Data)
* **Required / Optional:** Required
* **Conceptual Data Type:** `foreign-key reference`
* **Allowed Values / Domain:** Valid `Title.title_id`
* **Default Behavior:** None
* **Validation Rules:** Must reference existing `Title`
* **Uniqueness Expectations:** Foreign key constraint
* **Relationship Target:** `Title.title_id`
* **Source of Truth:** CineVault System Core
* **Provenance Requirement:** System generated
* **Derived / Calculated?:** No
* **Mutability:** Mutable only during title re-parenting/merge
* **Audit Requirement:** Logged on re-parenting
* **Privacy Classification:** Public
* **Merge Behavior:** Re-pointed to surviving `Title.title_id`
* **Split Behavior:** Re-pointed to corresponding split child `Title.title_id`
* **Deletion Behavior:** Cascade soft-delete when parent Title is retired
* **Deferred Details:** None

#### Field: `edition_name`
* **Purpose:** Name of the edition or cut.
* **Business Meaning:** Descriptive label for the version (e.g., "Primary Edition", "Director's Cut", "Unrated Extended Edition").
* **Entity Ownership:** `Edition`
* **Category:** `CAT-1` (Canonical Platform Data)
* **Required / Optional:** Required
* **Conceptual Data Type:** `short text`
* **Allowed Values / Domain:** Standard edition labels or custom cut names
* **Default Behavior:** "Primary Edition" for primary cuts
* **Validation Rules:** Non-empty string
* **Uniqueness Expectations:** Unique per Title (`title_id`, `edition_name`)
* **Relationship Target:** None
* **Source of Truth:** Ingestion / Governance
* **Provenance Requirement:** Required for non-primary editions
* **Derived / Calculated?:** No
* **Mutability:** Mutable
* **Audit Requirement:** Logged on update
* **Privacy Classification:** Public
* **Merge Behavior:** Preserved or merged if identical cut name
* **Split Behavior:** Re-parented
* **Deletion Behavior:** Soft delete
* **Deferred Details:** None

#### Field: `is_primary`
* **Purpose:** Flags the single primary edition for a Title.
* **Business Meaning:** Identifies whether this is the default conceptual edition of the work (`ADR-002`).
* **Entity Ownership:** `Edition`
* **Category:** `CAT-1` (Canonical Platform Data)
* **Required / Optional:** Required
* **Conceptual Data Type:** `boolean`
* **Allowed Values / Domain:** `true`, `false`
* **Default Behavior:** `true` for initial edition created with Title
* **Validation Rules:** Exactly one edition per Title MUST have `is_primary = true`
* **Uniqueness Expectations:** Partial unique index: `(title_id)` where `is_primary = true`
* **Relationship Target:** Constraint rule
* **Source of Truth:** CineVault Governance Pipeline
* **Provenance Requirement:** Required on primary reassignment
* **Derived / Calculated?:** No
* **Mutability:** Mutable (Primary flag can be reassigned to another edition of the same Title)
* **Audit Requirement:** Full audit on primary edition flag change
* **Privacy Classification:** Public
* **Merge Behavior:** Primary flag maintained on surviving edition
* **Split Behavior:** Primary flag established per split Title
* **Deletion Behavior:** Cannot delete edition where `is_primary = true` while title active
* **Deferred Details:** Partial unique index DDL (Physical DB Phase)

#### Field: `runtime_minutes`
* **Purpose:** Exact running time of this specific edition in minutes.
* **Business Meaning:** Total duration of this version of the content.
* **Entity Ownership:** `Edition`
* **Category:** `CAT-1` (Canonical Platform Data)
* **Required / Optional:** Optional
* **Conceptual Data Type:** `ordered integer`
* **Allowed Values / Domain:** Positive integer > 0
* **Default Behavior:** Null
* **Validation Rules:** Must be > 0 if specified
* **Uniqueness Expectations:** None
* **Relationship Target:** None
* **Source of Truth:** Metadata Ingestion
* **Provenance Requirement:** Provenance required
* **Derived / Calculated?:** No
* **Mutability:** Mutable
* **Audit Requirement:** Logged on update
* **Privacy Classification:** Public
* **Merge Behavior:** Retained from surviving edition
* **Split Behavior:** Preserved per edition
* **Deletion Behavior:** Nullified on soft delete
* **Deferred Details:** None

---

### Entity: Release

Represents a real-world distribution event for a specific Edition (e.g., Festival Premiere, Theatrical Release, Streaming Launch).

#### Field: `release_id`
* **Purpose:** Permanent internal canonical identifier of the release event.
* **Business Meaning:** Unique identity of a distribution event.
* **Entity Ownership:** `Release`
* **Category:** `CAT-1` (Canonical Platform Data)
* **Required / Optional:** Required
* **Conceptual Data Type:** `UUIDv7 identifier`
* **Allowed Values / Domain:** Valid UUIDv7
* **Default Behavior:** Generated internally
* **Validation Rules:** Must be valid UUIDv7
* **Uniqueness Expectations:** System-wide unique primary key
* **Relationship Target:** Primary key of `Release`
* **Source of Truth:** CineVault System Core
* **Provenance Requirement:** System generated
* **Derived / Calculated?:** No
* **Mutability:** Immutable
* **Audit Requirement:** Logged on creation
* **Privacy Classification:** Public
* **Merge Behavior:** Re-parented to surviving Edition
* **Split Behavior:** Re-parented to corresponding Edition
* **Deletion Behavior:** Soft delete
* **Deferred Details:** None

#### Field: `edition_id`
* **Purpose:** Foreign key link to parent Edition.
* **Business Meaning:** Identifies the content version being distributed.
* **Entity Ownership:** `Release`
* **Category:** `CAT-1` (Canonical Platform Data)
* **Required / Optional:** Required
* **Conceptual Data Type:** `foreign-key reference`
* **Allowed Values / Domain:** Valid `Edition.edition_id`
* **Default Behavior:** None
* **Validation Rules:** Must reference existing `Edition`
* **Uniqueness Expectations:** Foreign key constraint
* **Relationship Target:** `Edition.edition_id`
* **Source of Truth:** CineVault System Core
* **Provenance Requirement:** Required
* **Derived / Calculated?:** No
* **Mutability:** Mutable during edition merge/re-parenting
* **Audit Requirement:** Logged on re-parenting
* **Privacy Classification:** Public
* **Merge Behavior:** Re-pointed to surviving Edition
* **Split Behavior:** Re-pointed to split Edition
* **Deletion Behavior:** Cascade soft-delete when parent Edition is retired
* **Deferred Details:** None

#### Field: `release_type`
* **Purpose:** Classification of the distribution event.
* **Business Meaning:** Channel or window of release (Festival, Theatrical, TV, Streaming, Physical, Digital, ReRelease).
* **Entity Ownership:** `Release`
* **Category:** `CAT-1` (Canonical Platform Data)
* **Required / Optional:** Required
* **Conceptual Data Type:** `enum-like controlled vocabulary`
* **Allowed Values / Domain:** `Festival`, `Theatrical`, `Television`, `Streaming`, `Physical`, `DigitalPurchase`, `DigitalRental`, `ReRelease`
* **Default Behavior:** None
* **Validation Rules:** Must exist in release type vocabulary
* **Uniqueness Expectations:** None
* **Relationship Target:** Taxonomy reference
* **Source of Truth:** Ingestion Pipeline
* **Provenance Requirement:** Required
* **Derived / Calculated?:** No
* **Mutability:** Mutable
* **Audit Requirement:** Logged on update
* **Privacy Classification:** Public
* **Merge Behavior:** Preserved on re-parented release
* **Split Behavior:** Preserved
* **Deletion Behavior:** Soft delete
* **Deferred Details:** None

#### Field: `release_date`
* **Purpose:** Date of the distribution event.
* **Business Meaning:** Real-world premiere or launch date for this release event.
* **Entity Ownership:** `Release`
* **Category:** `CAT-1` (Canonical Platform Data)
* **Required / Optional:** Optional
* **Conceptual Data Type:** `date`
* **Allowed Values / Domain:** Valid calendar date (YYYY-MM-DD)
* **Default Behavior:** Null
* **Validation Rules:** Must be a valid historical or future date
* **Uniqueness Expectations:** None
* **Relationship Target:** Point-in-time temporal model
* **Source of Truth:** Ingestion Pipeline (TMDb, IMDb, TVDB)
* **Provenance Requirement:** Source, retrieval timestamp, and verification status required
* **Derived / Calculated?:** No
* **Mutability:** Mutable
* **Audit Requirement:** Logged on update
* **Privacy Classification:** Public
* **Merge Behavior:** Retained
* **Split Behavior:** Retained
* **Deletion Behavior:** Soft delete
* **Deferred Details:** Partial date support (e.g., Year-only or Month-Year) deferred to physical schema formatting

---

### Entities: Season & Episode

#### Field: `season_id` (Season Entity)
* **Conceptual Data Type:** `UUIDv7 identifier`
* **Ownership / Category:** `CAT-1` (Canonical)
* **Validation / Rules:** Primary key of `Season`. Linked to `Title.title_id`.
* **Invariants:** Belongs to episodic Title.

#### Field: `season_number` (Season Entity)
* **Conceptual Data Type:** `ordered integer`
* **Ownership / Category:** `CAT-1` (Canonical)
* **Validation / Rules:** Canonical default season index (e.g., Season 1). Unique per `Title`.
* **Invariants:** Display ordering can be overridden by regional ordering.

#### Field: `episode_id` (Episode Entity)
* **Conceptual Data Type:** `UUIDv7 identifier`
* **Ownership / Category:** `CAT-1` (Canonical)
* **Validation / Rules:** Primary key of `Episode`. Permanent canonical identity.
* **Invariants:** Identity strictly independent of episode sequence numbering (`ADR-002`).

#### Field: `season_id` (Episode Entity FK)
* **Conceptual Data Type:** `foreign-key reference`
* **Ownership / Category:** `CAT-1` (Canonical)
* **Validation / Rules:** FK to `Season.season_id`.

#### Field: `title_id` (Episode Entity FK)
* **Conceptual Data Type:** `foreign-key reference`
* **Ownership / Category:** `CAT-1` (Canonical)
* **Validation / Rules:** Direct FK to `Title.title_id` (Denormalized for query efficiency).

#### Field: `episode_number` (Episode Entity)
* **Conceptual Data Type:** `ordered integer`
* **Ownership / Category:** `CAT-1` (Canonical)
* **Validation / Rules:** Canonical default episode number within season.

---

### Entity: Franchise, Universe & FranchiseEntry

#### Field: `universe_id` (Universe Entity)
* **Conceptual Data Type:** `UUIDv7 identifier` | `CAT-1` Canonical | Primary Key.

#### Field: `franchise_id` (Franchise Entity)
* **Conceptual Data Type:** `UUIDv7 identifier` | `CAT-1` Canonical | Primary Key. Optional FK to `Universe.universe_id`.

#### Field: `franchise_entry_id` (FranchiseEntry Entity)
* **Conceptual Data Type:** `UUIDv7 identifier` | `CAT-1` Canonical | Primary Key connecting `Franchise` and `Title`.

#### Field: `order_type` (FranchiseEntry Entity)
* **Purpose:** Categorizes viewing order type.
* **Conceptual Data Type:** `enum-like controlled vocabulary`
* **Allowed Values:** `ReleaseOrder`, `ChronologicalOrder`, `StoryOrder`, `RecommendedOrder`, `CompletionistOrder`
* **Invariants:** Hard-coded order columns on `Title` or `Franchise` are prohibited (`ADR-002`).

#### Field: `position` (FranchiseEntry Entity)
* **Purpose:** Numeric sequence position within specified `order_type`.
* **Conceptual Data Type:** `decimal/rating value` (Supports decimal insertions like 1.5 for mid-series specials).

---

### Entity: Platform & PlatformOffer

#### Field: `platform_offer_id` (PlatformOffer Entity)
* **Conceptual Data Type:** `UUIDv7 identifier` | `CAT-1`/`CAT-5` | Primary Key.

#### Field: `valid_from` (PlatformOffer Entity)
* **Purpose:** Start timestamp of streaming subscription availability window (`DEC-PRP-04`).
* **Conceptual Data Type:** `timestamp` | Optional | Temporal Interval Start.

#### Field: `valid_until` (PlatformOffer Entity)
* **Purpose:** End timestamp of streaming subscription availability window (`DEC-PRP-04`).
* **Conceptual Data Type:** `timestamp` | Optional (NULL = Currently Active / Unbounded) | Temporal Interval End.

#### Field: `offer_type` (PlatformOffer Entity)
* **Conceptual Data Type:** `enum-like controlled vocabulary` | Values: `Subscription`, `Rental`, `Purchase`, `FreeWithAds`.

---

## 3. External Identity Dictionary

> [!IMPORTANT]
> **CANONICAL IDENTITY STATEMENT**  
> External provider IDs are mappings to CineVault entities. External provider IDs are **NEVER** canonical CineVault identity (`ADR-001`).

### Entity: TitleExternalId
* `title_external_id`: `UUIDv7 identifier` | Primary Key.
* `title_id`: `foreign-key reference` | FK -> `Title.title_id` | Required.
* `provider`: `enum-like controlled vocabulary` | `IMDb`, `TMDb`, `AniList`, `MyAnimeList`, `TVDB`, `JustWatch`, `Wikidata`, `ISAN` | Required.
* `external_id`: `short text` | String ID from provider | Required.
* `is_primary_for_provider`: `boolean` | Flags main external ID for provider | Default `true`.
* `last_verified_at`: `timestamp` | Ingestion timestamp | Operational tracking.
* **Uniqueness Expectations:** Composite unique `(provider, external_id)`.

### Entity: EpisodeExternalId
* `episode_external_id`: `UUIDv7 identifier` | Primary Key.
* `episode_id`: `foreign-key reference` | FK -> `Episode.episode_id`.
* `provider`: `enum-like controlled vocabulary` | `IMDb`, `TMDb`, `TVDB`, `AniList`, `MyAnimeList`.
* `external_id`: `short text` | Provider string ID.
* **Uniqueness Expectations:** Composite unique `(provider, external_id)`.

### Entity: PersonExternalId & FranchiseExternalId
* Analogous entity-scoped structure mapping `Person` and `Franchise` to external IDs without polymorphic foreign keys (`ADR-001`).

---

## 4. Geographic & Language Taxonomy Dictionary

---

### Geographic Model (Country Roles)

Country relationships MUST NOT be collapsed into an overloaded scalar string field on `Title`. Distinct roles are represented conceptually via relationship entities:

| Relationship Entity | Country Role Semantics | Attached Entity Target | Conceptual Data Type |
|---|---|---|---|
| `TitleCountry` | `ProductionCountry` | `Title.title_id` | `foreign-key reference` to `Country` |
| `TitleCountry` | `FilmingCountry` | `Title.title_id` | `foreign-key reference` to `Country` |
| `TitleCountry` | `CountryOfOrigin` | `Title.title_id` | `foreign-key reference` to `Country` |
| `ReleaseTerritory` | `ReleaseTerritory` | `Release.release_id` | `foreign-key reference` to `Country` |
| `PlatformOfferRegion` | `AvailabilityRegion` | `PlatformOffer.platform_offer_id` | `foreign-key reference` to `Country` |

---

### Language Model (Language Roles)

Language relationships MUST NOT be collapsed into an overloaded scalar string field on `Title`. Explicit conceptual attachments:

| Relationship Entity | Language Role Semantics | Attached Entity Target | Conceptual Attachment Justification |
|---|---|---|---|
| `TitleLanguage` | `OriginalLanguage` | `Title.title_id` | Creative work origin attribute (`Title`). |
| `EditionLanguage` | `AudioLanguage` | `Edition.edition_id` | Specific content cut audio variation (`Edition`). |
| `EditionLanguage` | `SubtitleLanguage` | `Edition.edition_id` | Text overlay track availability (`Edition`). |
| `EditionLanguage` | `DubbedLanguage` | `Edition.edition_id` | Localized voice dubbing track (`Edition`). |

* **Deferred Status:** Physical foreign key constraint attachment optimization: `DEFERRED`.

---

## 5. People & Credits Domain Entities

### Entity: Person
* `person_id`: `UUIDv7 identifier` | Primary Key | `CAT-1` Canonical | Immutable.
* `primary_name`: `short text` | Standard display name | Required.
* `birth_date`: `date` | Optional | Provenance required.

### Entity: Character
* `character_id`: `UUIDv7 identifier` | Primary Key | `CAT-1` Canonical.
* `character_name`: `short text` | Fictional/non-fictional character name.

### Entity: Credit
* `credit_id`: `UUIDv7 identifier` | Primary Key | `CAT-1` Canonical.
* `person_id`: `foreign-key reference` -> `Person.person_id` | Required.
* `credit_category`: `enum-like controlled vocabulary` | `Cast`, `Director`, `Writer`, `Producer`, `Composer`, `Cinematographer`, `Editor`.
* `billing_order`: `ordered integer` | Optional cast rank order.
* `title_id` / `edition_id` / `episode_id`: `foreign-key reference` | Target creative entity. Must reference at least one.

---

## 6. Awards & Festivals Domain Dictionary (Approved DEC-PRP-01)

### Entities: Award, AwardCategory, AwardEvent, AwardResult
* `award_id`: `UUIDv7 identifier` | Awarding organization (e.g., Academy Awards).
* `award_category_id`: `UUIDv7 identifier` | Award category (e.g., Best Picture).
* `award_event_id`: `UUIDv7 identifier` | Annual event instance (e.g., 96th Academy Awards, 2024).
* `award_result_id`: `UUIDv7 identifier` | Result linking `AwardEvent` + `AwardCategory` + `Title`/`Person` + `status` (`Nominee`, `Winner`, `Honoree`).

### Entities: Festival, FestivalEdition, FestivalParticipation
* `festival_id`: `UUIDv7 identifier` | Festival organization (e.g., Cannes Film Festival).
* `festival_edition_id`: `UUIDv7 identifier` | Specific festival year instance.
* `festival_participation_id`: `UUIDv7 identifier` | Result linking `FestivalEdition` + `Title` + `section` (`InCompetition`, `OutOfCompetition`, `Premieres`).

---

## 7. User Domain & Personal Data Dictionary

---

### Entity: User & UserProfile
* `user_id`: `UUIDv7 identifier` | Primary Key | `CAT-2` User Personal Data | Private | Deletable upon user account purge.
* `username`: `short text` | Unique username.
* `email`: `short text` | Private user contact email.

---

### Entity: LibraryEntry
* `library_entry_id`: `UUIDv7 identifier` | Primary Key | `CAT-2` User Personal Data.
* `user_id`: `foreign-key reference` -> `User.user_id` | Private.
* `title_id`: `foreign-key reference` -> `Title.title_id` | Title-scoped library membership (`ADR-003`).
* `preferred_edition_id`: `foreign-key reference` -> `Edition.edition_id` | Optional user display preference. Does NOT alter canonical Title identity (`ADR-003`).
* `added_at`: `timestamp` | Point-in-time addition timestamp.

---

### Entity: WatchEvent (Field Contract)

Append-only historical viewing record representing user activity (`ADR-003`).

#### Field: `watch_event_id`
* **Purpose:** Event identity.
* **Conceptual Data Type:** `UUIDv7 identifier`
* **Category:** `CAT-2` (User-Owned Personal Data)
* **Required / Optional:** Required
* **Invariants:** Immutable append-only log record.

#### Field: `user_id`
* **Conceptual Data Type:** `foreign-key reference` -> `User.user_id` | Required | `CAT-2`.

#### Field: `title_id`
* **Conceptual Data Type:** `foreign-key reference` -> `Title.title_id` | Required | `CAT-2`.

#### Field: `edition_id`
* **Purpose:** References specific content cut watched.
* **Conceptual Data Type:** `foreign-key reference` -> `Edition.edition_id` | **Optional**
* **INVARIANT:** `edition_id = NULL` strictly means **unknown / unspecified Edition**, NOT Primary Edition (`ADR-003`).

#### Field: `season_id` & `episode_id`
* **Conceptual Data Type:** `foreign-key reference` | Optional episodic viewing references.

#### Field: `watched_at`
* **Purpose:** Timestamp of viewing activity.
* **Conceptual Data Type:** `timestamp` | Required | Point-in-Time Event.

#### Field: `client_mutation_id`
* **Purpose:** Idempotency identifier generated by Flutter offline client outbox (`ADR-004`).
* **Conceptual Data Type:** `UUIDv7 identifier` | Optional | Prevents duplicate event insertion on offline retry.

---

### Entity: WatchEventCorrection
* `correction_id`: `UUIDv7 identifier` | Primary Key | `CAT-2`/`CAT-4`.
* `original_watch_event_id`: `foreign-key reference` -> `WatchEvent.watch_event_id`.
* `corrected_watch_event_id`: `foreign-key reference` -> `WatchEvent.watch_event_id` (Optional).
* `reason`: `enum-like controlled vocabulary` | `UserEdit`, `DuplicateTombstone`.

---

### Entity: UserRating
* `rating_id`: `UUIDv7 identifier` | Primary Key | `CAT-2` User Personal Data.
* `user_id`: `foreign-key reference` -> `User.user_id`.
* `title_id`: `foreign-key reference` -> `Title.title_id` | Title-scoped rating (`ADR-003`).
* `rating_value`: `decimal/rating value` | Personal score (e.g., 8.5 / 10.0).
* **Merge Rule:** `PRESERVE_CONFLICT`. Conflicting ratings during title merges MUST NOT be silently averaged (`ADR-003`).

---

### Entity: UserReview & UserNote
* `review_id`: `UUIDv7 identifier` | `CAT-2` | Publishable review | Privacy: `Public`/`Friends`/`Private` (`ADR-003`).
* `note_id`: `UUIDv7 identifier` | `CAT-2` | Strictly private user note | Privacy: `Private` (`ADR-003`).
* **Merge Rule:** `PRESERVE_CONFLICT`. Notes and reviews MUST NOT be automatically concatenated (`Note A + Note B` prohibited) (`ADR-003`).

---

### Entity: UserTitleState (Approved DEC-PRP-02)
* `user_title_state_id`: `UUIDv7 identifier` | Primary Key | `CAT-2`/`CAT-3`.
* `user_id`: `foreign-key reference` -> `User.user_id`.
* `title_id`: `foreign-key reference` -> `Title.title_id`.
* `derived_status`: `enum-like controlled vocabulary` | Status calculated from Watch Events (`PlanToWatch`, `Watching`, `Completed`, `Dropped`).
* `manual_status_override`: `enum-like controlled vocabulary` | Optional manual user status choice (`DEC-PRP-02`).
* `is_favorite`: `boolean` | Favorite current state.
* **Transition Logic:** `DEFERRED`.

---

### Entities: PersonalDataConflict & UserSplitResolution (Approved DEC-PRP-03)
* `conflict_id` / `resolution_id`: `UUIDv7 identifier` | Primary Key | `CAT-2`/`CAT-4`.
* `user_id`: `foreign-key reference` -> `User.user_id`.
* `conflict_type`: `enum-like controlled vocabulary` | `ConflictingRatings`, `ConflictingNotes`, `AmbiguousSplitWatchEvent`.
* `payload`: `JSON-like structured payload where explicitly justified` | Contains conflicting entity references awaiting explicit user resolution (`DEC-PRP-03`).
* **Queue Algorithm:** `DEFERRED`.

---

## 8. Derived Data Dictionary

---

### Entity: UserProgress (Derived Read Model)
* `progress_id`: `UUIDv7 identifier` | `CAT-3` Derived Data.
* `user_id`: `foreign-key reference` -> `User.user_id`.
* `title_id`: `foreign-key reference` -> `Title.title_id`.
* `percentage_complete`: `decimal/rating value` | Recomputable progress index.
* `recalculated_at`: `timestamp` | Derived timestamp.
* **AUTHORITATIVE STATEMENT:** Derived from authoritative `WatchEvent` history. UserProgress is NOT an independent source of truth (`ADR-003`).

---

## 9. Operational & Identity Tombstones

---

### Entity: IdentityRedirect
* `redirect_id`: `UUIDv7 identifier` | Primary Key | `CAT-4` Operational Data.
* `retired_uuid`: `UUIDv7 identifier` | Retired entity ID (Title or Person).
* `surviving_uuid`: `UUIDv7 identifier` | Target surviving entity ID.
* `entity_type`: `enum-like controlled vocabulary` | `Title`, `Person`.
* `redirect_reason`: `enum-like controlled vocabulary` | `Merge`, `Split`, `Reclassification`.

---

## 10. Temporal Classification Summary

| Field | Temporal Class | Conceptual Representation | Business Rule |
|---|---|---|---|
| `Release.release_date` | Point-in-time | `date` | Real-world premiere date |
| `WatchEvent.watched_at` | Point-in-time | `timestamp` | Activity occurrence time |
| `PlatformOffer.valid_from` | Interval Start | `timestamp` | Subscription window start (`DEC-PRP-04`) |
| `PlatformOffer.valid_until` | Interval End | `timestamp` | Subscription window end (`NULL` = active) (`DEC-PRP-04`) |
| `UserTitleState.is_favorite` | Current State | `boolean` | Mutable current user flag |
| `UserProgress.recalculated_at` | Derived Timestamp | `timestamp` | Read model calculation time |

---

## 11. Provenance & Audit Requirements

### Minimum Provenance Requirements
* External catalog metadata fields (`canonical_title`, `synopsis`, `runtime_minutes`, `release_date`) require source provider string, retrieval timestamp, and confidence score.
* Physical provenance table schema: `DEFERRED — INGESTION / PROVENANCE REVIEW`.

### Audit Boundary Rules
* Canonical metadata modifications, reclassifications, merges, and splits require full audit logging (`CanonicalAuditLog`).
* **Privacy Purge Boundary:** User account deletion purges personal content (`WatchEvent`, `UserRating`, `UserNote`, `UserReview`). Audit logs retain ONLY anonymized transaction metadata, and MUST NOT retain copies of deleted personal notes or reviews (`ADR-004`).
* Physical audit table schema DDL: `DEFERRED — AUDIT / SECURITY REVIEW`.

---

## 12. Decision Status Summary

* **APPROVED:** All items derived from `ADR-001` through `ADR-004` and `DEC-PRP-01` through `DEC-PRP-04`.
* **DERIVED:** Persisted primary edition row, denormalized Title FK on Episode, WatchEventCorrection entity, role-based country/language tables.
* **PROPOSED (NEW OWNER APPROVAL REQUIRED):** *None.* No new unapproved proposed decisions introduced in this document.
* **DEFERRED:** Physical PostgreSQL DDL, physical indexes, scene-by-scene delta schema, regional episode ordering DDL, offline outbox JSON schema, physical provenance DDL, physical audit DDL, backup retention purge timelines.
