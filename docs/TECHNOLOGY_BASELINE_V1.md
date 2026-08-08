# CineVault OS — Authoritative Technology Baseline V1

**Document Type:** Authoritative Physical Technology Baseline Specification  
**Status:** OWNER APPROVED  
**Approval Date:** 2026-08-08  
**Governance State:** OWNER APPROVED TECHNOLOGY BASELINE  
**Implementation Boundary:** IMPLEMENTATION AUTHORIZED  
**Production Boundary:** PRODUCTION NOT YET AUTHORIZED  

---

> [!IMPORTANT]
> **AUTHORITATIVE STATUS DECLARATION:**  
> **OWNER APPROVED**  
> **IMPLEMENTATION AUTHORIZED**  
> **PRODUCTION NOT YET AUTHORIZED**  
> This specification is the single authoritative physical technology source of truth for CineVault OS. All physical implementation artifacts (code, container configurations, database migration scripts, local development stacks) MUST conform strictly to the technologies, interfaces, and security perimeters defined herein.

---

## 1. Owner Approval Record

* **Project Owner Approval:** CONFIRMED
* **Technology Baseline:** APPROVED
* **Implementation Authorization:** AUTHORIZED (Phase 0 Local Development Setup Authorized)
* **Production Authorization:** NOT AUTHORIZED (Production release remains gated under a separate release protocol)
* **Approval Timestamp:** 2026-08-08

---

## 2. Master Approved Technology Matrix

```text
┌───────────────────┬─────────────────────────────┬───────────────────────────────────────────┬───────────────────┬───────────────────────┐
│ Decision ID       │ Technology Category         │ Approved Physical Technology              │ License Type      │ Owner Approval Status │
├───────────────────┼─────────────────────────────┼───────────────────────────────────────────┼───────────────────┼───────────────────────┤
│ `DEC-API-DEF-02`  │ Authentication Provider     │ **Keycloak** (Self-Hosted OIDC Server)    │ Apache 2.0        │ OWNER APPROVED        │
│ `DEC-SEC-OPN-01`  │ Control Room MFA Strategy   │ **WebAuthn Hybrid Option D**              │ Open Policy Std   │ OWNER APPROVED        │
│ `DEC-API-DEF-03`  │ API Gateway Proxy           │ **Kong Gateway (Open Source)**            │ Apache 2.0        │ OWNER APPROVED        │
│ `DEC-API-DEF-04`  │ Distributed Cache & Limits  │ **Valkey** (Linux Foundation)             │ BSD 3-Clause      │ OWNER APPROVED        │
│ `DEC-INFRA-OPN-01`│ Queue Broker                │ **RabbitMQ** (Quorum Queues / DLX)        │ MPL 2.0           │ OWNER APPROVED        │
│ `DEC-PHYS-DEF-02` │ Database Migration Tool     │ **Flyway Community Edition**              │ Apache 2.0        │ OWNER APPROVED        │
│ `DEC-PHYS-DEF-03` │ Connection Pooling Proxy    │ **PgBouncer** (Transaction Mode)          │ PostgreSQL BSD    │ OWNER APPROVED        │
│ `DEC-ING-PRP-05`  │ Object Storage Target       │ **Cloudflare R2 / S3 API Standard**       │ S3 Protocol       │ OWNER APPROVED        │
│ `DEC-PHYS-DEF-04` │ Backup / DR Storage Target  │ **pgBackRest + Multi-Region S3 Target**   │ PostgreSQL BSD    │ OWNER APPROVED        │
│ `DEC-INFRA-DEF-01`│ Cloud Provider & Edge WAF   │ **Cloudflare WAF + Agnostic K8s Compute** │ Commercial / OCI  │ OWNER APPROVED        │
│ `DEC-INFRA-DEF-02`│ Orchestration & IaC         │ **OpenTofu (CNCF)** + **Kubernetes**      │ MPL 2.0 / Apache2 │ OWNER APPROVED        │
│ `DEC-INFRA-DEF-03`│ CI/CD Pipeline Automation   │ **GitHub Actions (OIDC)** + **ArgoCD**    │ Managed / Apache2 │ OWNER APPROVED        │
│ `DEC-OBS-DEF-01`  │ Alert Routing Platform      │ **Grafana OnCall** + **Alertmanager**     │ AGPLv3 / Apache 2 │ OWNER APPROVED        │
│ `DEC-OBS-DEF-02`  │ Observability Telemetry     │ **OpenTelemetry** + **Prometheus/Grafana**│ Apache2 / AGPLv3  │ OWNER APPROVED        │
│ `DEC-OBS-DEF-03`  │ Log Aggregation Backend     │ **Grafana Loki**                          │ AGPLv3            │ OWNER APPROVED        │
│ `DEC-SEC-OPN-02`  │ SIEM / Security Analytics   │ **Wazuh SIEM & XDR Engine**               │ GPLv2             │ OWNER APPROVED        │
└───────────────────┴─────────────────────────────┴───────────────────────────────────────────┴───────────────────┴───────────────────────┘
```

