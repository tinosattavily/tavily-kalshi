# Part 4: Frontend Architecture Exploration

> **For Claude:** This is a READ-ONLY exploration plan. Do not modify any files. Document findings as you go.

**Goal:** Understand the Next.js frontend architecture including component hierarchy, state management, polling logic, and UI patterns.

**Context:** Prophily uses Next.js 16 with React 19, TypeScript, and Tailwind CSS. The main dashboard shows real-time analysis results with skeleton loading states.

**Deliverable:** After completing this plan, produce a component diagram and state management reference.

---

## Task 1: Application Structure

**Files to read:**
- `frontend/app/layout.tsx`
- `frontend/app/page.tsx`
- `frontend/package.json`
- `frontend/tailwind.config.ts`

**Step 1: Read layout.tsx**

```bash
cat frontend/app/layout.tsx
```

**Document these findings:**
1. What is the root layout structure?
2. What fonts are loaded?
3. What metadata is set?
4. Are there any providers or context?

**Step 2: Read page.tsx**

```bash
cat frontend/app/page.tsx
```

**Document these findings:**
1. What is the home page structure?
2. What components are rendered?
3. Is it a server or client component?

**Step 3: Read package.json**

```bash
cat frontend/package.json
```

**Document these findings:**
1. What is the Next.js version?
2. What is the React version?
3. What key dependencies are used?
   - UI libraries?
   - State management?
   - HTTP client?
4. What scripts are available?

**Step 4: Read tailwind.config.ts**

```bash
cat frontend/tailwind.config.ts
```

**Document these findings:**
1. What custom colors are defined?
2. What custom fonts are used?
3. Any custom utilities?

---

## Task 2: Main Dashboard Component

**Files to read:**
- `frontend/components/Background.tsx`

**Step 1: Read Background.tsx (full analysis)**

```bash
cat frontend/components/Background.tsx
```

**Document these findings:**

**Component Structure:**
1. What is the overall layout? (grid structure)
2. What child components are rendered?
3. How is the 3-column layout implemented?

**State Variables:**
```typescript
// Document each state variable:
url: string                    // ?
isSubmitting: boolean          // ?
configuration: AnalysisConfiguration // ?
results: AnalysisResults       // ?
runStatus: object              // ?
runId: string                  // ?
selectedMarketSlug: string     // ?
selectedRunId: string          // ?
pollingRef: React.MutableRefObject // ?
```

**Key Handlers:**
1. `handleSubmit()` - What does it do?
2. `handleSelectMarket()` - What does it do?
3. `handleRunSelect()` - What does it do?
4. `handleSortedOptionsChange()` - What does it do?

**Conditional Rendering:**
1. When is `MarketSelection` shown?
2. When is `EmptyPrompt` shown?
3. When are skeletons shown vs actual cards?

---

## Task 3: Input Components

**Files to read:**
- `frontend/components/background/UrlInputBar.tsx`
- `frontend/components/background/ConfigurationPanel.tsx`

**Step 1: Read UrlInputBar.tsx**

```bash
cat frontend/components/background/UrlInputBar.tsx
```

**Document these findings:**
1. What props does it accept?
2. How is the input styled?
3. How is submission triggered?
4. What loading state is shown?

**Step 2: Read ConfigurationPanel.tsx**

```bash
cat frontend/components/background/ConfigurationPanel.tsx
```

**Document these findings:**
1. What is `AnalysisConfiguration` interface?
2. What is `DEFAULT_CONFIG`?
3. What configuration options are available?
   - `useTavilyPromptAgent`
   - `useNewsSummaryAgent`
   - `maxArticles`
   - `maxArticlesPerQuery`
   - `minConfidence`
   - `enableSentimentAnalysis`
4. How are toggles and sliders implemented?

---

## Task 4: Result Display Components

**Files to read:**
- `frontend/components/MarketSnapshotCard.tsx`
- `frontend/components/NewsCard.tsx`
- `frontend/components/background/SignalCard.tsx`
- `frontend/components/background/DecisionCard.tsx`
- `frontend/components/background/ReportCard.tsx`

**Step 1: Read MarketSnapshotCard.tsx**

```bash
cat frontend/components/MarketSnapshotCard.tsx
```

**Document these findings:**
1. What props does it accept?
2. What market data is displayed?
   - Event title
   - Question
   - Yes/No prices
   - Volume, liquidity
   - Order book visualization?
3. How is the previous markets dropdown implemented?
4. How is the price display formatted?

**Step 2: Read NewsCard.tsx**

```bash
cat frontend/components/NewsCard.tsx
```

**Document these findings:**
1. What props does it accept?
2. How are articles displayed?
3. How is sentiment shown? (color coding?)
4. How is the summary displayed?
5. How are article links handled?

**Step 3: Read SignalCard.tsx**

```bash
cat frontend/components/background/SignalCard.tsx
```

**Document these findings:**
1. What props does it accept?
2. How is direction displayed? (up/down/flat)
3. How is confidence displayed?
4. How is probability displayed?
5. How is the rationale formatted?

**Step 4: Read DecisionCard.tsx**

```bash
cat frontend/components/background/DecisionCard.tsx
```

**Document these findings:**
1. What props does it accept?
2. How is action displayed? (BUY/SELL/HOLD)
3. How is edge percentage shown?
4. How is Kelly fraction displayed?

**Step 5: Read ReportCard.tsx**

