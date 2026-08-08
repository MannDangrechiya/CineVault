# CineVault OS — Technology Evaluation: Cloud Infrastructure Provider & WAF V1

**Document Type:** Technology Evaluation & Selection Proposal  
**Decision ID:** `DEC-INFRA-DEF-01` — Cloud Infrastructure Provider & Edge WAF Selection  
**Status:** Evaluation Complete — Awaiting Owner Approval  
**Date:** 2026-08-08  
**Selected Technology Recommendation:** Cloudflare Edge WAF + Multi-AZ Cloud Infrastructure (AWS / Agnostic OCI Provider)  
**Alternative Candidate:** GCP (Cloud Armor + GKE + Cloud SQL)  
**Governance State:** PROPOSED TECHNOLOGY RECOMMENDATION — OWNER REVIEW REQUIRED  
**Implementation Authorization:** NOT AUTHORIZED  

---

## 1. Decision Under Evaluation

* **Decision ID:** `DEC-INFRA-DEF-01`
* **Topic:** Cloud Infrastructure Provider & Edge WAF Technology Selection
* **Originating Baseline:** Infrastructure Architecture V1 (`docs/INFRASTRUCTURE_ARCHITECTURE_V1.md`, `DEC-INFRA-PRP-01`, `DEC-INFRA-PRP-06`) & Security Architecture V1 (`docs/SECURITY_ARCHITECTURE_V1.md`)
* **Current Governance State:** `DEFERRED` → `PROPOSED` (Awaiting Owner Review)
* **Objective:** Select a primary cloud infrastructure provider model and Edge Web Application Firewall (WAF) tier to host CineVault OS microservices, handle L4/L7 DDoS mitigation, terminate TLS 1.3 at the global edge, manage multi-AZ VPC isolation, and provide high-availability computing and database hosting.

---

## 2. Canonical Architecture Requirements

Derived from locked baseline specifications (`Infrastructure Architecture V1`, `Security Architecture V1`):

```text
┌───────────────────────────────────────┬───────────────────────────────────────────┬───────────────────────────────────────────┐
│ Feature / Capability Requirement      │ Architectural Specification               │ Canonical Source Reference                │
├───────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────┤
│ 1. Multi-AZ High Availability Compute │ 3 Availability Zone (AZ) fault tolerance  │ Infrastructure V1 (DEC-INFRA-PRP-01)      │
│ 2. Edge L4/L7 WAF & DDoS Filtering    │ Global edge DDoS protection & OWASP rules  │ Security V1 (DEC-SEC-PRP-01, INFRA-06)   │
│ 3. VPC Network Isolation              │ Public, Application, & Private DB Subnets │ Infrastructure V1 (DEC-INFRA-PRP-01)      │
│ 4. OCI Container Orchestration        │ Managed Kubernetes runtime compatibility │ Infrastructure V1 (DEC-INFRA-PRP-02)      │
│ 5. Managed / Self-Hosted PostgreSQL 16│ Multi-AZ primary & replica instance support│ Physical DB V1 (DEC-PHYS-PRP-01)         │
│ 6. Terraform / OpenTofu IaC Support   │ Declarative infrastructure provisioning   │ Infrastructure V1 (DEC-INFRA-DEF-02)      │
└───────────────────────────────────────┴───────────────────────────────────────────┴───────────────────────────────────────────┘
```

---

## 3. Architecture Dependencies

* **API Gateway:** Kong Gateway (`DEC-API-DEF-03`) downstream of WAF.
* **Identity Server:** Keycloak (`DEC-API-DEF-02`) hosted in application VPC subnet.
* **IaC Engine:** OpenTofu / Terraform (`DEC-INFRA-DEF-02`).

---

## 4. Candidate Technologies Identified

Four cloud provider and WAF architecture combinations were evaluated:

1. **Cloudflare Edge WAF + AWS (Multi-AZ EKS / RDS):** Cloudflare global edge network for DDoS/WAF paired with AWS EKS and RDS multi-AZ infrastructure.
2. **Cloudflare Edge WAF + Hetzner / Bare Metal (Self-Hosted Kube):** Cloudflare edge WAF paired with self-hosted Kubernetes on bare-metal servers.
3. **Google Cloud Platform (Cloud Armor + GKE + Cloud SQL):** Native GCP cloud security and compute suite.
4. **Microsoft Azure (Front Door + AKS + Azure Database for Postgres):** Native Azure cloud security and compute suite.

