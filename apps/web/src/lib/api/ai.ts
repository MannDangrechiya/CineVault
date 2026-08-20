// CineVault OS — Conversational AI Assistant & Group Matchmaking API Client Module
// Integrates with /v1/ai/assistant/query, /social/friendships, and /ai/group-matchmaking

import { apiFetch } from "./client";

export interface AIIntentExtraction {
  raw_query: string;
  sanitized_query: string;
  target_genres: string[];
  target_directors: string[];
  target_actors: string[];
  min_year?: number | null;
  max_year?: number | null;
  max_runtime?: number | null;
  preferred_content_type?: string | null;
  detected_intent_mode: string;
}

export interface MatchedAssistantTitle {
  id?: string;
  title_id?: string;
  canonical_title: string;
  production_year?: number | null;
  content_type?: string;
  poster_url?: string | null;
  vote_average?: number | null;
  overview?: string | null;
  genres?: string[];
  directors?: string[];
}

export interface AssistantQueryResponse {
  response_text: string;
  intent: AIIntentExtraction;
  matched_titles: MatchedAssistantTitle[];
  provider_used: string;
  is_grounded: boolean;
  fallback_applied: boolean;
}

export interface FriendshipItem {
  friendship_id: string;
  friend_id: string;
  friend_name: string;
  friend_username: string;
  avatar_url?: string | null;
  status: "PENDING" | "ACCEPTED" | "REJECTED" | "BLOCKED" | string;
  trust_score: number;
  created_at: string;
}

export interface GroupMatchResponse {
  status: string;
  mood: string;
  group_size: number;
  group_member_ids: string[];
  recommended_titles: string[];
  ai_recommendation: string;
  group_vector_preview?: number[] | null;
}

// ── Conversational Assistant ───────────────────────────────────────────────

export async function queryAssistant(
  queryText: string,
  options: {
    include_recommendation_context?: boolean;
    max_results?: number;
  } = {}
): Promise<AssistantQueryResponse> {
  const { include_recommendation_context = true, max_results = 5 } = options;

  return await apiFetch<AssistantQueryResponse>("/v1/ai/assistant/query", {
    method: "POST",
    body: JSON.stringify({
      query_text: queryText,
      include_recommendation_context,
      max_results,
    }),
  });
}

// ── Friendships & Social ───────────────────────────────────────────────────

export async function getFriendships(): Promise<FriendshipItem[]> {
  return await apiFetch<FriendshipItem[]>("/social/friendships");
}

// ── Group Matchmaking ──────────────────────────────────────────────────────

export async function runGroupMatchmaking(
  friendIds: string[],
  mood: string
): Promise<GroupMatchResponse> {
  return await apiFetch<GroupMatchResponse>("/ai/group-matchmaking", {
    method: "POST",
    body: JSON.stringify({
      friend_ids: friendIds,
      mood,
    }),
  });
}
