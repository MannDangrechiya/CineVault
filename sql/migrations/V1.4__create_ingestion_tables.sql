-- CineVault OS — Flyway Migration V1.4: Ingestion Raw Staging Tables (CAT-5)
-- Implements DEC-ING-PRP-02, DEC-ING-DEF-01, Physical Database Design V1

CREATE TABLE ingestion.raw_payload_capture (
    raw_payload_id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    provider_name VARCHAR(64) NOT NULL,
    external_entity_type VARCHAR(64) NOT NULL,
    external_entity_id VARCHAR(128) NOT NULL,
    payload_checksum VARCHAR(64) NOT NULL,
    raw_payload JSONB NOT NULL,
    http_status_code SMALLINT,
    acquired_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    ingestion_run_id UUID NOT NULL
);

CREATE TABLE ingestion.provider_checkpoint (
    provider_name VARCHAR(64) PRIMARY KEY,
    last_successful_sync_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    last_processed_cursor VARCHAR(256),
    status_flag VARCHAR(32) NOT NULL DEFAULT 'HEALTHY'
);
