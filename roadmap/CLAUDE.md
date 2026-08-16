# CineVault OS — Roadmap Operating Rules
(Auto-loaded by Claude Code every session in this repo. Do not delete.)

## How to use this repo
1. Read `STATUS.md` first — always, before touching code.
2. Read the phase file for the CURRENT phase only, under `phases/`.
3. Never build more than one phase per session. Never combine phases to move faster.
4. Update `STATUS.md` before the session ends, even if the phase isn't finished.

---

## 0. Source of Truth (priority order — never override a higher one silently)
1. Approved ADRs
2. Approved Technical Requirements
3. Approved Data Model
4. Approved Master Concept
5. Current repository
6. Research
7. AI suggestions
8. Conversation history

If implementation requires a NEW architectural decision:
**STOP → explain the issue → propose the decision → wait for approval → then update/create the ADR.**

---

## 1. Non-Negotiables — NEVER do these, regardless of what a phase file asks for
- destroy personal history during a metadata update
- unauthorized scraping
- piracy functionality
- let AI become canonical authority directly
- let unverified AI metadata become canonical automatically
- silent provider conflicts
- silent identity merges
- cross-user data access
- hardcoded production secrets
- fake catalog data represented as real data
- bypass ingestion quality controls
- bypass licensing gates
- break existing APIs without approval
- replace approved technologies without approval

**Trade-off priority when in doubt:**
`ACCURACY > PROVENANCE > DEDUPLICATION > CONSISTENCY > COVERAGE > QUANTITY`

---

## 2. Execution Model — required for every phase, no exceptions
```
AUDIT → PLAN → IMPLEMENT → TEST → RUNTIME VERIFY → SECURITY VERIFY
      → REGRESSION VERIFY → DOCUMENT → GIT COMMIT → PHASE GATE → NEXT PHASE
```

A phase is COMPLETE only when **all** of the following are true:
- implementation works
- tests pass
- runtime behavior verified (not unit tests alone)
- architecture matches approved docs
- security is acceptable
- documentation updated
- git state is clean
- phase gate passes

**Never mark a phase complete based on unit tests alone.**

---

## 3. Git Workflow
Branch prefixes: `main`, `develop`, `feature/*`, `fix/*`, `chore/*`, `docs/*`, `security/*`, `data/*`, `perf/*`

Never work directly on `main` for feature implementation.

Before every phase, run:
```
git status
git branch --show-current
git log --oneline -10
```
Then create an appropriately named branch.

Commit prefixes: `feat: fix: security: data: test: perf: docs: refactor: chore:`

Never use `git reset --hard`, `git clean -fd`, or force push unless explicitly approved.
Never delete user work. Never commit secrets.

End of phase: `git status`, `git diff`, `git log` — branch must be clean.
Do **not** auto-merge into main. Do **not** auto-delete branches.

---

## 4. Session Protocol
1. Read `STATUS.md`.
2. Read the current phase file in `phases/`.
3. Confirm actual branch/repo state matches what `STATUS.md` says before starting.
4. Run the Execution Model above.
5. Update `STATUS.md` before ending the session — status, branch, gate result, notes for next time.

If repo state and `STATUS.md` disagree, stop and flag it before proceeding.

---

## 5. Phase Completion Report (produce this at the end of every phase)
```
PHASE STATUS

Objective:
Implemented:
Tests:
Runtime:
Security:
Performance:
Documentation:
Git:
Remaining issues:
Next phase:
```
Status must be one of: `COMPLETE`, `COMPLETE WITH DEFERRED ITEMS`, `BLOCKED`, `FAILED`.
**Never use COMPLETE when important functionality is still stubbed.**

---

## 6. Blocker Rule
If a critical issue is discovered mid-phase: **STOP the current phase.**
Do not continue building features on a broken foundation.

Examples of a stop-the-phase issue: data corruption, an authentication
vulnerability, a personal-data leak, an identity merge bug, licensing
uncertainty, migration corruption, broken canonical relationships.

Fix and re-audit before continuing.

---

## 7. No Fake Progress
Never report progress that isn't real, e.g.:
- "5,000 titles imported" when the records are synthetic
- "AI implemented" when only an interface exists
- "offline sync complete" when only local storage exists
- "recommendations complete" when only static recommendations exist
- "production ready" before the complete release gate passes

---

## 8. Priorities (apply when trade-offs come up, in this order)
```
QUALITY               > SPEED
REAL IMPLEMENTATION   > DOCUMENTATION CLAIMS
REAL DATA             > SYNTHETIC ROW COUNT
DATA INTEGRITY        > FEATURE COUNT
SECURITY              > CONVENIENCE
PERSONAL DATA PROTECTION > AUTOMATION
PROVENANCE            > COVERAGE
TESTED EXECUTION      > CODE EXISTENCE
RECOVERABILITY        > "IT SHOULD WORK"
```
Proceed one phase at a time. Never skip a gate. Never silently change
architecture. Never hide blockers. Never fabricate progress.

---

See also: `DOCUMENTATION_MAP.md` (which docs to keep in sync),
`FINAL_COMPLETION_GATE.md` (the checklist before declaring the project done),
and `FINAL_REPORT_TEMPLATE.md` (the report to produce once every gate passes).
