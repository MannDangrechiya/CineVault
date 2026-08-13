// CineVault OS — Next.js Route Protection Middleware
// Enforces server-side authentication boundaries for protected application pages.

import { NextResponse, type NextRequest } from "next/server";
import { SESSION_COOKIE_NAME, decryptSession } from "@/lib/auth/session";

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

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if requested path requires authentication
  const isProtectedRoute = PROTECTED_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`)
  );

  if (isProtectedRoute) {
    const sessionCookie = request.cookies.get(SESSION_COOKIE_NAME);
    const session = sessionCookie ? decryptSession(sessionCookie.value) : null;

    if (!session) {
      // Redirect unauthenticated user to login with returnTo parameter
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("returnTo", pathname);
      return NextResponse.redirect(loginUrl);
    }
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
