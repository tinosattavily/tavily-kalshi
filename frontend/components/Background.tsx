"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import GridAndNoise from "./background/GridAndNoise";
import TopNav from "./background/TopNav";
import UrlInputBar from "./background/UrlInputBar";
import MarketSelection from "./background/MarketSelection";
import ConfigurationPanel, {
  AnalysisConfiguration,
  DEFAULT_CONFIG,
} from "./background/ConfigurationPanel";
import RecentSessions from "./background/RecentSessions";
import { RecentRun } from "./background/RecentMarketCard";
import { MarketSnapshotCard } from "../components/MarketSnapshotCard";
import { NewsCard } from "../components/NewsCard";
import SignalCard from "./background/SignalCard";
import ReportCard from "./background/ReportCard";
import EmptyPrompt from "./background/EmptyPrompt";
import { MarketSnapshotSkeleton } from "../components/skeletons/MarketSnapshotSkeleton";
import { NewsSkeleton } from "../components/skeletons/NewsSkeleton";
import { SignalSkeleton } from "../components/skeletons/SignalSkeleton";
import { ReportSkeleton } from "../components/skeletons/ReportSkeleton";
import { logger } from "../lib/logger";

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

export default function Background(): React.JSX.Element {
  const [isFocused, setIsFocused] = useState(false);
  const [url, setUrl] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [configuration, setConfiguration] = useState<AnalysisConfiguration>(DEFAULT_CONFIG);
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

  // Handler to load a saved run from RecentSessions
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
        throw new Error(
          errorData.detail || errorData.error || "Failed to load saved run",
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
        resolution: savedRun.resolution,
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

  // Polling effect for phased analysis
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
          const newsCtx = run.news_context as NewsContext;
          const articlesCount = Array.isArray(newsCtx.articles) ? newsCtx.articles.length : 0;
          logger.debug(
            "News context received from backend",
            run.run_id as string,
            `articles: ${articlesCount}`,
            `has_summary: ${!!newsCtx.summary}`,
            `keys: ${Object.keys(newsCtx).join(", ")}`,
          );
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
        if (error instanceof Error && error.message.includes("Network error")) {
          logger.warn("Network error while polling:", error.message);
        }
        scheduleNextPoll(2500);
      }
    }

    poll();

    return () => {
      cancelled = true;
    };
  }, [runId]);

  const mapNewsArticles = useCallback((newsContext?: NewsContext) => {
    const articles = newsContext?.articles;
    if (!Array.isArray(articles) || articles.length === 0) {
      logger.debug(
        "No articles to map",
        `has_context: ${!!newsContext}`,
        `articles_length: ${articles?.length ?? 0}`,
      );
      return [];
    }

    logger.debug("Mapping news articles", `count: ${articles.length}`);

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

  return (
    <section id="app-root" className={`relative bg-white text-neutral-900 ${!results ? 'h-screen overflow-hidden' : 'min-h-screen'}`}>
      {/* Soft grid + noise background, hero-style */}
      <GridAndNoise />

      {/* Tailwind CSS grid: 2 rows × 3 columns (2-8-2).
          - Row 1 (auto) has three cells; each gets top & bottom borders.
          - Row 2 (1fr) fills remaining height when empty, auto when content exists.
          - Columns have left/right borders so vertical lines span both rows. */}
      <div id="app-grid" className={`grid w-full grid-cols-[minmax(0,2fr)_minmax(0,8fr)_minmax(0,2fr)] ${!results ? 'h-full grid-rows-[auto,1fr]' : 'grid-rows-[auto,auto]'}`}>
        {/* Row 1, Col 1 */}
        <div className="border-y border-l border-neutral-300 bg-white/90">
          <div className="h-10" />
        </div>

        {/* Row 1, Col 2 (navbar cell) */}
        <TopNav />

        {/* Row 1, Col 3 */}
        <div className="border-y border-r border-neutral-300 bg-white/90">
          <div className="h-10" />
        </div>

        {/* Row 2, Col 1 - Recent Sessions */}
        <RecentSessions
          onRunSelect={handleRunSelect}
          activeRunId={(selectedRunId || runId) ?? undefined}
          refreshTrigger={recentSessionsRefreshTrigger}
        />

        {/* Row 2, Col 2 */}
        <div className={`border-x border-neutral-300 bg-white/90 flex flex-col ${!results ? 'overflow-hidden' : ''}`}>
          {/* Row 1: Input field in a grid */}
          <div id="input-row" className="grid grid-cols-[1fr_2fr_1fr] border-b border-neutral-300">
            <div className="p-4">{/* Cell 1 */}</div>
            <div className="p-4 border-x border-neutral-300" id="url-input-cell">
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
            <div className="p-4">{/* Cell 3 */}</div>
          </div>

          {/* Row 2: Analysis results (or selection UI) */}
          <div className={`p-4 ${!results ? 'flex-1' : ''}`} id="results-pane">
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
              <div>
                {/* Market Snapshot */}
                {hasMarketSnapshot && results.market_snapshot && (
                  <div className="mb-6">
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
                  </div>
                )}
                {isMarketPending && (
                  <div className="mb-6">
                    <MarketSnapshotSkeleton />
                  </div>
                )}

                {/* News */}
                {runStatus?.news === "done" && hasNewsContent(results.news_context) && (
                  <div className="mb-6">
                    <NewsCard
                      heading="Market News & Analysis"
                      highlights={mapNewsArticles(results.news_context)}
                      isLoading={false}
                      newsSummary={results.news_context?.summary}
                      combinedSummary={results.news_context?.combined_summary}
                      onItemClick={handleNewsItemClick}
                    />
                  </div>
                )}
                {isNewsPending && (
                  <div className="mb-6">
                    <NewsSkeleton />
                  </div>
                )}

                {/* Signal */}
                {runStatus?.signal === "done" && results.signal && Object.keys(results.signal).length > 0 && (
                  <SignalCard signal={results.signal} />
                )}
                {isSignalPending && <SignalSkeleton />}

                {/* Report */}
                {runStatus?.report === "done" && results.report && (
                  <ReportCard report={results.report} eventContext={results.event_context} />
                )}
                {isReportPending && <ReportSkeleton />}
              </div>
            )}
          </div>
        </div>

        {/* Row 2, Col 3 - Configuration Panel */}
        <ConfigurationPanel
          config={configuration}
          onChange={setConfiguration}
          isSubmitting={isSubmitting}
        />
      </div>
    </section>
  );
}

