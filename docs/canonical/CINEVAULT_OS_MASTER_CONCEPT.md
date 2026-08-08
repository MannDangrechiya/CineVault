# CineVault OS --- Master Product Concept & Functional Specification

**Document type:** Product / Concept Master Document\
**Status:** Research baseline --- no implementation phases defined yet\
**Purpose:** Shared context for ChatGPT, Claude, Gemini, DeepSeek, Kimi
and future agents\
**Scope:** Global entertainment knowledge, discovery, personal tracking,
analytics, recommendations, archival awareness and future mobile/web
applications.

------------------------------------------------------------------------

## 1. Executive Vision

CineVault OS is a scalable personal entertainment knowledge platform ---
not merely a movie spreadsheet.

The system should combine the strongest concepts from film databases,
watch trackers, recommendation systems, anime databases, streaming
aggregators, personal media libraries and knowledge graphs.

The long-term goal is to maintain one structured source of truth for:

-   Films
-   Television series
-   Web series
-   Anime
-   Anime films
-   OVAs / ONAs
-   Documentaries
-   Reality / competition programs
-   Shorts
-   Specials
-   Stand-up and other audiovisual formats where useful

The system must simultaneously support two kinds of information:

1.  **Canonical entertainment metadata** --- what a title is.
2.  **Personal interaction data** --- what the user thinks, watches,
    owns, rates and wants to watch.

These must remain separate.

------------------------------------------------------------------------

## 2. Core Product Principle

> **Metadata can change; personal history must never be destroyed by
> metadata updates.**

For example, if a streaming provider changes, a runtime is corrected, a
title receives an award, or a title gets a new localized name, the
user's:

-   watched status
-   watch dates
-   personal rating
-   notes
-   favorites
-   progress
-   rewatch history

must remain intact.

------------------------------------------------------------------------

## 3. What Makes This Different

CineVault OS should eventually provide:

-   Global entertainment catalog
-   Personal watch tracker
-   Watchlist
-   Ratings and reviews
-   Episode progress
-   Franchise tracking
-   Collection management
-   Advanced discovery
-   Streaming availability
-   Awards and cultural significance
-   Personal statistics
-   Taste analysis
-   Recommendation engine
-   AI conversational assistant
-   Release calendar
-   Data quality monitoring
-   Metadata update history
-   Export/import
-   Offline-capable personal library
-   Future Flutter mobile/web/desktop clients

------------------------------------------------------------------------

## 4. Content Universe

### Cinema

-   Hollywood
-   British cinema
-   Bollywood / Hindi
-   Tamil
-   Telugu
-   Malayalam
-   Kannada
-   Marathi
-   Bengali
-   Punjabi
-   Assamese
-   Gujarati
-   Bhojpuri
-   Korean
-   Japanese
-   Chinese
-   Hong Kong
-   Taiwanese
-   Thai
-   Indonesian
-   Filipino
-   Vietnamese
-   French
-   German
-   Italian
-   Spanish
-   Portuguese
-   Nordic
-   Eastern European
-   Turkish
-   Iranian
-   Arab cinema
-   African cinema
-   Nollywood
-   Latin American cinema
-   Other emerging industries

### Television / Web

-   US
-   UK
-   Canada
-   Australia
-   India
-   Korea
-   Japan
-   China
-   Thailand
-   Europe
-   Latin America
-   Middle East
-   Africa
-   Global streaming originals

### Anime

-   Shonen
-   Shojo
-   Seinen
-   Josei
-   Kodomo
-   Isekai
-   Mecha
-   Sports
-   Psychological
-   Horror
-   Romance
-   Slice of life
-   Historical
-   Music
-   Mystery
-   Supernatural
-   Sci-fi
-   Cyberpunk
-   Experimental

Formats:

-   TV anime
-   Anime film
-   OVA
-   ONA
-   Special
-   Short
-   Compilation film

### Non-fiction

-   Documentary film
-   Documentary series
-   Nature
-   Science
-   History
-   True crime
-   Music
-   Sports
-   Politics / current affairs
-   Film history
-   Biography
-   Investigative

