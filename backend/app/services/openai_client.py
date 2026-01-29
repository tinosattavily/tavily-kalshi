"""OpenAI API client with caching and circuit breaker."""

from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any, Optional

from app.config import settings
from app.core.cache import openai_cache
from app.core.logging_config import get_logger
from app.core.resilience import openai_circuit

logger = get_logger(__name__)

try:
    import openai
except ImportError:  # pragma: no cover - handled at runtime
    openai = None  # type: ignore[assignment]


class OpenAIClient:
    """Client for interacting with OpenAI API.

    Provides async methods with built-in caching and circuit breaker protection.
    """

    def __init__(self) -> None:
        """Initialize OpenAI client."""
        self.api_key = settings.openai_api_key
        self.client = None
        self._use_new_api = False

        if openai is not None and self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                self._use_new_api = True
            except (ImportError, AttributeError):
                openai.api_key = self.api_key
                self._use_new_api = False

    def _ensure_available(self) -> None:
        """Raise if OpenAI is not configured."""
        if openai is None or not self.api_key:
            logger.warning("OPENAI_API_KEY missing or openai not installed")
            raise RuntimeError("OpenAI is not available")

    def _check_circuit_breaker(self, operation: str) -> None:
        """Check circuit breaker state and raise if open."""
        if not openai_circuit.can_attempt():
            logger.warning(f"OpenAI circuit breaker is OPEN for {operation}")
            raise RuntimeError("OpenAI circuit breaker is OPEN")

    def _call_chat_completion(
        self,
        system_msg: str,
        user_msg: str,
        temperature: float = 0.2,
    ) -> str:
        """Make a chat completion request and return the content."""
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]

        if self.client and self._use_new_api:
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=temperature,
            )
            return completion.choices[0].message.content
        else:
            completion = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=temperature,
            )
            return completion.choices[0].message["content"]

    def _generate_signal_sync(
        self,
        event_title: str,
        market_question: str,
        yes_price: float,
        news_summary: str,
        top_headlines: str,
        tag_label: str = "",
    ) -> dict[str, Any]:
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
        self._ensure_available()

        system_msg = (
            "You are a careful prediction market analyst. "
            "Given a Polymarket market, its current YES price and recent news, "
            "you estimate the TRUE probability that YES is correct over the next few days. "
            "You must respond ONLY with a single JSON object."
        )

        user_msg = f"""
Event: {event_title}
Market: {market_question}
Bracket / label: {tag_label}

Current Polymarket YES price: {yes_price:.4f}
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
  (0-1 space) capturing how much you expect the price could move
  if the market corrected
- "confidence": string, one of "low", "medium", "high"
  * Use "high" only when you have strong, recent, and diverse evidence supporting your estimate
  * Use "medium" when you have moderate evidence or some uncertainty
  * Use "low" when evidence is sparse, conflicting, or the situation is highly uncertain
- "rationale": a short 1-3 sentence explanation referencing the news
"""

        cache_input = (
            f"{event_title}:{market_question}:{yes_price:.4f}:"
            f"{news_summary[:200]}:{top_headlines[:200]}"
        )
        cache_key = f"openai:{hashlib.md5(cache_input.encode()).hexdigest()}"

        cached_result = openai_cache.get(cache_key)
        if cached_result is not None:
            logger.debug("Cache hit for OpenAI", event_title=event_title)
            return cached_result

        self._check_circuit_breaker("signal generation")

        try:
            logger.debug("Cache miss - calling OpenAI API", event_title=event_title)
            raw_content = self._call_chat_completion(system_msg, user_msg)
            data = json.loads(raw_content)
            openai_circuit.record_success()
            openai_cache.set(cache_key, data)
            logger.debug("OpenAI API call successful and cached")
            return data
        except Exception as exc:
            openai_circuit.record_failure()
            logger.warning("OpenAI call failed", error=str(exc), exc_info=True)
            raise

    async def generate_signal(
        self,
        event_title: str,
        market_question: str,
        yes_price: float,
        news_summary: str,
        top_headlines: str,
        tag_label: str = "",
    ) -> dict[str, Any]:
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
        )

    def _summarize_news_with_sentiment_sync(
        self,
        articles: list[dict[str, Any]],
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
        self._ensure_available()

        sentiment_groups = {
            "bullish": [a for a in articles if a.get("sentiment") == "bullish"],
            "bearish": [a for a in articles if a.get("sentiment") == "bearish"],
            "neutral": [a for a in articles if a.get("sentiment") == "neutral"],
        }

        counts = {sentiment: len(group) for sentiment, group in sentiment_groups.items()}
        total_count = len(articles)

        majority_sentiment = max(counts, key=counts.get)
        majority_count = counts[majority_sentiment]

        sampled_articles = self._sample_articles_by_sentiment(
            sentiment_groups, majority_sentiment, total_count
        )

        article_contexts = self._build_article_contexts(sampled_articles)

        system_msg = (
            "You are a financial news analyst. Your task is to synthesize a comprehensive "
            "summary of recent news articles related to a prediction market event. "
            "The summary should be weighted towards the sentiment category with the most articles, "
            "but also acknowledge perspectives from all sentiment categories. "
            "Provide a clear, concise summary that captures the key developments "
            "and their implications."
        )

        def pct(count: int) -> float:
            return (count / total_count * 100) if total_count > 0 else 0.0

        user_msg = f"""
Event: {event_title}
Market Question: {market_question}

Sentiment Distribution:
- Bullish articles: {counts['bullish']} ({pct(counts['bullish']):.1f}%)
- Bearish articles: {counts['bearish']} ({pct(counts['bearish']):.1f}%)
- Neutral articles: {counts['neutral']} ({pct(counts['neutral']):.1f}%)
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

        cache_input = (
            f"{event_title}:{market_question}:"
            f"{counts['bullish']}:{counts['bearish']}:{counts['neutral']}:"
            f"{':'.join(a.get('title', '')[:50] for a in sampled_articles[:5])}"
        )
        cache_key = f"openai:summary:{hashlib.md5(cache_input.encode()).hexdigest()}"

        cached_result = openai_cache.get(cache_key)
        if cached_result is not None:
            logger.debug("Cache hit for OpenAI news summary", event_title=event_title)
            return cached_result

        self._check_circuit_breaker("summary generation")

        try:
            logger.debug(
                "Cache miss - calling OpenAI API for news summary",
                event_title=event_title,
            )
            summary = self._call_chat_completion(system_msg, user_msg, temperature=0.3).strip()
            openai_circuit.record_success()
            openai_cache.set(cache_key, summary)
            logger.debug("OpenAI news summary generated and cached")
            return summary
        except Exception as exc:
            openai_circuit.record_failure()
            logger.warning("OpenAI summary call failed", error=str(exc), exc_info=True)
            raise

    def _sample_articles_by_sentiment(
        self,
        sentiment_groups: dict[str, list[dict[str, Any]]],
        majority_sentiment: str,
        total_count: int,
    ) -> list[dict[str, Any]]:
        """Sample articles with weighting towards majority sentiment."""
        sampled: list[dict[str, Any]] = []

        for group in sentiment_groups.values():
            if group:
                sampled.append(group[0])

        if total_count <= 3:
            return sampled[:12]

        max_articles = min(12, total_count)
        remaining_slots = max_articles - len(sampled)

        if remaining_slots > 0:
            majority_proportion = (
                len(sentiment_groups[majority_sentiment]) / total_count
                if total_count > 0
                else 0.33
            )
            majority_slots = min(max(1, int(remaining_slots * majority_proportion * 1.5)),
                                 remaining_slots)

            majority_articles = sentiment_groups[majority_sentiment][1:]
            for article in majority_articles[:majority_slots]:
                if article not in sampled and len(sampled) < max_articles:
                    sampled.append(article)

            all_articles = [
                a
                for group in sentiment_groups.values()
                for a in group
                if a not in sampled
            ]
            remaining = max_articles - len(sampled)
            sampled.extend(all_articles[:remaining])

        return sampled[:12]

    def _build_article_contexts(self, articles: list[dict[str, Any]]) -> list[str]:
        """Build formatted article context strings for the prompt."""
        contexts = []
        for idx, article in enumerate(articles, 1):
            title = article.get("title", "Untitled")
            snippet = article.get("snippet") or article.get("summary", "")
            source = article.get("source", "Unknown source")
            sentiment = article.get("sentiment", "neutral")
            content = snippet[:300] if snippet else "No content available"
            contexts.append(
                f"Article {idx} ({sentiment.upper()}):\n"
                f"Title: {title}\n"
                f"Source: {source}\n"
                f"Content: {content}\n"
            )
        return contexts

    async def summarize_news_with_sentiment(
        self,
        articles: list[dict[str, Any]],
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
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._summarize_news_with_sentiment_sync,
            articles,
            event_title,
            market_question,
        )


_openai_client: Optional[OpenAIClient] = None


def get_openai_client() -> OpenAIClient:
    """Get the singleton OpenAIClient instance."""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAIClient()
    return _openai_client
