// CineVault OS — Next.js BFF Logout Route Handler
// Invalidates the CineVault web session, clears HttpOnly cookies,
// and redirects user to login page or public home.

import { NextResponse } from "next/server";
import { SESSION_COOKIE_NAME } from "@/lib/auth/session";

export async function GET() {
  return performLogout();
}

export async function POST() {
  return performLogout();
}

function performLogout() {
  const appBaseUrl = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";
  const response = NextResponse.redirect(`${appBaseUrl}/login?logged_out=1`);

  // Destroy session cookie and any OAuth state cookies
  response.cookies.delete(SESSION_COOKIE_NAME);
  response.cookies.delete("cv_pkce_verifier");
  response.cookies.delete("cv_oauth_state");
  response.cookies.delete("cv_return_to");

  return response;
}
