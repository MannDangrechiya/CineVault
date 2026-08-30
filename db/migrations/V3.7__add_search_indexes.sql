-- CineVault OS - Flyway Migration V3.7: Search Performance Indexes
-- Implements W9 Search Quality requirements

-- Add GIN Trigram index on title aliases for fast fuzzy search
CREATE INDEX IF NOT EXISTS idx_title_alias_trgm ON canonical.title_alias USING gin (alias_name gin_trgm_ops);

-- Index display_id for fast exact matching if not already backed by unique constraint
-- Display ID is already UNIQUE (uq_canonical_title_display_id or similar), but we'll ensure we can search it fast.

