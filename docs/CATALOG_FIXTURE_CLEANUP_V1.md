# Catalog Fixture Cleanup (Day 1-7 remediation, Batch 3)

## What happened

The Day 1-7 audit found `canonical.title` holding 51,667+ rows, 98.5% of
which were synthetic fixtures produced by `generate_dynamic_catalog_item()`
in the ingestion adapters (mock mode is the default; no live provider
credentials were ever configured). A separate discovery during this
cleanup found `tests/test_day7_large_scale_catalog_expansion.py` wrote
permanently to the same shared dev database with no teardown, so the
count kept growing on every `pytest` run (51,667 → 56,767 across this
remediation session alone) — see the `fix(tests): isolate Day 7
ingestion tests` commit for that fix.

## Protected set

The 10 baseline titles (`SEED_FALLBACK_TITLES` in
[`services/api/repositories/canonical.py`](../services/api/repositories/canonical.py))
— 9 movies + 1 TV series — plus one additional fixture title
(`00013417-6b24-43c1-93cb-032d475e48cb`, display_id `MOV-007993`) that
real `personal.watch_event` / `personal.user_title_state` rows
reference. See [`scripts/cleanup_fixture_data.py`](../scripts/cleanup_fixture_data.py)
for the exact UUID list and rationale.

Two pre-existing data issues were found and **deliberately left
untouched** by this cleanup (they belong to later remediation batches,
not fixture cleanup):

- **Duplicate Inception** (`MOV-000002` and `MOV-000005`) — dedup is
  Batch 4's job (identity resolution + `identity_redirect`), since it
  requires deciding which row survives and redirecting references, not
  a blind delete.
- **`MOV-007993` is fixture-pattern data with real personal data
  attached** — left in place (the `ON DELETE RESTRICT` FK would block
  deleting it anyway) until Batch 4's merge-safety work can properly
  redirect that personal history to a correct canonical title.
- **Sholay is missing** from the baseline entirely — `SEED_FALLBACK_TITLES`
  defines it as `MOV-000002`, but the Day 1 SQL seed
  (`R__seed_development_taxonomy.sql`) claimed that display_id for
  Inception instead, so Sholay was never inserted. Not fixed here —
  flagging for whoever owns the baseline data going forward.

## What was removed

- 56,756 `canonical.title` rows (and their `edition` rows) — every one
  of them had a `canonical.title_external_id` mapping, confirming 100%
  pipeline origin; verified zero exceptions before deleting.
- All ingestion/quality pipeline history: `ingestion.ingestion_runs`,
  `ingestion.ingestion_items`, `ingestion.raw_payload_capture`,
  `quality.candidate_title`, `quality.field_provenance`,
  `quality.metadata_conflict`, `quality.ai_proposal_staging`. Every row
  in that history came from a mock-mode run — none of it is a record
  of real provider contact.

## Backup

A full `pg_dump` (custom format) was taken and its table of contents
verified before running the cleanup. It is not committed to the repo
(large binary, contains data) — ask whoever ran the cleanup for the
`.dump` file if a restore is ever needed.

## Re-running

`python scripts/cleanup_fixture_data.py` (dry-run, default) or
`--apply` to execute. Idempotent — safe to re-run after a successful
cleanup; it will report zero rows to delete.