```bash
cat frontend/components/background/ReportCard.tsx
```

**Document these findings:**
1. What props does it accept?
2. How is markdown rendered?
3. How are bull/bear cases displayed?
4. How are key risks shown?

---

## Task 5: Skeleton Loading Components

**Files to read:**
- `frontend/components/skeletons/MarketSnapshotSkeleton.tsx`
- `frontend/components/skeletons/NewsSkeleton.tsx`
- `frontend/components/skeletons/SignalSkeleton.tsx`
- `frontend/components/skeletons/ReportSkeleton.tsx`

**Step 1: Read all skeleton files**

```bash
cat frontend/components/skeletons/MarketSnapshotSkeleton.tsx
cat frontend/components/skeletons/NewsSkeleton.tsx
cat frontend/components/skeletons/SignalSkeleton.tsx
cat frontend/components/skeletons/ReportSkeleton.tsx
```

**Document these findings:**
1. What is the skeleton pattern used?
2. How are pulse animations implemented?
3. Do skeletons match the actual card layouts?

---

## Task 6: Sidebar Components

**Files to read:**
- `frontend/components/background/RecentSessions.tsx`
- `frontend/components/background/RecentMarketCard.tsx`
- `frontend/components/background/MarketSelection.tsx`

**Step 1: Read RecentSessions.tsx**

```bash
cat frontend/components/background/RecentSessions.tsx
```

**Document these findings:**
1. How does it fetch recent runs?
2. How is the list rendered?
3. How is run selection handled?
4. What is `refreshTrigger` for?

**Step 2: Read RecentMarketCard.tsx**

```bash
cat frontend/components/background/RecentMarketCard.tsx
```

**Document these findings:**
1. What is the `RecentRun` interface?
2. What data is displayed per run?
3. How is the active run highlighted?

**Step 3: Read MarketSelection.tsx**

```bash
cat frontend/components/background/MarketSelection.tsx
```

**Document these findings:**
1. When is this component shown?
2. How are market options displayed?
3. How is selection handled?
4. How is sorting implemented?

---

## Task 7: Navigation and Layout

**Files to read:**
- `frontend/components/background/TopNav.tsx`
- `frontend/components/background/GridAndNoise.tsx`
- `frontend/components/background/EmptyPrompt.tsx`

**Step 1: Read TopNav.tsx**

```bash
cat frontend/components/background/TopNav.tsx
```

**Document these findings:**
1. What navigation items exist?
2. How is branding displayed?

**Step 2: Read GridAndNoise.tsx**

```bash
cat frontend/components/background/GridAndNoise.tsx
```

**Document these findings:**
1. What visual effects are implemented?
2. How is the grid pattern created?

**Step 3: Read EmptyPrompt.tsx**

```bash
cat frontend/components/background/EmptyPrompt.tsx
```

**Document these findings:**
1. What is shown when no analysis is active?
2. What instructions are provided?

---

## Task 8: API Client & Utilities

**Files to read:**
- `frontend/lib/api.ts`
- `frontend/lib/logger.ts`

**Step 1: Read api.ts**

```bash
cat frontend/lib/api.ts
```

**Document these findings:**
1. What API helper functions exist?
2. How is the backend URL configured?
3. Are there any shared fetch wrappers?

**Step 2: Read logger.ts**

```bash
cat frontend/lib/logger.ts
```

**Document these findings:**
1. How is client-side logging implemented?
2. What log levels are used?
3. Is there any log shipping?

---

## Summary Output

After completing all tasks, create:

### Component Tree

```
app/layout.tsx
└── app/page.tsx
    └── Background.tsx (client component)
        ├── GridAndNoise.tsx (background effects)
        ├── TopNav.tsx (navigation)
        │
        ├── RecentSessions.tsx (left sidebar)
        │   └── RecentMarketCard.tsx (per run)
        │
        ├── UrlInputBar.tsx (URL input)
        │
        ├── [Results Area]
        │   ├── EmptyPrompt.tsx (no analysis)
        │   ├── MarketSelection.tsx (choose market)
        │   │
        │   ├── MarketSnapshotCard.tsx | MarketSnapshotSkeleton.tsx
        │   ├── NewsCard.tsx | NewsSkeleton.tsx
        │   ├── SignalCard.tsx | SignalSkeleton.tsx
        │   ├── DecisionCard.tsx
        │   └── ReportCard.tsx | ReportSkeleton.tsx
        │
        └── ConfigurationPanel.tsx (right sidebar)
```

### State Management Reference

| State | Type | Updated By | Used By |
|-------|------|-----------|---------|
| `url` | string | UrlInputBar | handleSubmit |
| `isSubmitting` | boolean | submit/polling | UI loading states |
| `results` | AnalysisResults | polling effect | All result cards |
| `runStatus` | object | polling effect | Skeleton vs card logic |
| `runId` | string | handleSubmit | polling effect |
| `configuration` | object | ConfigurationPanel | handleSubmit |

### Conditional Rendering Logic

```
if (!results) → EmptyPrompt
else if (requires_market_selection) → MarketSelection
else:
  if (runStatus.market === "pending") → MarketSnapshotSkeleton
  else if (runStatus.market === "done") → MarketSnapshotCard

  if (runStatus.news === "pending") → NewsSkeleton
  else if (runStatus.news === "done") → NewsCard

  // ... similar for signal and report
```
