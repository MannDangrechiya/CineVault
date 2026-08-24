-- CineVault Physical Database Design — Module 3 / Phase 2
-- V3.3: Creates social.pick_room, social.pick_room_candidate, and social.pick_vote tables for shareable group ballots

CREATE TABLE IF NOT EXISTS social.pick_room (
    room_id UUID PRIMARY KEY,
    host_id UUID NOT NULL,
    slug VARCHAR(64) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL DEFAULT 'Movie Night Ballot',
    constraints_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(32) NOT NULL DEFAULT 'OPEN', -- OPEN, CLOSED, RESOLVED
    winning_title_id UUID REFERENCES canonical.title(title_id) ON DELETE SET NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pick_room_host_id ON social.pick_room (host_id);
CREATE INDEX IF NOT EXISTS idx_pick_room_slug ON social.pick_room (slug);

CREATE TABLE IF NOT EXISTS social.pick_room_candidate (
    room_id UUID NOT NULL REFERENCES social.pick_room(room_id) ON DELETE CASCADE,
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE CASCADE,
    PRIMARY KEY (room_id, title_id)
);

CREATE TABLE IF NOT EXISTS social.pick_vote (
    vote_id UUID PRIMARY KEY,
    room_id UUID NOT NULL REFERENCES social.pick_room(room_id) ON DELETE CASCADE,
    user_id UUID,
    guest_name VARCHAR(128),
    voter_fingerprint VARCHAR(64) NOT NULL,
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE CASCADE,
    vote_type VARCHAR(16) NOT NULL DEFAULT 'UPVOTE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_pick_vote_voter_candidate UNIQUE (room_id, voter_fingerprint, title_id)
);

CREATE INDEX IF NOT EXISTS idx_pick_vote_room_id ON social.pick_vote (room_id);

