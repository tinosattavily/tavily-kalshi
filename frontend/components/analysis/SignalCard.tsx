"use client";

import React from "react";
import clsx from "clsx";

type Signal = {
  // New comprehensive signal fields
  market_prob?: number;
  model_prob?: number;
  edge_pct?: number;
  expected_value_per_dollar?: number;
  kelly_fraction_yes?: number;
  kelly_fraction_no?: number;
  confidence_level?: string;
  confidence_score?: number;
  recommended_action?: string;
  recommended_size_fraction?: number;
  target_take_profit_prob?: number;
  target_stop_loss_prob?: number;
  horizon?: string;
  rationale_short?: string;
  rationale_long?: string;
  // Legacy fields for backward compatibility
  direction?: string;
  model_prob_abs?: number;
  confidence?: string;
  rationale?: string;
};

type ConfidenceLevel = "LOW" | "MEDIUM" | "HIGH";
type RecommendedAction = "buy_yes" | "buy_no" | "reduce_yes" | "reduce_no" | "hold";

function formatPct(x: number | null | undefined, digits = 2): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "–";
  return `${(x * 100).toFixed(digits)}%`;
}

function actionLabel(action: RecommendedAction | string): string {
  const normalized = action.toLowerCase();
  switch (normalized) {
    case "buy_yes": return "BUY YES";
    case "buy_no": return "BUY NO";
    case "reduce_yes": return "REDUCE YES";
    case "reduce_no": return "REDUCE NO";
    case "hold": return "HOLD";
    default: return "HOLD";
  }
}

function actionClasses(action: RecommendedAction | string): string {
  const normalized = action.toLowerCase();
  if (normalized === "buy_yes") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700";
  }
  if (normalized === "buy_no" || normalized === "reduce_yes") {
    return "border-rose-200 bg-rose-50 text-rose-700";
  }
  if (normalized === "reduce_no") {
    return "border-amber-200 bg-amber-50 text-amber-700";
  }
  // hold
  return "border-slate-200 bg-slate-50 text-slate-600";
}

function confidenceClasses(level: string): string {
  const normalized = level.toUpperCase();
  switch (normalized) {
    case "HIGH":
      return "bg-emerald-50 text-emerald-700 border-emerald-200";
    case "MEDIUM":
      return "bg-indigo-50 text-indigo-700 border-indigo-200";
    case "LOW":
    default:
      return "bg-amber-50 text-amber-700 border-amber-200";
  }
}

function normalizeConfidenceLevel(level: string | undefined): ConfidenceLevel {
  if (!level) return "LOW";
  const normalized = level.toUpperCase();
  if (normalized === "HIGH" || normalized === "MEDIUM" || normalized === "LOW") {
    return normalized as ConfidenceLevel;
  }
  return "LOW";
}

function getDecisionColorScheme(action: RecommendedAction | string): {
  bgColor: string;
  borderColor: string;
  shadowColor: string;
  textColor: string;
} {
  const normalized = action.toLowerCase();
  
  if (normalized === "buy_yes") {
    // Buy YES - Green
    return {
      bgColor: "bg-emerald-50/40",
      borderColor: "border-emerald-100/50",
      shadowColor: "rgba(16, 185, 129, 0.2)", // emerald-500 with opacity
      textColor: "text-emerald-700",
    };
  } else if (normalized === "buy_no" || normalized === "reduce_yes") {
    // Buy NO or Reduce YES - Red
    return {
      bgColor: "bg-rose-50/40",
      borderColor: "border-rose-100/50",
      shadowColor: "rgba(244, 63, 94, 0.2)", // rose-500 with opacity
      textColor: "text-rose-700",
    };
  } else if (normalized === "reduce_no") {
    // Reduce NO - Amber
    return {
      bgColor: "bg-amber-50/40",
      borderColor: "border-amber-100/50",
      shadowColor: "rgba(245, 158, 11, 0.2)", // amber-500 with opacity
      textColor: "text-amber-700",
    };
  } else {
    // Hold - Grey
    return {
      bgColor: "bg-slate-50/40",
      borderColor: "border-slate-100/50",
      shadowColor: "rgba(100, 116, 139, 0.2)", // slate-500 with opacity
      textColor: "text-slate-700",
    };
  }
}

