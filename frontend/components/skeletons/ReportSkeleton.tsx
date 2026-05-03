"use client";

import React from "react";

export function ReportSkeleton() {
  return (
    <section className="rounded-lg p-5 bg-glass border border-ring shadow-soft backdrop-blur-glass animate-pulse">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div>
          <div className="h-3 w-32 rounded bg-neu-track mb-2" />
          <div className="h-4 w-56 rounded bg-neu-track" />
        </div>
        <div className="h-7 w-24 rounded-full bg-neu-track" />
      </div>

      {/* Content skeleton */}
      <div className="flex flex-col gap-4">
        {/* Headline */}
        <div className="h-6 w-3/4 rounded bg-neu-track" />

        {/* Thesis */}
        <div>
          <div className="h-3 w-20 rounded bg-neu-track mb-2" />
          <div className="h-3 w-full rounded bg-neu-track mb-1.5" />
          <div className="h-3 w-5/6 rounded bg-neu-track" />
        </div>

        {/* Bull/Bear cases */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="rounded p-4 bg-yes-soft border border-ring">
            <div className="h-3 w-24 rounded bg-neu-track mb-3" />
            <div className="space-y-2">
              <div className="h-3 w-full rounded bg-neu-track" />
              <div className="h-3 w-5/6 rounded bg-neu-track" />
            </div>
          </div>
          <div className="rounded p-4 bg-no-soft border border-ring">
            <div className="h-3 w-24 rounded bg-neu-track mb-3" />
            <div className="space-y-2">
              <div className="h-3 w-full rounded bg-neu-track" />
              <div className="h-3 w-5/6 rounded bg-neu-track" />
            </div>
          </div>
        </div>

        {/* Key risks */}
        <div className="rounded p-4 bg-glass-strong border border-ring">
          <div className="h-3 w-28 rounded bg-neu-track mb-3" />
          <div className="space-y-2">
            <div className="h-3 w-full rounded bg-neu-track" />
            <div className="h-3 w-4/5 rounded bg-neu-track" />
          </div>
        </div>
      </div>
    </section>
  );
}
