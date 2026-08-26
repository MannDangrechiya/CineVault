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
import { getSession } from "@/lib/auth/session";

function getBackendBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
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

async function forward(request: Request, pathSegments: string[]): Promise<NextResponse> {
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

  const session = await getSession();
  if (session?.access_token) {
    forwardedHeaders.set("Authorization", `Bearer ${session.access_token}`);
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
  return new NextResponse(responseBody, {
    status: backendResponse.status,
    statusText: backendResponse.statusText,
    headers: responseHeaders,
  });
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
