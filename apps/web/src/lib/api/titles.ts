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
 * Offset-based catalog page fetch with search, genre, year and sort filters.
 * Fetches directly from the live FastAPI backend.
 */
export async function getCatalogPage(
  params: CatalogParams = {}
): Promise<CatalogPageResponse> {
  const { q, genre, production_year, sort, limit = 24, offset = 0 } = params;

  const query = new URLSearchParams();
  if (q) query.append("q", q);
  if (genre) query.append("genre", genre);
  if (production_year) query.append("production_year", production_year.toString());
  if (sort) query.append("sort", sort);
  query.append("limit", limit.toString());
  query.append("offset", offset.toString());

  const endpoint = `/v1/catalog?${query.toString()}`;
  return await apiFetch<CatalogPageResponse>(endpoint);
}

/**
 * Fetches the genre taxonomy list from the backend.
 */
export async function getGenres(): Promise<GenreSummary[]> {
  return await apiFetch<GenreSummary[]>("/v1/genres");
}
