# prophecy-pred-markets

AI-driven analysis dashboard for Kalshi & Polymarket prediction markets. FastAPI backend, Next.js frontend.

**Live:** https://prophecy-pred-markets.vercel.app

## Optional Parallel news research

The backend uses Tavily for news research by default. To gather evidence for
Kalshi and Polymarket analysis with [Parallel Search MCP](https://docs.parallel.ai/integrations/mcp/search-mcp),
install the optional dependencies from the repository root:

```bash
python -m pip install -r backend/requirements-parallel.txt
```

Set `NEWS_SEARCH_PROVIDER=parallel` in the root `.env` file or backend environment,
then restart the backend. Parallel connects over Streamable HTTP to
`https://search.parallel.ai/mcp` without an account or API key. Anonymous search
uses Fast mode and is intended for exploration and light use, with service rate
limits. Other application credentials in `.env.example` still apply;
`TAVILY_API_KEY` is only needed for the Tavily provider.

Search excerpts flow into the existing article deduplication, sentiment and
summary pipeline. Parallel does not supply Tavily's answer summary or relevance
scores; publication dates can be absent. `max_results` limits the returned articles
locally, and Tavily's `search_depth` setting does not apply to Parallel. Search
failures leave that query without articles, following the existing news fetcher's
behavior. To switch back, set `NEWS_SEARCH_PROVIDER=tavily` (or unset it) and
configure `TAVILY_API_KEY`.
