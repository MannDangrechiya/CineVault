-- CineVault OS — Flyway Migration V2.2: Add Catalog Uniqueness Constraints
-- Enforces data integrity at database level preventing duplicate canonical titles and provider external IDs

-- 1. Enforce unique canonical title per production year and content type
ALTER TABLE canonical.title
    ADD CONSTRAINT uq_canonical_title_year_type UNIQUE (canonical_title, production_year, content_type_id);

-- 2. Ensure title_external_id has explicit unique constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'unique_provider_title_mapping' OR conname = 'uq_provider_external_id'
    ) THEN
        ALTER TABLE canonical.title_external_id
            ADD CONSTRAINT uq_provider_external_id UNIQUE (provider_name, external_id);
    END IF;
END $$;
