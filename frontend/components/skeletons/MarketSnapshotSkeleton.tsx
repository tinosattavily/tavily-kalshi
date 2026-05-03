"use client";

import React from "react";

export function MarketSnapshotSkeleton() {
  return (
    <div
      className="relative rounded-lg bg-glass border border-ring shadow-soft backdrop-blur-glass p-5 animate-pulse"
    >
      {/* Header skeleton */}
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="h-3 w-28 rounded bg-neu-track mb-3" />
          <div className="h-6 w-64 rounded bg-neu-track mb-4" />
          <div className="h-4 w-48 rounded bg-neu-track" />
        </div>
        <div className="h-8 w-32 rounded-full bg-neu-track" />
      </div>

      {/* Grid skeleton */}
      <div className="grid gap-2.5" style={{ gridTemplateColumns: "minmax(0, 1fr) auto" }}>
        <div className="grid grid-cols-2 gap-2.5">
          <div className="h-24 rounded bg-yes-soft" />
          <div className="h-24 rounded bg-no-soft" />
        </div>

        {/* Metrics column */}
        <div className="flex flex-col gap-2.5" style={{ width: 150 }}>
          <div className="h-12 rounded bg-glass-strong border border-ring" />
          <div className="h-12 rounded bg-glass-strong border border-ring" />
          <div className="h-12 rounded bg-glass-strong border border-ring" />
        </div>
      </div>

      {/* Footer skeleton */}
      <div className="mt-3 flex items-center justify-between">
        <div className="h-3 w-32 rounded bg-neu-track" />
        <div className="h-3 w-24 rounded bg-neu-track" />
      </div>
    </div>
  );
}
