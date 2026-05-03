"use client";

type Kind = "bullish" | "bearish" | "neutral";

const MAP: Record<Kind, { color: string }> = {
  bullish: { color: "var(--yes)" },
  bearish: { color: "var(--no)" },
  neutral: { color: "var(--ink-mute)" },
};

export default function Sentiment({ kind }: { kind: Kind }) {
  const { color } = MAP[kind];
  return (
    <span
      className="inline-flex items-center gap-1.5 font-mono uppercase"
      style={{ fontSize: 10, letterSpacing: 0.6, color }}
    >
      <span className="rounded-full" style={{ width: 6, height: 6, background: color }} />
      {kind}
    </span>
  );
}
