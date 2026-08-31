// CineVault OS — Public Catalog Titles API Endpoint Service (CAT-1)
// Fetches canonical titles from FastAPI backend.

import { apiFetch } from "./client";
import {
  TitleDetail,
  CatalogParams,
  CatalogPageResponse,
  GenreSummary,
} from "./types";

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
    query,
    genre,
    year,
    content_type,
    sort,
    limit = 24,
    offset = 0,
  } = params;

  const searchParams = new URLSearchParams();
  if (query) searchParams.append("query", query);
  if (genre) searchParams.append("genre", genre);
  if (year !== undefined && year !== null) {
    searchParams.append("year", year.toString());
  }
  if (content_type) searchParams.append("content_type", content_type);
  if (sort) searchParams.append("sort", sort);
  searchParams.append("limit", limit.toString());
  searchParams.append("offset", offset.toString());

  const endpoint = `/v1/catalog?${searchParams.toString()}`;
  return await apiFetch<CatalogPageResponse>(endpoint);
}

/**
 * Fetches the genre taxonomy list from the backend.
 */
export async function getGenres(): Promise<GenreSummary[]> {
  return await apiFetch<GenreSummary[]>("/v1/genres");
}

