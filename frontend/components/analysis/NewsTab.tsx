"use client";

import React from "react";
import { ArrowUpRight } from "lucide-react";
import Sentiment from "./Sentiment";
import type { NewsArticle } from "../../types/market";

export type NewsItem = NewsArticle;

type Props = {
  heading?: string;
  highlights: NewsItem[];
  isLoading?: boolean;
  onItemClick?: (item: NewsItem) => void;
};

export default function NewsTab({ heading, highlights, isLoading, onItemClick }: Props) {
  const showLoading = isLoading && highlights.length === 0;

  return (
    <div className="flex flex-col gap-3">
      {heading ? (
        <p className="font-mono uppercase text-ink-mute" style={{ fontSize: 10, letterSpacing: 0.6 }}>
          {heading}
        </p>
      ) : null}

      {showLoading ? (
        <div className="animate-pulse space-y-3 rounded p-3.5 bg-glass border border-ring shadow-soft backdrop-blur-glass">
          <div className="h-4 w-2/3 rounded bg-neu-track" />
          <div className="h-3 w-full rounded bg-neu-track" />
          <div className="h-3 w-5/6 rounded bg-neu-track" />
        </div>
      ) : highlights.length === 0 ? (
        <div className="rounded p-3.5 bg-glass border border-ring shadow-soft backdrop-blur-glass text-sm text-ink-mute">
          No articles in this run.
        </div>
      ) : (
        highlights.map((item, idx) => {
          const sentiment = (item.sentiment ?? "neutral") as "bullish" | "bearish" | "neutral";
          const publishedAt = item.publishedAt ?? item.published_at;
          const snippet = item.snippet ?? item.summary;
          return (
            <button
              key={`${item.title ?? "untitled"}-${idx}`}
              type="button"
              onClick={() => onItemClick?.(item)}
              className="text-left rounded p-3.5 bg-glass border border-ring shadow-soft backdrop-blur-glass transition hover:-translate-y-0.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
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
                    className="group inline-flex items-center gap-1.5 font-mono uppercase text-accent hover:underline"
                    style={{ fontSize: 10, letterSpacing: 0.6 }}
                  >
                    <span>{item.source}</span>
                    <ArrowUpRight className="h-3 w-3" />
                  </a>
                ) : (
                  <span
                    className="font-mono uppercase text-ink-mute"
                    style={{ fontSize: 10, letterSpacing: 0.6 }}
                  >
                    {item.source ?? "Source"}
                  </span>
                )}
                {publishedAt ? (
                  <span
                    className="font-mono uppercase text-ink-mute"
                    style={{ fontSize: 10, letterSpacing: 0.6 }}
                  >
                    {new Date(publishedAt).toLocaleString(undefined, {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                ) : null}
                <Sentiment kind={sentiment} />
              </div>
              <h3 className="mt-1.5 text-base font-semibold text-ink">{item.title ?? "Untitled"}</h3>
              {snippet ? (
                <p className="mt-1 text-sm text-ink-soft line-clamp-2">{snippet}</p>
              ) : null}
            </button>
          );
        })
      )}
    </div>
  );
}
