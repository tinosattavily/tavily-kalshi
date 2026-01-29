"use client";

import React from "react";

export function NewsSkeleton(): React.JSX.Element {
  return (
    <div className="relative">
      {/* Tab header skeleton */}
      <div className="flex gap-2 mb-4 border-b border-indigo-200/50">
        <div className="h-10 w-24 rounded-t-lg bg-slate-200 animate-pulse" />
        <div className="h-10 w-24 rounded-t-lg bg-slate-100 animate-pulse" />
      </div>

      {/* Card skeleton */}
      <div className="rounded-3xl bg-indigo-50/40 p-8 shadow-[0_16px_40px_rgba(99,102,241,0.2)] backdrop-blur-xl border border-indigo-100/50 animate-pulse">
        {/* Header */}
        <div className="flex items-center justify-between gap-3 mb-4">
          <div className="h-6 w-48 rounded-full bg-slate-200" />
          <div className="h-6 w-24 rounded-full bg-slate-200" />
        </div>

        {/* News items skeleton */}
        <div className="flex flex-col gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="rounded-2xl bg-white/60 px-6 py-5 shadow-sm">
              <div className="flex items-center justify-between gap-2 mb-2">
                <div className="h-4 w-32 rounded-full bg-slate-200" />
                <div className="h-4 w-20 rounded-full bg-slate-200" />
                <div className="h-5 w-16 rounded-full bg-slate-200" />
              </div>
              <div className="h-5 w-full rounded-full bg-slate-200 mb-2" />
              <div className="h-4 w-3/4 rounded-full bg-slate-200" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
