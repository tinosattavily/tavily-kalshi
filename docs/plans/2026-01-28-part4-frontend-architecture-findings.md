# Part 4: Frontend Architecture - Findings

> **Exploration completed:** 2026-01-28

This document captures the findings from exploring Prophily's Next.js frontend architecture.

---

## Task 1: Application Structure

### Root Layout (`frontend/app/layout.tsx`)

**Structure:**
- Server component (no "use client" directive)
- Basic HTML structure with `<html>` and `<body>` tags

**Font:**
- Inter font from Google Fonts
- Subsets: "latin"
- Display: "swap" (font-display: swap for better loading)

**Metadata:**
```typescript
export const metadata = {
  title: "Tavily Polymarket Signals",
  description: "Dashboard for multi-agent Polymarket signals.",
};
```

**No Providers/Context:**
- No React context providers at root level
- State management is local to components

### Home Page (`frontend/app/page.tsx`)

**Structure:**
- Client component (`"use client"`)
- Renders single `<Layout />` component
- Layout wraps `<Background />` component

**Component Chain:**
```
app/page.tsx (client)
  └── Layout.tsx (client)
        └── Background.tsx (client) - main dashboard
```

### Package Dependencies (`frontend/package.json`)

| Category | Package | Version |
|----------|---------|---------|
| **Framework** | Next.js | ^16.0.3 |
| **UI Library** | React | ^19.2.0 |
| **Styling** | Tailwind CSS | ^3.4.15 |
| **Utilities** | clsx | ^2.1.1 |
| **Icons** | lucide-react | ^0.460.0 |
| **Testing** | Jest + RTL | ^29.7.0 / ^16.0.0 |

**Scripts:**
| Script | Command |
|--------|---------|
| `dev` | `next dev` |
| `build` | `next build` |
| `start` | `next start` |
| `type-check` | `tsc --noEmit` |
| `lint` | `eslint . --ext .js,.jsx,.ts,.tsx` |
| `test` | `jest` |
| `test:coverage` | `jest --coverage` |

### Tailwind Configuration (`frontend/tailwind.config.ts`)

**Content Paths:**
- `./app/**/*.{js,ts,jsx,tsx}`
- `./components/**/*.{js,ts,jsx,tsx}`

**Custom Extensions:** None (default Tailwind theme)

**Custom Utilities:** None (uses Tailwind defaults)

**Note:** Custom CSS classes like `bg-grid` and `bg-noise` are defined in `globals.css` (not shown in config).

---

## Task 2: Main Dashboard Component (`frontend/components/Background.tsx`)

### Component Structure

**Layout:** CSS Grid with 2 rows × 3 columns (2fr-8fr-2fr column ratio)
```
┌─────────────┬─────────────────────────┬─────────────┐
│             │       TopNav            │             │
│   (spacer)  │                         │   (spacer)  │
├─────────────┼─────────────────────────┼─────────────┤
│   Recent    │    URL Input Bar        │   Config    │
│   Sessions  ├─────────────────────────┤   Panel     │
│             │    Results Area         │             │
│             │    (or EmptyPrompt)     │             │
│             │    (or MarketSelection) │             │
└─────────────┴─────────────────────────┴─────────────┘
```

### State Variables

| State | Type | Purpose |
|-------|------|---------|
| `url` | `string` | Current Polymarket URL input |
| `isSubmitting` | `boolean` | Whether analysis is in progress |
| `isFocused` | `boolean` | URL input focus state |
| `configuration` | `AnalysisConfiguration` | Analysis settings from config panel |
| `results` | `AnalysisResults \| null` | Analysis results from backend |
| `runStatus` | `{market, news, signal, report}` | Per-phase status ("pending"/"done"/"error") |
| `runId` | `string \| null` | Current analysis run ID for polling |
| `selectedMarketSlug` | `string \| null` | Currently selected market slug |
| `selectedRunId` | `string \| null` | Selected historical run ID |
| `lastSortedMarketOptions` | `[{slug, question}]` | Sorted market options from MarketSelection |
| `recentSessionsRefreshTrigger` | `number` | Counter to trigger RecentSessions refresh |
| `pollingRef` | `React.MutableRefObject<boolean>` | Prevents duplicate polling |
| `runIdRef` | `React.MutableRefObject<string \| null>` | Stable runId for polling closure |

