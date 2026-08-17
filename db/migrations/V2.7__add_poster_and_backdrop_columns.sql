-- CineVault OS — Flyway Migration V2.7: Add Poster and Backdrop Columns to Canonical Title
-- Supports automated metadata, poster, backdrop and overview synchronization from TMDB and external sources

ALTER TABLE canonical.title
    ADD COLUMN IF NOT EXISTS poster_url VARCHAR(512),
    ADD COLUMN IF NOT EXISTS backdrop_url VARCHAR(512),
    ADD COLUMN IF NOT EXISTS poster_sync_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    ADD COLUMN IF NOT EXISTS metadata_synced_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_title_poster_sync_status
    ON canonical.title(poster_sync_status)
    WHERE poster_url IS NULL;
