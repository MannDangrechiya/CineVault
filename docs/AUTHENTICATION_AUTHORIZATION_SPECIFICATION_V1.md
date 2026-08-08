# CineVault OS — Authentication & Authorization Specification V1 (Phase 2)

**Document Type:** Security & Authentication Infrastructure Specification  
**Status:** IMPLEMENTED & VALIDATED  
**Phase:** 2 — Authentication & Authorization  
**Date:** 2026-08-08  
**Approved Security Stack:** Keycloak (Self-Hosted OIDC Server), OAuth 2.1 / OIDC (Authorization Code + PKCE S256), RS256 JWKS Validation, WebAuthn Hybrid MFA  

---

## 1. Overview & Architectural Boundaries

The **CineVault OS Authentication & Authorization Foundation** implements the approved security architecture (`docs/SECURITY_ARCHITECTURE_V1.md`) and authentication decisions (`DEC-API-DEF-02`, `DEC-SEC-OPN-01`).

### Core Architectural Invariants Enforced
1. **Keycloak Authentication Boundary:** Keycloak is the authentication provider (`OIDC Issuer`). Keycloak MUST NOT store domain relationships or become the CineVault catalog database.
2. **Authorization Code + PKCE S256:** All public web and mobile clients authenticate via PKCE S256 (`code_challenge_method=S256`). Implicit flow and embedded client secrets are strictly prohibited for public clients.
3. **CineVault Human RBAC:** Identity tokens map to CineVault application-owned roles (`Anonymous`, `AuthenticatedUser`, `Curator`, `SystemAdmin`).
4. **Service Identity Isolation:** Machine workloads (`cinevault-ingest-service`, `cinevault-quality-service`) authenticate via short-lived OIDC service account tokens. The ingestion service is strictly prohibited from writing directly to the `canonical` PostgreSQL schema.
5. **Privileged Session Timeout (DEC-SEC-PRP-10):** Control Room Curator privileged sessions enforce a strict **15-minute** idle timeout (`CURATOR_SESSION_IDLE_TIMEOUT_SECONDS = 900`).
6. **High-Risk Fresh WebAuthn Guard (DEC-SEC-OPN-01):** High-risk operations (entity merge, entity split, role promotion, personal-data dispute resolution, credential/key operations, security configuration changes) require fresh WebAuthn/FIDO2 hardware key authentication within a **60-second** window (`HIGH_RISK_FRESH_AUTH_WINDOW_SECONDS = 60`). **TOTP is strictly prohibited** for high-risk operations.
7. **Personal Data Isolation (ADR-003):** JWT tokens contain zero `CAT-2` personal user metadata.

---

## 2. Keycloak Development Realm & Client Setup

* **Realm Name:** `cinevault-dev` ([cinevault-realm-dev.json](file:///c:/Desktop/flutter_projects/CineVault/config/keycloak/cinevault-realm-dev.json))
* **Issuer URL:** `http://localhost:8080/realms/cinevault-dev`
* **JWKS Certs Endpoint:** `http://localhost:8080/realms/cinevault-dev/protocol/openid-connect/certs`

### Configured Development Clients
1. `cinevault-public-client`: Public SPA / Flutter App client (`publicClient: true`, `PKCE S256`, Redirect URIs: `http://localhost:3000/*`, `http://localhost:8000/*`).
2. `cinevault-api-gateway`: Confidential Kong Gateway service client (`serviceAccountsEnabled: true`).
3. `cinevault-ingest-service`: Ingestion worker service client (`serviceAccountsEnabled: true`, Role: `ingestion_write`).
4. `cinevault-quality-service`: Quality engine worker service client (`serviceAccountsEnabled: true`, Role: `quality_write`).
5. `cinevault-sync-service`: Offline sync worker service client (`serviceAccountsEnabled: true`, Role: `sync_write`).

---

## 3. Synthetic Development Users

| Username | Email | Assigned Roles | Use Case |
|---|---|---|---|
| `dev_user` | `dev_user@cinevault.local` | `AuthenticatedUser` | Standard library, watch log, rating operations |
| `dev_curator` | `dev_curator@cinevault.local` | `AuthenticatedUser`, `Curator` | Evidence reconciliation & moderation queue |
| `dev_admin` | `dev_admin@cinevault.local` | `AuthenticatedUser`, `Curator`, `SystemAdmin` | System administration & break-glass framework |

---

## 4. OIDC Token Validator & Security Policy Engine

### Core Components Implemented
* [jwt_validator.py](file:///c:/Desktop/flutter_projects/CineVault/services/api/auth/jwt_validator.py): Decodes OIDC JWT headers/payloads, validates issuer, audience, expiration (`exp`), not-before (`nbf`), and verifies RS256 JWKS public key signatures.
* [rbac.py](file:///c:/Desktop/flutter_projects/CineVault/services/api/auth/rbac.py): Enforces CineVault RBAC roles, PKCE S256 verifier calculation, 15-minute curator session idle timeout guard, and 60-second fresh WebAuthn high-risk operation enforcement (with explicit TOTP rejection).

---

## 5. Validation & Test Executable Commands

```powershell
# Run PowerShell authentication foundation audit
powershell -ExecutionPolicy Bypass -File .\scripts\validate-auth-foundation.ps1

# Run Python security unit test suite directly
python -m unittest tests/test_authentication_authorization.py
```
