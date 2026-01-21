# Backend Restructuring Design

**Date:** 2026-01-21
**Status:** Approved
**Approach:** Domain-Driven Structure

## Overview

Restructure the backend to improve maintainability, readability, scalability, and testability. The codebase will be organized by business domain, with clear separation between orchestration, infrastructure, and API layers.

## Goals

- Clean, compartmentalized agentic flow
- Clean database management
- Easy-to-navigate config for envs/keys
- Organized utilities
- Large files chunked into maintainable pieces

## New Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Slim FastAPI entry (~50 lines)
│   │
│   ├── config/                    # All configuration
│   │   ├── __init__.py
│   │   ├── settings.py            # Environment variables
│   │   ├── constants.py           # API endpoints, magic numbers
│   │   └── logging.py             # Logging configuration
│   │
│   ├── domains/                   # Business domains
│   │   ├── markets/               # Polymarket data
│   │   ├── news/                  # News aggregation
│   │   ├── analysis/              # Signal generation
│   │   └── reports/               # Report generation
│   │
│   ├── orchestration/             # Agent graph and workflow
│   │   ├── __init__.py
│   │   ├── state.py
│   │   ├── graph.py
│   │   ├── phased.py
│   │   ├── snapshot.py
│   │   └── agents/
│   │
│   ├── infrastructure/            # External integrations
│   │   ├── database/
│   │   ├── http/
│   │   └── llm/
│   │
│   ├── api/                       # HTTP layer
│   │   ├── routes/
│   │   ├── schemas/
│   │   └── dependencies.py
│   │
│   └── shared/                    # Cross-cutting utilities
│       ├── types.py
│       └── exceptions.py
│
└── tests/                         # Mirrors app/ structure
    ├── conftest.py
    ├── unit/
    └── integration/
```

---

## Complete File Mapping

### Config

| From | To |
|------|-----|
| `app/config.py` (lines 1-41) | `app/config/settings.py` |
| `app/config.py` (lines 44-52) | `app/config/constants.py` |
| `app/core/logging_config.py` | `app/config/logging.py` |

### Infrastructure

| From | To |
|------|-----|
| `app/db/async_client.py` | `app/infrastructure/database/client.py` |
| `app/db/async_repositories.py` | `app/infrastructure/database/repositories.py` |
| `app/db/client.py` | *REMOVE* (verify unused first) |
| `app/db/repositories.py` | *REMOVE* (verify unused first) |
| `app/db/utils.py` | `app/infrastructure/database/utils.py` |
| `app/core/cache.py` | `app/infrastructure/http/cache.py` |
| `app/core/resilience.py` | `app/infrastructure/http/resilience.py` |
| `app/services/polymarket_client.py` | `app/infrastructure/http/polymarket.py` |
| `app/services/tavily_client.py` | `app/infrastructure/http/tavily.py` |
| `app/services/openai_client.py` | `app/infrastructure/llm/client.py` |

### Markets Domain

| From | To |
|------|-----|
| `app/schemas/polymarket.py` | `app/domains/markets/schemas.py` |
| `app/core/polymarket_utils.py` (URL/price parsing) | `app/domains/markets/parsing.py` |
| `app/core/polymarket_utils.py` (get_event_and_markets) | `app/domains/markets/fetcher.py` |
| `app/core/polymarket_utils.py` (async HTTP) | `app/infrastructure/http/polymarket.py` |
| `app/core/market_transformer.py` | `app/domains/markets/transformer.py` |
| `app/core/market_selector.py` | `app/domains/markets/selector.py` |
| `app/agents/market_agent.py` (logic) | `app/domains/markets/service.py` |
| `app/agents/event_agent.py` (logic) | `app/domains/markets/event_service.py` |

**Markets domain structure:**
```
app/domains/markets/
├── __init__.py
├── schemas.py          # Pydantic models
├── parsing.py          # URL/price parsing
├── fetcher.py          # API data fetching
├── transformer.py      # Data transformation
├── selector.py         # Market selection
├── service.py          # MarketService
└── event_service.py    # EventService
```

### News Domain

| From | To |
|------|-----|
| `app/schemas/tavily.py` | `app/domains/news/schemas.py` |
| `app/agents/tavily_prompt_agent.py` (logic) | `app/domains/news/query_generator.py` |
| `app/agents/news_agent.py` (fetching) | `app/domains/news/fetcher.py` |
| `app/agents/news_agent.py` (orchestration) | `app/domains/news/service.py` |
| `app/agents/news_summary_agent.py` (logic) | `app/domains/news/summarizer.py` |
| `app/core/sentiment_analyzer.py` (patterns) | `app/domains/news/sentiment/patterns.py` |
| `app/core/sentiment_analyzer.py` (logic) | `app/domains/news/sentiment/analyzer.py` |

**News domain structure:**
```
app/domains/news/
├── __init__.py
├── schemas.py              # Pydantic models
├── query_generator.py      # Search query generation
├── fetcher.py              # Article fetching
├── summarizer.py           # News summarization
├── service.py              # NewsService
└── sentiment/
    ├── __init__.py         # Facade
    ├── patterns.py         # BULLISH_PATTERNS, BEARISH_PATTERNS, NEGATION_WORDS
    └── analyzer.py         # Matching logic
