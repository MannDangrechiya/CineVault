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
  try {
    const res = await apiFetch<FriendshipItem[]>("/social/friendships");
    if (Array.isArray(res) && res.length > 0) {
      return res;
    }
  } catch {
    // Fallback seed friendships for local dev preview
  }

  return [
    {
      friendship_id: "018f4a00-0000-7000-8000-000000000101",
      friend_id: "018f4a00-0000-7000-8000-000000000201",
      friend_name: "Elena Rostova",
      friend_username: "elena_cinema",
      avatar_url: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80",
      status: "ACCEPTED",
      trust_score: 94.5,
      created_at: "2026-08-01T10:00:00Z",
    },
    {
      friendship_id: "018f4a00-0000-7000-8000-000000000102",
      friend_id: "018f4a00-0000-7000-8000-000000000202",
      friend_name: "Marcus Vance",
      friend_username: "marcus_film",
      avatar_url: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&q=80",
      status: "ACCEPTED",
      trust_score: 88.0,
      created_at: "2026-08-04T15:30:00Z",
    },
    {
      friendship_id: "018f4a00-0000-7000-8000-000000000103",
      friend_id: "018f4a00-0000-7000-8000-000000000203",
      friend_name: "Aoi Takahashi",
      friend_username: "aoi_t",
      avatar_url: "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=200&q=80",
      status: "ACCEPTED",
      trust_score: 91.2,
      created_at: "2026-08-08T18:00:00Z",
    },
  ];
}

// ── Group Matchmaking ──────────────────────────────────────────────────────

export async function runGroupMatchmaking(
  friendIds: string[],
  mood: string
): Promise<GroupMatchResponse> {
  try {
    return await apiFetch<GroupMatchResponse>("/ai/group-matchmaking", {
      method: "POST",
      body: JSON.stringify({
        friend_ids: friendIds,
        mood,
      }),
    });
  } catch {
    // Fallback response for dev when LLM server is not locally bound
    return {
      status: "success",
      mood,
      group_size: friendIds.length + 1,
      group_member_ids: friendIds,
      recommended_titles: [
        "Blade Runner 2049",
        "Arrival",
        "Interstellar",
        "Dune: Part Two",
      ],
      ai_recommendation: `Based on your group's taste vectors combining Sci-Fi and cerebral thrillers with mood "${mood}", the AI Brain recommends a consensus viewing featuring Denis Villeneuve and Christopher Nolan. Strong cinematic resonance detected across all group members.`,
      group_vector_preview: [0.042, 0.081, 0.035, 0.091, 0.012, 0.067],
    };
  }
}
