-- CineVault OS — Migration V2.5: User Custom Lists & Collections (CAT-2)
-- Enables personal custom collections, ordered lists, and notes

CREATE TABLE IF NOT EXISTS personal.user_list (
    list_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    title VARCHAR(256) NOT NULL,
    description TEXT,
    is_private BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS idx_user_list_user_id ON personal.user_list(user_id);

CREATE TABLE IF NOT EXISTS personal.user_list_item (
    item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    list_id UUID NOT NULL REFERENCES personal.user_list(list_id) ON DELETE CASCADE,
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE RESTRICT,
    position INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    added_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT uq_user_list_item UNIQUE (list_id, title_id)
);

CREATE INDEX IF NOT EXISTS idx_user_list_item_list_pos ON personal.user_list_item(list_id, position);
