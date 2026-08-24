-- CineVault Physical Database Design — Module 3 / Phase 1
-- V3.0: Creates personal.user_streak table for tracking daily viewing streaks

CREATE TABLE IF NOT EXISTS personal.user_streak (
    user_id UUID PRIMARY KEY,
    current_streak INT NOT NULL DEFAULT 0,
    longest_streak INT NOT NULL DEFAULT 0,
    last_watch_date DATE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_streak_user_id ON personal.user_streak (user_id);
