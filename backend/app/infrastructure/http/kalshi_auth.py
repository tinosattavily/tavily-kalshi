"""Kalshi API authentication using RSA-PSS signing."""

from __future__ import annotations

import base64
import time
from typing import TYPE_CHECKING, Dict, Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from app.config import get_logger, settings

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

logger = get_logger(__name__)

_private_key_cache: Optional["RSAPrivateKey"] = None


def get_settings():
    """Get settings instance (for easier mocking in tests)."""
    return settings


def _load_private_key() -> Optional["RSAPrivateKey"]:
    """Load RSA private key from file or base64 env var. Cached."""
    global _private_key_cache

    if _private_key_cache is not None:
        return _private_key_cache

    current_settings = get_settings()
    key_data: Optional[bytes] = None

    # Try file path first
    if current_settings.kalshi_private_key_path:
        try:
            with open(current_settings.kalshi_private_key_path, "rb") as f:
                key_data = f.read()
            logger.debug("Loaded Kalshi private key from file")
        except FileNotFoundError:
            logger.warning("Kalshi private key file not found")
        except Exception as e:
            logger.warning("Failed to read Kalshi private key file", error=str(e))

    # Fall back to base64
    if key_data is None and current_settings.kalshi_private_key_base64:
        try:
            key_data = base64.b64decode(current_settings.kalshi_private_key_base64)
            logger.debug("Loaded Kalshi private key from base64")
        except Exception as e:
            logger.warning("Failed to decode base64 private key", error=str(e))

    if key_data is None:
        return None

    try:
        _private_key_cache = serialization.load_pem_private_key(key_data, password=None)
        return _private_key_cache
    except Exception as e:
        logger.error("Failed to load private key", error=str(e))
        return None


def is_kalshi_auth_available() -> bool:
    """Check if Kalshi authentication is configured."""
    current_settings = get_settings()
    has_key_id = bool(current_settings.kalshi_api_key_id)
    has_private_key = _load_private_key() is not None
    return has_key_id and has_private_key


def sign_request(method: str, path: str, timestamp: str) -> str:
    """Sign a request using RSA-PSS.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path without query params (e.g., /trade-api/v2/markets/ABC)
        timestamp: Unix timestamp in milliseconds as string

    Returns:
        Base64-encoded signature

    Raises:
        RuntimeError: If private key not available
    """
    private_key = _load_private_key()
    if private_key is None:
        raise RuntimeError("Kalshi private key not configured")

    # Message format: timestamp + method + path
    message = f"{timestamp}{method}{path}".encode("utf-8")

    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )

    return base64.b64encode(signature).decode("utf-8")


def get_auth_headers(method: str, path: str) -> Dict[str, str]:
    """Generate authentication headers for a Kalshi API request.

    Args:
        method: HTTP method
        path: Request path (without base URL, without query params)

    Returns:
        Dict with KALSHI-ACCESS-KEY, KALSHI-ACCESS-TIMESTAMP, KALSHI-ACCESS-SIGNATURE
    """
    current_settings = get_settings()
    timestamp = str(int(time.time() * 1000))  # Milliseconds
    signature = sign_request(method, path, timestamp)

    return {
        "KALSHI-ACCESS-KEY": current_settings.kalshi_api_key_id,
        "KALSHI-ACCESS-TIMESTAMP": timestamp,
        "KALSHI-ACCESS-SIGNATURE": signature,
    }
