// CineVault OS — Shared Keycloak Token-Endpoint Helper
// Used by both the callback route (authorization_code exchange) and the
// refresh route / middleware (refresh_token exchange). Pure — no cookie
// access here, so it can run from middleware as well as route handlers.

export interface KeycloakTokenResult {
  access_token: string;
  refresh_token?: string;
  expires_in?: number;
}

function tokenEndpoint(): string {
  const keycloakHost = process.env.KEYCLOAK_HOST || "http://localhost:8080";
  const realm = process.env.KEYCLOAK_REALM || "cinevault-dev";
  return `${keycloakHost}/realms/${realm}/protocol/openid-connect/token`;
}

/**
 * Local-dev refresh tokens are minted by services/api/routers/auth.py's
 * /v1/auth/login as an opaque `rt_local_{user_id}_{issued_at}` string, not
 * a real Keycloak-issued token -- real Keycloak has been down in this
 * environment (`docker ps` shows it Exited days ago), and even when it's
 * up, local-dev logins never went through it in the first place (see
 * local-login/route.ts). Redeeming one of these against the real Keycloak
 * token endpoint would always fail; redeem it against the matching local
 * backend endpoint instead.
 */
function isLocalDevRefreshToken(refreshToken: string): boolean {
  return refreshToken.startsWith("rt_local_");
}

async function exchangeLocalDevRefreshToken(
  refreshToken: string
): Promise<KeycloakTokenResult | null> {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  try {
    const response = await fetch(`${apiBaseUrl}/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
      signal: AbortSignal.timeout(8000),
    });

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    if (!data.access_token) {
      return null;
    }

    return {
      access_token: data.access_token,
      refresh_token: data.refresh_token,
      expires_in: data.expires_in,
    };
  } catch {
    return null;
  }
}

/**
 * Exchanges a refresh_token for a new access_token (and, typically, a
 * rotated refresh_token). Local-dev tokens go to the FastAPI backend's own
 * /v1/auth/refresh; anything else goes to Keycloak's real OIDC token
 * endpoint, for staging/production where Keycloak is the real IdP.
 *
 * Returns null on any failure (expired/revoked refresh token, network
 * error, malformed response) — callers must treat null as "refresh failed,
 * destroy the session and require login," never as "keep the old tokens."
 */
export async function exchangeRefreshToken(
  refreshToken: string
): Promise<KeycloakTokenResult | null> {
  if (isLocalDevRefreshToken(refreshToken)) {
    return exchangeLocalDevRefreshToken(refreshToken);
  }

  const clientId = process.env.KEYCLOAK_CLIENT_ID || "cinevault-public-client";

  const params = new URLSearchParams({
    grant_type: "refresh_token",
    client_id: clientId,
    refresh_token: refreshToken,
  });

  try {
    const response = await fetch(tokenEndpoint(), {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: params.toString(),
    });

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    if (!data.access_token) {
      return null;
    }

    return {
      access_token: data.access_token,
      refresh_token: data.refresh_token,
      expires_in: data.expires_in,
    };
  } catch {
    return null;
  }
}
