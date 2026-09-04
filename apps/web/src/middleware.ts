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
import { exchangeRefreshToken } from "@/lib/auth/token-refresh";

// Was missing most of the app (movies, series, social, clubs, friends,
// oracle, import, pick) -- pages outside this list never got a chance at
// the refresh-on-expiry logic below at page-load time, only the handful
// listed here did. The underlying data still comes from client-side calls
// through /api/proxy either way, but this list is what decides whether a
// stale session gets refreshed (or bounced to /login) BEFORE a page
// renders, versus silently rendering with a dead token and only failing
// once something tries to fetch.
const PROTECTED_ROUTES = [
  "/dashboard",
  "/oracle",
  "/movies",
  "/series",
  "/social",
  "/clubs",
  "/library",
  "/watchlist",
  "/history",
  "/watch-history",
  "/ratings",
  "/collections",
  "/import",
  "/friends",
  // NOT /pick -- POST /social/pick-rooms/{slug}/vote intentionally allows
  // guest voting (get_optional_claims, no auth required), so forcing a
  // login redirect there would break that supported flow.
  "/profile",
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
        // Same two-expiry split as local-login/route.ts: `expires_at` inside
        // the session tracks the real (short) access-token lifetime so the
        // next decryptSession() check fires another refresh at the right
        // time; the cookie's own browser-level `expires` slides forward by
        // the longer window so it's still present in the browser to refresh
        // from again next time, rather than the two being collapsed into
        // one value (the original bug -- see that file for the full story).
        const accessTokenExpiresAt = Date.now() + (refreshed.expires_in || 3600) * 1000;
        const cookieExpiresAt = Date.now() + 7 * 24 * 60 * 60 * 1000;
        const newSession: SessionData = {
          access_token: refreshed.access_token,
          refresh_token: refreshed.refresh_token || expiredSession.refresh_token,
          user: expiredSession.user,
          expires_at: accessTokenExpiresAt,
        };

        const response = NextResponse.next();
        const encrypted = await encryptSession(newSession);
        response.cookies.set(SESSION_COOKIE_NAME, encrypted, {
          httpOnly: true,
          secure: process.env.NODE_ENV === "production",
          sameSite: "lax",
          path: "/",
          expires: new Date(cookieExpiresAt),
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
