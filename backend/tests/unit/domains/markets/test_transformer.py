"""Tests for Market Transformer."""

from __future__ import annotations

from app.domains.markets.transformer import build_market_options, build_market_snapshot


def test_build_market_options_multiple_markets():
    """Test build_market_options with multiple markets."""
    markets = [
        {
            "slug": "market-1",
            "question": "Market 1?",
            "groupItemTitle": "Item 1",
            "liquidity": 1000000.0,
            "bestBid": 0.45,
            "bestAsk": 0.55,
            "image": "https://example.com/img1.png",
        },
        {
            "slug": "market-2",
            "title": "Market 2",
            "groupItemTitle": "Item 2",
            "liquidity": 2000000.0,
            "icon": "https://example.com/img2.png",
        },
    ]

    options = build_market_options(markets)

    assert len(options) == 2
    assert options[0]["slug"] == "market-1"
    assert options[0]["question"] == "Market 1?"
    assert options[0]["liquidity"] == 1000000.0
    assert options[1]["slug"] == "market-2"
    assert options[1]["question"] == "Market 2"  # Uses title


def test_build_market_options_single_market():
    """Test build_market_options with single market."""
    markets = [
        {
            "slug": "market-1",
            "question": "Market 1?",
        }
    ]

    options = build_market_options(markets)

    assert len(options) == 1
    assert options[0]["slug"] == "market-1"


def test_build_market_options_missing_fields():
    """Test build_market_options with missing fields."""
    markets = [
        {
            "slug": "market-1",
        }
    ]

    options = build_market_options(markets)

    assert len(options) == 1
    assert options[0]["slug"] == "market-1"
    assert options[0]["question"] is None


def test_build_market_options_edge_cases():
    """Test build_market_options with edge cases."""
    # Empty list
    options1 = build_market_options([])
    assert len(options1) == 0

    # Market with icon instead of image
    markets2 = [
        {
            "slug": "market-1",
            "icon": "https://example.com/icon.png",
        }
    ]
    options2 = build_market_options(markets2)
    assert options2[0]["image"] == "https://example.com/icon.png"


def test_build_market_snapshot_full_order_book():
    """Test build_market_snapshot with full order book data."""
    market = {
        "question": "Will this test pass?",
        "outcomes": ["Yes", "No"],
        "yes_index": 0,
    }
    market_url = "https://polymarket.com/market/test"
    order_book = {
        "bids": [[0.48, 100], [0.47, 200]],
        "asks": [[0.52, 150], [0.53, 250]],
        "best_bid": 0.48,
        "best_ask": 0.52,
    }
    state = {}
    slug = "test-market"

    snapshot = build_market_snapshot(market, market_url, order_book, state, slug)

    assert snapshot["question"] == "Will this test pass?"
    assert snapshot["slug"] == "test-market"
    assert snapshot["url"] == market_url
    assert snapshot["order_book"]["bids"] == order_book["bids"]
    assert snapshot["best_bid"] == 0.48
    assert snapshot["best_ask"] == 0.52


def test_build_market_snapshot_missing_order_book():
    """Test build_market_snapshot with missing order book."""
    market = {
        "question": "Will this test pass?",
        "outcomes": ["Yes", "No"],
        "yes_index": 0,
    }
    market_url = "https://polymarket.com/market/test"
    order_book = {}
    state = {}
    slug = "test-market"

    snapshot = build_market_snapshot(market, market_url, order_book, state, slug)

    assert snapshot["question"] == "Will this test pass?"
    # When order_book is empty dict, order_book_data should have empty bids/asks arrays
    assert snapshot["order_book"] == {"bids": [], "asks": []}


def test_build_market_snapshot_api_market_record():
    """Test build_market_snapshot with API market record."""
    market = {
        # No question in market dict, so it will use api_record's question
        "outcomes": ["Yes", "No"],
    }
    market_url = "https://polymarket.com/market/test"
    order_book = {}
    state = {}
    slug = "test-market"
    api_record = {
        "question": "API Question?",
        "bestBid": 0.49,
        "bestAsk": 0.51,
        "volume24hr": 500000.0,
        "liquidity": 1000000.0,
        "endDate": "2025-12-31T00:00:00Z",
    }

    snapshot = build_market_snapshot(
        market, market_url, order_book, state, slug, api_market_record=api_record
    )

    # Should use API record's question since market dict doesn't have one
    assert snapshot["question"] == "API Question?"
    # API record data should be used for other fields
    assert snapshot["best_bid"] == 0.49
    assert snapshot["best_ask"] == 0.51


def test_build_market_snapshot_price_fallback():
    """Test build_market_snapshot price fallback logic."""
    market = {
        "question": "Test?",
        "outcomes": ["Yes", "No"],
    }
    market_url = "https://polymarket.com/market/test"
    order_book = {}
    state = {
        "market_snapshot": {
            "yes_price": 0.3,
        }
    }
    slug = "test-market"

    snapshot = build_market_snapshot(market, market_url, order_book, state, slug)

    # Should use fallback price
    assert snapshot["yes_price"] is not None
    assert 0.0 <= snapshot["yes_price"] <= 1.0


def test_build_market_snapshot_end_date():
    """Test build_market_snapshot end_date handling."""
    market = {
        "question": "Test?",
        "outcomes": ["Yes", "No"],
    }
    market_url = "https://polymarket.com/market/test"
    order_book = {}
    state = {
        "event": {
            "end_date": "2025-12-31T00:00:00Z",
        }
    }
    slug = "test-market"
    api_record = {
        "endDate": "2025-12-31T00:00:00Z",
    }

    snapshot = build_market_snapshot(
        market, market_url, order_book, state, slug, api_market_record=api_record
    )

    assert snapshot["end_date"] is not None
    assert "Z" in snapshot["end_date"] or "T" in snapshot["end_date"]


def test_build_market_snapshot_comment_count():
    """Test build_market_snapshot comment count handling."""
    market = {
        "question": "Test?",
        "outcomes": ["Yes", "No"],
    }
    market_url = "https://polymarket.com/market/test"
    order_book = {}
    state = {
        "event": {
            "commentCount": 10,
            "seriesCommentCount": 5,
        }
    }
    slug = "test-market"

    snapshot = build_market_snapshot(market, market_url, order_book, state, slug)

    assert snapshot["comment_count"] == 10
    assert snapshot["commentCount"] == 10
    assert snapshot["event_comment_count"] == 10
    assert snapshot["series_comment_count"] == 5


def test_build_market_snapshot_formatted_outcomes():
    """Test build_market_snapshot formatted outcomes."""
    market = {
        "question": "Test?",
        "outcomes": ["Yes", "No"],
        "yes_index": 0,
    }
    market_url = "https://polymarket.com/market/test"
    order_book = {}
    state = {}
    slug = "test-market"

    snapshot = build_market_snapshot(market, market_url, order_book, state, slug)

    assert "formatted_outcomes" in snapshot
    assert len(snapshot["formatted_outcomes"]) == 2
    assert snapshot["formatted_outcomes"][0]["title"] == "Yes"
    assert snapshot["formatted_outcomes"][1]["title"] == "No"
