// CineVault OS — Data Portability & Document Ingestion Engine API Client Module
// Supports Letterboxd CSV, JSON, Samsung Notes / plain text, and PDF (text-layer) parsing

import { apiFetch } from "./client";
import { APIClientError } from "./types";

export interface ImportItemPayload {
  canonical_title?: string;
  production_year?: number;
  title_id?: string;
  watched_at?: string;
  progress_percentage?: number;
  rating_value?: number;
  is_favorite?: boolean;
  manual_status_override?: string;
  notes?: string;
}

export interface ImportCandidateMatch {
  title_id: string;
  display_id?: string;
  canonical_title: string;
  production_year?: number;
  content_type?: string;
  confidence: number;
}

export interface ImportConflictItem {
  title_id: string;
  canonical_title: string;
  field_name: string;
  existing_value: unknown;
  imported_value: unknown;
}

export interface ImportItemVerdict {
  index: number;
  canonical_title: string;
  production_year?: number;
  matched: boolean;
  matched_title_id?: string;
  matched_display_id?: string;
  confidence_score: number;
  verdict: "EXACT_MATCH" | "PROBABLE_MATCH" | "REVIEW_REQUIRED" | "UNMATCHED";
  candidates?: ImportCandidateMatch[];
  reasons?: string[];
}

export interface ImportPreviewResponse {
  total_items: number;
  matched_titles: number;
  probable_matches?: number;
  review_required?: number;
  unmatched_titles: number;
  conflicts_count: number;
  duplicate_skips_count?: number;
  conflicts: ImportConflictItem[];
  item_verdicts?: ImportItemVerdict[];
}

export interface ImportApplyResponse {
  applied_count: number;
  conflicts_resolved: number;
  strategy_applied: string;
  applied_at: string;
}

export interface ImportUploadResponse {
  filename: string;
  total_parsed: number;
  items: ImportItemPayload[];
}

// ── API Operations ─────────────────────────────────────────────────────────

export async function uploadImportFile(file: File): Promise<ImportUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  let response: Response;
  try {
    response = await fetch("/api/proxy/v1/personal/import/upload", {
      method: "POST",
      body: formData,
    });
  } catch (error) {
    throw new APIClientError(
      error instanceof Error ? error.message : "Failed to reach the CineVault API server.",
      0
    );
  }

  if (!response.ok) {
    let message = `HTTP ${response.status} ${response.statusText}`;
    try {
      const errorData = await response.json();
      message = errorData?.detail || errorData?.error?.message || message;
    } catch {
      // Fallback
    }
    throw new APIClientError(message, response.status);
  }

  return (await response.json()) as ImportUploadResponse;
}

export async function downloadExport(
  format: "json" | "csv" | "excel" | "xlsx" | "markdown" | "md" = "json",
  scope?: string
): Promise<void> {
  const params = new URLSearchParams({ format, download: "true" });
  if (scope) params.append("scope", scope);

  const res = await fetch(`/api/proxy/v1/personal/export?${params.toString()}`);
  if (!res.ok) {
    let message = `Export failed: ${res.statusText}`;
    try {
      const err = await res.json();
      message = err?.detail || message;
    } catch {
      // ignore
    }
    throw new Error(message);
  }

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  const ext = format === "excel" || format === "xlsx" ? "xlsx" : format === "csv" ? "zip" : format === "markdown" || format === "md" ? "md" : "json";
  a.download = `cinevault_export_${new Date().toISOString().slice(0, 10)}.${ext}`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  a.remove();
}

export async function previewImport(
  items: ImportItemPayload[]
): Promise<ImportPreviewResponse> {
  return await apiFetch<ImportPreviewResponse>("/v1/personal/import/preview", {
    method: "POST",
    body: JSON.stringify({ items }),
  });
}

export async function applyImport(
  items: ImportItemPayload[],
  conflictStrategy: "KEEP_EXISTING" | "OVERWRITE" | "MERGE" = "KEEP_EXISTING"
): Promise<ImportApplyResponse> {
  return await apiFetch<ImportApplyResponse>("/v1/personal/import/apply", {
    method: "POST",
    body: JSON.stringify({
      items,
      conflict_strategy: conflictStrategy,
    }),
  });
}

export interface PdfExtractResponse {
  extracted_text: string;
  page_count: number;
  warning?: string;
}

// Bypasses apiFetch deliberately: apiFetch hard-sets Content-Type: application/json,
// which would strip the multipart boundary a FormData body needs. The browser sets
// the correct multipart Content-Type itself as long as we don't override it here.
export async function extractPdfText(file: File): Promise<PdfExtractResponse> {
  const formData = new FormData();
  formData.append("file", file);

  let response: Response;
  try {
    response = await fetch("/api/proxy/v1/personal/import/extract-pdf", {
      method: "POST",
      body: formData,
    });
  } catch (error) {
    throw new APIClientError(
      error instanceof Error ? error.message : "Failed to reach the CineVault API server.",
      0
    );
  }

  if (!response.ok) {
    let message = `HTTP ${response.status} ${response.statusText}`;
    try {
      const errorData = await response.json();
      message = errorData?.detail || errorData?.error?.message || message;
    } catch {
      // Fall back to the generic status message above.
    }
    throw new APIClientError(message, response.status);
  }

  return (await response.json()) as PdfExtractResponse;
}

// ── Multi-Format Text / Document Parsers ───────────────────────────────────