### Key Interfaces

```typescript
interface AnalysisResults {
  market_snapshot?: { question, url, yes_price, no_price, volume, liquidity, ... };
  event_context?: { title, url, volume24hr, commentCount };
  news_context?: { articles, summary, combined_summary, tavily_queries };
  signal?: { direction, model_prob, confidence, rationale, ... };
  decision?: { action, edge_pct, toy_kelly_fraction, notes };
  report?: string | { title, markdown } | StructuredReport;
  market_options?: Array<{ slug, question, id }>;
  requires_market_selection?: boolean;
}
```

### Key Handlers

| Handler | Purpose |
|---------|---------|
| `handleSubmit()` | POST to `/api/analyze/start`, initializes polling |
| `handleSelectMarket(slug)` | POST with `selected_market_slug`, restarts polling |
| `handleRunSelect(run)` | Loads saved run from `/api/run/{id}` |
| `handleSortedOptionsChange(options)` | Updates `lastSortedMarketOptions` from MarketSelection |
| `handleKeyDown(e)` | Enter key triggers submit |

### Polling Effect

```typescript
useEffect(() => {
  // Runs when runId changes
  // Polls /api/run/{runId} every 1.5 seconds
  // Updates results and runStatus as phases complete
  // Stops when all phases are "done" or "error"
  // Uses pollingRef to prevent duplicate polling
}, [runId]);
```

**Polling Interval:** 1500ms (normal), 2500ms (on error), 3000ms (on 500 errors)

### Conditional Rendering Logic

```
if (!results) → EmptyPrompt
else if (requires_market_selection && !market_snapshot) → MarketSelection
else:
  if (runStatus.market === "pending") → MarketSnapshotSkeleton
  else if (runStatus.market === "done") → MarketSnapshotCard

  if (runStatus.news === "pending") → NewsSkeleton
  else if (runStatus.news === "done" && has_articles/summary) → NewsCard

  if (runStatus.signal === "pending") → SignalSkeleton
  else if (runStatus.signal === "done") → SignalCard

  if (runStatus.report === "pending") → ReportSkeleton
  else if (runStatus.report === "done") → ReportCard
```

---

## Task 3: Input Components

### UrlInputBar (`frontend/components/background/UrlInputBar.tsx`)

**Props:**
```typescript
type Props = {
  url: string;
  isSubmitting: boolean;
  isFocused: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  onFocusChange: (focused: boolean) => void;
};
```

**Styling:**
- Rounded-full pill shape with backdrop blur
- Blue border when focused, neutral when unfocused
- Disabled state during submission
- Icon changes color based on focus

**Submission:**
- Click submit button or Enter key
- Button disabled when empty or submitting

### ConfigurationPanel (`frontend/components/background/ConfigurationPanel.tsx`)

**AnalysisConfiguration Interface:**
```typescript
interface AnalysisConfiguration {
  useTavilyPromptAgent: boolean;    // AI-generated queries vs fallback
  useNewsSummaryAgent: boolean;     // AI-generated summary vs fallback
  maxArticles: number;              // 5-30
  maxArticlesPerQuery: number;      // 5-12
  minConfidence: "low" | "medium" | "high";
  enableSentimentAnalysis: boolean;
}
```

**DEFAULT_CONFIG:**
```typescript
{
  useTavilyPromptAgent: true,
  useNewsSummaryAgent: true,
  maxArticles: 15,
  maxArticlesPerQuery: 8,
  minConfidence: "medium",
  enableSentimentAnalysis: true,
}
```

**UI Components:**
- Toggle switches (custom CSS checkbox with peer selectors)
- Range sliders (native `<input type="range">`)
- Dropdown select for confidence
- Collapsible panel with expand/collapse button
- Reset to defaults button

---

## Task 4: Result Display Components

### MarketSnapshotCard (`frontend/components/MarketSnapshotCard.tsx`)

