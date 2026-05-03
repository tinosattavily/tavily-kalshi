"use client";

import React from "react";

export function NewsSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      {/* Card skeleton — 3 stacked news article placeholders */}
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="rounded p-3.5 bg-glass border border-ring shadow-soft backdrop-blur-glass animate-pulse"
        >
          <div className="flex items-center gap-2 mb-2">
            <div className="h-3 w-24 rounded bg-neu-track" />
            <div className="h-3 w-16 rounded bg-neu-track" />
            <span className="flex-1" />
            <div className="h-3 w-16 rounded bg-neu-track" />
          </div>
          <div className="h-4 w-full rounded bg-neu-track mb-1.5" />
          <div className="h-3 w-3/4 rounded bg-neu-track" />
        </div>
      ))}
    </div>
  );
}
