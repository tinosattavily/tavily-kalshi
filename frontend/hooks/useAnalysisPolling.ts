"use client";

import { useEffect, useRef, useCallback, MutableRefObject } from "react";
import { logger } from "../lib/logger";
import type { AnalysisResults, RunStatus } from "../types";

interface UseAnalysisPollingOptions {
  runId: string | null;
  onStatusUpdate: (status: RunStatus) => void;
  onResultsUpdate: (updater: (prev: AnalysisResults | null) => AnalysisResults | null) => void;
  onMarketSelectionRequired: (marketOptions: Array<{ market_id?: string; slug?: string; question?: string }>) => void;
  onComplete: (marketId?: string) => void;
  onRefreshTrigger: () => void;
}

interface UseAnalysisPollingReturn {
  pollingRef: MutableRefObject<boolean>;
  runIdRef: MutableRefObject<string | null>;
  startPolling: (newRunId: string) => void;
  stopPolling: () => void;
}

/**
 * Hook for polling analysis run status and updating results progressively
 */
export function useAnalysisPolling({
  runId,
  onStatusUpdate,
  onResultsUpdate,
  onMarketSelectionRequired,
  onComplete,
  onRefreshTrigger,
}: UseAnalysisPollingOptions): UseAnalysisPollingReturn {
  const pollingRef = useRef<boolean>(false);
  const runIdRef = useRef<string | null>(null);

  const startPolling = useCallback((newRunId: string) => {
    runIdRef.current = newRunId;
    pollingRef.current = true;
  }, []);

  const stopPolling = useCallback(() => {
    pollingRef.current = false;
  }, []);

  useEffect(() => {
    // Use ref as fallback if state hasn't updated yet
    const effectiveRunId = runId || runIdRef.current;

    // No run in progress yet
    if (!effectiveRunId) {
      return;
    }

    if (typeof effectiveRunId !== "string") {
      return;
    }

    if (!pollingRef.current) {
      return;
    }

    const trimmedRunId = effectiveRunId.trim();
    if (trimmedRunId === "" || trimmedRunId === "undefined" || trimmedRunId === "null") {
      return;
    }

    const currentRunId = trimmedRunId;
    let cancelled = false;

    async function poll() {
      if (cancelled || !pollingRef.current) {
        return;
      }

      const runIdToUse = currentRunId;
      if (!runIdToUse || typeof runIdToUse !== "string" || runIdToUse.trim() === "" || runIdToUse === "undefined" || runIdToUse === "null") {
        logger.error("runId is invalid in poll function!", runIdToUse);
        return;
      }

      try {
        const response = await fetch(`/api/run/${runIdToUse}`);
        if (!response.ok) {
          if (response.status === 404) {
            window.setTimeout(poll, 1500);
            return;
          }
          if (response.status === 500) {
            try {
              const errorData = await response.json();
              const _errorDetail = errorData.detail || errorData.error || "Internal server error";
            } catch {
              // Ignore JSON parse errors
            }
            window.setTimeout(poll, 3000);
            return;
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const run = data.run;

        if (!run) {
          if (!cancelled) {
            window.setTimeout(poll, 1500);
          }
          return;
        }

        if (!cancelled) {
          if (run.status) {
            onStatusUpdate(run.status);
          }

          onResultsUpdate((prevResults) => {
            if (!prevResults) {
              return {
                market_snapshot: {},
                event_context: {},
                news_context: {},
                signal: {},
                decision: {},
                report: {},
              };
            }

            const updatedResults: AnalysisResults = { ...prevResults };

            if (run.status?.market === "done") {
              if (run.market_snapshot && Object.keys(run.market_snapshot).length > 0) {
                updatedResults.market_snapshot = run.market_snapshot;
              }
              if (run.event_context) {
                updatedResults.event_context = run.event_context;
              }
              if (run.market_options && Array.isArray(run.market_options) && run.market_options.length > 0) {
                updatedResults.market_options = run.market_options;
                if (!run.market_snapshot || Object.keys(run.market_snapshot).length === 0) {
                  updatedResults.requires_market_selection = true;
                } else {
                  updatedResults.requires_market_selection = false;
                }
              }
            }

            if (run.status?.news === "done" && run.news_context) {
              updatedResults.news_context = run.news_context;
              const articlesCount = Array.isArray(run.news_context.articles)
                ? run.news_context.articles.length
                : 0;
              logger.debug(
                "News context received from backend",
                run.run_id,
                `articles: ${articlesCount}`,
                `has_summary: ${!!run.news_context.summary}`,
                `keys: ${Object.keys(run.news_context).join(", ")}`
              );
            }

            if (run.status?.signal === "done" && run.signal) {
              updatedResults.signal = run.signal;
              updatedResults.decision = run.decision || updatedResults.decision;
            }

            if (run.status?.report === "done" && run.report) {
              updatedResults.report = run.report;
            }

            return updatedResults;
          });

          // Check if market selection is required
          const requiresMarketSelection =
            run.market_options &&
            Array.isArray(run.market_options) &&
            run.market_options.length > 0 &&
            (!run.market_snapshot || Object.keys(run.market_snapshot).length === 0);

          if (requiresMarketSelection) {
            onMarketSelectionRequired(run.market_options);
            pollingRef.current = false;
            return;
          }

          // Check if all phases are done or errored
          const status = run.status || {};
          const phases = Object.values(status);
          const allDoneOrError =
            phases.length > 0 &&
            phases.every((s) => s === "done" || s === "error");

          if (allDoneOrError) {
            pollingRef.current = false;
            onComplete(run.selected_market_id || run.venue_market_id || run.market_snapshot?.market_id || run.market_snapshot?.slug);
            onRefreshTrigger();
          } else {
            window.setTimeout(poll, 1500);
          }
        }
      } catch (error) {
        logger.error("Error polling run status:", error);
        if (!cancelled && pollingRef.current) {
          if (error instanceof Error && error.message.includes("Network error")) {
            logger.warn("Network error while polling:", error.message);
          }
          window.setTimeout(poll, 2500);
        }
      }
    }

    poll();

    return () => {
      cancelled = true;
    };
  }, [runId, onStatusUpdate, onResultsUpdate, onMarketSelectionRequired, onComplete, onRefreshTrigger]);

  return {
    pollingRef,
    runIdRef,
    startPolling,
    stopPolling,
  };
}