export function parseImportText(
  rawText: string,
  formatHint: "auto" | "csv" | "json" | "notes" = "auto"
): ImportItemPayload[] {
  const trimmed = rawText.trim();
  if (!trimmed) return [];

  // 1. Try JSON
  if (
    formatHint === "json" ||
    (formatHint === "auto" && (trimmed.startsWith("[") || trimmed.startsWith("{")))
  ) {
    try {
      const parsed = JSON.parse(trimmed);
      const array = Array.isArray(parsed) ? parsed : [parsed];
      return array.map((item: Record<string, unknown>) => ({
        canonical_title: String(item.canonical_title || item.title || item.name || "").trim(),
        production_year: item.production_year ? Number(item.production_year) : (item.year ? Number(item.year) : undefined),
        rating_value: item.rating_value ? Number(item.rating_value) : (item.rating ? Number(item.rating) : undefined),
        watched_at: item.watched_at ? String(item.watched_at) : (item.date ? String(item.date) : undefined),
        manual_status_override: item.manual_status_override ? String(item.manual_status_override) : (item.status ? String(item.status) : "COMPLETED"),
        is_favorite: Boolean(item.is_favorite || item.favorite),
        notes: item.notes ? String(item.notes) : undefined,
      })).filter((i) => Boolean(i.canonical_title));
    } catch {
      // Fall through if JSON parse fails
    }
  }

  // 2. Try CSV (Letterboxd / Trakt export)
  if (
    formatHint === "csv" ||
    (formatHint === "auto" && trimmed.includes(",") && (trimmed.includes("\n") || trimmed.includes("\r")))
  ) {
    const lines = trimmed.split(/\r?\n/).filter((l) => l.trim().length > 0);
    if (lines.length > 1 && (lines[0].toLowerCase().includes("title") || lines[0].toLowerCase().includes("name"))) {
      const headers = lines[0].split(",").map((h) => h.trim().toLowerCase().replace(/"/g, ""));
      const titleIdx = headers.findIndex((h) => h === "title" || h === "name" || h === "film");
      const yearIdx = headers.findIndex((h) => h === "year" || h === "release year");
      const ratingIdx = headers.findIndex((h) => h === "rating" || h === "rating10" || h === "score");
      const dateIdx = headers.findIndex((h) => h.includes("date") || h === "watched_at" || h === "watched date");

      if (titleIdx !== -1) {
        const results: ImportItemPayload[] = [];
        for (let i = 1; i < lines.length; i++) {
          const cols = lines[i].split(",").map((c) => c.trim().replace(/^"|"$/g, ""));
          const title = cols[titleIdx];
          if (!title) continue;

          const year = yearIdx !== -1 && cols[yearIdx] ? parseInt(cols[yearIdx], 10) : undefined;
          const rating = ratingIdx !== -1 && cols[ratingIdx] ? parseFloat(cols[ratingIdx]) : undefined;
          const date = dateIdx !== -1 && cols[dateIdx] ? cols[dateIdx] : undefined;

          results.push({
            canonical_title: title,
            production_year: isNaN(year as number) ? undefined : year,
            rating_value: isNaN(rating as number) ? undefined : Math.round(rating as number),
            watched_at: date,
            manual_status_override: "COMPLETED",
          });
        }
        if (results.length > 0) return results;
      }
    }
  }

  // 3. Fallback: Samsung Notes / Plain Text Unstructured Lines
  // Format examples:
  // "1. Dune: Part Two (2024) - Watched, 5/5"
  // "Blade Runner 2049 [2017] ★★★★★"
  // "- Oppenheimer (2023) - Great IMAX experience"
  const lines = trimmed.split(/\r?\n/).filter((l) => l.trim().length > 0);
  const items: ImportItemPayload[] = [];

  for (const line of lines) {
    let clean = line.trim();
    // Strip leading list numbers/bullets: "1.", "1)", "-", "*", "•"
    clean = clean.replace(/^(\d+[\.\)]|\-|\*|•)\s*/, "").trim();
    if (!clean) continue;

    let year: number | undefined;
    let rating: number | undefined;
    let notes: string | undefined;

    // Check for stars: ★★★★★ or ★★★★
    const starCount = (clean.match(/★/g) || []).length;
    if (starCount > 0) {
      rating = starCount;
      clean = clean.replace(/★+/g, "").trim();
    }

    // Check for "X/5" or "X/10"
    const scoreMatch = clean.match(/(\d+(?:\.\d+)?)\s*\/\s*(5|10)/);
    if (scoreMatch) {
      const val = parseFloat(scoreMatch[1]);
      const max = parseFloat(scoreMatch[2]);
      rating = max === 10 ? Math.round(val / 2) : Math.round(val);
      clean = clean.replace(scoreMatch[0], "").trim();
    }

    // Check for year in parentheses or brackets: (2024) or [2024]
    const yearMatch = clean.match(/[\(\[]\s*(18\d\d|19\d\d|20\d\d)\s*[\)\]]/);
    if (yearMatch) {
      year = parseInt(yearMatch[1], 10);
      clean = clean.replace(yearMatch[0], "").trim();
    }

    // Check for notes or dash separation
    if (clean.includes(" - ")) {
      const parts = clean.split(" - ");
      clean = parts[0].trim();
      notes = parts.slice(1).join(" - ").trim();
    }

    // Strip trailing commas, colons, and a dangling "-" left over when the
    // " - " note-separator above matched with nothing after it (e.g.
    // "Parasite (2019) - 5/5" -- once the year and the "5/5" score are both
    // consumed, "Parasite (2019) -" has no space-dash-space left to split
    // on, so a bare trailing "-" survived into the parsed title and broke
    // canonical matching for an otherwise-real, otherwise-exact title).
    clean = clean.replace(/[,:;-]+$/, "").trim();

    if (clean.length > 0) {
      items.push({
        canonical_title: clean,
        production_year: year,
        rating_value: rating,
        notes: notes,
        manual_status_override: "COMPLETED",
        watched_at: new Date().toISOString(),
      });
    }
  }

  return items;
}