export default function SignalCard({ signal }: { signal: Signal }) {
  if (!signal || Object.keys(signal).length === 0) return null;
  
  // Extract and normalize values
  const marketProb = signal.market_prob ?? signal.model_prob_abs ?? 0;
  const modelProb = signal.model_prob ?? signal.model_prob_abs ?? 0;
  const edge = signal.edge_pct ?? 
    (signal.model_prob !== undefined && signal.market_prob !== undefined 
      ? signal.model_prob - signal.market_prob 
      : 0);
  const kellyYes = signal.kelly_fraction_yes ?? 0;
  const confidenceLevel = normalizeConfidenceLevel(signal.confidence_level ?? signal.confidence);
  const confidenceScore = signal.confidence_score ?? 0.5;
  const takeProfit = signal.target_take_profit_prob;
  const stopLoss = signal.target_stop_loss_prob;
  const recommendedAction = (signal.recommended_action ?? "hold").toLowerCase() as RecommendedAction;
  const rationale = signal.rationale_short ?? signal.rationale_long ?? signal.rationale;
  const colorScheme = getDecisionColorScheme(recommendedAction);

  return (
    <section 
      className={clsx(
        "mb-6 rounded-3xl p-8 backdrop-blur-xl flex flex-col gap-4",
        colorScheme.bgColor,
        colorScheme.borderColor,
        "border"
      )}
      style={{ 
        boxShadow: `0 16px 40px ${colorScheme.shadowColor}`,
        WebkitBackdropFilter: "blur(14px)"
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className={clsx("py-2 flex items-center gap-2 text-base uppercase tracking-[0.18em]", colorScheme.textColor)}>
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 16 17" className="currentColor">
              <path fill="currentColor" fillRule="evenodd" d="M8.5 13.984a.499.499 0 0 1-.479-.358L6.647 8.984H4.993a.5.5 0 0 1-.486-.383l-.976-4.052l-1.048 4.06a.501.501 0 0 1-.484.375H0v-.953h1.61l1.452-5.625a.5.5 0 0 1 .484-.375h.004a.5.5 0 0 1 .482.383l1.352 5.617h1.635c.222 0 .417.146.479.358l1.005 3.346l1.02-3.348a.499.499 0 0 1 .479-.356h.687l1.347-2.736a.501.501 0 0 1 .445-.279h.004c.188 0 .359.104.444.271l1.41 2.744h1.63v.953h-1.936a.496.496 0 0 1-.444-.271l-1.095-2.131l-1.047 2.123a.497.497 0 0 1-.447.279h-.626l-1.396 4.644a.497.497 0 0 1-.478.356z"/>
            </svg>
            Signal
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Model vs market probability and sizing.
          </p>
        </div>

        <span
          className={clsx(
            "inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide",
            "shadow-[0_0_0_1px_rgba(15,23,42,0.02)]",
            actionClasses(recommendedAction)
          )}
        >
          {actionLabel(recommendedAction)}
        </span>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <div className="group relative cursor-help">
          <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-slate-500">
            Market Prob
          </p>
          <p className="mt-1 text-lg md:text-xl font-semibold text-slate-900">
            {formatPct(marketProb)}
          </p>
          <p className="mt-0.5 text-[11px] text-slate-500">
            Implied by current YES price
          </p>
          {/* Tooltip */}
          <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-50 w-64">
            <div className="bg-slate-900 text-white text-xs rounded-lg py-2 px-3 shadow-lg">
              <div className="font-semibold mb-1">Market Probability</div>
              <div className="text-slate-300">
                The current probability implied by Kalshi prices. This is what the market believes is the true probability of the YES outcome.
              </div>
              <div className="absolute top-full left-4 w-0 h-0 border-l-[6px] border-r-[6px] border-t-[6px] border-transparent border-t-slate-900"></div>
            </div>
          </div>
        </div>

        <div className="group relative cursor-help">
          <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-slate-500">
            Model Prob
          </p>
          <p className="mt-1 text-lg md:text-xl font-semibold text-slate-900">
            {formatPct(modelProb)}
          </p>
          <p className="mt-0.5 text-[11px] text-slate-500">
            After news & event analysis
          </p>
          {/* Tooltip */}
          <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-50 w-64">
            <div className="bg-slate-900 text-white text-xs rounded-lg py-2 px-3 shadow-lg">
              <div className="font-semibold mb-1">Model Probability</div>
              <div className="text-slate-300">
                Our AI model&apos;s estimate of the true probability after analyzing recent news, market context, and information from Tavily. This is our best guess at what the probability should be.
              </div>
              <div className="absolute top-full left-4 w-0 h-0 border-l-[6px] border-r-[6px] border-t-[6px] border-transparent border-t-slate-900"></div>
            </div>
          </div>
        </div>

        <div className="group relative cursor-help">
          <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-slate-500">
            Edge
          </p>
          <p className={clsx(
            "mt-1 text-lg md:text-xl font-semibold",
            edge >= 0 ? "text-emerald-700" : "text-rose-700"
          )}>
            {formatPct(edge)}
          </p>
          <p className="mt-0.5 text-[11px] text-slate-500">
            Model minus market
          </p>
          {/* Tooltip */}
          <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-50 w-64">
            <div className="bg-slate-900 text-white text-xs rounded-lg py-2 px-3 shadow-lg">
              <div className="font-semibold mb-1">Edge</div>
              <div className="text-slate-300">
                The difference between our model&apos;s probability and the market&apos;s probability. A positive edge means we think the market is underpricing YES; negative means it&apos;s overpricing. This represents our expected advantage.
              </div>
              {signal.expected_value_per_dollar !== undefined && signal.expected_value_per_dollar !== edge && (
                <div className="mt-2 pt-2 border-t border-slate-700">
                  <div className="font-semibold mb-1">Expected Value</div>
                  <div className="text-slate-300">
                    The expected profit per dollar invested in a $1 binary contract. For a $1 bet, this equals the edge in probability points.
                  </div>
                </div>
              )}
              <div className="absolute top-full left-4 w-0 h-0 border-l-[6px] border-r-[6px] border-t-[6px] border-transparent border-t-slate-900"></div>
            </div>
          </div>
        </div>

        <div className="group relative cursor-help">
          <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-slate-500">
            Kelly Yes
          </p>
          <p className="mt-1 text-lg md:text-xl font-semibold text-slate-900">
            {formatPct(kellyYes)}
          </p>
          <p className="mt-0.5 text-[11px] text-slate-500">
            Theoretical optimal allocation
          </p>
          {/* Tooltip */}
          <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-50 w-64">
            <div className="bg-slate-900 text-white text-xs rounded-lg py-2 px-3 shadow-lg">
              <div className="font-semibold mb-1">Kelly Fraction (YES)</div>
              <div className="text-slate-300">
                The theoretical optimal fraction of your bankroll to bet on YES according to the Kelly Criterion. This is the raw calculation before applying risk management constraints. A value of 0.20 means the Kelly formula suggests betting 20% of your capital.
              </div>
              <div className="absolute top-full left-4 w-0 h-0 border-l-[6px] border-r-[6px] border-t-[6px] border-transparent border-t-slate-900"></div>
            </div>
          </div>
        </div>
      </div>

      {/* Position Size - the actual recommended allocation */}
      {signal.recommended_size_fraction !== undefined && signal.recommended_size_fraction > 0 && (
        <div className="group relative cursor-help">
          <div className={clsx("p-3 rounded-xl border backdrop-blur-sm", colorScheme.bgColor.replace("/40", "/60"), colorScheme.borderColor.replace("/50", "/40"))}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-slate-500">
                  Position Size
                </p>
                <p className="mt-1 text-lg md:text-xl font-semibold text-emerald-700">
                  {formatPct(signal.recommended_size_fraction)}
                </p>
                <p className="mt-0.5 text-[11px] text-slate-500">
                  Recommended allocation after risk limits
                </p>
              </div>
            </div>
          </div>
          {/* Tooltip */}
          <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-50 w-64">
            <div className="bg-slate-900 text-white text-xs rounded-lg py-2 px-3 shadow-lg">
              <div className="font-semibold mb-1">Position Size</div>
              <div className="text-slate-300">
                The actual recommended fraction of your capital to allocate to this trade. This is the Kelly fraction after applying risk management constraints (Kelly cap and max capital limits). This is the practical position size you should use, not the raw Kelly value.
              </div>
              <div className="absolute top-full left-4 w-0 h-0 border-l-[6px] border-r-[6px] border-t-[6px] border-transparent border-t-slate-900"></div>
            </div>
          </div>
        </div>
      )}

      {/* Confidence + TP/SL row */}
      <div className={clsx("flex flex-col gap-2 md:flex-row md:items-center md:justify-between border-t pt-3", colorScheme.borderColor.replace("/50", "/30"))}>
        <div className="flex items-center gap-2">
          <span
            className={clsx(
              "inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-medium",
              confidenceClasses(confidenceLevel)
            )}
          >
            <span className="mr-1 inline-block h-2 w-2 rounded-full bg-current" />
            Confidence: {confidenceLevel} ({(confidenceScore * 100).toFixed(0)}%)
          </span>
        </div>

        <p className="text-[11px] text-slate-500">
          {takeProfit != null && (
            <>
              <span className="font-medium text-slate-700">Take Profit:</span>{" "}
              {formatPct(takeProfit)}
            </>
          )}
          {takeProfit != null && stopLoss != null && <span className="mx-2">•</span>}
          {stopLoss != null && (
            <>
              <span className="font-medium text-slate-700">Stop Loss:</span>{" "}
              {formatPct(stopLoss)}
            </>
          )}
        </p>
      </div>

      {/* Rationale */}
      {rationale && (
        <p className="mt-3 text-sm leading-relaxed text-slate-600 italic">
          {rationale}
        </p>
      )}
    </section>
  );
}
