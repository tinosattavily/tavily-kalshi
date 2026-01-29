"use client";

import React, { useState } from "react";

import {
  Activity,
  ArrowUpRight,
  CheckCircle2,
  Hash,
  MessageCircle,
  Scale,
  Timer,
  Waves,
  XCircle,
} from "lucide-react";

interface OrderBookLevel {
  price: number;
  size: number;
}

interface PreviousMarketOption {
  slug: string;
  question: string;
}

interface Resolution {
  status?: 'pending' | 'resolved_yes' | 'resolved_no' | 'voided' | 'unknown';
  winning_outcome?: string;
  resolved_at?: string;
  final_yes_price?: number;
  final_no_price?: number;
}

interface MarketSnapshotProps {
  eventTitle: string;
  groupItemTitle?: string;
  polymarketUrl: string;
  closesIn: string;
  endDate?: string;
  question?: string;
  previousMarkets?: PreviousMarketOption[];
  onMarketSelect?: (slug: string) => void;
  activeMarketSlug?: string;
  yesPrice: number;
  noPrice: number;
  marketVolume: number;
  volume24h?: number;
  liquidity?: number;
  commentCount?: number;
  eventCommentCount?: number;
  seriesCommentCount?: number;
  bestBid?: number;
  bestAsk?: number;
  bids?: OrderBookLevel[];
  asks?: OrderBookLevel[];
  resolution?: Resolution;
}

function formatUsdCompact(value: number | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)}B`;
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}k`;
  return value.toFixed(0);
}

function getCountdownColor(endDate?: string): string {
  if (!endDate) return "text-red-500";

  try {
    const end = new Date(endDate).getTime();
    if (Number.isNaN(end)) return "text-red-500";

    const now = Date.now();
    const diffMs = Math.max(0, end - now);
    const diffDays = diffMs / (1000 * 60 * 60 * 24);

    if (diffDays < 1) return "text-red-500";
    if (diffDays < 7) return "text-yellow-500";
    return "text-green-500";
  } catch {
    return "text-red-500";
  }
}

function sumDepth(levels: OrderBookLevel[]): number {
  return levels.slice(0, 3).reduce((acc, lvl) => acc + (lvl.size || 0), 0);
}


