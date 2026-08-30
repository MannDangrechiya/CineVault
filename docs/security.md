# CineVault OS — Security & Threat Modeling Specification (W11)

## 1. Authentication & JWT Hardening
- **Zero-Trust Token Validation**: All incoming requests to protected routes (/v1/personal/*, /admin/*, /internal/v1/control-room/*, /automations/*) require valid OAuth2 / OIDC Bearer tokens.
- **Algorithm Enforcement**: Rejects \lg=none\ and symmetric mock signatures in staging/production environments. Cryptographic RS256 validation executes against Keycloak JWKS endpoints.
- **Token Claims Verification**: Issuer (\iss\), Audience (\ud\), Expiration (\exp\), and Subject (\sub\) strictly verified before granting request context.

## 2. Role-Based Access Control (RBAC) & Service Isolation
- **Human RBAC Roles**:
  - \AuthenticatedUser\: Access to personal library, history, watchlist, notes, ratings, reviews, collections, exports, imports, and social circle.
  - \Curator\: Access to \/internal/v1/control-room/*\ (candidate triage, quarantine resolution, audit inspection).
  - \SystemAdmin\: Access to administrative sync endpoints (\/admin/*\) and high-risk system operations.
- **Machine Service Isolation**: Enforces zero-trust isolation boundaries across internal services:
  - Ingestion / AI Proposal services are strictly prohibited from direct write mutations to \canonical\ schema.
  - Analytics service has zero access to \personal\ (CAT-2) schema data.
  - Public API nodes cannot execute internal administrative actions.

## 3. IDOR Defense Across All Resources
- All personal data queries derive \user_id\ exclusively from verified JWT claims (\claims.sub\). No user-spoofed path or query parameter can access, mutate, or export another user's personal media records.
- Social resources (friendships, recommendations, watch club memberships, pick room votes) enforce strict participant authorization before state transitions or deletions.

## 4. Next.js BFF Proxy CSRF Protection
- \pps/web/src/app/api/proxy/[...path]/route.ts\ intercepts all state-changing HTTP methods (\POST\, \PUT\, \PATCH\, \DELETE\).
- Validates \Origin\ and \Referer\ headers against \Host\ to block cross-site request forgery attacks.
- Missing or mismatched origins on mutation requests receive immediate \403 Forbidden\.

## 5. Defense-in-Depth Protections
- **Formula Injection Defense**: All exported CSV and XLSX files sanitize leading formula triggers (\=\, \+\, \-\, \@\, \\t\, \\r\) with single-quote escaping.
- **SQL Injection Defense**: Dynamic queries use parameterized SQLAlchemy ORM statements.
- **Security Headers**: Standard production headers enforced on all responses (\X-Content-Type-Options: nosniff\, \X-Frame-Options: DENY\, \Strict-Transport-Security: max-age=31536000\, \Content-Security-Policy: default-src 'self'\).
- **CAT-6 AI Governance**: AI proposal metadata is staged in \quality.ai_proposal_staging\ with status \PENDING\ and HMAC SHA-256 integrity signatures, requiring human curator review before canonical promotion.
