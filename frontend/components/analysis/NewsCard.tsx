"use client";

import React from "react";
import NewsTab from "./NewsTab";
import SummaryTab from "./SummaryTab";
import type { NewsArticle } from "../../types/market";

export type NewsItem = NewsArticle;

export interface NewsCardProps {
  heading?: string;
  highlights: NewsItem[];
  isLoading?: boolean;
  onItemClick?: (item: NewsItem) => void;
  newsSummary?: string;
  combinedSummary?: string;
}

/**
 * Legacy compatibility wrapper. New code should mount <NewsTab /> and
 * <SummaryTab /> directly via <MainPanel />.
 */
export function NewsCard(props: NewsCardProps) {
  return (
    <div className="flex flex-col gap-3">
      <NewsTab
        heading={props.heading}
        highlights={props.highlights}
        isLoading={props.isLoading}
        onItemClick={props.onItemClick}
      />
      <SummaryTab
        highlights={props.highlights}
        combinedSummary={props.combinedSummary}
        newsSummary={props.newsSummary}
      />
    </div>
  );
}

export default NewsCard;
