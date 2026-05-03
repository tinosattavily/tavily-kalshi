"use client";

import { ChevronDown } from "lucide-react";

type Sibling = {
  marketId: string;
  name: string;
};

type VenueMeta = {
  name: string;
  favicon: string;
};

const VENUE_META: Record<"polymarket" | "kalshi", VenueMeta> = {
  polymarket: { name: "Polymarket", favicon: "https://polymarket.com/favicon.ico" },
  kalshi: { name: "Kalshi", favicon: "https://kalshi.com/favicon.ico" },
};

type Props = {
  current: Sibling;
  siblings: Sibling[];
  venue: "polymarket" | "kalshi";
  venueUrl: string;
  open: boolean;
  onToggle: () => void;
  onPick: (marketId: string) => void;
};

export default function MarketPickerChip({
  current,
  siblings,
  venue,
  venueUrl,
  open,
  onToggle,
  onPick,
}: Props) {
  const meta = VENUE_META[venue];
  const others = siblings.filter((s) => s.marketId !== current.marketId);

  return (
    <div className="relative mb-3.5">
      <button
        type="button"
        onClick={onToggle}
        className={
          "flex items-start gap-2.5 w-full px-3.5 py-2.5 rounded border border-ring text-left text-ink transition-shadow " +
          (open ? "bg-glass-strong shadow-neu-inset" : "bg-glass-strong shadow-neu-raised")
        }
      >
        <span
          className="font-mono uppercase font-bold flex-shrink-0 mt-0.5"
          style={{
            background: "var(--accent-soft)",
            color: "var(--accent)",
            fontSize: 9,
            letterSpacing: 1.2,
            padding: "3px 6px",
            borderRadius: 3,
          }}
        >
          MARKET
        </span>
        <span
          className="flex-1 font-semibold leading-tight text-ink min-w-0"
          style={{
            fontSize: 21,
            letterSpacing: "-0.02em",
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {current.name}
        </span>
        <span className="flex items-center gap-2 flex-shrink-0 mt-0.5">
          <a
            href={venueUrl}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="inline-flex items-center gap-1.5 rounded-full bg-glass-strong shadow-neu-raised border border-ring py-1 pl-1.5 pr-2.5 text-[10.5px] font-semibold text-ink no-underline"
          >
            <img src={meta.favicon} alt="" width={13} height={13} className="rounded" />
            {meta.name}
          </a>
          <span
            className="font-mono text-ink-mute"
            style={{ fontSize: 10, padding: "2px 7px", borderRadius: 3, border: "1px solid var(--line)" }}
          >
            {siblings.length} markets
          </span>
          <span
            className="text-ink-mute transition-transform"
            style={{ transform: open ? "rotate(180deg)" : "rotate(0deg)" }}
          >
            <ChevronDown size={12} />
          </span>
        </span>
      </button>

      {open && others.length > 0 && (
        <div
          className="absolute left-0 right-0 z-20 rounded p-1 bg-glass-strong border border-ring shadow-soft backdrop-blur-glass"
          style={{ top: "calc(100% + 4px)", maxHeight: 260, overflow: "auto" }}
        >
          <div
            className="font-mono uppercase text-ink-mute flex items-center gap-2 px-3 pt-2 pb-1.5"
            style={{ fontSize: 9, letterSpacing: 1.2 }}
          >
            OTHER MARKETS UNDER THIS EVENT
            <span className="flex-1" />
            <span className="text-accent">Sorted by volume</span>
          </div>
          {others.map((s) => (
            <button
              key={s.marketId}
              type="button"
              onClick={() => onPick(s.marketId)}
              className="block w-full text-left rounded px-3 py-2 text-[12.5px] text-ink-soft leading-tight hover:bg-accent-soft"
            >
              {s.name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
