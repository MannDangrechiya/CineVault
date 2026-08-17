-- CineVault OS — Flyway Migration V1.3: Personal Data Isolated Tables (CAT-2)
-- Implements ADR-003, ADR-004, Physical Database Design V1

CREATE TABLE personal.library_entry (
    user_id UUID NOT NULL,
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE RESTRICT,
    added_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    status_override VARCHAR(32),
    PRIMARY KEY (user_id, title_id)
);

CREATE TABLE personal.watch_event (
    watch_event_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    user_id UUID NOT NULL,
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE RESTRICT,
    edition_id UUID REFERENCES canonical.edition(edition_id) ON DELETE RESTRICT,
    season_id UUID REFERENCES canonical.season(season_id) ON DELETE RESTRICT,
    episode_id UUID REFERENCES canonical.episode(episode_id) ON DELETE RESTRICT,
    watched_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    device_type VARCHAR(64),
    notes TEXT,
    is_tombstoned BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE personal.user_title_state (
    user_id UUID NOT NULL,
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE RESTRICT,
    manual_status_override VARCHAR(32),
    is_favorite BOOLEAN NOT NULL DEFAULT false,
    preferred_edition_id UUID REFERENCES canonical.edition(edition_id) ON DELETE SET NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (user_id, title_id)
);

CREATE TABLE personal.rating (
    rating_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    user_id UUID NOT NULL,
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE RESTRICT,
    rating_value SMALLINT NOT NULL CONSTRAINT check_rating CHECK (rating_value >= 1 AND rating_value <= 10),
    rated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT unique_user_title_rating UNIQUE (user_id, title_id)
);

CREATE TABLE personal.note (
    note_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    user_id UUID NOT NULL,
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE RESTRICT,
    note_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE personal.review (
    review_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    user_id UUID NOT NULL,
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE RESTRICT,
    review_title VARCHAR(256),
    review_text TEXT NOT NULL,
    contains_spoilers BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE personal.personal_data_conflict (
    conflict_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    user_id UUID NOT NULL,
    conflict_type VARCHAR(64) NOT NULL,
    surviving_title_id UUID REFERENCES canonical.title(title_id) ON DELETE RESTRICT,
    retired_title_id UUID REFERENCES canonical.title(title_id) ON DELETE RESTRICT,
    conflicting_data JSONB NOT NULL,
    resolution_status VARCHAR(32) NOT NULL DEFAULT 'UNRESOLVED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE personal.user_split_resolution (
    resolution_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    conflict_id UUID NOT NULL REFERENCES personal.personal_data_conflict(conflict_id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    chosen_title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE RESTRICT,
    resolved_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE personal.sync_outbox_mutation (
    mutation_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    user_id UUID NOT NULL,
    mutation_type VARCHAR(64) NOT NULL,
    client_timestamp TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL,
    processing_state VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    processed_at TIMESTAMPTZ,
    CONSTRAINT unique_user_mutation UNIQUE (user_id, mutation_id)
);

CREATE TABLE personal.sync_cursor_state (
    user_id UUID NOT NULL,
    device_id VARCHAR(128) NOT NULL,
    last_synced_mutation_id UUID,
    last_synced_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (user_id, device_id)
);
