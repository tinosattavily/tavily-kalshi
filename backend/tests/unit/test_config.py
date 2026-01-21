"""Tests for Config."""

from __future__ import annotations

from unittest.mock import patch

from app.config import PolymarketAPI, Settings, _get_env


def test_get_env():
    """Test _get_env function."""
    with patch("os.getenv", return_value="env-value"):
        result = _get_env("TEST_KEY")
        assert result == "env-value"

    # Test with None
    with patch("os.getenv", return_value=None):
        result = _get_env("TEST_KEY")
        assert result is None

    # Test with whitespace stripping
    with patch("os.getenv", return_value="  env-value  "):
        result = _get_env("TEST_KEY")
        assert result == "env-value"


def test_settings_class():
    """Test Settings class configuration options."""
    with patch("os.getenv") as mock_getenv:
        mock_getenv.side_effect = lambda key, default=None: {
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "6379",
            "REDIS_DB": "0",
            "USE_REDIS_CACHE": "false",
        }.get(key, default)

        settings = Settings()

        assert settings.redis_host == "localhost"
        assert settings.redis_port == 6379
        assert settings.redis_db == 0
        assert settings.use_redis_cache is False


def test_settings_default_values():
    """Test Settings class default values."""
    with patch("os.getenv") as mock_getenv:

        def getenv_side_effect(key, default=None):
            # Return defaults for Redis settings
            defaults = {
                "REDIS_HOST": "localhost",
                "REDIS_PORT": "6379",
                "REDIS_DB": "0",
                "USE_REDIS_CACHE": "false",
            }
            return defaults.get(key, default)

        mock_getenv.side_effect = getenv_side_effect
        settings = Settings()

        # Should have defaults
        assert settings.redis_host == "localhost"
        assert settings.redis_port == 6379
        assert settings.redis_db == 0


def test_polymarket_api():
    """Test PolymarketAPI class."""
    assert PolymarketAPI.GAMMA_API == "https://gamma-api.polymarket.com"
    assert PolymarketAPI.CLOB_API == "https://clob.polymarket.com"
