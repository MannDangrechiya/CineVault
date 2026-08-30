-- CineVault Physical Database Design — Module 3 / Phase 2 & 3 Hardening
-- V3.6: Hardens social schema constraints for pairwise uniqueness, race-safety, and query performance

-- 1. Enforce pairwise uniqueness for friendships (User A <-> User B cannot have duplicate rows in either direction)
CREATE UNIQUE INDEX IF NOT EXISTS uq_friendship_pairwise
ON social.friendship (LEAST(requester_id, addressee_id), GREATEST(requester_id, addressee_id));

-- 2. Performance indexes for social queries and inbox lookups
CREATE INDEX IF NOT EXISTS idx_recommendation_pair ON social.recommendation (sender_id, recipient_id);
CREATE INDEX IF NOT EXISTS idx_pick_vote_candidate ON social.pick_vote (room_id, title_id);
CREATE INDEX IF NOT EXISTS idx_challenge_active ON social.challenge (starts_at, ends_at);
