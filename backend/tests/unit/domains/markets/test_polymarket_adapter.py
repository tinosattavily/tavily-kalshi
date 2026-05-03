import pytest

from app.domains.markets.adapters.polymarket import PolymarketAdapter


@pytest.mark.asyncio
async def test_polymarket_adapter_requires_selection(monkeypatch):
    adapter = PolymarketAdapter()

    class FakeService:
        def is_event(self, markets):
            return True

        async def fetch_market_data(self, market_url, slug=None):
            return {"slug": "event", "title": "Event"}, [
                {"slug": "a", "question": "A?", "outcomePrices": '["0.4","0.6"]'},
                {"slug": "b", "question": "B?", "outcomePrices": '["0.5","0.5"]'},
            ], "event"

        def build_options(self, markets):
            return [{"slug": m["slug"], "question": m["question"]} for m in markets]

        def select_market(self, markets, selected_slug, url_slug):
            return None, None, True

        def update_event_metadata(self, event_state, event, event_image):
            return {"title": event["title"], "slug": event["slug"]}

    monkeypatch.setattr(
        "app.domains.markets.adapters.polymarket.get_market_service",
        lambda: FakeService(),
    )

    result = await adapter.fetch("https://polymarket.com/event/event")
    assert result["venue"] == "polymarket"
    assert result["requires_market_selection"] is True
    assert result["market_options"][0]["market_id"] == "a"
    assert result["market_options"][0]["label"] == "A?"


@pytest.mark.asyncio
async def test_polymarket_adapter_normalizes_selected_market(monkeypatch):
    adapter = PolymarketAdapter()

    class FakeService:
        def is_event(self, markets):
            return False

        async def fetch_market_data(self, market_url, slug=None):
            return {"slug": "event", "title": "Event"}, [
                {
                    "slug": "market-a",
                    "question": "Market A?",
                    "outcomePrices": '["0.42","0.58"]',
                    "id": "123",
                }
            ], "market-a"

        def find_market(self, markets, selected_slug):
            return next((m for m in markets if m.get("slug") == selected_slug), None)

        def extract_event_image(self, event, markets, selected_market, is_event):
            return None

        def update_event_metadata(self, event_state, event, event_image):
            return {"title": event["title"], "slug": event["slug"]}

        def extract_comment_count_from_market(self, selected_market, event_state):
            return event_state

        def extract_question(self, selected_market, markets, state_question, slug):
            return selected_market["question"]

        def build_market_dict(self, **kwargs):
            return {
                "slug": kwargs["slug"],
                "question": kwargs["question"],
                "polymarket_url": kwargs["polymarket_url"],
                "gamma_market_id": kwargs["gamma_market_id"],
                "outcomes": ["Yes", "No"],
                "yes_index": 0,
            }

        def build_snapshot(self, **kwargs):
            return {
                "slug": "market-a",
                "url": kwargs["market_url"],
                "question": "Market A?",
                "yes_price": 0.42,
                "best_bid": 0.41,
                "best_ask": 0.43,
            }

    monkeypatch.setattr(
        "app.domains.markets.adapters.polymarket.get_market_service",
        lambda: FakeService(),
    )
    monkeypatch.setattr(
        "app.domains.markets.adapters.polymarket.fetch_order_book_async",
        lambda token_id: {},
    )

    result = await adapter.fetch("https://polymarket.com/market/market-a")
    assert result["venue"] == "polymarket"
    assert result["market_id"] == "market-a"
    assert result["market_snapshot"]["yes_price"] == 0.42


@pytest.mark.asyncio
async def test_polymarket_adapter_single_market_auto_resolves(monkeypatch):
    adapter = PolymarketAdapter()

    class FakeService:
        def is_event(self, markets):
            return False

        async def fetch_market_data(self, market_url, slug=None):
            return {"slug": "event", "title": "Event"}, [
                {"slug": "only-market", "question": "Only?", "outcomePrices": '["0.6","0.4"]'}
            ], "event"

        def extract_event_image(self, event, markets, selected_market, is_event):
            return None

        def update_event_metadata(self, event_state, event, event_image):
            return {"title": event["title"], "slug": event["slug"]}

        def extract_comment_count_from_market(self, selected_market, event_state):
            return event_state

        def extract_question(self, selected_market, markets, state_question, slug):
            return selected_market["question"]

        def build_market_dict(self, **kwargs):
            return {"slug": kwargs["slug"], "question": kwargs["question"], "outcomes": ["Yes", "No"]}

        def build_snapshot(self, **kwargs):
            return {"slug": "only-market", "question": "Only?", "yes_price": 0.6}

    monkeypatch.setattr(
        "app.domains.markets.adapters.polymarket.get_market_service",
        lambda: FakeService(),
    )
    monkeypatch.setattr(
        "app.domains.markets.adapters.polymarket.fetch_order_book_async",
        lambda token_id: {},
    )

    result = await adapter.fetch("https://polymarket.com/event/event")
    assert result["requires_market_selection"] is False
    assert result["selected_market_id"] == "only-market"


@pytest.mark.asyncio
async def test_polymarket_adapter_empty_markets_returns_safe_unknown(monkeypatch):
    adapter = PolymarketAdapter()

    class FakeService:
        def is_event(self, markets):
            return False

        async def fetch_market_data(self, market_url, slug=None):
            return {"slug": "empty", "title": "Empty"}, [], "empty"

        def extract_event_image(self, event, markets, selected_market, is_event):
            return None

        def update_event_metadata(self, event_state, event, event_image):
            return {"title": event["title"], "slug": event["slug"]}

        def extract_comment_count_from_market(self, selected_market, event_state):
            return event_state

        def extract_question(self, selected_market, markets, state_question, slug):
            return "Will empty resolve to Yes?"

        def build_market_dict(self, **kwargs):
            return {"slug": kwargs["slug"], "question": kwargs["question"], "outcomes": ["Yes", "No"]}

        def build_snapshot(self, **kwargs):
            return {"slug": "empty", "question": "Will empty resolve to Yes?", "yes_price": 0.5}

    monkeypatch.setattr(
        "app.domains.markets.adapters.polymarket.get_market_service",
        lambda: FakeService(),
    )

    result = await adapter.fetch("https://polymarket.com/event/empty")
    assert result["market_id"] == "empty"
    assert result["market_snapshot"]["yes_price"] == 0.5
