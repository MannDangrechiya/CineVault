# ADR-001 — Canonical Identity & Classification

**Status:** Accepted
**Decision Owner:** CineVault Project Owner
**Scope:** Canonical identity, display identity, content classification

## Context

CineVault must maintain stable internal identity independent of external metadata providers and independent of changes to content classification.

External provider identifiers cannot serve as permanent CineVault identity.

## Decision

### Canonical Identity

CineVault uses **UUIDv7 as the permanent canonical identity**.

A canonical UUID:

* is generated internally;
* never changes;
* is never reused;
* is independent of providers;
* is independent of content type;
* is independent of human-readable identifiers.

### Human-Readable Identity

CineVault also uses immutable human-readable identifiers such as:

* `MOV-000001`
* `SER-000001`
* `ANI-000001`

These are secondary identifiers.

They are assigned once and never changed.

The prefix represents the record's classification at creation and is therefore historical.

The current classification is determined exclusively by `content_type`.

### External Identity

External provider IDs are mappings to CineVault entities.

They are never canonical identity.

### Content Type

`content_type` is the authoritative current classification and may change through governed processes.

A classification change must:

1. be validated;
2. check structural compatibility;
3. preserve provenance;
4. preserve personal data;
5. create appropriate audit history;
6. require explicit review when dependent structures could become invalid.

Changing `content_type` must never change the canonical UUID or display ID.

## Consequences

This provides stable identity while allowing metadata correction and reclassification.

Display identifiers remain useful to humans without becoming a second source of truth.

External providers remain replaceable.

## Deferred

The exact display-ID sequence implementation and physical database constraints will be finalized during Data Model design.
