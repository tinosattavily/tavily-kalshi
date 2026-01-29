"use client";

import React, { useState, useCallback, useEffect, useRef } from "react";
import { Settings } from "lucide-react";

// Components
import TopNav from "../background/TopNav";
import UrlInputBar from "../background/UrlInputBar";
import RecentSessions from "../background/RecentSessions";
import ConfigurationPanel, {
  AnalysisConfiguration,
  DEFAULT_CONFIG,
} from "../background/ConfigurationPanel";
import { RecentRun } from "../background/RecentMarketCard";
import { MarketSnapshotCard } from "../MarketSnapshotCard";
import { NewsCard } from "../NewsCard";
import SignalCard from "../background/SignalCard";
import ReportCard from "../background/ReportCard";
import EmptyPrompt from "../background/EmptyPrompt";
import MarketSelection from "../background/MarketSelection";
import { MarketSnapshotSkeleton } from "../skeletons/MarketSnapshotSkeleton";
import { NewsSkeleton } from "../skeletons/NewsSkeleton";
import { SignalSkeleton } from "../skeletons/SignalSkeleton";
import { ReportSkeleton } from "../skeletons/ReportSkeleton";
import { logger } from "../../lib/logger";

// Types
interface NewsArticle {
  title?: string;
  source?: string;
  url?: string;
  published_at?: string;
  snippet?: string;
  sentiment?: "bullish" | "bearish" | "neutral";
}

interface NewsContext {
  articles?: NewsArticle[];
  summary?: string;
  combined_summary?: string;
  tavily_queries?: string[];
  queries?: Array<{
    name?: string;
    query?: string;
    results?: NewsArticle[];
    answer?: string;
  }>;
}

interface OrderBookEntry {
  price?: number;
  size?: number;
}

interface MarketSnapshot {
  question?: string;
  url?: string;
  slug?: string;
  endDate?: string;
  end_date?: string;
  group_item_title?: string;
  groupItemTitle?: string;
  yes_price?: number;
  no_price?: number;
  volume?: string | number;
  volume24hr?: number;
  liquidity?: string | number;
  comment_count?: number;
  commentCount?: number;
  event_comment_count?: number;
  eventCommentCount?: number;
  series_comment_count?: number;
  seriesCommentCount?: number;
  best_bid?: number;
  bestBid?: number;
  best_ask?: number;
  bestAsk?: number;
  order_book?: { bids?: OrderBookEntry[]; asks?: OrderBookEntry[] };
  orderBook?: { bids?: OrderBookEntry[]; asks?: OrderBookEntry[] };
}

interface EventContext {
  title?: string;
  url?: string;
  volume24hr?: number;
  commentCount?: number;
  seriesCommentCount?: number;
}

interface Signal {
  direction?: string;
  model_prob?: number;
  model_prob_abs?: number;
  confidence?: string;
  rationale?: string;
}

interface Decision {
  action?: string;
  edge_pct?: number;
  toy_kelly_fraction?: number;
  notes?: string;
}

interface MarketOption {
  slug?: string;
  question?: string;
  id?: string;
  title?: string;
}

interface Resolution {
  status?: 'pending' | 'resolved_yes' | 'resolved_no' | 'voided' | 'unknown';
  winning_outcome?: string;
  resolved_at?: string;
  final_yes_price?: number;
  final_no_price?: number;
  checked_at?: string;
}

interface AnalysisResults {
  market_snapshot?: MarketSnapshot;
  event_context?: EventContext;
  news_context?: NewsContext;
  signal?: Signal;
  decision?: Decision;
  report?: string | { title?: string; markdown?: string } | Record<string, unknown>;
  market_options?: MarketOption[];
  requires_market_selection?: boolean;
  resolution?: Resolution;
}

interface RunStatus {
  market?: string;
  news?: string;
  signal?: string;
  report?: string;
}

// Utility functions
function mapConfigurationToBackend(config: AnalysisConfiguration): Record<string, unknown> {
  return {
    use_tavily_prompt_agent: config.useTavilyPromptAgent,
    use_news_summary_agent: config.useNewsSummaryAgent,
    max_articles: config.maxArticles,
    max_articles_per_query: config.maxArticlesPerQuery,
    min_confidence: config.minConfidence,
    enable_sentiment_analysis: config.enableSentimentAnalysis,
  };
}

function createEmptyResults(): AnalysisResults {
  return {
    market_snapshot: {},
    event_context: {},
    news_context: {},
    signal: {},
    decision: {},
    report: {},
  };
}

