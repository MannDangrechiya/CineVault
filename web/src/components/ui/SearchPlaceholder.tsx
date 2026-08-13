import React from "react";
import { Search, Command } from "lucide-react";

export const SearchPlaceholder: React.FC = () => {
  return (
    <div className="relative w-full max-w-md">
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
        <Search className="w-4 h-4" />
      </div>
      <input
        type="text"
        disabled
        placeholder="Search movies, series, directors, genres... (Placeholder)"
        className="w-full pl-9 pr-12 py-2 text-xs bg-slate-900/80 border border-slate-800 rounded-lg text-slate-300 placeholder:text-slate-500 focus:outline-none focus:border-violet-500/50 cursor-not-allowed opacity-80"
      />
      <div className="absolute inset-y-0 right-0 pr-2.5 flex items-center pointer-events-none text-slate-500">
        <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-mono font-medium text-slate-400 bg-slate-800 border border-slate-700/60 rounded">
          <Command className="w-2.5 h-2.5" /> K
        </kbd>
      </div>
    </div>
  );
};
