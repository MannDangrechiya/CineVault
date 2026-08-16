# Phase 25 — Observability
**Goal:** Implement the approved conceptual operations architecture.

## Use
metrics, logs, traces, audit events, security events, business/data signals.

## Trace path
```
API → queue → worker → provider → database
```

## Monitor
API, ingestion, quality, reconciliation, sync, database, providers, queues,
storage, AI operations.

## Constraint
Do not prematurely choose vendors where architecture has intentionally left
them open. The approved observability architecture is vendor-neutral and
explicitly defers infrastructure/vendor choices.
