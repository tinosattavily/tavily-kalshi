"use client";

import React from "react";

type EventContext = {
  title?: string;
  image?: string;
};

type StructuredReport = {
  headline?: string;
  thesis?: string;
  bull_case?: string[];
  bear_case?: string[];
  key_risks?: string[];
  execution_notes?: string;
  // Legacy fields
  title?: string;
  markdown?: string;
};

type Report = string | StructuredReport | Record<string, unknown>;

function isStructuredReport(report: Report): report is StructuredReport {
  return (
    typeof report === "object" &&
    report !== null &&
    ("headline" in report || "thesis" in report || "bull_case" in report || "execution_notes" in report)
  );
}

export default function ReportCard({
  report,
  eventContext,
}: {
  report: Report;
  eventContext?: EventContext | null;
}) {
  const structured = isStructuredReport(report) ? report : null;
  const hasStructuredData = structured && (
    structured.headline || 
    structured.thesis || 
    (structured.bull_case && structured.bull_case.length > 0) ||
    (structured.bear_case && structured.bear_case.length > 0) ||
    (structured.key_risks && structured.key_risks.length > 0) ||
    structured.execution_notes
  );

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

      {hasStructuredData ? (
        <div className="flex flex-col gap-6">
          {/* Headline */}
          {structured.headline && (
            <div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">
                {structured.headline}
              </h3>
            </div>
          )}

          {/* Thesis */}
          {structured.thesis && (
            <div>
              <h4 className="text-sm font-semibold uppercase tracking-[0.1em] text-slate-600 mb-2">
                Thesis
              </h4>
              <p className="text-sm leading-relaxed text-slate-700">
                {structured.thesis}
              </p>
            </div>
          )}

          {/* Bull Case & Bear Case Side by Side */}
          {(structured.bull_case?.length || structured.bear_case?.length) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Bull Case */}
              {structured.bull_case && structured.bull_case.length > 0 && (
                <div className="rounded-xl bg-emerald-50/60 border border-emerald-100/50 p-4">
                  <h4 className="text-sm font-semibold uppercase tracking-[0.1em] text-emerald-700 mb-3">
                    Bull Case
                  </h4>
                  <ul className="space-y-2">
                    {structured.bull_case.map((point, idx) => (
                      <li key={idx} className="text-sm text-emerald-800 flex items-start gap-2">
                        <span className="text-emerald-500 mt-1">•</span>
                        <span>{point}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Bear Case */}
              {structured.bear_case && structured.bear_case.length > 0 && (
                <div className="rounded-xl bg-rose-50/60 border border-rose-100/50 p-4">
                  <h4 className="text-sm font-semibold uppercase tracking-[0.1em] text-rose-700 mb-3">
                    Bear Case
                  </h4>
                  <ul className="space-y-2">
                    {structured.bear_case.map((point, idx) => (
                      <li key={idx} className="text-sm text-rose-800 flex items-start gap-2">
                        <span className="text-rose-500 mt-1">•</span>
                        <span>{point}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Key Risks */}
          {structured.key_risks && structured.key_risks.length > 0 && (
            <div className="rounded-xl bg-amber-50/60 border border-amber-100/50 p-4">
              <h4 className="text-sm font-semibold uppercase tracking-[0.1em] text-amber-700 mb-3">
                Key Risks
              </h4>
              <ul className="space-y-2">
                {structured.key_risks.map((risk, idx) => (
                  <li key={idx} className="text-sm text-amber-800 flex items-start gap-2">
                    <span className="text-amber-500 mt-1">•</span>
                    <span>{risk}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Execution Notes */}
          {structured.execution_notes && (
            <div className="border-t border-slate-200/50 pt-4">
              <h4 className="text-sm font-semibold uppercase tracking-[0.1em] text-slate-600 mb-2">
                Execution Notes
              </h4>
              <p className="text-sm leading-relaxed text-slate-700">
                {structured.execution_notes}
              </p>
            </div>
          )}
        </div>
      ) : (
        /* Fallback to legacy markdown rendering */
        <div className="text-sm text-slate-700">
          {typeof report === "object" && "markdown" in report && report.markdown ? (
            <div className="whitespace-pre-wrap">{String(report.markdown)}</div>
          ) : typeof report === "string" ? (
            <div className="whitespace-pre-wrap">{report}</div>
          ) : (
            <div className="whitespace-pre-wrap font-mono text-xs">
              {JSON.stringify(report, null, 2)}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
