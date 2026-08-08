# CineVault OS — Technology Evaluation: Alert Routing Platform V1

**Document Type:** Technology Evaluation & Selection Proposal  
**Decision ID:** `DEC-OBS-DEF-01` — Alert Routing & Incident Management Selection  
**Status:** Evaluation Complete — Awaiting Owner Approval  
**Date:** 2026-08-08  
**Selected Technology Recommendation:** Grafana OnCall (AGPLv3 License) + Prometheus Alertmanager (Apache 2.0)  
**Alternative Candidate:** PagerDuty (Proprietary SaaS)  
**Governance State:** PROPOSED TECHNOLOGY RECOMMENDATION — OWNER REVIEW REQUIRED  
**Implementation Authorization:** NOT AUTHORIZED  

---

## 1. Decision Under Evaluation

* **Decision ID:** `DEC-OBS-DEF-01`
* **Topic:** Alert Routing Platform & Incident Escalation Selection
* **Originating Baseline:** Observability & Operations Architecture V1 (`docs/OBSERVABILITY_OPERATIONS_ARCHITECTURE_V1.md`, `DEC-OBS-PRP-08`)
* **Current Governance State:** `DEFERRED` → `PROPOSED` (Awaiting Owner Review)
* **Objective:** Select an alert routing, deduplication, grouping, and incident escalation platform to receive alert triggers from Prometheus metrics (`DEC-OBS-DEF-02`), evaluate SLO error budget burn rates, manage Control Room on-call rotations, dispatch mobile/webhook notifications, and enforce incident response SLAs.

---

## 2. Canonical Architecture Requirements

Derived from locked baseline specifications (`Observability Architecture V1`, `Security Architecture V1`):

```text
┌───────────────────────────────────────┬───────────────────────────────────────────┬───────────────────────────────────────────┐
│ Feature / Capability Requirement      │ Architectural Specification               │ Canonical Source Reference                │
├───────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────┤
│ 1. SLO Error Budget Alert Triggers    │ Multi-window burn rate alert triggers     │ Observability V1 (DEC-OBS-PRP-04)         │
│ 2. Alert Deduplication & Grouping     │ Prevent alert fatigue during cascading failures│ Observability V1 (DEC-OBS-PRP-08)        │
│ 3. On-Call Schedule Rotation          │ Control Room engineer shift schedules     │ Observability V1 (DEC-OBS-PRP-08)         │
│ 4. Multi-Channel Notification Dispatch │ Webhook, Slack, Email, SMS, & Push routing│ Observability V1 (DEC-OBS-PRP-08)         │
│ 5. Permissive Open-Source Option      │ Self-hostable stack (No required per-user SaaS)│ Infrastructure V1 (DEC-INFRA-DEF-01)   │
└───────────────────────────────────────┴───────────────────────────────────────────┴───────────────────────────────────────────┘
```

---

## 3. Architecture Dependencies

* **Observability Platform:** Prometheus metric alert rules (`DEC-OBS-DEF-02`).
* **Log Backend:** Grafana Loki (`DEC-OBS-DEF-03`).
* **SIEM Integration:** Security log tamper alerts (`DEC-SEC-OPN-02`).

---

## 4. Candidate Technologies Identified

Four alert routing platforms were evaluated:

1. **Grafana OnCall + Prometheus Alertmanager (AGPLv3 / Apache 2.0):** Self-hostable, open-source incident management system with schedule rotations and Slack/SMS integration.
2. **PagerDuty (Proprietary SaaS):** SaaS incident management platform.
3. **Opsgenie (Atlassian Proprietary SaaS):** SaaS alert routing platform.
4. **Rootly / Incident.io (Proprietary SaaS):** Slack-native incident management platforms.

---

## 5. Candidate Evaluation & Feature Compatibility Matrix

```text
┌───────────────────────────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ Dimension / Feature                   │ 1. Grafana OnCall │ 2. PagerDuty      │ 3. Opsgenie       │ 4. Rootly         │
├───────────────────────────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ License / Delivery Model              │ AGPLv3 / Self-Host│ Proprietary SaaS  │ Proprietary SaaS  │ Proprietary SaaS  │
│ Prometheus / Alertmanager Integration │ 100% NATIVE       │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │
│ On-Call Schedule Rotation             │ NATIVE EXCELLENT  │ NATIVE EXCELLENT  │ NATIVE EXCELLENT  │ NATIVE            │
│ Multi-Channel Dispatch (Slack/SMS/App)│ SUPPORTED         │ EXCELLENT         │ EXCELLENT         │ EXCELLENT         │
│ Per-User Monthly License Cost         │ **$0 (Self-Hosted)**│ ~$39 / user / mo  │ ~$29 / user / mo  │ ~$49 / user / mo  │
│ Vendor Lock-In Risk                   │ **LOW**           │ HIGH              │ HIGH              │ HIGH              │
└───────────────────────────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

---

## 6. Detailed Evaluation Dimensions

### Functional Compatibility & DX
**Prometheus Alertmanager** handles alert deduplication, grouping (e.g., grouping 50 microservice pod crash alerts into 1 unified notification), and inhibition rules. **Grafana OnCall** provides an intuitive open-source Web UI for managing Control Room engineer on-call schedules, escalation policies, and dispatching alerts directly to Slack channels, Telegram, or push notification webhooks.

### Security & Compliance
* All alert notifications contain zero user personal data (`CAT-2`), containing strictly operational system metrics, cluster node names, and SLO error budget burn rate indicators.

---

## 7. Cost Model & 36-Month TCO

* **Software Cost:** $0 (Grafana OnCall AGPLv3 + Alertmanager Apache 2.0).
* **Compute Cost:** Small container pod inside K8s cluster (~$15/month = ~$540 / 36 months).
* **Comparison (PagerDuty for 5 Engineers):** 5 x $39/mo = $195/mo (~$7,020 / 36 months).
* **TCO Summary (36 Months):** ~$540 total operational cost (saving ~$6,480 vs SaaS).

---

## 8. Vendor Lock-In & Portability Analysis

* **Protocol Portability:** Standard Prometheus Alertmanager webhook format. Alerts can be re-routed to any notification receiver without changing alerting rules.
* **Lock-In Depth:** **LOW** (Open Prometheus Webhook standard).

---

## 9. Risk Assessment & Mitigations

* **Risk:** Webhook delivery failure during external network outage.
  * **Mitigation:** Configure dual notification dispatch channels (e.g., primary Slack webhook + secondary SMS/Push gateway).

---

## 10. Recommended Technology Selection

* **Primary Recommendation:** **Grafana OnCall (AGPLv3) + Prometheus Alertmanager (Apache 2.0)**
* **Alternative Candidate:** **PagerDuty (Proprietary SaaS)**
* **Justification:** Grafana OnCall paired with Prometheus Alertmanager provides a fully open-source, zero-license-cost incident management platform that integrates natively with the CineVault observability stack.

---

## 11. Final Governance Status

Evaluation:
COMPLETE

Recommendation:
Grafana OnCall (AGPLv3) + Prometheus Alertmanager (Apache 2.0)

Governance:
PROPOSED TECHNOLOGY RECOMMENDATION

Approval:
OWNER REVIEW REQUIRED

Technology Approved:
NO

Implementation:
NOT AUTHORIZED