---

## 5. Candidate Evaluation & Feature Compatibility Matrix

```text
┌───────────────────────────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ Dimension / Feature                   │ 1. Cloudflare+AWS │ 2. Cloudflare+Hetz│ 3. GCP            │ 4. Azure          │
├───────────────────────────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ Edge DDoS Mitigation Capacity         │ > 300 Tbps (Best) │ > 300 Tbps        │ ~100 Tbps         │ ~150 Tbps         │
│ Managed Kubernetes (K8s) Maturity     │ EXCELLENT (EKS)   │ Self-Managed      │ EXCELLENT (GKE)   │ EXCELLENT (AKS)   │
│ Multi-AZ VPC Security Isolation       │ NATIVE PERFECT    │ REQUIRES MANUAL   │ NATIVE PERFECT    │ NATIVE PERFECT    │
│ Bandwidth Egress Costs                │ LOW (via R2/CF)   │ VERY LOW          │ HIGH              │ HIGH              │
│ Terraform / OpenTofu Provider Quality │ EXCELLENT         │ GOOD              │ EXCELLENT         │ EXCELLENT         │
│ Operational Overhead                  │ LOW               │ HIGH              │ LOW               │ LOW               │
│ Vendor Lock-In Depth                  │ MODERATE-LOW      │ VERY LOW          │ MODERATE          │ MODERATE          │
└───────────────────────────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

---

## 6. Detailed Evaluation Dimensions

### Functional Compatibility & Security Perimeter
Cloudflare operates as Zone 1 (Global Edge Perimeter), filtering OWASP Top 10 exploits, rate-limiting malicious IP bots, and inspecting TLS 1.3 certificates before forwarding traffic over authenticated origin tunnels (`Cloudflare Tunnel`) into the application VPC. AWS EKS provides Multi-AZ container compute, while AWS RDS / Aurora PostgreSQL 16 provides multi-AZ database failover.

### Security & Privacy
* Zero public IPv4/IPv6 exposure of internal application pods or database nodes; origin servers accept connections strictly from Cloudflare Tunnel / Security Groups.
* Personal user data (`CAT-2`) remains encrypted within isolated private VPC subnets.

---

## 7. Cost Model & 36-Month TCO

* **Cloudflare Tier:** Pro / Business Tier WAF ($200/month = $7,200 / 36 months).
* **Compute / DB Infrastructure:** 3-AZ K8s Cluster + Multi-AZ Postgres 16 DB (~$450/month = $16,200 / 36 months).
* **TCO Summary (36 Months):** ~$23,400 total cloud infrastructure cost.

---

## 8. Vendor Lock-In & Portability Analysis

* **Infrastructure Portability:** All application workloads run in standard OCI containers on Kubernetes (`DEC-INFRA-DEF-02`).
* **IaC Portability:** Infrastructure defined entirely via OpenTofu / Terraform scripts. Switching cloud compute providers requires changing Terraform provider modules without modifying application code.
* **Lock-In Depth:** **MODERATE-LOW** (Standard Kubernetes & OpenTofu IaC).

---

## 9. Risk Assessment & Mitigations

* **Risk:** Cloud provider egress cost inflation.
  * **Mitigation:** Route all media traffic through Cloudflare CDN/R2 ($0 egress fees) and maintain cloud-agnostic Kubernetes manifests.

---

## 10. Recommended Technology Selection

* **Primary Recommendation:** **Cloudflare Edge WAF + Multi-AZ Cloud Infrastructure (AWS / Agnostic OCI Provider)**
* **Alternative Candidate:** **Google Cloud Platform (Cloud Armor + GKE + Cloud SQL)**
* **Justification:** Cloudflare WAF delivers superior edge DDoS protection and zero egress penalties, while standard Multi-AZ Kubernetes compute ensures high availability and portable cloud hosting.

---

## 11. Final Governance Status

Evaluation:
COMPLETE

Recommendation:
Cloudflare Edge WAF + Multi-AZ Cloud Infrastructure (AWS / Agnostic OCI Provider)

Governance:
PROPOSED TECHNOLOGY RECOMMENDATION

Approval:
OWNER REVIEW REQUIRED

Technology Approved:
NO

Implementation:
NOT AUTHORIZED
