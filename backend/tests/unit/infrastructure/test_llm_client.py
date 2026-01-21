"""Tests for OpenAI Client."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.llm.client import OpenAIClient, get_openai_client


@patch("app.infrastructure.llm.client.openai")
@patch("app.infrastructure.llm.client.settings")
def test_openai_client_init_new_api(mock_settings, mock_openai):
    """Test OpenAIClient.__init__ with new API format (v1.0+)."""
    mock_settings.openai_api_key = "test-key"

    # Patch the OpenAI class import inside the method
    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        client = OpenAIClient()

        assert client.api_key == "test-key"
        assert client._use_new_api is True
        assert client.client == mock_client


@patch("app.infrastructure.llm.client.openai")
@patch("app.infrastructure.llm.client.settings")
def test_openai_client_init_old_api(mock_settings, mock_openai):
    """Test OpenAIClient.__init__ with old API format (v0.x)."""
    mock_settings.openai_api_key = "test-key"

    # Simulate old API (no OpenAI class) - patch the import to raise ImportError
    with patch("openai.OpenAI", side_effect=ImportError):
        client = OpenAIClient()

        assert client.api_key == "test-key"
        assert client._use_new_api is False
        assert mock_openai.api_key == "test-key"


@patch("app.infrastructure.llm.client.settings")
def test_openai_client_init_missing_key(mock_settings):
    """Test OpenAIClient.__init__ with missing API key."""
    mock_settings.openai_api_key = None

    client = OpenAIClient()

    assert client.api_key is None
    assert client.client is None


@patch("app.infrastructure.llm.client.openai", None)
@patch("app.infrastructure.llm.client.settings")
def test_openai_client_init_not_installed(mock_settings):
    """Test OpenAIClient.__init__ with OpenAI not installed."""
    mock_settings.openai_api_key = "test-key"

    client = OpenAIClient()

    assert client.client is None


@patch("app.infrastructure.llm.client.openai_cache")
@patch("app.infrastructure.llm.client.openai_circuit")
def test_generate_signal_sync_success(mock_circuit, mock_cache):
    """Test _generate_signal_sync successful generation."""
    mock_circuit.can_attempt.return_value = True
    mock_cache.get.return_value = None
    mock_cache.set = MagicMock()

    client = OpenAIClient()
    client.api_key = "test-key"
    client.client = MagicMock()
    client._use_new_api = True

    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = json.dumps(
        {
            "model_prob_abs": 0.6,
            "direction": "up",
            "confidence": "high",
            "rationale": "Test",
        }
    )
    client.client.chat.completions.create = MagicMock(return_value=mock_completion)
    mock_circuit.record_success = MagicMock()

    result = client._generate_signal_sync(
        "Test Event",
        "Will this test pass?",
        0.5,
        "Test summary",
        "Headline 1",
        "Test label",
    )

    assert result["model_prob_abs"] == 0.6
    assert mock_cache.set.called


@patch("app.infrastructure.llm.client.openai_cache")
@patch("app.infrastructure.llm.client.openai_circuit")
@patch("app.infrastructure.llm.client.openai")
def test_generate_signal_sync_circuit_breaker(mock_openai, mock_circuit, mock_cache):
    """Test _generate_signal_sync with circuit breaker open."""
    # Ensure openai module exists
    mock_openai_module = MagicMock()
    mock_openai_module.ChatCompletion = MagicMock()
    mock_openai.return_value = mock_openai_module

    mock_circuit.can_attempt.return_value = False
    mock_cache.get.return_value = None  # Cache miss

    client = OpenAIClient()
    client.api_key = "test-key"
    # Ensure openai module is available (not None)
    import sys

    if "openai" not in sys.modules or sys.modules.get("openai") is None:
        sys.modules["openai"] = mock_openai_module

    with pytest.raises(RuntimeError, match="circuit breaker"):
        client._generate_signal_sync(
            "Test Event",
            "Test?",
            0.5,
            "Summary",
            "Headlines",
        )


@patch("app.infrastructure.llm.client.openai_cache")
@patch("app.infrastructure.llm.client.openai_circuit")
def test_generate_signal_sync_api_error(mock_circuit, mock_cache):
    """Test _generate_signal_sync with API errors."""
    mock_circuit.can_attempt.return_value = True
    mock_cache.get.return_value = None

    client = OpenAIClient()
    client.api_key = "test-key"
    client.client = MagicMock()
    client._use_new_api = True
    client.client.chat.completions.create = MagicMock(side_effect=Exception("API Error"))
    mock_circuit.record_failure = MagicMock()

    with pytest.raises(RuntimeError):
        client._generate_signal_sync(
            "Test Event",
            "Test?",
            0.5,
            "Summary",
            "Headlines",
        )

    assert mock_circuit.record_failure.called


@pytest.mark.anyio(backend="asyncio")
async def test_generate_signal():
    """Test generate_signal async wrapper."""
    client = OpenAIClient()
    client.api_key = "test-key"

    with patch.object(client, "_generate_signal_sync", return_value={"model_prob_abs": 0.6}):
        result = await client.generate_signal(
            "Test Event",
            "Test?",
            0.5,
            "Summary",
            "Headlines",
        )

        assert result["model_prob_abs"] == 0.6


@patch("app.infrastructure.llm.client.openai_cache")
@patch("app.infrastructure.llm.client.openai_circuit")
def test_summarize_news_with_sentiment_sync(mock_circuit, mock_cache):
    """Test _summarize_news_with_sentiment_sync."""
    mock_circuit.can_attempt.return_value = True
    mock_cache.get.return_value = None
    mock_cache.set = MagicMock()

    client = OpenAIClient()
    client.api_key = "test-key"
    client.client = MagicMock()
    client._use_new_api = True

    articles = [
        {
            "title": "Article 1",
            "snippet": "Content 1",
            "source": "Source 1",
            "sentiment": "bullish",
        },
        {
            "title": "Article 2",
            "snippet": "Content 2",
            "source": "Source 2",
            "sentiment": "bearish",
        },
    ]

    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = "Generated summary"
    client.client.chat.completions.create = MagicMock(return_value=mock_completion)
    mock_circuit.record_success = MagicMock()

    result = client._summarize_news_with_sentiment_sync(
        articles,
        "Test Event",
        "Test Question?",
    )

    assert result == "Generated summary"
    assert mock_cache.set.called


@pytest.mark.anyio(backend="asyncio")
async def test_summarize_news_with_sentiment():
    """Test summarize_news_with_sentiment async wrapper."""
    client = OpenAIClient()
    client.api_key = "test-key"

    articles = [
        {"title": "Article 1", "sentiment": "bullish"},
    ]

    with patch.object(client, "_summarize_news_with_sentiment_sync", return_value="Summary"):
        result = await client.summarize_news_with_sentiment(
            articles,
            "Test Event",
            "Test Question?",
        )

        assert result == "Summary"


def test_get_openai_client_singleton():
    """Test get_openai_client singleton pattern."""
    # Reset singleton
    import app.infrastructure.llm.client

    app.infrastructure.llm.client._openai_client = None

    client1 = get_openai_client()
    client2 = get_openai_client()

    assert client1 is client2


@patch("app.infrastructure.llm.client.openai_cache")
@patch("app.infrastructure.llm.client.openai_circuit")
def test_generate_signal_sync_cache_hit(mock_circuit, mock_cache):
    """Test _generate_signal_sync with cache hit."""
    cached_data = {"model_prob_abs": 0.6}
    mock_cache.get.return_value = cached_data

    client = OpenAIClient()
    client.api_key = "test-key"

    result = client._generate_signal_sync(
        "Test Event",
        "Test?",
        0.5,
        "Summary",
        "Headlines",
    )

    assert result == cached_data
    # Should not call OpenAI API when cache hit occurs
    # The client might still exist, but the API should not be called
    # Verify cache was checked
    assert mock_cache.get.called


@patch("app.infrastructure.llm.client.openai_cache")
@patch("app.infrastructure.llm.client.openai_circuit")
def test_generate_signal_sync_old_api_format(mock_circuit, mock_cache):
    """Test _generate_signal_sync with old API format."""
    mock_circuit.can_attempt.return_value = True
    mock_cache.get.return_value = None
    mock_cache.set = MagicMock()

    client = OpenAIClient()
    client.api_key = "test-key"
    client._use_new_api = False

    with patch("app.infrastructure.llm.client.openai") as mock_openai:
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message = {"content": json.dumps({"model_prob_abs": 0.6})}
        mock_openai.ChatCompletion.create = MagicMock(return_value=mock_completion)
        mock_circuit.record_success = MagicMock()

        result = client._generate_signal_sync(
            "Test Event",
            "Test?",
            0.5,
            "Summary",
            "Headlines",
        )

        assert result["model_prob_abs"] == 0.6
