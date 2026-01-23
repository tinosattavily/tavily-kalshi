/**
 * Market-related type definitions for the Tavily Kalshi Signals frontend.
 */

/** A single news article from Tavily search results. */
export interface NewsArticle {
  title?: string;
  source?: string;
  url?: string;
  published_at?: string;
  publishedAt?: string; // Alias for camelCase
  snippet?: string;
  summary?: string;
  sentiment?: "bullish" | "bearish" | "neutral";
}

/** News context containing articles and summaries. */
export interface NewsContext {
  articles?: NewsArticle[];
  summary?: string;
  combined_summary?: string;
  tavily_queries?: string[];
  queries?: Array<{
    name?: string;
    query?: string;
    results?: NewsArticle[];
    answer?: string;
  }>;
}

/** Order book entry with price and size. */
export interface OrderBookEntry {
  price?: number;
  size?: number;
}

/** Order book with bids and asks. */
export interface OrderBook {
  bids?: OrderBookEntry[];
  asks?: OrderBookEntry[];
}

/** Market snapshot data from Kalshi API. */
export interface MarketSnapshot {
  question?: string;
  url?: string;
  slug?: string;
  endDate?: string;
  end_date?: string;
  group_item_title?: string;
  groupItemTitle?: string;
  yes_price?: number;
  no_price?: number;
  volume?: string | number;
  volume24hr?: number;
  liquidity?: string | number;
  comment_count?: number;
  commentCount?: number;
  event_comment_count?: number;
  eventCommentCount?: number;
  series_comment_count?: number;
  seriesCommentCount?: number;
  best_bid?: number;
  bestBid?: number;
  best_ask?: number;
  bestAsk?: number;
  order_book?: OrderBook;
  orderBook?: OrderBook;
}

/** Event context from Kalshi. */
export interface EventContext {
  title?: string;
  url?: string;
  volume24hr?: number;
  commentCount?: number;
  seriesCommentCount?: number;
}

/** Market option for selection. */
export interface MarketOption {
  slug?: string;
  question?: string;
  id?: string;
}
