"use client";

import React, { useCallback } from "react";
import MarketPicker from "./MarketPicker";
import { MarketCard } from "./MarketCard";
import MainPanel from "./MainPanel";
import NewsTab from "./NewsTab";
import SummaryTab from "./SummaryTab";
import SignalCard from "./SignalCard";
import ReportCard from "./ReportCard";
import { MarketSnapshotSkeleton } from "../skeletons/MarketSnapshotSkeleton";
import { NewsSkeleton } from "../skeletons/NewsSkeleton";
import { SignalSkeleton } from "../skeletons/SignalSkeleton";
import { ReportSkeleton } from "../skeletons/ReportSkeleton";
import EmptyState from "../input/EmptyState";
import { logger } from "../../lib/logger";
import type { AnalysisResults as AnalysisResultsType, NewsArticle, NewsContext, RunStatus } from "../../types";

interface AnalysisResultsProps {
  results: AnalysisResultsType | null;
  runStatus: RunStatus | null;
  url: string;
  isSubmitting: boolean;
  selectedMarketId: string | null;
  lastSortedMarketOptions: { market_id: string; question: string; slug?: string }[];
  onSelectMarket: (marketId: string) => void;
  onSortedOptionsChange: (options: Array<{ market_id?: string; slug?: string; question?: string; id?: string; title?: string; label?: string }>) => void;
}

/**
 * Renders analysis results including market card, news, signal, and report
 */
export function AnalysisResultsView({
  results,
  runStatus,
  url,
  isSubmitting,
  selectedMarketId,
  lastSortedMarketOptions,
  onSelectMarket,
  onSortedOptionsChange,
}: AnalysisResultsProps): React.JSX.Element {

  // Utility: humanize time remaining
  const humanizeClosesIn = useCallback((isoDate?: string) => {
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
  }, []);

  // Utility: map market options
  const mapMarketOptions = useCallback(
    (options: Array<{ market_id?: string; slug?: string; question?: string; id?: string; title?: string; label?: string }> | undefined | null) => {
      if (!Array.isArray(options)) return [];
      return options
        .flatMap((option) => {
          const marketId = option?.market_id ?? option?.slug ?? option?.id;
          if (!marketId) return [];
          return {
            market_id: String(marketId),
            slug: option?.slug,
            question: option?.label || option?.question || option?.title || String(marketId),
          };
        });
    },
    []
  );

  // Utility: map news articles
  const mapNewsArticles = useCallback((newsContext?: NewsContext) => {
    if (!newsContext?.articles || !Array.isArray(newsContext.articles) || newsContext.articles.length === 0) {
      logger.debug(
        "No articles to map",
        `has_context: ${!!newsContext}`,
        `articles_type: ${typeof newsContext?.articles}`,
        `articles_length: ${newsContext?.articles?.length ?? 0}`,
        `is_array: ${Array.isArray(newsContext?.articles)}`
      );
      return [];
    }

    logger.debug("Mapping news articles", `count: ${newsContext.articles.length}`);

    return newsContext.articles.map((article: NewsArticle) => ({
      title: article.title || "Untitled",
      source: article.source || "Unknown source",
      publishedAt: article.published_at || undefined,
      url: article.url || undefined,
      summary: article.snippet || undefined,
      sentiment: (article.sentiment || "neutral") as "bullish" | "bearish" | "neutral",
    }));
  }, []);

  // Empty state
  if (!results) {
    return <EmptyState />;
  }

  // Market selection required
  const requiresMarketSelection =
    results.requires_market_selection &&
    (!results.market_snapshot || Object.keys(results.market_snapshot).length === 0) &&
    results.market_options &&
    results.market_options.length > 0;

  if (requiresMarketSelection) {
    return (
      <MarketPicker
        options={results.market_options!.filter((opt) => Boolean(opt.market_id || opt.slug || opt.id))}
        eventContext={results.event_context}
        isSubmitting={isSubmitting}
        onSelect={onSelectMarket}
        onSortedOptionsChange={onSortedOptionsChange}
      />
    );
  }

  // Render analysis cards
  return (
    <div>
      {/* Market Card */}
      <MarketCardSection
        results={results}
        runStatus={runStatus}
        url={url}
        selectedMarketId={selectedMarketId}
        lastSortedMarketOptions={lastSortedMarketOptions}
        onSelectMarket={onSelectMarket}
        humanizeClosesIn={humanizeClosesIn}
        mapMarketOptions={mapMarketOptions}
      />

      {/* Tabbed main panel: News / Summary / Thesis */}
      <MainPanelSection
        results={results}
        runStatus={runStatus}
        mapNewsArticles={mapNewsArticles}
      />
    </div>
  );
}

// Sub-components for each section

interface MarketCardSectionProps {
  results: AnalysisResultsType;
  runStatus: RunStatus | null;
  url: string;
  selectedMarketId: string | null;
  lastSortedMarketOptions: { market_id: string; question: string; slug?: string }[];
  onSelectMarket: (marketId: string) => void;
  humanizeClosesIn: (isoDate?: string) => string;
  mapMarketOptions: (options: Array<{ market_id?: string; slug?: string; question?: string; id?: string; title?: string; label?: string }> | undefined | null) => { market_id: string; question: string; slug?: string }[];
}

