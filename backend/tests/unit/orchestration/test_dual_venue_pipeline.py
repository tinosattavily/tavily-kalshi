from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import patch

import pytest

from app.api.schemas.requests import AnalyzeRequest
from app.orchestration.graph import run_analysis_graph
from app.orchestration.initial_state import build_initial_state


@contextmanager
def patch_downstream_agents():
    def preserve(state, **updates):
        return {**state, **updates}

    with (
        patch("app.orchestration.graph.run_event_agent", side_effect=lambda state: state),
        patch(
            "app.orchestration.graph.run_search_planner",
            side_effect=lambda state: preserve(state, tavily_queries=[]),
        ),
        patch(
            "app.orchestration.graph.run_article_fetcher",
            side_effect=lambda state: preserve(state, news_context={"articles": []}),
        ),
        patch(
            "app.orchestration.graph.run_summarizer",
            side_effect=lambda state: preserve(state, news_context={"articles": [], "summary": "No live fetch"}),
        ),
        patch(
            "app.orchestration.graph.run_probability_agent",
            side_effect=lambda state: preserve(state, signal={"direction": "yes"}),
        ),
        patch(
            "app.orchestration.graph.run_strategy_agent",
            side_effect=lambda state: preserve(state, decision={"action": "watch"}),
        ),
        patch(
            "app.orchestration.graph.run_report_agent",
            side_effect=lambda state: preserve(state, report={"headline": "Done"}),
        ),
    ):
        yield


@pytest.mark.anyio(backend="asyncio")
@pytest.mark.parametrize(
    ("market_url", "selected_market_id", "venue", "event_id"),
    [
        ("https://kalshi.com/markets/AAA-25JAN-B1", "AAA-25JAN-B1", "kalshi", "AAA-25JAN"),
        ("https://polymarket.com/market/test-market", "test-market", "polymarket", "test-event"),
    ],
)
async def test_dual_venue_graph_pipeline_keeps_market_identity(
    market_url: str,
    selected_market_id: str,
    venue: str,
    event_id: str,
):
    request = AnalyzeRequest(
        market_url=market_url,
        selected_market_id=selected_market_id,
        horizon="24h",
        strategy_preset="Balanced",
    )
    initial_state = build_initial_state(request)

    def preserve(state, **updates):
        return {**state, **updates}

    def market_agent(state):
        assert state["venue"] == venue
        assert state["selected_market_id"] == selected_market_id
        return preserve(
            state,
            market_id=selected_market_id,
            event_id=event_id,
            selected_market_id=selected_market_id,
            requires_market_selection=False,
            market_snapshot={
                "venue": venue,
                "market_id": selected_market_id,
                "question": "Will this resolve yes?",
                "yes_price": 0.42,
            },
            event_context={"venue": venue, "event_id": event_id, "title": "Test event"},
        )

    def news_agent(state):
        assert state["venue"] == venue
        assert state["market_id"] == selected_market_id
        return preserve(state, news_context={"articles": [], "summary": "No live fetch"})

    with (
        patch("app.orchestration.graph.run_market_agent", side_effect=market_agent) as mock_market,
        patch("app.orchestration.graph.run_event_agent", side_effect=lambda state: state),
        patch("app.orchestration.graph.run_search_planner", side_effect=lambda state: preserve(state, tavily_queries=[])),
        patch("app.orchestration.graph.run_article_fetcher", side_effect=news_agent),
        patch("app.orchestration.graph.run_summarizer", side_effect=news_agent),
        patch("app.orchestration.graph.run_probability_agent", side_effect=lambda state: preserve(state, signal={"direction": "yes"})),
        patch("app.orchestration.graph.run_strategy_agent", side_effect=lambda state: preserve(state, decision={"action": "watch"})),
        patch("app.orchestration.graph.run_report_agent", side_effect=lambda state: preserve(state, report={"headline": "Done"})),
    ):
        result = await run_analysis_graph(initial_state)

    assert mock_market.called
    assert result["venue"] == venue
    assert result["market_id"] == selected_market_id
    assert result["selected_market_id"] == selected_market_id
    assert result["market_snapshot"]["venue"] == venue
    assert result["report"]["headline"] == "Done"


