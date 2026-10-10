// CineVault OS — Access Token Refresh Helper
// Redeems a refresh_token for a new access_token against the native FastAPI
// backend. Used by the /api/auth/refresh route, the proxy route, and
// middleware. Pure — no cookie access here, so it can run from middleware as
// well as route handlers.
//
// Phase 3 infrastructure consolidation: this used to also fall back to a
// real Keycloak OIDC token endpoint for tokens issued via the (now removed)
// Keycloak login flow. Native login is the only auth path left, so that
// fallback — and the Keycloak-only "local-dev token" special case it
// existed alongside — were removed along with it.

export interface TokenRefreshResult {
  access_token: string;
  refresh_token?: string;
  expires_in?: number;
}

/**
 * Exchanges a refresh_token for a new access_token (and, typically, a
 * rotated refresh_token) via FastAPI's native /v1/auth/refresh endpoint.
 *
 * Returns null on any failure (expired/revoked refresh token, network
 * error, malformed response) — callers must treat null as "refresh failed,
 * destroy the session and require login," never as "keep the old tokens."
 */
export async function exchangeRefreshToken(
  refreshToken: string
): Promise<TokenRefreshResult | null> {
  const apiBaseUrl = process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

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