---

## 3. Technology Responsibilities & Architectural Mapping

1. **Keycloak (`DEC-API-DEF-02`):** Issues OIDC JWT tokens, authenticates public users and Control Room Curators, enforces RBAC roles, manages refresh tokens, and exposes RS256 JWKS endpoints for Gateway validation.
2. **WebAuthn Hybrid Option D (`DEC-SEC-OPN-01`):** Enforces hardware security keys for Control Room operations (`/internal/v1/*`), enforces a 60-second fresh authentication window for high-risk actions, and governs dual-admin break-glass emergency access.
3. **Kong Gateway (`DEC-API-DEF-03`):** Terminates edge requests, routes 3-tier API perimeters (`/v1/`, `/internal/v1/`), validates Keycloak bearer tokens via JWKS, enforces distributed rate-limiting via Valkey, and injects `X-Correlation-ID` headers.
4. **Valkey (`DEC-API-DEF-04`):** Stores atomic rate-limiting counters, ephemeral cache records for CAT-1 metadata, and token revocation hashes using RESP protocol.
5. **RabbitMQ (`DEC-INFRA-OPN-01`):** Manages asynchronous ingestion pipelines (`CAT-5`), payload validation jobs, artwork proxy processing, and Dead-Letter Exchange (DLX) queues.
6. **Flyway (`DEC-PHYS-DEF-02`):** Version-controls PostgreSQL schema DDL across 5 physical schemas (`core`, `catalog`, `ingestion`, `quality`, `personal`) using plain SQL versioned scripts.
7. **PgBouncer (`DEC-PHYS-DEF-03`):** Multiplexes client API and worker database connections in transaction pooling mode (`pool_mode = transaction`) against PostgreSQL 16.
8. **Cloudflare R2 / S3 API (`DEC-ING-PRP-05`):** Stores raw provider payloads (`CAT-5`) and media artwork poster thumbnails (`CAT-1`) with $0 egress bandwidth costs.
9. **pgBackRest (`DEC-PHYS-DEF-04`):** Performs continuous WAL archiving, daily block-level delta backups, AES-256 client-side encryption, and Point-In-Time Recovery (PITR) to S3 targets (RPO < 5m, RTO < 1h).
10. **Cloudflare Edge WAF + Kubernetes (`DEC-INFRA-DEF-01`):** Provides global L4/L7 DDoS mitigation, TLS 1.3 termination, and origin tunnel routing to multi-AZ Kubernetes worker nodes.
11. **OpenTofu & Kubernetes (`DEC-INFRA-DEF-02`):** Declaratively provisions cloud infrastructure (VPCs, Security Groups, IAM, DBs) via OpenTofu (MPL 2.0) and orchestrates container microservices via CNCF Kubernetes manifests.
12. **GitHub Actions & ArgoCD (`DEC-INFRA-DEF-03`):** Executes CI builds and scans using short-lived OIDC IAM tokens, paired with in-cluster ArgoCD GitOps deployment synchronization.
13. **OpenTelemetry + Prometheus + Grafana (`DEC-OBS-DEF-02`):** Ingests OTLP traces and metrics, redacts personal data (`CAT-2`), evaluates SLO burn rates, and renders operational dashboards.
14. **Grafana Loki (`DEC-OBS-DEF-03`):** Aggregates structured JSON log streams from pod stdout, indexing metadata labels and storing compressed log chunks in S3 storage.
15. **Grafana OnCall + Alertmanager (`DEC-OBS-DEF-01`):** Deduplicates alert triggers, manages Control Room shift rotations, and dispatches incident notifications to Slack/SMS/Webhooks.
16. **Wazuh SIEM (`DEC-SEC-OPN-02`):** Parses Keycloak and Kong security audit logs, enforces File Integrity Monitoring (FIM), and detects audit log tampering.

