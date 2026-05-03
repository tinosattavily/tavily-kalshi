"use client";

import React from "react";
import { Clock, RefreshCw } from "lucide-react";

interface HistorySidebarHeaderProps {
  isLoading: boolean;
  onRefresh: () => void;
}

export default function HistorySidebarHeader({
  isLoading: _isLoading,
  onRefresh,
}: HistorySidebarHeaderProps): React.JSX.Element {
  return (
    <div className="px-4 pt-4 pb-3 flex items-center gap-2">
      <Clock size={13} className="text-ink-mute" />
      <span
        className="font-mono uppercase text-ink-mute flex-1"
        style={{ fontSize: 11, letterSpacing: 1.2 }}
      >
        Sessions
      </span>
      <button
        type="button"
        onClick={onRefresh}
        className="text-ink-mute p-1 hover:text-ink-soft"
        aria-label="Refresh sessions"
      >
        <RefreshCw size={12} />
      </button>
    </div>
  );
}
