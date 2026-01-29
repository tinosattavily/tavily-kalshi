"use client";

import React, { useState } from "react";

import { ArrowUpRight } from "lucide-react";

interface NewsItem {
  title: string;
  source?: string;
  publishedAt?: string;
  url?: string;
  summary?: string;
  sentiment?: "bullish" | "bearish" | "neutral";
}

export interface NewsCardProps {
  heading?: string;
  highlights: NewsItem[];
  isLoading?: boolean;
  onItemClick?: (item: NewsItem) => void;
  newsSummary?: string;
  combinedSummary?: string;
}

const SENTIMENT_COLORS: Record<string, string> = {
  bearish: "text-rose-900 bg-red-50",
  bullish: "text-emerald-900 bg-green-50",
  neutral: "text-slate-600 bg-slate-100",
};

function calculateSentimentBreakdown(items: NewsItem[]): {
  bullishPct: number;
  bearishPct: number;
  neutralPct: number;
} {
  const total = items.length;
  if (total === 0) {
    return { bullishPct: 0, bearishPct: 0, neutralPct: 0 };
  }

  const counts = items.reduce(
    (acc, item) => {
      const sentiment = item.sentiment || "neutral";
      acc[sentiment] = (acc[sentiment] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  return {
    bullishPct: ((counts.bullish || 0) / total) * 100,
    bearishPct: ((counts.bearish || 0) / total) * 100,
    neutralPct: ((counts.neutral || 0) / total) * 100,
  };
}

export function NewsCard({
  heading = "Market News",
  highlights,
  isLoading,
  onItemClick,
  newsSummary,
  combinedSummary,
}: NewsCardProps): React.JSX.Element {
  const [activeTab, setActiveTab] = useState<"news" | "summary">("news");

  const { bullishPct, bearishPct, neutralPct } = calculateSentimentBreakdown(highlights);
  const totalArticles = highlights.length;

  return (
    <div className="relative">
      {/* Tab header */}
      <div className="flex gap-2 mb-4 border-b border-[#1e3a8a]/20">
        <button
          onClick={() => setActiveTab("news")}
          className={`px-4 py-2 text-sm font-semibold uppercase tracking-wide transition-all duration-200 border-b-2 ${
            activeTab === "news"
              ? "text-[#1e3a8a] border-[#1e3a8a]"
              : "text-[#1e3a8a]/50 border-transparent hover:text-[#1e3a8a]/80"
          }`}
        >
          News
        </button>
        <button
          onClick={() => setActiveTab("summary")}
          className={`px-4 py-2 text-sm font-semibold uppercase tracking-wide transition-all duration-200 border-b-2 ${
            activeTab === "summary"
              ? "text-[#1e3a8a] border-[#1e3a8a]"
              : "text-[#1e3a8a]/50 border-transparent hover:text-[#1e3a8a]/80"
          }`}
        >
          Summary
        </button>
      </div>

      {/* Tab content */}
      <div
        className="rounded-3xl bg-[#1e3a8a]/5 p-8 shadow-[0_16px_40px_rgba(30,58,138,0.15)] backdrop-blur-xl border border-[#1e3a8a]/20 flex flex-col gap-4"
        style={{ WebkitBackdropFilter: "blur(14px)" }}
      >
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="py-2 flex items-center gap-2 text-base uppercase tracking-[0.18em] text-[#1e3a8a]">
              {activeTab === "news" ? (
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 2048 2048" className="text-[#1e3a8a]">
                  <path fill="currentColor" d="M2048 512v896q0 53-20 99t-55 81t-82 55t-99 21H249q-51 0-96-20t-79-53t-54-79t-20-97V256h1792v256h256zm-128 128h-128v704q0 26-19 45t-45 19q-26 0-45-19t-19-45V384H128v1031q0 25 9 47t26 38t39 26t47 10h1543q27 0 50-10t40-27t28-41t10-50V640zm-384 0H256V512h1280v128zm0 768h-512v-128h512v128zm0-256h-512v-128h512v128zm0-256h-512V768h512v128zm-640 512H256V765h640v643zm-512-128h384V893H384v387z"/>
                </svg>
              ) : (
                <svg width="20" height="20" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" className="text-[#1e3a8a]">
                  <path fill="currentColor" d="M2 15h2v7H2zm6-5h2v12H8zm6 4h2v8h-2zm6-4h2v12h-2zm-2-5h1v1h-1zm-1 1h1v1h-1zm-3 1h2v1h-2zm0 3h2v1h-2zm-1-2h1v2h-1zm3 0h1v2h-1zm-4-2h1v1h-1zm-1-1h1v1h-1zM8 4h2v1H8zm0-3h2v1H8zm2 1h1v2h-1zM7 2h1v2H7zm13 2h2v1h-2zm-1-2h1v2h-1zm1-1h2v1h-2zm2 1h1v2h-1zM6 6h1v1H6zM5 7h1v1H5zM4 9h1v2H4zM1 9h1v2H1zm1-1h2v1H2zm0 3h2v1H2z"/>
                </svg>
              )}
              {activeTab === "news" ? "Market News" : "Sentiment Analysis and Summary"}
            </p>
          </div>
          {activeTab === "news" && (
            <span className="rounded-full bg-[#1e3a8a]/10 px-3 py-1 text-xs font-semibold text-[#1e3a8a] shadow-sm">
              {isLoading ? "Updating…" : `${highlights.length} stories`}
            </span>
          )}
        </div>

        {/* News Tab Content */}
        {activeTab === "news" && (
          <div className="flex flex-col gap-4 min-h-0 flex-shrink-0 max-h-[380px] overflow-y-auto overflow-x-hidden pr-2" style={{ scrollbarWidth: 'thin', WebkitOverflowScrolling: 'touch' }}>
            {isLoading && highlights.length === 0 ? (
              <div className="animate-pulse space-y-3">
                <div className="h-4 w-2/3 rounded bg-white/60" />
                <div className="h-3 w-full rounded bg-white/60" />
                <div className="h-3 w-5/6 rounded bg-white/60" />
              </div>
            ) : (
              highlights.map((item, idx) => {
                const sentimentColor =
                  item.sentiment && SENTIMENT_COLORS[item.sentiment]
                    ? SENTIMENT_COLORS[item.sentiment]
                    : SENTIMENT_COLORS.neutral;
                return (
                  <button
                    key={`${item.title}-${idx}`}
                    onClick={() => onItemClick?.(item)}
                    className="text-left rounded-2xl bg-white/60 px-6 py-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1e3a8a]/50"
                  >
                    <div className="flex items-center justify-between gap-2">
                      {item.url && item.source ? (
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => {
                            e.stopPropagation();
                            onItemClick?.(item);
                          }}
                          className="group flex items-center gap-1.5 text-sm font-medium text-[#1e3a8a] hover:text-[#1e3a8a]/80 transition-colors"
                        >
                          <span>{item.source}</span>
                          <ArrowUpRight className="h-3 w-3 text-[#1e3a8a]/70 group-hover:text-[#1e3a8a] transition-colors" />
                        </a>
                      ) : (
                        <span className="text-sm font-medium text-slate-500">
                          {item.source ?? "Source"}
                        </span>
                      )}
                      {item.publishedAt ? (
                        <span className="text-xs text-slate-400">
                          {new Date(item.publishedAt).toLocaleString(undefined, {
                            month: "short",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      ) : null}
                      <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${sentimentColor}`}>
                        {item.sentiment ?? "neutral"}
                      </span>
                    </div>
                    <h3 className="mt-1 text-base font-semibold text-slate-900">{item.title}</h3>
                    {item.summary ? (
                      <p className="mt-1 text-sm text-slate-600 line-clamp-2">{item.summary}</p>
                    ) : null}
                  </button>
                );
              })
            )}
          </div>
        )}

        {/* Summary/Sentiment Analysis Tab Content */}
        {activeTab === "summary" && (
          <div className="flex flex-col gap-4 min-h-0 flex-shrink-0 max-h-[380px] overflow-y-auto overflow-x-hidden pr-2" style={{ scrollbarWidth: 'thin', WebkitOverflowScrolling: 'touch' }}>
            {/* Sentiment Breakdown */}
            <div className="rounded-2xl bg-white/60 px-4 py-3 shadow-sm">
              <h3 className="text-base font-semibold text-slate-900 mb-3">Sentiment Analysis</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">Bullish</span>
                  <div className="flex items-center gap-2">
                    <div className="w-32 h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-emerald-900 rounded-full transition-all duration-300"
                        style={{ width: `${bullishPct}%` }}
                      />
                    </div>
                    <span className="text-sm font-semibold text-emerald-900 w-12 text-right">
                      {bullishPct.toFixed(0)}%
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">Bearish</span>
                  <div className="flex items-center gap-2">
                    <div className="w-32 h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-rose-900 rounded-full transition-all duration-300"
                        style={{ width: `${bearishPct}%` }}
                      />
                    </div>
                    <span className="text-sm font-semibold text-rose-900 w-12 text-right">
                      {bearishPct.toFixed(0)}%
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">Neutral</span>
                  <div className="flex items-center gap-2">
                    <div className="w-32 h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-slate-400 rounded-full transition-all duration-300"
                        style={{ width: `${neutralPct}%` }}
                      />
                    </div>
                    <span className="text-sm font-semibold text-slate-600 w-12 text-right">
                      {neutralPct.toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-slate-200">
                <p className="text-xs text-slate-500">
                  Based on {totalArticles} article{totalArticles !== 1 ? "s" : ""}
                </p>
              </div>
            </div>

            {/* News Summary */}
            {(newsSummary || combinedSummary) && (
              <div className="rounded-2xl bg-white/60 px-4 py-3 shadow-sm">
                <h3 className="text-base font-semibold text-slate-900 mb-2">Summary</h3>
                <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                  {newsSummary || combinedSummary}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
