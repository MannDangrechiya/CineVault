-- CineVault OS — Flyway Migration V2.0: Day 4 Ingestion Pipeline & Field Provenance Tables
-- Implements Ingestion Architecture Day 4: Ingestion Runs, Items, Candidate Staging & Field Provenance

CREATE TABLE IF NOT EXISTS ingestion.ingestion_runs (
    run_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    provider_name VARCHAR(64) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    completed_at TIMESTAMPTZ,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    records_seen INT NOT NULL DEFAULT 0,
    records_valid INT NOT NULL DEFAULT 0,
    records_rejected INT NOT NULL DEFAULT 0,
    records_created INT NOT NULL DEFAULT 0,
    records_updated INT NOT NULL DEFAULT 0,
    records_conflicted INT NOT NULL DEFAULT 0,
    error_count INT NOT NULL DEFAULT 0,
    dry_run BOOLEAN NOT NULL DEFAULT FALSE,
    summary_notes JSONB
);

CREATE TABLE IF NOT EXISTS ingestion.ingestion_items (
    item_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    ingestion_run_id UUID NOT NULL REFERENCES ingestion.ingestion_runs(run_id) ON DELETE CASCADE,
    external_id VARCHAR(128) NOT NULL,
    raw_record_id UUID REFERENCES ingestion.raw_payload_capture(raw_payload_id) ON DELETE SET NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'RECEIVED',
    candidate_title_id UUID,
    error_details JSONB,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE IF NOT EXISTS quality.candidate_title (
    candidate_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    ingestion_run_id UUID REFERENCES ingestion.ingestion_runs(run_id) ON DELETE SET NULL,
    provider_name VARCHAR(64) NOT NULL,
    external_id VARCHAR(128) NOT NULL,
    candidate_payload JSONB NOT NULL,
    match_status VARCHAR(32) NOT NULL DEFAULT 'NO_MATCH',
    matched_canonical_title_id UUID REFERENCES canonical.title(title_id) ON DELETE SET NULL,
    match_score NUMERIC(4,3) NOT NULL DEFAULT 0.000,
    match_rule_id VARCHAR(128),
    review_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE IF NOT EXISTS quality.field_provenance (
    provenance_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    entity_type VARCHAR(64) NOT NULL DEFAULT 'TITLE',
    entity_id UUID NOT NULL,
    field_name VARCHAR(64) NOT NULL,
    field_value TEXT NOT NULL,
    source_provider VARCHAR(64) NOT NULL,
    external_id VARCHAR(128),
    confidence VARCHAR(32) NOT NULL DEFAULT 'UNKNOWN',
    verification_status VARCHAR(32) NOT NULL DEFAULT 'UNVERIFIED',
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS idx_ingestion_runs_status ON ingestion.ingestion_runs(status);
CREATE INDEX IF NOT EXISTS idx_ingestion_items_run_id ON ingestion.ingestion_items(ingestion_run_id);
CREATE INDEX IF NOT EXISTS idx_ingestion_items_external_id ON ingestion.ingestion_items(external_id);
CREATE INDEX IF NOT EXISTS idx_candidate_title_external_id ON quality.candidate_title(provider_name, external_id);
CREATE INDEX IF NOT EXISTS idx_candidate_title_matched ON quality.candidate_title(matched_canonical_title_id);
CREATE INDEX IF NOT EXISTS idx_field_provenance_entity ON quality.field_provenance(entity_type, entity_id);
