-- CineVault OS — Flyway Migration V1.7: Performance Indexes and Partial Unique Constraints
-- Implements DEC-PHYS-PRP-09, Section 24 & 25 Indexing and Constraint Strategy

-- 1. Partial Unique Index enforcing exactly ONE Primary Edition per Title
CREATE UNIQUE INDEX unique_primary_edition ON canonical.edition (title_id) WHERE (is_primary = true);

-- 2. GIN Trigram Search Index for case-insensitive title search
CREATE INDEX idx_title_canonical_trgm ON canonical.title USING gin (canonical_title gin_trgm_ops);
CREATE INDEX idx_person_canonical_trgm ON canonical.person USING gin (canonical_name gin_trgm_ops);

-- 3. GIN Index for JSONB Raw Payload Key Lookups
CREATE INDEX idx_raw_payload_jsonb ON ingestion.raw_payload_capture USING gin (raw_payload jsonb_path_ops);

-- 4. B-Tree Indexes for External Provider Lookups
CREATE INDEX idx_title_ext_lookup ON canonical.title_external_id (provider_name, external_id);
CREATE INDEX idx_person_ext_lookup ON canonical.person_external_id (provider_name, external_id);

-- 5. B-Tree Index for Personal Watch Event Log
CREATE INDEX idx_user_watch_events ON personal.watch_event (user_id, watched_at DESC);

-- 6. Partial Indexes for Pending Quarantine and AI Proposal Queues
CREATE INDEX idx_pending_quarantine ON quality.quarantine_record (review_status) WHERE (review_status = 'PENDING');
CREATE INDEX idx_pending_ai_proposals ON quality.ai_proposal_staging (review_status) WHERE (review_status = 'PENDING');
CREATE INDEX idx_pending_reconciliation ON quality.reconciliation_candidate (decision_status) WHERE (decision_status = 'PENDING');

-- 7. B-Tree Index for Credit & Billing Lookups
CREATE INDEX idx_credit_title_lookup ON canonical.credit (title_id, credit_role_id);
CREATE INDEX idx_credit_person_lookup ON canonical.credit (person_id);

-- 8. B-Tree Index for Audit Log Lookups
CREATE INDEX idx_audit_target_lookup ON audit.canonical_audit_log (target_table, target_id);
CREATE INDEX idx_audit_recorded_at ON audit.canonical_audit_log (recorded_at DESC);
