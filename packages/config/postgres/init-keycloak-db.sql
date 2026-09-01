-- CineVault OS — Production Keycloak Database Bootstrap
-- Runs as 02-init-keycloak-db.sql, after 01-init-schemas.sql, only in the
-- production Postgres init sequence (infra/docker/docker-compose.prod.yml).
-- Creates a dedicated `keycloak` database, separate from the application's
-- `cinevault` database/schemas, per Keycloak's own guidance against sharing
-- a database with application data. Idempotent: only runs on first init
-- (docker-entrypoint-initdb.d scripts only execute against an empty data
-- directory) and only creates the database if it doesn't already exist.
SELECT 'CREATE DATABASE keycloak'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'keycloak')\gexec
