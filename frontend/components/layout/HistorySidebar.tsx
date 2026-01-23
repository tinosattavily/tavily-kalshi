"use client";

import React, { useEffect, useState, useRef } from "react";
import { RefreshCw, History } from "lucide-react";
import clsx from "clsx";
import HistoryCard, { RecentRun } from "./HistoryCard";

interface HistorySidebarProps {
  onRunSelect: (run: RecentRun) => void;
  activeRunId?: string;
  refreshTrigger?: number; // Increment this to trigger refresh
}

export default function HistorySidebar({
  onRunSelect,
  activeRunId,
  refreshTrigger = 0,
}: HistorySidebarProps): React.JSX.Element {
  const [runs, setRuns] = useState<RecentRun[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchRecentRuns = async () => {
    // Cancel any pending requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new AbortController for this request
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    setIsLoading(true);
    setError(null);
    
    // Add timeout to prevent hanging requests (30 seconds)
    const timeoutId = globalThis.setTimeout(() => {
      if (!abortController.signal.aborted) {
        abortController.abort();
      }
    }, 30000);
    
    try {
      const response = await fetch("/api/runs/recent?limit=20", {
        signal: abortController.signal,
      });
      
      globalThis.clearTimeout(timeoutId);
      
      // Check if request was aborted before processing response
      if (abortController.signal.aborted) {
        return;
      }
      
      if (!response.ok) {
        // Try to parse error response, but handle cases where response body might be empty
        let errorData: {
          detail?: string;
          error?: string;
          message?: string;
        } = {};
        try {
          const text = await response.text();
          if (text) {
            errorData = JSON.parse(text) as {
              detail?: string;
              error?: string;
              message?: string;
            };
          }
        } catch {
          // If parsing fails, use status text or default message
          errorData = { error: response.statusText || `HTTP ${response.status}` };
        }
        
        // Check again if aborted after async operations
        if (abortController.signal.aborted) {
          return;
        }
        
        throw new Error(
          errorData.detail || errorData.error || `Failed to fetch recent runs (${response.status})`,
        );
      }
      
      const data = await response.json();
      
      // Only update state if request wasn't aborted
      if (!abortController.signal.aborted) {
        setRuns(data.runs || []);
      }
    } catch (err) {
      // Clear timeout if error occurs
      globalThis.clearTimeout(timeoutId);
      // Check if request was aborted - this includes AbortError and DOMException with "terminated" message
      if (
        abortController.signal.aborted ||
        (err instanceof Error && (
          err.name === "AbortError" ||
          err.message === "terminated" ||
          err.message.includes("aborted")
        )) ||
        (err instanceof globalThis.DOMException && err.name === "AbortError")
      ) {
        // Silently ignore abort errors
        return;
      }
      
      // Only set error if request wasn't aborted
      if (!abortController.signal.aborted) {
        let errorMessage = "Failed to load recent sessions";
        if (err instanceof Error) {
          // Don't show "terminated" as error message - it's not user-friendly
          if (err.message === "terminated" || err.message.includes("aborted")) {
            errorMessage = "Request was cancelled";
          } else {
            errorMessage = err.message;
          }
        }
        setError(errorMessage);
        console.error("Error fetching recent runs:", err);
      }
    } finally {
      // Only update loading state if request wasn't aborted
      if (!abortController.signal.aborted) {
        setIsLoading(false);
      }
    }
  };

  useEffect(() => {
    fetchRecentRuns();
    // Cleanup: abort request on unmount or when refreshTrigger changes
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [refreshTrigger]);

  return (
    <div
      id="recent-sessions"
      className="h-full flex flex-col bg-white/90 border-0"
    >
      {/* Header */}
      <div className="p-4 bg-white/90">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold text-neutral-800 flex items-center gap-2">
            <History className="w-5 h-5" />
            Recent Sessions
          </h2>
          <button
            onClick={fetchRecentRuns}
            disabled={isLoading}
            className="p-1.5 rounded-md hover:bg-neutral-200 transition-colors disabled:opacity-50"
            title="Refresh recent sessions"
          >
            <RefreshCw
              className={clsx("w-4 h-4 text-neutral-600", isLoading && "animate-spin")}
            />
          </button>
        </div>
        <p className="text-xs text-neutral-500">
          Click a card to view analysis
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 border-0">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="text-sm text-neutral-500">Loading...</div>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-8">
            <p className="text-sm text-red-600 mb-2">{error}</p>
            <button
              onClick={fetchRecentRuns}
              className="text-xs text-indigo-600 hover:text-indigo-700 underline"
            >
              Try again
            </button>
          </div>
        ) : runs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <History className="w-12 h-12 text-neutral-300 mb-3" />
            <p className="text-sm text-neutral-500 mb-1">No recent sessions</p>
            <p className="text-xs text-neutral-400">
              Run an analysis to see it here
            </p>
          </div>
        ) : (
          <div className="space-y-3 border-0">
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

