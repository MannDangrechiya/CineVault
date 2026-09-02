// CineVault OS — Startup Configuration Validation
// Next.js calls register() once when a new server instance boots (both the
// Node.js runtime and, separately, the Edge runtime used by middleware.ts —
// hence the NEXT_RUNTIME guard below so this only runs once per process).
// This is the fail-closed check for SESSION_SECRET: without it, the BFF
// session cookie (see lib/auth/session.ts) would silently be signed with a
// hardcoded, publicly-known development default in production.
//
// Verified against the actual built/running image (R1 hardening pass): a
// plain `throw` here is NOT enough — Next.js's standalone server.js catches
// whatever register() throws, logs "Failed to prepare server Error: ...",
// and then keeps booting and serving traffic anyway. That's the opposite of
// fail-closed. process.exit(1) is what actually stops the process, matching
// the same fail-closed guarantee services/api/config.py's insecure-default
// validator gets for free (an uncaught exception at Python import time) and
// the required (":?") secrets in infra/docker/docker-compose.prod.yml.
export function register() {
  if (process.env.NEXT_RUNTIME !== "nodejs") {
    return;
  }

  if (process.env.NODE_ENV === "production" && !process.env.SESSION_SECRET) {
    // eslint-disable-next-line no-console -- startup fatal, must reach container logs
    console.error(
      "FATAL: SESSION_SECRET must be set in production — refusing to start without a real " +
        "session-signing secret. Generate one with e.g. `openssl rand -base64 48` and set " +
        "it in the production environment (see infra/docker/docker-compose.prod.yml)."
    );
    process.exit(1);
  }
}
