"use client";

import React from "react";
import { RefreshCw, History } from "lucide-react";
import clsx from "clsx";

interface HistorySidebarHeaderProps {
  isLoading: boolean;
  onRefresh: () => void;
}

export default function HistorySidebarHeader({
  isLoading,
  onRefresh,
}: HistorySidebarHeaderProps): React.JSX.Element {
  return (
    <div className="h-full flex flex-col bg-white/60 backdrop-blur-sm border-l border-b border-neutral-300">
      <div className="p-4">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold text-neutral-800 flex items-center gap-2">
            <History className="w-5 h-5" />
            Recent Sessions
          </h2>
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="p-1.5 rounded-md hover:bg-neutral-200 transition-colors disabled:opacity-50"
            title="Refresh recent sessions"
          >
            <RefreshCw
              className={clsx("w-4 h-4 text-neutral-600", isLoading && "animate-spin")}
            />
          </button>
        </div>
        <p className="text-xs text-neutral-500">Click a card to view analysis</p>
      </div>
    </div>
  );
}
