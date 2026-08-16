# Phase 1 — Canonical Data Foundation
**Goal:** Make the entertainment catalog structurally complete and trustworthy.

## Implement/verify
Title, aliases, original titles, languages, countries, genres, themes, keywords,
people, characters, credits, studios, networks, distributors, production companies,
certifications, franchises, universes, awards, festivals, external IDs, editions,
releases, seasons, episodes.

## Verify these hierarchies are real relationships, not empty schema
```
Title → Season → Episode
Title → Edition → Release
```
Do not confuse Edition with Season.

## Gate
Representative movie, representative TV series, representative anime, and
representative documentary must all work correctly.
