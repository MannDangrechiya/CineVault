# CineVault OS — Technology Evaluation: CI/CD Pipeline Automation V1

**Document Type:** Technology Evaluation & Selection Proposal  
**Decision ID:** `DEC-INFRA-DEF-03` — CI/CD Pipeline Automation Selection  
**Status:** Evaluation Complete — Awaiting Owner Approval  
**Date:** 2026-08-08  
**Selected Technology Recommendation:** GitHub Actions (SaaS / Ephemeral Runners) + ArgoCD (CNCF GitOps)  
**Alternative Candidate:** GitLab CI/CD (SaaS / Self-Hosted Runners)  
**Governance State:** PROPOSED TECHNOLOGY RECOMMENDATION — OWNER REVIEW REQUIRED  
**Implementation Authorization:** NOT AUTHORIZED  

---

## 1. Decision Under Evaluation

* **Decision ID:** `DEC-INFRA-DEF-03`
* **Topic:** CI/CD Pipeline Automation Technology Selection
* **Originating Baseline:** Infrastructure Architecture V1 (`docs/INFRASTRUCTURE_ARCHITECTURE_V1.md`, `DEC-INFRA-PRP-01`)
* **Current Governance State:** `DEFERRED` → `PROPOSED` (Awaiting Owner Review)
* **Objective:** Select a CI/CD pipeline automation framework to automate static code analysis, security vulnerability scanning, unit/integration testing, container image building, OpenTofu plan verification, and declarative GitOps deployments across staging and production environments.

---

## 2. Canonical Architecture Requirements

Derived from locked baseline specifications (`Infrastructure Architecture V1`, `Security Architecture V1`):

```text
┌───────────────────────────────────────┬───────────────────────────────────────────┬───────────────────────────────────────────┐
│ Feature / Capability Requirement      │ Architectural Specification               │ Canonical Source Reference                │
├───────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────┤
│ 1. OIDC Credential Federation         │ Short-lived cloud IAM tokens (No static keys)│ Security V1 (DEC-SEC-PRP-06)           │
│ 2. Automated Testing Enforcement      │ Unit, integration, & schema migration tests│ Infrastructure V1 (DEC-INFRA-DEF-03)      │
│ 3. Automated Container Security Scan  │ Trivy / Grype vulnerability container scan│ Security V1 (DEC-SEC-PRP-11)              │
│ 4. GitOps Declarative Deployment      │ Pull-based Kubernetes state sync (ArgoCD) │ Infrastructure V1 (DEC-INFRA-DEF-02)      │
│ 5. Secret Protection & Masking        │ Automatic masking of secrets in build logs│ Security V1 (DEC-SEC-PRP-06)              │
└───────────────────────────────────────┴───────────────────────────────────────────┴───────────────────────────────────────────┘
```

---

## 3. Architecture Dependencies

* **Code Repository:** Git version control.
* **Orchestration:** Kubernetes & Helm (`DEC-INFRA-DEF-02`).
* **Secrets Management:** Short-lived OIDC Cloud Tokens (`DEC-SEC-PRP-06`).

---

## 4. Candidate Technologies Identified

Four CI/CD pipeline architectural approaches were evaluated:

1. **GitHub Actions + ArgoCD (GitOps):** Cloud CI workflows using OIDC federated authentication for build/test paired with ArgoCD for Kubernetes GitOps deployment.
2. **GitLab CI/CD:** Integrated GitLab pipeline runner suite.
3. **Tekton Pipelines (CNCF):** Kubernetes-native pipeline engine.
4. **Jenkins (Open Source):** Traditional self-hosted automation server.

---

## 5. Candidate Evaluation & Feature Compatibility Matrix

```text
┌───────────────────────────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ Dimension / Feature                   │ 1. GHA + ArgoCD   │ 2. GitLab CI/CD   │ 3. Tekton         │ 4. Jenkins        │
├───────────────────────────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ License / Delivery Model              │ Managed / Apache  │ MIT / Managed     │ Apache 2.0 (CNCF) │ MIT Open Source   │
│ Short-Lived OIDC Cloud Auth           │ NATIVE EXCELLENT  │ SUPPORTED         │ SUPPORTED         │ REQUIRES PLUGIN   │
│ Declarative GitOps Synchronization    │ NATIVE (ArgoCD)   │ SUPPORTED         │ MANUAL            │ MANUAL            │
│ Ephemeral Build Runner Isolation      │ EXCELLENT         │ EXCELLENT         │ NATIVE (Pods)     │ MODERATE          │
│ Secret Masking & Protection           │ NATIVE EXCELLENT  │ NATIVE EXCELLENT  │ GOOD              │ MODERATE          │
│ Operational Maintenance Overhead      │ VERY LOW          │ LOW               │ HIGH              │ HIGH              │
│ Developer Familiarity                 │ UNIVERSAL (High)  │ HIGH              │ MODERATE          │ HIGH              │
└───────────────────────────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

---

## 6. Detailed Evaluation Dimensions

### Functional Compatibility & Security Isolation
GitHub Actions allows workflows to authenticate directly to AWS / GCP via **OIDC identity federation**, issuing short-lived 15-minute access tokens for container pushes, eliminating static AWS access keys stored in CI secrets. For deployment, **ArgoCD** runs inside the Kubernetes cluster, pulling updated image tags and Helm values from Git without exposing cluster admin ports to the internet.

### Security & Compliance
* All CI steps run in ephemeral container runners.
* Pull requests from external contributors are prohibited from accessing production secrets or triggering automated deployments without explicit approval.

---

## 7. Cost Model & 36-Month TCO

* **GitHub Actions SaaS Tier:** 3,000 free build minutes/month; paid tier ~$40/month (~$1,440 / 36 months).
* **ArgoCD In-Cluster Controller:** Ephemeral pod resource overhead (~$15/month = ~$540 / 36 months).
* **TCO Summary (36 Months):** ~$1,980 total CI/CD operational cost.

---

## 8. Vendor Lock-In & Portability Analysis

* **Pipeline Portability:** CI build scripts execute standard shell commands, Docker build commands, and OpenTofu CLI operations. Workflows can be ported to GitLab CI or Tekton with minimal script changes.
* **Lock-In Depth:** **LOW** (Standard Docker & CLI invocations).

---

## 9. Risk Assessment & Mitigations

* **Risk:** SaaS runner outage impacting release deployments.
  * **Mitigation:** Self-hosted fallback runner infrastructure and local OpenTofu/Helm deployment capability.

---

## 10. Recommended Technology Selection

* **Primary Recommendation:** **GitHub Actions (SaaS / Ephemeral Runners) + ArgoCD (CNCF GitOps)**
* **Alternative Candidate:** **GitLab CI/CD (SaaS / Self-Hosted Runners)**
* **Justification:** GitHub Actions provides native OIDC token federation to eliminate permanent cloud API keys, while ArgoCD delivers pull-based, secure GitOps deployment synchronization inside Kubernetes.

---

## 11. Final Governance Status

Evaluation:
COMPLETE

Recommendation:
GitHub Actions (SaaS / Ephemeral Runners) + ArgoCD (CNCF GitOps)

Governance:
PROPOSED TECHNOLOGY RECOMMENDATION

Approval:
OWNER REVIEW REQUIRED

Technology Approved:
NO

Implementation:
NOT AUTHORIZED
