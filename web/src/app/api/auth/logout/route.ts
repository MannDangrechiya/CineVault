// CineVault OS — Next.js BFF Logout Route Handler
// Invalidates the CineVault web session, clears HttpOnly cookies,
// and redirects user to public home page or Keycloak end-session endpoint.

import { NextResponse } from "next/server";
import { SESSION_COOKIE_NAME } from "@/lib/auth/session";

export async function GET() {
  return performLogout();
}

export async function POST() {
  return performLogout();
}

function performLogout() {
  const appBaseUrl = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";
  const keycloakHost = process.env.KEYCLOAK_HOST || "http://localhost:8080";
  const realm = process.env.KEYCLOAK_REALM || "cinevault-dev";

  // Keycloak OIDC end-session endpoint
  const logoutUrl = `${keycloakHost}/realms/${realm}/protocol/openid-connect/logout?post_logout_redirect_uri=${encodeURIComponent(appBaseUrl)}`;

  const response = NextResponse.redirect(logoutUrl);

  // Destroy session cookie
  response.cookies.delete(SESSION_COOKIE_NAME);
  response.cookies.delete("cv_pkce_verifier");
  response.cookies.delete("cv_oauth_state");
  response.cookies.delete("cv_return_to");

  return response;
}