### Unscripted

Only culturally significant or genre-defining:

-   Reality
-   Competition
-   Talent
-   Survival
-   Dating
-   Food
-   Travel
-   Lifestyle
-   Documentary-reality hybrids

------------------------------------------------------------------------

## 5. Title Identity Model

Every title receives a permanent internal ID.

Suggested IDs:

-   `MOV-000001`
-   `SER-000001`
-   `ANI-000001`
-   `ANIF-000001`
-   `DOC-000001`
-   `REA-000001`
-   `SHO-000001`
-   `SPC-000001`

External identifiers should also be stored where legitimately available:

-   IMDb ID
-   TMDb ID
-   AniList ID
-   MyAnimeList ID
-   TVDB ID
-   JustWatch ID
-   Wikidata Q-ID
-   ISAN / other identifiers where appropriate

IMDb's current documentation explicitly uses unique title/name
identifiers, while its licensed bulk/API products are versioned and
updated. External IDs should therefore be treated as links, not as
replacements for the permanent internal ID.

------------------------------------------------------------------------

## 6. Entity / Knowledge-Graph Concept

The system should model relationships rather than storing everything in
one flat row.

Important entities:

-   Title
-   Title Edition
-   Season
-   Episode
-   Person
-   Character
-   Director
-   Writer
-   Producer
-   Composer
-   Studio
-   Production Company
-   Distributor
-   Network
-   Streaming Provider
-   Country
-   Language
-   Genre
-   Subgenre
-   Theme
-   Keyword
-   Award
-   Festival
-   Franchise
-   Collection
-   Universe
-   Platform Offer
-   Certification
-   Release Event
-   User
-   Watch Event
-   Rating
-   Review
-   Note
-   Recommendation
-   External Identifier

Examples of relationships:

`Person -> acted_in -> Title`

`Person -> directed -> Title`

`Title -> belongs_to -> Franchise`

`Title -> part_of -> Collection`

`Title -> has_genre -> Genre`

`Title -> produced_in -> Country`

`Title -> available_on -> Platform Offer`

`User -> watched -> Title`

`User -> rated -> Title`

`User -> wants_to_watch -> Title`

`Title -> similar_to -> Title`

------------------------------------------------------------------------

## 7. Title Types Must Be Extensible

Do not hard-code only "movie" and "series."

The architecture must support future types such as:

-   Film
-   Episode
-   Series
-   Season
-   Anime
-   OVA
-   ONA
-   Special
-   Short
-   Documentary
-   Reality
-   Stand-up
-   Concert film
-   Music documentary
-   Anthology
-   Interactive special

New types should be addable through controlled configuration/schema
changes rather than redesigning the entire database.

------------------------------------------------------------------------

## 8. Release Timeline

Store multiple dates when applicable:

-   Production year
-   Festival premiere
-   World premiere
-   Theatrical release
-   Regional theatrical release
-   Television premiere
-   Streaming premiere
-   Digital purchase release
-   Physical release
-   Season release
-   Episode release
-   Re-release

A title can therefore be filtered by actual release event instead of
relying on one ambiguous "year."

Timeline labels:

-   Golden Age
-   Classic
-   Modern
-   Contemporary
-   Recent

Configurable date ranges should live in settings, not be permanently
hard-coded.

------------------------------------------------------------------------

## 9. Metadata Dimensions

### Core

-   Title
-   Original title
-   Alternative titles
-   Release year
-   Runtime
-   Type
-   Country
-   Primary language
-   Original language
-   Status

### Creative

-   Director
-   Writer
-   Creator
-   Producer
-   Main cast
-   Key crew
-   Composer
-   Cinematographer
-   Editor
-   Studio
-   Production company

### Classification

-   Genre
-   Subgenre
-   Themes
-   Keywords
-   Mood
-   Tone
-   Content warnings
-   Certification
-   Audience category

### Critical

-   IMDb
-   Rotten Tomatoes
-   Metacritic
-   Letterboxd
-   User rating
-   Vote counts
-   Awards
-   Festival selections
-   Cultural significance

