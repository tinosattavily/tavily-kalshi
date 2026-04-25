"""Tests for the venue-backed market agent behavior."""

from __future__ import annotations

import pytest

from app.orchestration.agents.market import run_market_agent
from app.orchestration.state import AgentState


class StubAdapter:
    venue = "polymarket"

    def __init__(self, result):
        self.result = result
        self.selected_market_id = None

    async def fetch(self, url, selected_market_id=None):
        self.selected_market_id = selected_market_id
        return dict(self.result)


@pytest.mark.anyio(backend="asyncio")
async def test_run_market_agent_single_market(monkeypatch):
    adapter = StubAdapter(
        {
            "venue": "polymarket",
            "raw_url": "https://polymarket.com/market/test-market",
            "canonical_url": "https://polymarket.com/market/test-market",
            "market_id": "test-market",
            "event_id": "test-event",
            "selected_market_id": "test-market",
            "requires_market_selection": False,
            "market": {"slug": "test-market", "question": "Will this test pass?"},
            "event": {"title": "Test Event", "commentCount": 10},
            "market_snapshot": {
                "venue": "polymarket",
                "market_id": "test-market",
                "question": "Will this test pass?",
                "yes_price": 0.5,
                "order_book": {"bids": [], "asks": []},
            },
            "event_context": {"title": "Test Event", "commentCount": 10},
        }
    )
    monkeypatch.setattr("app.orchestration.agents.market.get_adapter_for_url", lambda url: adapter)

    result = await run_market_agent({"market_url": "https://polymarket.com/market/test-market"})

    assert result["slug"] == "test-market"
    assert result["market_id"] == "test-market"
    assert result["selected_market_id"] == "test-market"
    assert result["selected_market_slug"] == "test-market"
    assert result["market_snapshot"]["question"] == "Will this test pass?"
    assert result["event_context"]["commentCount"] == 10


@pytest.mark.anyio(backend="asyncio")
async def test_run_market_agent_event_requires_selection(monkeypatch):
    adapter = StubAdapter(
        {
            "venue": "kalshi",
            "raw_url": "https://kalshi.com/events/AAA-25JAN",
            "canonical_url": "https://kalshi.com/events/AAA-25JAN",
            "event_id": "AAA-25JAN",
            "requires_market_selection": True,
            "market_options": [
                {"venue": "kalshi", "market_id": "AAA-25JAN-B1", "label": "Market 1?"},
                {"venue": "kalshi", "market_id": "AAA-25JAN-B2", "label": "Market 2?"},
            ],
            "event": {"title": "Test Event", "image": "https://example.com/image.png"},
            "event_context": {"title": "Test Event", "image": "https://example.com/image.png"},
        }
    )
    monkeypatch.setattr("app.orchestration.agents.market.get_adapter_for_url", lambda url: adapter)

    result = await run_market_agent({"market_url": "https://kalshi.com/events/AAA-25JAN"})

    assert result["requires_market_selection"] is True
    assert result["market_options"][0]["market_id"] == "AAA-25JAN-B1"
    assert result["event_context"]["image"] == "https://example.com/image.png"


@pytest.mark.anyio(backend="asyncio")
async def test_run_market_agent_passes_selected_market_id(monkeypatch):
    adapter = StubAdapter(
        {
            "venue": "kalshi",
            "raw_url": "https://kalshi.com/events/AAA-25JAN",
            "canonical_url": "https://kalshi.com/markets/AAA-25JAN-B2",
            "market_id": "AAA-25JAN-B2",
            "event_id": "AAA-25JAN",
            "selected_market_id": "AAA-25JAN-B2",
            "requires_market_selection": False,
            "market": {"ticker": "AAA-25JAN-B2", "question": "Market 2?"},
            "event": {"title": "Test Event"},
            "market_snapshot": {"venue": "kalshi", "market_id": "AAA-25JAN-B2", "question": "Market 2?"},
            "event_context": {"title": "Test Event"},
        }
    )
    monkeypatch.setattr("app.orchestration.agents.market.get_adapter_for_url", lambda url: adapter)

    state: AgentState = {
        "market_url": "https://kalshi.com/events/AAA-25JAN",
        "selected_market_id": "AAA-25JAN-B2",
    }
    result = await run_market_agent(state)

    assert adapter.selected_market_id == "AAA-25JAN-B2"
    assert result["ticker"] == "AAA-25JAN-B2"
    assert result["selected_ticker"] == "AAA-25JAN-B2"
    assert result["market_snapshot"]["question"] == "Market 2?"


@pytest.mark.anyio(backend="asyncio")
async def test_run_market_agent_uses_legacy_selection_fields(monkeypatch):
    adapter = StubAdapter(
        {
            "venue": "polymarket",
            "raw_url": "https://polymarket.com/event/test-event",
            "canonical_url": "https://polymarket.com/market/test-event-market-2",
            "market_id": "test-event-market-2",
            "event_id": "test-event",
            "selected_market_id": "test-event-market-2",
            "requires_market_selection": False,
            "market": {"slug": "test-event-market-2", "question": "Market 2?"},
            "event": {"title": "Test Event"},
            "market_snapshot": {
                "venue": "polymarket",
                "market_id": "test-event-market-2",
                "question": "Market 2?",
            },
            "event_context": {"title": "Test Event"},
        }
    )
    monkeypatch.setattr("app.orchestration.agents.market.get_adapter_for_url", lambda url: adapter)

    result = await run_market_agent(
        {
            "market_url": "https://polymarket.com/event/test-event",
            "selected_market_slug": "test-event-market-2",
        }
    )

    assert adapter.selected_market_id == "test-event-market-2"
    assert result["selected_market_slug"] == "test-event-market-2"


@pytest.mark.anyio(backend="asyncio")
async def test_run_market_agent_missing_url_raises():
    with pytest.raises(ValueError, match="market_url is required"):
        await run_market_agent({})
