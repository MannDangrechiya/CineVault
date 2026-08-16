# Phase 19 — Offline Sync
**Goal:** Robust synchronization.

## Must define
```
local change → sync queue → server → conflict detection → merge → acknowledgement
```

## Handle
same record edited offline on two devices, duplicate events, out-of-order
events, retry, network loss, partial sync, deleted records, identity changes.

## Constraint
Never silently lose personal history. Document the concrete merge algorithm.
Test offline scenarios extensively.
