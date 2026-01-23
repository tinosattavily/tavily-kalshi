import React from "react";

type MarketOption = {
  slug: string;
  question?: string;
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
};

type Props = {
  options: MarketOption[];
  eventContext?: EventContext | null;
  isSubmitting: boolean;
  onSelect: (slug: string) => void;
  onSortedOptionsChange?: (options: MarketOption[]) => void;
};

export default function MarketSelection({
  options,
  eventContext,
  isSubmitting,
  onSelect,
  onSortedOptionsChange,
}: Props) {
  const [sortBy, setSortBy] = React.useState<"active" | "soonest" | "total">("active");
  const [isSortOpen, setIsSortOpen] = React.useState(false);
  const [hoveredIndex, setHoveredIndex] = React.useState<number | null>(null);
  const [sliderStyle, setSliderStyle] = React.useState<React.CSSProperties>({ opacity: 0 });
  const buttonRefs = React.useRef<(HTMLButtonElement | null)[]>([]);
  const gridRef = React.useRef<HTMLDivElement | null>(null);
  const count = options.length;

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

  // Reset refs when sortedOptions changes
  React.useEffect(() => {
    buttonRefs.current = [];
  }, [sortedOptions]);

  // Update slider position when hovered index changes
  React.useEffect(() => {
    if (hoveredIndex === null || !buttonRefs.current[hoveredIndex] || !gridRef.current) {
      setSliderStyle({ opacity: 0 });
      return;
    }

    const button = buttonRefs.current[hoveredIndex];
    const grid = gridRef.current;
    if (!button || !grid) return;

    const buttonRect = button.getBoundingClientRect();
    const gridRect = grid.getBoundingClientRect();

    setSliderStyle({
      opacity: 1,
      left: `${buttonRect.left - gridRect.left}px`,
      top: `${buttonRect.top - gridRect.top}px`,
      width: `${buttonRect.width}px`,
      height: `${buttonRect.height}px`,
    });
  }, [hoveredIndex, sortedOptions]);

  const MarketButton = (m: MarketOption, index: number) => (
    <button
      id={`market-option-${m.slug}`}
      key={m.slug}
      ref={(el) => {
        buttonRefs.current[index] = el;
      }}
      type="button"
      disabled={isSubmitting}
      onClick={() => onSelect(m.slug)}
      onMouseEnter={() => setHoveredIndex(index)}
      className="text-left rounded-xl border border-transparent transition-all duration-300 ease-in-out p-4 bg-white/30 backdrop-blur-sm disabled:opacity-50 relative"
      style={{ WebkitBackdropFilter: "blur(8px)", zIndex: 1 }}
    >
      <div className="flex items-start gap-3">
        {m.image ? (
          <img
            src={m.image}
            alt={m.question || "Market"}
            width={40}
            height={40}
            className="rounded-md border border-white/70 w-10 h-10 object-cover"
            onError={(e) => {
              e.currentTarget.style.display = "none";
            }}
          />
        ) : null}
        <div className="flex-1">
          <div className="font-medium text-neutral-900 line-clamp-2">
            {m.question || m.slug}
          </div>
          <div className="mt-1 text-xs text-neutral-600">
            {(m.best_bid || m.best_ask) ? (
              <span className="ml-2">Bid/Ask: {m.best_bid ?? "-"} / {m.best_ask ?? "-"}</span>
            ) : null}
            {m.liquidity ? <span className="ml-2">Liq: {Number(m.liquidity).toLocaleString()}</span> : null}
          </div>
          </div>
        </div>
    </button>
  );

  const SingleRow = (n: number) => {
    const colClass = n === 1 ? "grid-cols-1" : n === 2 ? "grid-cols-2" : "grid-cols-3";
    return (
      <div 
        id="market-options-grid" 
        ref={gridRef}
        className={`grid ${colClass} gap-3 relative`}
        onMouseLeave={() => setHoveredIndex(null)}
      >
        <div
          className="absolute rounded-xl bg-neutral-200/80 border border-white shadow-xl pointer-events-none transition-all duration-300 ease-in-out z-0"
          style={sliderStyle}
        />
        {sortedOptions.map((m, idx) => MarketButton(m, idx))}
      </div>
    );
  };

  return (
    <div id="market-selection" className="mb-6">
      <div
        className="rounded-2xl border border-white bg-white/20 shadow-[0_4px_30px_rgba(0,0,0,0.1)] backdrop-blur-[11.3px] p-5 overflow-visible"
        style={{ WebkitBackdropFilter: "blur(11.3px)" }}
      >
        <div
          id="market-selection-header"
          className="flex items-start gap-3 mb-3 relative z-10 overflow-visible"
        >
          {eventContext?.image ? (
            <img
              src={eventContext.image}
              alt={eventContext.title || "Event"}
              width={36}
              height={36}
              className="w-9 h-9 rounded-md border border-white object-cover"
              onError={(e) => {
                e.currentTarget.style.display = "none";
              }}
            />
          ) : null}
          <div className="flex-1 flex flex-col justify-between h-12">
            <div className="text-base font-semibold text-neutral-900 leading-none">
              {eventContext?.title || "Event"}
            </div>
            <div className="text-xs text-neutral-600 leading-none">
              {count === 1 ? (options[0]?.question || "Selected market") : "Select a market"}
            </div>
          </div>
        {/* Sort dropdown */}
        <div id="market-sort" className="ml-auto relative select-none z-20">
          <label className="block text-[10px] uppercase tracking-[0.14em] text-neutral-600 mb-1 text-right">
            Sort by
          </label>
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-full border border-neutral-300 bg-white px-3 py-1 text-sm text-neutral-800 shadow-sm hover:bg-neutral-50"
            onClick={() => setIsSortOpen((o) => !o)}
            disabled={isSubmitting}
            aria-haspopup="listbox"
            aria-expanded={isSortOpen}
          >
            {sortBy === "active" && <span>Active (24h volume)</span>}
            {sortBy === "soonest" && <span>Soonest to close</span>}
            {sortBy === "total" && <span>Highest total volume</span>}
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" className="text-neutral-500">
              <path fill="currentColor" d="m7 10l5 5l5-5z" />
            </svg>
          </button>
          {isSortOpen && !isSubmitting && (
            <div
              id="market-sort-menu"
              className="absolute right-0 z-30 mt-2 w-56 rounded-xl border border-neutral-200 bg-white p-1 shadow-lg"
            >
              <ul id="market-sort-options" role="listbox" className="max-h-60 overflow-auto">
                {[
                  { key: "active", label: "Active (24h volume)" },
                  { key: "soonest", label: "Soonest to close" },
                  { key: "total", label: "Highest total volume" },
                ].map((opt) => (
                  <li key={opt.key}>
                    <button
                      id={`market-sort-option-${opt.key}`}
                      type="button"
                      role="option"
                      aria-selected={sortBy === opt.key}
                      className="flex w-full items-center justify-between gap-2 rounded-lg px-3 py-2 text-sm hover:bg-neutral-100"
                      onClick={() => {
                        setSortBy(opt.key as typeof sortBy);
                        setIsSortOpen(false);
                      }}
                    >
                      <span className="text-neutral-800">{opt.label}</span>
                      {sortBy === opt.key && (
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24">
                          <path fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M5 14.5s1.5 0 3.5 3.5c0 0 5.559-9.167 10.5-11" />
                        </svg>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
        </div>

        {count <= 3 && SingleRow(count)}
        {count === 4 && (
          <div 
            id="market-options-grid"
            ref={gridRef}
            className="grid grid-cols-2 gap-3 relative"
            onMouseLeave={() => setHoveredIndex(null)}
          >
            <div
              className="absolute rounded-xl bg-neutral-200/80 border border-white shadow-xl pointer-events-none transition-all duration-300 ease-in-out z-0"
              style={sliderStyle}
            />
            {sortedOptions.map((m, idx) => MarketButton(m, idx))}
          </div>
        )}
        {count === 5 && (
          <div 
            id="market-options-grid"
            ref={gridRef}
            className="space-y-3 relative"
            onMouseLeave={() => setHoveredIndex(null)}
          >
            <div
              className="absolute rounded-xl bg-neutral-200/80 border border-white shadow-xl pointer-events-none transition-all duration-300 ease-in-out z-0"
              style={sliderStyle}
            />
            <div className="grid grid-cols-3 gap-3">
              {sortedOptions.slice(0, 3).map((m, idx) => MarketButton(m, idx))}
            </div>
            <div className="grid grid-cols-2 gap-3">
              {sortedOptions.slice(3).map((m, idx) => MarketButton(m, idx + 3))}
            </div>
          </div>
        )}
        {count >= 6 && (
          <div 
            id="market-options-grid"
            ref={gridRef}
            className="grid grid-cols-3 gap-3 relative"
            onMouseLeave={() => setHoveredIndex(null)}
          >
            <div
              className="absolute rounded-xl bg-neutral-200/80 border border-white shadow-xl pointer-events-none transition-all duration-300 ease-in-out z-0"
              style={sliderStyle}
            />
            {sortedOptions.map((m, idx) => MarketButton(m, idx))}
          </div>
        )}
      </div>
    </div>
  );
}