### Commercial

-   Budget
-   Box office
-   Opening
-   Gross
-   Revenue data source
-   Streaming popularity where legitimately licensed

### Availability

-   Platform
-   Country
-   Offer type
-   Subscription / rent / buy / free
-   Audio languages
-   Subtitle languages
-   Last verified date
-   Source
-   Confidence

------------------------------------------------------------------------

## 10. Streaming Availability Is Time-Dependent

Never store:

> Netflix = Yes

as permanent truth.

Instead store an availability event:

-   Title
-   Provider
-   Country
-   Offer type
-   URL/deep link where permitted
-   Valid-from
-   Valid-to if known
-   Last checked
-   Source
-   Confidence
-   Data version

JustWatch's partner documentation describes country-specific offers and
daily updates across many providers, making this kind of temporal model
important.

The database should distinguish:

-   Available
-   Coming soon
-   Expired
-   Unknown
-   Region locked
-   Rent
-   Buy
-   Subscription
-   Free with ads
-   Free
-   Broadcast
-   Physical only

------------------------------------------------------------------------

## 11. User Tracking

Each user should have an independent library relationship.

Fields:

-   Status
-   Watched
-   First watched date
-   Last watched date
-   Rewatch count
-   Personal rating
-   Favorite
-   Hidden
-   Progress
-   Current season
-   Current episode
-   Notes
-   Personal tags
-   Mood at watch time
-   Watch location/device if desired
-   Spoiler-safe review
-   Private review
-   Date added
-   Date completed

### Status vocabulary

-   Plan to Watch
-   Watching
-   Completed
-   Paused
-   Dropped
-   Rewatching
-   Waiting for New Season
-   On Hold
-   Hidden

------------------------------------------------------------------------

## 12. Checkbox / Marking System

The user explicitly wants visible tracking.

The UI should support:

-   Watched checkbox
-   Favorite checkbox
-   Rewatch checkbox
-   Owned checkbox
-   Hidden checkbox
-   Plan-to-watch checkbox

For series:

`18 / 62 episodes`

and an automatic completion percentage.

For movies:

`Completed`

The database should store the state, while the UI may render it as
checkboxes, icons, buttons or toggles.

------------------------------------------------------------------------

## 13. Watch History

Do not only store "watched = true."

Store individual watch events.

Example:

-   User
-   Title
-   Season
-   Episode
-   Started at
-   Completed at
-   Watch date
-   Device
-   Platform
-   Rewatch number
-   Completion state

This enables:

-   daily statistics
-   monthly statistics
-   yearly statistics
-   streaks
-   rewatch analysis
-   total hours
-   platform usage
-   binge sessions

------------------------------------------------------------------------

## 14. Personal Ratings

Keep external ratings separate from personal ratings.

External:

-   IMDb
-   RT
-   Metacritic
-   Letterboxd
-   AniList
-   MyAnimeList

Personal:

-   0--10
-   0--100
-   1--5 stars
-   Favorite
-   Masterpiece
-   Would recommend
-   Would rewatch

The system should be able to calculate an optional personal rating
profile.

------------------------------------------------------------------------

## 15. Reviews and Notes

Support:

-   Private notes
-   Public-style review
-   Spoiler-free review
-   Spoiler section
-   Quotes entered by the user
-   Favorite scenes
-   Favorite characters
-   Personal observations

Spoiler content should be separately marked.

------------------------------------------------------------------------

## 16. Collections

Collections can be:

### Manual

User manually adds titles.

### Dynamic

Example:

`Oscar Winners + Unwatched + IMDb >= 8`

### Curated

Example:

`Best Korean Cinema`

### System

Automatically generated:

-   Unwatched
-   Favorites
-   Recently Added
-   Recently Completed
-   Dropped
-   Rewatch Candidates

------------------------------------------------------------------------

## 17. Franchise / Universe Tracking

A title may belong to:

-   Franchise
-   Shared universe
-   Series
-   Saga
-   Trilogy
-   Duology
-   Anthology

Store multiple viewing orders:

