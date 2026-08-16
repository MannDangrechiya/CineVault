import React from "react";
import { Search, Command } from "lucide-react";

export const SearchPlaceholder: React.FC = () => {
  return (
    <div className="relative w-full max-w-md">
      <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-zinc-500">
        <Search className="w-4 h-4" />
      </div>
      <input
        type="text"
        disabled
        placeholder="Search films, directors, neural genres..."
        className="w-full pl-10 pr-12 py-2 text-xs bg-zinc-900/60 border border-zinc-800/80 rounded-xl text-zinc-200 placeholder:text-zinc-500 focus:outline-none focus:border-violet-500/50 cursor-not-allowed transition-colors"
      />
      <div className="absolute inset-y-0 right-0 pr-2.5 flex items-center pointer-events-none text-zinc-500">
        <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-mono font-medium text-zinc-400 bg-zinc-800 border border-zinc-700/60 rounded-md">
          <Command className="w-2.5 h-2.5" /> K
        </kbd>
      </div>
    </div>
  );
};
