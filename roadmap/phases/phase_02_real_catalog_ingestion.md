# Phase 2 — Real Catalog Ingestion
**Goal:** Build a trustworthy real-world catalog.

Start with ONE approved provider. Never begin with thousands.

## Sequence (each stage gated on the last)
100 real → 500 real → 1,000 real → 5,000+ → larger scale

Every stage requires: dry run, quality check, identity resolution, conflict
detection, controlled apply, idempotency, provenance, regression.

Never fabricate records to reach a number. Catalog quality > row count.

## Provider data must retain
provider, external ID, retrieval time, provenance, confidence, source status