-   Release order
-   Chronological order
-   Story order
-   Recommended order
-   Optional order
-   Completionist order

Do not assume there is only one correct viewing order.

------------------------------------------------------------------------

## 18. Awards and Festivals

Track:

-   Oscar
-   BAFTA
-   Cannes
-   Palme d'Or
-   Venice
-   Berlin
-   Golden Globe
-   Emmy
-   SAG
-   National Film Awards
-   Filmfare
-   IIFA
-   Critics' Choice
-   César
-   Goya
-   European Film Awards
-   Anime awards
-   Major regional awards

Store:

-   Award organization
-   Ceremony year
-   Category
-   Nomination/win
-   Recipient
-   Title/person
-   Source

------------------------------------------------------------------------

## 19. Cultural Significance

Use controlled tags such as:

-   Oscar Winner
-   Palme d'Or
-   Golden Lion
-   Golden Bear
-   BAFTA Winner
-   National Award Winner
-   Filmfare Winner
-   Cult Classic
-   Viral Phenomenon
-   Meme Status
-   Industry Game-Changer
-   Sleeper Hit
-   Box Office Record
-   Censored / Controversial
-   Banned / Restricted
-   Landmark Work
-   New Wave
-   Genre Defining
-   Franchise Defining
-   Technical Milestone

Important: "banned" or "controversial" should include a source and
context rather than being a subjective tag.

------------------------------------------------------------------------

## 20. Recommendation Engine

Recommendation should not depend entirely on an LLM.

Use layers:

### Layer A --- Hard Filters

-   Language
-   Country
-   Year
-   Genre
-   Runtime
-   Certification
-   Platform
-   Watched state

### Layer B --- Similarity

-   Genre overlap
-   Keywords
-   Themes
-   Cast
-   Director
-   Studio
-   Franchise
-   Embeddings

### Layer C --- Personal Taste

-   Personal ratings
-   Favorites
-   Completion history
-   Drop history
-   Rewatch history

### Layer D --- Context

-   Available time
-   Mood
-   Company
-   Device
-   Subscription
-   Recent viewing
-   Desired intensity

### Layer E --- AI Explanation

The AI should explain:

> "You may like this because you rated X and Y highly, and this shares
> their psychological-thriller + slow-burn characteristics."

The AI should not invent reasons unsupported by stored data.

------------------------------------------------------------------------

## 21. Recommendation Modes

Examples:

-   Recommend Tonight
-   30-minute watch
-   Under 90 minutes
-   Weekend marathon
-   One perfect movie
-   Comfort watch
-   Dark night
-   Mind-bending
-   Emotional
-   Family-friendly
-   Date night
-   Solo night
-   Anime starter
-   Korean cinema starter
-   Indian cinema starter
-   Oscar education
-   Film-history education
-   Director marathon
-   Actor marathon
-   Franchise completion
-   Hidden gems
-   Cult classics
-   "Because you liked X"

------------------------------------------------------------------------

## 22. Taste Profile

The system should gradually learn:

-   Favorite genres
-   Least-liked genres
-   Favorite countries
-   Favorite languages
-   Favorite decades
-   Favorite directors
-   Favorite actors
-   Favorite studios
-   Preferred runtimes
-   Rating patterns
-   Completion behavior
-   Drop behavior

Taste should be explainable and editable.

------------------------------------------------------------------------

## 23. Search

Search should support:

-   Exact title
-   Partial title
-   Original title
-   Alternate title
-   Person
-   Character
-   Genre
-   Country
-   Language
-   Franchise
-   Platform
-   Award
-   Year
-   Keyword

Advanced natural-language search:

> "Show unwatched Korean crime thrillers under two hours."

The system should translate natural language into structured filters
before querying the database.

------------------------------------------------------------------------

## 24. Globalization

Support:

-   UTF-8
-   Original scripts
-   Transliteration
-   Multiple localized titles
-   Unicode-safe search
-   Country-specific certifications
-   Language hierarchy
-   Region-specific availability

Examples:

Japanese + romaji + English title

Korean + romanized title + English title