**Props:**
```typescript
type MarketSnapshotProps = {
  eventTitle: string;
  groupItemTitle?: string;           // e.g. "50+ bps decrease"
  polymarketUrl: string;
  closesIn: string;                  // preformatted, e.g. "23 days"
  endDate?: string;                  // ISO date for color calculation
  question?: string;
  previousMarkets?: PreviousMarketOption[];
  onMarketSelect?: (slug: string) => void;
  activeMarketSlug?: string;
  yesPrice: number;                  // 0-1
  noPrice: number;                   // 0-1
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
};
```

**Layout:** 2×3 CSS Grid
- Row 1: YES tile (green), NO tile (red), Metrics stack (volume, liquidity)
- Row 2: Order book snapshot, Comments, (empty)
- Footer: Tags + Polymarket link

**Market Dropdown:**
- Hover-triggered dropdown for `previousMarkets`
- Shows checkmark for active market
- Allows switching to other markets in the event

**Countdown Colors:**
- Red: < 1 day
- Yellow: 1-7 days
- Green: > 7 days

**Order Book Display:**
- Best bid/ask prices
- Spread calculation (absolute and % of mid)
- Top 3 levels depth sum
- "Bid-heavy" / "Ask-heavy" / "Balanced" label

### NewsCard (`frontend/components/NewsCard.tsx`)

**Props:**
```typescript
interface NewsCardProps {
  heading?: string;
  highlights: NewsItem[];
  isLoading?: boolean;
  onItemClick?: (item: NewsItem) => void;
  newsSummary?: string;
  combinedSummary?: string;
}

type NewsItem = {
  title: string;
  source?: string;
  publishedAt?: string;
  url?: string;
  summary?: string;
  sentiment?: "bullish" | "bearish" | "neutral";
};
```

**Tabs:**
1. **News** - List of article cards with sentiment badges
2. **Summary** - Sentiment breakdown bars + AI-generated summary

**Sentiment Color Coding:**
```typescript
const sentimentColors = {
  bearish: "text-red-600 bg-red-50",
  bullish: "text-green-600 bg-green-50",
  neutral: "text-slate-600 bg-slate-100",
};
```

**Sentiment Breakdown:**
- Visual progress bars for bullish/bearish/neutral percentages
- Calculated from article sentiment distribution

### SignalCard (`frontend/components/background/SignalCard.tsx`)

**Signal Type:**
```typescript
type Signal = {
  // New comprehensive fields
  market_prob?: number;
  model_prob?: number;
  edge_pct?: number;
  expected_value_per_dollar?: number;
  kelly_fraction_yes?: number;
  kelly_fraction_no?: number;
  confidence_level?: string;
  confidence_score?: number;
  recommended_action?: string;
  recommended_size_fraction?: number;
  target_take_profit_prob?: number;
  target_stop_loss_prob?: number;
  horizon?: string;
  rationale_short?: string;
  rationale_long?: string;
  // Legacy fields
  direction?: string;
  model_prob_abs?: number;
  confidence?: string;
  rationale?: string;
};
```

**Displayed Metrics:**
- Market Prob, Model Prob, Edge, Kelly Yes (4-column grid)
- Position Size (if non-zero)
- Confidence badge with score
- Take Profit / Stop Loss values
- Rationale text

**Action Label Mapping:**
- `buy_yes` → "BUY YES" (green)
- `buy_no` → "BUY NO" (red)
- `reduce_yes` → "REDUCE YES" (red)
- `reduce_no` → "REDUCE NO" (amber)
- `hold` → "HOLD" (grey)

**Color Scheme:** Entire card background changes based on action

### ReportCard (`frontend/components/background/ReportCard.tsx`)

**Report Types:**
```typescript
type StructuredReport = {
  headline?: string;
  thesis?: string;
  bull_case?: string[];
  bear_case?: string[];
  key_risks?: string[];
  execution_notes?: string;
  title?: string;       // legacy
  markdown?: string;    // legacy
};

type Report = string | StructuredReport | Record<string, unknown>;
```

**Sections:**
- Headline
- Thesis (3-5 sentences)
- Bull Case / Bear Case (side-by-side cards, green/red)
- Key Risks (amber card)
- Execution Notes

