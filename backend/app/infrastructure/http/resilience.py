"""Error recovery utilities: retry logic and circuit breakers."""

from __future__ import annotations

import asyncio
import functools
import logging
import time
from enum import Enum
from typing import Any, Callable, TypeVar

from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])
AsyncF = TypeVar("AsyncF", bound=Callable[..., Any])


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Simple circuit breaker implementation."""

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0,
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            success_threshold: Number of successes in half-open to close circuit
            timeout: Seconds to wait before trying half-open state
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: float | None = None

    def record_success(self) -> None:
        """Record a successful operation."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                logger.info("Circuit breaker closing", breaker=str(self))
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self) -> None:
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            logger.warning(
                "Circuit breaker reopening after failure in half-open",
                breaker=str(self),
            )
            self.state = CircuitState.OPEN
            self.success_count = 0
        elif self.failure_count >= self.failure_threshold:
            logger.error("Circuit breaker opening", breaker=str(self), failures=self.failure_count)
            self.state = CircuitState.OPEN

    def can_attempt(self) -> bool:
        """Check if request can be attempted."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if (
                self.last_failure_time is not None
                and time.time() - self.last_failure_time >= self.timeout
            ):
                logger.info("Circuit breaker entering half-open state", breaker=str(self))
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                return True
            return False

        # HALF_OPEN
        return True

    def reset(self) -> None:
        """Manually reset the circuit breaker to CLOSED state."""
        logger.info("Circuit breaker manually reset", breaker=str(self))
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    def __str__(self) -> str:
        """String representation."""
        return f"CircuitBreaker(state={self.state.value}, failures={self.failure_count})"


# Global circuit breakers for external services
polymarket_circuit = CircuitBreaker(failure_threshold=5, timeout=30.0)
tavily_circuit = CircuitBreaker(failure_threshold=5, timeout=60.0)
openai_circuit = CircuitBreaker(failure_threshold=3, timeout=120.0)


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
):
    """Decorator for retrying functions with exponential backoff."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=base_delay, max=max_delay),
        retry=retry_if_exception_type(exceptions),
        after=after_log(logger, logging.INFO),
        reraise=True,
    )


def with_circuit_breaker(circuit: CircuitBreaker):
    """Decorator for circuit breaker protection."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not circuit.can_attempt():
                raise RuntimeError(f"Circuit breaker is OPEN for {func.__name__}")

            try:
                result = func(*args, **kwargs)
                circuit.record_success()
                return result
            except Exception as exc:
                circuit.record_failure()
                raise exc

        return wrapper  # type: ignore[return-value]

    return decorator


def _safe_error_message(exc: Exception) -> str:
    try:
        return str(exc)
    except Exception:
        return repr(exc)


async def with_async_retry(
    func: AsyncF,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Async retry helper with exponential backoff."""
    attempt = 0
    last_exception: Exception | None = None

    function_name = getattr(func, "__name__", func.__class__.__name__)

    while attempt < max_attempts:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            attempt += 1
            last_exception = e
            if attempt >= max_attempts:
                logger.error(
                    "Max retry attempts reached",
                    function=function_name,
                    attempts=attempt,
                    error=_safe_error_message(e),
                )
                raise

            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            logger.warning(
                "Retrying after failure",
                function=function_name,
                attempt=attempt,
                max_attempts=max_attempts,
                delay=delay,
                error=_safe_error_message(e),
            )
            await asyncio.sleep(delay)

    if last_exception:
        raise last_exception
    raise RuntimeError("Retry logic failed unexpectedly")
