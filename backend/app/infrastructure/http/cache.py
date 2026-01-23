"""Caching utilities with TTL support and Redis backend."""

from __future__ import annotations

import functools
import json
import time
from typing import Any, Callable, TypeVar

from app.config import get_logger, settings

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# Try to import Redis, fall back to in-memory if not available
try:
    import redis
    from redis.exceptions import ConnectionError, RedisError

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, falling back to in-memory cache")


class TTLCache:
    """Simple TTL cache implementation (in-memory fallback)."""

    def __init__(self, ttl_seconds: int = 300):
        """Initialize cache with TTL in seconds."""
        self._cache: dict[str, tuple[Any, float]] = {}
        self.ttl = ttl_seconds

    def get(self, key: str) -> Any | None:
        """Get value from cache if not expired."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            # Expired, remove it
            del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set value in cache with current timestamp."""
        self._cache[key] = (value, time.time())

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        now = time.time()
        expired = [k for k, (_, ts) in self._cache.items() if now - ts >= self.ttl]
        for k in expired:
            del self._cache[k]
        return len(expired)


class RedisCache:
    """Redis-backed cache with TTL support."""

    def __init__(
        self,
        ttl_seconds: int = 300,
        redis_url: str | None = None,
        redis_host: str | None = None,
        redis_port: int | None = None,
        redis_db: int | None = None,
        redis_password: str | None = None,
    ):
        """Initialize Redis cache."""
        self.ttl = ttl_seconds
        self._client: redis.Redis | None = None
        self._connected = False

        # Use URL if provided, otherwise use individual parameters
        if redis_url:
            try:
                self._client = redis.from_url(
                    redis_url,
                    decode_responses=False,  # We'll handle serialization ourselves
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # Test connection
                self._client.ping()
                self._connected = True
                url_display = redis_url.split("@")[-1] if "@" in redis_url else "***"
                logger.info("Redis cache connected via URL", url=url_display)
            except (ConnectionError, RedisError) as e:
                logger.warning(
                    "Failed to connect to Redis, falling back to in-memory cache",
                    error=str(e),
                )
                self._client = None
        elif redis_host:
            try:
                self._client = redis.Redis(
                    host=redis_host,
                    port=redis_port or 6379,
                    db=redis_db or 0,
                    password=redis_password,
                    decode_responses=False,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # Test connection
                self._client.ping()
                self._connected = True
                logger.info("Redis cache connected", host=redis_host, port=redis_port or 6379)
            except (ConnectionError, RedisError) as e:
                logger.warning(
                    "Failed to connect to Redis, falling back to in-memory cache",
                    error=str(e),
                )
                self._client = None

        # Fallback to in-memory cache if Redis not available
        if not self._connected:
            self._fallback_cache = TTLCache(ttl_seconds=ttl_seconds)

    def _serialize(self, value: Any) -> bytes:
        """Serialize value to bytes for Redis storage."""
        try:
            return json.dumps(value).encode("utf-8")
        except (TypeError, ValueError) as e:
            logger.warning("Failed to serialize value for cache", error=str(e))
            raise

    def _deserialize(self, value: bytes) -> Any:
        """Deserialize value from bytes."""
        try:
            return json.loads(value.decode("utf-8"))
        except (TypeError, ValueError, UnicodeDecodeError) as e:
            logger.warning("Failed to deserialize value from cache", error=str(e))
            return None

    def get(self, key: str) -> Any | None:
        """Get value from cache if not expired."""
        if not self._connected or not self._client:
            return self._fallback_cache.get(key)

        try:
            value = self._client.get(key)
            if value is None:
                return None
            return self._deserialize(value)
        except (ConnectionError, RedisError) as e:
            logger.warning(
                "Redis get failed, falling back to in-memory",
                error=str(e),
                key=key[:50],
            )
            self._connected = False
            if not hasattr(self, "_fallback_cache"):
                self._fallback_cache = TTLCache(ttl_seconds=self.ttl)
            return self._fallback_cache.get(key)

    def set(self, key: str, value: Any) -> None:
        """Set value in cache with TTL."""
        if not self._connected or not self._client:
            self._fallback_cache.set(key, value)
            return

        try:
            serialized = self._serialize(value)
            self._client.setex(key, self.ttl, serialized)
        except (ConnectionError, RedisError) as e:
            logger.warning(
                "Redis set failed, falling back to in-memory",
                error=str(e),
                key=key[:50],
            )
            self._connected = False
            if not hasattr(self, "_fallback_cache"):
                self._fallback_cache = TTLCache(ttl_seconds=self.ttl)
            self._fallback_cache.set(key, value)

    def clear(self) -> None:
        """Clear all cached values."""
        if not self._connected or not self._client:
            self._fallback_cache.clear()
            return

        try:
            # Note: This clears the entire Redis database, use with caution
            # In production, consider using key prefixes and clearing by pattern
            self._client.flushdb()
        except (ConnectionError, RedisError) as e:
            logger.warning("Redis clear failed", error=str(e))
            if not hasattr(self, "_fallback_cache"):
                self._fallback_cache = TTLCache(ttl_seconds=self.ttl)
            self._fallback_cache.clear()

    def cleanup_expired(self) -> int:
        """Redis handles expiration automatically, but we can check for expired keys."""
        if not self._connected or not self._client:
            return self._fallback_cache.cleanup_expired()

        # Redis handles TTL automatically, so this is mostly a no-op
        # But we can return 0 to indicate no manual cleanup needed
        return 0


def _create_cache(ttl_seconds: int, cache_name: str) -> TTLCache | RedisCache:
    """Create cache instance based on configuration."""
    if settings.use_redis_cache and REDIS_AVAILABLE:
        return RedisCache(
            ttl_seconds=ttl_seconds,
            redis_url=settings.redis_url,
            redis_host=settings.redis_host,
            redis_port=settings.redis_port,
            redis_db=settings.redis_db,
            redis_password=settings.redis_password,
        )
    else:
        if settings.use_redis_cache:
            logger.warning(
                "Redis cache requested but not available, using in-memory cache",
                cache_name=cache_name,
            )
        return TTLCache(ttl_seconds=ttl_seconds)


# Global caches - use Redis if configured, otherwise in-memory
polymarket_cache = _create_cache(ttl_seconds=30, cache_name="polymarket")  # 30 second TTL
tavily_cache = _create_cache(ttl_seconds=300, cache_name="tavily")  # 5 minute TTL
openai_cache = _create_cache(ttl_seconds=600, cache_name="openai")  # 10 minute TTL
kalshi_cache = _create_cache(ttl_seconds=30, cache_name="kalshi")  # 30 second TTL


def cached(ttl: int = 300, cache_instance: TTLCache | RedisCache | None = None):
    """Decorator for caching function results with TTL."""
    cache = cache_instance or TTLCache(ttl_seconds=ttl)

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create cache key from function name and arguments
            key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Try cache first
            cached_value = cache.get(key)
            if cached_value is not None:
                logger.debug("Cache hit", function=func.__name__, key=key[:50])
                return cached_value

            # Cache miss, compute value
            logger.debug("Cache miss", function=func.__name__, key=key[:50])
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result

        return wrapper  # type: ignore[return-value]

    return decorator