**Fallback:** Legacy markdown rendering if not structured

---

## Task 5: Skeleton Loading Components

### Common Pattern

All skeletons use:
- `animate-pulse` for shimmer effect
- Rounded shapes matching actual card layouts
- `bg-slate-200` / `bg-slate-100` placeholder colors
- Same card structure as actual components

### MarketSnapshotSkeleton
- Header with title placeholders
- 2×3 grid with colored placeholders for YES/NO tiles
- Footer placeholders

### NewsSkeleton
- Tab header placeholders
- 3 article card placeholders with source/title/snippet areas

### SignalSkeleton
- Header with action badge placeholder
- 4-column metrics grid placeholders
- Position size, confidence, rationale areas

### ReportSkeleton
- Header with image placeholder
- Headline, thesis, bull/bear case, key risks placeholders

---

## Task 6: Sidebar Components

### RecentSessions (`frontend/components/background/RecentSessions.tsx`)

**Props:**
```typescript
interface RecentSessionsProps {
  onRunSelect: (run: RecentRun) => void;
  activeRunId?: string;
  refreshTrigger?: number;  // Increment to trigger refresh
}
```

**State:**
- `runs: RecentRun[]` - list of recent runs
- `isLoading: boolean`
- `error: string | null`
- `abortControllerRef` - for cancelling pending requests

**Data Fetching:**
- GET `/api/runs/recent?limit=20`
- 30-second timeout
- AbortController for cleanup/cancellation

**Refresh Behavior:**
- Manual refresh button with spinning icon
- Auto-refresh via `refreshTrigger` prop
- `refreshTrigger` incremented when analysis completes

### RecentMarketCard (`frontend/components/background/RecentMarketCard.tsx`)

**RecentRun Interface:**
```typescript
interface RecentRun {
  _id: string;
  run_id?: string;
  slug?: string;
  polymarket_url?: string;
  run_at?: string;
  market_snapshot?: { question, yes_price, no_price };
  event_context?: { title };
  signal?: { direction, confidence, confidence_level };
  status?: { market, news, signal, report };
}
```

**Displays:**
- Question/title (2-line clamp)
- YES/NO prices
- Signal direction icon (TrendingUp/TrendingDown/Minus)
- Relative date ("5m ago", "2h ago", "3d ago")
- Confidence badge
- "Incomplete" badge if not all phases done

**Active Highlighting:**
- Blue background when `isActive` prop is true

### MarketSelection (`frontend/components/background/MarketSelection.tsx`)

**When Shown:**
- `results.requires_market_selection` is true
- `results.market_snapshot` is empty
- `results.market_options` has items

**Features:**
- Grid layout adapts to number of options (1-3: single row, 4: 2×2, 5: 3+2, 6+: 3-column)
- Sort dropdown: "Active (24h volume)", "Soonest to close", "Highest total volume"
- Hover effect with sliding background
- Calls `onSortedOptionsChange` to update parent state

**Sorting Logic:**
- "active": 24h volume → total volume → liquidity (descending), tie-break by end date
- "total": total volume → 24h volume → liquidity (descending), tie-break by end date
- "soonest": end date (ascending), tie-break by 24h volume

---

## Task 7: Navigation and Layout

### TopNav (`frontend/components/background/TopNav.tsx`)

**Content:**
- "prophily" branding text (Courier Prime bold font)
- Tavily logo
- OpenAI logo

**No Navigation Links** - single-page app

### GridAndNoise (`frontend/components/background/GridAndNoise.tsx`)

**Visual Effects:**
- `bg-grid` - CSS class for grid pattern (defined in globals.css)
- `bg-noise` - CSS class for noise texture
- Both positioned absolute with negative z-index
- Opacity: 40% grid, 20% noise

### EmptyPrompt (`frontend/components/background/EmptyPrompt.tsx`)

**Content:**
- Dashed border container
- Text: "Enter a Polymarket URL above to generate analysis."

---

## Task 8: API Client & Utilities

### API Utilities (`frontend/lib/api.ts`)

**Functions:**

