"use client";

import React, { useMemo, useState } from "react";
import ActivitySparkline from "./ActivitySparkline";
import MarketPickerChip from "./MarketPickerChip";
import { articlesToBuckets } from "../../lib/sparkline-buckets";
import type { NewsArticle } from "../../types/market";

type OrderBookLevel = {
  price: number;
  size: number;
};

type PreviousMarketOption = {
  market_id: string;
  slug?: string;
  question: string;
};

export type MarketSnapshotProps = {
  // Event-level
  eventTitle: string;
  venue?: "kalshi" | "polymarket";
  groupItemTitle?: string;
  marketUrl: string;
  closesIn: string;
  endDate?: string;
  // Market-level
  question?: string;
  previousMarkets?: PreviousMarketOption[];
  onMarketSelect?: (marketId: string) => void;
  activeMarketId?: string;

  yesPrice: number;
  noPrice: number;

  marketVolume: number;
  volume24h?: number;
  liquidity?: number;

  commentCount?: number | null;
  eventCommentCount?: number | null;
  seriesCommentCount?: number | null;

  bestBid?: number;
  bestAsk?: number;
  bids?: OrderBookLevel[];
  asks?: OrderBookLevel[];

  // New optional props for live-activity card
  resolvedOutcome?: "YES" | "NO" | null;
  tags?: string[];
  articles?: NewsArticle[];
  lastRefreshedAt?: number;
};

const VENUE_META = {
  polymarket: {
    name: "Polymarket",
    favicon: "https://polymarket.com/favicon.ico",
    volumeUnit: "USDC",
    liquidityUnit: "USDC",
  },
  kalshi: {
    name: "Kalshi",
    favicon: "https://kalshi.com/favicon.ico",
    volumeUnit: "contracts",
    liquidityUnit: "OI",
  },
} as const;