export function MarketSnapshotCard(props: MarketSnapshotProps): React.JSX.Element {
  const {
    eventTitle,
    groupItemTitle,
    polymarketUrl,
    closesIn,
    endDate,
    question,
    previousMarkets = [],
    onMarketSelect,
    activeMarketSlug,
    yesPrice,
    noPrice,
    marketVolume,
    volume24h,
    liquidity,
    commentCount,
    eventCommentCount,
    seriesCommentCount,
    bestBid,
    bestAsk,
    bids = [],
    asks = [],
    resolution,
  } = props;

  const [isMarketDropdownOpen, setIsMarketDropdownOpen] = useState(false);

  const countdownColor = getCountdownColor(endDate);
  const yesPct = yesPrice * 100;
  const noPct = noPrice * 100;
  const impliedMultiplier = yesPrice > 0 ? (1 / yesPrice).toFixed(1) : "∞";

  const hasQuotes = typeof bestBid === "number" && typeof bestAsk === "number";
  const spread = hasQuotes ? Math.max(0, bestAsk! - bestBid!) : undefined;
  const mid = hasQuotes ? (bestAsk! + bestBid!) / 2 : undefined;
  const spreadPct = hasQuotes && mid && mid > 0 ? (spread! / mid) * 100 : undefined;

  const bidDepth = sumDepth(bids);
  const askDepth = sumDepth(asks);

  let depthLabel = "Balanced book";
  if (bidDepth > askDepth * 1.4) {
    depthLabel = "Bid-heavy";
  } else if (askDepth > bidDepth * 1.4) {
    depthLabel = "Ask-heavy";
  }

  return (
    <div
      id="market-snapshot-card"
      className="rounded-3xl bg-[#f3f4f6] p-6 shadow-neumorph-lg overflow-visible"
    >
      {/* Header: title + chips */}
      <div className="mb-3 flex items-start justify-between gap-3 overflow-visible">
        <div className="min-w-0 overflow-visible">
          <p className="py-2 flex items-center gap-2 text-base uppercase tracking-[0.18em] text-[#1e3a8a]">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 48 48" className="text-[#1e3a8a]">
              <g fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="4">
                <path d="M44 11a3 3 0 0 0-3-3H7a3 3 0 0 0-3 3v9h40v-9ZM4.112 39.03l12.176-12.3l6.58 6.3L30.91 26l4.48 4.368"/>
                <path d="M44 18v19a3 3 0 0 1-3 3H12m7.112-26h18M11.11 14h2M4 18v9"/>
              </g>
            </svg>
            Market snapshot
          </p>
          <div className="mt-1 flex items-center gap-2 pt-2 px-2">
            <span className="inline-flex items-center rounded-full bg-slate-200 px-2 py-0.5 text-xs uppercase tracking-[0.1em] text-[#1e3a8a]">
              EVENT:
            </span>
            <h3 className="text-sm font-semibold text-slate-900">
              {eventTitle}
            </h3>
          </div>
          {question && (
            <div className="mt-2 ml-4 flex flex-wrap items-center gap-2 pb-2 px-2 overflow-visible">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 256 256" className="text-[#1e3a8a]">
                <path fill="currentColor" d="m228.24 156.24l-48 48a6 6 0 0 1-8.48-8.48L209.51 158H128A102.12 102.12 0 0 1 26 56a6 6 0 0 1 12 0a90.1 90.1 0 0 0 90 90h81.51l-37.75-37.76a6 6 0 0 1 8.48-8.48l48 48a6 6 0 0 1 0 8.48Z"/>
              </svg>
              <div 
                className="relative inline-block group overflow-visible"
                onMouseEnter={() => {
                  if (previousMarkets.length > 0) {
                    setIsMarketDropdownOpen(true);
                  }
                }}
                onMouseLeave={() => setIsMarketDropdownOpen(false)}
              >
                <span className="inline-flex items-center rounded-full bg-slate-200 px-2 py-0.5 text-xs uppercase tracking-[0.1em] text-[#1e3a8a] cursor-pointer">
                  MARKET:
                </span>
                {previousMarkets.length > 0 && (
                  <div 
                    className={`absolute left-0 top-full z-[9999] w-64 rounded-xl border border-neutral-200 bg-white p-1 shadow-lg transition-all duration-200 ${
                      isMarketDropdownOpen ? 'opacity-100 mt-1 pointer-events-auto block' : 'opacity-0 mt-0 pointer-events-none hidden'
                    }`}
                    style={{ position: 'absolute', zIndex: 9999 }}
                    onMouseEnter={() => setIsMarketDropdownOpen(true)}
                    onMouseLeave={() => setIsMarketDropdownOpen(false)}
                  >
                    <ul className="max-h-60 overflow-auto">
                      {previousMarkets.map((market) => (
                        <li key={market.slug}>
                          <button
                            type="button"
                            className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-left hover:bg-neutral-100 transition-colors ${
                              activeMarketSlug === market.slug ? "bg-[#1e3a8a]/10" : ""
                            }`}
                            onClick={() => {
                              onMarketSelect?.(market.slug);
                              setIsMarketDropdownOpen(false);
                            }}
                          >
                            <span
                              className={`flex-1 line-clamp-2 ${
                                activeMarketSlug === market.slug
                                  ? "text-[#1e3a8a] font-semibold"
                                  : "text-neutral-800"
                              }`}
                            >
                              {market.question}
                            </span>
                            {activeMarketSlug === market.slug && (
                              <svg
                                xmlns="http://www.w3.org/2000/svg"
                                width="20"
                                height="20"
                                viewBox="0 0 24 24"
                                className="text-[#1e3a8a]"
                              >
                                <path
                                  fill="none"
                                  stroke="currentColor"
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth="1.5"
                                  d="M5 14.5s1.5 0 3.5 3.5c0 0 5.559-9.167 10.5-11"
                                />
                              </svg>
                            )}
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              <p className="text-[13px] font-medium leading-snug text-slate-800">
                {question}
              </p>
            </div>
          )}
        </div>
        <div className="flex flex-col items-end gap-1">
          {resolution?.status === 'resolved_yes' ? (
            <div className="inline-flex items-center gap-2 rounded-full bg-[#e8f5e9] px-3 py-2 text-sm font-semibold text-emerald-800">
              <CheckCircle2 className="h-5 w-5" />
              Resolved: YES
            </div>
          ) : resolution?.status === 'resolved_no' ? (
            <div className="inline-flex items-center gap-2 rounded-full bg-[#ffebee] px-3 py-2 text-sm font-semibold text-rose-900">
              <XCircle className="h-5 w-5" />
              Resolved: NO
            </div>
          ) : resolution?.status === 'voided' ? (
            <div className="inline-flex items-center gap-2 rounded-full bg-neutral-200 px-3 py-2 text-sm font-semibold text-neutral-700">
              Market Voided
            </div>
          ) : endDate ? (
            <div className="group relative inline-flex items-center gap-1 rounded-full bg-transparent px-2 py-2 text-sm cursor-help">
              <Timer className={`h-5 w-5 ${countdownColor} animate-pulse`} />
              <span className={countdownColor}>Closes in {closesIn}</span>
              <div className="absolute top-full right-0 mt-2 hidden group-hover:block z-[9999]">
                <div className="bg-slate-900 text-white text-xs rounded-lg py-2 px-3 shadow-xl whitespace-nowrap relative">
                  <div className="absolute bottom-full right-4 w-0 h-0 border-l-[6px] border-r-[6px] border-b-[6px] border-transparent border-b-slate-900"></div>
                  <div className="font-semibold mb-1">Closure Date</div>
                  <div>{new Date(endDate).toLocaleString('en-US', { 
                    weekday: 'long', 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}</div>
                </div>
              </div>
            </div>
          ) : (
            <span className={`inline-flex items-center gap-1 rounded-full bg-transparent px-2 py-2 text-sm ${countdownColor}`}>
              <Timer className={`h-5 w-5 ${countdownColor} animate-pulse`} />
              Closes in {closesIn}
            </span>
          )}
        </div>
      </div>

      {/* 2x3 Grid: YES/NO/Metrics and Order Book/Comments */}
      <div className="mb-3 grid gap-3 text-xs sm:grid-cols-[1fr_1fr_auto]">
        {/* Row 1, Column 1: YES side */}
        <div 
          id="tile-yes" 
          className="flex flex-col rounded-2xl bg-[#e8f5e9] p-3"
          style={{
            boxShadow: '6px 6px 12px #c8d6c9, -6px -6px 12px #ffffff'
          }}
        >
          <div>
            <p className="text-base font-semibold tracking-wide text-emerald-800">YES</p>
            <p className="mt-1 text-3xl font-semibold text-emerald-900">
              {yesPrice.toFixed(3)}
              <span className="ml-1 text-[11px] text-emerald-700">
                ({yesPct.toFixed(1)}%)
              </span>
            </p>
            <p className="mt-1 text-[10px] text-emerald-600">
              Implied multiplier:{" "}
              <span className="text-emerald-800">{impliedMultiplier}x</span>
            </p>
          </div>
          <p className="mt-auto pt-2 text-[10px] text-emerald-600/80">
            Cheap lottery ticket territory if you think the world is wrong.
          </p>
        </div>

        {/* Row 1, Column 2: NO side */}
        <div 
          id="tile-no" 
          className="flex flex-col rounded-2xl bg-[#ffebee] p-3"
          style={{
            boxShadow: '6px 6px 12px #e6d3d5, -6px -6px 12px #ffffff'
          }}
        >
          <div>
            <p className="text-base font-semibold tracking-wide text-rose-900">NO</p>
            <p className="mt-1 text-3xl font-semibold text-rose-900">
              {noPrice.toFixed(3)}
              <span className="ml-1 text-[11px] text-rose-900">
                ({noPct.toFixed(1)}%)
              </span>
            </p>
          </div>
          <p className="mt-auto pt-2 text-[10px] text-rose-900/80">
            Market is basically saying &quot;no way&quot; right now.
          </p>
        </div>

        {/* Row 1, Column 3: Market Metrics - stacked */}
        <div className="flex flex-col w-fit">
          <div className="flex items-center gap-2 bg-transparent p-2.5 border-b border-gray-400">
            <Activity className="h-3.5 w-3.5 text-sky-400" />
            <div>
              <p className="text-[11px] text-slate-500 font-medium">Volume (24h)</p>
              <p className="text-base font-semibold text-black">
                {volume24h != null
                  ? `${formatUsdCompact(volume24h)} USDC`
                  : `${formatUsdCompact(marketVolume)} USDC`}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-transparent p-2.5 border-b border-gray-400">
            <Waves className="h-3.5 w-3.5 text-emerald-400" />
            <div>
              <p className="text-[11px] text-slate-500 font-medium">Total volume</p>
              <p className="text-base font-semibold text-black">
                {formatUsdCompact(marketVolume)} USDC
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-transparent p-2.5">
            <Scale className="h-3.5 w-3.5 text-purple-400" />
            <div>
              <p className="text-[11px] text-slate-500 font-medium">Liquidity</p>
              <p className="text-base font-semibold text-black">
                {liquidity != null ? `${formatUsdCompact(liquidity)} USDC` : "—"}
              </p>
            </div>
          </div>
        </div>

        {/* Row 2, Column 1: Order Book snapshot */}
        <div id="market-snapshot-micro" className="flex flex-col gap-1 rounded-2xl bg-transparent px-3 py-2 text-sm text-black">
        <div className="flex flex-wrap items-center gap-2">
          {hasQuotes ? (
            <>
              <span>
                <span className="text-slate-500">Bid</span>{" "}
                <span className="font-mono text-black">
                  {bestBid!.toFixed(3)}
                </span>
              </span>
              <span className="text-black">·</span>
              <span>
                <span className="text-slate-500">Ask</span>{" "}
                <span className="font-mono text-black">
                  {bestAsk!.toFixed(3)}
                </span>
              </span>
              {spread != null && (
                <>
                  <span className="text-black">·</span>
                  <span>
                    <span className="text-slate-500">Spread</span>{" "}
                    <span className="font-mono text-black">
                      {spread.toFixed(3)}
                    </span>
                    {spreadPct != null && (
                      <span className="ml-1 text-slate-500">
                        (~{spreadPct.toFixed(1)}% of mid)
                      </span>
                    )}
                  </span>
                </>
              )}
            </>
          ) : (
            <span className="text-slate-500">
              Order book snapshot not available.
            </span>
          )}
        </div>
        {bids.length > 0 || asks.length > 0 ? (
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-black">
              Depth (top 3) — bid{" "}
              <span className="font-mono text-black">
                {formatUsdCompact(bidDepth)}
              </span>{" "}
              vs ask{" "}
              <span className="font-mono text-black">
                {formatUsdCompact(askDepth)}
              </span>
            </span>
            <span className="rounded-full bg-slate-900/80 px-2 py-0.5 text-xs uppercase tracking-[0.14em] text-slate-400">
              {depthLabel}
            </span>
          </div>
        ) : null}
        <div className="mt-1">
          <span className="text-xs text-slate-500">
            Snapshot for analysis only — not execution advice.
          </span>
        </div>
        </div>

        {/* Row 2, Column 2: Comments */}
        <div id="market-snapshot-stats" className="flex flex-col gap-2 rounded-2xl bg-transparent px-3 py-2 text-sm text-black">
          <div className="flex items-center gap-2">
            <MessageCircle className="h-3.5 w-3.5 text-slate-500" />
            <span className="text-slate-500">Comments</span>
          </div>
          {eventCommentCount != null || seriesCommentCount != null ? (
            <div className="flex flex-wrap gap-3 text-sm text-slate-600">
              {eventCommentCount != null && (
                <div>
                  Event:{" "}
                  <span className="font-semibold text-black">
                    {eventCommentCount.toLocaleString()}
                  </span>
                </div>
              )}
              {seriesCommentCount != null && (
                <div>
                  Series:{" "}
                  <span className="font-semibold text-black">
                    {seriesCommentCount.toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          ) : (
            <span className="font-semibold text-black">
              {commentCount != null ? commentCount.toLocaleString() : "—"}
            </span>
          )}
        </div>

        {/* Row 2, Column 3: Empty */}
        <div></div>
      </div>

      {/* Tags and Polymarket link - bottom row */}
      <div className="flex items-center mt-3">
        {groupItemTitle && (
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-slate-600 font-medium">Tags:</span>
            <span className="inline-flex items-center gap-1 rounded-full bg-slate-200 px-2 py-0.5 text-[10px] uppercase tracking-[0.1em] text-[#1e3a8a]">
              <Hash className="h-3 w-3 text-[#1e3a8a]" />
              {groupItemTitle}
            </span>
          </div>
        )}
        <a
          href={polymarketUrl}
          target="_blank"
          rel="noreferrer"
          className="group rounded-lg bg-white/90 px-2 py-1.5 flex items-center gap-1.5 hover:bg-white transition-colors ml-auto"
        >
          <img
            src="https://polymarket.com/favicon.ico"
            alt="Polymarket"
            className="h-4 w-4 object-contain"
            onError={(e) => {
              // Hide image if it fails to load
              const img = e.currentTarget as HTMLImageElement;
              img.style.display = "none";
            }}
          />
          <span className="text-[10px] text-slate-700 font-medium group-hover:text-[#1e3a8a] transition-colors">Polymarket</span>
          <ArrowUpRight className="h-3 w-3 text-slate-500 group-hover:text-[#1e3a8a] transition-colors" />
        </a>
      </div>
    </div>
  );
}
