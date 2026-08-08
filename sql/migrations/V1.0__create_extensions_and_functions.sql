-- CineVault OS — Flyway Migration V1.0: Extensions and Utility Functions
-- Authority: Flyway Community Edition Canonical Schema Evolution

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "citext";

-- UUIDv7 Generation Function
-- Implements ADR-001 time-ordered sequential 128-bit UUID primary keys
CREATE OR REPLACE FUNCTION generate_uuid_v7() RETURNS uuid AS $$
DECLARE
    v_time timestamp with time zone := clock_timestamp();
    v_secs bigint := extract(epoch from v_time);
    v_msec bigint := mod(floor(extract(milliseconds from v_time))::bigint, 1000);
    v_timestamp bigint := (v_secs * 1000) + v_msec;
    v_rand_a int := (random() * 4095)::int;
    v_rand_b bigint := (random() * 4611686018427387903)::bigint;
BEGIN
    RETURN (
        lpad(to_hex(v_timestamp), 12, '0') ||
        '7' || lpad(to_hex(v_rand_a), 3, '0') ||
        to_hex((v_rand_b >> 62) | 8) || lpad(to_hex(v_rand_b & 4611686018427387903), 15, '0')
    )::uuid;
END;
$$ LANGUAGE plpgsql VOLATILE;

-- Automatic updated_at timestamp trigger function
CREATE OR REPLACE FUNCTION update_timestamp() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = clock_timestamp();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
