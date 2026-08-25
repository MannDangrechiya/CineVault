# Handoff — CineVault Stabilization + Social Layer + Flutter Parity

**Last updated:** 2026-08-25, after regression re-run and Part 3 planning.

Read [PLAN.md](PLAN.md) for the full task breakdown and status. This file
covers session-end state, environment notes, and what's next.

---

## Current state summary

| Area | Status |
|------|--------|
| Part 1 (stabilization, 1.1–1.6) | ✅ Done — **514/514 pass (100%)** |
| Part 2 (social layer, 2.1–2.13) | ✅ Done — all 3 phases delivered |
| Root Cause D fix (`display_id` collision) | ✅ Fixed and confirmed — 4/4 pass |
| Part 3 (Flutter mobile parity) | 📋 Planned — see PLAN.md Part 3 |
| TypeScript build | ✅ Clean |
| Security findings | ✅ All closed |

---

## Regression baseline — 514/514 pass (100%) ✅

```
2026-08-25 full suite:  514 tests, 510 passed, 4 failed (~57 min)
2026-08-25 Root Cause D confirmation: 4/4 passed (~63 min)
Combined:  514/514 pass — zero known failures
```

All original 26 failures (Root Causes A, B, C) plus the 4 Root Cause D
`display_id` collision failures are resolved. See PLAN.md 1.6 for
per-root-cause details.

---

## What's next — Part 3: Flutter Mobile Feature Parity

The Flutter mobile app (`apps/mobile/`, 10 screens, 48 Dart files) has
**none of the Part 2 social features** and is missing several core
personal features that the web app has. All backend APIs are built — this
is purely Flutter UI + data layer work.

### Feature gap (web → mobile)

| Feature | Web | Mobile |
|---------|-----|--------|
| Social hub (friends, recs, taste matches) | ✅ | ❌ |
| Dashboard badges + recap | ✅ | ❌ |
| Watch history | ✅ | ❌ |
| Watchlist | ✅ | ❌ |
| Collections | ✅ | ❌ |
| Invite flow + referrals | ✅ | ❌ |
| Group pick rooms | ✅ | ❌ |
| Clubs + challenges | ✅ | ❌ |
| Import wizard | ✅ | ❌ |
| Streaks + leaderboard | ✅ | ❌ |

### Execution order (from PLAN.md Part 3)

1. **3.1** — Social API data layer (unblocks everything)
2. **3.4** — Watch history + watchlist (core personal, high usage)
3. **3.5** — Collections
4. **3.2** — Social hub (biggest screen)
5. **3.3** — Dashboard enhancements (streaks, badges, recap)
6. **3.6 → 3.7 → 3.8** — Invite, pick rooms, clubs
7. **3.9** — Import wizard (least mobile-critical)

### Flutter app architecture (for reference)

```
apps/mobile/lib/
├── app.dart                     # App entry + routing
├── main.dart                    # Bootstrap
├── core/                        # Config, theme, constants
├── data/
│   ├── local/                   # SQLite/Hive local storage
│   ├── remote/                  # API datasources (8 files)
│   └── repositories/            # Repository implementations
├── domain/
│   ├── entities/                # Domain models (7 files)
│   └── repositories/            # Repository interfaces
└── presentation/
    ├── providers/               # Riverpod/ChangeNotifier providers (6 files)
    ├── screens/                 # Screen widgets (10 files)
    └── widgets/                 # Reusable widgets (empty)
```

Existing remote datasources: `auth`, `ai_assistant`, `catalog`,
`control_room`, `personal`, `recommendations`, `search`, `sync`,
`titles`. Missing: `social` (the entire Part 2 surface area).

---

## Environment notes (carried forward)

### Docker Desktop

- **Stale socket fix:** delete `C:\Users\dipak\AppData\Local\Docker\run`
  folder, relaunch Docker Desktop.
- **Postgres first-boot crash:** recreate with
  `docker compose -f infra/docker/docker-compose.yml up -d postgres`.
- **Docker is currently UP** — Postgres healthy on port 5432.

### Regression suite timing

514 tests, ~57 minutes against live Postgres. Don't pipe through `tail`.
Use `python -u -m pytest tests/ -v --tb=short` run in the background.
