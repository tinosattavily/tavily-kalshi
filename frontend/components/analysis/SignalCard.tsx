"use client";

import React from "react";

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

function actionTone(action: RecommendedAction | string): string {
  const n = action.toLowerCase();
  if (n === "buy_yes") return "var(--yes)";
  if (n === "buy_no" || n === "reduce_yes") return "var(--no)";
  if (n === "reduce_no") return "var(--accent)";
  return "var(--ink-soft)";
}

function confidenceTone(level: string): string {
  const n = level.toUpperCase();
  if (n === "HIGH") return "var(--yes)";
  if (n === "MEDIUM") return "var(--accent)";
  return "var(--ink-mute)";
}

function normalizeConfidenceLevel(level: string | undefined): ConfidenceLevel {
  if (!level) return "LOW";
  const normalized = level.toUpperCase();
  if (normalized === "HIGH" || normalized === "MEDIUM" || normalized === "LOW") {
    return normalized as ConfidenceLevel;
  }
  return "LOW";
}

function Metric({
  label,
  value,
  hint,
  color,
}: {
  label: string;
  value: string;
  hint?: string;
  color?: string;
}) {
  return (
    <div className="flex flex-col gap-1">
      <p
        className="font-mono uppercase text-ink-mute"
        style={{ fontSize: 10, letterSpacing: 1.4 }}
      >
        {label}
      </p>
      <p
        className="font-mono font-semibold leading-tight"
        style={{ fontSize: 18, color: color ?? "var(--ink)", letterSpacing: "-0.01em" }}
      >
        {value}
      </p>
      {hint ? (
        <p className="text-[11px] text-ink-mute leading-snug">{hint}</p>
      ) : null}
    </div>
  );
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
  const tone = actionTone(recommendedAction);
  const confTone = confidenceTone(confidenceLevel);
  const edgeColor = edge >= 0 ? "var(--yes)" : "var(--no)";

  return (
    <section
      id="signal-card"
      className="relative overflow-hidden rounded-lg p-5 bg-glass border border-ring shadow-soft backdrop-blur-glass mb-3.5"
    >
      <div
        className="absolute inset-0 rounded-lg pointer-events-none"
        style={{ boxShadow: "inset 0 1px 0 var(--highlight)" }}
      />

      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <p
            className="font-mono uppercase text-ink-mute"
            style={{ fontSize: 10, letterSpacing: 1.4 }}
          >
            SIGNAL
          </p>
          <p className="text-[11px] text-ink-mute mt-0.5">
            Model vs market probability and sizing.
          </p>
        </div>

        <span
          className="inline-flex items-center rounded-full bg-glass-strong shadow-neu-raised border border-ring font-mono font-semibold uppercase"
          style={{
            color: tone,
            fontSize: 10,
            letterSpacing: 1.2,
            padding: "4px 10px",
          }}
        >
          <span
            className="rounded-full mr-1.5"
            style={{ width: 6, height: 6, background: tone, boxShadow: `0 0 6px ${tone}` }}
          />
          {actionLabel(recommendedAction)}
        </span>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Metric
          label="MARKET PROB"
          value={formatPct(marketProb)}
          hint="Implied by current YES price"
        />
        <Metric
          label="MODEL PROB"
          value={formatPct(modelProb)}
          hint="After news & event analysis"
        />
        <Metric
          label="EDGE"
          value={formatPct(edge)}
          hint="Model minus market"
          color={edgeColor}
        />
        <Metric
          label="KELLY YES"
          value={formatPct(kellyYes)}
          hint="Theoretical optimal allocation"
        />
      </div>

      {/* Position size (when present) */}
      {signal.recommended_size_fraction !== undefined &&
        signal.recommended_size_fraction > 0 && (
          <div
            className="mt-3 rounded p-3 bg-glass-strong border border-ring shadow-neu-inset flex items-center justify-between"
          >
            <div>
              <p
                className="font-mono uppercase text-ink-mute"
                style={{ fontSize: 10, letterSpacing: 1.4 }}
              >
                POSITION SIZE
              </p>
              <p
                className="font-mono font-semibold leading-tight mt-0.5"
                style={{ fontSize: 18, color: "var(--accent)", letterSpacing: "-0.01em" }}
              >
                {formatPct(signal.recommended_size_fraction)}
              </p>
            </div>
            <p className="text-[11px] text-ink-mute leading-snug max-w-[180px] text-right">
              Recommended allocation after risk limits
            </p>
          </div>
        )}

      {/* Confidence + TP/SL row */}
      <div className="mt-3 pt-3 border-t border-line flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-2">
          <span
            className="inline-flex items-center rounded-full bg-glass-strong shadow-neu-raised border border-ring font-mono font-semibold uppercase"
            style={{
              color: confTone,
              fontSize: 10,
              letterSpacing: 1.2,
              padding: "3px 9px",
            }}
          >
            <span
              className="rounded-full mr-1.5"
              style={{ width: 6, height: 6, background: confTone }}
            />
            CONFIDENCE: {confidenceLevel} ({(confidenceScore * 100).toFixed(0)}%)
          </span>
        </div>

        {(takeProfit != null || stopLoss != null) && (
          <p className="font-mono text-[11px] text-ink-mute">
            {takeProfit != null && (
              <>
                <span className="text-ink-soft font-semibold">Take Profit:</span>{" "}
                <span className="text-ink-soft">{formatPct(takeProfit)}</span>
              </>
            )}
            {takeProfit != null && stopLoss != null && (
              <span className="mx-2 text-ink-mute">•</span>
            )}
            {stopLoss != null && (
              <>
                <span className="text-ink-soft font-semibold">Stop Loss:</span>{" "}
                <span className="text-ink-soft">{formatPct(stopLoss)}</span>
              </>
            )}
          </p>
        )}
      </div>

      {/* Rationale */}
      {rationale && (
        <p className="mt-3 text-[12.5px] leading-relaxed text-ink-soft italic">
          {rationale}
        </p>
      )}
    </section>
  );
}
