// CineVault OS — Next.js BFF API Proxy Route Handler
//
// The browser never talks to the FastAPI backend directly for authenticated
// calls — `apiFetch` (src/lib/api/client.ts) routes every request through
// here instead. This is the one place allowed to read the real access token
// out of the encrypted HttpOnly session cookie and attach it as a Bearer
// header before forwarding to FastAPI, so the token never has to be exposed
// to client-side JavaScript (see src/app/api/auth/me/route.ts's comment on
// the same boundary). Before this route existed, `apiFetch` called FastAPI
// directly from the browser with no Authorization header at all — every
// `require_authenticated_user` endpoint 401'd, and every `get_optional_claims`
// endpoint silently ran as the anonymous fallback user regardless of who was
// actually logged in.

import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import {
  getSession,
  SESSION_COOKIE_NAME,
  SessionData,
  decryptSessionUnchecked,
  encryptSession,
} from "@/lib/auth/session";
import { exchangeRefreshToken } from "@/lib/auth/keycloak";

function getBackendBaseUrl(): string {
  const url = process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  return url.replace(/\/+$/, "");
}

// Headers that are specific to the hop between browser and this Next.js
// server and must not be forwarded to (request) or from (response) FastAPI.
const HOP_BY_HOP_REQUEST_HEADERS = new Set(["host", "connection", "cookie", "content-length"]);
const HOP_BY_HOP_RESPONSE_HEADERS = new Set([
  "content-encoding",
  "content-length",
  "transfer-encoding",
  "connection",
]);

// Most of the app fetches data client-side (react-query calls straight
// through this proxy) rather than via a fresh page navigation, so
// middleware.ts's refresh-on-expiry logic (which only runs at page-load
// time for a fixed list of routes) never gets a chance to fire for those
// calls — a tab left open past the access token's real lifetime would keep
// sending a dead token to every endpoint this proxy touches, forever,
// until the next full navigation. Attempt the same refresh here, right
// where the token is actually attached, so it's covered no matter how the
// request was triggered. Returns the token to use (possibly freshly
// refreshed) and, if a refresh happened, the new session to persist on the
// outgoing response's cookie.
async function resolveAccessToken(): Promise<{
  accessToken: string | null;
  refreshedSession: SessionData | null;
}> {
  const session = await getSession();
  if (session?.access_token) {
    return { accessToken: session.access_token, refreshedSession: null };
  }

  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get(SESSION_COOKIE_NAME);
  if (!sessionCookie?.value) {
    return { accessToken: null, refreshedSession: null };
  }

  const expiredSession = await decryptSessionUnchecked(sessionCookie.value);
  if (!expiredSession?.refresh_token) {
    return { accessToken: null, refreshedSession: null };
  }

  const refreshed = await exchangeRefreshToken(expiredSession.refresh_token);
  if (!refreshed) {
    return { accessToken: null, refreshedSession: null };
  }

  const accessTokenExpiresAt = Date.now() + (refreshed.expires_in || 3600) * 1000;
  const newSession: SessionData = {
    access_token: refreshed.access_token,
    refresh_token: refreshed.refresh_token || expiredSession.refresh_token,
    user: expiredSession.user,
    expires_at: accessTokenExpiresAt,
  };
  return { accessToken: newSession.access_token, refreshedSession: newSession };
}

async function forward(request: Request, pathSegments: string[]): Promise<NextResponse> {
  // --- CSRF Protection ---
  if (!["GET", "HEAD", "OPTIONS"].includes(request.method)) {
    const origin = request.headers.get("origin");
    const referer = request.headers.get("referer");
    const host = request.headers.get("host");

    let isSafe = false;
    if (origin) {
      try {
        const originUrl = new URL(origin);
        if (originUrl.host === host) isSafe = true;
      } catch {
        // invalid URL format -> not safe
      }
    } else if (referer) {
      try {
        const refererUrl = new URL(referer);
        if (refererUrl.host === host) isSafe = true;
      } catch {
        // invalid URL format -> not safe
      }
    }

    if (!isSafe) {
      return NextResponse.json(
        { error: { code: "FORBIDDEN", message: "CSRF verification failed: Invalid or missing Origin/Referer." } },
        { status: 403 }
      );
    }
  }
  // -----------------------

  const backendBaseUrl = getBackendBaseUrl();
  const targetPath = pathSegments.map(encodeURIComponent).join("/");
  const search = new URL(request.url).search;
  const targetUrl = `${backendBaseUrl}/${targetPath}${search}`;

  const forwardedHeaders = new Headers();
  request.headers.forEach((value, key) => {
    if (!HOP_BY_HOP_REQUEST_HEADERS.has(key.toLowerCase())) {
      forwardedHeaders.set(key, value);
    }
  });

  const { accessToken, refreshedSession } = await resolveAccessToken();
  if (accessToken) {
    forwardedHeaders.set("Authorization", `Bearer ${accessToken}`);
  }

  const hasBody = !["GET", "HEAD", "OPTIONS"].includes(request.method);

  let backendResponse: Response;
  try {
    backendResponse = await fetch(targetUrl, {
      method: request.method,
      headers: forwardedHeaders,
      body: hasBody ? await request.arrayBuffer() : undefined,
      // FastAPI is not the browser's same origin from this server's point of
      // view, but this request is server-to-server — no browser CORS rules
      // apply here, so no `mode`/`credentials` tuning is needed.
    });
  } catch (error) {
    return NextResponse.json(
      {
        error: {
          code: "PROXY_UPSTREAM_UNREACHABLE",
          message: error instanceof Error ? error.message : "Failed to reach the CineVault API server.",
        },
      },
      { status: 502 }
    );
  }

  const responseHeaders = new Headers();
  backendResponse.headers.forEach((value, key) => {
    if (!HOP_BY_HOP_RESPONSE_HEADERS.has(key.toLowerCase())) {
      responseHeaders.set(key, value);
    }
  });

  const responseBody = await backendResponse.arrayBuffer();
  const response = new NextResponse(responseBody, {
    status: backendResponse.status,
    statusText: backendResponse.statusText,
    headers: responseHeaders,
  });

  // If resolveAccessToken() had to refresh, persist the new session now —
  // otherwise every subsequent request keeps hitting the same expired
  // cookie and re-refreshing from scratch instead of reusing this one.
  if (refreshedSession) {
    const encrypted = await encryptSession(refreshedSession);
    response.cookies.set(SESSION_COOKIE_NAME, encrypted, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      expires: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    });
  }

  return response;
}

interface RouteParams {
  params: Promise<{ path: string[] }>;
}

export async function GET(request: Request, { params }: RouteParams) {
  const { path } = await params;
  return forward(request, path);
}

export async function POST(request: Request, { params }: RouteParams) {
  const { path } = await params;
  return forward(request, path);
}

export async function PUT(request: Request, { params }: RouteParams) {
  const { path } = await params;
  return forward(request, path);
}

export async function PATCH(request: Request, { params }: RouteParams) {
  const { path } = await params;
  return forward(request, path);
}

export async function DELETE(request: Request, { params }: RouteParams) {
  const { path } = await params;
  return forward(request, path);
}

export async function OPTIONS(request: Request, { params }: RouteParams) {
  const { path } = await params;
  return forward(request, path);
}
