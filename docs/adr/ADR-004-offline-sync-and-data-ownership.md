# ADR-004 — Offline Sync, Conflict Resolution & Data Ownership

**Status:** Accepted
**Decision Owner:** CineVault Project Owner
**Scope:** Offline-first synchronization, conflict handling, privacy and ownership

## Offline Synchronization

The Flutter client will support durable offline mutations.

Conceptually:

```text
Flutter Local Database
        ↓
Durable Outbox
        ↓
Mutation ID
        ↓
Server
        ↓
Idempotency Check
        ↓
Domain Processing
        ↓
Conflict Resolution
```

State-changing mutations receive stable client-generated identifiers so retrying the same operation does not create duplicate effects.

A mutation represents a state-changing operation, not every client interaction.

## Conflict Resolution

Conflict resolution is data-specific.

Last-write-wins is permitted only for explicitly designated low-risk state.

It must not be used blindly for:

* Watch Events;
* Ratings;
* Reviews;
* Notes;
* canonical metadata;
* merge decisions;
* personal-data deletion.

Append-only events should generally be reconciled as events rather than overwritten.

Meaningful singleton conflicts must preserve conflicting values until safely resolved.

## Duplicate Watch Events

The system must not automatically delete Watch Events solely because they occur close together in time.

Potential duplicates may be flagged or reconciled through controlled logic.

No simplistic time-window heuristic may become an unconditional deletion rule.

## Data Ownership Classes

CineVault distinguishes:

1. Canonical platform data
2. User-owned personal data
3. Derived data
4. Operational/audit data
5. External-source data
6. AI-generated proposals

Each category has different modification, deletion and reconstruction rules.

## AI-Generated Data

AI-generated information is not automatically canonical.

It remains a proposal until validated according to CineVault's governance process.

## Privacy

User-owned personal data must be exportable and deletable.

Operational/audit records may retain appropriately redacted information necessary for system integrity and operational accountability.

Audit records must not become a permanent copy of deleted substantive personal content.

Backup retention and deletion behavior will be governed by a later explicit retention policy.

## Data Integrity Responsibility

### PostgreSQL

Structural integrity:

* foreign keys;
* uniqueness;
* required values;
* structural checks.

### Application / Domain Layer

Business rules:

* merge;
* split;
* classification;
* permissions;
* semantic conflict resolution.

### Ingestion

Data quality:

* normalization;
* source validation;
* provenance;
* duplicate detection;
* source conflicts.

### Human Review

Ambiguous/high-impact decisions.

## Consequences

CineVault can support multiple offline devices without treating one device as permanently authoritative.

User-owned data remains recoverable, exportable and protected from silent loss.

The architecture avoids applying one generic conflict algorithm to fundamentally different data types.

## Deferred

Exact outbox schema, mutation schema, synchronization protocol, conflict-record schema, deletion-retention periods and backup policies will be finalized in later architecture/data-model reviews.
