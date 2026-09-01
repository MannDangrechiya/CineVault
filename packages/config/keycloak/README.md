# Keycloak Realm Configs

## `cinevault-realm-dev.json`
Auto-imported by `infra/docker/docker-compose.yml` (local dev only) via
`start-dev --import-realm`. Contains throwaway dev users and hardcoded
placeholder client secrets (`dev_*_secret_change_me`) — never reuse these
values or this file outside local development.

## `cinevault-realm-prod.template.json`
Starting point for the production realm, used by
`infra/docker/docker-compose.prod.yml`. **Not auto-imported** — the
production `keycloak` service starts with plain `start` (no
`--import-realm`), because a real production realm needs a real domain and
real, randomly-generated client secrets, which is not something safe to bake
into a committed template file or a Docker image env-substitution step.

To bring a production realm up for the first time:

1. Copy the template and substitute your real production domain (must match
   `SITE_ADDRESS` in `.env.prod`) for the `__SITE_ADDRESS__` placeholder:
   ```bash
   sed "s/__SITE_ADDRESS__/${SITE_ADDRESS}/g" \
     packages/config/keycloak/cinevault-realm-prod.template.json \
     > /tmp/cinevault-realm-prod.json
   ```
2. Start the stack (`docker compose -f infra/docker/docker-compose.prod.yml up -d postgres keycloak`),
   then import the rendered realm via the Keycloak Admin Console
   (`https://<KEYCLOAK_HOSTNAME>/admin/`, sign in with
   `KEYCLOAK_ADMIN_USER`/`KEYCLOAK_ADMIN_PASSWORD`) → **Create Realm** →
   **Browse** → select `/tmp/cinevault-realm-prod.json` → **Create**. Or use
   `kcadm.sh create realms -f /tmp/cinevault-realm-prod.json` from inside the
   `keycloak` container.
3. The four confidential service clients (`cinevault-api-gateway`,
   `cinevault-ingest-service`, `cinevault-quality-service`,
   `cinevault-sync-service`) are created with no `secret` in the template —
   Keycloak generates a random one on creation. Copy each generated secret
   from **Clients → *client* → Credentials** into wherever that service
   consumes it; do not hardcode them back into this file.
4. Configure an SMTP relay under **Realm Settings → Email** if you want
   password-reset/verification emails to send — the template ships with no
   SMTP server configured (unlike the dev realm's MailHog wiring).
5. Delete `/tmp/cinevault-realm-prod.json` once imported — it now contains
   your real production domain and should not be left lying around or
   committed.

Once the realm exists, `services/api` and `apps/web` pick it up automatically
via the `KEYCLOAK_ISSUER`/`JWKS_URI`/`KEYCLOAK_HOST`/`NEXT_PUBLIC_KEYCLOAK_URL`
env vars wired in `docker-compose.prod.yml` — no code changes needed for a
new deployment, only a new domain substitution.
