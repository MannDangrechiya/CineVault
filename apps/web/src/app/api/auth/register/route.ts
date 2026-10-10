// CineVault OS — Next.js BFF User Registration Route Handler
// Implements Phase 1 Invite-Gated Registration for Web Clients

import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { encryptSession, SESSION_COOKIE_NAME, SessionData, SessionUser } from "@/lib/auth/session";

interface RegisterRequestBody {
  email?: string;
  password?: string;
  invite_code?: string;
  returnTo?: string;
}

export async function POST(request: Request) {
  try {
    const body: RegisterRequestBody = await request.json().catch(() => ({}));
    const returnTo =
      body.returnTo && body.returnTo.startsWith("/") && !body.returnTo.startsWith("//")
        ? body.returnTo
        : "/dashboard";

    const email = (body.email || "").toLowerCase().trim();
    const password = body.password || "";
    const invite_code = (body.invite_code || "").trim();

    if (!email || !password || !invite_code) {
      return NextResponse.json(
        { success: false, error: "Email, password, and invite code are all required." },
        { status: 400 }
      );
    }

    const apiBaseUrl =
      process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

    const backendRes = await fetch(`${apiBaseUrl}/v1/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, invite_code }),
      signal: AbortSignal.timeout(8000),
    });

    if (!backendRes.ok) {
      const errorData = await backendRes.json().catch(() => ({}));
      return NextResponse.json(
        {
          success: false,
          error: errorData.detail || "Registration failed. Please verify your invite code.",
        },
        { status: backendRes.status }
      );
    }

    const backendData = await backendRes.json();
    const sessionUser: SessionUser = {
      sub: backendData.user_id,
      email: backendData.email || email,
      username: (backendData.email || email).split("@")[0],
      roles: backendData.roles || ["authenticated_user"],
    };

    const tokenExpiresInSeconds = backendData.expires_in || 86400;
    const accessTokenExpiresAt = Date.now() + tokenExpiresInSeconds * 1000;
    const cookieExpiresAt = Date.now() + 7 * 24 * 60 * 60 * 1000;

    const session: SessionData = {
      access_token: backendData.access_token,
      refresh_token: backendData.refresh_token,
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
    console.error("Registration route error:", error);
    return NextResponse.json(
      { error: "Unable to connect to authentication service." },
      { status: 503 }
    );
  }
}