Chinese + simplified + traditional + romanized title

Indian languages + English transliteration

------------------------------------------------------------------------

## 25. Archival / Preservation Model

The system should track preservation risk without facilitating piracy.

Useful fields:

-   Physical media availability
-   Digital availability
-   Streaming availability
-   Region limitations
-   Restoration status
-   Archive institution
-   Festival/curated availability
-   Last known legal availability
-   Preservation notes
-   Rights uncertainty

Do not store or promote unauthorized download sources or piracy
channels.

------------------------------------------------------------------------

## 26. Data Quality System

Every important metadata field should have:

-   Source
-   Retrieved date
-   Confidence
-   Verification status
-   Last modified
-   Data provider
-   Version

Quality states:

-   Verified
-   Partially verified
-   Imported
-   Needs review
-   Conflicting
-   Deprecated

------------------------------------------------------------------------

## 27. Duplicate Detection

Potential duplicate matching should consider:

-   External IDs
-   Title
-   Original title
-   Release year
-   Runtime
-   Country
-   Director
-   Episode count

Never automatically merge ambiguous records without confidence
thresholds.

------------------------------------------------------------------------

## 28. Data Provenance

Every imported field should ideally be traceable.

Example:

`runtime_minutes = 142`

Source:

`TMDb`

Retrieved:

`2026-08-08`

Confidence:

`High`

This becomes essential when different providers disagree.

------------------------------------------------------------------------

## 29. AI Collaboration

AI agents should not directly modify production data without validation.

Recommended workflow:

`Research -> Candidate Data -> Validation -> Human Review -> Approved Data -> Production`

AI outputs should carry:

-   source
-   confidence
-   proposed change
-   reason
-   timestamp

------------------------------------------------------------------------

## 30. Roles for AI Tools

### ChatGPT

-   Product architecture
-   Database design
-   Requirements
-   System reasoning
-   Documentation
-   Recommendation architecture
-   QA planning

### Claude

-   Large-context document analysis
-   Schema review
-   Code review
-   Documentation
-   Data-quality reasoning

### Gemini

-   Current web research
-   New-release research
-   Regional discovery
-   Cross-checking current information

### DeepSeek

-   SQL
-   Algorithms
-   Backend implementation
-   Performance reasoning

### Kimi

-   Large-scale catalog research
-   Long-context regional research
-   Chinese/East Asian catalog research

### Other agents

Use only when their capability or integration is materially useful.

No AI should be considered an authoritative source by itself.

------------------------------------------------------------------------

## 31. External Data Strategy

Potential sources:

### Primary / structured sources

-   TMDb
-   IMDb licensed data/API
-   AniList
-   MyAnimeList
-   JustWatch partner data
-   Wikidata
-   Official award/festival sites
-   Official platform pages
-   Official studio/distributor pages

### Editorial / discovery sources

-   Variety
-   The Hollywood Reporter
-   Deadline
-   IndieWire
-   Film Companion
-   major regional entertainment publications

### Community/reference sources

-   Letterboxd
-   Trakt
-   IMDb user data
-   AniList community data
-   MyAnimeList community data

Community ratings should be labeled as community ratings, not objective
critical truth.

------------------------------------------------------------------------

## 32. Licensing Principle

Metadata and media are different.

CineVault OS should store legal metadata, links and references, not
redistribute copyrighted movies or series.

Do not design the system around pirated files or unauthorized
Telegram/archive channels.

Where an API or dataset requires attribution, licensing, payment, or
usage restrictions, those constraints must be recorded in the project's
data-source registry.

------------------------------------------------------------------------

## 33. Excel / Google Sheets Compatibility

Even though PostgreSQL should eventually be the canonical database,
exports should remain possible.

Recommended export columns:

`internal_id, external_ids, title, original_title, type, year, language, country, genres, runtime, director, cast, platform, region, watched, status, progress, personal_rating, favorite, notes, last_verified`

Checkboxes should be represented consistently in CSV/Excel as:

-   TRUE/FALSE
-   1/0

UI checkboxes can be generated from those values.

