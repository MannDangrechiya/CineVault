# ADR-002 — Title / Edition / Release Domain Model

**Status:** Accepted
**Decision Owner:** CineVault Project Owner
**Scope:** Entertainment-domain hierarchy

## Decision

CineVault adopts:

```text
Title
  ↓
Edition
  ↓
Release
```

### Title

Represents the abstract creative work.

### Edition

Represents a materially distinct version of the content.

Examples:

* theatrical cut;
* director's cut;
* extended cut;
* international cut;
* censored/uncensored version;
* materially different alternate cut.

Every Title conceptually has one Primary Edition.

Additional Editions are created only when the actual content materially differs.

### Release

Represents a real-world distribution event for an Edition.

Examples:

* festival;
* theatrical;
* television;
* streaming;
* digital purchase;
* digital rental;
* physical;
* re-release.

One Edition may have many Releases.

## Core Rule

```text
Material content difference → Edition
Distribution difference → Release
```

A streaming or physical release of the same content does not automatically create a new Edition.

A restoration/remaster does not automatically create an Edition unless it represents materially distinct content.

## Episodic Content

The episodic hierarchy remains:

```text
Title
  ↓
Season
  ↓
Episode
```

Episode identity is independent of human-facing episode numbering.

Regional ordering and alternate episode-version modeling remain deferred.

## Franchise / Universe

Franchise and Universe are separate concepts.

A Franchise may optionally belong to a Universe.

A Title may participate in multiple franchise relationships.

## Viewing Orders

Franchise viewing orders use an extensible conceptual model:

```text
Franchise Entry
+
Order Type
+
Position
```

rather than hard-coded order columns.

## Consequences

The model handles simple titles without forcing unnecessary complexity while supporting alternate cuts, versions and multiple distribution events.

The Edition layer may be hidden from users when only the Primary Edition exists.

## Deferred

Exact PostgreSQL entities, keys, constraints, episode-version modeling, regional ordering and continuity modeling will be finalized during the Data Model/ERD phase.
