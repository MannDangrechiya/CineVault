-- CineVault OS — V3.5: Add AI Proposal Provenance Columns
-- Fixes a confirmed defect found 2026-08-29: services/api/repositories/ai_assistant.py's
-- stage_ai_proposal has always tried to write provider_name, prompt_version,
-- and submitted_by onto quality.ai_proposal_staging, but the original
-- V1.5__create_quality_tables.sql table never had these columns -- every
-- real INSERT has always failed with a SQLAlchemy TypeError, silently
-- swallowed by the repository's allow_seed_fallback exception handler, so
-- no AI proposal has ever actually been persisted to a real database.
--
-- Additive, non-destructive: three new nullable columns on an existing
-- table, no data loss risk. AI proposals must remain distinguishable from
-- verified canonical data and retain provenance of which AI provider/
-- prompt version produced them and who/what submitted them.

ALTER TABLE quality.ai_proposal_staging
    ADD COLUMN IF NOT EXISTS provider_name VARCHAR(64),
    ADD COLUMN IF NOT EXISTS prompt_version VARCHAR(32),
    ADD COLUMN IF NOT EXISTS submitted_by VARCHAR(128);
