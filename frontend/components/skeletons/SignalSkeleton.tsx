"use client";

import React from "react";

export function SignalSkeleton() {
  return (
    <section className="rounded-lg p-5 bg-glass border border-ring shadow-soft backdrop-blur-glass mb-3.5 flex flex-col gap-4 animate-pulse">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="h-3 w-20 rounded bg-neu-track mb-2" />
          <div className="h-3 w-48 rounded bg-neu-track" />
        </div>
        <div className="h-6 w-24 rounded-full bg-neu-track" />
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex flex-col gap-1.5">
            <div className="h-3 w-20 rounded bg-neu-track" />
            <div className="h-5 w-16 rounded bg-neu-track" />
            <div className="h-3 w-28 rounded bg-neu-track" />
          </div>
        ))}
      </div>

      {/* Confidence row */}
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between border-t border-line pt-3">
        <div className="h-6 w-40 rounded-full bg-neu-track" />
        <div className="h-3 w-48 rounded bg-neu-track" />
      </div>
    </section>
  );
}
