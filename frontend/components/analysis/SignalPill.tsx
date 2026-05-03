import type { Signal } from "../../types/signal";

type Size = "sm" | "lg";

type Props = {
  signal: Signal | null | undefined;
  size?: Size;
};

const ACTION_LABELS: Record<string, string> = {
  BUY_YES: "BUY YES",
  BUY_NO: "BUY NO",
  HOLD: "HOLD",
  REDUCE: "REDUCE",
  SELL: "SELL",
  PASS: "PASS",
};

function pickAction(signal: Signal): string {
  const raw = signal.recommended_action ?? signal.direction ?? "HOLD";
  const key = String(raw).toUpperCase().replace(/\s+/g, "_");
  return ACTION_LABELS[key] ?? String(raw).toUpperCase();
}

function pickEdgePercent(signal: Signal): number | null {
  if (typeof signal.edge_pct === "number") return Math.round(signal.edge_pct * 100);
  if (typeof signal.model_prob === "number" && typeof signal.market_prob === "number") {
    return Math.round((signal.model_prob - signal.market_prob) * 100);
  }
  return null;
}

export default function SignalPill({ signal, size = "sm" }: Props) {
  if (!signal) return null;

  const action = pickAction(signal);
  const edge = pickEdgePercent(signal);

  const tone =
    action === "BUY YES"
      ? "var(--yes)"
      : action === "BUY NO"
        ? "var(--no)"
        : "var(--ink-soft)";

  const big = size === "lg";

  return (
    <div
      className={
        "inline-flex items-center rounded-full bg-glass-strong shadow-neu-raised border border-ring " +
        (big ? "gap-3 px-3 py-2" : "gap-2 px-2.5 py-1.5")
      }
    >
      <span
        className={big ? "w-2.5 h-2.5 rounded-full" : "w-2 h-2 rounded-full"}
        style={{ background: tone, boxShadow: `0 0 12px ${tone}` }}
      />
      <span
        className="font-mono font-semibold uppercase"
        style={{ color: tone, fontSize: big ? 12 : 10, letterSpacing: 1.2 }}
      >
        {action}
      </span>
      {edge !== null && (
        <>
          <span className={big ? "w-px h-3.5 bg-line" : "w-px h-2.5 bg-line"} />
          <span
            className="font-mono text-ink-soft"
            style={{ fontSize: big ? 11 : 10 }}
          >
            EDGE{" "}
            <span className="text-ink font-semibold">
              {edge > 0 ? "+" : ""}
              {edge}%
            </span>
          </span>
        </>
      )}
    </div>
  );
}
