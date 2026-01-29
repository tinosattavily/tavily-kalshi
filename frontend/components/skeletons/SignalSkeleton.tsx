"use client";

import React from "react";

export function SignalSkeleton(): React.JSX.Element {
  return (
    <section className="mb-6 rounded-3xl p-8 backdrop-blur-xl flex flex-col gap-4 bg-slate-50/40 border border-slate-100/50 animate-pulse">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="h-6 w-32 rounded-full bg-slate-200 mb-2" />
          <div className="h-4 w-48 rounded-full bg-slate-200" />
        </div>
        <div className="h-8 w-24 rounded-full bg-slate-200" />
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="group relative">
            <div className="h-4 w-24 rounded-full bg-slate-200 mb-2" />
            <div className="h-8 w-20 rounded-full bg-slate-200 mb-1" />
            <div className="h-3 w-32 rounded-full bg-slate-200" />
          </div>
        ))}
      </div>

      {/* Position size skeleton */}
      <div className="p-3 rounded-xl border bg-slate-100/60">
        <div className="h-4 w-28 rounded-full bg-slate-200 mb-2" />
        <div className="h-8 w-24 rounded-full bg-slate-200 mb-1" />
        <div className="h-3 w-40 rounded-full bg-slate-200" />
      </div>

      {/* Confidence row */}
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between border-t pt-3">
        <div className="h-8 w-40 rounded-full bg-slate-200" />
        <div className="h-4 w-48 rounded-full bg-slate-200" />
      </div>

      {/* Rationale skeleton */}
      <div className="mt-3">
        <div className="h-4 w-full rounded-full bg-slate-200 mb-2" />
        <div className="h-4 w-5/6 rounded-full bg-slate-200" />
      </div>
    </section>
  );
}
