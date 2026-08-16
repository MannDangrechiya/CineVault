import React from "react";
import { PageContainer } from "@/components/ui/PageContainer";
import { Sparkles, Moon, Shield, Server, Database } from "lucide-react";

export default function SettingsPage() {
  return (
    <PageContainer
      title="Settings & System Status"
      subtitle="Application configuration, theme preferences, and sync status"
    >
      <div className="space-y-6 max-w-4xl">
        {/* Appearance Settings */}
        <div className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-900 space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-zinc-900 text-sm font-bold text-zinc-100">
            <Moon className="w-4 h-4 text-violet-400" />
            <span>Theme & Display Aesthetics</span>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-xs font-semibold text-zinc-200">Active Theme Mode</h4>
              <p className="text-[11px] text-zinc-500">True OLED Black with violet & emerald accents</p>
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
              <span className="text-zinc-500 text-[10px] uppercase">Embedding Dimension</span>
              <p className="text-zinc-200 font-mono font-bold">1536-dim text-embedding-3</p>
            </div>
            <div className="p-4 rounded-xl bg-zinc-950/60 border border-zinc-900 space-y-1">
              <span className="text-zinc-500 text-[10px] uppercase">Vector Similarity Index</span>
              <p className="text-emerald-400 font-mono font-bold">HNSW Cosine Distance</p>
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
                <span>Identity & Auth: Keycloak OIDC + PKCE</span>
              </div>
              <span className="text-emerald-400 font-mono text-[11px]">Ready</span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-zinc-950/60 border border-zinc-900">
              <div className="flex items-center gap-2 text-zinc-300">
                <Database className="w-4 h-4 text-violet-400" />
                <span>Local Cache: Dexie IndexedDB Offline Sync</span>
              </div>
              <span className="text-violet-300 font-mono text-[11px]">Active</span>
            </div>
          </div>
        </div>
      </div>
    </PageContainer>
  );
}
