-- CineVault OS — Flyway Migration V3.9: Native Authentication User Table
-- Implements Phase 1 Sovereign Native Authentication Architecture (ADR-003, ADR-004)

CREATE SCHEMA IF NOT EXISTS auth;

CREATE TABLE IF NOT EXISTS auth.user (
    user_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    roles TEXT[] NOT NULL DEFAULT '{authenticated_user}',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS idx_auth_user_email ON auth.user (email);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_auth_user_updated_at'
    ) THEN
        CREATE TRIGGER trg_auth_user_updated_at
        BEFORE UPDATE ON auth.user
        FOR EACH ROW
        EXECUTE FUNCTION update_timestamp();
    END IF;
END $$;
