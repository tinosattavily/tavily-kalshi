"use client";

import { useCallback, MutableRefObject } from "react";
import { logger } from "../lib/logger";
import type { AnalysisResults, RunStatus } from "../types";

interface AnalysisConfiguration {
  useTavilyPromptAgent: boolean;
  useNewsSummaryAgent: boolean;
  maxArticles: number;
  maxArticlesPerQuery: number;
  minConfidence: "low" | "medium" | "high";
  enableSentimentAnalysis: boolean;
}

interface UseAnalysisSubmitOptions {
  url: string;
  configuration: AnalysisConfiguration;
  isSubmitting: boolean;
  setIsSubmitting: (value: boolean) => void;
  setResults: (results: AnalysisResults | null) => void;
  setRunStatus: (status: RunStatus | null) => void;
  setRunId: (id: string | null) => void;
  setSelectedRunId: (id: string | null) => void;
  startPolling: (runId: string) => void;
  stopPolling: () => void;
  runIdRef: MutableRefObject<string | null>;
  showToast: (message: string, type: "error" | "success" | "info" | "warning") => void;
}

interface UseAnalysisSubmitReturn {
  handleSubmit: () => Promise<void>;
  handleSelectMarket: (marketId: string) => Promise<void>;
}

/**
 * Hook for submitting analysis requests and selecting markets
 */
export function useAnalysisSubmit({
  url,
  configuration,
  isSubmitting,
  setIsSubmitting,
  setResults,
  setRunStatus,
  setRunId,
  setSelectedRunId,
  startPolling,
  stopPolling,
  runIdRef,
  showToast,
}: UseAnalysisSubmitOptions): UseAnalysisSubmitReturn {

  const initializeResults = useCallback(() => {
    setResults({
      market_snapshot: {},
      event_context: {},
      news_context: {},
      signal: {},
      decision: {},
      report: {},
    });
    setRunStatus({
      market: "pending",
      news: "pending",
      signal: "pending",
      report: "pending",
    });
  }, [setResults, setRunStatus]);

  const resetState = useCallback(() => {
    stopPolling();
    setIsSubmitting(true);
    setResults(null);
    setRunStatus(null);
    setRunId(null);
    setSelectedRunId(null);
    runIdRef.current = null;
  }, [stopPolling, setIsSubmitting, setResults, setRunStatus, setRunId, setSelectedRunId, runIdRef]);

  const validateAndSetRunId = useCallback((data: { run_id?: string }): string => {
    if (!data.run_id) {
      logger.error("No run_id in response:", data);
      throw new Error("Backend did not return run_id");
    }

    const newRunId = String(data.run_id).trim();
    if (!newRunId || newRunId === "undefined" || newRunId === "null") {
      logger.error("Invalid run_id:", newRunId);
      throw new Error("Invalid run_id received from backend");
    }

    return newRunId;
  }, []);

  const buildRequestConfig = useCallback(() => ({
    use_tavily_prompt_agent: configuration.useTavilyPromptAgent,
    use_news_summary_agent: configuration.useNewsSummaryAgent,
    max_articles: configuration.maxArticles,
    max_articles_per_query: configuration.maxArticlesPerQuery,
    min_confidence: configuration.minConfidence,
    enable_sentiment_analysis: configuration.enableSentimentAnalysis,
  }), [configuration]);

  const handleSubmit = useCallback(async () => {
    if (!url.trim() || isSubmitting) {
      return;
    }

    resetState();

    try {
      const requestBody = {
        market_url: url.trim(),
        configuration: buildRequestConfig(),
      };

      const response = await fetch("/api/analyze/start", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: "Unknown error" }));
        const errorMessage = errorData.detail || errorData.error || errorData.details || `HTTP error! status: ${response.status}`;
        throw new Error(errorMessage);
      }

      const data = await response.json();
      const newRunId = validateAndSetRunId(data);

      startPolling(newRunId);
      setRunId(newRunId);
      initializeResults();
    } catch (error) {
      logger.error("Error submitting URL:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to start analysis. Please try again.";
      showToast(errorMessage, "error");
      setIsSubmitting(false);
    }
  }, [url, isSubmitting, resetState, buildRequestConfig, validateAndSetRunId, startPolling, setRunId, initializeResults, showToast, setIsSubmitting]);

  const handleSelectMarket = useCallback(async (marketId: string) => {
    resetState();

    try {
      const body = {
        market_url: url.trim(),
        selected_market_id: marketId,
        configuration: buildRequestConfig(),
      };

      const response = await fetch("/api/analyze/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: "Unknown error" }));
        const errorMessage = errorData.detail || errorData.error || errorData.details || `HTTP error! status: ${response.status}`;
        throw new Error(errorMessage);
      }

      const data = await response.json();
      const newRunId = validateAndSetRunId(data);

      startPolling(newRunId);
      setRunId(newRunId);
      initializeResults();
    } catch (e) {
      logger.error("Error selecting market:", e);
      const errorMessage = e instanceof Error ? e.message : "Failed to analyze selected market. Please try again.";
      showToast(errorMessage, "error");
      setIsSubmitting(false);
    }
  }, [url, resetState, buildRequestConfig, validateAndSetRunId, startPolling, setRunId, initializeResults, showToast, setIsSubmitting]);

  return {
    handleSubmit,
    handleSelectMarket,
  };
}
