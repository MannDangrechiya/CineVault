-- CineVault OS — Flyway Migration V1.2: Canonical Domain Tables (CAT-1)
-- Implements ADR-001, ADR-002, Data Model V1, Physical Database Design V1

-- Taxonomy Tables
CREATE TABLE canonical.content_type (
    content_type_id VARCHAR(32) PRIMARY KEY,
    type_name VARCHAR(64) NOT NULL,
    description TEXT
);

CREATE TABLE canonical.genre (
    genre_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    description TEXT
);

CREATE TABLE canonical.theme (
    theme_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    description TEXT
);

CREATE TABLE canonical.keyword (
    keyword_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL
);

CREATE TABLE canonical.credit_role (
    credit_role_id VARCHAR(64) PRIMARY KEY,
    role_name VARCHAR(128) NOT NULL,
    category VARCHAR(64) NOT NULL
);

-- Core Title Hierarchy (ADR-001, ADR-002)
CREATE TABLE canonical.title (
    title_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    display_id VARCHAR(32) NOT NULL UNIQUE,
    content_type_id VARCHAR(32) NOT NULL REFERENCES canonical.content_type(content_type_id),
    canonical_title VARCHAR(512) NOT NULL,
    original_title VARCHAR(512) NOT NULL,
    production_year SMALLINT CONSTRAINT check_production_year CHECK (production_year >= 1888 AND production_year <= 2100),
    tagline VARCHAR(512),
    synopsis TEXT,
    status_flag VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE canonical.edition (
    edition_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE RESTRICT,
    edition_name VARCHAR(256) NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT false,
    runtime_minutes INTEGER,
    aspect_ratio VARCHAR(32),
    color_format VARCHAR(32),
    sound_mix VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE canonical.release (
    release_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    edition_id UUID NOT NULL REFERENCES canonical.edition(edition_id) ON DELETE CASCADE,
    release_name VARCHAR(256) NOT NULL,
    release_type VARCHAR(64) NOT NULL,
    release_date DATE,
    country_code CHAR(2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE canonical.identity_redirect (
    redirect_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    from_id UUID NOT NULL,
    to_id UUID NOT NULL,
    entity_type VARCHAR(64) NOT NULL,
    merge_reason VARCHAR(256),
    merged_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

-- Episodic Hierarchy
CREATE TABLE canonical.season (
    season_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE RESTRICT,
    season_number INTEGER NOT NULL,
    season_name VARCHAR(256),
    overview TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT unique_season_number UNIQUE (title_id, season_number)
);

CREATE TABLE canonical.episode (
    episode_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    season_id UUID NOT NULL REFERENCES canonical.season(season_id) ON DELETE RESTRICT,
    episode_number INTEGER NOT NULL,
    episode_name VARCHAR(512),
    air_date DATE,
    runtime_minutes INTEGER,
    overview TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT unique_episode_number UNIQUE (season_id, episode_number)
);

CREATE TABLE canonical.regional_episode_order (
    order_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    episode_id UUID NOT NULL REFERENCES canonical.episode(episode_id) ON DELETE CASCADE,
    region_code CHAR(2) NOT NULL,
    display_order INTEGER NOT NULL,
    regional_title VARCHAR(512)
);

-- Universe, Franchise, & Viewing Orders
CREATE TABLE canonical.universe (
    universe_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    name VARCHAR(256) NOT NULL,
    overview TEXT
);

CREATE TABLE canonical.franchise (
    franchise_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    universe_id UUID REFERENCES canonical.universe(universe_id) ON DELETE SET NULL,
    name VARCHAR(256) NOT NULL
);

CREATE TABLE canonical.franchise_entry (
    franchise_entry_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    franchise_id UUID NOT NULL REFERENCES canonical.franchise(franchise_id) ON DELETE CASCADE,
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE RESTRICT,
    entry_type VARCHAR(64) NOT NULL DEFAULT 'CANONICAL'
);

CREATE TABLE canonical.viewing_order (
    viewing_order_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    franchise_id UUID NOT NULL REFERENCES canonical.franchise(franchise_id) ON DELETE CASCADE,
    order_name VARCHAR(256) NOT NULL,
    order_type VARCHAR(64) NOT NULL DEFAULT 'CHRONOLOGICAL'
);

CREATE TABLE canonical.viewing_order_item (
    item_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    viewing_order_id UUID NOT NULL REFERENCES canonical.viewing_order(viewing_order_id) ON DELETE CASCADE,
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE RESTRICT,
    position INTEGER NOT NULL
);

-- People, Credits & Companies
CREATE TABLE canonical.person (
    person_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    canonical_name VARCHAR(256) NOT NULL,
    birth_date DATE,
    death_date DATE,
    gender VARCHAR(32),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE canonical.person_name (
    name_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    person_id UUID NOT NULL REFERENCES canonical.person(person_id) ON DELETE CASCADE,
    name_type VARCHAR(64) NOT NULL DEFAULT 'PRIMARY',
    name_value VARCHAR(256) NOT NULL,
    language_code CHAR(3)
);

CREATE TABLE canonical.credit (
    credit_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE RESTRICT,
    edition_id UUID REFERENCES canonical.edition(edition_id) ON DELETE SET NULL,
    person_id UUID NOT NULL REFERENCES canonical.person(person_id) ON DELETE RESTRICT,
    credit_role_id VARCHAR(64) NOT NULL REFERENCES canonical.credit_role(credit_role_id),
    character_name VARCHAR(256),
    billing_order INTEGER
);

CREATE TABLE canonical.production_company (
    company_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    company_name VARCHAR(256) NOT NULL,
    country_code CHAR(2)
);

CREATE TABLE canonical.title_company (
    title_company_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE RESTRICT,
    company_id UUID NOT NULL REFERENCES canonical.production_company(company_id) ON DELETE RESTRICT,
    role VARCHAR(64) NOT NULL DEFAULT 'PRODUCTION'
);

-- Many-to-Many Relationships & Metadata Tables
CREATE TABLE canonical.title_genre (
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE CASCADE,
    genre_id VARCHAR(64) NOT NULL REFERENCES canonical.genre(genre_id) ON DELETE CASCADE,
    PRIMARY KEY (title_id, genre_id)
);

CREATE TABLE canonical.title_theme (
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE CASCADE,
    theme_id VARCHAR(64) NOT NULL REFERENCES canonical.theme(theme_id) ON DELETE CASCADE,
    PRIMARY KEY (title_id, theme_id)
);

CREATE TABLE canonical.title_keyword (
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE CASCADE,
    keyword_id VARCHAR(64) NOT NULL REFERENCES canonical.keyword(keyword_id) ON DELETE CASCADE,
    PRIMARY KEY (title_id, keyword_id)
);

CREATE TABLE canonical.title_country (
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE CASCADE,
    country_code CHAR(2) NOT NULL,
    PRIMARY KEY (title_id, country_code)
);

CREATE TABLE canonical.title_lang (
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE CASCADE,
    language_code CHAR(3) NOT NULL,
    PRIMARY KEY (title_id, language_code)
);

-- Awards & Festivals
CREATE TABLE canonical.award (
    award_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    award_name VARCHAR(256) NOT NULL,
    organization VARCHAR(256) NOT NULL
);

CREATE TABLE canonical.award_category (
    category_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    award_id UUID NOT NULL REFERENCES canonical.award(award_id) ON DELETE CASCADE,
    category_name VARCHAR(256) NOT NULL
);

CREATE TABLE canonical.award_event (
    event_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    award_id UUID NOT NULL REFERENCES canonical.award(award_id) ON DELETE CASCADE,
    year SMALLINT NOT NULL,
    edition_number INTEGER
);

CREATE TABLE canonical.award_result (
    result_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    event_id UUID NOT NULL REFERENCES canonical.award_event(event_id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES canonical.award_category(category_id) ON DELETE CASCADE,
    title_id UUID REFERENCES canonical.title(title_id) ON DELETE RESTRICT,
    person_id UUID REFERENCES canonical.person(person_id) ON DELETE RESTRICT,
    is_winner BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE canonical.festival (
    festival_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    festival_name VARCHAR(256) NOT NULL,
    country_code CHAR(2)
);

CREATE TABLE canonical.festival_edition (
    festival_edition_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    festival_id UUID NOT NULL REFERENCES canonical.festival(festival_id) ON DELETE CASCADE,
    year SMALLINT NOT NULL,
    edition_number INTEGER
);

CREATE TABLE canonical.festival_participation (
    participation_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    festival_edition_id UUID NOT NULL REFERENCES canonical.festival_edition(festival_edition_id) ON DELETE CASCADE,
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE RESTRICT,
    section_name VARCHAR(256)
);

-- Platform Offers
CREATE TABLE canonical.platform (
    platform_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    name VARCHAR(256) NOT NULL,
    code VARCHAR(64) NOT NULL UNIQUE
);

CREATE TABLE canonical.platform_offer (
    offer_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    platform_id UUID NOT NULL REFERENCES canonical.platform(platform_id) ON DELETE RESTRICT,
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE RESTRICT,
    country_code CHAR(2) NOT NULL,
    offer_type VARCHAR(32) NOT NULL,
    valid_from TIMESTAMPTZ,
    valid_to TIMESTAMPTZ
);

-- External Provider Identifier Mapping Tables (ADR-001, DS-01)
CREATE TABLE canonical.title_external_id (
    mapping_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE CASCADE,
    provider_name VARCHAR(64) NOT NULL,
    external_id VARCHAR(128) NOT NULL,
    external_url VARCHAR(512),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT unique_provider_title_mapping UNIQUE (provider_name, external_id)
);

CREATE TABLE canonical.person_external_id (
    mapping_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    person_id UUID NOT NULL REFERENCES canonical.person(person_id) ON DELETE CASCADE,
    provider_name VARCHAR(64) NOT NULL,
    external_id VARCHAR(128) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT unique_provider_person_mapping UNIQUE (provider_name, external_id)
);
