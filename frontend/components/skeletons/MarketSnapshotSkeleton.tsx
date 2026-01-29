"use client";

import React from "react";

export function MarketSnapshotSkeleton(): React.JSX.Element {
  return (
    <div
      className="rounded-3xl bg-white/30 p-6 shadow-[0_18px_45px_rgba(30,58,138,0.25)] backdrop-blur-[12px] overflow-visible animate-pulse"
      style={{ WebkitBackdropFilter: "blur(12px)" }}
    >
      {/* Header skeleton */}
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="h-3 w-28 rounded-full bg-slate-200 mb-3" />
          <div className="h-6 w-64 rounded-full bg-slate-200 mb-4" />
          <div className="h-4 w-48 rounded-full bg-slate-200" />
        </div>
        <div className="h-8 w-32 rounded-full bg-slate-200" />
      </div>

      {/* Grid skeleton */}
      <div className="grid gap-3 text-xs sm:grid-cols-[1fr_1fr_auto]">
        {/* YES/NO tiles */}
        <div className="h-32 rounded-2xl bg-slate-200" />
        <div className="h-32 rounded-2xl bg-slate-100" />
        
        {/* Metrics column */}
        <div className="flex flex-col w-fit">
          <div className="h-16 rounded-xl bg-slate-200 mb-2" />
          <div className="h-16 rounded-xl bg-slate-200 mb-2" />
          <div className="h-16 rounded-xl bg-slate-200" />
        </div>

        {/* Order book skeleton */}
        <div className="h-24 rounded-2xl bg-slate-100" />
        
        {/* Comments skeleton */}
        <div className="h-24 rounded-2xl bg-slate-100" />
        
        {/* Empty cell */}
        <div></div>
      </div>

      {/* Footer skeleton */}
      <div className="mt-3 flex items-center justify-between">
        <div className="h-6 w-24 rounded-full bg-slate-200" />
        <div className="h-8 w-32 rounded-lg bg-slate-200" />
      </div>
    </div>
  );
}
