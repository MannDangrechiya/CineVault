# CineVault OS — Data Source Decision Log V1

**Document Type:** Mandatory Data Source Strategy Decision Classification Log  
**Status:** Complete (Formal Owner Approval Pass)  
**Date:** 2026-08-08  
**Scope:** Approved, Derived, Proposed, Deferred, and Blocked Data Source Strategy Decisions  

---

## 1. Executive Summary

This Data Source Decision Log categorizes all source-strategy choices made in `DATA_SOURCE_REGISTRY_V1.md` according to task governance rules.

Decisions are strictly divided into five mandatory categories:
* **APPROVED:** Explicitly approved by project owner (`DS-01` through `DS-07`, `DEC-SRC-PRP-01`, `DEC-SRC-PRP-02`).
* **DERIVED:** Direct consequences of approved source strategy decisions.
* **PROPOSED:** New recommendations requiring owner review (labeled `PROPOSED — OWNER REVIEW REQUIRED`).
* **DEFERRED:** Intentionally postponed technical ingestion choices.
* **BLOCKED:** Decisions awaiting external legal, contract, or provider input.

---

## 2. Decision Log Matrix

### A. APPROVED DECISIONS (Project Owner Approved)

| Decision ID | Decision Title | Source Baseline | Summary of Approved Decision |
|---|---|---|---|
| `DS-01` | **Domain-Specific Source Authority** | Owner Approval | No single universal global provider. Authority determined per domain based on quality, licensing, coverage, and provenance. |
| `DS-02` | **TMDb Conditional Status** | Owner Approval | TMDb is a candidate provider; NOT permanently approved for commercial use without licensing verification. |
| `DS-03` | **AniList Restricted Ingestion** | Owner Approval | AniList persistent canonical ingestion restricted under current public terms. Role limited to on-demand lookup/enrichment. |
| `DS-04` | **IMDb Public Dataset Exclusion** | Owner Approval | IMDb public non-commercial datasets EXCLUDED from production ingestion. Commercial IMDb products remain candidates (`CONDITIONAL`). |
| `DS-05` | **JustWatch & Scraping Prohibition** | Owner Approval | Web scraping public interfaces is explicitly PROHIBITED. JustWatch candidate via official partner channel (`CONDITIONAL`). |
| `DS-06` | **Wikidata Structured Reference Data** | Owner Approval | Wikidata structured data candidate (CC0). Linked media/image licensing evaluated separately. |
| `DS-07` | **Candidate Registry Expansion** | Owner Approval | TheTVDB, AniDB, ANN, Europeana, Internet Archive, LoC, KOBIS, Kitsu registered as candidate sources. |
| `DEC-SRC-PRP-01` | **KOBIS / KOFIC Primary Korean Authority** | Owner Approval (Post-Gate) | **APPROVED BY OWNER.** Designated Primary Korean-Domain Authority. Approval scope: Authority role designation ONLY. Implementation condition: Licensing/access verification remains required before production ingestion (Provider Status: `CANDIDATE`). |
| `DEC-SRC-PRP-02` | **TheTVDB Secondary TV Authority** | Owner Approval (Post-Gate) | **APPROVED BY OWNER.** Designated Secondary TV Authority. Approval scope: Authority role designation ONLY. Implementation condition: Revenue-tier licensing verification remains required before production ingestion (Provider Status: `CANDIDATE`). |

---

### B. DERIVED DECISIONS

| Decision ID | Decision Title | Source Approved Decision | Summary of Derived Decision |
|---|---|---|---|
| `DEC-SRC-DER-01` | **Metadata vs Media Rights Isolation** | `DS-06` | Image and media licensing evaluated independently from metadata licensing for all providers. |
| `DEC-SRC-DER-02` | **External Identity Provider Mapping** | `ADR-001`, `DS-01` | All external provider IDs categorized as `External Identity Mapping` and NEVER canonical identity. |
| `DEC-SRC-DER-03` | **Minimum Provenance Requirements** | `DS-01` | Every ingested external field must record provider name, external ID, retrieval timestamp, and license context. |
| `DEC-SRC-DER-04` | **Candidate Commercial Feed Designation** | `DS-04`, `DS-05` | Gracenote, TiVo/Rovi, Reelgood, Whip Media registered as candidate commercial feeds if open sources prove insufficient. |

---

### C. PROPOSED DECISIONS (PROPOSED — OWNER REVIEW REQUIRED)

```text
NEW UNAPPROVED PROPOSED DECISIONS: 0
```
* All source authority proposals (`DEC-SRC-PRP-01` and `DEC-SRC-PRP-02`) have received formal Project Owner approval.

---

### D. DEFERRED DECISIONS (Intentionally Postponed)

| Decision ID | Deferred Topic | Reason for Deferral | Target Phase |
|---|---|---|---|
| `DEC-SRC-DEF-01` | **Ingestion Pipeline Network Client Code** | Source registry is documentation only. Code creation prohibited in this phase. | Ingestion Pipeline Phase |
| `DEC-SRC-DEF-02` | **Rate-Limiting & API Throttling Queues** | Network infrastructure engineering postponed. | Ingestion Architecture Phase |
| `DEC-SRC-DEF-03` | **Cross-Provider Field Conflict Weighting** | Field resolution weighting algorithms postponed. | Ingestion Quality Phase |
| `DEC-SRC-DEF-04` | **Physical Provenance Schema DDL** | Marked as `DEFERRED — INGESTION / PROVENANCE REVIEW`. | Ingestion Review Phase |

---

### E. BLOCKED DECISIONS (Awaiting Legal / Provider Input)

| Decision ID | Blocked Item | Dependency / Barrier | Action Needed to Unblock |
|---|---|---|---|
| `DEC-SRC-BLK-01` | **TMDb Production Ingestion Execution** | Commercial license verification (`DS-02`) | Commercial agreement execution by project owner |
| `DEC-SRC-BLK-02` | **JustWatch Availability Feed Ingestion** | Official partner contract (`DS-05`) | Partner application & contract signing |
| `DEC-SRC-BLK-03` | **IMDb Commercial Feed Ingestion** | AWS Data Exchange license (`DS-04`) | Commercial contract execution |
