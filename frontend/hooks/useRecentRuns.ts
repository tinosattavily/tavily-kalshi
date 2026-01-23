"use client";

import { useCallback, MutableRefObject } from "react";
import { logger } from "../lib/logger";
import type { AnalysisResults, RunStatus } from "../types";

interface RecentRun {
  run_id?: string;
  _id?: string;
  market_url?: string;
  polymarket_url?: string;
  market_snapshot?: {
    slug?: string;
    [key: string]: unknown;
  };
  event_context?: Record<string, unknown>;
  news_context?: Record<string, unknown>;
  signal?: Record<string, unknown>;
  decision?: Record<string, unknown>;
  report?: Record<string, unknown>;
  status?: {
    market?: string;
    news?: string;
    signal?: string;
    report?: string;
  };
}

interface UseRecentRunsOptions {
  setSelectedRunId: (id: string | null) => void;
  setIsSubmitting: (value: boolean) => void;
  setRunId: (id: string | null) => void;
  setResults: (results: AnalysisResults | null) => void;
  setRunStatus: (status: RunStatus | null) => void;
  setUrl: (url: string) => void;
  setSelectedMarketSlug: (slug: string | null) => void;
  stopPolling: () => void;
  runIdRef: MutableRefObject<string | null>;
  showToast: (message: string, type: "error" | "success" | "info" | "warning") => void;
}

interface UseRecentRunsReturn {
  handleRunSelect: (run: RecentRun) => Promise<void>;
}

/**
 * Hook for loading and displaying saved analysis runs
 */
export function useRecentRuns({
  setSelectedRunId,
  setIsSubmitting,
  setRunId,
  setResults,
  setRunStatus,
  setUrl,
  setSelectedMarketSlug,
  stopPolling,
  runIdRef,
  showToast,
}: UseRecentRunsOptions): UseRecentRunsReturn {

  const handleRunSelect = useCallback(async (run: RecentRun) => {
    const runIdToLoad = run.run_id || run._id;
    if (!runIdToLoad) {
      logger.error("No run_id or _id in selected run:", run);
      return;
    }

    setSelectedRunId(String(runIdToLoad));
    setIsSubmitting(false);
    stopPolling();
    setRunId(null);
    runIdRef.current = null;

    try {
      const response = await fetch(`/api/run/${encodeURIComponent(runIdToLoad)}`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || errorData.error || "Failed to load saved run"
        );
      }

      const data = await response.json();
      const savedRun = data.run;

      if (!savedRun) {
        throw new Error("No run data in response");
      }

      // Map saved run to AnalysisResults format
      const mappedResults: AnalysisResults = {
        market_snapshot: savedRun.market_snapshot || {},
        event_context: savedRun.event_context || {},
        news_context: savedRun.news_context || {},
        signal: savedRun.signal || {},
        decision: savedRun.decision || {},
        report: savedRun.report || {},
        requires_market_selection: false,
      };

      // Set run status based on saved status
      const savedStatus = savedRun.status || {};
      setRunStatus({
        market: savedStatus.market === "done" ? "done" : "pending",
        news: savedStatus.news === "done" ? "done" : "pending",
        signal: savedStatus.signal === "done" ? "done" : "pending",
        report: savedStatus.report === "done" ? "done" : "pending",
      });

      setResults(mappedResults);
      setUrl(savedRun.market_url || savedRun.polymarket_url || "");

      if (savedRun.market_snapshot?.slug) {
        setSelectedMarketSlug(savedRun.market_snapshot.slug);
      }
    } catch (error) {
      logger.error("Error loading saved run:", error);
      showToast(
        error instanceof Error ? error.message : "Failed to load saved run",
        "error"
      );
    }
  }, [setSelectedRunId, setIsSubmitting, stopPolling, setRunId, runIdRef, setResults, setRunStatus, setUrl, setSelectedMarketSlug, showToast]);

  return {
    handleRunSelect,
  };
}
