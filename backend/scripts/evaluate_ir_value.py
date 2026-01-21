"""Evaluate IR/LLM contribution by comparing baseline vs full model performance.

This script computes Brier scores and simulates PnL to measure the value
added by the Tavily+LLM information retrieval pipeline.
"""

from __future__ import annotations

import asyncio
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.database.repositories import runs_collection_async


async def load_runs_with_outcomes() -> list[dict[str, Any]]:
    """Load all runs from MongoDB that have outcome data.

    Returns:
        List of run documents with signal and outcome information
    """
    runs_coll = await runs_collection_async()

    # Query all runs (in production, you'd filter for resolved markets)
    cursor = runs_coll.find({})
    runs = []
    async for run in cursor:
        runs.append(run)

    return runs


def extract_signal_data(run: dict[str, Any]) -> dict[str, Any] | None:
    """Extract signal data from a run document.

    Returns:
        Dict with p_mkt, p_model, and other signal fields, or None if invalid
    """
    signal = run.get("signal", {})
    if not signal:
        return None

    # Handle both new Signal format and legacy format
    p_mkt = signal.get("market_prob")
    p_model = signal.get("model_prob")

    # Fallback to legacy format
    if p_mkt is None:
        market_snapshot = run.get("market_snapshot", {})
        p_mkt = market_snapshot.get("yes_price")

    if p_model is None:
        # Try legacy model_prob_abs
        p_model = signal.get("model_prob_abs")
        if p_model is None:
            # Try model_prob as delta
            delta = signal.get("model_prob", 0.0)
            if isinstance(delta, (int, float)) and abs(delta) < 1.0:
                p_model = (p_mkt or 0.5) + delta

    if p_mkt is None or p_model is None:
        return None

    return {
        "p_mkt": float(p_mkt),
        "p_model": float(p_model),
        "edge_pct": signal.get("edge_pct", float(p_model) - float(p_mkt)),
        "kelly_yes": signal.get("kelly_fraction_yes", 0.0),
        "confidence_level": signal.get("confidence_level", "low"),
        "recommended_action": signal.get("recommended_action", "hold"),
        "recommended_size_fraction": signal.get("recommended_size_fraction", 0.0),
    }


def extract_outcome(run: dict[str, Any]) -> int | None:
    """Extract outcome (0 or 1) from run document.

    For now, returns None as outcome tracking needs to be implemented.
    In production, this would check if the market resolved and what the outcome was.

    Returns:
        0 if NO won, 1 if YES won, None if not resolved or unknown
    """
    # TODO: Implement outcome extraction when market resolution tracking is added
    # This could check:
    # - run.get("outcome") if added to RunDocument
    # - Market resolution status from Polymarket API
    # - Event end_date and resolution data

    return None


def compute_brier_score(predicted: float, actual: int) -> float:
    """Compute Brier score for a single prediction.

    Brier score = (predicted - actual)^2
    Lower is better (0 = perfect, 1 = worst)
    """
    return (predicted - actual) ** 2


def simulate_pnl(runs: list[dict[str, Any]], initial_capital: float = 10000.0) -> dict[str, Any]:
    """Simulate PnL by following recommended actions.

    Args:
        runs: List of run documents with signals
        initial_capital: Starting capital in dollars

    Returns:
        Dict with PnL metrics for different strategies
    """
    capital_flat = initial_capital
    capital_market = initial_capital
    capital_full = initial_capital

    positions_flat: dict[str, dict[str, Any]] = {}  # market_id -> position info
    positions_market: dict[str, dict[str, Any]] = {}
    positions_full: dict[str, dict[str, Any]] = {}

    # Group runs by market_id to simulate sequential decisions
    runs_by_market: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        market_id = str(run.get("market_id", "unknown"))
        runs_by_market[market_id].append(run)

    # Sort runs by run_at timestamp
    for market_id in runs_by_market:
        runs_by_market[market_id].sort(key=lambda r: r.get("run_at", ""))

    # Simulate each strategy
    for market_id, market_runs in runs_by_market.items():
        # Flat strategy: do nothing
        # (positions_flat stays empty)

        # Market strategy: follow market probability naively
        # (simplified: buy YES if p_mkt > 0.5, NO if p_mkt < 0.5)
        for run in market_runs:
            signal_data = extract_signal_data(run)
            if not signal_data:
                continue

            p_mkt = signal_data["p_mkt"]

            # Simple market strategy: bet proportionally to distance from 0.5
            if p_mkt > 0.55:
                size = min(0.1, (p_mkt - 0.5) * 0.2)  # Up to 10% of capital
                positions_market[market_id] = {
                    "side": "yes",
                    "size": size * capital_market,
                    "entry_price": p_mkt,
                }
            elif p_mkt < 0.45:
                size = min(0.1, (0.5 - p_mkt) * 0.2)
                positions_market[market_id] = {
                    "side": "no",
                    "size": size * capital_market,
                    "entry_price": 1.0 - p_mkt,
                }

        # Full strategy: follow signal recommendations
        for run in market_runs:
            signal_data = extract_signal_data(run)
            if not signal_data:
                continue

            action = signal_data["recommended_action"]
            size_fraction = signal_data["recommended_size_fraction"]
            p_mkt = signal_data["p_mkt"]

            if action in ("buy_yes", "buy_no") and size_fraction > 0:
                side = "yes" if action == "buy_yes" else "no"
                size = size_fraction * capital_full
                positions_full[market_id] = {
                    "side": side,
                    "size": size,
                    "entry_price": p_mkt if side == "yes" else (1.0 - p_mkt),
                }
            elif action in ("reduce_yes", "reduce_no"):
                # Reduce position (simplified: close it)
                if market_id in positions_full:
                    del positions_full[market_id]

    # Calculate final PnL (simplified: assume all positions held to resolution)
    # In production, you'd use actual market outcomes
    pnl_flat = 0.0
    pnl_market = 0.0
    pnl_full = 0.0

    # Note: Actual PnL calculation requires outcome data
    # This is a placeholder structure

    return {
        "initial_capital": initial_capital,
        "final_capital_flat": capital_flat + pnl_flat,
        "final_capital_market": capital_market + pnl_market,
        "final_capital_full": capital_full + pnl_full,
        "pnl_flat": pnl_flat,
        "pnl_market": pnl_market,
        "pnl_full": pnl_full,
        "return_flat": (pnl_flat / initial_capital) * 100,
        "return_market": (pnl_market / initial_capital) * 100,
        "return_full": (pnl_full / initial_capital) * 100,
        "positions_flat": len(positions_flat),
        "positions_market": len(positions_market),
        "positions_full": len(positions_full),
    }


