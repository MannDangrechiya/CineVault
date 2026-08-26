// CineVault OS — Next.js BFF Token Refresh Route Handler
// P0 Fix (Day 1-7 remediation): the refresh_token was previously stored in
// the session but never exchanged, so users were silently logged out at
// access-token expiry. This route performs the server-side refresh —
// the refresh_token never leaves the server, and the browser only ever
// sees the encrypted session cookie.

import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import {
  SESSION_COOKIE_NAME,
  SessionData,
  decryptSessionUnchecked,
  encryptSession,
} from "@/lib/auth/session";
import { exchangeRefreshToken } from "@/lib/auth/keycloak";

export async function POST() {
  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get(SESSION_COOKIE_NAME);

  if (!sessionCookie?.value) {
    return NextResponse.json({ error: "No session to refresh." }, { status: 401 });
  }

  // Use the expiry-agnostic decrypt: the whole point of this route is to
  // renew a session whose access_token has already (or is about to) expire.
  const existingSession = await decryptSessionUnchecked(sessionCookie.value);

  if (!existingSession?.refresh_token) {
    cookieStore.delete(SESSION_COOKIE_NAME);
    return NextResponse.json(
      { error: "Session has no refresh token. Please log in again." },
      { status: 401 }
    );
  }

  const refreshed = await exchangeRefreshToken(existingSession.refresh_token);

  if (!refreshed) {
    // Refresh failed (expired/revoked refresh token, Keycloak unreachable, etc.)
    // Destroy the session — do not keep serving the stale/expired tokens.
    cookieStore.delete(SESSION_COOKIE_NAME);
    return NextResponse.json(
      { error: "Session refresh failed. Please log in again." },
      { status: 401 }
    );
  }

  // Same two-expiry split as local-login/route.ts and middleware.ts:
  // `expires_at` inside the session tracks the real (short) access-token
  // lifetime; the cookie's own browser-level `expires` slides forward by
  // the longer window so it's still present to refresh from again later.
  const accessTokenExpiresAt = Date.now() + (refreshed.expires_in || 3600) * 1000;
  const cookieExpiresAt = Date.now() + 7 * 24 * 60 * 60 * 1000;

  const newSession: SessionData = {
    access_token: refreshed.access_token,
    // Keycloak rotates refresh tokens by default; fall back to the existing
    // one only if the response didn't include a new one.
    refresh_token: refreshed.refresh_token || existingSession.refresh_token,
    user: existingSession.user,
    expires_at: accessTokenExpiresAt,
  };

  const encrypted = await encryptSession(newSession);
  cookieStore.set(SESSION_COOKIE_NAME, encrypted, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    expires: new Date(cookieExpiresAt),
  });

  return NextResponse.json({ ok: true, expires_at: accessTokenExpiresAt });
}
