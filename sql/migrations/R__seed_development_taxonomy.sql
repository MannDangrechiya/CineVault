-- CineVault OS — Flyway Repeatable Migration: Synthetic Development Seed Taxonomy
-- ENVIRONMENT BOUNDARY: DEVELOPMENT ONLY. NEVER EXUTE OR LOAD IN PRODUCTION.

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

-- 6. Synthetic Test Titles (DEVELOPMENT ONLY SEED)
INSERT INTO canonical.title (title_id, display_id, content_type_id, canonical_title, original_title, production_year, tagline, synopsis, status_flag) VALUES
('10000000-0000-7000-8000-000000000001', 'MOV-000001', 'movie', 'Parasite', 'Gisaengchung', 2019, 'Act like you own the place.', 'Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.', 'ACTIVE'),
('10000000-0000-7000-8000-000000000002', 'MOV-000002', 'movie', 'Inception', 'Inception', 2010, 'Your mind is the scene of the crime.', 'A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.', 'ACTIVE')
ON CONFLICT (display_id) DO UPDATE SET canonical_title = EXCLUDED.canonical_title;

-- 7. Synthetic Primary Editions
INSERT INTO canonical.edition (edition_id, title_id, edition_name, is_primary, runtime_minutes, aspect_ratio, sound_mix) VALUES
('20000000-0000-7000-8000-000000000001', '10000000-0000-7000-8000-000000000001', 'Theatrical Cut', true, 132, '2.39:1', 'Dolby Atmos'),
('20000000-0000-7000-8000-000000000002', '10000000-0000-7000-8000-000000000002', 'Theatrical Cut', true, 148, '2.39:1', 'DTS-HD MA 5.1')
ON CONFLICT (edition_id) DO NOTHING;

-- 8. Synthetic Persons & Credits
INSERT INTO canonical.person (person_id, canonical_name, birth_date, gender) VALUES
('30000000-0000-7000-8000-000000000001', 'Bong Joon-ho', '1969-09-14', 'MALE'),
('30000000-0000-7000-8000-000000000002', 'Christopher Nolan', '1970-07-30', 'MALE')
ON CONFLICT (person_id) DO NOTHING;

INSERT INTO canonical.credit (credit_id, title_id, edition_id, person_id, credit_role_id, billing_order) VALUES
('40000000-0000-7000-8000-000000000001', '10000000-0000-7000-8000-000000000001', '20000000-0000-7000-8000-000000000001', '30000000-0000-7000-8000-000000000001', 'director', 1),
('40000000-0000-7000-8000-000000000002', '10000000-0000-7000-8000-000000000002', '20000000-0000-7000-8000-000000000002', '30000000-0000-7000-8000-000000000002', 'director', 1)
ON CONFLICT (credit_id) DO NOTHING;
