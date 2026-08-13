// CineVault OS — Public Catalog Titles API Endpoint Service (CAT-1)

import { apiFetch } from "./client";
import { PaginatedResponse, TitleSummary, TitleDetail } from "./types";

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

  return apiFetch<PaginatedResponse<TitleSummary>>(endpoint);
}

export async function getTitleById(titleId: string): Promise<TitleDetail> {
  return apiFetch<TitleDetail>(`/v1/titles/${encodeURIComponent(titleId)}`);
}
