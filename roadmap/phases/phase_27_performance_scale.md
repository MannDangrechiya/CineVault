# Phase 27 — Performance / Scale
**Goal:** Benchmark and optimize based on evidence.

## Benchmark tiers (where practical)
5,000 → 10,000 → 100,000 → 1,000,000+

## Measure
catalog search, title lookup, filtering, pagination, ingestion, identity
matching, database writes, API latency, recommendation queries, analytics.

## Constraint
Optimize based on measurements. Do not prematurely introduce Elasticsearch,
OpenSearch, a distributed database, or microservices unless evidence requires
them. PostgreSQL remains the canonical database foundation.
