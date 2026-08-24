"use client";

import React, { useState, useRef } from "react";
import Link from "next/link";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { PageContainer } from "@/components/ui/PageContainer";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ArrowLeft,
  RotateCcw,
  Sparkles,
  History,
  Bookmark,
  Check,
  Search,
  X,
  Sliders,
} from "lucide-react";
import {
  parseImportText,
  previewImport,
  applyImport,
  ImportItemPayload,
  ImportPreviewResponse,
  ImportApplyResponse,
} from "@/lib/api/import";

const SAMPLE_SAMSUNG_NOTES = `1. Dune: Part Two (2024) - Watched, 5/5 ★★★★★
2. Blade Runner 2049 (2017) ★★★★★ - Roger Deakins masterpiece
3. Oppenheimer (2023) - 9/10 in IMAX 70mm
4. Severance - S1 (2022) [Watched]
5. Arrival (2016) ★★★★★ - Linguistic exploration
6. Interstellar (2014) - 10/10 Nolan marathon`;

const SAMPLE_CSV = `Title,Year,Rating,Watched Date,Notes
Dune: Part Two,2024,5,2026-08-20,Denis Villeneuve epic
Blade Runner 2049,2017,5,2026-08-19,Atmospheric neon noir
Oppenheimer,2023,4,2026-08-13,Trinity test sequence
Parasite,2019,5,2026-08-01,Palme d'Or winner`;

const SAMPLE_JSON = `[
  {
    "canonical_title": "Dune: Part Two",
    "production_year": 2024,
    "rating_value": 5,
    "manual_status_override": "COMPLETED",
    "notes": "Desert cinematography"
  },
  {
    "canonical_title": "Blade Runner 2049",
    "production_year": 2017,
    "rating_value": 5,
    "manual_status_override": "COMPLETED",
    "notes": "Replicant existentialism"
  }
]`;