function fmtNumber(n: number | undefined): string {
  if (n == null || Number.isNaN(n)) return "0";
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}B`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return Math.round(n).toLocaleString();
}

function Stat({ label, value, unit }: { label: string; value: string; unit?: string }) {
  return (
    <div className="rounded p-3 bg-glass-strong border border-ring shadow-neu-inset">
      <div className="font-mono uppercase text-ink-mute" style={{ fontSize: 9, letterSpacing: 1.2 }}>
        {label}
      </div>
      <div className="font-mono font-semibold text-ink mt-0.5" style={{ fontSize: 16 }}>
        {value}
        {unit && (
          <span className="font-mono font-normal text-ink-mute ml-1" style={{ fontSize: 10 }}>
            {unit}
          </span>
        )}
      </div>
    </div>
  );
}

function ProbCard({
  side,
  color,
  softBg,
  pct,
  price,
  note,
}: {
  side: "YES" | "NO";
  color: string;
  softBg: string;
  pct: number;
  price: number;
  note: string;
}) {
  return (
    <div
      id={side === "YES" ? "tile-yes" : "tile-no"}
      className="relative overflow-hidden rounded p-3.5"
      style={{ background: softBg, border: `1px solid ${color}22` }}
    >
      <div className="absolute top-0 left-0 right-0" style={{ height: 2, background: color, opacity: 0.6 }} />
      <div className="flex items-baseline gap-2">
        <span className="font-mono font-bold" style={{ color, fontSize: 10, letterSpacing: 1.2 }}>{side}</span>
        <span className="font-mono text-ink-mute" style={{ fontSize: 10 }}>{price.toFixed(3)}</span>
      </div>
      <div className="font-semibold leading-tight" style={{ color, fontSize: 30, letterSpacing: "-0.03em" }}>
        {pct.toFixed(1)}<span style={{ fontSize: 18, opacity: 0.6 }}>%</span>
      </div>
      <div className="text-[11px] text-ink-soft mt-0.5">{note}</div>
    </div>
  );
}

function getCountdownColor(endDate?: string): string {
  if (!endDate) return "var(--no)";
  try {
    const end = new Date(endDate).getTime();
    if (Number.isNaN(end)) return "var(--no)";
    const diffDays = Math.max(0, end - Date.now()) / (1000 * 60 * 60 * 24);
    if (diffDays < 1) return "var(--no)";
    if (diffDays < 7) return "var(--accent)";
    return "var(--yes)";
  } catch {
    return "var(--no)";
  }
}

export function MarketCard(props: MarketSnapshotProps) {
  const venue = props.venue ?? "polymarket";
  const venueMeta = VENUE_META[venue];
  const [pickerOpen, setPickerOpen] = useState(false);

  const yesPct = (props.yesPrice ?? 0) * 100;
  const noPct = (props.noPrice ?? 0) * 100;

  const hasQuotes = typeof props.bestBid === "number" && typeof props.bestAsk === "number";
  const spread = hasQuotes ? Math.max(0, (props.bestAsk ?? 0) - (props.bestBid ?? 0)) : 0;

  // Depth label (preserved from existing logic)
  const sumDepth = (levels: OrderBookLevel[] | undefined) =>
    (levels ?? []).slice(0, 3).reduce((acc, lvl) => acc + (lvl.size || 0), 0);
  const bidDepth = sumDepth(props.bids);
  const askDepth = sumDepth(props.asks);
  let depthLabel: string | null = null;
  if (bidDepth > 0 || askDepth > 0) {
    if (bidDepth > askDepth * 1.4) depthLabel = "Bid-heavy";
    else if (askDepth > bidDepth * 1.4) depthLabel = "Ask-heavy";
    else depthLabel = "Balanced book";
  }

  const buckets = useMemo(
    () => articlesToBuckets(props.articles ?? []),
    [props.articles],
  );
  const totalComments =
    (props.eventCommentCount ?? props.commentCount ?? 0) +
    (props.seriesCommentCount ?? 0);
  const showLiveCard = buckets.length > 0 || totalComments > 0;

  const liveAge = props.lastRefreshedAt != null
    ? Math.max(0, Math.floor((Date.now() - props.lastRefreshedAt) / 1000))
    : null;
  const liveLabel =
    liveAge == null
      ? null
      : liveAge < 60
        ? `LIVE · ${liveAge}s`
        : liveAge < 3600
          ? `LIVE · ${Math.floor(liveAge / 60)}m`
          : null;

  const yesNote =
    yesPct > 90 ? "Market favors YES strongly" :
    yesPct > 50 ? "Market favors YES" :
    yesPct > 10 ? "Could go either way" :
    "Cheap lottery territory";
  const noNote =
    noPct > 90 ? "Market is saying \"no way\"" :
    noPct > 50 ? "Market favors NO" :
    noPct > 10 ? "Could go either way" :
    "Cheap lottery territory";

  // Adapt previousMarkets shape (snake_case from API → camelCase for chip)
  const siblings = (props.previousMarkets ?? []).map((m) => ({
    marketId: m.market_id,
    name: m.question,
  }));

  const countdownColor = getCountdownColor(props.endDate);

  return (
    <div
      id="market-snapshot-card"
      className="relative rounded-lg bg-glass border border-ring shadow-soft backdrop-blur-glass p-5 overflow-visible"
    >
      <div
        className="absolute inset-0 rounded-lg pointer-events-none"
        style={{ boxShadow: "inset 0 1px 0 var(--highlight)" }}
      />

      <div className="grid items-start gap-5 relative" style={{ gridTemplateColumns: "minmax(0, 1fr) auto" }}>
        <div className="min-w-0">
          {/* Event line */}
          <div className="flex items-center gap-2.5 mb-2 flex-wrap">
            <span className="font-mono uppercase text-ink-mute" style={{ fontSize: 10, letterSpacing: 1.4 }}>
              EVENT
            </span>
            <span className="text-[13px] text-ink-soft font-medium">{props.eventTitle}</span>
            {props.resolvedOutcome && (
              <span
                className="font-mono uppercase font-semibold"
                style={{
                  fontSize: 9,
                  letterSpacing: 0.6,
                  background: "var(--no-soft)",
                  color: "var(--no)",
                  padding: "2px 6px",
                  borderRadius: 3,
                }}
              >
                RESOLVED · {props.resolvedOutcome}
              </span>
            )}
            {props.endDate && !props.resolvedOutcome && (
              <span
                className="font-mono uppercase font-semibold"
                style={{
                  fontSize: 9,
                  letterSpacing: 0.6,
                  color: countdownColor,
                  marginLeft: "auto",
                }}
                title={new Date(props.endDate).toLocaleString("en-US", {
                  weekday: "long",
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              >
                Closes in {props.closesIn}
              </span>
            )}
            {!props.endDate && !props.resolvedOutcome && (
              <span
                className="font-mono uppercase font-semibold"
                style={{
                  fontSize: 9,
                  letterSpacing: 0.6,
                  color: countdownColor,
                  marginLeft: "auto",
                }}
              >
                Closes in {props.closesIn}
              </span>
            )}
          </div>

          {/* Market picker (chip) when there are sibling markets, otherwise simple title + venue link */}
          {siblings.length > 0 && (props.question ?? props.groupItemTitle) ? (
            <MarketPickerChip
              current={{
                marketId: props.activeMarketId ?? siblings[0].marketId,
                name: props.question ?? props.groupItemTitle ?? "",
              }}
              siblings={siblings}
              venue={venue}
              venueUrl={props.marketUrl}
              open={pickerOpen}
              onToggle={() => setPickerOpen((o) => !o)}
              onPick={(id) => {
                setPickerOpen(false);
                props.onMarketSelect?.(id);
              }}
            />
          ) : (
            <div className="mb-3.5 flex items-start gap-2.5">
              {(props.question || props.groupItemTitle) && (
                <span className="flex-1 text-[21px] font-semibold leading-tight text-ink" style={{ letterSpacing: "-0.02em" }}>
                  {props.question ?? props.groupItemTitle}
                </span>
              )}
              <a
                href={props.marketUrl}
                target="_blank"
                rel="noopener noreferrer"
                className={`inline-flex items-center gap-1.5 rounded-full bg-glass-strong shadow-neu-raised border border-ring py-1 pl-1.5 pr-2.5 text-[10.5px] font-semibold text-ink no-underline flex-shrink-0 mt-1 ${(props.question || props.groupItemTitle) ? "" : "ml-auto"}`}
              >
                <img
                  src={venueMeta.favicon}
                  alt={venueMeta.name}
                  width={13}
                  height={13}
                  className="rounded"
                  onError={(e) => {
                    const img = e.currentTarget as HTMLImageElement;
                    img.style.display = "none";
                  }}
                />
                {venueMeta.name}
              </a>
            </div>
          )}

          {/* YES / NO probability cards */}
          <div className="grid grid-cols-2 gap-2.5">
            <ProbCard
              side="YES"
              color="var(--yes)"
              softBg="var(--yes-soft)"
              pct={yesPct}
              price={props.yesPrice ?? 0}
              note={yesNote}
            />
            <ProbCard
              side="NO"
              color="var(--no)"
              softBg="var(--no-soft)"
              pct={noPct}
              price={props.noPrice ?? 0}
              note={noNote}
            />
          </div>

          {/* Bid / Ask / Spread + depth label + tags */}
          <div className="flex items-center gap-4 mt-3 font-mono text-[11px] text-ink-mute flex-wrap">
            <span>
              BID <span className="text-ink-soft">{(props.bestBid ?? 0).toFixed(3)}</span>
            </span>
            <span>
              ASK <span className="text-ink-soft">{(props.bestAsk ?? 0).toFixed(3)}</span>
            </span>
            <span>
              SPREAD <span className="text-ink-soft">{spread.toFixed(3)}</span>
            </span>
            {depthLabel && (
              <span
                className="font-mono uppercase"
                style={{
                  padding: "2px 8px",
                  borderRadius: 3,
                  background: "var(--neu-track)",
                  color: "var(--ink-soft)",
                  fontSize: 9,
                  letterSpacing: 0.6,
                }}
              >
                {depthLabel}
              </span>
            )}
            <span className="flex-1" />
            {props.groupItemTitle && (
              <span
                className="font-mono"
                style={{
                  padding: "2px 8px",
                  borderRadius: 3,
                  background: "var(--accent-soft)",
                  color: "var(--accent)",
                  letterSpacing: 0.6,
                }}
              >
                #{props.groupItemTitle}
              </span>
            )}
            {(props.tags ?? []).map((t) => (
              <span
                key={t}
                className="font-mono"
                style={{
                  padding: "2px 8px",
                  borderRadius: 3,
                  background: "var(--accent-soft)",
                  color: "var(--accent)",
                  letterSpacing: 0.6,
                }}
              >
                #{t}
              </span>
            ))}
          </div>
        </div>

        {/* Stats rail */}
        <div className="grid gap-2.5" style={{ width: 150 }}>
          <Stat label="24H VOLUME" value={fmtNumber(props.volume24h)} unit={venueMeta.volumeUnit} />
          <Stat label="TOTAL" value={fmtNumber(props.marketVolume)} unit={venueMeta.volumeUnit} />
          <Stat
            label={venue === "kalshi" ? "OPEN INTEREST" : "LIQUIDITY"}
            value={fmtNumber(props.liquidity)}
            unit={venueMeta.liquidityUnit}
          />

          {showLiveCard && (
            <div className="rounded p-3 bg-glass-strong border border-ring shadow-neu-raised flex flex-col gap-1.5">
              {liveLabel && (
                <div
                  className="flex items-center gap-1.5 font-mono uppercase text-ink-mute"
                  style={{ fontSize: 9, letterSpacing: 1.2 }}
                >
                  <span
                    className="rounded-full"
                    style={{
                      width: 6,
                      height: 6,
                      background: "var(--yes)",
                      boxShadow: "0 0 6px var(--yes)",
                    }}
                  />
                  {liveLabel}
                </div>
              )}
              {totalComments > 0 && (
                <div className="font-mono text-ink-soft" style={{ fontSize: 11 }}>
                  <span className="text-ink font-semibold">{totalComments.toLocaleString()}</span>
                  <span className="text-ink-mute"> comments</span>
                </div>
              )}
              {buckets.length > 0 && <ActivitySparkline buckets={buckets} />}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default MarketCard;
