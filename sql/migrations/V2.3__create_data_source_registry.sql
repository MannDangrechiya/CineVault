-- CineVault OS — V2.3 Flyway Migration: Persistent Data Source Registry (DS-01, ADR-001, Batch 8)
-- Implements DB-backed persistent data source registry with dynamic governance, access levels, and authority roles

CREATE TABLE IF NOT EXISTS ingestion.data_source_registry (
    source_id VARCHAR(64) PRIMARY KEY,
    provider_name VARCHAR(64) NOT NULL UNIQUE,
    dataset_api VARCHAR(128) NOT NULL,
    source_type VARCHAR(64) NOT NULL,
    official_url VARCHAR(256) NOT NULL,
    license_info VARCHAR(256) NOT NULL,
    attribution_requirement VARCHAR(256),
    commercial_use_status VARCHAR(64) NOT NULL,
    redistribution_restrictions VARCHAR(256),
    rate_limit_per_min INTEGER NOT NULL DEFAULT 60,
    update_frequency VARCHAR(64) NOT NULL DEFAULT 'DAILY',
    authentication_requirements VARCHAR(64) NOT NULL,
    regions JSONB NOT NULL DEFAULT '[]'::jsonb,
    available_fields JSONB NOT NULL DEFAULT '[]'::jsonb,
    reliability_score NUMERIC(3, 2) NOT NULL DEFAULT 0.50,
    activation_status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    authority_role VARCHAR(64) NOT NULL,
    access_status VARCHAR(32) NOT NULL DEFAULT 'PERMITTED',
    requires_api_key BOOLEAN NOT NULL DEFAULT true,
    scraping_permitted BOOLEAN NOT NULL DEFAULT false,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_data_source_registry_provider ON ingestion.data_source_registry(provider_name);
CREATE INDEX IF NOT EXISTS idx_data_source_registry_access ON ingestion.data_source_registry(access_status);
CREATE INDEX IF NOT EXISTS idx_data_source_registry_status ON ingestion.data_source_registry(activation_status);

-- Seed initial 8 providers from LicensingGate baseline
INSERT INTO ingestion.data_source_registry (
    source_id, provider_name, dataset_api, source_type, official_url, license_info,
    attribution_requirement, commercial_use_status, redistribution_restrictions,
    rate_limit_per_min, update_frequency, authentication_requirements,
    regions, available_fields, reliability_score, activation_status, authority_role,
    access_status, requires_api_key, scraping_permitted, description
) VALUES
(
    'kobis', 'KOBIS', 'KOBIS OpenAPI REST', 'OFFICIAL_BOX_OFFICE', 'http://www.kobis.or.kr/',
    'Public Data Open License (Type 1)', 'Source attribution required (KOBIS)',
    'PERMITTED', 'Commercial redistribution permitted with attribution',
    300, 'DAILY', 'API_KEY',
    '["KR"]'::jsonb, '["title", "original_title", "directors", "cast", "release_year", "genres"]'::jsonb,
    0.98, 'ACTIVE', 'PRIMARY_KOREAN', 'PERMITTED', true, false,
    'Primary Korean-domain film box office & canonical catalog authority.'
),
(
    'tvdb', 'TVDB', 'TVDB API v4 REST', 'COMMERCIAL_METADATA_API', 'https://thetvdb.com/',
    'TVDB API v4 Commercial License', 'Attribution required',
    'LICENSED', 'Requires paid API key subscription',
    1200, 'HOURLY', 'BEARER_TOKEN',
    '["GLOBAL"]'::jsonb, '["title", "seasons", "episodes", "overview", "genres", "release_year"]'::jsonb,
    0.92, 'APPROVED', 'SECONDARY_TV', 'PERMITTED', true, false,
    'Secondary TV series & episode structure authority.'
),
(
    'tmdb', 'TMDB', 'TMDb API v3 REST', 'GLOBAL_COMMUNITY_METADATA', 'https://www.themoviedb.org/',
    'TMDb API Terms of Use', 'TMDb attribution logo required',
    'PERMITTED', 'Free for non-commercial and commercial with attribution',
    2400, 'HOURLY', 'BEARER_TOKEN',
    '["GLOBAL"]'::jsonb, '["title", "original_title", "overview", "release_date", "runtime", "genres", "production_companies"]'::jsonb,
    0.90, 'ACTIVE', 'CANDIDATE_GLOBAL', 'PERMITTED', true, false,
    'Global candidate metadata source with broad coverage across film and television.'
),
(
    'anilist', 'ANILIST', 'AniList GraphQL API v2', 'ANIME_SPECIALIST_GRAPHQL', 'https://anilist.co/',
    'AniList API Terms of Service', 'Non-commercial attribution required',
    'NON_COMMERCIAL_ONLY', 'Commercial use strictly requires explicit written agreement',
    90, 'DAILY', 'BEARER_TOKEN',
    '["JP", "GLOBAL"]'::jsonb, '["title", "romaji", "native", "episodes", "format", "genres", "studios"]'::jsonb,
    0.95, 'ACTIVE', 'ANIME_SPECIALIST', 'PERMITTED_SERVER_ONLY', true, false,
    'Primary authority for Japanese animation, manga, format classifications, and voice talent.'
),
(
    'wikidata', 'WIKIDATA', 'Wikidata SPARQL Query Service', 'OPEN_KNOWLEDGE_GRAPH_SPARQL', 'https://www.wikidata.org/',
    'Creative Commons CC0 1.0 Universal Public Domain Dedication', 'None (CC0 Public Domain)',
    'PERMITTED', 'Unrestricted public domain reuse',
    300, 'WEEKLY', 'NONE',
    '["GLOBAL"]'::jsonb, '["instance_of", "publication_date", "country_of_origin", "director", "cast_member", "external_identifiers"]'::jsonb,
    0.96, 'ACTIVE', 'REFERENCE_SPARQL', 'PERMITTED', false, false,
    'Open universal knowledge base for cross-linking identifier authority and entity resolution.'
),
(
    'omdb', 'OMDB', 'OMDb API REST', 'RESTRICTED_COMMERCIAL_API', 'http://www.omdbapi.com/',
    'OMDb API Terms of Service', 'Attribution required',
    'RESTRICTED', 'Free tier for personal only; commercial requires paid Patreon license',
    60, 'WEEKLY', 'API_KEY',
    '["US", "GLOBAL"]'::jsonb, '["title", "year", "rated", "released", "runtime", "genre", "ratings"]'::jsonb,
    0.80, 'REVIEW_REQUIRED', 'CANDIDATE_GLOBAL', 'RESTRICTED', true, false,
    'Commercial use requires active paid Patreon license key.'
),
(
    'imdb_scraping', 'IMDB_SCRAPING', 'Direct HTML Scraping', 'UNAUTHORIZED_SCRAPING', 'https://www.imdb.com/',
    'IMDb Conditions of Use (Prohibits Robot/Automated Scraping)', 'None',
    'PROHIBITED', 'Direct HTML scraping is legally and contractually prohibited',
    0, 'NEVER', 'UNAUTHORIZED',
    '["GLOBAL"]'::jsonb, '[]'::jsonb,
    0.00, 'SUSPENDED', 'UNAUTHORIZED', 'PROHIBITED', false, false,
    'Automated scraping violates IMDb robots.txt and Conditions of Use. Blocked at licensing gate.'
),
(
    'thepiratebay', 'THEPIRATEBAY', 'BitTorrent Tracker / Scraper', 'PROHIBITED_PIRACY_TRACKER', 'https://thepiratebay.org/',
    'None (Piracy / Copyright Infringement)', 'None',
    'PROHIBITED', 'Prohibited copyright infringement source',
    0, 'NEVER', 'UNAUTHORIZED',
    '["GLOBAL"]'::jsonb, '[]'::jsonb,
    0.00, 'RETIRED', 'UNAUTHORIZED', 'PROHIBITED', false, false,
    'Prohibited copyright-infringing content tracker. Absolute block enforced by system policy.'
)
ON CONFLICT (provider_name) DO NOTHING;
