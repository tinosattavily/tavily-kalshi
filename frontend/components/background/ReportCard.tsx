"use client";

import React from "react";

interface EventContext {
  title?: string;
  image?: string;
}

interface StructuredReport {
  headline?: string;
  thesis?: string;
  bull_case?: string[];
  bear_case?: string[];
  key_risks?: string[];
  execution_notes?: string;
  title?: string;
  markdown?: string;
}

type Report = string | StructuredReport | Record<string, unknown>;

interface ReportCardProps {
  report: Report;
  eventContext?: EventContext | null;
}

function isStructuredReport(report: Report): report is StructuredReport {
  if (typeof report !== "object" || report === null) return false;
  return "headline" in report || "thesis" in report || "bull_case" in report || "execution_notes" in report;
}

function hasStructuredContent(report: StructuredReport): boolean {
  return Boolean(
    report.headline ||
      report.thesis ||
      (report.bull_case && report.bull_case.length > 0) ||
      (report.bear_case && report.bear_case.length > 0) ||
      (report.key_risks && report.key_risks.length > 0) ||
      report.execution_notes,
  );
}

interface BulletListProps {
  items: string[];
  title: string;
  bgColor: string;
  borderColor: string;
  titleColor: string;
  textColor: string;
  bulletColor: string;
}

function BulletList({
  items,
  title,
  bgColor,
  borderColor,
  titleColor,
  textColor,
  bulletColor,
}: BulletListProps): React.JSX.Element {
  return (
    <div className={`rounded-xl ${bgColor} border ${borderColor} p-4`}>
      <h4 className={`text-sm font-semibold uppercase tracking-[0.1em] ${titleColor} mb-3`}>{title}</h4>
      <ul className="space-y-2">
        {items.map((item, idx) => (
          <li key={idx} className={`text-sm ${textColor} flex items-start gap-2`}>
            <span className={`${bulletColor} mt-1`}>•</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function ReportCard({ report, eventContext }: ReportCardProps): React.JSX.Element {
  const structured = isStructuredReport(report) ? report : null;
  const showStructured = structured && hasStructuredContent(structured);

  return (
    <section className="mb-6 rounded-3xl border border-slate-100/50 bg-slate-50/40 backdrop-blur-xl p-8 shadow-[0_16px_40px_rgba(100,116,139,0.2)]">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-6">
        <div>
          <p className="py-2 flex items-center gap-2 text-base uppercase tracking-[0.18em] text-slate-700">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-slate-700">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
            Report & Thesis
          </p>
          <p className="mt-1 text-xs text-slate-500">
            AI-generated analysis and trade rationale.
          </p>
        </div>
        {eventContext?.image && (
          <div className="flex-shrink-0">
            <img
              src={eventContext.image}
              alt={eventContext.title || "Event image"}
              width={60}
              height={60}
              className="rounded-lg object-cover border border-slate-200 w-15 h-15 bg-slate-100"
              onError={(e) => {
                e.currentTarget.style.display = "none";
              }}
            />
          </div>
        )}
      </div>

      {showStructured && structured ? (
        <div className="flex flex-col gap-6">
          {structured.headline && (
            <h3 className="text-lg font-semibold text-slate-900 mb-2">{structured.headline}</h3>
          )}

          {structured.thesis && (
            <div>
              <h4 className="text-sm font-semibold uppercase tracking-[0.1em] text-slate-600 mb-2">
                Thesis
              </h4>
              <p className="text-sm leading-relaxed text-slate-700">{structured.thesis}</p>
            </div>
          )}

          {(structured.bull_case?.length || structured.bear_case?.length) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {structured.bull_case && structured.bull_case.length > 0 && (
                <BulletList
                  items={structured.bull_case}
                  title="Bull Case"
                  bgColor="bg-emerald-50/60"
                  borderColor="border-emerald-100/50"
                  titleColor="text-emerald-900"
                  textColor="text-emerald-900"
                  bulletColor="text-emerald-900"
                />
              )}
              {structured.bear_case && structured.bear_case.length > 0 && (
                <BulletList
                  items={structured.bear_case}
                  title="Bear Case"
                  bgColor="bg-rose-50/60"
                  borderColor="border-rose-100/50"
                  titleColor="text-rose-900"
                  textColor="text-rose-900"
                  bulletColor="text-rose-900"
                />
              )}
            </div>
          )}

          {structured.key_risks && structured.key_risks.length > 0 && (
            <BulletList
              items={structured.key_risks}
              title="Key Risks"
              bgColor="bg-amber-50/60"
              borderColor="border-amber-100/50"
              titleColor="text-amber-700"
              textColor="text-amber-800"
              bulletColor="text-amber-500"
            />
          )}

          {structured.execution_notes && (
            <div className="border-t border-slate-200/50 pt-4">
              <h4 className="text-sm font-semibold uppercase tracking-[0.1em] text-slate-600 mb-2">
                Execution Notes
              </h4>
              <p className="text-sm leading-relaxed text-slate-700">{structured.execution_notes}</p>
            </div>
          )}
        </div>
      ) : (
        <div className="text-sm text-slate-700">
          {typeof report === "object" && "markdown" in report && report.markdown ? (
            <div className="whitespace-pre-wrap">{String(report.markdown)}</div>
          ) : typeof report === "string" ? (
            <div className="whitespace-pre-wrap">{report}</div>
          ) : (
            <div className="whitespace-pre-wrap font-mono text-xs">{JSON.stringify(report, null, 2)}</div>
          )}
        </div>
      )}
    </section>
  );
}
