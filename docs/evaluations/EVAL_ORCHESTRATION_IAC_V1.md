# CineVault OS — Technology Evaluation: Orchestration & IaC Technology V1

**Document Type:** Technology Evaluation & Selection Proposal  
**Decision ID:** `DEC-INFRA-DEF-02` — Container Orchestration & IaC Tooling Selection  
**Status:** Evaluation Complete — Awaiting Owner Approval  
**Date:** 2026-08-08  
**Selected Technology Recommendation:** OpenTofu (MPL 2.0 — CNCF) + Kubernetes (CNCF Standard) + Helm  
**Alternative Candidate:** Pulumi (Apache License 2.0) + Kubernetes  
**Governance State:** PROPOSED TECHNOLOGY RECOMMENDATION — OWNER REVIEW REQUIRED  
**Implementation Authorization:** NOT AUTHORIZED  

---

## 1. Decision Under Evaluation

* **Decision ID:** `DEC-INFRA-DEF-02`
* **Topic:** Container Orchestration & Infrastructure as Code (IaC) Selection
* **Originating Baseline:** Infrastructure Architecture V1 (`docs/INFRASTRUCTURE_ARCHITECTURE_V1.md`, `DEC-INFRA-PRP-02`)
* **Current Governance State:** `DEFERRED` → `PROPOSED` (Awaiting Owner Review)
* **Objective:** Select a vendor-neutral Infrastructure as Code (IaC) tool to declaratively manage cloud resources (VPCs, Subnets, Security Groups, IAM roles, S3 buckets) and a container orchestration standard to deploy, scale, health-check, and manage CineVault OS microservices, background workers, gateways, and sidecars.

---

## 2. Canonical Architecture Requirements

Derived from locked baseline specifications (`Infrastructure Architecture V1`, `Security Architecture V1`):

```text
┌───────────────────────────────────────┬───────────────────────────────────────────┬───────────────────────────────────────────┐
│ Feature / Capability Requirement      │ Architectural Specification               │ Canonical Source Reference                │
├───────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────┤
│ 1. Declarative Infrastructure State   │ State management with encryption at rest  │ Infrastructure V1 (DEC-INFRA-PRP-02)      │
│ 2. Permissive Open-Source License     │ OSI/CNCF open source (No BSL commercial risk)│ Baseline Governance (DEC-INFRA-DEF-02)   │
│ 3. Automated Pod Health & HPA Scaling │ Auto-scaling microservices based on CPU/RAM│ Infrastructure V1 (DEC-INFRA-PRP-02)      │
│ 4. Zero-Downtime Rolling Deployments  │ Rolling update deployment strategies      │ Infrastructure V1 (DEC-INFRA-PRP-02)      │
│ 5. Local Development Parity           │ Local Kubernetes (k3d / minikube / Docker)│ Infrastructure V1 (DEC-INFRA-PRP-01)      │
└───────────────────────────────────────┴───────────────────────────────────────────┴───────────────────────────────────────────┘
```

---

## 3. Architecture Dependencies

* **Containers:** OCI-compliant Docker containers (`DEC-INFRA-PRP-01`).
* **Cloud Provider:** Multi-AZ Cloud Compute & VPC (`DEC-INFRA-DEF-01`).
* **CI/CD Pipeline:** Deployment pipeline runner (`DEC-INFRA-DEF-03`).

---

## 4. Candidate Technologies Identified

Four IaC and Orchestration combinations were evaluated:

1. **OpenTofu (MPL 2.0 — CNCF) + Kubernetes + Helm:** Community-governed, vendor-neutral open-source IaC fork of Terraform hosted by CNCF/Linux Foundation, paired with CNCF Kubernetes.
2. **Terraform (BSL 1.1 — HashiCorp/IBM) + Kubernetes + Helm:** Source-available IaC tool subject to BSL 1.1 commercial restrictions.
3. **Pulumi (Apache 2.0) + Kubernetes:** Code-driven IaC platform using TypeScript/Python/Go.
4. **HashiCorp Nomad (BSL 1.1) + Terraform:** Workload orchestrator alternative.

---

## 5. Candidate Evaluation & Feature Compatibility Matrix

