# Handoff — CineVault Stabilization Work

Session ended due to a laptop shutdown, mid-way through closing out Part 1.
Read [PLAN.md](PLAN.md) first — it now has the full regression-run results
and root-cause breakdown under 1.6. This file only covers what PLAN.md
doesn't: environment quirks hit *this* session.

## Docker Desktop gotcha #2: stale `dockerInference` socket file

Beyond the "engine takes 30-90s to come up" issue from before, this session
hit a harder failure: Docker Desktop's backend crashed on startup with:

```
starting services: initializing Inference manager: listening on
unix://C:/Users/dipak/AppData/Local/Docker/run/dockerInference: remove
C:/Users/dipak/AppData/Local/Docker/run/dockerInference: The file cannot be
accessed by the system.
```

A stale Unix-socket file (marked as a Windows reparse point) survives an
unclean shutdown and blocks the backend from ever starting — it sits at an
error dialog ("Quit" / "Reset to factory defaults") instead of retrying.
Every deletion method that operates on the file directly fails identically
(`File.Delete`, `Remove-Item`, `fsutil reparsepoint delete`, even after
`wsl --shutdown`) — the fix that actually worked was deleting the entire
`C:\Users\dipak\AppData\Local\Docker\run` folder (not just the one file),
then relaunching Docker Desktop. If this recurs, go straight to deleting
that folder rather than fighting the individual file.

Separately, even after Docker Desktop itself is healthy, the
`cinevault-local-postgres` container can still exit (255) once shortly
after a fresh `docker compose up` — recreating it
(`docker compose -f infra/docker/docker-compose.yml up -d postgres`) fixed
it immediately and it stayed healthy for the full ~70+ minute session after
that. Treat one early crash-and-recreate as normal; only worry if it keeps
happening after a recreate.

## Full regression suite timing — plan for ~60 minutes, not ~20

The 478-test suite took **3650s (~61 min)** end-to-end against live
Postgres, not the ~15-20 min a naive per-test extrapolation suggests. A
handful of individual tests (`test_stage_5000_*`, `test_stage_1000_*` style
large-scale catalog/batch tests) each take 5-30+ minutes alone. Two
practical notes for next time:
- **Don't pipe through `tail`** — `python -m pytest tests/ -q 2>&1 | tail
  -100` buffers everything and shows zero output until the whole run
  finishes, so a genuinely-still-working run is indistinguishable from a
  hung one. Use `python -u -m pytest tests/ -v --tb=short` (unbuffered,
  verbose, no pipe) run in the background instead, so progress is visible
  live via the harness output file as it streams.
- Budget the full hour before starting if you need the complete result in
  one sitting.

## What's next

Go to [PLAN.md](PLAN.md)'s 1.6 section — it has the complete failure list
(26/478), grouped by root cause, with specific file/line pointers and
suggested fixes for each group. Highest-value single fix: `TitleModel` in
`services/api/models/canonical.py` is missing the `status_flag` mapped
column that already exists in the live DB schema — that one gap explains
12 of the 26 failures plus at least one likely silent data-loss bug in
`services/api/quality/reconciliation.py`'s title-merge retire step.
