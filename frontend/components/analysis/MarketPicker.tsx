import React from "react";
import ClosesInChip from "./ClosesInChip";

type MarketOption = {
  slug?: string;
  id?: string;
  market_id?: string;
  venue?: "kalshi" | "polymarket";
  label?: string;
  question?: string;
  title?: string;
  image?: string;
  best_bid?: number;
  best_ask?: number;
  liquidity?: number;
  // Optional volume fields if provided by backend
  volume?: number;
  volume24hr?: number;
  end_date?: string;
  outcomes?: string[];
  outcome_prices?: number[];
};

type EventContext = {
  title?: string;
  image?: string;
  endDate?: string;
  end_date?: string;
};

type Props = {
  options: MarketOption[];
  eventContext?: EventContext | null;
  isSubmitting: boolean;
  onSelect: (marketId: string) => void;
  onSortedOptionsChange?: (options: MarketOption[]) => void;
};

const SORT_OPTIONS: { key: "active" | "soonest" | "total"; label: string }[] = [
  { key: "active", label: "Active (24h volume)" },
  { key: "soonest", label: "Soonest to close" },
  { key: "total", label: "Highest total volume" },
];

const getMarketId = (m: MarketOption) => String(m.market_id ?? m.slug ?? m.id ?? "");
const getMarketLabel = (m: MarketOption) =>
  m.label || m.question || m.title || m.slug || m.market_id || "Market";

function MarketGridCard({
  m,
  active,
  isSubmitting,
  onClick,
}: {
  m: MarketOption;
  active: boolean;
  isSubmitting: boolean;
  onClick: () => void;
}) {
  const askVal = typeof m.best_ask === "number" ? m.best_ask : undefined;
  const bidVal = typeof m.best_bid === "number" ? m.best_bid : undefined;
  const ask = typeof askVal === "number" ? askVal.toFixed(2) : "—";
  const bid = typeof bidVal === "number" ? bidVal.toFixed(2) : "—";
  const mid =
    typeof bidVal === "number" && typeof askVal === "number"
      ? (bidVal + askVal) / 2
      : typeof askVal === "number"
      ? askVal
      : 0;
  const name = getMarketLabel(m);
  const liq =
    typeof m.liquidity === "number" && Number.isFinite(m.liquidity)
      ? Number(m.liquidity).toLocaleString()
      : "—";

  return (
    <button
      id={`market-option-${getMarketId(m)}`}
      type="button"
      disabled={isSubmitting}
      onClick={onClick}
      className={
        "relative overflow-hidden rounded p-3 text-left cursor-pointer transition-shadow border disabled:opacity-50 " +
        (active
          ? "bg-glass-strong shadow-neu-raised"
          : "bg-glass shadow-soft backdrop-blur-glass")
      }
      style={{ borderColor: active ? "var(--accent-soft)" : "var(--ring)" }}
    >
      {active && (
        <div
          className="absolute top-0 left-0 right-0"
          style={{ height: 2, background: "var(--accent)" }}
        />
      )}
      <div className="flex items-start gap-2.5">
        <div
          className="grid place-items-center flex-shrink-0 mt-0.5 rounded bg-neu-track shadow-neu-inset"
          style={{ width: 28, height: 28 }}
        >
          <div
            className="rounded-sm"
            style={{ width: 14, height: 14, background: "var(--accent)", opacity: 0.6 }}
          />
        </div>
        <div className="flex-1 min-w-0">
          <div
            className="text-[12.5px] font-semibold text-ink leading-tight"
            style={{
              letterSpacing: "-0.01em",
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
            }}
          >
            {name}
          </div>
          <div className="flex gap-2.5 mt-2 font-mono text-[10px] text-ink-mute">
            <span>
              BID <span className="text-ink-soft">{bid}</span>
            </span>
            <span>
              ASK <span className="text-ink-soft">{ask}</span>
            </span>
            <span>
              LIQ <span className="text-ink-soft">{liq}</span>
            </span>
          </div>
          <div className="mt-2 h-0.5 rounded bg-neu-track shadow-neu-inset relative overflow-hidden">
            <div
              className="absolute left-0 inset-y-0"
              style={{
                width: `${Math.round(Math.max(0, Math.min(1, mid)) * 100)}%`,
                background: "var(--accent)",
                opacity: 0.8,
              }}
            />
          </div>
        </div>
      </div>
    </button>
  );
}

