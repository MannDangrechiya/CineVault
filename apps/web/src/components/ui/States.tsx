"use client";

import React from "react";
import { Loader2, AlertTriangle, Inbox, RefreshCw } from "lucide-react";

interface StateProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export const LoadingState: React.FC<{ message?: string }> = ({
  message = "Loading CineVault data...",
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center rounded-2xl bg-zinc-900/30 border border-zinc-900 backdrop-blur-md min-h-[260px]">
      <div className="relative flex items-center justify-center mb-4">
        <div className="absolute w-12 h-12 rounded-full bg-violet-600/20 animate-ping" />
        <Loader2 className="w-8 h-8 text-violet-400 animate-spin relative z-10" />
      </div>
      <p className="text-sm font-semibold text-zinc-200">{message}</p>
      <p className="text-xs text-zinc-400 mt-1">Connecting to CineVault OS backend...</p>
    </div>
  );
};

export const EmptyState: React.FC<StateProps> = ({
  title = "No Items Found",
  description = "There are currently no items in this view.",
  actionLabel,
  onAction,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center rounded-2xl bg-zinc-900/30 border border-zinc-900 backdrop-blur-md min-h-[280px]">
      <div className="w-12 h-12 rounded-2xl bg-zinc-900 flex items-center justify-center mb-4 border border-zinc-800">
        <Inbox className="w-6 h-6 text-zinc-400" />
      </div>
      <h3 className="text-base font-bold text-zinc-100 mb-1">{title}</h3>
      <p className="text-xs sm:text-sm text-zinc-400 max-w-md mb-6 leading-relaxed">{description}</p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="px-5 py-2 text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 rounded-full shadow-lg shadow-violet-600/20 transition-all cursor-pointer"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
};

export const ErrorState: React.FC<StateProps> = ({
  title = "Something Went Wrong",
  description = "An error occurred while loading this section. Please try again.",
  actionLabel = "Retry",
  onAction,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center rounded-2xl bg-rose-950/10 border border-rose-900/30 backdrop-blur-md min-h-[280px]">
      <div className="w-12 h-12 rounded-2xl bg-rose-950/40 flex items-center justify-center mb-4 border border-rose-900/50">
        <AlertTriangle className="w-6 h-6 text-rose-400" />
      </div>
      <h3 className="text-base font-bold text-rose-200 mb-1">{title}</h3>
      <p className="text-xs sm:text-sm text-zinc-400 max-w-md mb-6 leading-relaxed">{description}</p>
      {onAction && (
        <button
          onClick={onAction}
          className="inline-flex items-center gap-2 px-5 py-2 text-xs font-medium text-rose-200 bg-rose-900/30 hover:bg-rose-900/50 border border-rose-700/50 rounded-full transition-all cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          {actionLabel}
        </button>
      )}
    </div>
  );
};