@pytest.mark.anyio(backend="asyncio")
async def test_dual_venue_graph_runs_real_kalshi_adapter(monkeypatch):
    async def fake_get_market(ticker):
        assert ticker == "AAA-25JAN-B1"
        return {
            "ticker": "AAA-25JAN-B1",
            "event_ticker": "AAA-25JAN",
            "title": "Will Kalshi adapter run?",
            "yes_bid": 41,
            "yes_ask": 43,
            "last_price": 42,
            "volume": 123,
            "volume_24h": 45,
            "open_interest": 67,
        }

    async def fake_get_event(event_ticker):
        assert event_ticker == "AAA-25JAN"
        return {"event_ticker": "AAA-25JAN", "title": "Kalshi Event", "category": "Tests"}

    async def fake_get_orderbook(ticker):
        assert ticker == "AAA-25JAN-B1"
        return {"orderbook": {"yes": [[41, 10]], "no": [[57, 8]]}}

    async def fake_get_markets(event_ticker=None, status="open", limit=100):
        # The single-market path now also fetches sibling markets so the picker
        # chip can render. Stub it to return an empty list to keep this test
        # offline.
        return []

    monkeypatch.setattr("app.domains.markets.adapters.kalshi.get_market", fake_get_market)
    monkeypatch.setattr("app.domains.markets.adapters.kalshi.get_event", fake_get_event)
    monkeypatch.setattr("app.domains.markets.adapters.kalshi.get_orderbook", fake_get_orderbook)
    monkeypatch.setattr("app.domains.markets.adapters.kalshi.get_markets", fake_get_markets)

    request = AnalyzeRequest(
        market_url="https://kalshi.com/markets/AAA-25JAN-B1",
        selected_market_id="AAA-25JAN-B1",
    )
    with patch_downstream_agents():
        result = await run_analysis_graph(build_initial_state(request))

    assert result["venue"] == "kalshi"
    assert result["market_id"] == "AAA-25JAN-B1"
    assert result["event_id"] == "AAA-25JAN"
    assert result["market_snapshot"]["yes_price"] == pytest.approx(0.42)
    asks = result["market_snapshot"]["order_book"]["asks"]
    assert len(asks) == 1
    assert asks[0]["price"] == pytest.approx(0.43)
    assert asks[0]["size"] == 8


@pytest.mark.anyio(backend="asyncio")
async def test_dual_venue_graph_runs_real_polymarket_adapter(monkeypatch):
    class FakeMarketService:
        async def fetch_market_data(self, url, selected_market_id=None):
            assert selected_market_id == "test-market"
            return (
                {"slug": "test-event", "title": "Polymarket Event", "commentCount": 4},
                [
                    {
                        "slug": "test-market",
                        "id": "gamma-1",
                        "question": "Will Polymarket adapter run?",
                        "token_id": "token-1",
                        "bestBid": 0.48,
                        "bestAsk": 0.52,
                    }
                ],
                "test-market",
            )

        def is_event(self, markets):
            return False

        def extract_event_image(self, event, markets, selected_market, is_event):
            return None

        def update_event_metadata(self, event_state, event, event_image):
            return {"title": event["title"], "commentCount": event["commentCount"]}

        def extract_comment_count_from_market(self, selected_market, event_state):
            return event_state

        def extract_question(self, selected_market, markets, _existing_market, selected_slug):
            return selected_market["question"]

        def build_market_dict(
            self,
            *,
            slug,
            question,
            selected_market,
            gamma_market_id,
            polymarket_url,
            outcomes,
            yes_index,
            existing_market,
        ):
            return {
                "slug": slug,
                "question": question,
                "gamma_market_id": gamma_market_id,
                "polymarket_url": polymarket_url,
                "outcomes": outcomes,
                "yes_index": yes_index,
            }

        def build_snapshot(self, *, market, market_url, order_book, state, slug, api_market_record):
            return {
                "question": market["question"],
                "slug": slug,
                "url": market_url,
                "yes_price": 0.5,
                "order_book": order_book,
            }

    async def fake_orderbook(token_id):
        assert token_id == "token-1"
        return {"bids": [{"price": 0.48, "size": 10}], "asks": [{"price": 0.52, "size": 9}]}

    monkeypatch.setattr(
        "app.domains.markets.adapters.polymarket.get_market_service",
        lambda: FakeMarketService(),
    )
    monkeypatch.setattr(
        "app.domains.markets.adapters.polymarket.fetch_order_book_async",
        fake_orderbook,
    )

    request = AnalyzeRequest(
        market_url="https://polymarket.com/market/test-market",
        selected_market_id="test-market",
    )
    with patch_downstream_agents():
        result = await run_analysis_graph(build_initial_state(request))

    assert result["venue"] == "polymarket"
    assert result["market_id"] == "test-market"
    assert result["event_id"] == "test-event"
    assert result["market_snapshot"]["order_book"]["bids"] == [{"price": 0.48, "size": 10}]
