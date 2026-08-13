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
    <div className="flex flex-col items-center justify-center p-12 text-center rounded-xl bg-slate-900/40 border border-slate-800/60 backdrop-blur-sm min-h-[260px]">
      <div className="relative flex items-center justify-center mb-4">
        <div className="absolute w-12 h-12 rounded-full bg-violet-600/20 animate-ping" />
        <Loader2 className="w-8 h-8 text-violet-400 animate-spin relative z-10" />
      </div>
      <p className="text-sm font-medium text-slate-300">{message}</p>
      <p className="text-xs text-slate-500 mt-1">Connecting to local application shell...</p>
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
    <div className="flex flex-col items-center justify-center p-12 text-center rounded-xl bg-slate-900/40 border border-slate-800/60 backdrop-blur-sm min-h-[280px]">
      <div className="w-12 h-12 rounded-full bg-slate-800/80 flex items-center justify-center mb-4 border border-slate-700/50">
        <Inbox className="w-6 h-6 text-slate-400" />
      </div>
      <h3 className="text-base font-semibold text-slate-200 mb-1">{title}</h3>
      <p className="text-sm text-slate-400 max-w-md mb-6">{description}</p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 text-xs font-medium text-violet-200 bg-violet-600/30 hover:bg-violet-600/50 border border-violet-500/40 rounded-lg transition-all cursor-pointer"
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
    <div className="flex flex-col items-center justify-center p-12 text-center rounded-xl bg-rose-950/20 border border-rose-900/40 backdrop-blur-sm min-h-[280px]">
      <div className="w-12 h-12 rounded-full bg-rose-900/40 flex items-center justify-center mb-4 border border-rose-800/50">
        <AlertTriangle className="w-6 h-6 text-rose-400" />
      </div>
      <h3 className="text-base font-semibold text-rose-200 mb-1">{title}</h3>
      <p className="text-sm text-slate-400 max-w-md mb-6">{description}</p>
      {onAction && (
        <button
          onClick={onAction}
          className="inline-flex items-center gap-2 px-4 py-2 text-xs font-medium text-rose-200 bg-rose-900/40 hover:bg-rose-900/60 border border-rose-700/50 rounded-lg transition-all cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          {actionLabel}
        </button>
      )}
    </div>
  );
};
