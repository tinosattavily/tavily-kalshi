"use client";

import React from "react";
import { Clock } from "lucide-react";

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
  const yesPct = Math.round(yesPrice * 100);
  const noPct = 100 - yesPct;

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

  // Check if analysis is complete (preserved from original behavior)
  const isComplete =
    run.status?.market === "done" &&
    run.status?.news === "done" &&
    run.status?.signal === "done" &&
    run.status?.report === "done";

  // Derive a status pill from existing data:
  // - Not complete -> LIVE (running/pending)
  // - Complete + signal up -> YES_WON
  // - Complete + signal down -> NO_WON
  // - Complete + neutral/none -> PENDING (LIVE label)
  const direction = run.signal?.direction?.toLowerCase();
  let statusKey = "PENDING";
  if (!isComplete) {
    statusKey = "RUNNING";
  } else if (direction === "up") {
    statusKey = "YES_WON";
  } else if (direction === "down") {
    statusKey = "NO_WON";
  }

  const statusMap: Record<
    string,
    { bg: string; fg: string; label: string }
  > = {
    NO_WON: { bg: "var(--no-soft)", fg: "var(--no)", label: "NO WON" },
    YES_WON: { bg: "var(--yes-soft)", fg: "var(--yes)", label: "YES WON" },
    PENDING: {
      bg: "var(--neu-track)",
      fg: "var(--ink-mute)",
      label: "LIVE",
    },
    RUNNING: {
      bg: "var(--neu-track)",
      fg: "var(--ink-mute)",
      label: "LIVE",
    },
  };
  const st =
    statusMap[statusKey] ?? {
      bg: "var(--neu-track)",
      fg: "var(--ink-mute)",
      label: statusKey || "—",
    };

  const confidenceValue =
    run.signal?.confidence_level || run.signal?.confidence;
  const hasSignal = run.signal && Object.keys(run.signal).length > 0;

  return (
    <button
      type="button"
      onClick={() => onClick(run)}
      className={
        "w-full text-left p-3 rounded mb-1.5 cursor-pointer transition-all border " +
        (isActive
          ? "bg-glass-strong shadow-neu-inset"
          : "bg-transparent hover:bg-glass border-transparent")
      }
      style={{ borderColor: isActive ? "var(--accent-soft)" : undefined }}
    >
      <div
        className="text-[12.5px] font-medium text-ink leading-snug"
        style={{
          display: "-webkit-box",
          WebkitLineClamp: 2,
          WebkitBoxOrient: "vertical",
          overflow: "hidden",
        }}
      >
        {question || "Untitled run"}
      </div>
      <div className="flex items-center gap-2 mt-2 font-mono text-[10px]">
        <span className="text-yes-ink">{yesPct}%</span>
        <div className="flex-1 h-0.5 rounded bg-no-soft relative overflow-hidden">
          <div
            className="absolute inset-0"
            style={{ width: `${yesPct}%`, background: "var(--yes)" }}
          />
        </div>
        <span className="text-no-ink">{noPct}%</span>
      </div>
      <div className="flex items-center gap-2 mt-2 font-mono text-[10px] text-ink-mute flex-wrap">
        <span className="inline-flex items-center gap-1">
          <Clock size={10} />
          {formatDate(run.run_at)}
        </span>
        <span className="flex-1" />
        <span
          className="font-mono uppercase font-semibold"
          style={{
            padding: "1px 6px",
            borderRadius: 3,
            background: st.bg,
            color: st.fg,
            letterSpacing: 0.5,
          }}
        >
          {st.label}
        </span>
        {hasSignal && confidenceValue && (
          <span
            className="font-mono text-ink-mute"
            style={{
              fontSize: 9,
              padding: "1px 4px",
              border: "1px solid var(--line)",
              borderRadius: 3,
            }}
          >
            {String(confidenceValue).toUpperCase()}
          </span>
        )}
        {!isComplete && (
          <span
            className="font-mono"
            style={{
              fontSize: 9,
              padding: "1px 4px",
              background: "var(--no-soft)",
              color: "var(--no)",
              borderRadius: 3,
            }}
          >
            INCOMPLETE
          </span>
        )}
      </div>
    </button>
  );
}
