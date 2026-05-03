# app/infrastructure/llm/client.py
"""OpenAI API client with caching and circuit breaker."""

from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any, Dict, List, Optional

from app.config import get_logger, settings
from app.domains.markets.adapters.base import Venue
from app.infrastructure.http.cache import openai_cache
from app.infrastructure.http.resilience import openai_circuit

logger = get_logger(__name__)

try:
    import openai
except ImportError:  # pragma: no cover - handled at runtime
    openai = None  # type: ignore[assignment]


def build_signal_cache_key(
    venue: Venue,
    market_id: str,
    event_title: str,
    market_question: str,
    yes_price: float,
    news_summary: str,
    top_headlines: str,
) -> str:
    cache_input = (
        f"{venue}:{market_id}:{event_title}:{market_question}:"
        f"{yes_price:.4f}:{news_summary[:200]}:{top_headlines[:200]}"
    )
    return f"openai:{hashlib.md5(cache_input.encode()).hexdigest()}"


class OpenAIClient:
    """Client for interacting with OpenAI API.

    Provides async methods with built-in caching and circuit breaker protection.
    """

    def __init__(self):
        """Initialize OpenAI client."""
        self.api_key = settings.openai_api_key
        self.client = None
        self._use_new_api = False
        if openai is not None and self.api_key:
            # Support both old (v0.x) and new (v1.0+) OpenAI API formats
            try:
                # Try new API format (v1.0+)
                from openai import OpenAI

                self.client = OpenAI(api_key=self.api_key)
                self._use_new_api = True
            except (ImportError, AttributeError):
                # Fall back to old API format (v0.x)
                openai.api_key = self.api_key
                self._use_new_api = False

    def _generate_signal_sync(
        self,
        event_title: str,
        market_question: str,
        yes_price: float,
        news_summary: str,
        top_headlines: str,
        tag_label: str = "",
        venue: Venue = "polymarket",
        market_id: str = "unknown-market",
    ) -> Dict[str, Any]:
        """Generate a trading signal using OpenAI.

        Args:
            event_title: Title of the event
            market_question: The market question
            yes_price: Current YES price (0-1)
            news_summary: Summary of recent news
            top_headlines: Top headlines separated by semicolons
            tag_label: Optional tag/label for the market

        Returns:
            Dictionary with signal data including:
            - direction: "up", "down", or "flat"
            - model_prob: Delta from current price
            - model_prob_abs: Absolute probability estimate
            - expected_delta_range: [lo, hi] probability range
            - confidence: "low", "medium", or "high"
            - rationale: Explanation string
        """
        if openai is None or not self.api_key:
            logger.warning("OPENAI_API_KEY missing or openai not installed")
            raise RuntimeError("OpenAI is not available")

        system_msg = (
            "You are a careful prediction market analyst. "
            "Given a prediction market, its current YES price and recent news, "
            "you estimate the TRUE probability that YES is correct over the next few days. "
            "You must respond ONLY with a single JSON object."
        )

        user_msg = f"""
Event: {event_title}
Market: {market_question}
Bracket / label: {tag_label}

Current market YES price: {yes_price:.4f}
Implied market probability: {yes_price * 100:.2f}%

Summary of recent news (from Tavily):
{news_summary or "No major news surfaced in this window."}

Top headlines:
{top_headlines or "None available."}

Based on this information, estimate the TRUE probability that YES is correct
over the relevant horizon (a few days to the event), relative to the current
market price.

Return a JSON object with the following keys:
- "model_prob_abs": float between 0 and 1 (your best estimate of the TRUE probability of YES)
- "direction": string, one of "up", "down", or "flat" relative to the market's implied probability
- "expected_delta_range": list of two floats [lo, hi] in probability points
  (0–1 space) capturing how much you expect the price could move
  if the market corrected
- "confidence": string, one of "low", "medium", "high"
  * Use "high" only when you have strong, recent, and diverse evidence supporting your estimate
  * Use "medium" when you have moderate evidence or some uncertainty
  * Use "low" when evidence is sparse, conflicting, or the situation is highly uncertain
- "rationale": a short 1–3 sentence explanation referencing the news
"""

        # Create cache key from input parameters
        cache_key = build_signal_cache_key(
            venue,
            market_id,
            event_title,
            market_question,
            yes_price,
            news_summary,
            top_headlines,
        )

        # Try cache first
        cached_result = openai_cache.get(cache_key)
        if cached_result is not None:
            logger.debug("Cache hit for OpenAI", event_title=event_title)
            return cached_result

        # Check circuit breaker
        if not openai_circuit.can_attempt():
            logger.warning("OpenAI circuit breaker is OPEN")
            raise RuntimeError("OpenAI circuit breaker is OPEN")

        # Cache miss - call OpenAI
        try:
            logger.debug("Cache miss - calling OpenAI API", event_title=event_title)
            if self.client and self._use_new_api:
                # New API format (v1.0+)
                completion = self.client.chat.completions.create(
                    model="gpt-4o-mini",  # gpt-5-mini doesn't exist yet, using gpt-4o-mini
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg},
                    ],
                    temperature=0.2,
                )
                raw_content = completion.choices[0].message.content
            else:
                # Old API format (v0.x)
                completion = openai.ChatCompletion.create(
                    model="gpt-4o-mini",  # gpt-5-mini doesn't exist yet, using gpt-4o-mini
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg},
                    ],
                    temperature=0.2,
                )
                raw_content = completion.choices[0].message["content"]
            data = json.loads(raw_content)
            openai_circuit.record_success()

            # Cache successful result
            openai_cache.set(cache_key, data)
            logger.debug("OpenAI API call successful and cached")
            return data
        except Exception as exc:
            openai_circuit.record_failure()
            logger.warning("OpenAI call failed", error=str(exc), exc_info=True)
            raise RuntimeError("OpenAI API error") from exc

    async def generate_signal(
        self,
        event_title: str,
        market_question: str,
        yes_price: float,
        news_summary: str,
        top_headlines: str,
        tag_label: str = "",
        venue: Venue = "polymarket",
        market_id: str = "unknown-market",
    ) -> Dict[str, Any]:
        """Generate a trading signal using OpenAI (async wrapper).

        Args:
            event_title: Title of the event
            market_question: The market question
            yes_price: Current YES price (0-1)
            news_summary: Summary of recent news
            top_headlines: Top headlines separated by semicolons
            tag_label: Optional tag/label for the market

        Returns:
            Dictionary with signal data including:
            - direction: "up", "down", or "flat"
            - model_prob: Delta from current price
            - model_prob_abs: Absolute probability estimate
            - expected_delta_range: [lo, hi] probability range
            - confidence: "low", "medium", or "high"
            - rationale: Explanation string
        """
        # Run sync OpenAI call in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._generate_signal_sync,
            event_title,
            market_question,
            yes_price,
            news_summary,
            top_headlines,
            tag_label,
            venue,
            market_id,
        )

    def _summarize_news_with_sentiment_sync(
        self,
        articles: List[Dict[str, Any]],
        event_title: str,
        market_question: str,
    ) -> str:
        """Generate a comprehensive news summary using OpenAI, weighted by sentiment.

        Args:
            articles: List of article dicts with sentiment labels (bullish, bearish, neutral)
            event_title: Title of the event
            market_question: The market question

        Returns:
            A comprehensive summary string
        """
        if openai is None or not self.api_key:
            logger.warning("OPENAI_API_KEY missing or openai not installed")
            raise RuntimeError("OpenAI is not available")

        # Group articles by sentiment
        bullish_articles = [a for a in articles if a.get("sentiment") == "bullish"]
        bearish_articles = [a for a in articles if a.get("sentiment") == "bearish"]
        neutral_articles = [a for a in articles if a.get("sentiment") == "neutral"]

        # Count articles by sentiment
        bullish_count = len(bullish_articles)
        bearish_count = len(bearish_articles)
        neutral_count = len(neutral_articles)
        total_count = len(articles)

        # Determine majority sentiment
        if bullish_count > bearish_count and bullish_count > neutral_count:
            majority_sentiment = "bullish"
            majority_count = bullish_count
        elif bearish_count > neutral_count:
            majority_sentiment = "bearish"
            majority_count = bearish_count
        else:
            majority_sentiment = "neutral"
            majority_count = neutral_count

        # Sample articles: at least one from each sentiment, then weight towards majority
        sampled_articles: List[Dict[str, Any]] = []

        # Always include at least one from each sentiment if available
        if bullish_articles:
            sampled_articles.append(bullish_articles[0])
        if bearish_articles:
            sampled_articles.append(bearish_articles[0])
        if neutral_articles:
            sampled_articles.append(neutral_articles[0])

        # Add more articles from majority sentiment (weighted sampling)
        # Calculate how many more to add based on proportion
        if total_count > 3:
            # Add proportionally more from majority sentiment
            # Take up to 50% of remaining articles from majority, rest distributed
            max_articles = min(12, total_count)
            remaining_slots = max_articles - len(sampled_articles)
            if remaining_slots > 0:
                majority_proportion = majority_count / total_count if total_count > 0 else 0.33
                # Calculate slots for majority sentiment (1.5x weight)
                majority_slots = max(1, int(remaining_slots * majority_proportion * 1.5))
                # Don't exceed remaining slots
                majority_slots = min(majority_slots, remaining_slots)

                if majority_sentiment == "bullish" and bullish_articles:
                    # Add more bullish articles (skip first one already added)
                    available_bullish = bullish_articles[1:]
                    for article in available_bullish[:majority_slots]:
                        if article not in sampled_articles and len(sampled_articles) < max_articles:
                            sampled_articles.append(article)
                elif majority_sentiment == "bearish" and bearish_articles:
                    # Add more bearish articles
                    available_bearish = bearish_articles[1:]
                    for article in available_bearish[:majority_slots]:
                        if article not in sampled_articles and len(sampled_articles) < max_articles:
                            sampled_articles.append(article)
                elif majority_sentiment == "neutral" and neutral_articles:
                    # Add more neutral articles
                    available_neutral = neutral_articles[1:]
                    for article in available_neutral[:majority_slots]:
                        if article not in sampled_articles and len(sampled_articles) < max_articles:
                            sampled_articles.append(article)

                # Fill remaining slots with other articles (distributed across all sentiments)
                remaining = max_articles - len(sampled_articles)
                if remaining > 0:
                    all_remaining = [a for a in articles if a not in sampled_articles]
                    sampled_articles.extend(all_remaining[:remaining])

        # Limit to reasonable number for prompt
        sampled_articles = sampled_articles[:12]

        # Build article context for prompt
        article_contexts = []
        for idx, article in enumerate(sampled_articles, 1):
            title = article.get("title", "Untitled")
            snippet = article.get("snippet") or article.get("summary", "")
            source = article.get("source", "Unknown source")
            sentiment = article.get("sentiment", "neutral")
            article_contexts.append(
                f"Article {idx} ({sentiment.upper()}):\n"
                f"Title: {title}\n"
                f"Source: {source}\n"
                f"Content: {snippet[:300] if snippet else 'No content available'}\n"
            )

        system_msg = (
            "You are a financial news analyst. Your task is to synthesize a comprehensive "
            "summary of recent news articles related to a prediction market event. "
            "The summary should be weighted towards the sentiment category with the most articles, "
            "but also acknowledge perspectives from all sentiment categories. "
            "Provide a clear, concise summary that captures the key developments "
            "and their implications."
        )

        # Calculate percentages safely
        bullish_pct = (bullish_count / total_count * 100) if total_count > 0 else 0.0
        bearish_pct = (bearish_count / total_count * 100) if total_count > 0 else 0.0
        neutral_pct = (neutral_count / total_count * 100) if total_count > 0 else 0.0

        user_msg = f"""
Event: {event_title}
Market Question: {market_question}

Sentiment Distribution:
- Bullish articles: {bullish_count} ({bullish_pct:.1f}%)
- Bearish articles: {bearish_count} ({bearish_pct:.1f}%)
- Neutral articles: {neutral_count} ({neutral_pct:.1f}%)
- Majority sentiment: {majority_sentiment.upper()} ({majority_count} articles)

Articles to summarize:
{chr(10).join(article_contexts)}

Please provide a comprehensive summary that:
1. Acknowledges the majority sentiment ({majority_sentiment}) and gives it appropriate weight
2. Includes perspectives from all sentiment categories (bullish, bearish, neutral)
3. Synthesizes the key developments and their implications for the market
4. Is concise but informative (2-4 paragraphs)
5. Focuses on facts and developments rather than speculation

Summary:
"""

        # Create cache key from input parameters
        cache_input = (
            f"{event_title}:{market_question}:"
            f"{bullish_count}:{bearish_count}:{neutral_count}:"
            f"{':'.join(a.get('title', '')[:50] for a in sampled_articles[:5])}"
        )
        cache_key = f"openai:summary:{hashlib.md5(cache_input.encode()).hexdigest()}"

        # Try cache first
        cached_result = openai_cache.get(cache_key)
        if cached_result is not None:
            logger.debug("Cache hit for OpenAI news summary", event_title=event_title)
            return cached_result

        # Check circuit breaker
        if not openai_circuit.can_attempt():
            logger.warning("OpenAI circuit breaker is OPEN for summary generation")
            raise RuntimeError("OpenAI circuit breaker is OPEN")

        # Cache miss - call OpenAI
        try:
            logger.debug(
                "Cache miss - calling OpenAI API for news summary",
                event_title=event_title,
            )
            if self.client and self._use_new_api:
                # New API format (v1.0+)
                completion = self.client.chat.completions.create(
                    model="gpt-4o-mini",  # gpt-5-mini doesn't exist yet, using gpt-4o-mini
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg},
                    ],
                    temperature=0.3,  # Lower temperature for more consistent summaries
                )
                summary = completion.choices[0].message.content.strip()
            else:
                # Old API format (v0.x)
                completion = openai.ChatCompletion.create(
                    model="gpt-4o-mini",  # gpt-5-mini doesn't exist yet, using gpt-4o-mini
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg},
                    ],
                    temperature=0.3,  # Lower temperature for more consistent summaries
                )
                summary = completion.choices[0].message["content"].strip()
            openai_circuit.record_success()

            # Cache successful result
            openai_cache.set(cache_key, summary)
            logger.debug("OpenAI news summary generated and cached")
            return summary
        except Exception as exc:
            openai_circuit.record_failure()
            logger.warning("OpenAI summary call failed", error=str(exc), exc_info=True)
            raise

    async def summarize_news_with_sentiment(
        self,
        articles: List[Dict[str, Any]],
        event_title: str,
        market_question: str,
    ) -> str:
        """Generate a comprehensive news summary using OpenAI, weighted by sentiment.

        Async wrapper.

        Args:
            articles: List of article dicts with sentiment labels (bullish, bearish, neutral)
            event_title: Title of the event
            market_question: The market question

        Returns:
            A comprehensive summary string
        """
        # Run sync OpenAI call in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._summarize_news_with_sentiment_sync,
            articles,
            event_title,
            market_question,
        )


# Module-level singleton instance
_openai_client: Optional[OpenAIClient] = None


def get_openai_client() -> OpenAIClient:
    """Get the singleton OpenAIClient instance."""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAIClient()
    return _openai_client