async def main() -> None:
    """Main evaluation function."""
    print("Loading runs from MongoDB...")
    runs = await load_runs_with_outcomes()
    print(f"Loaded {len(runs)} runs")

    # Extract signal data and outcomes
    signal_data_list = []
    outcomes = []

    for run in runs:
        signal_data = extract_signal_data(run)
        if signal_data:
            signal_data_list.append((run, signal_data))
            outcome = extract_outcome(run)
            outcomes.append(outcome)

    print(f"Extracted signal data from {len(signal_data_list)} runs")
    print(f"Outcomes available: {sum(1 for o in outcomes if o is not None)}")

    # Compute Brier scores (only for runs with outcomes)
    brier_scores_market = []
    brier_scores_full = []

    for (_run, signal_data), outcome in zip(signal_data_list, outcomes, strict=True):
        if outcome is None:
            continue

        p_mkt = signal_data["p_mkt"]
        p_model = signal_data["p_model"]

        brier_mkt = compute_brier_score(p_mkt, outcome)
        brier_full = compute_brier_score(p_model, outcome)

        brier_scores_market.append(brier_mkt)
        brier_scores_full.append(brier_full)

    # Aggregate metrics
    if brier_scores_market:
        avg_brier_market = sum(brier_scores_market) / len(brier_scores_market)
        avg_brier_full = sum(brier_scores_full) / len(brier_scores_full)
        improvement = ((avg_brier_market - avg_brier_full) / avg_brier_market) * 100
    else:
        avg_brier_market = None
        avg_brier_full = None
        improvement = None
        print("Warning: No outcomes available for Brier score calculation")

    # Simulate PnL
    print("\nSimulating PnL...")
    pnl_results = simulate_pnl(runs)

    # Compile summary report
    report = {
        "summary": {
            "total_runs": len(runs),
            "runs_with_signals": len(signal_data_list),
            "runs_with_outcomes": sum(1 for o in outcomes if o is not None),
        },
        "brier_scores": {
            "market_only": {
                "average": avg_brier_market,
                "count": len(brier_scores_market),
            },
            "full_model": {
                "average": avg_brier_full,
                "count": len(brier_scores_full),
            },
            "improvement_pct": improvement,
        },
        "pnl_simulation": pnl_results,
    }

    # Print summary
    print("\n" + "=" * 60)
    print("IR/LLM Value Evaluation Report")
    print("=" * 60)
    print(f"\nTotal runs analyzed: {report['summary']['total_runs']}")
    print(f"Runs with signals: {report['summary']['runs_with_signals']}")
    print(f"Runs with outcomes: {report['summary']['runs_with_outcomes']}")

    if avg_brier_market is not None:
        print("\nBrier Scores (lower is better):")
        print(f"  Market-only baseline: {avg_brier_market:.4f}")
        print(f"  Full model (IR+LLM):  {avg_brier_full:.4f}")
        if improvement is not None:
            direction = "improved" if improvement > 0 else "worsened"
            print(f"  Improvement: {abs(improvement):.2f}% {direction}")

    print("\nPnL Simulation (placeholder - requires outcome data):")
    print(f"  Flat strategy: ${pnl_results['pnl_flat']:.2f} ({pnl_results['return_flat']:.2f}%)")
    print(
        f"  Market strategy: ${pnl_results['pnl_market']:.2f} ({pnl_results['return_market']:.2f}%)"
    )
    print(
        f"  Full signal strategy: ${pnl_results['pnl_full']:.2f} "
        f"({pnl_results['return_full']:.2f}%)"
    )

    # Save report to JSON
    output_file = Path(__file__).parent / "ir_evaluation_report.json"
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nFull report saved to: {output_file}")

    print("\n" + "=" * 60)
    print("Note: PnL simulation requires outcome data.")
    print("To enable full evaluation, implement outcome tracking in runs.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
