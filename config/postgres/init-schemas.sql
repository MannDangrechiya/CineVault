-- CineVault OS — Local PostgreSQL Schema Initialization Script
-- Executed automatically on local postgres container startup

CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS catalog;
CREATE SCHEMA IF NOT EXISTS ingestion;
CREATE SCHEMA IF NOT EXISTS quality;
CREATE SCHEMA IF NOT EXISTS personal;

-- Basic status check table in ingestion schema
CREATE TABLE IF NOT EXISTS ingestion.local_dev_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    initialized_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    status TEXT NOT NULL DEFAULT 'READY'
);

INSERT INTO ingestion.local_dev_status (status) VALUES ('LOCAL_DATABASE_INITIALIZED');
