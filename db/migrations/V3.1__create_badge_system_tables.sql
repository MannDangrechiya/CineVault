-- CineVault Physical Database Design — Module 3 / Phase 1
-- V3.1: Creates social.badge_definition and social.user_badge tables with initial seed badges

CREATE TABLE IF NOT EXISTS social.badge_definition (
    badge_id UUID PRIMARY KEY,
    slug VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    description TEXT NOT NULL,
    icon_url VARCHAR(512),
    criteria_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS social.user_badge (
    user_id UUID NOT NULL,
    badge_id UUID NOT NULL REFERENCES social.badge_definition(badge_id) ON DELETE CASCADE,
    earned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    context_json JSONB,
    PRIMARY KEY (user_id, badge_id)
);

CREATE INDEX IF NOT EXISTS idx_user_badge_user_id ON social.user_badge (user_id);

-- Seed core initial achievements
INSERT INTO social.badge_definition (badge_id, slug, name, description, criteria_json) VALUES
('018f3a00-0000-7000-8000-000000000001', 'first-watch', 'First Reel', 'Log your first film or episode watch event', '{"type": "watch_count", "threshold": 1}'::jsonb),
('018f3a00-0000-7000-8000-000000000002', 'century-club', 'Century Club', 'Watch and log 100 titles in CineVault', '{"type": "watch_count", "threshold": 100}'::jsonb),
('018f3a00-0000-7000-8000-000000000003', 'seven-day-streak', 'Dedicated Cinephile', 'Maintain a continuous 7-day viewing streak', '{"type": "streak_days", "threshold": 7}'::jsonb),
('018f3a00-0000-7000-8000-000000000004', 'inner-circle', 'Inner Circle', 'Connect with 5 accepted cinephile friends', '{"type": "friend_count", "threshold": 5}'::jsonb),
('018f3a00-0000-7000-8000-000000000005', 'first-review', 'Critic in the Making', 'Publish your first film review or critique', '{"type": "review_count", "threshold": 1}'::jsonb),
('018f3a00-0000-7000-8000-000000000006', 'curator-elite', 'Curator Elite', 'Create your first custom film collection', '{"type": "collection_count", "threshold": 1}'::jsonb)
ON CONFLICT (slug) DO NOTHING;
