"use client";

import React from "react";
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
  if (isLoading) {
    return (
      <div className="text-ink-mute text-sm p-4">Loading sessions...</div>
    );
  }

  if (error) {
    return (
      <div className="text-no text-sm p-4">
        {error}{" "}
        <button onClick={onRetry} className="underline">
          Retry
        </button>
      </div>
    );
  }

  if (runs.length === 0) {
    return <div className="text-ink-mute text-sm p-4">No sessions yet.</div>;
  }

  return (
    <div className="px-2.5 pb-2.5 overflow-auto flex-1">
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
  );
}
