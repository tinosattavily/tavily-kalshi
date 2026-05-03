"""Tests for Cache utilities."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

from app.infrastructure.http.cache import RedisCache, TTLCache, _create_cache, cached


def test_ttl_cache_get_set():
    """Test TTLCache get/set operations."""
    cache = TTLCache(ttl_seconds=60)

    # Set and get
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"

    # Get non-existent key
    assert cache.get("key2") is None


def test_ttl_cache_expiration():
    """Test TTLCache TTL expiration."""
    cache = TTLCache(ttl_seconds=1)

    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"

    # Wait for expiration
    time.sleep(1.1)
    assert cache.get("key1") is None


def test_ttl_cache_cleanup_expired():
    """Test TTLCache cleanup_expired()."""
    cache = TTLCache(ttl_seconds=1)

    cache.set("key1", "value1")
    cache.set("key2", "value2")

    # Wait for expiration
    time.sleep(1.1)

    removed = cache.cleanup_expired()
    assert removed == 2
    assert cache.get("key1") is None
    assert cache.get("key2") is None


def test_ttl_cache_clear():
    """Test TTLCache clear()."""
    cache = TTLCache(ttl_seconds=60)

    cache.set("key1", "value1")
    cache.set("key2", "value2")

    cache.clear()
    assert cache.get("key1") is None
    assert cache.get("key2") is None


@patch("app.infrastructure.http.cache.redis")
def test_redis_cache_connection_success(mock_redis):
    """Test RedisCache connection success."""
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_redis.from_url.return_value = mock_client

    cache = RedisCache(ttl_seconds=60, redis_url="redis://localhost:6379")

    assert cache._connected is True
    assert cache._client is not None


@patch("app.infrastructure.http.cache.redis")
def test_redis_cache_connection_failure(mock_redis):
    """Test RedisCache connection failure (fallback to in-memory)."""
    from redis.exceptions import ConnectionError

    mock_redis.from_url.side_effect = ConnectionError("Connection failed")

    cache = RedisCache(ttl_seconds=60, redis_url="redis://localhost:6379")

    assert cache._connected is False
    assert cache._fallback_cache is not None


@patch("app.infrastructure.http.cache.redis")
def test_redis_cache_get_set(mock_redis):
    """Test RedisCache get/set operations with Redis."""
    import json

    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_client.get.return_value = json.dumps("value1").encode("utf-8")
    mock_redis.from_url.return_value = mock_client

    cache = RedisCache(ttl_seconds=60, redis_url="redis://localhost:6379")

    # Test get
    value = cache.get("key1")
    assert value == "value1"

    # Test set
    cache.set("key2", "value2")
    mock_client.setex.assert_called()


@patch("app.infrastructure.http.cache.redis")
def test_redis_cache_fallback_on_error(mock_redis):
    """Test RedisCache fallback to in-memory on error."""
    from redis.exceptions import RedisError

    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_client.setex.side_effect = RedisError("Redis error")
    mock_client.get.side_effect = RedisError("Redis error")
    mock_redis.from_url.return_value = mock_client

    cache = RedisCache(ttl_seconds=60, redis_url="redis://localhost:6379")

    # Initially connected, but will fail on set/get
    # First set should trigger error and create fallback
    cache.set("key1", "value1")
    # Now get should use fallback
    value = cache.get("key1")
    # After error, _fallback_cache should exist
    assert hasattr(cache, "_fallback_cache")
    assert value == "value1"  # From fallback cache


@patch("app.infrastructure.http.cache.redis")
def test_redis_cache_clear(mock_redis):
    """Test RedisCache clear()."""
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_redis.from_url.return_value = mock_client

    cache = RedisCache(ttl_seconds=60, redis_url="redis://localhost:6379")
    cache.clear()

    mock_client.flushdb.assert_called()


@patch("app.infrastructure.http.cache.redis")
def test_redis_cache_cleanup_expired(mock_redis):
    """Test RedisCache cleanup_expired()."""
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_redis.from_url.return_value = mock_client

    cache = RedisCache(ttl_seconds=60, redis_url="redis://localhost:6379")

    # Redis handles expiration automatically
    removed = cache.cleanup_expired()
    assert removed == 0


@patch("app.infrastructure.http.cache.settings")
@patch("app.infrastructure.http.cache.REDIS_AVAILABLE", True)
def test_create_cache_redis_available(mock_settings):
    """Test _create_cache with Redis available."""
    mock_settings.use_redis_cache = True
    mock_settings.redis_url = "redis://localhost:6379"
    mock_settings.redis_host = None
    mock_settings.redis_port = None
    mock_settings.redis_db = None
    mock_settings.redis_password = None

    with patch("app.infrastructure.http.cache.RedisCache") as mock_redis_cache:
        mock_redis_cache.return_value = MagicMock()
        _create_cache(ttl_seconds=60, cache_name="test")

        assert mock_redis_cache.called


@patch("app.infrastructure.http.cache.settings")
@patch("app.infrastructure.http.cache.REDIS_AVAILABLE", False)
def test_create_cache_redis_unavailable(mock_settings):
    """Test _create_cache with Redis unavailable (fallback to TTLCache)."""
    mock_settings.use_redis_cache = True

    cache = _create_cache(ttl_seconds=60, cache_name="test")

    assert isinstance(cache, TTLCache)


def test_cached_decorator():
    """Test @cached decorator."""
    call_count = 0

    @cached(ttl=60)
    def test_func(x: int) -> int:
        nonlocal call_count
        call_count += 1
        return x * 2

    # First call - cache miss
    result1 = test_func(5)
    assert result1 == 10
    assert call_count == 1

    # Second call - cache hit
    result2 = test_func(5)
    assert result2 == 10
    assert call_count == 1  # Should not increment


def test_cached_decorator_with_custom_cache():
    """Test @cached decorator with custom cache instance."""
    cache = TTLCache(ttl_seconds=60)
    call_count = 0

    @cached(cache_instance=cache)
    def test_func(x: int) -> int:
        nonlocal call_count
        call_count += 1
        return x * 2

    result1 = test_func(5)
    assert result1 == 10
    assert call_count == 1

    result2 = test_func(5)
    assert result2 == 10
    assert call_count == 1


def test_cached_decorator_different_args():
    """Test @cached decorator with different arguments."""
    call_count = 0

    @cached(ttl=60)
    def test_func(x: int) -> int:
        nonlocal call_count
        call_count += 1
        return x * 2

    # Different args should cause cache miss
    test_func(5)
    test_func(10)

    assert call_count == 2  # Both should be cache misses
