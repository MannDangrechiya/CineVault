# Phase 6 — Watch History Engine
**Goal:** Proper watch-event architecture.

## Support
started, paused, resumed, completed, stopped, rewatched, watch date/time,
duration, episode progress.

## Hierarchies
```
TV:     series → season → episode → watch events
Movie:  title → watch events
```

## Constraints
Avoid duplicate watch events where idempotency is required.
Preserve history when canonical metadata changes.
