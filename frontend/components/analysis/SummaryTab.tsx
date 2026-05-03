"use client";

import React from "react";
import type { NewsArticle } from "../../types/market";

type Props = {
  highlights: NewsArticle[];
  combinedSummary?: string;
  newsSummary?: string;
};

export default function SummaryTab({ highlights, combinedSummary, newsSummary }: Props) {
  const total = highlights.length;
  const counts = highlights.reduce(
    (acc, item) => {
      const kind = (item.sentiment ?? "neutral") as "bullish" | "bearish" | "neutral";
      acc[kind] = (acc[kind] ?? 0) + 1;
      return acc;
    },
    { bullish: 0, bearish: 0, neutral: 0 } as Record<"bullish" | "bearish" | "neutral", number>
  );

  const bullishPct = total > 0 ? (counts.bullish / total) * 100 : 0;
  const bearishPct = total > 0 ? (counts.bearish / total) * 100 : 0;
  const neutralPct = total > 0 ? (counts.neutral / total) * 100 : 0;

  const summaryText = newsSummary || combinedSummary;

  if (total === 0 && !summaryText) {
    return (
      <div className="rounded p-4 bg-glass border border-ring shadow-soft backdrop-blur-glass text-sm text-ink-mute">
        No summary available.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {total > 0 ? (
        <div className="rounded p-4 bg-glass border border-ring shadow-soft backdrop-blur-glass">
          <h3
            className="font-mono uppercase text-ink-mute mb-3"
            style={{ fontSize: 10, letterSpacing: 0.6 }}
          >
            Sentiment Analysis
          </h3>
          <div className="space-y-2">
            <Row label="Bullish" pct={bullishPct} color="var(--yes)" />
            <Row label="Bearish" pct={bearishPct} color="var(--no)" />
            <Row label="Neutral" pct={neutralPct} color="var(--ink-mute)" />
          </div>
          <div className="mt-3 pt-3 border-t border-ring">
            <p
              className="font-mono uppercase text-ink-mute"
              style={{ fontSize: 10, letterSpacing: 0.6 }}
            >
              Based on {total} article{total !== 1 ? "s" : ""}
            </p>
          </div>
        </div>
      ) : null}

      {summaryText ? (
        <div className="rounded p-4 bg-glass border border-ring shadow-soft backdrop-blur-glass">
          <h3
            className="font-mono uppercase text-ink-mute mb-2"
            style={{ fontSize: 10, letterSpacing: 0.6 }}
          >
            Summary
          </h3>
          <p className="text-sm text-ink leading-relaxed whitespace-pre-wrap">{summaryText}</p>
        </div>
      ) : null}
    </div>
  );
}

function Row({ label, pct, color }: { label: string; pct: number; color: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-sm text-ink-soft">{label}</span>
      <div className="flex items-center gap-2">
        <div className="w-32 h-2 bg-neu-track rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-300"
            style={{ width: `${pct}%`, background: color }}
          />
        </div>
        <span
          className="font-mono w-12 text-right"
          style={{ fontSize: 11, color }}
        >
          {pct.toFixed(0)}%
        </span>
      </div>
    </div>
  );
}
