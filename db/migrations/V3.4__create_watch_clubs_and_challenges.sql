-- CineVault OS — V3.4: Watch Clubs, Club Taste DNA, Club Activity Feed, and Monthly Challenges
-- Part 2 Phase 3 (Items 2.10, 2.11, 2.12, 2.13)

-- ─── 2.10  Watch Clubs ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS social.watch_club (
    club_id         UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(200)    NOT NULL,
    slug            VARCHAR(120)    NOT NULL UNIQUE,
    created_by      UUID            NOT NULL,
    avatar_url      TEXT,
    description     TEXT,
    member_count    INTEGER         NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);

CREATE INDEX idx_watch_club_slug     ON social.watch_club (slug);
CREATE INDEX idx_watch_club_created  ON social.watch_club (created_by);

CREATE TABLE IF NOT EXISTS social.club_membership (
    club_id         UUID            NOT NULL REFERENCES social.watch_club(club_id) ON DELETE CASCADE,
    user_id         UUID            NOT NULL,
    role            VARCHAR(32)     NOT NULL DEFAULT 'MEMBER',  -- OWNER, ADMIN, MEMBER
    joined_at       TIMESTAMPTZ     NOT NULL DEFAULT now(),
    PRIMARY KEY (club_id, user_id)
);

CREATE INDEX idx_club_membership_user ON social.club_membership (user_id);

-- ─── 2.11  Club Taste DNA ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS social.club_taste_profile (
    club_id         UUID            PRIMARY KEY REFERENCES social.watch_club(club_id) ON DELETE CASCADE,
    taste_vector    vector(384),
    total_watches   INTEGER         NOT NULL DEFAULT 0,
    top_genres_json JSONB           DEFAULT '[]'::jsonb,
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);

-- ─── 2.12  Club Activity Feed ───────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS social.club_activity (
    activity_id     UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    club_id         UUID            NOT NULL REFERENCES social.watch_club(club_id) ON DELETE CASCADE,
    user_id         UUID            NOT NULL,
    activity_type   VARCHAR(64)     NOT NULL,  -- WATCH, RATING, REVIEW, RECOMMENDATION, JOINED, CHALLENGE_COMPLETE
    reference_id    UUID,
    metadata_json   JSONB           DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);

CREATE INDEX idx_club_activity_club    ON social.club_activity (club_id, created_at DESC);
CREATE INDEX idx_club_activity_user    ON social.club_activity (user_id);

-- ─── 2.13  Monthly Challenges ───────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS social.challenge (
    challenge_id    UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    title           VARCHAR(200)    NOT NULL,
    description     TEXT,
    challenge_type  VARCHAR(64)     NOT NULL DEFAULT 'GLOBAL',  -- GLOBAL, CLUB
    club_id         UUID            REFERENCES social.watch_club(club_id) ON DELETE CASCADE,
    criteria_json   JSONB           NOT NULL DEFAULT '{}'::jsonb,
    goal_count      INTEGER         NOT NULL DEFAULT 1,
    starts_at       TIMESTAMPTZ     NOT NULL,
    ends_at         TIMESTAMPTZ     NOT NULL,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);

CREATE INDEX idx_challenge_dates ON social.challenge (starts_at, ends_at);
CREATE INDEX idx_challenge_club  ON social.challenge (club_id) WHERE club_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS social.challenge_participant (
    challenge_id    UUID            NOT NULL REFERENCES social.challenge(challenge_id) ON DELETE CASCADE,
    user_id         UUID            NOT NULL,
    progress        INTEGER         NOT NULL DEFAULT 0,
    completed       BOOLEAN         NOT NULL DEFAULT FALSE,
    completed_at    TIMESTAMPTZ,
    joined_at       TIMESTAMPTZ     NOT NULL DEFAULT now(),
    PRIMARY KEY (challenge_id, user_id)
);

CREATE INDEX idx_challenge_participant_user ON social.challenge_participant (user_id);
