-- CineVault OS — Local PostgreSQL Container Bootstrap Script
-- BOUNDARY SPECIFICATION: Container startup bootstrap ONLY.
-- DDL migration authority belongs strictly to Flyway Community Edition (sql/migrations/).
-- This file MUST NOT contain table definitions or compete with Flyway migration history.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "citext";
CREATE EXTENSION IF NOT EXISTS vector;
