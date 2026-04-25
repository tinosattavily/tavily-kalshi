import pytest

from app.domains.markets.adapters.kalshi import KalshiAdapter, kalshi_cents_to_probability


def test_kalshi_cents_to_probability_property():
    for cents in range(1, 100):
        p = kalshi_cents_to_probability(cents)
        assert 0.01 <= p <= 0.99
        assert p == cents / 100.0


@pytest.mark.asyncio
async def test_kalshi_adapter_normalizes_direct_market(monkeypatch):
    adapter = KalshiAdapter()

    async def fake_get_market(ticker):
        return {
            "ticker": ticker,
            "event_ticker": "INXD-25JAN17",
            "title": "S&P above threshold",
            "subtitle": "At close",
            "status": "open",
            "yes_bid": 41,
            "yes_ask": 43,
            "last_price": 42,
            "volume": 1000,
            "volume_24h": 200,
            "open_interest": 300,
        }

    async def fake_get_event(event_ticker):
        return {"event_ticker": event_ticker, "title": "S&P event", "category": "Finance"}

    async def fake_get_orderbook(ticker, depth=10):
        return {"orderbook": {"yes": [[41, 10]], "no": [[57, 9]]}}

    monkeypatch.setattr("app.domains.markets.adapters.kalshi.get_market", fake_get_market)
    monkeypatch.setattr("app.domains.markets.adapters.kalshi.get_event", fake_get_event)
    monkeypatch.setattr("app.domains.markets.adapters.kalshi.get_orderbook", fake_get_orderbook)

    result = await adapter.fetch("https://kalshi.com/markets/INXD-25JAN17-B24999")
    assert result["venue"] == "kalshi"
    assert result["market_id"] == "INXD-25JAN17-B24999"
    assert result["market_snapshot"]["yes_price"] == 0.42
    assert result["market_snapshot"]["best_bid"] == 0.41
    assert result["market_snapshot"]["best_ask"] == 0.43
    assert result["market_snapshot"]["yes_price_cents"] == 42
    assert result["market_snapshot"]["order_book"]["asks"][0]["price"] == 0.43


@pytest.mark.asyncio
async def test_kalshi_adapter_requires_selection_for_event(monkeypatch):
    adapter = KalshiAdapter()

    async def fake_get_event(event_ticker):
        return {"event_ticker": event_ticker, "title": "S&P event", "category": "Finance"}

    async def fake_get_markets(event_ticker=None, status="open", limit=100):
        return [
            {"ticker": "AAA-1", "title": "A", "yes_bid": 10, "yes_ask": 12, "status": "open"},
            {"ticker": "AAA-2", "title": "B", "yes_bid": 20, "yes_ask": 22, "status": "open"},
        ]

    monkeypatch.setattr("app.domains.markets.adapters.kalshi.get_event", fake_get_event)
    monkeypatch.setattr("app.domains.markets.adapters.kalshi.get_markets", fake_get_markets)

    result = await adapter.fetch("https://kalshi.com/events/INXD-25JAN17")
    assert result["requires_market_selection"] is True
    assert [option["market_id"] for option in result["market_options"]] == ["AAA-1", "AAA-2"]
    assert result["market_options"][0]["yes_price"] == 0.11