```

### Analysis Domain

| From | To |
|------|-----|
| `app/schemas/api.py` (Signal, StrategyParamsModel) | `app/domains/analysis/schemas.py` |
| `app/core/signal_utils.py` | `app/domains/analysis/calculations.py` |
| `app/agents/prob_agent.py` (logic) | `app/domains/analysis/probability.py` |
| `app/agents/strategy_agent.py` (presets) | `app/domains/analysis/presets.py` |
| `app/agents/strategy_agent.py` (sizing) | `app/domains/analysis/sizing.py` |
| `app/agents/strategy_agent.py` (decisions) | `app/domains/analysis/decision.py` |
| `app/agents/strategy_agent.py` (orchestration) | `app/domains/analysis/service.py` |

**Analysis domain structure:**
```
app/domains/analysis/
├── __init__.py
├── schemas.py              # Signal, StrategyParamsModel
├── calculations.py         # Edge, Kelly, EV math
├── presets.py              # CAUTIOUS, BALANCED, AGGRESSIVE
├── sizing.py               # Position sizing
├── decision.py             # Buy/sell/hold rules
├── probability.py          # Model probability estimation
└── service.py              # AnalysisService
```

### Reports Domain

| From | To |
|------|-----|
| `app/schemas/api.py` (ReportSection) | `app/domains/reports/schemas.py` |
| `app/agents/report_agent.py` (prompts) | `app/domains/reports/prompts.py` |
| `app/agents/report_agent.py` (templates) | `app/domains/reports/templates.py` |
| `app/agents/report_agent.py` (LLM gen) | `app/domains/reports/generator.py` |
| `app/agents/report_agent.py` (formatting) | `app/domains/reports/formatter.py` |
| `app/agents/report_agent.py` (orchestration) | `app/domains/reports/service.py` |

**Reports domain structure:**
```
app/domains/reports/
├── __init__.py
├── schemas.py              # ReportSection, ReportBlock
├── prompts.py              # LLM prompt strings
├── templates.py            # Fallback templates
├── generator.py            # LLM-based generation
├── formatter.py            # Output formatting
└── service.py              # ReportService
```

### Orchestration

| From | To |
|------|-----|
| `app/agents/state.py` | `app/orchestration/state.py` |
| `app/agents/graph.py` | `app/orchestration/graph.py` |
| `app/services/phased_analysis.py` | `app/orchestration/phased.py` |
| `app/services/run_snapshot.py` | `app/orchestration/snapshot.py` |
| `app/agents/market_agent.py` (wrapper) | `app/orchestration/agents/market.py` |
| `app/agents/event_agent.py` (wrapper) | `app/orchestration/agents/event.py` |
| `app/agents/tavily_prompt_agent.py` (wrapper) | `app/orchestration/agents/search_planner.py` |
| `app/agents/news_agent.py` (wrapper) | `app/orchestration/agents/article_fetcher.py` |
| `app/agents/news_summary_agent.py` (wrapper) | `app/orchestration/agents/summarizer.py` |
| `app/agents/prob_agent.py` (wrapper) | `app/orchestration/agents/probability.py` |
| `app/agents/strategy_agent.py` (wrapper) | `app/orchestration/agents/strategy.py` |
| `app/agents/report_agent.py` (wrapper) | `app/orchestration/agents/report.py` |

**Orchestration structure:**
```
app/orchestration/
├── __init__.py
├── state.py                # AgentState TypedDict
├── graph.py                # LangGraph build + run
├── phased.py               # Phased analysis
├── snapshot.py             # Run persistence
└── agents/                 # Thin wrappers
    ├── __init__.py
    ├── market.py
    ├── event.py
    ├── search_planner.py
    ├── article_fetcher.py
    ├── summarizer.py
    ├── probability.py
    ├── strategy.py
    └── report.py
