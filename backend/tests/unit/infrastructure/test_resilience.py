"""Tests for Resilience utilities."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, patch

import pytest

from app.infrastructure.http.resilience import (
    CircuitBreaker,
    CircuitState,
    with_async_retry,
    with_circuit_breaker,
    with_retry,
)


def test_circuit_breaker_closed_state():
    """Test CircuitBreaker in CLOSED state (normal operation)."""
    cb = CircuitBreaker(failure_threshold=3, timeout=10.0)

    assert cb.state == CircuitState.CLOSED
    assert cb.can_attempt() is True
    assert cb.failure_count == 0


def test_circuit_breaker_record_success():
    """Test CircuitBreaker record_success()."""
    cb = CircuitBreaker(failure_threshold=3, timeout=10.0)

    cb.record_success()
    assert cb.failure_count == 0

    # Record failures then success
    cb.record_failure()
    cb.record_failure()
    cb.record_success()
    assert cb.failure_count == 0


def test_circuit_breaker_record_failure():
    """Test CircuitBreaker record_failure()."""
    cb = CircuitBreaker(failure_threshold=3, timeout=10.0)

    cb.record_failure()
    assert cb.failure_count == 1
    assert cb.last_failure_time is not None


def test_circuit_breaker_opens_on_threshold():
    """Test CircuitBreaker opens when failure threshold reached."""
    cb = CircuitBreaker(failure_threshold=3, timeout=10.0)

    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED

    cb.record_failure()  # Third failure
    assert cb.state == CircuitState.OPEN
    assert cb.can_attempt() is False


def test_circuit_breaker_half_open_recovery():
    """Test CircuitBreaker half-open state and recovery."""
    cb = CircuitBreaker(failure_threshold=2, success_threshold=2, timeout=0.1)

    # Open the circuit
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    # Wait for timeout
    time.sleep(0.2)

    # Should transition to half-open
    assert cb.can_attempt() is True
    assert cb.state == CircuitState.HALF_OPEN

    # Record successes to close
    cb.record_success()
    cb.record_success()
    assert cb.state == CircuitState.CLOSED


def test_circuit_breaker_half_open_failure():
    """Test CircuitBreaker failure in half-open state."""
    cb = CircuitBreaker(failure_threshold=2, success_threshold=2, timeout=0.1)

    # Open the circuit
    cb.record_failure()
    cb.record_failure()
    time.sleep(0.2)
    cb.can_attempt()  # Transition to half-open

    # Failure in half-open should reopen
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.success_count == 0


def test_circuit_breaker_reset():
    """Test CircuitBreaker reset()."""
    cb = CircuitBreaker(failure_threshold=2, timeout=10.0)

    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    cb.reset()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    assert cb.success_count == 0
    assert cb.last_failure_time is None


def test_circuit_breaker_timeout_handling():
    """Test CircuitBreaker timeout handling."""
    cb = CircuitBreaker(failure_threshold=2, timeout=0.1)

    # Open the circuit
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.can_attempt() is False

    # Wait for timeout
    time.sleep(0.2)

    # Should allow attempt after timeout
    assert cb.can_attempt() is True
    assert cb.state == CircuitState.HALF_OPEN


def test_with_retry_decorator():
    """Test with_retry decorator."""
    call_count = 0

    @with_retry(max_attempts=3, exceptions=(ValueError,))
    def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Temporary error")
        return "success"

    result = flaky_function()
    assert result == "success"
    assert call_count == 3


def test_with_retry_max_attempts_exceeded():
    """Test with_retry decorator with max attempts exceeded."""
    call_count = 0

    @with_retry(max_attempts=3, exceptions=(ValueError,))
    def always_fails():
        nonlocal call_count
        call_count += 1
        raise ValueError("Always fails")

    with pytest.raises(ValueError):
        always_fails()

    assert call_count == 3


def test_with_circuit_breaker_decorator():
    """Test with_circuit_breaker decorator."""
    cb = CircuitBreaker(failure_threshold=2, timeout=10.0)

    @with_circuit_breaker(cb)
    def test_function():
        return "success"

    result = test_function()
    assert result == "success"
    assert cb.failure_count == 0


def test_with_circuit_breaker_failure():
    """Test with_circuit_breaker decorator with failure."""
    cb = CircuitBreaker(failure_threshold=2, timeout=10.0)

    @with_circuit_breaker(cb)
    def failing_function():
        raise ValueError("Error")

    with pytest.raises(ValueError):
        failing_function()

    assert cb.failure_count == 1


def test_with_circuit_breaker_open():
    """Test with_circuit_breaker decorator when circuit is open."""
    cb = CircuitBreaker(failure_threshold=2, timeout=10.0)

    # Open the circuit
    cb.record_failure()
    cb.record_failure()

    @with_circuit_breaker(cb)
    def test_function():
        return "success"

    with pytest.raises(RuntimeError, match="Circuit breaker is OPEN"):
        test_function()


@pytest.mark.anyio(backend="asyncio")
async def test_with_async_retry_success():
    """Test with_async_retry with successful execution."""
    call_count = 0

    async def async_func():
        nonlocal call_count
        call_count += 1
        return "success"

    result = await with_async_retry(async_func)

    assert result == "success"
    assert call_count == 1


@pytest.mark.anyio(backend="asyncio")
async def test_with_async_retry_retry_logic():
    """Test with_async_retry retry logic."""
    call_count = 0

    async def flaky_async_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Temporary error")
        return "success"

    result = await with_async_retry(flaky_async_func, max_attempts=5)

    assert result == "success"
    assert call_count == 3


@pytest.mark.anyio(backend="asyncio")
async def test_with_async_retry_max_attempts():
    """Test with_async_retry with max attempts exceeded."""
    call_count = 0

    async def always_fails():
        nonlocal call_count
        call_count += 1
        raise ValueError("Always fails")

    with pytest.raises(ValueError):
        await with_async_retry(always_fails, max_attempts=3)

    assert call_count == 3


@pytest.mark.anyio(backend="asyncio")
async def test_with_async_retry_delay():
    """Test with_async_retry delay between retries."""
    call_count = 0

    async def flaky_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Error")
        return "success"

    with patch("asyncio.sleep") as mock_sleep:
        mock_sleep.return_value = AsyncMock()
        await with_async_retry(flaky_func, max_attempts=3, base_delay=0.1)

        # Should have slept once (between first and second attempt)
        assert mock_sleep.called


@pytest.mark.anyio(backend="asyncio")
async def test_with_async_retry_error_handling():
    """Test with_async_retry error handling."""

    async def error_func():
        raise RuntimeError("Test error")

    with pytest.raises(RuntimeError):
        await with_async_retry(error_func, max_attempts=2)
