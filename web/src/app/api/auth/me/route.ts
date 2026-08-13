// CineVault OS — Next.js BFF Current User Route Handler
// Returns safe user identity information from the HttpOnly session cookie.
// Does NOT expose access tokens or refresh tokens to client-side JavaScript.

import { NextResponse } from "next/server";
import { getSession } from "@/lib/auth/session";

export async function GET() {
  const session = await getSession();

  if (!session) {
    return NextResponse.json(
      { authenticated: false, user: null },
      { status: 401 }
    );
  }

  return NextResponse.json({
    authenticated: true,
    user: session.user,
  });
}
