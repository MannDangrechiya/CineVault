import { apiFetch } from "./client";

export interface WatchlistStateResponse {
  in_watchlist: boolean;
  status: string;
}

export interface WatchlistItem {
  id: string;
  title_id: string;
  canonical_title: string;
  production_year?: number | null;
  content_type: string;
  poster_url?: string | null;
  added_at: string;
}

export interface WatchlistPageResponse {
  items: WatchlistItem[];
  total: number;
  limit: number;
  offset: number;
}

// Matches services/api/schemas/social.py's EnrichedRecommendationResponse.
// Raw sender_id/recipient_id/title_id are kept alongside the joined/resolved
// fields per PLAN.md 1.2 ("keep the raw fields too"). Name fields are
// best-effort only -- this backend has no user-profile table, so they're
// null for anyone outside the fixed local-dev credential store.
export interface RecommendationItem {
  recommendation_id: string;
  sender_id: string;
  sender_name: string | null;
  sender_username: string | null;
  recipient_id: string;
  recipient_name: string | null;
  recipient_username: string | null;
  title_id: string;
  canonical_title: string | null;
  poster_url: string | null;
  production_year: number | null;
  status: "SENT" | "ACCEPTED" | "REJECTED" | "WATCHED" | "RATED";
  context_note: string | null;
  sent_at: string;
  updated_at: string;
}

export interface CompatibilityResponse {
  user_id: string;
  friend_id: string;
  friend_name: string | null;
  friend_username: string | null;
  compatibility_score: number;
  taste_tier: "Oracle" | "Critic" | "Regular" | "Curious" | string;
  shared_genres: string[];
  shared_directors: string[];
  shared_favorite_titles: string[];
  calculated_at: string;
}

// ── Watchlist ─────────────────────────────────────────────────────────────
// Maps onto the backend's title-state system: "add" sets manual_status_override
// to PLAN_TO_WATCH, "remove" sends it as explicit null, which the backend now
// clears back to unset (PATCH /v1/me/title-states/{id} treats an explicitly
// null field as "clear this", distinct from an omitted field).

export async function toggleWatchlistState(
  titleId: string,
  inWatchlist: boolean
): Promise<WatchlistStateResponse> {
  const state = await apiFetch<{ manual_status_override: string | null }>(
    `/v1/me/title-states/${encodeURIComponent(titleId)}`,
    {
      method: "PATCH",
      body: JSON.stringify({
        manual_status_override: inWatchlist ? "PLAN_TO_WATCH" : null,
      }),
    }
  );
  return {
    in_watchlist: state.manual_status_override === "PLAN_TO_WATCH",
    status: state.manual_status_override ?? "NONE",
  };
}

export async function getWatchlist(): Promise<WatchlistItem[]> {
  const page = await apiFetch<WatchlistPageResponse>("/v1/personal/watchlist?limit=100");
  return page.items;
}

export async function removeFromWatchlist(titleId: string): Promise<void> {
  await toggleWatchlistState(titleId, false);
}

// ── Social Recommendations ────────────────────────────────────────────────

export async function sendRecommendation(
  titleId: string,
  recipientId: string,
  contextNote?: string
): Promise<void> {
  await apiFetch("/social/recommendations", {
    method: "POST",
    body: JSON.stringify({
      title_id: titleId,
      recipient_id: recipientId,
      // Backend field is context_note, not message -- the old "message" key
      // was silently dropped by pydantic on every call (PLAN.md 1.2).
      context_note: contextNote || undefined,
    }),
  });
}

export async function getRecommendations(
  params: { role?: "sent" | "received" | "all" } = {}
): Promise<RecommendationItem[]> {
  const qs = params.role ? `?role=${encodeURIComponent(params.role)}` : "";
  return await apiFetch<RecommendationItem[]>(`/social/recommendations${qs}`);
}

export async function updateRecommendationStatus(
  id: string,
  status: "ACCEPTED" | "REJECTED"
): Promise<RecommendationItem> {
  return await apiFetch<RecommendationItem>(`/social/recommendations/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export async function getFriendCompatibility(friendId: string): Promise<CompatibilityResponse> {
  return await apiFetch<CompatibilityResponse>(
    `/social/friendships/${encodeURIComponent(friendId)}/compatibility`
  );
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

export interface UserStreakResponse {
  user_id: string;
  current_streak: number;
  longest_streak: number;
  last_watch_date: string | null;
  updated_at: string;
}

export async function getUserStreak(): Promise<UserStreakResponse> {
  return await apiFetch<UserStreakResponse>("/v1/personal/streak");
}

export interface LeaderboardEntry {
  user_id: string;
  name: string | null;
  username: string | null;
  watch_count: number;
  watch_hours: number;
  rank: number;
  is_current_user: boolean;
}

export interface LeaderboardResponse {
  period: "weekly" | "monthly" | "all_time";
  entries: LeaderboardEntry[];
  calculated_at: string;
}

export async function getSocialLeaderboard(
  period: "weekly" | "monthly" | "all_time" = "weekly"
): Promise<LeaderboardResponse> {
  return await apiFetch<LeaderboardResponse>(`/social/leaderboard?period=${period}`);
}

export async function getTopRecommendations(limit: number = 5): Promise<import("./types").RecommendationListResponse> {
  return await apiFetch<import("./types").RecommendationListResponse>(`/v1/recommendations?limit=${limit}`);
}

export interface BadgeResponse {
  badge_id: string;
  slug: string;
  name: string;
  description: string;
  icon_url: string | null;
  is_earned: boolean;
  earned_at: string | null;
  context_json: Record<string, unknown> | null;
}

export interface UserBadgesResponse {
  user_id: string;
  badges: BadgeResponse[];
  total_earned: number;
}

export async function getUserBadges(userId?: string): Promise<UserBadgesResponse> {
  const endpoint = userId ? `/social/badges/${encodeURIComponent(userId)}` : "/social/badges";
  return await apiFetch<UserBadgesResponse>(endpoint);
}

export async function evaluateUserBadges(): Promise<UserBadgesResponse> {
  return await apiFetch<UserBadgesResponse>("/social/badges/evaluate", {
    method: "POST",
  });
}




