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
        <div className="flex flex-col items-center justify-center p-12 text-center rounded-2xl bg-zinc-900/30 border border-zinc-900 backdrop-blur-md min-h-[300px]">
          <div className="w-12 h-12 rounded-2xl bg-violet-600/10 border border-violet-500/20 flex items-center justify-center mb-4 text-violet-400">
            <Lock className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-zinc-100 mb-2">
            Authentication Required for Personal Library
          </h3>
          <p className="text-xs sm:text-sm text-zinc-400 max-w-md mb-6 leading-relaxed">
            Personal library entries and watch history endpoints (<code className="text-xs bg-zinc-800 px-1.5 py-0.5 rounded text-violet-300 font-mono">/v1/me/*</code>) require authenticated Bearer tokens.
          </p>

          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-violet-950/20 border border-violet-800/30 text-xs text-violet-300">
            <ShieldAlert className="w-4 h-4 shrink-0 text-violet-400" />
            <span>Session integration active for authorized profiles.</span>
          </div>
        </div>
      </div>
    </PageContainer>
  );
}
