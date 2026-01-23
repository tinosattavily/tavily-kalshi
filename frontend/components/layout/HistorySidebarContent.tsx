"use client";

import React from "react";
import { History } from "lucide-react";
import HistoryCard, { RecentRun } from "./HistoryCard";

interface HistorySidebarContentProps {
  runs: RecentRun[];
  isLoading: boolean;
  error: string | null;
  activeRunId?: string;
  onRunSelect: (run: RecentRun) => void;
  onRetry: () => void;
}

export default function HistorySidebarContent({
  runs,
  isLoading,
  error,
  activeRunId,
  onRunSelect,
  onRetry,
}: HistorySidebarContentProps): React.JSX.Element {
  return (
    <div className="h-full flex flex-col bg-white/60 backdrop-blur-sm border-l border-b border-neutral-300">
      <div className="flex-1 overflow-y-auto p-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="text-sm text-neutral-500">Loading...</div>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-8">
            <p className="text-sm text-red-600 mb-2">{error}</p>
            <button
              onClick={onRetry}
              className="text-xs text-indigo-600 hover:text-indigo-700 underline"
            >
              Try again
            </button>
          </div>
        ) : runs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <History className="w-12 h-12 text-neutral-300 mb-3" />
            <p className="text-sm text-neutral-500 mb-1">No recent sessions</p>
            <p className="text-xs text-neutral-400">Run an analysis to see it here</p>
          </div>
        ) : (
          <div className="space-y-3">
            {runs.map((run) => {
              const runId = run.run_id || run._id;
              return (
                <HistoryCard
                  key={runId}
                  run={run}
                  onClick={onRunSelect}
                  isActive={activeRunId === runId}
                />
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
