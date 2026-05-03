"""Tests for Market Selector."""

from __future__ import annotations

from app.domains.markets.selector import find_market_by_slug, select_market_from_options


def test_select_market_from_options_single_market():
    """Test select_market_from_options with single market (auto-select)."""
    markets = [{"slug": "test-market", "id": "123", "question": "Test?"}]

    market, slug, requires_selection = select_market_from_options(markets, None, "test-market")

    assert market == markets[0]
    assert slug == "test-market"
    assert requires_selection is False


def test_select_market_from_options_auto_selection():
    """Test select_market_from_options auto-selection scenarios."""
    markets = [
        {"slug": "market-1", "id": "1"},
        {"slug": "market-2", "id": "2"},
    ]

    # No selection provided, should require selection
    market, slug, requires_selection = select_market_from_options(markets, None, "test-event")

    assert requires_selection is True


def test_select_market_from_options_manual_selection():
    """Test select_market_from_options with manual selection."""
    markets = [
        {"slug": "market-1", "id": "1", "question": "Market 1?"},
        {"slug": "market-2", "id": "2", "question": "Market 2?"},
    ]

    market, slug, requires_selection = select_market_from_options(markets, "market-2", "test-event")

    assert market == markets[1]
    assert slug == "market-2"
    assert requires_selection is False


def test_select_market_from_options_fuzzy_matching():
    """Test select_market_from_options fuzzy matching."""
    markets = [
        {"slug": "test-event-market-1", "id": "1"},
        {"slug": "test-event-market-2", "id": "2"},
    ]

    # Fuzzy match
    market, slug, requires_selection = select_market_from_options(markets, "market-1", "test-event")

    assert market is not None
    assert requires_selection is False


def test_select_market_from_options_requires_selection():
    """Test select_market_from_options requires selection scenarios."""
    markets = [
        {"slug": "market-1", "id": "1"},
        {"slug": "market-2", "id": "2"},
        {"slug": "market-3", "id": "3"},
    ]

    # No selection, multiple markets
    market, slug, requires_selection = select_market_from_options(markets, None, "test-event")

    assert requires_selection is True


def test_select_market_from_options_empty_markets():
    """Test select_market_from_options with empty markets list."""
    markets = []

    market, slug, requires_selection = select_market_from_options(markets, None, "test")

    assert market is None
    assert slug is None
    assert requires_selection is False


def test_find_market_by_slug_found():
    """Test find_market_by_slug when market is found."""
    markets = [
        {"slug": "market-1", "id": "1"},
        {"slug": "market-2", "id": "2"},
    ]

    market = find_market_by_slug(markets, "market-1")

    assert market == markets[0]


def test_find_market_by_slug_not_found():
    """Test find_market_by_slug when market is not found."""
    markets = [
        {"slug": "market-1", "id": "1"},
    ]

    market = find_market_by_slug(markets, "market-2")

    assert market is None


def test_find_market_by_slug_by_id():
    """Test find_market_by_slug finding by ID."""
    markets = [
        {"slug": "market-1", "id": "123"},
        {"slug": "market-2", "id": "456"},
    ]

    market = find_market_by_slug(markets, "123")

    assert market == markets[0]


def test_find_market_by_slug_empty_markets():
    """Test find_market_by_slug with empty markets."""
    market = find_market_by_slug([], "test")

    assert market is None


def test_find_market_by_slug_none_slug():
    """Test find_market_by_slug with None slug."""
    markets = [{"slug": "market-1", "id": "1"}]

    market = find_market_by_slug(markets, None)

    assert market is None