```typescript
// Get backend URL based on environment
function getBackendUrl(): string
// - Uses BACKEND_URL env var if set
// - Development: http://localhost:8000
// - Production: https://tavily-backend-env.eba-jv6q9hd7.us-east-1.elasticbeanstalk.com

// Handle fetch errors
function handleFetchError(error: unknown): NextResponse

// Parse error response from backend
async function parseErrorResponse(response: Response): Promise<Record<string, unknown>>
```

### Logger (`frontend/lib/logger.ts`)

**Log Levels:**
```typescript
export const logger = {
  error: (...args: unknown[]) => void,
  warn: (...args: unknown[]) => void,
  info: (...args: unknown[]) => void,
  debug: (...args: unknown[]) => void,
};
```

**Behavior:**
- Development: logs to console
- Production: logs suppressed (placeholder for error tracking service)

**No Log Shipping:** Comment indicates Sentry integration as future enhancement

---

## Summary: Component Tree

```
app/layout.tsx (server)
└── app/page.tsx (client)
    └── Layout.tsx (client)
        └── Background.tsx (client, main dashboard)
            ├── GridAndNoise.tsx (background effects)
            │
            ├── TopNav.tsx (navigation/branding)
            │
            ├── RecentSessions.tsx (left sidebar)
            │   └── RecentMarketCard.tsx (per saved run)
            │
            ├── UrlInputBar.tsx (URL input)
            │
            ├── [Results Area]
            │   ├── EmptyPrompt.tsx (when no analysis)
            │   │
            │   ├── MarketSelection.tsx (when market selection required)
            │   │
            │   ├── MarketSnapshotCard.tsx | MarketSnapshotSkeleton.tsx
            │   ├── NewsCard.tsx | NewsSkeleton.tsx
            │   ├── SignalCard.tsx | SignalSkeleton.tsx
            │   └── ReportCard.tsx | ReportSkeleton.tsx
            │
            └── ConfigurationPanel.tsx (right sidebar)
```

## Summary: State Management Reference

| State | Type | Updated By | Used By |
|-------|------|-----------|---------|
| `url` | string | UrlInputBar onChange | handleSubmit, display |
| `isSubmitting` | boolean | handleSubmit, polling | All components (disable state) |
| `configuration` | AnalysisConfiguration | ConfigurationPanel | handleSubmit request body |
| `results` | AnalysisResults | Polling effect | All result cards |
| `runStatus` | object | Polling effect | Skeleton vs card rendering |
| `runId` | string | handleSubmit | Polling effect dependency |
| `selectedMarketSlug` | string | Polling effect, handleSelectMarket | MarketSnapshotCard active highlight |
| `selectedRunId` | string | handleRunSelect | RecentSessions active highlight |
| `lastSortedMarketOptions` | array | MarketSelection callback | MarketSnapshotCard dropdown |
| `recentSessionsRefreshTrigger` | number | Polling effect (on complete) | RecentSessions useEffect |

## Summary: API Routes Used

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/analyze/start` | POST | Start analysis, returns `run_id` |
| `/api/run/{runId}` | GET | Poll run status and results |
| `/api/runs/recent` | GET | Fetch recent sessions (limit=20) |

## Summary: Conditional Rendering Logic

```javascript
// Main rendering decision tree
if (!results) {
  return <EmptyPrompt />;
}

if (results.requires_market_selection &&
    !results.market_snapshot &&
    results.market_options?.length > 0) {
  return <MarketSelection />;
}

// For each card:
// Market
if (runStatus?.market === "done" && results.market_snapshot) {
  return <MarketSnapshotCard />;
} else if (runStatus?.market === "pending") {
  return <MarketSnapshotSkeleton />;
}

// News
if (runStatus?.news === "done" && hasNewsContent) {
  return <NewsCard />;
} else if (runStatus?.news === "pending") {
  return <NewsSkeleton />;
}

// Signal
if (runStatus?.signal === "done" && results.signal) {
  return <SignalCard />;
} else if (runStatus?.signal === "pending") {
  return <SignalSkeleton />;
}

// Report
if (runStatus?.report === "done" && results.report) {
  return <ReportCard />;
} else if (runStatus?.report === "pending") {
  return <ReportSkeleton />;
}
```
