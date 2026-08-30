// CineVault OS — Web API Client Type Definitions (CAT-1 Catalog & Error Schemas)

export interface TitleSummary {
  id: string;
  display_id: string;
  canonical_title: string;
  original_title?: string | null;
  content_type: "MOVIE" | "TV_SERIES" | "ANIME" | string;
  production_year?: number | null;
  origin_country?: string | null;
  has_licensed_artwork: boolean;
  poster_url?: string | null;
  backdrop_url?: string | null;
}

export interface TitleAliasSummary {
  alias_name: string;
  alias_type: string;
  language_code?: string | null;
  country_code?: string | null;
}

export interface ThemeSummary {
  theme_id: string;
  name: string;
}

export interface KeywordSummary {
  keyword_id: string;
  name: string;
}

export interface CertificationSummary {
  country_code: string;
  certification_code: string;
  rating_body?: string | null;
  meaning?: string | null;
  min_age?: number | null;
  note?: string | null;
}

export interface CreditSummary {
  credit_id: string;
  person_id: string;
  person_name: string;
  role_name: string;
  role_category: string;
  character_name?: string | null;
  billing_order?: number | null;
}

export interface CompanySummary {
  company_id: string;
  company_name: string;
  role: string;
  country_code?: string | null;
}

export interface AwardResultSummary {
  award_name: string;
  organization: string;
  category_name: string;
  year: number;
  is_winner: boolean;
}

export interface FestivalParticipationSummary {
  festival_name: string;
  year: number;
  section_name?: string | null;
}

export interface ReleaseSummary {
  release_id: string;
  edition_id: string;
  release_name: string;
  release_type: string;
  release_date?: string | null;
  country_code?: string | null;
}

export interface ExternalIdSummary {
  provider_name: string;
  external_id: string;
  external_url?: string | null;
}

export interface EditionSummary {
  id: string;
  title_id: string;
  edition_name: string;
  is_primary?: boolean;
  runtime_minutes?: number | null;
  format?: string | null;
  aspect_ratio?: string | null;
  color_format?: string | null;
  sound_mix?: string | null;
  releases?: ReleaseSummary[];
}

export interface EpisodeSummary {
  id: string;
  season_id: string;
  episode_number: number;
  episode_name?: string | null;
  air_date?: string | null;
  runtime_minutes?: number | null;
  overview?: string | null;
}

export interface SeasonSummary {
  id: string;
  title_id: string;
  season_number: number;
  season_name?: string | null;
  overview?: string | null;
  episodes: EpisodeSummary[];
}

export interface TitleDetail extends TitleSummary {
  tagline?: string | null;
  synopsis?: string | null;
  genres: string[];
  themes?: ThemeSummary[];
  keywords?: KeywordSummary[];
  aliases?: TitleAliasSummary[];
  languages?: string[];
  countries?: string[];
  certifications?: CertificationSummary[];
  credits?: CreditSummary[];
  companies?: CompanySummary[];
  awards?: AwardResultSummary[];
  festival_participations?: FestivalParticipationSummary[];
  primary_edition?: EditionSummary | null;
  editions?: EditionSummary[];
  seasons?: SeasonSummary[];
  external_ids?: ExternalIdSummary[];
}

export interface RatingResponse {
  id: string;
  title_id: string;
  rating_value: number;
  updated_at: string;
}

export interface NoteResponse {
  id: string;
  title_id: string;
  note_text: string;
  updated_at: string;
}

export interface ReviewResponse {
  id: string;
  title_id: string;
  review_title?: string;
  review_text: string;
  is_public: boolean;
  created_at: string;
}

export interface UserTitleStateResponse {
  title_id: string;
  derived_status: string;
  manual_status_override?: string | null;
  is_favorite: boolean;
  preferred_edition_id?: string | null;
  updated_at: string;
}

export interface APIErrorDetail {
  field?: string | null;
  issue: string;
}

export interface APIErrorBody {
  code: string;
  message: string;
  status: number;
  correlation_id: string;
  timestamp: string;
  details?: APIErrorDetail[];
}

export interface APIErrorResponse {
  error: APIErrorBody;
}

// ── Catalog Browsing (Offset Pagination) ────────────────────────────────

