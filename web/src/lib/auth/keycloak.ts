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
 * Exchanges a refresh_token for a new access_token (and, typically, a
 * rotated refresh_token) via Keycloak's OIDC token endpoint.
 *
 * Returns null on any failure (expired/revoked refresh token, network
 * error, malformed response) — callers must treat null as "refresh failed,
 * destroy the session and require login," never as "keep the old tokens."
 */
export async function exchangeRefreshToken(
  refreshToken: string
): Promise<KeycloakTokenResult | null> {
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