export default function MarketSelection({
  options,
  eventContext,
  isSubmitting,
  onSelect,
  onSortedOptionsChange,
}: Props) {
  const [sortBy, setSortBy] = React.useState<"active" | "soonest" | "total">("active");
  const [isSortOpen, setIsSortOpen] = React.useState(false);

  // No filtering; operate directly on options
  const filteredOptions = options;

  // Sort options based on selection:
  // - "active": 24h volume desc (fallback total, then liquidity), tie-break soonest end_date
  // - "total": total volume desc (fallback 24h, then liquidity), tie-break soonest end_date
  // - "soonest": soonest end_date first, tie-break by 24h volume desc
  const sortedOptions = React.useMemo(() => {
    const v24 = (m: MarketOption): number => {
      const n = Number(m.volume24hr ?? NaN);
      return Number.isNaN(n) ? 0 : n;
    };
    const vTotal = (m: MarketOption): number => {
      const n = Number(m.volume ?? NaN);
      return Number.isNaN(n) ? 0 : n;
    };
    const liq = (m: MarketOption): number => {
      const n = Number(m.liquidity ?? NaN);
      return Number.isNaN(n) ? 0 : n;
    };
    const scoreActive = (m: MarketOption): number => {
      const s24 = v24(m);
      if (s24) return s24;
      const vt = vTotal(m);
      if (vt) return vt;
      return liq(m);
    };
    const scoreTotal = (m: MarketOption): number => {
      const vt = vTotal(m);
      if (vt) return vt;
      const s24 = v24(m);
      if (s24) return s24;
      return liq(m);
    };
    const endTs = (m: MarketOption) => {
      const t = m.end_date ? Date.parse(m.end_date) : Number.POSITIVE_INFINITY;
      return Number.isNaN(t) ? Number.POSITIVE_INFINITY : t;
    };
    const arr = [...filteredOptions];
    if (sortBy === "active") {
      arr.sort((a, b) => {
        const vb = scoreActive(b);
        const va = scoreActive(a);
        if (vb !== va) return vb - va;
        return endTs(a) - endTs(b);
      });
      return arr;
    }
    if (sortBy === "total") {
      arr.sort((a, b) => {
        const vb = scoreTotal(b);
        const va = scoreTotal(a);
        if (vb !== va) return vb - va;
        return endTs(a) - endTs(b);
      });
      return arr;
    }
    // sortBy === "soonest"
    arr.sort((a, b) => endTs(a) - endTs(b));
    // For identical end times, break ties by 24h volume
    arr.sort((a, b) => {
      const ea = endTs(a);
      const eb = endTs(b);
      if (ea !== eb) return 0;
      return v24(b) - v24(a);
    });
    return arr;
  }, [filteredOptions, sortBy]);

  React.useEffect(() => {
    if (onSortedOptionsChange) {
      onSortedOptionsChange(sortedOptions);
    }
  }, [sortedOptions, onSortedOptionsChange]);

  const optionsCount = sortedOptions.length;
  const colClass =
    optionsCount === 1 ? "grid-cols-1" : optionsCount === 2 ? "grid-cols-2" : "grid-cols-3";

  const currentSortLabel =
    SORT_OPTIONS.find((opt) => opt.key === sortBy)?.label ?? SORT_OPTIONS[0].label;

  const closeTime = eventContext?.endDate ?? eventContext?.end_date;

  return (
    <div id="market-selection" className="mb-6">
      <div
        className="relative rounded-lg p-5 bg-glass border border-ring shadow-soft backdrop-blur-glass mb-3.5"
      >
        <div
          className="absolute inset-0 rounded-lg pointer-events-none"
          style={{ boxShadow: "inset 0 1px 0 var(--highlight)" }}
        />
        <div
          id="market-selection-header"
          className="flex items-center gap-2.5 mb-1.5 flex-wrap relative z-10"
        >
          <span
            className="font-mono uppercase text-ink-mute"
            style={{ fontSize: 10, letterSpacing: 1.4 }}
          >
            EVENT
          </span>
          <span className="flex-1 text-[13px] text-ink-soft font-medium">
            {eventContext?.title ?? "Multi-market event"}
          </span>
          <ClosesInChip closeTime={closeTime} />
        </div>
        <div
          className="text-[22px] font-semibold leading-tight text-ink mb-2.5 relative z-10"
          style={{ letterSpacing: "-0.02em", maxWidth: 680 }}
        >
          Select a market to analyze
        </div>
        <div className="flex items-center gap-2.5 flex-wrap relative z-10">
          <div
            className="font-mono uppercase font-semibold"
            style={{
              padding: "6px 12px",
              borderRadius: 999,
              background: "var(--accent-soft)",
              color: "var(--accent)",
              fontSize: 10,
              letterSpacing: 0.8,
            }}
          >
            {optionsCount} MARKETS
          </div>
          <span className="flex-1" />
          <div id="market-sort" className="relative select-none flex items-center gap-2.5">
            <span
              className="font-mono uppercase text-ink-mute"
              style={{ fontSize: 10, letterSpacing: 1.2 }}
            >
              SORT BY
            </span>
            <button
              type="button"
              className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-glass-strong shadow-neu-raised border border-ring text-[11px] text-ink"
              onClick={() => setIsSortOpen((o) => !o)}
              disabled={isSubmitting}
              aria-haspopup="listbox"
              aria-expanded={isSortOpen}
            >
              <span>{currentSortLabel}</span>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                className="text-ink-mute"
              >
                <path fill="currentColor" d="m7 10l5 5l5-5z" />
              </svg>
            </button>
            {isSortOpen && !isSubmitting && (
              <div
                id="market-sort-menu"
                className="absolute right-0 z-20 rounded p-1 bg-glass-strong border border-ring shadow-soft backdrop-blur-glass"
                style={{ top: "calc(100% + 4px)", minWidth: 200 }}
              >
                <ul id="market-sort-options" role="listbox">
                  {SORT_OPTIONS.map((opt) => (
                    <li key={opt.key}>
                      <button
                        id={`market-sort-option-${opt.key}`}
                        type="button"
                        role="option"
                        aria-selected={sortBy === opt.key}
                        className="block w-full text-left rounded px-3 py-2 text-[12.5px] text-ink-soft hover:bg-accent-soft"
                        onClick={() => {
                          setSortBy(opt.key);
                          setIsSortOpen(false);
                        }}
                      >
                        {opt.label}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>

      <div id="market-options-grid" className={`grid gap-2.5 ${colClass}`}>
        {sortedOptions.map((m, i) => (
          <MarketGridCard
            key={getMarketId(m) || i}
            m={m}
            active={i === 0}
            isSubmitting={isSubmitting}
            onClick={() => onSelect(getMarketId(m))}
          />
        ))}
      </div>
    </div>
  );
}