function createPendingStatus(): RunStatus {
  return {
    market: "pending",
    news: "pending",
    signal: "pending",
    report: "pending",
  };
}

function isValidRunId(runId: string | null | undefined): runId is string {
  if (!runId || typeof runId !== "string") return false;
  const trimmed = runId.trim();
  return trimmed !== "" && trimmed !== "undefined" && trimmed !== "null";
}

function humanizeClosesIn(isoDate?: string): string {
  if (!isoDate) return "—";
  const end = new Date(isoDate).getTime();
  if (Number.isNaN(end)) return "—";
  const now = Date.now();
  const diffMs = Math.max(0, end - now);
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (diffDays >= 1) return `${diffDays} day${diffDays === 1 ? "" : "s"}`;
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  if (diffHours >= 1) return `${diffHours} hr${diffHours === 1 ? "" : "s"}`;
  const diffMins = Math.floor(diffMs / (1000 * 60));
  return `${diffMins} min`;
}

// Header heights
const TOP_NAV_HEIGHT = 56;
const ROW2_HEIGHT = 64;
const FULL_HEADER_HEIGHT = TOP_NAV_HEIGHT + ROW2_HEIGHT;

export default function AppShell(): React.JSX.Element {
  // Config panel state
  const [isConfigExpanded, setIsConfigExpanded] = useState(true);

  // Header collapse state
  const [isHeaderCollapsed, setIsHeaderCollapsed] = useState(false);
  const lastScrollY = useRef(0);

  // Form state
  const [isFocused, setIsFocused] = useState(false);
  const [url, setUrl] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [configuration, setConfiguration] = useState<AnalysisConfiguration>(DEFAULT_CONFIG);

  // Results state
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [lastSortedMarketOptions, setLastSortedMarketOptions] = useState<
    { slug: string; question: string }[]
  >([]);
  const [selectedMarketSlug, setSelectedMarketSlug] = useState<string | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [runStatus, setRunStatus] = useState<RunStatus | null>(null);
  const pollingRef = useRef<boolean>(false);
  const runIdRef = useRef<string | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [recentSessionsRefreshTrigger, setRecentSessionsRefreshTrigger] = useState(0);

  // Scroll listener for header collapse
  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      const scrollingDown = currentScrollY > lastScrollY.current;
      const scrollThreshold = 50;

      if (scrollingDown && currentScrollY > scrollThreshold) {
        setIsHeaderCollapsed(true);
      } else if (!scrollingDown) {
        setIsHeaderCollapsed(false);
      }

      lastScrollY.current = currentScrollY;
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Callbacks
  const mapMarketOptions = useCallback(
    (options: MarketOption[] | undefined | null): { slug: string; question: string }[] => {
      if (!Array.isArray(options)) return [];
      return options
        .map((option) => {
          const slug = option?.slug ?? option?.id;
          if (!slug) return null;
          return {
            slug: String(slug),
            question: option?.question || option?.title || String(slug),
          };
        })
        .filter((option): option is { slug: string; question: string } => option !== null);
    },
    [],
  );

  const handleRunSelect = useCallback(async (run: RecentRun) => {
    const runIdToLoad = run.run_id || run._id;
    if (!runIdToLoad) {
      logger.error("No run_id or _id in selected run:", run);
      return;
    }

    setSelectedRunId(String(runIdToLoad));
    setIsSubmitting(false);
    pollingRef.current = false;
    setRunId(null);
    runIdRef.current = null;

    try {
      const response = await fetch(`/api/run/${encodeURIComponent(runIdToLoad)}`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.error || "Failed to load saved run");
      }

      const data = await response.json();
      const savedRun = data.run;

      if (!savedRun) {
        throw new Error("No run data in response");
      }

      const mappedResults: AnalysisResults = {
        market_snapshot: savedRun.market_snapshot || {},
        event_context: savedRun.event_context || {},
        news_context: savedRun.news_context || {},
        signal: savedRun.signal || {},
        decision: savedRun.decision || {},
        report: savedRun.report || {},
        requires_market_selection: false,
        resolution: savedRun.resolution,
      };

      const savedStatus = savedRun.status || {};
      setRunStatus({
        market: savedStatus.market === "done" ? "done" : "pending",
        news: savedStatus.news === "done" ? "done" : "pending",
        signal: savedStatus.signal === "done" ? "done" : "pending",
        report: savedStatus.report === "done" ? "done" : "pending",
      });

      setResults(mappedResults);
      setUrl(savedRun.polymarket_url || "");

      if (savedRun.market_snapshot?.slug) {
        setSelectedMarketSlug(savedRun.market_snapshot.slug);
      }
    } catch (error) {
      logger.error("Error loading saved run:", error);
      alert(error instanceof Error ? error.message : "Failed to load saved run");
    }
  }, []);

  const resetAnalysisState = useCallback(() => {
    pollingRef.current = false;
    setIsSubmitting(true);
    setResults(null);
    setRunStatus(null);
    setRunId(null);
    setSelectedRunId(null);
    runIdRef.current = null;
  }, []);

  const startPollingWithRunId = useCallback((newRunId: string) => {
    runIdRef.current = newRunId;
    pollingRef.current = true;
    setRunId(newRunId);
    setResults(createEmptyResults());
    setRunStatus(createPendingStatus());
  }, []);

  const showError = useCallback((message: string) => {
    if (typeof window !== "undefined") {
      window.alert(message);
    }
  }, []);

  const handleSubmit = async () => {
    if (!url.trim() || isSubmitting) return;

    resetAnalysisState();

    try {
      const response = await fetch("/api/analyze/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          market_url: url.trim(),
          configuration: mapConfigurationToBackend(configuration),
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: "Unknown error" }));
        const errorMessage = errorData.detail || errorData.error || errorData.details || `HTTP error! status: ${response.status}`;
        throw new Error(errorMessage);
      }

      const data = await response.json();

      if (!data.run_id) {
        logger.error("No run_id in response:", data);
        throw new Error("Backend did not return run_id");
      }

      const newRunId = String(data.run_id).trim();
      if (!isValidRunId(newRunId)) {
        logger.error("Invalid run_id:", newRunId);
        throw new Error("Invalid run_id received from backend");
      }

      startPollingWithRunId(newRunId);
    } catch (error) {
      logger.error("Error submitting URL:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to start analysis. Please try again.";
      showError(errorMessage);
      setIsSubmitting(false);
    }
  };

  const handleSelectMarket = async (marketSlug: string) => {
    resetAnalysisState();

    try {
      const response = await fetch("/api/analyze/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          market_url: url.trim(),
          selected_market_slug: marketSlug,
          configuration: mapConfigurationToBackend(configuration),
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: "Unknown error" }));
        const errorMessage = errorData.detail || errorData.error || errorData.details || `HTTP error! status: ${response.status}`;
        throw new Error(errorMessage);
      }

      const data = await response.json();

      if (!data.run_id) {
        logger.error("No run_id in response:", data);
        throw new Error("Server did not return a run_id");
      }

      const newRunId = String(data.run_id).trim();
      if (!isValidRunId(newRunId)) {
        logger.error("Invalid run_id:", newRunId);
        throw new Error("Invalid run_id received from backend");
      }

      startPollingWithRunId(newRunId);
    } catch (error) {
      logger.error("Error selecting market:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to analyze selected market. Please try again.";
      showError(errorMessage);
      setIsSubmitting(false);
    }
  };

  const handleSortedOptionsChange = useCallback(
    (options: MarketOption[]) => {
      const mapped = mapMarketOptions(options);
      setLastSortedMarketOptions((prev) => {
        const hasChanged =
          prev.length !== mapped.length ||
          prev.some((p, i) => p.slug !== mapped[i]?.slug || p.question !== mapped[i]?.question);
        return hasChanged ? mapped : prev;
      });
    },
    [mapMarketOptions],
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Polling effect
  useEffect(() => {
    const effectiveRunId = runId || runIdRef.current;
    if (!isValidRunId(effectiveRunId) || !pollingRef.current) return;

    const currentRunId = effectiveRunId.trim();
    let cancelled = false;

    const scheduleNextPoll = (delay: number) => {
      if (!cancelled && pollingRef.current) {
        window.setTimeout(poll, delay);
      }
    };

    const stopPolling = () => {
      pollingRef.current = false;
      setIsSubmitting(false);
    };

    const hasNonEmptyObject = (obj: unknown): boolean =>
      obj !== null && typeof obj === "object" && Object.keys(obj).length > 0;

    const isMarketSelectionRequired = (run: Record<string, unknown>): boolean =>
      Array.isArray(run.market_options) &&
      run.market_options.length > 0 &&
      !hasNonEmptyObject(run.market_snapshot);

    const updateResultsFromRun = (run: Record<string, unknown>) => {
      setResults((prev) => {
        const updated: AnalysisResults = prev ? { ...prev } : createEmptyResults();
        const status = run.status as RunStatus | undefined;

        if (status?.market === "done") {
          if (hasNonEmptyObject(run.market_snapshot)) {
            updated.market_snapshot = run.market_snapshot as MarketSnapshot;
          }
          if (run.event_context) {
            updated.event_context = run.event_context as EventContext;
          }
          if (Array.isArray(run.market_options) && run.market_options.length > 0) {
            updated.market_options = run.market_options as MarketOption[];
            updated.requires_market_selection = !hasNonEmptyObject(run.market_snapshot);
          }
        }

        if (status?.news === "done" && run.news_context) {
          updated.news_context = run.news_context as NewsContext;
        }

        if (status?.signal === "done" && run.signal) {
          updated.signal = run.signal as Signal;
          updated.decision = (run.decision as Decision) || updated.decision;
        }

        if (status?.report === "done" && run.report) {
          updated.report = run.report as AnalysisResults["report"];
        }

        // Include resolution data if available
        if (run.resolution) {
          updated.resolution = run.resolution as AnalysisResults["resolution"];
        }

        return updated;
      });
    };

    async function poll() {
      if (cancelled || !pollingRef.current) return;

      try {
        const response = await fetch(`/api/run/${currentRunId}`);

        if (!response.ok) {
          if (response.status === 404) {
            scheduleNextPoll(1500);
            return;
          }
          if (response.status === 500) {
            scheduleNextPoll(3000);
            return;
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const run = data.run;

        if (!run) {
          scheduleNextPoll(1500);
          return;
        }

        if (cancelled) return;

        if (run.status) {
          setRunStatus(run.status);
        }

        updateResultsFromRun(run);

        if (isMarketSelectionRequired(run)) {
          setResults((prev) =>
            prev ? { ...prev, requires_market_selection: true, market_options: run.market_options } : prev
          );
          stopPolling();
          return;
        }

        const status = run.status || {};
        const phases = Object.values(status);
        const allComplete = phases.length > 0 && phases.every((s) => s === "done" || s === "error");

        if (allComplete) {
          stopPolling();
          if (run.market_snapshot?.slug) {
            setSelectedMarketSlug(run.market_snapshot.slug);
          }
          setRecentSessionsRefreshTrigger((prev) => prev + 1);
        } else {
          scheduleNextPoll(1500);
        }
      } catch (error) {
        logger.error("Error polling run status:", error);
        scheduleNextPoll(2500);
      }
    }

    poll();

    return () => {
      cancelled = true;
    };
  }, [runId]);

  // Helper functions for rendering
  const mapNewsArticles = useCallback((newsContext?: NewsContext) => {
    const articles = newsContext?.articles;
    if (!Array.isArray(articles) || articles.length === 0) {
      return [];
    }
    return articles.map((article) => ({
      title: article.title || "Untitled",
      source: article.source || "Unknown source",
      publishedAt: article.published_at || undefined,
      url: article.url || undefined,
      summary: article.snippet || undefined,
      sentiment: article.sentiment || "neutral",
    }));
  }, []);

  const shouldShowMarketSelection =
    results?.requires_market_selection &&
    (!results.market_snapshot || Object.keys(results.market_snapshot).length === 0) &&
    results.market_options &&
    results.market_options.length > 0;

  const hasMarketSnapshot =
    runStatus?.market === "done" &&
    results?.market_snapshot &&
    Object.keys(results.market_snapshot).length > 0;

  const isMarketPending = runStatus?.market === "pending" || runStatus?.market === undefined;
  const isNewsPending = runStatus?.news === "pending" || runStatus?.news === undefined;
  const isSignalPending = runStatus?.signal === "pending" || runStatus?.signal === undefined;
  const isReportPending = runStatus?.report === "pending" || runStatus?.report === undefined;

  const hasNewsContent = (ctx?: NewsContext): boolean => {
    if (!ctx) return false;
    const hasArticles = Array.isArray(ctx.articles) && ctx.articles.length > 0;
    const hasSummary = !!ctx.summary?.trim();
    const hasCombinedSummary = !!ctx.combined_summary?.trim();
    return hasArticles || hasSummary || hasCombinedSummary;
  };

  const handleNewsItemClick = useCallback((item: { url?: string }) => {
    if (item.url) {
      window.open(item.url, "_blank", "noopener,noreferrer");
    }
  }, []);

  const mapOrderBook = (entries: OrderBookEntry[] | undefined) =>
    (entries || []).map((entry) => ({
      price: Number(entry.price ?? 0),
      size: Number(entry.size ?? 0),
    }));

  // Calculate widths based on config state
  const sidebarWidth = "16.67%"; // Fixed width - doesn't change when config expands/collapses
  const configWidth = isConfigExpanded ? "16.67%" : "0%";

  return (
    <div className="relative bg-[#f0f4f8] min-h-screen">
      {/* Grid Background */}
      <div className="pointer-events-none fixed inset-0 -z-10 bg-grid opacity-50" />

      {/* Fixed Header (Rows 1 & 2) */}
      <div
        className="fixed top-0 left-0 right-0 z-20 bg-[#f0f4f8] transition-transform duration-300 ease-out"
        style={{ transform: isHeaderCollapsed ? `translateY(-${TOP_NAV_HEIGHT}px)` : 'translateY(0)' }}
      >
        {/* ROW 1: Top Navigation */}
        <TopNav />

        {/* ROW 2: Headers (Sidebar Header | URL Input | Config Header) */}
        <div
          className="grid"
          style={{ gridTemplateColumns: "2fr 2fr 4fr 2fr 2fr" }}
        >
          {/* History Sidebar Header */}
          <div className="col-span-2 border-b border-r border-[#1e3a8a]/20 bg-white/40 backdrop-blur-sm">
            <div className="flex h-16 items-center justify-between px-5">
            </div>
          </div>

          {/* URL Input (center) */}
          <div className="border-b border-[#1e3a8a]/20 bg-white/40 backdrop-blur-sm">
            <div className="flex h-16 items-center justify-center px-6">
              <div className="w-full max-w-xl">
                <UrlInputBar
                  url={url}
                  isSubmitting={isSubmitting}
                  isFocused={isFocused}
                  onChange={setUrl}
                  onSubmit={handleSubmit}
                  onKeyDown={handleKeyDown}
                  onFocusChange={setIsFocused}
                />
              </div>
            </div>
          </div>

          {/* Config Panel Header */}
          <div className="col-span-2 border-b border-l border-[#1e3a8a]/20 bg-white/40 backdrop-blur-sm">
            <div className="flex h-16 items-center justify-end px-5">
              <button
                onClick={() => setIsConfigExpanded(!isConfigExpanded)}
                className={`flex h-8 w-8 items-center justify-center rounded-lg text-neutral-600 transition-all duration-300 hover:text-neutral-900 ${isConfigExpanded ? "rotate-90" : "rotate-0"}`}
                aria-label={isConfigExpanded ? "Collapse settings" : "Expand settings"}
              >
                <Settings size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Spacer for fixed header */}
      <div
        className="transition-[height] duration-300 ease-out"
        style={{ height: isHeaderCollapsed ? `${ROW2_HEIGHT}px` : `${FULL_HEADER_HEIGHT}px` }}
      />

      {/* Main Content Area (Row 3) */}
      <div
        className={`grid w-full ${!results ? 'min-h-0' : ''}`}
        style={{ gridTemplateColumns: "2fr 2fr 4fr 2fr 2fr" }}
      >
        <div className="col-span-5 flex items-start">
          {/* History Sidebar */}
          <div
            className="flex-shrink-0 border-r border-[#1e3a8a]/20 bg-white/40 backdrop-blur-sm transition-all duration-300 ease-out sticky self-start overflow-hidden"
            style={{
              width: sidebarWidth,
              top: isHeaderCollapsed ? `${ROW2_HEIGHT}px` : `${FULL_HEADER_HEIGHT}px`,
              height: isHeaderCollapsed ? `calc(100vh - ${ROW2_HEIGHT}px)` : `calc(100vh - ${FULL_HEADER_HEIGHT}px)`
            }}
          >
            <RecentSessions
              onRunSelect={handleRunSelect}
              activeRunId={(selectedRunId || runId) ?? undefined}
              refreshTrigger={recentSessionsRefreshTrigger}
            />
          </div>

          {/* Main Content Area */}
          <div className={`bg-white/40 backdrop-blur-sm ${!results ? 'flex-1 overflow-y-auto' : 'flex-1'}`}>
            <div className="p-6">
              {!results && <EmptyPrompt />}

              {results && shouldShowMarketSelection && (
                <MarketSelection
                  options={results.market_options!.filter((opt): opt is { slug: string; question?: string; id?: string } => !!opt.slug)}
                  eventContext={results.event_context}
                  isSubmitting={isSubmitting}
                  onSelect={handleSelectMarket}
                  onSortedOptionsChange={handleSortedOptionsChange}
                />
              )}

              {results && !shouldShowMarketSelection && (
                <div className="space-y-6">
                  {/* Market Snapshot */}
                  {hasMarketSnapshot && results.market_snapshot && (
                    <MarketSnapshotCard
                      eventTitle={results.event_context?.title || results.market_snapshot.question || "Event"}
                      groupItemTitle={results.market_snapshot.group_item_title || results.market_snapshot.groupItemTitle}
                      polymarketUrl={results.market_snapshot.url || results.event_context?.url || url || "#"}
                      closesIn={humanizeClosesIn(results.market_snapshot.endDate || results.market_snapshot.end_date)}
                      endDate={results.market_snapshot.endDate || results.market_snapshot.end_date}
                      question={results.market_snapshot.question}
                      previousMarkets={lastSortedMarketOptions.length > 0 ? lastSortedMarketOptions : mapMarketOptions(results.market_options)}
                      activeMarketSlug={selectedMarketSlug ?? undefined}
                      onMarketSelect={handleSelectMarket}
                      yesPrice={results.market_snapshot.yes_price ?? 0}
                      noPrice={results.market_snapshot.no_price ?? 0}
                      marketVolume={Number(results.market_snapshot.volume ?? 0)}
                      volume24h={results.market_snapshot.volume24hr || results.event_context?.volume24hr}
                      liquidity={Number(results.market_snapshot.liquidity ?? 0)}
                      commentCount={results.event_context?.commentCount ?? results.market_snapshot.comment_count ?? results.market_snapshot.commentCount}
                      eventCommentCount={results.event_context?.commentCount ?? results.market_snapshot.event_comment_count ?? results.market_snapshot.eventCommentCount}
                      seriesCommentCount={results.event_context?.seriesCommentCount ?? results.market_snapshot.series_comment_count ?? results.market_snapshot.seriesCommentCount}
                      bestBid={results.market_snapshot.best_bid ?? results.market_snapshot.bestBid}
                      bestAsk={results.market_snapshot.best_ask ?? results.market_snapshot.bestAsk}
                      bids={mapOrderBook(results.market_snapshot.order_book?.bids || results.market_snapshot.orderBook?.bids)}
                      asks={mapOrderBook(results.market_snapshot.order_book?.asks || results.market_snapshot.orderBook?.asks)}
                      resolution={results.resolution}
                    />
                  )}
                  {isMarketPending && results && <MarketSnapshotSkeleton />}

                  {/* News */}
                  {runStatus?.news === "done" && hasNewsContent(results?.news_context) && (
                    <NewsCard
                      heading="Market News & Analysis"
                      highlights={mapNewsArticles(results?.news_context)}
                      isLoading={false}
                      newsSummary={results?.news_context?.summary}
                      combinedSummary={results?.news_context?.combined_summary}
                      onItemClick={handleNewsItemClick}
                    />
                  )}
                  {isNewsPending && results && <NewsSkeleton />}

                  {/* Signal */}
                  {runStatus?.signal === "done" && results?.signal && Object.keys(results.signal).length > 0 && (
                    <SignalCard signal={results.signal} />
                  )}
                  {isSignalPending && results && <SignalSkeleton />}

                  {/* Report */}
                  {runStatus?.report === "done" && results?.report && (
                    <ReportCard report={results.report} eventContext={results?.event_context} />
                  )}
                  {isReportPending && results && <ReportSkeleton />}
                </div>
              )}
            </div>
          </div>

          {/* Config Panel */}
          <div
            className={`flex-shrink-0 border-l border-[#1e3a8a]/20 bg-white/40 backdrop-blur-sm transition-all duration-300 ease-out sticky self-start overflow-hidden ${isConfigExpanded ? "opacity-100" : "opacity-0 pointer-events-none"}`}
            style={{
              width: configWidth,
              top: isHeaderCollapsed ? `${ROW2_HEIGHT}px` : `${FULL_HEADER_HEIGHT}px`,
              height: isHeaderCollapsed ? `calc(100vh - ${ROW2_HEIGHT}px)` : `calc(100vh - ${FULL_HEADER_HEIGHT}px)`,
              minWidth: isConfigExpanded ? "16.67vw" : 0
            }}
          >
            <ConfigurationPanel
              config={configuration}
              onChange={setConfiguration}
              isSubmitting={isSubmitting}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
