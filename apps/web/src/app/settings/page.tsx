"use client";

import React, { useState } from "react";
import Link from "next/link";
import { PageContainer } from "@/components/ui/PageContainer";
import { Sparkles, Moon, Shield, Server, Download, FileSpreadsheet, FileCode, FileText, ArrowUpRight, CheckCircle2, AlertCircle } from "lucide-react";
import { downloadExport } from "@/lib/api/import";

export default function SettingsPage() {
  const [downloadingFormat, setDownloadingFormat] = useState<string | null>(null);
  const [exportNotice, setExportNotice] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleExport = async (format: "json" | "csv" | "excel" | "markdown") => {
    try {
      setDownloadingFormat(format);
      setExportNotice(null);
      await downloadExport(format);
      setExportNotice({ type: "success", text: `Successfully generated and downloaded ${format.toUpperCase()} export archive!` });
    } catch (err) {
      setExportNotice({ type: "error", text: err instanceof Error ? err.message : "Export failed. Please try again." });
    } finally {
      setDownloadingFormat(null);
    }
  };

  return (
    <PageContainer
      title="Settings & System Status"
      subtitle="Application configuration, theme preferences, and personal data portability"
    >
      <div className="space-y-6 max-w-4xl">
        {/* Data Portability & Export Section */}
        <div className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-900 space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-zinc-900">
            <div className="flex items-center gap-2 text-sm font-bold text-zinc-100">
              <Download className="w-4 h-4 text-violet-400" />
              <span>Personal Data Portability & Export</span>
            </div>
            <Link
              href="/import"
              className="flex items-center gap-1 text-xs font-semibold text-violet-400 hover:text-violet-300 transition-colors"
            >
              <span>Import Wizard</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <p className="text-xs text-zinc-400 leading-relaxed">
            Your data belongs to you. Export your complete library, watch history, ratings, private notes, reviews, and custom collections at any time in multiple open formats.
          </p>

          {exportNotice && (
            <div
              className={`p-3 rounded-xl border flex items-center gap-2.5 text-xs ${
                exportNotice.type === "success"
                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                  : "bg-rose-500/10 border-rose-500/30 text-rose-300"
              }`}
            >
              {exportNotice.type === "success" ? (
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
              ) : (
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              )}
              <span>{exportNotice.text}</span>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2">
            {/* JSON Export */}
            <button
              onClick={() => handleExport("json")}
              disabled={downloadingFormat !== null}
              className="p-4 rounded-xl bg-zinc-950/80 border border-zinc-800 hover:border-violet-500/50 hover:bg-zinc-900/50 transition-all text-left space-y-2 group cursor-pointer disabled:opacity-50"
            >
              <div className="w-8 h-8 rounded-lg bg-violet-600/10 border border-violet-500/20 text-violet-400 flex items-center justify-center group-hover:scale-110 transition-transform">
                <FileCode className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-zinc-100 group-hover:text-violet-300 transition-colors">JSON v2.0</h4>
                <p className="text-[10px] text-zinc-400 mt-0.5">Lossless schema backup</p>
              </div>
              <span className="inline-block text-[10px] font-semibold text-violet-400">
                {downloadingFormat === "json" ? "Downloading..." : "Download JSON →"}
              </span>
            </button>

            {/* CSV ZIP Export */}
            <button
              onClick={() => handleExport("csv")}
              disabled={downloadingFormat !== null}
              className="p-4 rounded-xl bg-zinc-950/80 border border-zinc-800 hover:border-violet-500/50 hover:bg-zinc-900/50 transition-all text-left space-y-2 group cursor-pointer disabled:opacity-50"
            >
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center group-hover:scale-110 transition-transform">
                <FileSpreadsheet className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-zinc-100 group-hover:text-emerald-300 transition-colors">CSV ZIP</h4>
                <p className="text-[10px] text-zinc-400 mt-0.5">Relational tables archive</p>
              </div>
              <span className="inline-block text-[10px] font-semibold text-emerald-400">
                {downloadingFormat === "csv" ? "Downloading..." : "Download ZIP →"}
              </span>
            </button>

            {/* Excel XLSX Export */}
            <button
              onClick={() => handleExport("excel")}
              disabled={downloadingFormat !== null}
              className="p-4 rounded-xl bg-zinc-950/80 border border-zinc-800 hover:border-violet-500/50 hover:bg-zinc-900/50 transition-all text-left space-y-2 group cursor-pointer disabled:opacity-50"
            >
              <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center group-hover:scale-110 transition-transform">
                <FileSpreadsheet className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-zinc-100 group-hover:text-cyan-300 transition-colors">Excel (.xlsx)</h4>
                <p className="text-[10px] text-zinc-400 mt-0.5">Multi-sheet workbook</p>
              </div>
              <span className="inline-block text-[10px] font-semibold text-cyan-400">
                {downloadingFormat === "excel" ? "Downloading..." : "Download XLSX →"}
              </span>
            </button>

            {/* Markdown Export */}
            <button
              onClick={() => handleExport("markdown")}
              disabled={downloadingFormat !== null}
              className="p-4 rounded-xl bg-zinc-950/80 border border-zinc-800 hover:border-violet-500/50 hover:bg-zinc-900/50 transition-all text-left space-y-2 group cursor-pointer disabled:opacity-50"
            >
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center group-hover:scale-110 transition-transform">
                <FileText className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-zinc-100 group-hover:text-amber-300 transition-colors">Markdown (.md)</h4>
                <p className="text-[10px] text-zinc-400 mt-0.5">Readable document archive</p>
              </div>
              <span className="inline-block text-[10px] font-semibold text-amber-400">
                {downloadingFormat === "markdown" ? "Downloading..." : "Download MD →"}
              </span>
            </button>
          </div>
        </div>

        {/* Appearance Settings */}
        <div className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-900 space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-zinc-900 text-sm font-bold text-zinc-100">
            <Moon className="w-4 h-4 text-violet-400" />
            <span>Theme & Display Aesthetics</span>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-xs font-semibold text-zinc-200">Active Theme Mode</h4>
              <p className="text-[11px] text-zinc-400">True OLED Black with violet & emerald accents</p>
            </div>
            <span className="px-3 py-1 text-xs font-semibold text-violet-300 bg-violet-600/15 border border-violet-500/30 rounded-full">
              Cinematic OLED (#09090B)
            </span>
          </div>
        </div>

        {/* AI Vector Engine Settings */}
        <div className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-900 space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-zinc-900 text-sm font-bold text-zinc-100">
            <Sparkles className="w-4 h-4 text-emerald-400" />
            <span>AI Neural Taste Engine</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-zinc-950/60 border border-zinc-900 space-y-1">
              <span className="text-zinc-400 text-[10px] uppercase">Embedding Dimension</span>
              <p className="text-zinc-200 font-mono font-bold">384-dim (all-MiniLM-L6-v2)</p>
            </div>
            <div className="p-4 rounded-xl bg-zinc-950/60 border border-zinc-900 space-y-1">
              <span className="text-zinc-400 text-[10px] uppercase">Vector Similarity Index</span>
              <p className="text-emerald-400 font-mono font-bold">pgvector Cosine Distance</p>
            </div>
          </div>
        </div>

        {/* Backend & Security */}
        <div className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-900 space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-zinc-900 text-sm font-bold text-zinc-100">
            <Server className="w-4 h-4 text-violet-400" />
            <span>Backend Services & Privacy</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-3 rounded-xl bg-zinc-950/60 border border-zinc-900">
              <div className="flex items-center gap-2 text-zinc-300">
                <Shield className="w-4 h-4 text-emerald-400" />
                <span>Identity & Auth: Native (FastAPI HS256)</span>
              </div>
              <span className="text-violet-300 font-mono text-[11px]">Configured</span>
            </div>
          </div>
        </div>
      </div>
    </PageContainer>
  );
}
