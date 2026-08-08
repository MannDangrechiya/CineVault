-- CineVault OS — Flyway Migration V1.8: Database Roles & Schema Least-Privilege Permissions
-- Implements DEC-PHYS-PRP-08 Security & Role Isolation Model

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'cinevault_app') THEN
        CREATE ROLE cinevault_app NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'cinevault_ingest') THEN
        CREATE ROLE cinevault_ingest NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'cinevault_admin') THEN
        CREATE ROLE cinevault_admin NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'cinevault_analytics') THEN
        CREATE ROLE cinevault_analytics NOLOGIN;
    END IF;
END
$$;

-- Grant Schema USAGE
GRANT USAGE ON SCHEMA canonical TO cinevault_app, cinevault_admin, cinevault_analytics;
GRANT USAGE ON SCHEMA personal TO cinevault_app, cinevault_admin;
GRANT USAGE ON SCHEMA ingestion TO cinevault_ingest, cinevault_admin;
GRANT USAGE ON SCHEMA quality TO cinevault_ingest, cinevault_admin;
GRANT USAGE ON SCHEMA audit TO cinevault_admin;

-- 1. cinevault_app: Read canonical, Read/Write personal
GRANT SELECT ON ALL TABLES IN SCHEMA canonical TO cinevault_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA personal TO cinevault_app;

-- 2. cinevault_ingest: Write ingestion, Read/Write quality (ZERO write to canonical or personal)
GRANT INSERT ON ALL TABLES IN SCHEMA ingestion TO cinevault_ingest;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA quality TO cinevault_ingest;

-- 3. cinevault_admin: Full admin access across canonical, quality, audit
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA canonical TO cinevault_admin;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA quality TO cinevault_admin;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA audit TO cinevault_admin;

-- 4. cinevault_analytics: Read-only canonical catalog (ZERO access to personal)
GRANT SELECT ON ALL TABLES IN SCHEMA canonical TO cinevault_analytics;
