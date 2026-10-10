-- CineVault OS — Flyway Migration V4.0: Canonical Reference Taxonomy (CAT-1)
-- Populates authoritative, non-sensitive reference taxonomy and classification metadata
-- required for bare-metal / blank-database production instances.
-- Idempotent: ON CONFLICT DO UPDATE / DO NOTHING.

-- 1. Content Types
INSERT INTO canonical.content_type (content_type_id, type_name, description) VALUES
('movie', 'Feature Film', 'Full-length motion picture released for theatrical, streaming, or physical media.'),
('tv_series', 'Television Series', 'Episodic television or web broadcast content.'),
('short_film', 'Short Film', 'Motion picture with a runtime under 40 minutes.')
ON CONFLICT (content_type_id) DO UPDATE SET type_name = EXCLUDED.type_name, description = EXCLUDED.description;

-- 2. Standard Genres
INSERT INTO canonical.genre (genre_id, name, description) VALUES
('action', 'Action', 'High-energy sequences, chases, physical feats, and combat.'),
('drama', 'Drama', 'Character-driven narratives focusing on emotional themes.'),
('sci_fi', 'Science Fiction', 'Speculative fiction dealing with futuristic concepts, technology, or space.'),
('comedy', 'Comedy', 'Humorous narratives designed to entertain and amuse.'),
('documentary', 'Documentary', 'Non-fictional recording of real-world events, subjects, or stories.'),
('thriller', 'Thriller', 'High-suspense tension and psychological anticipation.'),
('animation', 'Animation', 'Hand-drawn, computer-generated, or stop-motion animated works.')
ON CONFLICT (genre_id) DO UPDATE SET name = EXCLUDED.name;

-- 3. Themes & Keywords
INSERT INTO canonical.theme (theme_id, name, description) VALUES
('time_travel', 'Time Travel', 'Narratives featuring temporal displacement.'),
('ai_rebellion', 'AI Rebellion', 'Artificial intelligence defying human authority.'),
('cyberpunk', 'Cyberpunk', 'High-tech low-life futuristic society.')
ON CONFLICT (theme_id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO canonical.keyword (keyword_id, name) VALUES
('neo_noir', 'Neo-Noir'),
('dystopia', 'Dystopia'),
('mind_bending', 'Mind-Bending')
ON CONFLICT (keyword_id) DO UPDATE SET name = EXCLUDED.name;

-- 4. Credit Roles
INSERT INTO canonical.credit_role (credit_role_id, role_name, category) VALUES
('director', 'Director', 'CREW'),
('actor', 'Actor', 'CAST'),
('writer', 'Screenwriter', 'CREW'),
('cinematographer', 'Director of Photography', 'CREW'),
('composer', 'Composer', 'CREW'),
('producer', 'Producer', 'CREW')
ON CONFLICT (credit_role_id) DO UPDATE SET role_name = EXCLUDED.role_name;

-- 5. Streaming Platforms
INSERT INTO canonical.platform (platform_id, name, code) VALUES
('00000000-0000-7000-8000-000000000001', 'Netflix', 'NETFLIX'),
('00000000-0000-7000-8000-000000000002', 'Amazon Prime Video', 'PRIME_VIDEO'),
('00000000-0000-7000-8000-000000000003', 'The Criterion Channel', 'CRITERION')
ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name;