```text
┌───────────────────────────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ Dimension / Feature                   │ 1. OpenTofu+K8s   │ 2. Terraform+K8s  │ 3. Pulumi+K8s     │ 4. Nomad+Terraform│
├───────────────────────────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ License Type                          │ MPL 2.0 (CNCF)    │ BSL 1.1 (HashiCorp│ Apache 2.0        │ BSL 1.1           │
│ Governance Model                      │ Linux Foundation  │ Proprietary Corp  │ Proprietary Corp  │ Proprietary Corp  │
│ Native Client-Side State Encryption   │ NATIVE            │ ENTERPRISE ONLY   │ SUPPORTED         │ ENTERPRISE ONLY   │
│ Ecosystem & Provider Compatibility    │ 100% HCL Compatible 100% HCL Standard │ EXCELLENT         │ LIMITED           │
│ Container Auto-Scaling (HPA)          │ NATIVE (K8s)      │ NATIVE (K8s)      │ NATIVE (K8s)      │ SUPPORTED         │
│ Local Dev Parity (k3d / KinD)         │ EXCELLENT         │ EXCELLENT         │ EXCELLENT         │ MODERATE          │
│ BSL Commercial Restriction Risk       │ **ZERO RISK**     │ HIGH (BSL 1.1)    │ ZERO RISK         │ HIGH (BSL 1.1)    │
└───────────────────────────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

---

## 6. Detailed Evaluation Dimensions

### Licensing & Governance Analysis (Critical 2026 Context)
In August 2023, HashiCorp changed Terraform from Mozilla Public License (MPL 2.0) to Business Source License (BSL 1.1), restricting commercial competitive usage. In response, Linux Foundation established **OpenTofu** as an open-source fork under MPL 2.0, accepted as a **CNCF Sandbox project in 2025**. OpenTofu introduces native client-side state encryption out-of-the-box (a feature gated in enterprise Terraform). OpenTofu guarantees 100% vendor neutrality and zero legal risk.

### Functional Compatibility & Orchestration
Kubernetes (K8s) provides declarative YAML manifests (`Deployments`, `Services`, `ConfigMaps`, `Secrets`, `Ingress`, `HPA`), rolling deployment strategies, and health liveness/readiness probes. Helm charts package multi-component microservices cleanly.

---

## 7. Cost Model & 36-Month TCO

* **Software Cost:** $0 (OpenTofu MPL 2.0 + Kubernetes Apache 2.0).
* **State Storage Cost:** S3 bucket state file with client-side OpenTofu encryption (< $1/month = ~$36 / 36 months).
* **TCO Summary (36 Months):** ~$36 total IaC software cost.

---

## 8. Vendor Lock-In & Portability Analysis

* **IaC Portability:** OpenTofu uses standard HCL syntax compatible with all open cloud provider modules.
* **Orchestration Portability:** Kubernetes manifests run identically on AWS EKS, GCP GKE, Azure AKS, or local `k3d` clusters.
* **Lock-In Depth:** **LOW** (CNCF Open Standards).

---

## 9. Risk Assessment & Mitigations

* **Risk:** Drift between OpenTofu and future HashiCorp Terraform releases.
  * **Mitigation:** Rely on CNCF OpenTofu specifications and standard cloud provider HCL modules.

---

## 10. Recommended Technology Selection

* **Primary Recommendation:** **OpenTofu (MPL 2.0 — CNCF) + Kubernetes (CNCF Standard) + Helm**
* **Alternative Candidate:** **Pulumi (Apache License 2.0) + Kubernetes**
* **Justification:** OpenTofu offers 100% open-source MPL 2.0 licensing under Linux Foundation/CNCF governance, native state encryption, 100% HCL compatibility, and complete independence from HashiCorp BSL commercial restrictions.

---

## 11. Final Governance Status

Evaluation:
COMPLETE

Recommendation:
OpenTofu (MPL 2.0 — CNCF) + Kubernetes (CNCF Standard) + Helm

Governance:
PROPOSED TECHNOLOGY RECOMMENDATION

Approval:
OWNER REVIEW REQUIRED

Technology Approved:
NO

Implementation:
NOT AUTHORIZED
