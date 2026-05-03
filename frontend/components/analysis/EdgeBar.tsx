type Props = {
  marketProb: number; // 0..1
  modelProb: number;  // 0..1
};

function clamp01(x: number): number {
  if (Number.isNaN(x)) return 0;
  return Math.max(0, Math.min(1, x));
}

export default function EdgeBar({ marketProb, modelProb }: Props) {
  const m = clamp01(marketProb);
  const p = clamp01(modelProb);
  const negative = p < m;
  const left = Math.min(m, p) * 100;
  const right = Math.max(m, p) * 100;
  const fillColor = negative ? "var(--no)" : "var(--accent)";

  return (
    <div className="grid items-center gap-3" style={{ gridTemplateColumns: "60px 1fr 60px" }}>
      <span className="font-mono text-[10px] text-ink-mute text-right">
        MARKET {Math.round(m * 100)}%
      </span>
      <div className="relative h-1.5 rounded bg-neu-track shadow-neu-inset">
        <div
          className="absolute inset-y-0 rounded"
          style={{ left: `${left}%`, width: `${right - left}%`, background: fillColor }}
        />
        <div
          className="absolute"
          style={{
            left: `${p * 100}%`,
            top: -3,
            width: 2,
            height: 12,
            background: "var(--ink)",
            borderRadius: 1,
          }}
        />
      </div>
      <span className="font-mono text-[10px] font-semibold text-accent">
        MODEL {Math.round(p * 100)}%
      </span>
    </div>
  );
}
