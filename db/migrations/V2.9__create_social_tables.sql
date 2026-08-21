-- CineVault OS — Flyway Migration V2.9: Social Schema Tables (ADR-003, ADR-004)
-- Mirrors services/api/models/social.py 1:1 (FriendshipModel, RecommendationModel,
-- UserTasteProfileModel). This schema was never migrated even though the ORM
-- models, repository, and router code for it have existed since — every
-- social_repository DB call has only ever run against the in-memory seed
-- fallback until now. See PLAN.md 1.4 for the discovery.

CREATE SCHEMA IF NOT EXISTS social;

CREATE TABLE social.friendship (
    friendship_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    requester_id UUID NOT NULL,
    addressee_id UUID NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING', -- PENDING, ACCEPTED, BLOCKED
    trust_score DOUBLE PRECISION NOT NULL DEFAULT 50.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX idx_friendship_requester_id ON social.friendship (requester_id);
CREATE INDEX idx_friendship_addressee_id ON social.friendship (addressee_id);

CREATE TABLE social.recommendation (
    recommendation_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    sender_id UUID NOT NULL,
    recipient_id UUID NOT NULL,
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE RESTRICT,
    status VARCHAR(32) NOT NULL DEFAULT 'SENT', -- SENT, ACCEPTED, REJECTED, WATCHED, RATED
    sender_predicted_rating DOUBLE PRECISION,
    recipient_actual_rating DOUBLE PRECISION,
    context_note TEXT,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX idx_recommendation_sender_id ON social.recommendation (sender_id);
CREATE INDEX idx_recommendation_recipient_id ON social.recommendation (recipient_id);
CREATE INDEX idx_recommendation_title_id ON social.recommendation (title_id);

-- 384-dim dense taste vector (all-MiniLM-L6-v2 compatible), pgvector extension
-- enabled by V2.8. No ANN index (ivfflat/hnsw) yet — full-scan cosine distance
-- is fine at current friend-list scale; add one if/when that stops being true.
CREATE TABLE social.user_taste_profile (
    user_id UUID PRIMARY KEY,
    taste_vector vector(384),
    last_computed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);
