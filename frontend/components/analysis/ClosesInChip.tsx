"use client";

import { Clock } from "lucide-react";
import { useEffect, useState } from "react";
/* globals setInterval, clearInterval */

type Props = {
  closeTime: string | null | undefined;
};

const HOUR_MS = 60 * 60 * 1000;
const TICK_MS = 30 * 1000;

function format(diff: number): string {
  if (diff <= 0) return "Closed";
  const totalMin = Math.floor(diff / 60_000);
  const h = Math.floor(totalMin / 60);
  const m = totalMin % 60;
  if (h > 0) return `Closes in ${h}h ${m}m`;
  return `Closes in ${m}m`;
}

export default function ClosesInChip({ closeTime }: Props) {
  const [, force] = useState(0);

  useEffect(() => {
    const id = setInterval(() => force((n) => n + 1), TICK_MS);
    return () => clearInterval(id);
  }, []);

  if (!closeTime) return null;
  const target = Date.parse(closeTime);
  if (!Number.isFinite(target)) return null;

  const diff = target - Date.now();
  const danger = diff > 0 && diff < HOUR_MS;
  const closed = diff <= 0;

  return (
    <span
      className="inline-flex items-center gap-1.5 font-mono uppercase font-semibold"
      style={{
        fontSize: 10,
        color: danger || closed ? "var(--no)" : "var(--ink-mute)",
        letterSpacing: 0.6,
      }}
    >
      <Clock size={11} />
      {format(diff)}
    </span>
  );
}
