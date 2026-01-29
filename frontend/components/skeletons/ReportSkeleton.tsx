"use client";

import React from "react";

export function ReportSkeleton(): React.JSX.Element {
  return (
    <section className="mb-6 rounded-3xl border border-slate-100/50 bg-slate-50/40 backdrop-blur-xl p-8 shadow-[0_16px_40px_rgba(100,116,139,0.2)] animate-pulse">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-6">
        <div>
          <div className="h-6 w-40 rounded-full bg-slate-200 mb-2" />
          <div className="h-4 w-56 rounded-full bg-slate-200" />
        </div>
        <div className="h-15 w-15 rounded-lg bg-slate-200" />
      </div>

      {/* Content skeleton */}
      <div className="flex flex-col gap-6">
        {/* Headline */}
        <div className="h-6 w-3/4 rounded-full bg-slate-200" />

        {/* Thesis */}
        <div>
          <div className="h-4 w-20 rounded-full bg-slate-200 mb-2" />
          <div className="h-4 w-full rounded-full bg-slate-200 mb-2" />
          <div className="h-4 w-5/6 rounded-full bg-slate-200" />
        </div>

        {/* Bull/Bear cases */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="rounded-xl bg-slate-100/60 border border-slate-200/50 p-4">
            <div className="h-4 w-24 rounded-full bg-slate-200 mb-3" />
            <div className="space-y-2">
              <div className="h-4 w-full rounded-full bg-slate-200" />
              <div className="h-4 w-5/6 rounded-full bg-slate-200" />
            </div>
          </div>
          <div className="rounded-xl bg-slate-100/60 border border-slate-200/50 p-4">
            <div className="h-4 w-24 rounded-full bg-slate-200 mb-3" />
            <div className="space-y-2">
              <div className="h-4 w-full rounded-full bg-slate-200" />
              <div className="h-4 w-5/6 rounded-full bg-slate-200" />
            </div>
          </div>
        </div>

        {/* Key risks */}
        <div className="rounded-xl bg-slate-100/60 border border-slate-200/50 p-4">
          <div className="h-4 w-28 rounded-full bg-slate-200 mb-3" />
          <div className="space-y-2">
            <div className="h-4 w-full rounded-full bg-slate-200" />
            <div className="h-4 w-4/5 rounded-full bg-slate-200" />
          </div>
        </div>
      </div>
    </section>
  );
}
