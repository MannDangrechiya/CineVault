-- CineVault OS — Flyway Migration V2.1: Day 5 Metadata Conflict & Reconciliation Tables
-- Implements Day 5 Data Quality Architecture: Conflict Tracking, Resolution Lifecycle & Candidate Quality

CREATE TABLE IF NOT EXISTS quality.metadata_conflict (
    conflict_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    entity_type VARCHAR(64) NOT NULL DEFAULT 'TITLE',
    entity_id UUID,
    field_name VARCHAR(64) NOT NULL,
    candidate_value TEXT NOT NULL,
    existing_value TEXT,
    source_provider VARCHAR(64) NOT NULL,
    confidence VARCHAR(32) NOT NULL DEFAULT 'CONFLICT',
    status VARCHAR(32) NOT NULL DEFAULT 'OPEN',
    resolution_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    resolved_at TIMESTAMPTZ,
    resolved_by VARCHAR(128)
);

CREATE INDEX IF NOT EXISTS idx_metadata_conflict_status ON quality.metadata_conflict(status);
CREATE INDEX IF NOT EXISTS idx_metadata_conflict_entity ON quality.metadata_conflict(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_metadata_conflict_provider ON quality.metadata_conflict(source_provider);
