# ADR-003 — Personal Data & Watch History

**Status:** Accepted
**Decision Owner:** CineVault Project Owner
**Scope:** User-owned entertainment data

## Core Principle

CineVault distinguishes between:

```text
Historical Events
Current State
Derived State
```

These must not be treated as interchangeable.

## Library

Library membership is primarily **Title-scoped**.

A Library Entry may optionally contain a preferred Edition.

Preferred Edition is a user preference and does not change canonical identity.

## Watch Events

Watch Events are append-only historical records.

A Watch Event represents a user's historical viewing activity.

The Watch Event is associated with a Title and may additionally reference:

* Edition;
* Season;
* Episode;
* timing information;
* device/source information;
* other validated contextual information.

An absent Edition means the Edition is unknown. It does not automatically mean Primary Edition.

## Corrections

Watch Events are not silently rewritten.

Corrections use a historical-preserving approach such as:

```text
Original Event
    ↓
Tombstone / correction
    ↓
Corrected Event
```

## Rewatch

Rewatch history is represented through multiple Watch Events.

Rewatch count is derived rather than authoritative stored state.

## Progress

Progress is a derived/cached read model.

Conceptually:

```text
Watch Events
     ↓
Progress calculation
     ↓
Cached progress
```

Progress is not an independent authoritative source of truth.

## Ratings

Ratings are Title-scoped by default.

Conflicting personal values must never be silently merged, averaged, or discarded.

Example:

```text
Title A → 7/10
Title B → 9/10
```

must remain unresolved until an explicit conflict-resolution process determines the appropriate result.

## Notes and Reviews

Notes and Reviews are distinct concepts.

### Notes

Personal/private by default.

### Reviews

Potentially publishable and therefore have different privacy semantics.

## Favorites

Favorite is current state rather than an authoritative historical event.

## Status

Status uses a conceptual separation between:

* derived status;
* manual status override.

Exact state transitions remain deferred.

## Merge / Split

Canonical metadata operations must never silently destroy personal data.

During a merge:

* historical watch events may be reassociated where safe;
* conflicting singleton values must be preserved;
* ambiguous personal data must require explicit resolution.

During a split:

* metadata may be reassigned through controlled processes;
* ambiguous personal data must not be automatically duplicated or guessed.

## Consequences

Personal data remains protected even when canonical metadata changes.

Historical events remain auditable and reconstructable.

Derived values can be rebuilt when necessary.

## Deferred

The exact schemas and algorithms for ratings, status, progress, conflict records, episode tracking and merge/split resolution will be finalized during subsequent Data Model reviews.
