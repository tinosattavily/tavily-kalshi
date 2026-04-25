"use client";

import React, { PropsWithChildren, useCallback, useState } from "react";
// Layout components
import { AppShell } from "./layout/AppShell";
import HistorySidebarHeader from "./layout/HistorySidebarHeader";
import HistorySidebarContent from "./layout/HistorySidebarContent";
import ConfigPanelHeader from "./layout/ConfigPanelHeader";
import ConfigPanelContent, { AnalysisConfiguration } from "./layout/ConfigPanelContent";
import { RecentRun } from "./layout/HistoryCard";
// Input components
import UrlInput from "./input/UrlInput";
// Analysis components
import { AnalysisResultsView } from "./analysis/AnalysisResults";
// Utilities
import { useToast } from "./ui/Toast";
import { useAnalysisPolling, useAnalysisSubmit, useRecentRuns, useRecentSessions } from "../hooks";
import type { AnalysisResults, RunStatus } from "../types";

const DEFAULT_CONFIG: AnalysisConfiguration = {
  useTavilyPromptAgent: true,
  useNewsSummaryAgent: true,
  maxArticles: 15,
  maxArticlesPerQuery: 8,
  minConfidence: "medium",
  enableSentimentAnalysis: true,
};

export default function Dashboard(_props: PropsWithChildren): React.JSX.Element {
  void _props;
  const { showToast } = useToast();

  // UI state
  const [isFocused, setIsFocused] = useState(false);
  const [url, setUrl] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [configuration, setConfiguration] = useState<AnalysisConfiguration>(DEFAULT_CONFIG);

  // Analysis state
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [runStatus, setRunStatus] = useState<RunStatus | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [selectedMarketId, setSelectedMarketId] = useState<string | null>(null);
  const [lastSortedMarketOptions, setLastSortedMarketOptions] = useState<
    { market_id: string; question: string; slug?: string }[]
  >([]);
  const [recentSessionsRefreshTrigger, setRecentSessionsRefreshTrigger] = useState(0);

  // Recent sessions hook
  const { runs, isLoading: sessionsLoading, error: sessionsError, fetchRecentRuns } = useRecentSessions({
    refreshTrigger: recentSessionsRefreshTrigger,
  });

  // Polling hook
  const { runIdRef, startPolling, stopPolling } = useAnalysisPolling({
    runId,
    onStatusUpdate: setRunStatus,
    onResultsUpdate: setResults,
    onMarketSelectionRequired: useCallback((marketOptions) => {
      setResults((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          requires_market_selection: true,
          market_options: marketOptions,
        };
      });
      setIsSubmitting(false);
    }, []),
    onComplete: useCallback((marketId?: string) => {
      setIsSubmitting(false);
      if (marketId) {
        setSelectedMarketId(marketId);
      }
    }, []),
    onRefreshTrigger: useCallback(() => {
      setRecentSessionsRefreshTrigger((prev) => prev + 1);
    }, []),
  });

  // Submit hook
  const { handleSubmit, handleSelectMarket } = useAnalysisSubmit({
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
  });

  // Recent runs hook (for selecting a run from history)
  const { handleRunSelect } = useRecentRuns({
    setSelectedRunId,
    setIsSubmitting,
    setRunId,
    setResults,
    setRunStatus,
    setUrl,
    setSelectedMarketId,
    stopPolling,
    runIdRef,
    showToast,
  });

  // Callbacks
  const handleSortedOptionsChange = useCallback(
    (options: Array<{ market_id?: string; slug?: string; question?: string; id?: string; title?: string; label?: string }>) => {
      const mapped = options
        .flatMap((option) => {
          const marketId = option?.market_id ?? option?.slug ?? option?.id;
          if (!marketId) return [];
          return {
            market_id: String(marketId),
            slug: option?.slug,
            question: option?.label || option?.question || option?.title || String(marketId),
          };
        });

      setLastSortedMarketOptions((prev) => {
        if (prev.length === mapped.length &&
            prev.every((p, i) => p.market_id === mapped[i]?.market_id && p.question === mapped[i]?.question)) {
          return prev;
        }
        return mapped;
      });
    },
    []
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleResetConfig = useCallback(() => {
    setConfiguration(DEFAULT_CONFIG);
  }, []);

  return (
    <AppShell
      signal={results?.signal ?? null}
      urlInput={
        <UrlInput
          url={url}
          isSubmitting={isSubmitting}
          isFocused={isFocused}
          onChange={setUrl}
          onSubmit={handleSubmit}
          onKeyDown={handleKeyDown}
          onFocusChange={setIsFocused}
        />
      }
      sessions={
        <>
          <HistorySidebarHeader
            isLoading={sessionsLoading}
            onRefresh={fetchRecentRuns}
          />
          <HistorySidebarContent
            runs={runs}
            isLoading={sessionsLoading}
            error={sessionsError}
            activeRunId={(selectedRunId || runId) ?? undefined}
            onRunSelect={handleRunSelect as (run: RecentRun) => void}
            onRetry={fetchRecentRuns}
          />
        </>
      }
      main={
        <div className="p-4" id="results-pane">
          <AnalysisResultsView
            results={results}
            runStatus={runStatus}
            url={url}
            isSubmitting={isSubmitting}
            selectedMarketId={selectedMarketId}
            lastSortedMarketOptions={lastSortedMarketOptions}
            onSelectMarket={handleSelectMarket}
            onSortedOptionsChange={handleSortedOptionsChange}
          />
        </div>
      }
      config={
        <>
          <ConfigPanelHeader
            isSubmitting={isSubmitting}
            onReset={handleResetConfig}
          />
          <ConfigPanelContent
            config={configuration}
            onChange={setConfiguration}
            isSubmitting={isSubmitting}
          />
        </>
      }
    />
  );
}
