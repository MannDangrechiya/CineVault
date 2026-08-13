-- CineVault OS — Flyway Migration V1.9: Data Model Scaling Indexes (Day 3)
-- Supports scaling to 5,000+ -> 1,000,000+ titles without structural redesign

-- 1. Foreign Key & Query Filters on Canonical Title
CREATE INDEX IF NOT EXISTS idx_title_content_type ON canonical.title (content_type_id);
CREATE INDEX IF NOT EXISTS idx_title_production_year ON canonical.title (production_year);
CREATE INDEX IF NOT EXISTS idx_title_status_flag ON canonical.title (status_flag);
CREATE INDEX IF NOT EXISTS idx_title_original_trgm ON canonical.title USING gin (original_title gin_trgm_ops);

-- 2. Episodic Hierarchy Indexes
CREATE INDEX IF NOT EXISTS idx_season_title ON canonical.season (title_id);
CREATE INDEX IF NOT EXISTS idx_episode_season ON canonical.episode (season_id);

-- 3. Cut & Release Distribution Hierarchy Indexes
CREATE INDEX IF NOT EXISTS idx_edition_title ON canonical.edition (title_id);
CREATE INDEX IF NOT EXISTS idx_release_edition ON canonical.release (edition_id);
CREATE INDEX IF NOT EXISTS idx_release_country_date ON canonical.release (country_code, release_date);

-- 4. Franchise & Viewing Order Hierarchy Indexes
CREATE INDEX IF NOT EXISTS idx_franchise_universe ON canonical.franchise (universe_id);
CREATE INDEX IF NOT EXISTS idx_franchise_entry_franchise ON canonical.franchise_entry (franchise_id);
CREATE INDEX IF NOT EXISTS idx_franchise_entry_title ON canonical.franchise_entry (title_id);
CREATE INDEX IF NOT EXISTS idx_viewing_order_franchise ON canonical.viewing_order (franchise_id);
CREATE INDEX IF NOT EXISTS idx_viewing_order_item_order ON canonical.viewing_order_item (viewing_order_id);

-- 5. Language Mapping Indexes
CREATE INDEX IF NOT EXISTS idx_title_lang_title ON canonical.title_lang (title_id);
CREATE INDEX IF NOT EXISTS idx_title_lang_code ON canonical.title_lang (language_code);
