// CineVault OS — Master API Client Utility

import { APIClientError, APIErrorResponse } from "./types";

const getBaseUrl = (): string => {
  const url = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (url) {
    return url.replace(/\/+$/, "");
  }
  return "http://localhost:8000";
};

export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getBaseUrl();
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const url = `${baseUrl}${cleanEndpoint}`;

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