------------------------------------------------------------------------

## 34. Dashboard

Main dashboard should show:

-   Total titles
-   Watched
-   Unwatched
-   Watching
-   Completed
-   Dropped
-   Favorites
-   Total watch hours
-   Movies watched
-   Series completed
-   Anime completed
-   Countries explored
-   Languages explored
-   Current watch streak
-   Monthly watch count
-   Annual watch count
-   Average personal rating

------------------------------------------------------------------------

## 35. Future Features

Possible additions:

-   Physical collection scanner
-   Barcode/ISBN scanning
-   Blu-ray/DVD inventory
-   Watch-party tracking
-   Shared family library
-   Multiple profiles
-   Private/public profiles
-   Social following
-   Lists
-   Comments
-   Likes
-   Recommendation challenges
-   Awards prediction
-   Festival calendar
-   Release calendar
-   Personalized newsletter
-   Calendar integration
-   Smart TV companion
-   Browser extension
-   Shareable recommendation cards
-   AI-generated viewing itineraries
-   Mood journal
-   soundtrack tracking
-   favorite quotes
-   scene tracking
-   character tracking
-   cinematography metadata
-   filming locations
-   trivia
-   behind-the-scenes references

These are optional extensions, not requirements for the initial product
definition.

------------------------------------------------------------------------

## 36. Non-Goals

CineVault OS should not initially become:

-   A movie piracy platform
-   A video hosting service
-   A social network clone
-   A replacement for every entertainment website
-   A giant uncontrolled scraper
-   An AI-generated misinformation database

The product should prioritize **quality, provenance, usability and
personal value over raw row count**.

------------------------------------------------------------------------

## 37. Success Definition

The system is successful when the user can:

1.  Find almost any relevant entertainment title quickly.
2.  Understand what it is and why it matters.
3.  Know whether they have watched it.
4.  Track episode/movie progress.
5.  Rate and annotate it.
6.  Know where it is legally available in their region when current data
    exists.
7.  Discover related titles.
8.  Analyze their own viewing history.
9.  Receive useful, explainable recommendations.
10. Export all personal data.
11. Continue using the system years later without structural migration.

------------------------------------------------------------------------

## 38. Long-Term Product Identity

CineVault OS should be treated as:

**Entertainment Database + Personal Media Library + Knowledge Graph +
Recommendation Engine + Viewing Journal + AI Assistant**

The database is the foundation.

The UI is replaceable.

The AI is replaceable.

The external providers are replaceable.

The user's personal data must remain portable and protected.

------------------------------------------------------------------------

# Research Notes

Current technical research confirms several important design decisions:

-   PostgreSQL provides built-in full-text search, indexing, ranking and
    related search capabilities, making it suitable for the initial
    relational/search foundation.
-   FastAPI provides a strong API layer for Python applications and
    automatic API documentation.
-   Flutter remains a strong cross-platform client choice; current
    official documentation supports mobile, web and desktop targets.
-   TMDb provides movie/TV/person/image APIs but has usage terms and
    rate-limit considerations.
-   IMDb provides licensed bulk/API products with stable IDs, schemas
    and versioning; licensing must be evaluated before using IMDb data
    commercially or redistributing it.
-   JustWatch provides partner integrations for
    country/provider-specific VOD offers and documents frequent
    availability updates.
-   External providers must therefore be treated as data sources, not as
    the permanent source of truth.

This research baseline should be re-checked before implementation
because API terms, platform availability and licensing can change.

------------------------------------------------------------------------

# Master Rule for All Future AI Agents

Before modifying CineVault OS, an AI agent must:

1.  Read this document.
2.  Read the technical requirements document.
3.  Preserve existing architecture decisions unless a justified change
    is proposed.
4.  Never mix user data with external metadata.
5.  Never silently overwrite verified information.
6.  Preserve source/provenance information.
7.  Never introduce piracy/unauthorized distribution functionality.
8.  Prefer extensible schemas over hard-coded lists.
9.  Explain architectural tradeoffs before making major changes.
10. Keep all data exportable.
