"use client";

import React from "react";

interface ConfigPanelHeaderProps {
  isSubmitting?: boolean;
  onReset: () => void;
}

export default function ConfigPanelHeader({
  isSubmitting: _isSubmitting = false,
  onReset,
}: ConfigPanelHeaderProps): React.JSX.Element {
  return (
    <div className="px-4 pt-4 pb-3 flex items-center">
      <div
        className="text-[13px] font-semibold text-ink"
        style={{ letterSpacing: "-0.01em" }}
      >
        Configuration
      </div>
      <span className="flex-1" />
      <button
        type="button"
        onClick={onReset}
        className="font-mono text-[10px] text-ink-mute px-2 py-0.5 rounded hover:text-ink-soft"
        style={{ letterSpacing: 0.6 }}
      >
        RESET
      </button>
    </div>
  );
}
