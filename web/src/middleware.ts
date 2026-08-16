// CineVault OS — Next.js Route Protection Middleware
// Enforces server-side authentication boundaries for protected application pages.

import { NextResponse, type NextRequest } from "next/server";
import {
  SESSION_COOKIE_NAME,
  SessionData,
  decryptSession,
  decryptSessionUnchecked,
  encryptSession,
} from "@/lib/auth/session";
import { exchangeRefreshToken } from "@/lib/auth/keycloak";

const PROTECTED_ROUTES = [
  "/dashboard",
  "/library",
  "/history",
  "/watch-history",
  "/ratings",
  "/collections",
  "/profile",
  "/watchlist",
  "/settings",
];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if requested path requires authentication
  const isProtectedRoute = PROTECTED_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`)
  );

  if (isProtectedRoute) {
    const sessionCookie = request.cookies.get(SESSION_COOKIE_NAME);
    const session = sessionCookie ? await decryptSession(sessionCookie.value) : null;

    if (session) {
      return NextResponse.next();
    }

    // Session is missing, corrupt, or its access token has expired. Before
    // forcing a full re-login, attempt a server-side refresh using the
    // (still potentially valid) refresh_token — P0 fix, Day 1-7 remediation.
    const expiredSession = sessionCookie ? await decryptSessionUnchecked(sessionCookie.value) : null;

    if (expiredSession?.refresh_token) {
      const refreshed = await exchangeRefreshToken(expiredSession.refresh_token);

      if (refreshed) {
        const expiresInMs = (refreshed.expires_in || 3600) * 1000;
        const expiresAt = Date.now() + expiresInMs;
        const newSession: SessionData = {
          access_token: refreshed.access_token,
          refresh_token: refreshed.refresh_token || expiredSession.refresh_token,
          user: expiredSession.user,
          expires_at: expiresAt,
        };

        const response = NextResponse.next();
        const encrypted = await encryptSession(newSession);
        response.cookies.set(SESSION_COOKIE_NAME, encrypted, {
          httpOnly: true,
          secure: process.env.NODE_ENV === "production",
          sameSite: "lax",
          path: "/",
          expires: new Date(expiresAt),
        });
        return response;
      }
    }

    // Refresh not possible or failed — destroy the session and require login.
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("returnTo", pathname);
    const redirectResponse = NextResponse.redirect(loginUrl);
    redirectResponse.cookies.delete(SESSION_COOKIE_NAME);
    return redirectResponse;
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public assets
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
