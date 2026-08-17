// CineVault OS — Next.js BFF Login Initiator Route Handler
// Generates PKCE S256 code challenge & state, stores state in HttpOnly cookies,
// and redirects browser to Keycloak Authorization Endpoint.

import { NextResponse } from "next/server";
import { generateCodeVerifier, generateCodeChallenge, generateState } from "@/lib/auth/pkce";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const returnTo = url.searchParams.get("returnTo") || "/dashboard";

  const keycloakHost = process.env.NEXT_PUBLIC_KEYCLOAK_URL || "http://localhost:8080";
  const realm = process.env.KEYCLOAK_REALM || "cinevault-dev";
  const clientId = process.env.KEYCLOAK_CLIENT_ID || "cinevault-public-client";
  const appBaseUrl = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";

  const redirectUri = `${appBaseUrl}/api/auth/callback`;

  // Generate PKCE credentials & state
  const verifier = generateCodeVerifier();
  const challenge = generateCodeChallenge(verifier);
  const state = generateState();

  const authUrl = new URL(`${keycloakHost}/realms/${realm}/protocol/openid-connect/auth`);
  authUrl.searchParams.set("client_id", clientId);
  authUrl.searchParams.set("response_type", "code");
  authUrl.searchParams.set("redirect_uri", redirectUri);
  authUrl.searchParams.set("scope", "openid profile email");
  authUrl.searchParams.set("state", state);
  authUrl.searchParams.set("code_challenge", challenge);
  authUrl.searchParams.set("code_challenge_method", "S256");

  const response = NextResponse.redirect(authUrl.toString());

  // Store verifier, state, and returnTo in short-lived HttpOnly cookies (10 mins)
  const isProd = process.env.NODE_ENV === "production";
  const cookieOptions = {
    httpOnly: true,
    secure: isProd,
    sameSite: "lax" as const,
    path: "/",
    maxAge: 600, // 10 minutes
  };

  response.cookies.set("cv_pkce_verifier", verifier, cookieOptions);
  response.cookies.set("cv_oauth_state", state, cookieOptions);
  response.cookies.set("cv_return_to", returnTo, cookieOptions);

  return response;
}
