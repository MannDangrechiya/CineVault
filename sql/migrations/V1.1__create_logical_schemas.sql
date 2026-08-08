-- CineVault OS — Flyway Migration V1.1: Logical PostgreSQL Schemas
-- Implements DEC-PHYS-PRP-01 5-schema partitioning

CREATE SCHEMA IF NOT EXISTS canonical;
CREATE SCHEMA IF NOT EXISTS personal;
CREATE SCHEMA IF NOT EXISTS ingestion;
CREATE SCHEMA IF NOT EXISTS quality;
CREATE SCHEMA IF NOT EXISTS audit;
