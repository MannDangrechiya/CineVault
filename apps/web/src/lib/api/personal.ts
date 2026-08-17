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
