import React from "react";
import { PageContainer } from "@/components/ui/PageContainer";
import { Lock, ShieldAlert } from "lucide-react";

export default function LibraryPage() {
  return (
    <PageContainer
      title="Personal Library"
      subtitle="Organized collection of titles added to your personal library (CAT-2)"
    >
      <div className="space-y-6">
        <div className="flex flex-col items-center justify-center p-12 text-center rounded-xl bg-slate-900/40 border border-slate-800/60 backdrop-blur-sm min-h-[300px]">
          <div className="w-12 h-12 rounded-full bg-amber-950/60 border border-amber-800/50 flex items-center justify-center mb-4 text-amber-400">
            <Lock className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-200 mb-2">
            Authentication Required for Personal Library
          </h3>
          <p className="text-sm text-slate-400 max-w-md mb-6 leading-relaxed">
            Personal library entries and watch history endpoints (<code className="text-xs bg-slate-800 px-1.5 py-0.5 rounded text-amber-300 font-mono">/v1/me/*</code>) require authenticated Bearer tokens.
          </p>

          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-950/30 border border-amber-800/40 text-xs text-amber-300">
            <ShieldAlert className="w-4 h-4 shrink-0" />
            <span>Authentication & session integration will be handled in the upcoming Auth Task.</span>
          </div>
        </div>
      </div>
    </PageContainer>
  );
}
