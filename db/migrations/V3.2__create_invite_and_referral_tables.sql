-- CineVault Physical Database Design — Module 3 / Phase 2
-- V3.2: Creates social.invite_token and social.referral tables for taste preview viral loops and referral rewards

CREATE TABLE IF NOT EXISTS social.invite_token (
    token VARCHAR(64) PRIMARY KEY,
    inviter_id UUID NOT NULL,
    preview_data_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    expires_at TIMESTAMPTZ,
    converted_user_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_invite_token_inviter_id ON social.invite_token (inviter_id);

CREATE TABLE IF NOT EXISTS social.referral (
    referral_id UUID PRIMARY KEY,
    inviter_id UUID NOT NULL,
    invitee_id UUID NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    milestone_reached_at TIMESTAMPTZ,
    reward_issued BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_referral_inviter_id ON social.referral (inviter_id);
CREATE INDEX IF NOT EXISTS idx_referral_invitee_id ON social.referral (invitee_id);