---

## 4. Security & Privacy Dependencies

* **Zero Personal Data Leakage:** OpenTelemetry Collector processors and Vector log agents scrub all `CAT-2` attributes (user emails, IPs, billing info) before telemetry leaves local pod perimeters (`DEC-SEC-PRP-08`).
* **Zero Permanent Cloud Credentials in CI:** GitHub Actions uses federated OIDC IAM tokens, issuing short-lived 15-minute execution credentials (`DEC-SEC-PRP-06`).
* **Audit Integrity:** Audit log hash verification and FIM rules run continuously inside Wazuh SIEM (`DEC-SEC-PRP-11`).

---

## 5. Licensing & Lock-In Matrix

All approved technologies use OSI-compliant permissive open-source or open-standard protocols:
* **Apache 2.0:** Keycloak, Kong Gateway, Flyway Community, OpenTelemetry, Prometheus, ArgoCD, S3 Protocol.
* **BSD 3-Clause / PostgreSQL BSD:** Valkey, PgBouncer, pgBackRest.
* **Mozilla Public License 2.0 (MPL 2.0):** RabbitMQ, OpenTofu.
* **AGPLv3 (Self-Hosted):** Grafana, Grafana Loki, Grafana OnCall.
* **GPLv2:** Wazuh SIEM.

**Overall Vendor Lock-In Rating:** **LOW** across all components.

---

## 6. Open Decisions & Non-Blocking Status

The following analytical open decisions are tracked and confirmed **NON-BLOCKING FOR IMPLEMENTATION**:
1. `DEC-INFRA-OPN-02` (Multi-Region Read Replica Scale): Default = Single-region multi-AZ primary + read replica (`OPEN — IMPLEMENTATION MAY PROCEED WITH DOCUMENTED BOUNDARY`).
2. `DEC-OBS-OPN-01` (Metric Retention): Default = 30 days hot TSDB retention (`OPEN — IMPLEMENTATION MAY PROCEED WITH DOCUMENTED BOUNDARY`).
3. `DEC-OBS-OPN-02` (Automated Anomaly Detection): Default = Static threshold burn-rate alerts (`OPEN — IMPLEMENTATION MAY PROCEED WITH DOCUMENTED BOUNDARY`).
4. `DEC-ING-OPN-02` (Raw CAT-5 Payload Retention): Default = 90 days payload expiration (`OPEN — IMPLEMENTATION MAY PROCEED WITH DOCUMENTED BOUNDARY`).
5. `DEC-QUAL-OPN-02` (Quarantine Retention): Default = 30 days quarantine window (`OPEN — IMPLEMENTATION MAY PROCEED WITH DOCUMENTED BOUNDARY`).
6. `DEC-PHYS-OPN-01` (Payload Partition Granularity): Default = Monthly table partitioning (`OPEN — IMPLEMENTATION MAY PROCEED WITH DOCUMENTED BOUNDARY`).

---

## 7. Formal Change-Control Protocol

Any future proposed modification to the approved technology baseline MUST trigger a formal **Technology Amendment Request (TAR)** containing:
1. Original approved technology & decision ID
2. Requested substitution or addition
3. Technical and security justification
4. License impact analysis
5. Cost and TCO impact analysis
6. Explicit Project Owner sign-off

---

## 8. Governance Boundaries

* **OWNER APPROVED**
* **IMPLEMENTATION AUTHORIZED**
* **PRODUCTION NOT YET AUTHORIZED**
