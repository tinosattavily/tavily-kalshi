# app/domains/analysis/service.py
"""Analysis service - orchestrates signal generation and strategy decisions."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.config import get_logger
from app.domains.analysis.calculations import infer_market_prob
from app.domains.analysis.decision import build_decision_dict, decide_action
from app.domains.analysis.presets import get_preset_with_overrides
from app.domains.analysis.probability import (
    create_fallback_signal,
    create_signal_from_dict,
    generate_signal,
)
from app.domains.analysis.schemas import Signal
from app.shared.types import StrategyParams

logger = get_logger(__name__)


class AnalysisService:
    """Service class for analysis-related business logic.

    Orchestrates signal generation, strategy evaluation, and trading decisions.
    """

    def __init__(self, default_preset: str = "Balanced"):
        """Initialize AnalysisService.

        Args:
            default_preset: Default strategy preset name
        """
        self.default_preset = default_preset

    def get_strategy_params(
        self,
        preset_name: Optional[str] = None,
        overrides: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> StrategyParams:
        """Get strategy parameters with overrides.

        Args:
            preset_name: Preset name (uses default if not specified)
            overrides: Optional parameter overrides
            config: Optional config dict (for min_confidence)

        Returns:
            Merged strategy parameters
        """
        preset = preset_name or self.default_preset
        params = get_preset_with_overrides(preset, overrides)

        # Apply config min_confidence if present and not overridden
        if config and "min_confidence" in config:
            if not overrides or "min_confidence" not in overrides:
                params["min_confidence"] = config["min_confidence"]
                logger.debug(
                    "Applied min_confidence from config",
                    min_confidence=config["min_confidence"],
                    preset=preset,
                )

        return params

    async def generate_signal(
        self,
        market_snapshot: Dict[str, Any],
        event_context: Dict[str, Any],
        news_context: Dict[str, Any],
        horizon: str = "24h",
    ) -> Signal:
        """Generate trading signal from context.

        Args:
            market_snapshot: Market data dict
            event_context: Event context dict
            news_context: News context dict
            horizon: Analysis horizon

        Returns:
            Signal model
        """
        return await generate_signal(
            market_snapshot=market_snapshot,
            event_context=event_context,
            news_context=news_context,
            horizon=horizon,
        )

    def normalize_signal(
        self,
        signal_data: Any,
        market_snapshot: Dict[str, Any],
        news_context: Dict[str, Any],
        horizon: str = "24h",
    ) -> Signal:
        """Normalize signal data to Signal model.

        Handles Signal models, dicts, and None.

        Args:
            signal_data: Raw signal data
            market_snapshot: Market snapshot
            news_context: News context
            horizon: Analysis horizon

        Returns:
            Normalized Signal model
        """
        if signal_data is None:
            logger.warning("No signal found, creating fallback")
            p_mkt = infer_market_prob(market_snapshot)
            return create_fallback_signal(p_mkt, horizon, "No signal available")

        if isinstance(signal_data, Signal):
            return signal_data

        if isinstance(signal_data, dict):
            return create_signal_from_dict(
                signal_dict=signal_data,
                market_snapshot=market_snapshot,
                news_context=news_context,
                horizon=horizon,
            )

        logger.warning("Unexpected signal type", signal_type=type(signal_data).__name__)
        p_mkt = infer_market_prob(market_snapshot)
        return create_fallback_signal(p_mkt, horizon, "Invalid signal type")

    def apply_strategy(
        self,
        signal: Signal,
        params: StrategyParams,
        position_side: str = "flat",
        position_size: float = 0.0,
    ) -> Signal:
        """Apply strategy rules to signal.

        Args:
            signal: Signal model
            params: Strategy parameters
            position_side: Current position side
            position_size: Current position size

        Returns:
            Updated Signal with action and targets
        """
        return decide_action(
            signal=signal,
            position_side=position_side,
            position_size=position_size,
            params=params,
        )

    def build_decision(self, signal: Signal) -> Dict[str, Any]:
        """Build legacy decision dict from signal.

        Args:
            signal: Signal model

        Returns:
            Decision dict
        """
        return build_decision_dict(signal)

    async def process_analysis(
        self,
        market_snapshot: Dict[str, Any],
        event_context: Dict[str, Any],
        news_context: Dict[str, Any],
        horizon: str = "24h",
        preset_name: Optional[str] = None,
        strategy_overrides: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        position_side: str = "flat",
        position_size: float = 0.0,
    ) -> Dict[str, Any]:
        """Full analysis pipeline.

        Generates signal, applies strategy, returns results.

        Args:
            market_snapshot: Market data dict
            event_context: Event context dict
            news_context: News context dict
            horizon: Analysis horizon
            preset_name: Strategy preset name
            strategy_overrides: Strategy parameter overrides
            config: Configuration dict
            position_side: Current position side
            position_size: Current position size

        Returns:
            Dict with signal, decision, params
        """
        # Get strategy parameters
        params = self.get_strategy_params(
            preset_name=preset_name,
            overrides=strategy_overrides,
            config=config,
        )

        # Generate signal
        signal = await self.generate_signal(
            market_snapshot=market_snapshot,
            event_context=event_context,
            news_context=news_context,
            horizon=horizon,
        )

        # Apply strategy
        signal = self.apply_strategy(
            signal=signal,
            params=params,
            position_side=position_side,
            position_size=position_size,
        )

        # Build decision dict
        decision = self.build_decision(signal)

        # Log results
        logger.info(
            "signal_decision",
            recommended_action=signal.recommended_action,
            recommended_size_fraction=round(signal.recommended_size_fraction, 4),
            edge=round(signal.edge_pct, 4),
            confidence_level=signal.confidence_level,
        )

        return {
            "signal": signal,
            "decision": decision,
            "strategy_params": params,
            "strategy_preset": preset_name or self.default_preset,
            "horizon": horizon,
        }


# Module-level singleton
_analysis_service: Optional[AnalysisService] = None


def get_analysis_service(default_preset: str = "Balanced") -> AnalysisService:
    """Get the AnalysisService instance.

    Args:
        default_preset: Default strategy preset

    Returns:
        AnalysisService instance
    """
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService(default_preset=default_preset)
    return _analysis_service
