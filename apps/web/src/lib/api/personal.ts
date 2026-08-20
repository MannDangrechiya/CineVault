import { apiFetch } from "./client";
import { TitleDetail } from "./types";

export interface WatchlistStateResponse {
  in_watchlist: boolean;
  status: string;
}

export interface WatchlistItem {
  id: string;
  title_id: string;
  added_at: string;
  title: TitleDetail; // assuming populated by backend
}

export interface RecommendationItem {
  id: string;
  sender_id: string;
  sender_name: string;
  title_id: string;
  title: TitleDetail; // assuming populated by backend
  message?: string;
  status: "pending" | "accepted" | "dismissed";
  sent_at: string;
}

// ── Watchlist ─────────────────────────────────────────────────────────────

export async function toggleWatchlistState(
  titleId: string,
  inWatchlist: boolean
): Promise<WatchlistStateResponse> {
  return await apiFetch<WatchlistStateResponse>(`/v1/personal/titles/${encodeURIComponent(titleId)}/state`, {
    method: "PATCH", // or POST depending on backend
    body: JSON.stringify({ in_watchlist: inWatchlist }),
  });
}

export async function getWatchlist(): Promise<WatchlistItem[]> {
  return await apiFetch<WatchlistItem[]>("/v1/personal/watchlist");
}

export async function removeFromWatchlist(titleId: string): Promise<void> {
  await apiFetch(`/v1/personal/titles/${encodeURIComponent(titleId)}/state`, {
    method: "PATCH",
    body: JSON.stringify({ in_watchlist: false }),
  });
}

// ── Social Recommendations ────────────────────────────────────────────────

export async function sendRecommendation(
  titleId: string,
  recipientId: string,
  message?: string
): Promise<void> {
  await apiFetch("/v1/social/recommendations", {
    method: "POST",
    body: JSON.stringify({
      title_id: titleId,
      recipient_id: recipientId,
      message,
    }),
  });
}

export async function getRecommendations(): Promise<RecommendationItem[]> {
  return await apiFetch<RecommendationItem[]>("/v1/social/recommendations");
}

export async function updateRecommendationStatus(
  id: string,
  status: "accepted" | "dismissed"
): Promise<RecommendationItem> {
  return await apiFetch<RecommendationItem>(`/v1/social/recommendations/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}


// ── Watch History ─────────────────────────────────────────────────────────

export async function getHistory(
  params: import("./types").HistoryParams = {}
): Promise<import("./types").HistoryPageResponse> {
  const searchParams = new URLSearchParams();
  if (params.limit !== undefined) searchParams.append("limit", params.limit.toString());
  if (params.offset !== undefined) searchParams.append("offset", params.offset.toString());
  if (params.type && params.type !== "ALL") searchParams.append("type", params.type);

  const qs = searchParams.toString();
  const endpoint = `/v1/personal/history${qs ? `?${qs}` : ""}`;
  return await apiFetch<import("./types").HistoryPageResponse>(endpoint);
}

export async function deleteHistoryItem(id: string): Promise<void> {
  await apiFetch(`/v1/personal/history/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}

// ── Personal Analytics & Dashboard ────────────────────────────────────────

export async function getPersonalAnalytics(): Promise<import("./types").PersonalAnalyticsData> {
  return await apiFetch<import("./types").PersonalAnalyticsData>("/v1/personal/analytics");
}

export async function getTopRecommendations(limit: number = 5): Promise<import("./types").RecommendationListResponse> {
  return await apiFetch<import("./types").RecommendationListResponse>(`/v1/recommendations?limit=${limit}`);
}

