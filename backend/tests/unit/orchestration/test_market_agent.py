import pytest

from app.orchestration.agents.market import run_market_agent


@pytest.mark.asyncio
async def test_market_agent_uses_adapter_result(monkeypatch):
    class Adapter:
        venue = "kalshi"

        async def fetch(self, url, selected_market_id=None):
            return {
                "venue": "kalshi",
                "raw_url": url,
                "canonical_url": "https://kalshi.com/markets/AAA-1",
                "market_id": "AAA-1",
                "event_id": "AAA",
                "selected_market_id": "AAA-1",
                "requires_market_selection": False,
                "market_options": [],
                "market": {"question": "A?"},
                "event": {"title": "Event"},
                "market_snapshot": {"question": "A?", "yes_price": 0.42},
                "event_context": {"title": "Event"},
            }

    monkeypatch.setattr(
        "app.orchestration.agents.market.get_adapter_for_url",
        lambda url: Adapter(),
    )

    state = await run_market_agent({"market_url": "https://kalshi.com/markets/AAA-1"})
    assert state["venue"] == "kalshi"
    assert state["market_id"] == "AAA-1"
    assert state["market_snapshot"]["yes_price"] == 0.42


@pytest.mark.asyncio
async def test_market_agent_preserves_selection_pause(monkeypatch):
    class Adapter:
        venue = "kalshi"

        async def fetch(self, url, selected_market_id=None):
            return {
                "venue": "kalshi",
                "raw_url": url,
                "canonical_url": url,
                "event_id": "AAA",
                "requires_market_selection": True,
                "market_options": [{"market_id": "AAA-1", "label": "A"}],
                "event_context": {"title": "Event"},
            }

    monkeypatch.setattr(
        "app.orchestration.agents.market.get_adapter_for_url",
        lambda url: Adapter(),
    )

    state = await run_market_agent({"market_url": "https://kalshi.com/events/AAA"})
    assert state["requires_market_selection"] is True
    assert state["market_options"][0]["market_id"] == "AAA-1"
