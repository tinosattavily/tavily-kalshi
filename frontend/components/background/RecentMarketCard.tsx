"use client";

import React from "react";

import { CheckCircle2, Clock, Minus, TrendingDown, TrendingUp, XCircle } from "lucide-react";
import clsx from "clsx";

export interface Resolution {
  status?: 'pending' | 'resolved_yes' | 'resolved_no' | 'voided' | 'unknown';
  winning_outcome?: string;
  resolved_at?: string;
  final_yes_price?: number;
  final_no_price?: number;
  checked_at?: string;
}

export interface RecentRun {
  _id: string;
  run_id?: string;
  slug?: string;
  polymarket_url?: string;
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
  resolution?: Resolution;
}

interface RecentMarketCardProps {
  run: RecentRun;
  onClick: (run: RecentRun) => void;
  isActive?: boolean;
}

function formatRelativeDate(dateStr?: string): string {
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
}

function getConfidenceClasses(level: string | undefined): string {
  const normalized = level?.toUpperCase() || "";
  if (normalized === "HIGH") return "bg-[#1e3a8a]/20 text-[#1e3a8a]";
  if (normalized === "MEDIUM") return "bg-[#1e3a8a]/10 text-[#1e3a8a]";
  return "bg-[#1e3a8a]/5 text-[#1e3a8a]/70";
}

function ResolutionBadge({ resolution }: { resolution?: Resolution }): React.JSX.Element | null {
  if (!resolution || !resolution.status || resolution.status === 'pending') {
    return null;
  }

  if (resolution.status === 'resolved_yes') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-[#e8f5e9] text-emerald-900 whitespace-nowrap">
        <CheckCircle2 className="w-3 h-3" />
        YES WON
      </span>
    );
  }

  if (resolution.status === 'resolved_no') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-[#ffebee] text-rose-900 whitespace-nowrap">
        <XCircle className="w-3 h-3" />
        NO WON
      </span>
    );
  }

  if (resolution.status === 'voided') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-neutral-200 text-neutral-700 whitespace-nowrap">
        VOIDED
      </span>
    );
  }

  return null;
}

export default function RecentMarketCard({
  run,
  onClick,
  isActive = false,
}: RecentMarketCardProps): React.JSX.Element {
  const question = run.market_snapshot?.question || run.event_context?.title || "Unknown Market";
  const yesPrice = run.market_snapshot?.yes_price ?? 0;
  const noPrice = run.market_snapshot?.no_price ?? 0;

  const hasSignal = run.signal && Object.keys(run.signal).length > 0;
  const confidence = run.signal?.confidence_level || run.signal?.confidence || "low";

  const isComplete =
    run.status?.market === "done" &&
    run.status?.news === "done" &&
    run.status?.signal === "done" &&
    run.status?.report === "done";

  function renderSignalIcon(): React.JSX.Element {
    const direction = run.signal?.direction?.toLowerCase();
    if (direction === "up") {
      return <TrendingUp className="w-3 h-3 text-emerald-900" />;
    }
    if (direction === "down") {
      return <TrendingDown className="w-3 h-3 text-rose-900" />;
    }
    return <Minus className="w-3 h-3 text-slate-400" />;
  }

  return (
    <button
      onClick={() => onClick(run)}
      className={clsx(
        "w-full text-left p-3 rounded-xl border transition-all duration-300 overflow-hidden backdrop-blur-sm relative",
        isActive
          ? "bg-[#1e3a8a]/10 border-[#1e3a8a]/25 shadow-[0_4px_20px_rgba(30,58,138,0.15)]"
          : "bg-white/5 border-white/15 shadow-[0_2px_8px_rgba(30,58,138,0.05)] hover:bg-white/10 hover:border-[#1e3a8a]/20 hover:shadow-[0_4px_16px_rgba(30,58,138,0.1)]",
      )}
      style={{ WebkitBackdropFilter: "blur(8px)" }}
    >
      {/* Question/Title */}
      <div className="mb-2 min-w-0">
        <p className={clsx(
          "text-sm font-medium line-clamp-2 break-words overflow-hidden",
          isActive ? "text-[#1e3a8a]" : "text-neutral-800"
        )}>
          {question}
        </p>
      </div>

      {/* Price and Signal Row */}
      <div className="flex items-center justify-between mb-2 min-w-0 gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs font-semibold text-emerald-900 whitespace-nowrap">
            YES: {(yesPrice * 100).toFixed(1)}%
          </span>
          <span className="text-xs font-semibold text-rose-900 whitespace-nowrap">
            NO: {(noPrice * 100).toFixed(1)}%
          </span>
        </div>
        {hasSignal && <div className="flex-shrink-0">{renderSignalIcon()}</div>}
      </div>

      {/* Footer: Date, Confidence, Status, Resolution */}
      <div className="flex items-center justify-between text-xs text-neutral-500 min-w-0 gap-2">
        <div className={clsx(
          "flex items-center gap-1 min-w-0",
          isActive && "text-[#1e3a8a]"
        )}>
          <Clock className="w-3 h-3 flex-shrink-0" />
          <span className="truncate">{formatRelativeDate(run.run_at)}</span>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <ResolutionBadge resolution={run.resolution} />
          {hasSignal && !run.resolution?.status?.startsWith('resolved') && (
            <span
              className={clsx(
                "px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap",
                getConfidenceClasses(confidence),
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
