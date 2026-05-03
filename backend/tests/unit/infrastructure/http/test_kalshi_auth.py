"""Tests for Kalshi authentication module."""

import base64
import time
from unittest.mock import MagicMock, patch

import pytest


class TestSignRequest:
    """Tests for sign_request function."""

    def test_sign_request_returns_base64_string(self):
        """sign_request should return a base64-encoded signature."""
        from cryptography.hazmat.primitives.asymmetric import rsa

        # Generate a test key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        with patch("app.infrastructure.http.kalshi_auth._load_private_key") as mock_load:
            mock_load.return_value = private_key

            from app.infrastructure.http.kalshi_auth import sign_request

            signature = sign_request("GET", "/trade-api/v2/markets/TEST", "1234567890")

            # Should be valid base64
            decoded = base64.b64decode(signature)
            assert len(decoded) > 0

    def test_sign_request_raises_when_no_key(self):
        """sign_request should raise RuntimeError when key not available."""
        with patch("app.infrastructure.http.kalshi_auth._load_private_key") as mock_load:
            mock_load.return_value = None

            from app.infrastructure.http.kalshi_auth import sign_request

            with pytest.raises(RuntimeError, match="private key not configured"):
                sign_request("GET", "/trade-api/v2/markets/TEST", "1234567890")


class TestGetAuthHeaders:
    """Tests for get_auth_headers function."""

    def test_get_auth_headers_includes_required_headers(self):
        """get_auth_headers should return all required Kalshi headers."""
        from cryptography.hazmat.primitives.asymmetric import rsa

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        mock_settings = MagicMock()
        mock_settings.kalshi_api_key_id = "test-key-id"

        with patch("app.infrastructure.http.kalshi_auth._load_private_key") as mock_load:
            mock_load.return_value = private_key
            with patch("app.infrastructure.http.kalshi_auth.get_settings") as mock_get_settings:
                mock_get_settings.return_value = mock_settings

                from app.infrastructure.http.kalshi_auth import get_auth_headers

                headers = get_auth_headers("GET", "/trade-api/v2/markets/TEST")

                assert "KALSHI-ACCESS-KEY" in headers
                assert "KALSHI-ACCESS-TIMESTAMP" in headers
                assert "KALSHI-ACCESS-SIGNATURE" in headers
                assert headers["KALSHI-ACCESS-KEY"] == "test-key-id"


class TestIsKalshiAuthAvailable:
    """Tests for is_kalshi_auth_available function."""

    def test_returns_false_when_no_key_id(self):
        """Should return False when API key ID is missing."""
        mock_settings = MagicMock()
        mock_settings.kalshi_api_key_id = ""
        mock_settings.kalshi_private_key_path = ""
        mock_settings.kalshi_private_key_base64 = ""

        with patch("app.infrastructure.http.kalshi_auth.get_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            with patch("app.infrastructure.http.kalshi_auth._load_private_key") as mock_load:
                mock_load.return_value = None

                from app.infrastructure.http.kalshi_auth import is_kalshi_auth_available

                assert is_kalshi_auth_available() is False

    def test_returns_true_when_configured(self):
        """Should return True when both key ID and private key are available."""
        from cryptography.hazmat.primitives.asymmetric import rsa

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        mock_settings = MagicMock()
        mock_settings.kalshi_api_key_id = "test-key-id"

        with patch("app.infrastructure.http.kalshi_auth.get_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            with patch("app.infrastructure.http.kalshi_auth._load_private_key") as mock_load:
                mock_load.return_value = private_key

                from app.infrastructure.http.kalshi_auth import is_kalshi_auth_available

                assert is_kalshi_auth_available() is True
