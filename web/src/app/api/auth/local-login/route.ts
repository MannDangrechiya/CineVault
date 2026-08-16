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

    // 1. First attempt to authenticate against FastAPI backend /v1/auth/login if online
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
    let backendSuccess = false;

    try {
      const backendRes = await fetch(`${apiBaseUrl}/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
        signal: AbortSignal.timeout(1500),
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
    }

    // 3. Establish 7-day session cookie
    const expiresInMs = 7 * 24 * 60 * 60 * 1000;
    const expiresAt = Date.now() + expiresInMs;

    const session: SessionData = {
      access_token: accessToken,
      refresh_token: `rt_${sessionUser.sub}`,
      user: sessionUser,
      expires_at: expiresAt,
    };

    const encryptedSession = encryptSession(session);
    const cookieStore = await cookies();

    cookieStore.set(SESSION_COOKIE_NAME, encryptedSession, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      expires: new Date(expiresAt),
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
