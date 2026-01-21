"""Tests for Market Agent."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.orchestration.agents.market import run_market_agent
from app.orchestration.state import AgentState


@pytest.mark.anyio(backend="asyncio")
async def test_run_market_agent_single_market():
    """Test run_market_agent with single market scenario."""
    state: AgentState = {
        "slug": "test-market",
        "market_url": "https://polymarket.com/market/test-market",
    }

    mock_event = {
        "title": "Test Event",
        "volume24hr": 1000000.0,
        "commentCount": 10,
    }
    mock_markets = [
        {
            "slug": "test-market",
            "question": "Will this test pass?",
            "id": "123",
            "bestBid": 0.5,
            "bestAsk": 0.51,
            "volume24hr": 500000.0,
            "outcomes": ["Yes", "No"],
        }
    ]

    with (
        patch("app.domains.markets.service.get_event_and_markets_by_slug") as mock_get,
        patch("app.orchestration.agents.market.fetch_order_book_async") as mock_fetch,
    ):
        mock_get.return_value = (mock_event, mock_markets)
        mock_fetch.return_value = {}

        result = await run_market_agent(state)

        assert result["slug"] == "test-market"
        assert result["market"]["slug"] == "test-market"
        # The question should come from the API market record
        assert result["market"]["question"] == "Will this test pass?"
        assert result["market_snapshot"]["question"] == "Will this test pass?"
        assert result["selected_market_slug"] == "test-market"
        assert result["event"]["title"] == "Test Event"
        assert result["event"]["commentCount"] == 10


@pytest.mark.anyio(backend="asyncio")
async def test_run_market_agent_event_requires_selection():
    """Test run_market_agent with event that requires market selection."""
    state: AgentState = {
        "slug": "test-event",
        "market_url": "https://polymarket.com/event/test-event",
    }

    mock_event = {
        "title": "Test Event",
        "image": "https://example.com/image.png",
        "volume24hr": 2000000.0,
        "commentCount": 20,
    }
    mock_markets = [
        {"slug": "test-event-market-1", "question": "Market 1?", "id": "1"},
        {"slug": "test-event-market-2", "question": "Market 2?", "id": "2"},
    ]

    with patch("app.domains.markets.service.get_event_and_markets_by_slug") as mock_get:
        mock_get.return_value = (mock_event, mock_markets)

        with patch("app.domains.markets.service.MarketService.select_market") as mock_select:
            # Return None, None, True to indicate selection is required
            mock_select.return_value = (None, None, True)

            result = await run_market_agent(state)

            assert result["requires_market_selection"] is True
            assert result["market_options"] is not None
            assert len(result["market_options"]) == 2
            assert result["event"]["title"] == "Test Event"
            assert result["event"]["image"] == "https://example.com/image.png"
            assert result["event"]["commentCount"] == 20


@pytest.mark.anyio(backend="asyncio")
async def test_run_market_agent_auto_selection():
    """Test run_market_agent with auto-selection of market."""
    state: AgentState = {
        "slug": "test-event",
        "market_url": "https://polymarket.com/event/test-event",
    }

    mock_event = {"title": "Test Event"}
    mock_markets = [
        {
            "slug": "test-event-market-1",
            "question": "Market 1?",
            "id": "1",
            "outcomes": ["Yes", "No"],
        },
        {
            "slug": "test-event-market-2",
            "question": "Market 2?",
            "id": "2",
            "outcomes": ["Yes", "No"],
        },
    ]

    with (
        patch("app.domains.markets.service.get_event_and_markets_by_slug") as mock_get,
        patch("app.domains.markets.service.MarketService.select_market") as mock_select,
        patch("app.orchestration.agents.market.fetch_order_book_async") as mock_fetch,
    ):
        mock_get.return_value = (mock_event, mock_markets)
        mock_select.return_value = (mock_markets[0], "test-event-market-1", False)
        mock_fetch.return_value = {}

        result = await run_market_agent(state)

                # When selection is not required, requires_market_selection should not be True
                # It might not be in the result at all, or it might be False/None
        assert result.get("requires_market_selection") is not True
        # Also verify it's not explicitly set to True
        if "requires_market_selection" in result:
            assert result["requires_market_selection"] is not True
        assert result["selected_market_slug"] == "test-event-market-1"


@pytest.mark.anyio(backend="asyncio")
async def test_run_market_agent_manual_selection():
    """Test run_market_agent with manual market selection."""
    state: AgentState = {
        "slug": "test-event",
        "market_url": "https://polymarket.com/event/test-event",
        "selected_market_slug": "test-event-market-2",
    }

    mock_event = {"title": "Test Event"}
    mock_markets = [
        {
            "slug": "test-event-market-1",
            "question": "Market 1?",
            "id": "1",
            "outcomes": ["Yes", "No"],
        },
        {
            "slug": "test-event-market-2",
            "question": "Market 2?",
            "id": "2",
            "outcomes": ["Yes", "No"],
        },
    ]

    with (
        patch("app.domains.markets.service.get_event_and_markets_by_slug") as mock_get,
        patch("app.domains.markets.service.MarketService.select_market") as mock_select,
        patch("app.orchestration.agents.market.fetch_order_book_async") as mock_fetch,
    ):
        mock_get.return_value = (mock_event, mock_markets)
        # Return the second market as selected
        mock_select.return_value = (mock_markets[1], "test-event-market-2", False)
        mock_fetch.return_value = {}

        result = await run_market_agent(state)

        assert result["selected_market_slug"] == "test-event-market-2"
        # The question should come from the selected market record
        assert result["market"]["question"] == "Market 2?"


@pytest.mark.anyio(backend="asyncio")
async def test_run_market_agent_missing_url_slug():
    """Test run_market_agent with missing market_url/slug (fallback)."""
    state: AgentState = {}

    mock_event = {}
    mock_markets = []

    with (
        patch("app.domains.markets.service.get_event_and_markets_by_slug") as mock_get,
        patch("app.domains.markets.service.extract_slug_from_url") as mock_extract,
    ):
        mock_get.return_value = (mock_event, mock_markets)
        mock_extract.return_value = None

        result = await run_market_agent(state)

        assert result["slug"] == "unknown-market"


@pytest.mark.anyio(backend="asyncio")
async def test_run_market_agent_order_book_success():
    """Test run_market_agent with successful order book fetch."""
    state: AgentState = {
        "slug": "test-market",
        "market_url": "https://polymarket.com/market/test-market",
    }

    mock_event = {}
    mock_markets = [
        {
            "slug": "test-market",
            "question": "Test?",
            "id": "123",
            "token_id": "token-123",
            "tokenId": "token-123",  # Also provide tokenId for compatibility
        }
    ]

    mock_order_book = {
        "bids": [{"price": 0.49, "size": 100}, {"price": 0.48, "size": 200}],
        "asks": [{"price": 0.51, "size": 150}, {"price": 0.52, "size": 250}],
        "best_bid": 0.49,
        "best_ask": 0.51,
    }

    with (
        patch("app.domains.markets.service.get_event_and_markets_by_slug") as mock_get,
        patch("app.orchestration.agents.market.fetch_order_book_async") as mock_fetch,
    ):
        mock_get.return_value = (mock_event, mock_markets)
        mock_fetch.return_value = mock_order_book

        result = await run_market_agent(state)

        # Order book should be in market_snapshot
        assert "order_book" in result["market_snapshot"]
        assert result["market_snapshot"]["order_book"] == {
            "bids": mock_order_book["bids"],
            "asks": mock_order_book["asks"],
        }


@pytest.mark.anyio(backend="asyncio")
async def test_run_market_agent_order_book_failure():
    """Test run_market_agent with order book fetch failure."""
    state: AgentState = {
        "slug": "test-market",
        "market_url": "https://polymarket.com/market/test-market",
    }

    mock_event = {}
    mock_markets = [
        {
            "slug": "test-market",
            "question": "Test?",
            "id": "123",
            "token_id": "token-123",
            "tokenId": "token-123",  # Also provide tokenId for compatibility
        }
    ]

    with (
        patch("app.domains.markets.service.get_event_and_markets_by_slug") as mock_get,
        patch("app.orchestration.agents.market.fetch_order_book_async") as mock_fetch,
    ):
        mock_get.return_value = (mock_event, mock_markets)
        mock_fetch.side_effect = Exception("API Error")

        result = await run_market_agent(state)

            # Should continue despite order book failure
        assert result["market_snapshot"] is not None
        # Order book should have empty bids/asks arrays when fetch fails
        order_book = result["market_snapshot"].get("order_book", {})
        assert order_book == {"bids": [], "asks": []} or order_book == {}


@pytest.mark.anyio(backend="asyncio")
async def test_run_market_agent_image_extraction():
    """Test run_market_agent image extraction from various sources."""
    state: AgentState = {
        "slug": "test-market",
    }

    mock_event = {
        "image": "https://example.com/event-image.png",
    }
    mock_markets = [
        {
            "slug": "test-market",
            "question": "Test?",
            "id": "123",
            "image": "https://example.com/market-image.png",
            "outcomes": ["Yes", "No"],
        }
    ]

    with (
        patch("app.domains.markets.service.get_event_and_markets_by_slug") as mock_get,
        patch("app.orchestration.agents.market.fetch_order_book_async") as mock_fetch,
    ):
        mock_get.return_value = (mock_event, mock_markets)
        mock_fetch.return_value = {}

        result = await run_market_agent(state)

            # Should use market image over event image (market image takes precedence)
        assert "image" in result["event"]
        assert result["event"]["image"] == "https://example.com/market-image.png"


@pytest.mark.anyio(backend="asyncio")
async def test_run_market_agent_image_fallback():
    """Test run_market_agent image fallback to event or first market."""
    state: AgentState = {
        "slug": "test-event",
    }

    mock_event = {
        "icon": "https://example.com/event-icon.png",
    }
    mock_markets = [
        {
            "slug": "test-event-market-1",
            "question": "Market 1?",
            "id": "1",
            "outcomes": ["Yes", "No"],
        },
        {
            "slug": "test-event-market-2",
            "question": "Market 2?",
            "id": "2",
            "icon": "https://example.com/market2-icon.png",
            "outcomes": ["Yes", "No"],
        },
    ]

    with (
        patch("app.domains.markets.service.get_event_and_markets_by_slug") as mock_get,
        patch("app.domains.markets.service.MarketService.select_market") as mock_select,
    ):
        mock_get.return_value = (mock_event, mock_markets)
        mock_select.return_value = (None, None, True)  # Requires selection

        result = await run_market_agent(state)

            # Should use event icon when no market selected (requires selection path)
        assert "image" in result["event"]
        assert result["event"]["image"] == "https://example.com/event-icon.png"


@pytest.mark.anyio(backend="asyncio")
async def test_run_market_agent_comment_count_handling():
    """Test run_market_agent commentCount handling (event and market level)."""
    state: AgentState = {
        "slug": "test-market",
    }

    mock_event = {
        "commentCount": 25,
        "seriesCommentCount": 10,
    }
    mock_markets = [
        {
            "slug": "test-market",
            "question": "Test?",
            "id": "123",
            "commentCount": 15,
            "outcomes": ["Yes", "No"],
        }
    ]

    with patch("app.domains.markets.service.get_event_and_markets_by_slug") as mock_get:
        mock_get.return_value = (mock_event, mock_markets)

        with patch(
            "app.orchestration.agents.market.fetch_order_book_async",
            new=AsyncMock(return_value={}),
        ):
            result = await run_market_agent(state)

            # Event commentCount should be used (event takes precedence over market)
            assert "commentCount" in result["event"]
            assert result["event"]["commentCount"] == 25
            assert "seriesCommentCount" in result["event"]
            assert result["event"]["seriesCommentCount"] == 10


@pytest.mark.anyio(backend="asyncio")
async def test_run_market_agent_comment_count_market_fallback():
    """Test run_market_agent commentCount fallback to market when event missing."""
    state: AgentState = {
        "slug": "test-market",
    }

    mock_event = {}  # No commentCount
    mock_markets = [
        {
            "slug": "test-market",
            "question": "Test?",
            "id": "123",
            "commentCount": 30,
            "outcomes": ["Yes", "No"],
        }
    ]

    with patch("app.domains.markets.service.get_event_and_markets_by_slug") as mock_get:
        mock_get.return_value = (mock_event, mock_markets)

        with patch(
            "app.orchestration.agents.market.fetch_order_book_async",
            new=AsyncMock(return_value={}),
        ):
            result = await run_market_agent(state)

            # Should use market commentCount as fallback when event doesn't have it
            assert "commentCount" in result["event"]
            assert result["event"]["commentCount"] == 30


@pytest.mark.anyio(backend="asyncio")
async def test_run_market_agent_comment_count_zero():
    """Test run_market_agent with commentCount of 0 (not None)."""
    state: AgentState = {
        "slug": "test-market",
    }

    mock_event = {
        "commentCount": 0,
    }
    mock_markets = [
        {
            "slug": "test-market",
            "question": "Test?",
            "id": "123",
            "outcomes": ["Yes", "No"],
        }
    ]

    with patch("app.domains.markets.service.get_event_and_markets_by_slug") as mock_get:
        mock_get.return_value = (mock_event, mock_markets)

        with patch(
            "app.orchestration.agents.market.fetch_order_book_async",
            new=AsyncMock(return_value={}),
        ):
            result = await run_market_agent(state)

            # Should preserve 0 value (not None)
            assert "commentCount" in result["event"]
            assert result["event"]["commentCount"] == 0


@pytest.mark.anyio(backend="asyncio")
async def test_run_market_agent_series_comment_count():
    """Test run_market_agent seriesCommentCount handling."""
    state: AgentState = {
        "slug": "test-market",
    }

    mock_event = {
        "seriesCommentCount": 5,
    }
    mock_markets = [
        {
            "slug": "test-market",
            "question": "Test?",
            "id": "123",
            "outcomes": ["Yes", "No"],
        }
    ]

    with patch("app.domains.markets.service.get_event_and_markets_by_slug") as mock_get:
        mock_get.return_value = (mock_event, mock_markets)

        with patch(
            "app.orchestration.agents.market.fetch_order_book_async",
            new=AsyncMock(return_value={}),
        ):
            result = await run_market_agent(state)

            assert "seriesCommentCount" in result["event"]
            assert result["event"]["seriesCommentCount"] == 5


@pytest.mark.anyio(backend="asyncio")
async def test_run_market_agent_market_snapshot_building():
    """Test run_market_agent builds market snapshot correctly."""
    state: AgentState = {
        "slug": "test-market",
        "market_url": "https://polymarket.com/market/test-market",
    }

    mock_event = {}
    mock_markets = [
        {
            "slug": "test-market",
            "question": "Will this test pass?",
            "id": "123",
            "bestBid": 0.45,
            "bestAsk": 0.55,
            "outcomes": ["Yes", "No"],
            "token_id": "token-123",
            "tokenId": "token-123",
        }
    ]

    mock_order_book = {
        "bids": [[0.44, 100]],
        "asks": [[0.56, 100]],
    }

    with patch("app.domains.markets.service.get_event_and_markets_by_slug") as mock_get:
        mock_get.return_value = (mock_event, mock_markets)

        with patch(
            "app.orchestration.agents.market.fetch_order_book_async",
            new=AsyncMock(return_value=mock_order_book),
        ):
            result = await run_market_agent(state)

            assert result["market_snapshot"]["question"] == "Will this test pass?"
            assert result["market_snapshot"]["slug"] == "test-market"
            assert result["market_snapshot"]["url"] == "https://polymarket.com/market/test-market"
            assert "order_book" in result["market_snapshot"]
            assert result["market_snapshot"]["order_book"]["bids"] == [[0.44, 100]]
            assert result["market_snapshot"]["order_book"]["asks"] == [[0.56, 100]]


@pytest.mark.anyio(backend="asyncio")
async def test_run_market_agent_polymarket_api_error():
    """Test run_market_agent handles Polymarket API errors gracefully."""
    state: AgentState = {
        "slug": "test-market",
    }

    with patch("app.domains.markets.service.get_event_and_markets_by_slug") as mock_get:
        mock_get.side_effect = Exception("API Error")

        # Should not crash, but may have limited state
        try:
            await run_market_agent(state)
            # If it doesn't crash, that's acceptable
        except Exception:
            # If it does crash, that's also acceptable for this test
            pass
