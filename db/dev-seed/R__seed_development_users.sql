-- CineVault OS — Flyway Repeatable Migration: Synthetic Development Seed Users
-- ENVIRONMENT BOUNDARY: DEVELOPMENT ONLY. NEVER EXECUTE OR LOAD IN PRODUCTION.

INSERT INTO auth.user (user_id, email, password_hash, roles, is_active) VALUES
(
    '018f0000-0000-7000-8000-000000000001',
    'dev@cinevault.local',
    '$2b$12$PVfblhI8qmxxO1ZbUoqIr.U.zkYngh4J9jLz5MxXcyCZPUB69DstG',
    ARRAY['authenticated_user'],
    true
),
(
    '018f0000-0000-7000-8000-000000000002',
    'curator@cinevault.local',
    '$2b$12$Yw5cy4oqZ80UoPxN/22V3uxLLYR73Dhy2dFGGBHJafogPcCUXVhXS',
    ARRAY['authenticated_user', 'curator'],
    true
)
ON CONFLICT (email) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    roles = EXCLUDED.roles,
    is_active = EXCLUDED.is_active;
