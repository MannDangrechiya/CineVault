// CineVault OS — Master API Client Utility

import { APIClientError, APIErrorResponse } from "./types";

// Every call is routed through the Next.js BFF proxy (src/app/api/proxy/[...path]/route.ts)
// rather than hitting the FastAPI backend directly. The proxy runs server-side, where it can
// read the real access token out of the encrypted HttpOnly session cookie and attach it as a
// Bearer header — the browser itself never has the token, so apiFetch has nothing to attach.
// Calling FastAPI directly from here would (and previously did) send every request with no
// auth at all, silently degrading every endpoint to its anonymous/unauthenticated fallback.
const PROXY_BASE_PATH = "/api/proxy";

export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const url = `${PROXY_BASE_PATH}${cleanEndpoint}`;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...options.headers,
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status} ${response.statusText}`;
      let errorCode: string | undefined;
      let correlationId: string | undefined;

      try {
        const errorData: APIErrorResponse = await response.json();
        if (errorData?.error) {
          errorMessage = errorData.error.message || errorMessage;
          errorCode = errorData.error.code;
          correlationId = errorData.error.correlation_id;
        }
      } catch {
        // Fallback to text if JSON parsing fails
      }

      throw new APIClientError(errorMessage, response.status, errorCode, correlationId);
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof APIClientError) {
      throw error;
    }
    throw new APIClientError(
      error instanceof Error ? error.message : "Failed to connect to CineVault API server.",
      0
    );
  }
}