export interface CatalogParams {
  query?: string;
  genre?: string;
  year?: number;
  content_type?: string;
  sort?: string;
  limit?: number;
  offset?: number;
}

export interface CatalogPageResponse {
  items: TitleSummary[];
  total: number;
  limit: number;
  next_offset: number | null;
}

export interface GenreSummary {
  genre_id: string;
  name: string;
  description?: string | null;
}

// ── Personal Watch History Types ────────────────────────────────────────

export interface HistoryItem {
  id: string;
  title_id: string;
  canonical_title: string;
  production_year?: number | null;
  content_type: "MOVIE" | "TV_SERIES" | "ANIME" | string;
  poster_url?: string | null;
  watched_at: string;
  rating_value?: number | null;
  device_type?: string | null;
  progress_percentage: number;
}

export interface HistoryParams {
  limit?: number;
  offset?: number;
  type?: string;
}

export interface HistoryPageResponse {
  items: HistoryItem[];
  total: number;
  limit: number;
  offset: number;
}

// ── Personal Media Library Types ────────────────────────────────────────

export interface LibraryItem {
  id: string;
  title_id: string;
  canonical_title: string;
  production_year?: number | null;
  content_type: "MOVIE" | "TV_SERIES" | "ANIME" | string;
  poster_url?: string | null;
  added_at: string;
}

export interface LibraryParams {
  limit?: number;
  offset?: number;
  type?: string;
}

export interface LibraryPageResponse {
  items: LibraryItem[];
  total: number;
  limit: number;
  offset: number;
}

// ── Collections & Franchises Types ──────────────────────────────────────

export interface CollectionItem {
  id: string;
  name: string;
  description?: string | null;
  item_count: number;
  banner_url?: string | null;
  curator: string;
  tags: string[];
  is_private: boolean;
  is_custom: boolean;
  created_at?: string | null;
}

export interface CreateCollectionPayload {
  name: string;
  description?: string;
  tags?: string[];
  banner_url?: string;
  is_private?: boolean;
}

export interface CollectionTitleItem {
  item_id: string;
  title_id: string;
  canonical_title: string;
  production_year?: number | null;
  content_type: string;
  poster_url?: string | null;
  notes?: string | null;
  added_at: string;
}

export interface CollectionDetail {
  collection: CollectionItem;
  items: CollectionTitleItem[];
}

// ── Personal Analytics & Dashboard Types ────────────────────────────────

export interface GenreAffinityItem {
  genre: string;
  count: number;
  percentage: number;
}

export interface CreatorAffinityItem {
  name: string;
  role: string;
  count: number;
}

export interface MonthlyTrendItem {
  month: string;
  count: number;
  hours: number;
}

export interface PersonalAnalyticsData {
  total_watch_hours: number;
  watched_count: number;
  total_titles: number;
  monthly_watch_count: number;
  annual_watch_count: number;
  watch_streak_days: number;
  taste_match_score: number;
  movies_watched: number;
  series_completed: number;
  anime_completed: number;
  pending_recommendations_count: number;
  top_genres: { genre: string; count: number; percentage: number }[];
  top_directors: CreatorAffinityItem[];
  top_actors: CreatorAffinityItem[];
  monthly_trend: MonthlyTrendItem[];
}

// ── Recommendation Item Types ───────────────────────────────────────────

export interface RecommendationSummary {
  title_id: string;
  display_id: string;
  canonical_title: string;
  original_title?: string | null;
  release_year?: number | null;
  content_type: string;
  runtime_minutes?: number | null;
  vote_average: number;
  genres: string[];
  directors: string[];
  recommendation_score: number;
  is_available: boolean;
  explanation: {
    explanation_text: string;
    matched_genres: string[];
    matched_directors: string[];
    matched_actors: string[];
  };
}

export interface RecommendationListResponse {
  mode: string;
  total: number;
  is_cold_start: boolean;
  data: RecommendationSummary[];
}

// ── API Error Types ─────────────────────────────────────────────────────

export class APIClientError extends Error {
  public status: number;
  public code?: string;
  public correlationId?: string;

  constructor(message: string, status: number, code?: string, correlationId?: string) {
    super(message);
    this.name = "APIClientError";
    this.status = status;
    this.code = code;
    this.correlationId = correlationId;
  }
}
