// CineVault OS — Next.js BFF Local & Dev Authentication Route Handler
// Enables seamless local development and demo access without requiring external Keycloak clusters.

import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { encryptSession, SESSION_COOKIE_NAME, SessionData, SessionUser } from "@/lib/auth/session";

interface LocalLoginRequestBody {
  email?: string;
  password?: string;
  role?: "dev_user" | "curator" | "admin";
  returnTo?: string;
}

export async function POST(request: Request) {
  try {
    const body: LocalLoginRequestBody = await request.json().catch(() => ({}));
    const returnTo = body.returnTo && body.returnTo.startsWith("/") && !body.returnTo.startsWith("//")
      ? body.returnTo
      : "/dashboard";

    const email = (body.email || "dev@cinevault.local").toLowerCase().trim();
    const password = body.password || "devpass";
    const selectedRole = body.role || "dev_user";

    let sessionUser: SessionUser = {
      sub: "018f0000-0000-7000-8000-000000000001",
      email: email,
      username: email.split("@")[0],
      roles: ["authenticated_user"],
    };
    let accessToken = `dev_jwt_${sessionUser.username}_${Date.now()}`;
    let refreshToken = `rt_${sessionUser.sub}`;
    // Real token lifetime from the backend, NOT the session cookie's own
    // shelf life -- see the expiresInMs fix below for why conflating the
    // two silently broke every authenticated action after ~24h.
    let tokenExpiresInSeconds = 7 * 24 * 60 * 60;

    // 1. First attempt to authenticate against FastAPI backend /v1/auth/login if online
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
    let backendSuccess = false;

    try {
      const backendRes = await fetch(`${apiBaseUrl}/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
        // Was 1500ms — too aggressive: a cold-started or briefly busy backend
        // (e.g. right after a dev server restart) would miss this window and
        // silently fall back to an unvalidatable synthetic token below, which
        // then made every strictly-authenticated endpoint 401 with no visible
        // error. 8s gives the real backend handshake a fair chance first.
        signal: AbortSignal.timeout(8000),
      });

      if (backendRes.ok) {
        const backendData = await backendRes.json();
        sessionUser = {
          sub: backendData.user_id || "018f0000-0000-7000-8000-000000000001",
          email: backendData.email || email,
          username: (backendData.email || email).split("@")[0],
          roles: backendData.roles || ["authenticated_user"],
        };
        accessToken = backendData.access_token;
        refreshToken = backendData.refresh_token || refreshToken;
        // The real JWT's own `exp` claim is set to this many seconds from
        // now by the backend (86400s / 24h today) -- was previously
        // ignored entirely in favor of a hardcoded 7-day cookie, so the
        // session cookie kept claiming "still valid" for 6 days after the
        // actual access_token inside it had expired. Every authenticated
        // call in that window silently sent a dead token: endpoints
        // requiring auth 401'd, endpoints with an optional-auth fallback
        // silently ran as the anonymous default user instead (a request
        // that looked like it succeeded, but wrote to nobody's real
        // account). The refresh flow in middleware.ts/api/proxy already
        // existed to handle exactly this, but never fired because
        // getSession() never saw the cookie as expired.
        if (typeof backendData.expires_in === "number" && backendData.expires_in > 0) {
          tokenExpiresInSeconds = backendData.expires_in;
        }
        backendSuccess = true;
      }
    } catch {
      // Backend offline or timeout — gracefully proceed to local dev session fallback
      backendSuccess = false;
    }

    // 2. Fallback: Generate local developer session directly in Next.js BFF
    if (!backendSuccess) {
      const roleMap: Record<string, { sub: string; email: string; username: string; roles: string[] }> = {
        dev_user: {
          sub: "018f0000-0000-7000-8000-000000000001",
          email: email || "dev@cinevault.local",
          username: "dev_user",
          roles: ["authenticated_user"],
        },
        curator: {
          sub: "018f0000-0000-7000-8000-000000000002",
          email: email || "curator@cinevault.local",
          username: "curator",
          roles: ["authenticated_user", "curator"],
        },
        admin: {
          sub: "018f0000-0000-7000-8000-000000000003",
          email: email || "admin@cinevault.local",
          username: "system_admin",
          roles: ["authenticated_user", "curator", "system_admin"],
        },
      };

      const preset = roleMap[selectedRole] || roleMap.dev_user;
      sessionUser = {
        sub: preset.sub,
        email: email || preset.email,
        username: email ? email.split("@")[0] : preset.username,
        roles: preset.roles,
      };
      accessToken = `dev_jwt_${sessionUser.username}_${Date.now()}`;
      refreshToken = `rt_${sessionUser.sub}`;
      // No real backend to honor an expiry from in this offline fallback
      // path, and no real refresh endpoint to renew against either --
      // tokenExpiresInSeconds keeps its 7-day default from above.
    }

    // 3. Two separate expiries, deliberately different:
    //   - `expires_at` (inside the encrypted session payload) now tracks the
    //     REAL access token lifetime returned by the backend, instead of
    //     always claiming 7 days regardless of what's actually inside it.
    //     decryptSession() checks this to decide "is my access token still
    //     good", and middleware.ts/api/proxy's refresh logic only fires once
    //     this check goes false.
    //   - the browser cookie's own `expires` attribute stays at the longer
    //     7-day window on purpose: the cookie (and the refresh_token inside
    //     it) must still be PRESENT for decryptSessionUnchecked() to recover
    //     and refresh from, once the access token itself has gone stale at
    //     the shorter window above. Collapsing these into one value was the
    //     bug -- it made the encrypted blob disappear from the browser at
    //     the same moment a refresh should have kicked in, or (as it was
    //     before this fix) let a dead access token keep getting sent for
    //     days because neither expiry ever actually reflected the token.
    const accessTokenExpiresAt = Date.now() + tokenExpiresInSeconds * 1000;
    const cookieMaxAgeMs = 7 * 24 * 60 * 60 * 1000;
    const cookieExpiresAt = Date.now() + cookieMaxAgeMs;

    const session: SessionData = {
      access_token: accessToken,
      refresh_token: refreshToken,
      user: sessionUser,
      expires_at: accessTokenExpiresAt,
    };

    const encryptedSession = await encryptSession(session);
    const cookieStore = await cookies();

    cookieStore.set(SESSION_COOKIE_NAME, encryptedSession, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      expires: new Date(cookieExpiresAt),
    });

    return NextResponse.json({
      success: true,
      user: sessionUser,
      redirectUrl: returnTo,
    });
  } catch (error) {
    console.error("Local login error:", error);
    return NextResponse.json(
      { error: "Authentication failed. Please try again." },
      { status: 500 }
    );
  }
}
