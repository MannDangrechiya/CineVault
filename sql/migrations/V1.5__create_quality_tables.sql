-- CineVault OS — Flyway Migration V1.5: Data Quality & Quarantine Tables (CAT-6)
-- Implements DEC-QUAL-PRP-06, DEC-QUAL-DEF-01, ADR-004 AI Proposal Boundary

CREATE TABLE quality.quarantine_record (
    quarantine_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    raw_payload_id UUID REFERENCES ingestion.raw_payload_capture(raw_payload_id) ON DELETE SET NULL,
    provider_name VARCHAR(64) NOT NULL,
    failure_category VARCHAR(64) NOT NULL,
    diagnostic_details JSONB NOT NULL,
    review_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    detected_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE quality.normalized_title_staging (
    staging_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    raw_payload_id UUID REFERENCES ingestion.raw_payload_capture(raw_payload_id) ON DELETE CASCADE,
    normalized_payload JSONB NOT NULL,
    normalization_status VARCHAR(32) NOT NULL DEFAULT 'NORMALIZED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

-- AI Proposal Staging (ADR-004 CAT-6 Boundary: Zero direct write access to canonical)
CREATE TABLE quality.ai_proposal_staging (
    proposal_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    target_entity_type VARCHAR(64) NOT NULL,
    target_entity_id UUID,
    proposed_attribute_name VARCHAR(64) NOT NULL,
    proposed_value TEXT NOT NULL,
    confidence_score NUMERIC(4,3) NOT NULL,
    evidence_payload JSONB NOT NULL,
    review_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE quality.reconciliation_candidate (
    candidate_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    provider_name VARCHAR(64) NOT NULL,
    external_id VARCHAR(128) NOT NULL,
    candidate_title_id UUID REFERENCES canonical.title(title_id) ON DELETE CASCADE,
    match_confidence NUMERIC(4,3) NOT NULL,
    match_rule_id VARCHAR(128) NOT NULL,
    decision_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);
