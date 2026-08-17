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

export interface EditionSummary {
  id: string;
  title_id: string;
  edition_name: string;
  runtime_minutes?: number | null;
  format?: string | null;
}

export interface TitleDetail extends TitleSummary {
  synopsis?: string | null;
  genres: string[];
  primary_edition?: EditionSummary | null;
}

export interface CursorPagination {
  next_cursor: string | null;
  has_more: boolean;
  limit: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: CursorPagination;
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