```

### API Layer

| From | To |
|------|-----|
| `app/routes/analyze.py` | `app/api/routes/analyze.py` |
| `app/routes/runs.py` | `app/api/routes/runs.py` |
| `app/main.py` (health endpoints) | `app/api/routes/health.py` |
| `app/core/dependencies.py` | `app/api/dependencies.py` |
| `app/schemas/api.py` (requests) | `app/api/schemas/requests.py` |
| `app/schemas/api.py` (responses) | `app/api/schemas/responses.py` |
| `app/schemas/api.py` (common) | `app/api/schemas/common.py` |
| `app/schemas/__init__.py` | `app/api/schemas/__init__.py` |

**API structure:**
```
app/api/
├── __init__.py
├── dependencies.py
├── routes/
│   ├── __init__.py
│   ├── analyze.py
│   ├── runs.py
│   └── health.py
└── schemas/
    ├── __init__.py
    ├── requests.py
    ├── responses.py
    └── common.py
```

### Shared

| From | To |
|------|-----|
| `app/db/models.py` | `app/shared/types.py` |
| *(new)* | `app/shared/exceptions.py` |

### Root Level (unchanged)

| File | Status |
|------|--------|
| `app/main.py` | Stays (slimmed) |
| `dev_server.py` | Stays |
| `test_tavily.py` | Move to `scripts/` |
| `requirements.txt` | Stays |
| `pyproject.toml` | Stays |
| `Procfile` | Stays |
| `runtime.txt` | Stays |

### Tests

```
backend/tests/
├── conftest.py             # Shared fixtures
├── unit/
│   ├── domains/
│   │   ├── markets/
│   │   ├── news/
│   │   ├── analysis/
│   │   └── reports/
│   ├── orchestration/
│   ├── infrastructure/
│   └── api/
└── integration/
```

---

## Files to Remove (after verification)

- `app/db/client.py` - Sync MongoDB client (verify unused)
- `app/db/repositories.py` - Sync repositories (verify unused)

---

## Key Principles

1. **Domains own logic** - Business logic lives in domain services, not agents
2. **Agents are thin wrappers** - Extract state, call domain, update state (~20-40 lines each)
3. **Infrastructure is isolated** - External APIs, DB, caching separated from business logic
4. **Config in one place** - All env vars, constants, logging in `config/`
5. **Schemas near their domain** - Domain-specific Pydantic models live with their domain

---

## Implementation Order

1. **Phase 1: Setup structure** - Create directories and `__init__.py` files
2. **Phase 2: Config** - Move and consolidate configuration
3. **Phase 3: Shared** - Move TypedDicts to shared/types.py
4. **Phase 4: Infrastructure** - Move DB, HTTP, LLM clients
5. **Phase 5: Domains** - Move and split domain logic (markets → news → analysis → reports)
6. **Phase 6: Orchestration** - Move state, graph, create thin agent wrappers
7. **Phase 7: API** - Move routes, schemas, dependencies
8. **Phase 8: Cleanup** - Remove old directories, update imports, verify tests
9. **Phase 9: Tests** - Reorganize tests to mirror new structure

---

## Import Path Changes

```python
# Before
from app.config import settings, PolymarketAPI
from app.core.logging_config import get_logger
from app.db.async_client import get_async_db
from app.agents.market_agent import run_market_agent

# After
from app.config import settings, PolymarketAPI, get_logger
from app.infrastructure.database import get_async_db
from app.orchestration.agents.market import run_market_agent
from app.domains.markets.service import MarketService
```

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking imports | Update imports incrementally, run tests after each phase |
| Missing code during move | Complete file mapping above ensures nothing lost |
| Circular imports | Domains depend on shared, never on each other |
| Test failures | Run full test suite after each phase |