function MarketCardSection({
  results,
  runStatus,
  url,
  selectedMarketId,
  lastSortedMarketOptions,
  onSelectMarket,
  humanizeClosesIn,
  mapMarketOptions,
}: MarketCardSectionProps): React.JSX.Element | null {
  const shouldShowMarketCard =
    runStatus?.market === "done" &&
    results.market_snapshot &&
    Object.keys(results.market_snapshot).length > 0;
  const shouldShowMarketSkeleton =
    runStatus?.market === "pending" || runStatus?.market === undefined;

  if (shouldShowMarketCard && results.market_snapshot) {
    return (
      <div className="mb-6">
        <MarketCard
          eventTitle={results.event_context?.title || results.market_snapshot.question || "Event"}
          groupItemTitle={results.market_snapshot.group_item_title || results.market_snapshot.groupItemTitle}
          venue={results.market_snapshot.venue}
          marketUrl={results.market_snapshot.url || results.event_context?.url || url || "#"}
          closesIn={humanizeClosesIn(results.market_snapshot.endDate || results.market_snapshot.end_date)}
          endDate={results.market_snapshot.endDate || results.market_snapshot.end_date}
          question={results.market_snapshot.question}
          previousMarkets={
            lastSortedMarketOptions.length > 0
              ? lastSortedMarketOptions
              : mapMarketOptions(results.market_options)
          }
          activeMarketId={selectedMarketId ?? undefined}
          onMarketSelect={onSelectMarket}
          yesPrice={results.market_snapshot.yes_price ?? 0}
          noPrice={results.market_snapshot.no_price ?? 0}
          marketVolume={Number(results.market_snapshot.volume ?? 0)}
          volume24h={results.market_snapshot.volume24hr || results.event_context?.volume24hr}
          liquidity={Number(results.market_snapshot.liquidity ?? 0)}
          commentCount={results.event_context?.commentCount ?? results.market_snapshot?.comment_count ?? results.market_snapshot?.commentCount}
          eventCommentCount={results.event_context?.commentCount ?? results.market_snapshot?.event_comment_count ?? results.market_snapshot?.eventCommentCount}
          seriesCommentCount={results.event_context?.seriesCommentCount ?? results.market_snapshot?.series_comment_count ?? results.market_snapshot?.seriesCommentCount}
          bestBid={results.market_snapshot.best_bid ?? results.market_snapshot.bestBid}
          bestAsk={results.market_snapshot.best_ask ?? results.market_snapshot.bestAsk}
          bids={(results.market_snapshot.order_book?.bids || results.market_snapshot.orderBook?.bids || []).map((b: { price?: number; size?: number }) => ({
            price: Number(b.price ?? 0),
            size: Number(b.size ?? 0),
          }))}
          asks={(results.market_snapshot.order_book?.asks || results.market_snapshot.orderBook?.asks || []).map((a: { price?: number; size?: number }) => ({
            price: Number(a.price ?? 0),
            size: Number(a.size ?? 0),
          }))}
        />
      </div>
    );
  }

  if (shouldShowMarketSkeleton) {
    return (
      <div className="mb-6">
        <MarketSnapshotSkeleton />
      </div>
    );
  }

  return null;
}

interface MainPanelSectionProps {
  results: AnalysisResultsType;
  runStatus: RunStatus | null;
  mapNewsArticles: (newsContext?: NewsContext) => Array<{
    title: string;
    source: string;
    publishedAt?: string;
    url?: string;
    summary?: string;
    sentiment: "bullish" | "bearish" | "neutral";
  }>;
}

function MainPanelSection({
  results,
  runStatus,
  mapNewsArticles,
}: MainPanelSectionProps): React.JSX.Element | null {
  const newsReady = runStatus?.news === "done" && Boolean(results.news_context);
  const signalReady =
    runStatus?.signal === "done" &&
    Boolean(results.signal) &&
    Object.keys(results.signal ?? {}).length > 0;
  const reportReady = runStatus?.report === "done" && Boolean(results.report);

  // While early phases are still pending, show stacked skeletons (preserves prior behavior).
  if (!newsReady && !signalReady && !reportReady) {
    return (
      <div>
        <div className="mb-6">
          <NewsSkeleton />
        </div>
        <SignalSkeleton />
        <ReportSkeleton />
      </div>
    );
  }

  const articles = newsReady ? mapNewsArticles(results.news_context) : [];

  const newsTab = (
    <NewsTab
      highlights={articles}
      isLoading={!newsReady}
      onItemClick={(item) => {
        if (item.url) {
          window.open(item.url, "_blank", "noopener,noreferrer");
        }
      }}
    />
  );

  const summaryTab = (
    <SummaryTab
      highlights={articles}
      newsSummary={results.news_context?.summary}
      combinedSummary={results.news_context?.combined_summary}
    />
  );

  const thesisTab = (
    <>
      {signalReady ? <SignalCard signal={results.signal!} /> : <SignalSkeleton />}
      {reportReady ? (
        <ReportCard report={results.report!} eventContext={results.event_context} signal={results.signal ?? null} />
      ) : (
        <ReportSkeleton />
      )}
    </>
  );

  return (
    <MainPanel
      newsCount={articles.length}
      newsTab={newsTab}
      summaryTab={summaryTab}
      thesisTab={thesisTab}
    />
  );
}
