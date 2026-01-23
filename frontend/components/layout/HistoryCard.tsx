"use client";

import React from "react";
import { Clock, TrendingUp, TrendingDown, Minus } from "lucide-react";
import clsx from "clsx";

export interface RecentRun {
  _id: string;
  run_id?: string;
  slug?: string;
  market_url?: string;
  polymarket_url?: string; // Legacy field for backwards compatibility
  run_at?: string;
  market_snapshot?: {
    question?: string;
    yes_price?: number;
    no_price?: number;
  };
  event_context?: {
    title?: string;
  };
  signal?: {
    direction?: string;
    confidence?: string;
    confidence_level?: string;
  };
  status?: {
    market?: string;
    news?: string;
    signal?: string;
    report?: string;
  };
}

interface RecentMarketCardProps {
  run: RecentRun;
  onClick: (run: RecentRun) => void;
  isActive?: boolean;
}

export default function RecentMarketCard({
  run,
  onClick,
  isActive = false,
}: RecentMarketCardProps): React.JSX.Element {
  const question =
    run.market_snapshot?.question ||
    run.event_context?.title ||
    "Unknown Market";

  const yesPrice = run.market_snapshot?.yes_price ?? 0;
  const noPrice = run.market_snapshot?.no_price ?? 0;

  // Format date
  const formatDate = (dateStr?: string): string => {
    if (!dateStr) return "Unknown date";
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return "Just now";
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      return date.toLocaleDateString();
    } catch {
      return "Unknown date";
    }
  };

  // Get signal direction icon
  const getSignalIcon = () => {
    const direction = run.signal?.direction?.toLowerCase();
    if (direction === "up") {
      return <TrendingUp className="w-3 h-3 text-emerald-600" />;
    }
    if (direction === "down") {
      return <TrendingDown className="w-3 h-3 text-rose-600" />;
    }
    return <Minus className="w-3 h-3 text-slate-400" />;
  };

  // Get confidence badge color
  const getConfidenceColor = (): string => {
    const confidence =
      run.signal?.confidence_level?.toUpperCase() ||
      run.signal?.confidence?.toUpperCase() ||
      "";
    if (confidence === "HIGH") return "bg-emerald-100 text-emerald-700";
    if (confidence === "MEDIUM") return "bg-indigo-100 text-indigo-700";
    return "bg-amber-100 text-amber-700";
  };

  const confidence =
    run.signal?.confidence_level || run.signal?.confidence || "low";

  // Check if analysis is complete
  const isComplete =
    run.status?.market === "done" &&
    run.status?.news === "done" &&
    run.status?.signal === "done" &&
    run.status?.report === "done";

  return (
    <button
      onClick={() => onClick(run)}
      className={clsx(
        "w-full text-left p-3 rounded-lg border transition-all duration-200",
        "hover:shadow-md hover:border-indigo-300 overflow-hidden",
        isActive
          ? "bg-indigo-50 border-indigo-300 shadow-sm"
          : "bg-white border-neutral-200 hover:bg-neutral-50",
      )}
    >
      {/* Question/Title */}
      <div className="mb-2 min-w-0">
        <p className="text-sm font-medium text-neutral-800 line-clamp-2 break-words overflow-hidden">
          {question}
        </p>
      </div>

      {/* Price and Signal Row */}
      <div className="flex items-center justify-between mb-2 min-w-0 gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs font-semibold text-emerald-600 whitespace-nowrap">
            YES: {(yesPrice * 100).toFixed(1)}%
          </span>
          <span className="text-xs font-semibold text-rose-600 whitespace-nowrap">
            NO: {(noPrice * 100).toFixed(1)}%
          </span>
        </div>
        {run.signal && Object.keys(run.signal).length > 0 && (
          <div className="flex-shrink-0">
            {getSignalIcon()}
          </div>
        )}
      </div>

      {/* Footer: Date, Confidence, Status */}
      <div className="flex items-center justify-between text-xs text-neutral-500 min-w-0 gap-2">
        <div className="flex items-center gap-1 min-w-0">
          <Clock className="w-3 h-3 flex-shrink-0" />
          <span className="truncate">{formatDate(run.run_at)}</span>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {run.signal && Object.keys(run.signal).length > 0 && (
            <span
              className={clsx(
                "px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap",
                getConfidenceColor(),
              )}
            >
              {confidence.toUpperCase()}
            </span>
          )}
          {!isComplete && (
            <span className="px-2 py-0.5 rounded text-xs bg-amber-100 text-amber-700 whitespace-nowrap">
              Incomplete
            </span>
          )}
        </div>
      </div>
    </button>
  );
}

