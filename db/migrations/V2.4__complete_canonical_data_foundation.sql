-- CineVault OS — Flyway Migration V2.4: Canonical Data Foundation Enhancements
-- Fulfills Phase 1 Requirements: Title Aliases, Ratings/Certifications, Taxonomy, and Complete Canonical Relations

-- 1. Title Aliases (Alternative names, romanizations, localized titles)
CREATE TABLE IF NOT EXISTS canonical.title_alias (
    alias_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE CASCADE,
    alias_name VARCHAR(512) NOT NULL,
    alias_type VARCHAR(64) NOT NULL DEFAULT 'ALTERNATIVE', -- 'TRANSLITERATED', 'LOCALIZED', 'WORKING', 'ALTERNATIVE'
    language_code CHAR(3),
    country_code CHAR(2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS idx_title_alias_title_id ON canonical.title_alias(title_id);
CREATE INDEX IF NOT EXISTS idx_title_alias_name ON canonical.title_alias(alias_name);

-- 2. Certifications / Content Ratings (MPAA, BBFC, TV-PG, CERO, etc.)
CREATE TABLE IF NOT EXISTS canonical.certification (
    certification_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    country_code CHAR(2) NOT NULL,
    certification_code VARCHAR(32) NOT NULL,
    rating_body VARCHAR(128), -- MPAA, BBFC, CBFC, FSK, etc.
    meaning TEXT,
    min_age SMALLINT,
    CONSTRAINT unique_country_cert UNIQUE (country_code, certification_code)
);

CREATE TABLE IF NOT EXISTS canonical.title_certification (
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE CASCADE,
    certification_id UUID NOT NULL REFERENCES canonical.certification(certification_id) ON DELETE CASCADE,
    note VARCHAR(256),
    PRIMARY KEY (title_id, certification_id)
);

CREATE INDEX IF NOT EXISTS idx_title_cert_title_id ON canonical.title_certification(title_id);

-- 3. Production Company role indexing and enhancements
CREATE INDEX IF NOT EXISTS idx_title_company_title_id ON canonical.title_company(title_id);
CREATE INDEX IF NOT EXISTS idx_title_company_role ON canonical.title_company(role);
CREATE INDEX IF NOT EXISTS idx_credit_title_id ON canonical.credit(title_id);
CREATE INDEX IF NOT EXISTS idx_credit_person_id ON canonical.credit(person_id);
CREATE INDEX IF NOT EXISTS idx_franchise_entry_title_id ON canonical.franchise_entry(title_id);
CREATE INDEX IF NOT EXISTS idx_award_result_title_id ON canonical.award_result(title_id);
CREATE INDEX IF NOT EXISTS idx_festival_part_title_id ON canonical.festival_participation(title_id);
