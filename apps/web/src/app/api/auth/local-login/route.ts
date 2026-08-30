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
    const apiBaseUrl = process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

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
        if (typeof backendData.expires_in === "number" && backendData.expires_in > 0) {
          tokenExpiresInSeconds = backendData.expires_in;
        }
      } else {
        const errorData = await backendRes.json().catch(() => ({}));
        return NextResponse.json(
          {
            success: false,
            error: errorData.detail || "Invalid email or password. Please check your credentials.",
          },
          { status: backendRes.status }
        );
      }
    } catch {
      return NextResponse.json(
        {
          success: false,
          error: "Unable to connect to authentication service. Please ensure API server is running.",
        },
        { status: 503 }
      );
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
