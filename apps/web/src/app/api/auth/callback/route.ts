// CineVault OS — Next.js BFF OAuth Callback Route Handler
// Validates state & PKCE verifier, performs server-side token exchange with Keycloak,
// verifies identity with FastAPI /v1/auth/me, and establishes secure HttpOnly session.

import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { encryptSession, SESSION_COOKIE_NAME, SessionData, SessionUser } from "@/lib/auth/session";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const error = url.searchParams.get("error");
  const errorDescription = url.searchParams.get("error_description");

  const appBaseUrl = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";

  // Check for Keycloak authorization error
  if (error) {
    console.error("Keycloak authorization error:", error, errorDescription);
    return NextResponse.redirect(`${appBaseUrl}/login?error=${encodeURIComponent(errorDescription || error)}`);
  }

  if (!code || !state) {
    return NextResponse.redirect(`${appBaseUrl}/login?error=${encodeURIComponent("Missing authorization code or state parameter.")}`);
  }

  const cookieStore = await cookies();
  const storedState = cookieStore.get("cv_oauth_state")?.value;
  const verifier = cookieStore.get("cv_pkce_verifier")?.value;
  const rawReturnTo = cookieStore.get("cv_return_to")?.value || "/dashboard";

  // Allowlist returnTo parameter to prevent open redirect vulnerabilities
  const returnTo = rawReturnTo.startsWith("/") && !rawReturnTo.startsWith("//") ? rawReturnTo : "/dashboard";

  // Validate CSRF state match
  if (!storedState || storedState !== state) {
    console.error("OAuth state mismatch error");
    return NextResponse.redirect(`${appBaseUrl}/login?error=${encodeURIComponent("Invalid OAuth state. Potential CSRF attempt.")}`);
  }

  if (!verifier) {
    console.error("Missing PKCE code_verifier cookie");
    return NextResponse.redirect(`${appBaseUrl}/login?error=${encodeURIComponent("PKCE session expired or invalid. Please try logging in again.")}`);
  }

  const keycloakHost = process.env.KEYCLOAK_HOST || "http://localhost:8080";
  const realm = process.env.KEYCLOAK_REALM || "cinevault-dev";
  const clientId = process.env.KEYCLOAK_CLIENT_ID || "cinevault-public-client";
  const redirectUri = `${appBaseUrl}/api/auth/callback`;

  // Server-side Token Exchange with Keycloak
  const tokenEndpoint = `${keycloakHost}/realms/${realm}/protocol/openid-connect/token`;

  const tokenParams = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: clientId,
    code: code,
    redirect_uri: redirectUri,
    code_verifier: verifier,
  });

  let tokenData: { access_token: string; refresh_token?: string; expires_in?: number };
  try {
    const tokenResponse = await fetch(tokenEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: tokenParams.toString(),
    });

    if (!tokenResponse.ok) {
      const errorText = await tokenResponse.text();
      console.error("Keycloak token exchange failed:", tokenResponse.status, errorText);
      return NextResponse.redirect(`${appBaseUrl}/login?error=${encodeURIComponent("Failed to exchange authorization code with Keycloak.")}`);
    }

    tokenData = await tokenResponse.json();
  } catch (err) {
    console.error("Failed to connect to Keycloak token endpoint:", err);
    return NextResponse.redirect(`${appBaseUrl}/login?error=${encodeURIComponent("Identity server unreachable.")}`);
  }

  // Retrieve user identity from FastAPI /v1/auth/me using access token.
  //
  // P0 Fix (Day 1-7 remediation): this previously fell back to parsing the
  // access token's JWT payload WITHOUT verifying its signature whenever
  // /v1/auth/me failed, and trusted whatever `roles` it found there. That
  // let an unverified claim set (including system_admin) install itself
  // into the encrypted session. The FastAPI endpoint is the only place
  // that verifies signature/issuer/audience/expiry — if it doesn't return
  // a verified identity, authentication has failed and no session may be
  // created. The user must retry login instead.
  const apiBaseUrl = process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
  let user: SessionUser;

  const failAuthentication = (reason: string) => {
    console.error("Authentication failed at /v1/auth/me verification step:", reason);
    const response = NextResponse.redirect(
      `${appBaseUrl}/login?error=${encodeURIComponent("Could not verify your identity. Please sign in again.")}`
    );
    response.cookies.delete("cv_pkce_verifier");
    response.cookies.delete("cv_oauth_state");
    response.cookies.delete("cv_return_to");
    return response;
  };

  try {
    const meResponse = await fetch(`${apiBaseUrl}/v1/auth/me`, {
      headers: {
        Authorization: `Bearer ${tokenData.access_token}`,
        Accept: "application/json",
      },
    });

    if (!meResponse.ok) {
      return failAuthentication(`/v1/auth/me returned ${meResponse.status}`);
    }

    const meData = await meResponse.json();
    user = {
      sub: meData.sub,
      email: meData.email,
      username: meData.username,
      roles: meData.roles || ["authenticated_user"],
    };
  } catch (err) {
    return failAuthentication(`/v1/auth/me request threw: ${err}`);
  }

  // Establish Session
  const expiresInMs = (tokenData.expires_in || 3600) * 1000;
  const expiresAt = Date.now() + expiresInMs;

  const session: SessionData = {
    access_token: tokenData.access_token,
    refresh_token: tokenData.refresh_token,
    user,
    expires_at: expiresAt,
  };

  const encryptedSession = await encryptSession(session);

  const redirectResponse = NextResponse.redirect(`${appBaseUrl}${returnTo}`);

  // Set secure HttpOnly session cookie
  redirectResponse.cookies.set(SESSION_COOKIE_NAME, encryptedSession, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    expires: new Date(expiresAt),
  });

  // Clear PKCE temporary state cookies
  redirectResponse.cookies.delete("cv_pkce_verifier");
  redirectResponse.cookies.delete("cv_oauth_state");
  redirectResponse.cookies.delete("cv_return_to");

  return redirectResponse;
}
