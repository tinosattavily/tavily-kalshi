import React, { useEffect, useMemo, useRef, useState } from "react";

interface MarketOption {
  slug: string;
  question?: string;
  image?: string;
  best_bid?: number;
  best_ask?: number;
  liquidity?: number;
  volume?: number;
  volume24hr?: number;
  end_date?: string;
  outcomes?: string[];
  outcome_prices?: number[];
}

interface EventContext {
  title?: string;
  image?: string;
}

interface MarketSelectionProps {
  options: MarketOption[];
  eventContext?: EventContext | null;
  isSubmitting: boolean;
  onSelect: (slug: string) => void;
  onSortedOptionsChange?: (options: MarketOption[]) => void;
}

type SortOption = "active" | "soonest" | "total";

const SORT_OPTIONS: Array<{ key: SortOption; label: string }> = [
  { key: "active", label: "Active (24h volume)" },
  { key: "soonest", label: "Soonest to close" },
  { key: "total", label: "Highest total volume" },
];

function getNumericValue(value: number | undefined): number {
  const n = Number(value ?? NaN);
  return Number.isNaN(n) ? 0 : n;
}

function getEndTimestamp(market: MarketOption): number {
  const t = market.end_date ? Date.parse(market.end_date) : Number.POSITIVE_INFINITY;
  return Number.isNaN(t) ? Number.POSITIVE_INFINITY : t;
}

function getActiveScore(market: MarketOption): number {
  const v24 = getNumericValue(market.volume24hr);
  if (v24) return v24;
  const vTotal = getNumericValue(market.volume);
  if (vTotal) return vTotal;
  return getNumericValue(market.liquidity);
}

function getTotalScore(market: MarketOption): number {
  const vTotal = getNumericValue(market.volume);
  if (vTotal) return vTotal;
  const v24 = getNumericValue(market.volume24hr);
  if (v24) return v24;
  return getNumericValue(market.liquidity);
}

function sortMarkets(markets: MarketOption[], sortBy: SortOption): MarketOption[] {
  const arr = [...markets];

  if (sortBy === "active") {
    arr.sort((a, b) => {
      const scoreDiff = getActiveScore(b) - getActiveScore(a);
      if (scoreDiff !== 0) return scoreDiff;
      return getEndTimestamp(a) - getEndTimestamp(b);
    });
    return arr;
  }

  if (sortBy === "total") {
    arr.sort((a, b) => {
      const scoreDiff = getTotalScore(b) - getTotalScore(a);
      if (scoreDiff !== 0) return scoreDiff;
      return getEndTimestamp(a) - getEndTimestamp(b);
    });
    return arr;
  }

  arr.sort((a, b) => {
    const endDiff = getEndTimestamp(a) - getEndTimestamp(b);
    if (endDiff !== 0) return endDiff;
    return getNumericValue(b.volume24hr) - getNumericValue(a.volume24hr);
  });
  return arr;
}

export default function MarketSelection({
  options,
  eventContext,
  isSubmitting,
  onSelect,
  onSortedOptionsChange,
}: MarketSelectionProps): React.JSX.Element {
  const [sortBy, setSortBy] = useState<SortOption>("active");
  const [isSortOpen, setIsSortOpen] = useState(false);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [sliderStyle, setSliderStyle] = useState<React.CSSProperties>({ opacity: 0 });
  const buttonRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const gridRef = useRef<HTMLDivElement | null>(null);

  const count = options.length;
  const sortedOptions = useMemo(() => sortMarkets(options, sortBy), [options, sortBy]);

  useEffect(() => {
    onSortedOptionsChange?.(sortedOptions);
  }, [sortedOptions, onSortedOptionsChange]);

  useEffect(() => {
    buttonRefs.current = [];
  }, [sortedOptions]);

  useEffect(() => {
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

  function renderMarketButton(m: MarketOption, index: number): React.JSX.Element {
    return (
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
  }

  function renderSingleRowGrid(n: number): React.JSX.Element {
    let colClass = "grid-cols-3";
    if (n === 1) colClass = "grid-cols-1";
    else if (n === 2) colClass = "grid-cols-2";
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
        {sortedOptions.map((m, idx) => renderMarketButton(m, idx))}
      </div>
    );
  }

  function renderHoverSlider(): React.JSX.Element {
    return (
      <div
        className="absolute rounded-xl bg-neutral-200/80 border border-white shadow-xl pointer-events-none transition-all duration-300 ease-in-out z-0"
        style={sliderStyle}
      />
    );
  }

  function getSortLabel(): string {
    const option = SORT_OPTIONS.find((o) => o.key === sortBy);
    return option?.label ?? "";
  }

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
            <span>{getSortLabel()}</span>
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
                {SORT_OPTIONS.map((opt) => (
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

        {count <= 3 && renderSingleRowGrid(count)}
        {count === 4 && (
          <div
            id="market-options-grid"
            ref={gridRef}
            className="grid grid-cols-2 gap-3 relative"
            onMouseLeave={() => setHoveredIndex(null)}
          >
            {renderHoverSlider()}
            {sortedOptions.map((m, idx) => renderMarketButton(m, idx))}
          </div>
        )}
        {count === 5 && (
          <div
            id="market-options-grid"
            ref={gridRef}
            className="space-y-3 relative"
            onMouseLeave={() => setHoveredIndex(null)}
          >
            {renderHoverSlider()}
            <div className="grid grid-cols-3 gap-3">
              {sortedOptions.slice(0, 3).map((m, idx) => renderMarketButton(m, idx))}
            </div>
            <div className="grid grid-cols-2 gap-3">
              {sortedOptions.slice(3).map((m, idx) => renderMarketButton(m, idx + 3))}
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
            {renderHoverSlider()}
            {sortedOptions.map((m, idx) => renderMarketButton(m, idx))}
          </div>
        )}
      </div>
    </div>
  );
}
