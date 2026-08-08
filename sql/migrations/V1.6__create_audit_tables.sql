-- CineVault OS — Flyway Migration V1.6: Operational Audit & Evidence Lineage Tables (CAT-4)
-- Implements DEC-QUAL-PRP-05, Physical Database Design V1

CREATE TABLE audit.canonical_audit_log (
    audit_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    actor_id UUID,
    action_type VARCHAR(64) NOT NULL,
    target_table VARCHAR(64) NOT NULL,
    target_id UUID NOT NULL,
    previous_state JSONB,
    resulting_state JSONB,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE audit.attribute_evidence_lineage (
    lineage_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    canonical_table VARCHAR(64) NOT NULL,
    canonical_id UUID NOT NULL,
    attribute_name VARCHAR(64) NOT NULL,
    promoted_value TEXT NOT NULL,
    source_provider VARCHAR(64) NOT NULL,
    source_external_id VARCHAR(128) NOT NULL,
    raw_payload_id UUID REFERENCES ingestion.raw_payload_capture(raw_payload_id) ON DELETE SET NULL,
    applied_rule_id VARCHAR(128) NOT NULL,
    confidence_band VARCHAR(32) NOT NULL,
    promoted_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);
