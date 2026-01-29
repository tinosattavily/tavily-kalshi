"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";

import { History, RefreshCw } from "lucide-react";
import clsx from "clsx";

import RecentMarketCard, { RecentRun } from "./RecentMarketCard";
import { logger } from "../../lib/logger";

const REQUEST_TIMEOUT_MS = 30000;

interface RecentSessionsProps {
  onRunSelect: (run: RecentRun) => void;
  activeRunId?: string;
  refreshTrigger?: number;
}

function isAbortError(err: unknown): boolean {
  if (err instanceof DOMException && err.name === "AbortError") return true;
  if (!(err instanceof Error)) return false;
  return err.name === "AbortError" || err.message === "terminated" || err.message.includes("aborted");
}

async function parseErrorResponse(response: Response): Promise<{ detail?: string; error?: string }> {
  try {
    const text = await response.text();
    return text ? JSON.parse(text) : {};
  } catch {
    return { error: response.statusText || `HTTP ${response.status}` };
  }
}

export default function RecentSessions({
  onRunSelect,
  activeRunId,
  refreshTrigger = 0,
}: RecentSessionsProps): React.JSX.Element {
  const [runs, setRuns] = useState<RecentRun[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Check resolutions for past markets in the background
  const checkResolutions = useCallback(async () => {
    try {
      const response = await fetch("/api/runs/check-resolutions", {
        method: "POST",
      });
      if (response.ok) {
        const data = await response.json();
        if (data.updated > 0) {
          logger.info(`Updated ${data.updated} market resolutions`);
          // Refresh runs to show updated resolution data
          return true;
        }
      }
    } catch (err) {
      // Silently fail - resolution checking is optional
      logger.debug("Resolution check failed:", err);
    }
    return false;
  }, []);

  const fetchRecentRuns = useCallback(async (checkResolutionsFirst = false) => {
    abortControllerRef.current?.abort();

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    setIsLoading(true);
    setError(null);

    // Check resolutions in background before fetching runs
    if (checkResolutionsFirst) {
      await checkResolutions();
    }

    const timeoutId = setTimeout(() => {
      if (!abortController.signal.aborted) {
        abortController.abort();
      }
    }, REQUEST_TIMEOUT_MS);

    try {
      const response = await fetch("/api/runs/recent?limit=20", {
        signal: abortController.signal,
      });

      clearTimeout(timeoutId);

      if (abortController.signal.aborted) return;

      if (!response.ok) {
        const errorData = await parseErrorResponse(response);
        if (abortController.signal.aborted) return;
        throw new Error(
          errorData.detail || errorData.error || `Failed to fetch recent runs (${response.status})`,
        );
      }

      const data = await response.json();

      if (!abortController.signal.aborted) {
        setRuns(data.runs || []);
      }
    } catch (err) {
      clearTimeout(timeoutId);

      if (abortController.signal.aborted || isAbortError(err)) {
        return;
      }

      if (!abortController.signal.aborted) {
        let errorMessage = "Failed to load recent sessions";
        if (err instanceof Error && !isAbortError(err)) {
          errorMessage = err.message;
        }
        setError(errorMessage);
        logger.error("Error fetching recent runs:", err);
      }
    } finally {
      if (!abortController.signal.aborted) {
        setIsLoading(false);
      }
    }
  }, [checkResolutions]);

  useEffect(() => {
    // Check resolutions on initial load
    fetchRecentRuns(true);
    return () => {
      abortControllerRef.current?.abort();
    };
  }, [refreshTrigger, fetchRecentRuns]);

  return (
    <div
      id="recent-sessions"
      className="h-full flex flex-col bg-transparent border-0"
    >
      {/* Header - stays fixed */}
      <div className="flex-shrink-0 p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-neutral-800 flex items-center gap-2">
            <History className="w-5 h-5" />
            Recent Sessions
          </h2>
          <button
            onClick={() => fetchRecentRuns(true)}
            disabled={isLoading}
            className="p-1.5 rounded-md hover:bg-neutral-200 transition-colors disabled:opacity-50"
            title="Refresh recent sessions and check resolutions"
          >
            <RefreshCw
              className={clsx("w-4 h-4 text-neutral-600", isLoading && "animate-spin")}
            />
          </button>
        </div>
      </div>

      {/* Content - scrollable */}
      <div className="flex-1 min-h-0 overflow-y-auto scrollbar-minimal p-4 border-0">
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
                <RecentMarketCard
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

      {/* Footer with info - stays fixed */}
      <div className="flex-shrink-0 border-t border-neutral-300 p-3">
        <p className="text-xs text-neutral-500 text-center">
          Click a card to view analysis
        </p>
      </div>
    </div>
  );
}
