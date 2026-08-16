# Phase 8 — Streaming Availability
**Goal:** Temporal and regional availability.

## Model
provider, country/region, offer type, price if legally available, currency,
valid_from, valid_until, last_verified, source, confidence.

## Support
subscription, rent, buy, free, ad-supported (where applicable).

## Constraint
Never claim availability without current source evidence. Availability is
temporal — an old record must not be presented as current without verification.
