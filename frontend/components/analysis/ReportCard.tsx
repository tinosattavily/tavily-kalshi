"use client";

import EdgeBar from "./EdgeBar";
import SignalPill from "./SignalPill";
import { Sparkles } from "lucide-react";
import type { Signal } from "../../types/signal";
import type { EventContext, Report } from "../../types";

type Props = {
  report: Report;
  eventContext?: EventContext | null;
  signal?: Signal | null;
};

type StructuredReportShape = {
  headline?: string;
  thesis?: string;
  bull_case?: string[];
  bear_case?: string[];
  key_risks?: string[];
  execution_notes?: string[];
};

function isStructured(r: Report): r is StructuredReportShape {
  return typeof r === "object" && r !== null && !Array.isArray(r);
}

/** Defensive normalizer: coerce any backend shape into string[]. */
function toStringArray(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.filter((v): v is string => typeof v === "string" && v.trim().length > 0);
  }
  if (typeof value === "string" && value.trim().length > 0) {
    // Split a paragraph/markdown blob into bullet-able lines.
    const lines = value
      .split(/\r?\n/)
      .map((l) => l.replace(/^\s*[-*•]\s*/, "").trim())
      .filter((l) => l.length > 0);
    return lines.length > 0 ? lines : [value.trim()];
  }
  return [];
}

function CaseCard({
  title,
  items,
  color,
  softBg,
}: {
  title: string;
  items: string[];
  color: string;
  softBg: string;
}) {
  if (!items?.length) return null;
  return (
    <div
      className="relative overflow-hidden rounded p-4 border"
      style={{ background: softBg, borderColor: `${color}22` }}
    >
      <div
        className="absolute top-0 left-0 right-0"
        style={{ height: 2, background: color, opacity: 0.5 }}
      />
      <div
        className="font-mono uppercase font-bold mb-2.5"
        style={{ color, fontSize: 10, letterSpacing: 1.4 }}
      >
        {title}
      </div>
      <ul className="m-0 p-0 list-none flex flex-col gap-1.5">
        {items.map((it, i) => (
          <li
            key={i}
            className="text-[12.5px] leading-relaxed text-ink-soft relative pl-3.5"
          >
            <span
              className="absolute left-0 rounded-full"
              style={{ top: 8, width: 4, height: 4, background: color }}
            />
            {it}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function ReportCard({ report, eventContext: _eventContext, signal }: Props) {
  if (!isStructured(report)) {
    return (
      <div className="rounded p-5 bg-glass border border-ring shadow-soft backdrop-blur-glass">
        <div className="text-[13.5px] leading-relaxed text-ink-soft">
          {typeof report === "string" ? report : "No structured report available."}
        </div>
      </div>
    );
  }

  const headline = typeof report.headline === "string" ? report.headline : undefined;
  const thesis = typeof report.thesis === "string" ? report.thesis : undefined;
  const bull = toStringArray(report.bull_case);
  const bear = toStringArray(report.bear_case);
  const risks = toStringArray(report.key_risks);
  const exec = toStringArray(report.execution_notes);

  const marketP = signal?.market_prob ?? 0;
  const modelP = signal?.model_prob ?? 0;

  return (
    <div className="flex flex-col gap-3.5">
      {/* Signal hero */}
      <div className="relative overflow-hidden rounded-lg p-5 bg-glass-strong border border-ring shadow-soft backdrop-blur-glass">
        <div
          className="absolute inset-0 rounded-lg pointer-events-none"
          style={{ boxShadow: "inset 0 1px 0 var(--highlight)" }}
        />
        <div className="flex items-center gap-2.5 mb-2.5">
          <Sparkles size={13} />
          <span className="font-mono uppercase text-ink-mute" style={{ fontSize: 10, letterSpacing: 1.4 }}>
            MODEL OUTPUT
          </span>
        </div>
        <div className="grid items-end gap-5" style={{ gridTemplateColumns: "1fr auto" }}>
          <div className="text-[28px] font-semibold leading-tight text-ink" style={{ letterSpacing: "-0.02em" }}>
            {headline ?? "Awaiting model output."}
          </div>
          <SignalPill signal={signal ?? null} size="lg" />
        </div>
        {signal && (
          <div className="mt-4">
            <EdgeBar marketProb={marketP} modelProb={modelP} />
          </div>
        )}
      </div>

      {/* Thesis */}
      {thesis && (
        <div className="rounded-lg p-5 bg-glass border border-ring shadow-soft backdrop-blur-glass">
          <div className="font-mono uppercase text-ink-mute mb-2" style={{ fontSize: 10, letterSpacing: 1.4 }}>
            THESIS
          </div>
          <div className="text-[13.5px] leading-relaxed text-ink-soft">{thesis}</div>
        </div>
      )}

      {/* Bull / Bear */}
      {(bull.length > 0 || bear.length > 0) && (
        <div className="grid grid-cols-2 gap-3">
          <CaseCard title="BULL CASE" items={bull} color="var(--yes)" softBg="var(--yes-soft)" />
          <CaseCard title="BEAR CASE" items={bear} color="var(--no)" softBg="var(--no-soft)" />
        </div>
      )}

      {/* Risks */}
      {risks.length > 0 && (
        <CaseCard title="KEY RISKS" items={risks} color="var(--ink-soft)" softBg="var(--glass-strong)" />
      )}

      {/* Execution Notes (preserved per Q1 — keep all live-app features) */}
      {exec.length > 0 && (
        <CaseCard title="EXECUTION NOTES" items={exec} color="var(--accent)" softBg="var(--glass-strong)" />
      )}
    </div>
  );
}
