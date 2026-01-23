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
  const [selectedMarketSlug, setSelectedMarketSlug] = useState<string | null>(null);
  const [lastSortedMarketOptions, setLastSortedMarketOptions] = useState<
    { slug: string; question: string }[]
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
    onComplete: useCallback((marketSlug?: string) => {
      setIsSubmitting(false);
      if (marketSlug) {
        setSelectedMarketSlug(marketSlug);
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
    setSelectedMarketSlug,
    stopPolling,
    runIdRef,
    showToast,
  });

  // Callbacks
  const handleSortedOptionsChange = useCallback(
    (options: Array<{ slug?: string; question?: string; id?: string; title?: string }>) => {
      const mapped = options
        .map((option) => {
          const slug = option?.slug ?? option?.id;
          if (!slug) return null;
          return { slug: String(slug), question: option?.question || option?.title || String(slug) };
        })
        .filter((option): option is { slug: string; question: string } => Boolean(option));

      setLastSortedMarketOptions((prev) => {
        if (prev.length === mapped.length &&
            prev.every((p, i) => p.slug === mapped[i]?.slug && p.question === mapped[i]?.question)) {
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
      sidebarHeader={
        <HistorySidebarHeader
          isLoading={sessionsLoading}
          onRefresh={fetchRecentRuns}
        />
      }
      sidebarContent={
        <HistorySidebarContent
          runs={runs}
          isLoading={sessionsLoading}
          error={sessionsError}
          activeRunId={(selectedRunId || runId) ?? undefined}
          onRunSelect={handleRunSelect as (run: RecentRun) => void}
          onRetry={fetchRecentRuns}
        />
      }
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
      configHeader={
        <ConfigPanelHeader
          isSubmitting={isSubmitting}
          onReset={handleResetConfig}
        />
      }
      configContent={
        <ConfigPanelContent
          config={configuration}
          onChange={setConfiguration}
          isSubmitting={isSubmitting}
        />
      }
    >
      {/* Results Pane */}
      <div className="p-4" id="results-pane">
        <AnalysisResultsView
          results={results}
          runStatus={runStatus}
          url={url}
          isSubmitting={isSubmitting}
          selectedMarketSlug={selectedMarketSlug}
          lastSortedMarketOptions={lastSortedMarketOptions}
          onSelectMarket={handleSelectMarket}
          onSortedOptionsChange={handleSortedOptionsChange}
        />
      </div>
    </AppShell>
  );
}
