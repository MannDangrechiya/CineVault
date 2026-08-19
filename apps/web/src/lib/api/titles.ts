// CineVault OS — Public Catalog Titles API Endpoint Service (CAT-1)
// Fetches canonical titles from FastAPI backend.

import { apiFetch } from "./client";
import {
  PaginatedResponse,
  TitleSummary,
  TitleDetail,
  CatalogParams,
  CatalogPageResponse,
  GenreSummary,
} from "./types";

export interface ListTitlesParams {
  content_type?: string;
  production_year?: number;
  origin_country?: string;
  sort?: string;
  limit?: number;
  cursor?: string;
}

export async function getTitles(
  params: ListTitlesParams = {}
): Promise<PaginatedResponse<TitleSummary>> {
  const query = new URLSearchParams();

  if (params.content_type) query.append("content_type", params.content_type);
  if (params.production_year) query.append("production_year", params.production_year.toString());
  if (params.origin_country) query.append("origin_country", params.origin_country);
  if (params.sort) query.append("sort", params.sort);
  if (params.limit) query.append("limit", params.limit.toString());
  if (params.cursor) query.append("cursor", params.cursor);

  const queryString = query.toString();
  const endpoint = `/v1/titles${queryString ? `?${queryString}` : ""}`;

  return await apiFetch<PaginatedResponse<TitleSummary>>(endpoint);
}

export async function getTitleById(titleId: string): Promise<TitleDetail> {
  return await apiFetch<TitleDetail>(`/v1/titles/${encodeURIComponent(titleId)}`);
}

// ── Catalog Browsing (Offset-based Infinite Scroll) ─────────────────────

/**
 * Offset-based catalog page fetch with search, genre, year, content_type and sort filters.
 * Fetches directly from the live FastAPI `/titles` endpoint.
 */
export async function getCatalogPage(
  params: CatalogParams = {}
): Promise<CatalogPageResponse> {
  const {
    q,
    query: queryParam,
    genre,
    year,
    production_year,
    content_type,
    sort,
    limit = 24,
    offset = 0,
  } = params;

  const searchParams = new URLSearchParams();
  const searchText = queryParam ?? q;
  if (searchText) searchParams.append("query", searchText);
  if (genre) searchParams.append("genre", genre);
  const releaseYear = year ?? production_year;
  if (releaseYear !== undefined && releaseYear !== null) {
    searchParams.append("year", releaseYear.toString());
  }
  if (content_type) searchParams.append("content_type", content_type);
  if (sort) searchParams.append("sort", sort);
  searchParams.append("limit", limit.toString());
  searchParams.append("offset", offset.toString());

  const endpoint = `/titles?${searchParams.toString()}`;
  return await apiFetch<CatalogPageResponse>(endpoint);
}

/**
 * Fetches the genre taxonomy list from the backend.
 */
export async function getGenres(): Promise<GenreSummary[]> {
  return await apiFetch<GenreSummary[]>("/genres");
}

