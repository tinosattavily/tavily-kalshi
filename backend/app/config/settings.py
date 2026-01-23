# app/config/settings.py
"""Environment variable configuration."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.config.constants import KalshiAPI

# Load .env file if it exists (before reading environment variables)
try:
    from dotenv import load_dotenv

    # Load .env from project root (one level up from backend/)
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass


def _get_env(name: str) -> Optional[str]:
    """Get environment variable, stripping whitespace."""
    value = os.getenv(name)
    return value.strip() if value else None


@dataclass
class Settings:
    """Central place to read environment variables for the backend."""

    openai_api_key: Optional[str] = _get_env("OPENAI_API_KEY")
    tavily_api_key: Optional[str] = _get_env("TAVILY_API_KEY")
    mongodb_uri: Optional[str] = _get_env("MONGODB_URI")
    # Redis configuration
    redis_url: Optional[str] = _get_env("REDIS_URL")
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    redis_password: Optional[str] = _get_env("REDIS_PASSWORD")
    # Cache configuration
    use_redis_cache: bool = os.getenv("USE_REDIS_CACHE", "false").lower() in ("true", "1", "yes")
    # Kalshi API configuration
    kalshi_api_key_id: Optional[str] = _get_env("KALSHI_API_KEY_ID")
    kalshi_private_key_path: Optional[str] = _get_env("KALSHI_PRIVATE_KEY_PATH")
    kalshi_private_key_base64: Optional[str] = _get_env("KALSHI_PRIVATE_KEY_BASE64")
    kalshi_env: str = os.getenv("KALSHI_ENV", "demo")

    @property
    def kalshi_base_url(self) -> str:
        """Get Kalshi API base URL based on environment."""
        if self.kalshi_env == "production":
            return KalshiAPI.PROD_BASE
        return KalshiAPI.DEMO_BASE


settings = Settings()