export default function ImportPage() {
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3>(1);
  const [inputMode, setInputMode] = useState<"paste" | "upload">("paste");
  const [rawText, setRawText] = useState(SAMPLE_SAMSUNG_NOTES);
  const [formatHint, setFormatHint] = useState<"auto" | "csv" | "json" | "notes">("auto");
  const [fileName, setFileName] = useState<string | null>(null);

  // Parsed and preview state
  const [parsedItems, setParsedItems] = useState<ImportItemPayload[]>([]);
  const [previewResult, setPreviewResult] = useState<ImportPreviewResponse | null>(null);
  const [conflictStrategy, setConflictStrategy] = useState<"KEEP_EXISTING" | "OVERWRITE" | "MERGE">("KEEP_EXISTING");

  // Disambiguation Modal State
  const [disambiguationIndex, setDisambiguationIndex] = useState<number | null>(null);
  const [customTitleInput, setCustomTitleInput] = useState("");

  // Ingest & Apply State
  const [applyResult, setApplyResult] = useState<ImportApplyResponse | null>(null);
  const [applyProgress, setApplyProgress] = useState(0);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const queryClient = useQueryClient();

  // ── Step 1: Parse & Preview Mutation ────────────────────────────────────
  const previewMutation = useMutation({
    mutationFn: (items: ImportItemPayload[]) => previewImport(items),
    onSuccess: (data) => {
      setPreviewResult(data);
      setCurrentStep(2);
    },
  });

  // ── Step 3: Apply Mutation ──────────────────────────────────────────────
  const applyMutation = useMutation({
    mutationFn: (payload: { items: ImportItemPayload[]; strategy: "KEEP_EXISTING" | "OVERWRITE" | "MERGE" }) =>
      applyImport(payload.items, payload.strategy),
    onSuccess: (data) => {
      setApplyResult(data);
      setApplyProgress(100);
      setCurrentStep(3);
      queryClient.invalidateQueries({ queryKey: ["history"] });
      queryClient.invalidateQueries({ queryKey: ["watchlist"] });
      queryClient.invalidateQueries({ queryKey: ["personalAnalytics"] });
    },
  });

  const handleParseAndAnalyze = () => {
    const items = parseImportText(rawText, formatHint);
    if (items.length === 0) return;
    setParsedItems(items);
    previewMutation.mutate(items);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      if (content) {
        setRawText(content);
        if (file.name.endsWith(".json")) setFormatHint("json");
        else if (file.name.endsWith(".csv")) setFormatHint("csv");
        else setFormatHint("notes");
      }
    };
    reader.readAsText(file);
  };

  const handleApplyImport = () => {
    setApplyProgress(35);
    applyMutation.mutate({ items: parsedItems, strategy: conflictStrategy });
  };

  const handleResolveDisambiguation = (newTitle: string, newYear?: number) => {
    if (disambiguationIndex === null) return;
    const updated = [...parsedItems];
    updated[disambiguationIndex] = {
      ...updated[disambiguationIndex],
      canonical_title: newTitle,
      production_year: newYear ?? updated[disambiguationIndex].production_year,
    };
    setParsedItems(updated);
    setDisambiguationIndex(null);
    setCustomTitleInput("");
    previewMutation.mutate(updated);
  };

  const handleResetWizard = () => {
    setCurrentStep(1);
    setParsedItems([]);
    setPreviewResult(null);
    setApplyResult(null);
    setApplyProgress(0);
  };

  return (
    <PageContainer
      title="Library Data Portability & Import Wizard"
      subtitle="Import watch history, ratings, and custom film lists from Samsung Notes, Letterboxd CSV, Trakt, and JSON"
    >
      <div className="space-y-8">
        {/* Wizard Step Progress Indicator */}
        <div className="flex items-center justify-between max-w-2xl mx-auto p-4 rounded-3xl bg-zinc-900/40 border border-zinc-900 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div
              className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold transition-all ${
                currentStep >= 1 ? "bg-violet-600 text-white shadow-lg shadow-violet-600/30" : "bg-zinc-800 text-zinc-400"
              }`}
            >
              1
            </div>
            <div>
              <p className="text-xs font-bold text-zinc-100">Upload & Parse</p>
              <p className="text-[10px] text-zinc-400">Notes / CSV / JSON</p>
            </div>
          </div>

          <div className={`h-0.5 w-12 sm:w-20 ${currentStep >= 2 ? "bg-violet-600" : "bg-zinc-800"}`} />

          <div className="flex items-center gap-3">
            <div
              className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold transition-all ${
                currentStep >= 2 ? "bg-violet-600 text-white shadow-lg shadow-violet-600/30" : "bg-zinc-800 text-zinc-400"
              }`}
            >
              2
            </div>
            <div>
              <p className="text-xs font-bold text-zinc-100">Preview & Match</p>
              <p className="text-[10px] text-zinc-400">Disambiguation</p>
            </div>
          </div>

          <div className={`h-0.5 w-12 sm:w-20 ${currentStep >= 3 ? "bg-violet-600" : "bg-zinc-800"}`} />

          <div className="flex items-center gap-3">
            <div
              className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold transition-all ${
                currentStep >= 3 ? "bg-emerald-500 text-white shadow-lg shadow-emerald-600/30" : "bg-zinc-800 text-zinc-400"
              }`}
            >
              3
            </div>
            <div>
              <p className="text-xs font-bold text-zinc-100">Ingest & Apply</p>
              <p className="text-[10px] text-zinc-400">Write to Vault</p>
            </div>
          </div>
        </div>

        {/* ── STEP 1: UPLOAD / PASTE ─────────────────────────────────────── */}
        {currentStep === 1 && (
          <div className="max-w-3xl mx-auto space-y-6">
            <div className="p-6 rounded-3xl bg-zinc-900/40 border border-zinc-900 space-y-5">
              {/* Input Mode Selector & Sample Presets */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-900">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setInputMode("paste")}
                    className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                      inputMode === "paste"
                        ? "bg-violet-600/20 text-violet-300 border border-violet-500/40 shadow-sm"
                        : "text-zinc-400 hover:text-zinc-200"
                    }`}
                  >
                    Direct Text / Notes
                  </button>
                  <button
                    onClick={() => setInputMode("upload")}
                    className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                      inputMode === "upload"
                        ? "bg-violet-600/20 text-violet-300 border border-violet-500/40 shadow-sm"
                        : "text-zinc-400 hover:text-zinc-200"
                    }`}
                  >
                    File Dropzone
                  </button>
                </div>

                {/* Sample Presets */}
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-zinc-500 font-medium">Load Template:</span>
                  <button
                    onClick={() => {
                      setRawText(SAMPLE_SAMSUNG_NOTES);
                      setFormatHint("notes");
                    }}
                    className="px-2.5 py-1 rounded-lg text-[10px] bg-zinc-950 border border-zinc-800 text-zinc-300 hover:text-violet-400 hover:border-violet-500/30 transition-all cursor-pointer"
                  >
                    Samsung Notes
                  </button>
                  <button
                    onClick={() => {
                      setRawText(SAMPLE_CSV);
                      setFormatHint("csv");
                    }}
                    className="px-2.5 py-1 rounded-lg text-[10px] bg-zinc-950 border border-zinc-800 text-zinc-300 hover:text-violet-400 hover:border-violet-500/30 transition-all cursor-pointer"
                  >
                    Letterboxd CSV
                  </button>
                  <button
                    onClick={() => {
                      setRawText(SAMPLE_JSON);
                      setFormatHint("json");
                    }}
                    className="px-2.5 py-1 rounded-lg text-[10px] bg-zinc-950 border border-zinc-800 text-zinc-300 hover:text-violet-400 hover:border-violet-500/30 transition-all cursor-pointer"
                  >
                    JSON
                  </button>
                </div>
              </div>

              {/* Upload Dropzone Tab */}
              {inputMode === "upload" && (
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="p-8 rounded-2xl border-2 border-dashed border-zinc-800 hover:border-violet-500/50 bg-zinc-950/60 hover:bg-zinc-950 flex flex-col items-center justify-center text-center gap-3 cursor-pointer transition-all group"
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv,.json,.txt"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  <div className="p-3.5 rounded-2xl bg-violet-600/10 border border-violet-500/20 text-violet-400 group-hover:scale-110 transition-transform">
                    <UploadCloud className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-xs sm:text-sm font-bold text-zinc-200">
                      {fileName ? `Selected: ${fileName}` : "Click or drag & drop files here"}
                    </p>
                    <p className="text-[11px] text-zinc-500 mt-1">
                      Supports Letterboxd CSV exports, CineVault JSON, and raw Samsung Notes text files
                    </p>
                  </div>
                </div>
              )}

              {/* Direct Text / Notes Tab */}
              {inputMode === "paste" && (
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-zinc-300 flex items-center justify-between">
                    <span>Paste Document Content or Unstructured Notes:</span>
                    <span className="text-[10px] text-zinc-500 font-mono">
                      {rawText.split("\n").filter((l) => l.trim().length > 0).length} lines detected
                    </span>
                  </label>
                  <textarea
                    rows={10}
                    value={rawText}
                    onChange={(e) => setRawText(e.target.value)}
                    placeholder="Paste your movie list here..."
                    className="w-full p-4 rounded-2xl bg-zinc-950 border border-zinc-800 text-xs sm:text-sm font-mono text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-violet-500 transition-colors resize-y leading-relaxed"
                  />
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-2">
                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-zinc-400">Format:</span>
                  <select
                    value={formatHint}
                    onChange={(e) => setFormatHint(e.target.value as "auto" | "csv" | "json" | "notes")}
                    className="px-2.5 py-1.5 rounded-xl bg-zinc-950 border border-zinc-800 text-xs text-zinc-300 focus:outline-none"
                  >
                    <option value="auto">Auto-Detect</option>
                    <option value="notes">Samsung Notes / Plain Text</option>
                    <option value="csv">Letterboxd / Trakt CSV</option>
                    <option value="json">JSON Array</option>
                  </select>
                </div>

                <button
                  type="button"
                  onClick={handleParseAndAnalyze}
                  disabled={!rawText.trim() || previewMutation.isPending}
                  className="px-6 py-2.5 rounded-xl text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 disabled:opacity-50 transition-all cursor-pointer shadow-lg shadow-violet-600/30 flex items-center gap-2"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{previewMutation.isPending ? "Validating Canonical Matches..." : "Parse & Preview Matches"}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── STEP 2: PREVIEW & DISAMBIGUATION ───────────────────────────── */}
        {currentStep === 2 && previewResult && (
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Stats Overview Banner */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-2xl bg-zinc-900/40 border border-zinc-900 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-violet-600/10 text-violet-400 flex items-center justify-center">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-[11px] text-zinc-400">Total Parsed</p>
                  <h4 className="text-xl font-bold text-zinc-100">{parsedItems.length} Titles</h4>
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-zinc-900/40 border border-zinc-900 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-[11px] text-zinc-400">Canonical Matches</p>
                  <h4 className="text-xl font-bold text-emerald-400">
                    {previewResult.matched_titles} Matched
                    {previewResult.total_items > 0 &&
                      ` (${Math.round((previewResult.matched_titles / previewResult.total_items) * 100)}%)`}
                  </h4>
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-zinc-900/40 border border-zinc-900 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-[11px] text-zinc-400">Conflicts / Collisions</p>
                  <h4 className="text-xl font-bold text-amber-400">{previewResult.conflicts_count} Detected</h4>
                </div>
              </div>
            </div>

            {/* Conflict Strategy Selector */}
            <div className="p-5 rounded-3xl bg-zinc-900/40 border border-zinc-900 space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold text-zinc-200">
                <Sliders className="w-4 h-4 text-violet-400" />
                <span>Conflict Resolution Strategy</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {[
                  {
                    id: "KEEP_EXISTING",
                    title: "Keep Existing Vault Data",
                    desc: "Preserves existing ratings and watch logs if records conflict.",
                  },
                  {
                    id: "OVERWRITE",
                    title: "Overwrite with Imported",
                    desc: "Replaces conflicting vault records with imported values.",
                  },
                  {
                    id: "MERGE",
                    title: "Merge Non-Null Fields",
                    desc: "Fills in missing dates and ratings without erasing existing data.",
                  },
                ].map((strat) => (
                  <button
                    key={strat.id}
                    type="button"
                    onClick={() => setConflictStrategy(strat.id as "KEEP_EXISTING" | "OVERWRITE" | "MERGE")}
                    className={`p-3.5 rounded-2xl border text-left space-y-1 transition-all cursor-pointer ${
                      conflictStrategy === strat.id
                        ? "bg-violet-600/15 border-violet-500 shadow-md"
                        : "bg-zinc-950/60 border-zinc-800 hover:border-zinc-700"
                    }`}
                  >
                    <p className="text-xs font-bold text-zinc-100">{strat.title}</p>
                    <p className="text-[10px] text-zinc-400 leading-relaxed">{strat.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Parsed Items Review Table */}
            <div className="p-6 rounded-3xl bg-zinc-900/40 border border-zinc-900 space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-zinc-900">
                <h4 className="text-xs font-bold text-zinc-200 uppercase tracking-wider">
                  Parsed Records Preview ({parsedItems.length})
                </h4>
                <span className="text-[11px] text-zinc-500">Click title to disambiguate</span>
              </div>

              <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
                {parsedItems.map((item, idx) => {
                  const verdict = previewResult?.item_verdicts?.[idx];
                  const isUnmatched = verdict?.verdict === "UNMATCHED" || verdict?.matched === false;
                  const isProbable = verdict?.verdict === "PROBABLE_MATCH";

                  return (
                    <div
                      key={idx}
                      className={`p-3 rounded-2xl border flex items-center justify-between gap-4 transition-all ${
                        isUnmatched
                          ? "bg-rose-950/15 border-rose-500/30 hover:border-rose-500/50"
                          : isProbable
                          ? "bg-zinc-950/90 border-amber-500/30 hover:border-amber-500/50"
                          : "bg-zinc-950/80 border-zinc-850 hover:border-zinc-700"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-mono font-bold shrink-0 ${
                            isUnmatched
                              ? "bg-rose-600/15 text-rose-400 border border-rose-500/20"
                              : isProbable
                              ? "bg-amber-600/15 text-amber-400 border border-amber-500/20"
                              : "bg-violet-600/10 text-violet-400"
                          }`}
                        >
                          {idx + 1}
                        </div>

                        <div className="space-y-0.5">
                          <div className="flex items-center gap-2">
                            <span className={`text-xs font-bold ${isUnmatched ? "text-rose-200" : "text-zinc-100"}`}>
                              {item.canonical_title}
                            </span>
                            {item.production_year && (
                              <span className="text-[10px] text-zinc-500">({item.production_year})</span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 text-[10px] text-zinc-400">
                            {item.rating_value && (
                              <span className="text-amber-400 font-semibold">★ {item.rating_value}/5</span>
                            )}
                            {item.notes && <span className="text-zinc-500 truncate max-w-xs">{item.notes}</span>}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          onClick={() => {
                            setDisambiguationIndex(idx);
                            setCustomTitleInput(item.canonical_title || "");
                          }}
                          className={`px-2.5 py-1 rounded-lg text-[10px] font-medium transition-colors cursor-pointer border ${
                            isUnmatched
                              ? "bg-rose-600/20 text-rose-200 border-rose-500/40 hover:bg-rose-600/30"
                              : "bg-zinc-900 hover:bg-zinc-800 text-zinc-300 border-zinc-800"
                          }`}
                        >
                          Disambiguate
                        </button>

                        {verdict ? (
                          verdict.verdict === "EXACT_MATCH" ? (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              <Check className="w-3 h-3" />
                              <span>Exact ({Math.round(verdict.confidence_score * 100)}%)</span>
                            </span>
                          ) : verdict.verdict === "PROBABLE_MATCH" ? (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                              <Sparkles className="w-3 h-3" />
                              <span>Probable ({Math.round(verdict.confidence_score * 100)}%)</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                              <AlertTriangle className="w-3 h-3" />
                              <span>Unmatched</span>
                            </span>
                          )
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            <Check className="w-3 h-3" />
                            <span>Matched</span>
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Ingestion Progress Bar */}
              {applyMutation.isPending && (
                <div className="space-y-1.5 pt-2">
                  <div className="flex items-center justify-between text-xs text-zinc-400">
                    <span className="flex items-center gap-1.5 text-emerald-400">
                      <Sparkles className="w-3.5 h-3.5 animate-spin" />
                      <span>Writing canonical records to personal vault...</span>
                    </span>
                    <span className="font-mono">{applyProgress}%</span>
                  </div>
                  <div className="h-2 w-full bg-zinc-950 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                      style={{ width: `${applyProgress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Navigation Back / Next */}
              <div className="flex items-center justify-between pt-4 border-t border-zinc-900">
                <button
                  type="button"
                  onClick={() => setCurrentStep(1)}
                  disabled={applyMutation.isPending}
                  className="px-4 py-2 rounded-xl text-xs font-medium text-zinc-400 hover:text-zinc-200 bg-zinc-900 border border-zinc-800 transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Back to Editor</span>
                </button>

                <button
                  type="button"
                  onClick={handleApplyImport}
                  disabled={applyMutation.isPending}
                  className="px-6 py-2.5 rounded-xl text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 transition-all cursor-pointer shadow-lg shadow-emerald-600/30 flex items-center gap-2"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>{applyMutation.isPending ? "Ingesting Records..." : "Confirm & Ingest to Vault"}</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── STEP 3: INGEST & APPLY (COMPLETION) ─────────────────────────── */}
        {currentStep === 3 && applyResult && (
          <div className="max-w-2xl mx-auto space-y-6">
            <div className="p-8 rounded-3xl bg-zinc-900/40 border border-zinc-900 text-center space-y-6">
              <div className="w-16 h-16 rounded-3xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto shadow-xl shadow-emerald-950/20">
                <CheckCircle2 className="w-8 h-8" />
              </div>

              <div className="space-y-1.5">
                <h3 className="text-xl font-bold text-zinc-100">Library Migration Successful!</h3>
                <p className="text-xs text-zinc-400 max-w-md mx-auto">
                  {applyResult.applied_count} entertainment records have been written idempotently into your personal vault.
                </p>
              </div>

              {/* Progress Summary Card */}
              <div className="p-4 rounded-2xl bg-zinc-950/80 border border-zinc-850 grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-[10px] text-zinc-500 uppercase">Records Applied</p>
                  <p className="text-lg font-bold text-emerald-400">{applyResult.applied_count}</p>
                </div>
                <div>
                  <p className="text-[10px] text-zinc-500 uppercase">Conflicts Handled</p>
                  <p className="text-lg font-bold text-zinc-200">{applyResult.conflicts_resolved}</p>
                </div>
                <div>
                  <p className="text-[10px] text-zinc-500 uppercase">Strategy</p>
                  <p className="text-xs font-bold text-violet-400 mt-1">{applyResult.strategy_applied}</p>
                </div>
              </div>

              {/* Quick Jump Links */}
              <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
                <Link
                  href="/history"
                  className="w-full sm:w-auto px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 transition-all flex items-center justify-center gap-2 shadow-lg shadow-violet-600/20"
                >
                  <History className="w-3.5 h-3.5" />
                  <span>View Watch History</span>
                </Link>

                <Link
                  href="/watchlist"
                  className="w-full sm:w-auto px-5 py-2.5 rounded-xl text-xs font-semibold text-zinc-300 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 transition-all flex items-center justify-center gap-2"
                >
                  <Bookmark className="w-3.5 h-3.5" />
                  <span>View Watchlist</span>
                </Link>

                <button
                  type="button"
                  onClick={handleResetWizard}
                  className="w-full sm:w-auto px-5 py-2.5 rounded-xl text-xs font-semibold text-zinc-400 hover:text-zinc-200 transition-all flex items-center justify-center gap-2"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Import More</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Disambiguation Title Picker Modal */}
      {disambiguationIndex !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="relative w-full max-w-md p-6 rounded-3xl bg-zinc-900 border border-zinc-800 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
              <div className="flex items-center gap-2">
                <Search className="w-4 h-4 text-violet-400" />
                <h3 className="text-sm font-bold text-zinc-100">Disambiguate Canonical Title</h3>
              </div>
              <button
                onClick={() => setDisambiguationIndex(null)}
                className="p-1 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3">
              <p className="text-xs text-zinc-400">
                Adjust title name or select canonical entity to resolve matching uncertainty:
              </p>

              <input
                type="text"
                value={customTitleInput}
                onChange={(e) => setCustomTitleInput(e.target.value)}
                placeholder="Search canonical title..."
                className="w-full px-3.5 py-2.5 rounded-xl bg-zinc-950 border border-zinc-800 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setDisambiguationIndex(null)}
                className="px-4 py-2 rounded-xl text-xs text-zinc-400 hover:text-zinc-200"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleResolveDisambiguation(customTitleInput)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500"
              >
                Save Resolution
              </button>
            </div>
          </div>
        </div>
      )}
    </PageContainer>
  );
}
