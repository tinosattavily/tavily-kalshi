/** @jest-environment jsdom */
import React from "react";
import { render, screen } from "@testing-library/react";
import SignalCard from "../components/analysis/SignalCard";

describe("SignalCard Component", () => {
  test("returns null for empty signal", () => {
    const { container } = render(<SignalCard signal={{}} />);
    expect(container.firstChild).toBeNull();
  });

  test("returns null for null signal", () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const { container } = render(<SignalCard signal={null as any} />);
    expect(container.firstChild).toBeNull();
  });

  test("renders with minimal signal data", () => {
    const signal = {
      market_prob: 0.5,
      model_prob: 0.6,
    };
    render(<SignalCard signal={signal} />);
    expect(screen.getByText("Signal")).toBeInTheDocument();
    expect(screen.getByText("50.00%")).toBeInTheDocument(); // Market Prob
    expect(screen.getByText("60.00%")).toBeInTheDocument(); // Model Prob
  });

  test("renders with full signal data", () => {
    const signal = {
      market_prob: 0.5,
      model_prob: 0.6,
      edge_pct: 0.1,
      kelly_fraction_yes: 0.2,
      confidence_level: "HIGH",
      confidence_score: 0.85,
      recommended_action: "buy_yes",
      recommended_size_fraction: 0.15,
      target_take_profit_prob: 0.7,
      target_stop_loss_prob: 0.4,
      rationale_short: "Strong bullish signal",
    };
    render(<SignalCard signal={signal} />);
    expect(screen.getByText("Signal")).toBeInTheDocument();
    expect(screen.getByText("BUY YES")).toBeInTheDocument();
    expect(screen.getByText("10.00%")).toBeInTheDocument(); // Edge
    expect(screen.getByText("20.00%")).toBeInTheDocument(); // Kelly Yes
    expect(screen.getByText("15.00%")).toBeInTheDocument(); // Position Size
    expect(screen.getByText(/Confidence: HIGH/)).toBeInTheDocument();
    expect(screen.getByText(/Take Profit:/)).toBeInTheDocument();
    expect(screen.getByText(/Stop Loss:/)).toBeInTheDocument();
    expect(screen.getByText("Strong bullish signal")).toBeInTheDocument();
  });

  test("uses legacy fields when new fields are missing", () => {
    const signal = {
      model_prob_abs: 0.65,
      confidence: "MEDIUM",
      rationale: "Legacy rationale",
    };
    render(<SignalCard signal={signal} />);
    // "65.00%" appears multiple times (Market Prob and Model Prob), so use getAllByText
    const percentageElements = screen.getAllByText("65.00%");
    expect(percentageElements.length).toBeGreaterThan(0);
    expect(screen.getByText(/Confidence: MEDIUM/)).toBeInTheDocument();
    expect(screen.getByText("Legacy rationale")).toBeInTheDocument();
  });

  test("calculates edge from market_prob and model_prob when edge_pct is missing", () => {
    const signal = {
      market_prob: 0.4,
      model_prob: 0.6,
    };
    render(<SignalCard signal={signal} />);
    expect(screen.getByText("20.00%")).toBeInTheDocument(); // Edge = 0.6 - 0.4 = 0.2
  });

  test("handles null and undefined values in formatPct", () => {
    const signal = {
      market_prob: undefined,
      model_prob: undefined,
      edge_pct: NaN,
      kelly_fraction_yes: 0.2,
    };
    render(<SignalCard signal={signal} />);
    expect(screen.getByText("–")).toBeInTheDocument(); // Should appear multiple times for null/undefined/NaN
  });

  test("displays correct action labels", () => {
    const actions = ["buy_yes", "buy_no", "reduce_yes", "reduce_no", "hold"];
    actions.forEach((action) => {
      const { unmount } = render(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        <SignalCard signal={{ recommended_action: action } as any} />
      );
      expect(screen.getByText(action.toUpperCase().replace("_", " "))).toBeInTheDocument();
      unmount();
    });
  });

  test("handles unknown action by defaulting to HOLD", () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    render(<SignalCard signal={{ recommended_action: "unknown_action" } as any} />);
    expect(screen.getByText("HOLD")).toBeInTheDocument();
  });

  test("normalizes confidence level case", () => {
    const { unmount } = render(
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      <SignalCard signal={{ confidence_level: "high" } as any} />
    );
    expect(screen.getByText(/Confidence: HIGH/)).toBeInTheDocument();
    unmount();

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    render(<SignalCard signal={{ confidence_level: "MEDIUM" } as any} />);
    expect(screen.getByText(/Confidence: MEDIUM/)).toBeInTheDocument();
    unmount();

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    render(<SignalCard signal={{ confidence_level: "low" } as any} />);
    expect(screen.getByText(/Confidence: LOW/)).toBeInTheDocument();
  });

  test("defaults to LOW confidence when invalid", () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    render(<SignalCard signal={{ confidence_level: "invalid" } as any} />);
    expect(screen.getByText(/Confidence: LOW/)).toBeInTheDocument();
  });

  test("displays positive edge in green", () => {
    const signal = {
      edge_pct: 0.1,
    };
    render(<SignalCard signal={signal} />);
    const edgeElement = screen.getByText("10.00%");
    expect(edgeElement).toHaveClass("text-emerald-700");
  });

  test("displays negative edge in red", () => {
    const signal = {
      edge_pct: -0.1,
    };
    render(<SignalCard signal={signal} />);
    const edgeElement = screen.getByText("-10.00%");
    expect(edgeElement).toHaveClass("text-rose-700");
  });

  test("displays position size when recommended_size_fraction > 0", () => {
    const signal = {
      recommended_size_fraction: 0.25,
      recommended_action: "buy_yes",
    };
    render(<SignalCard signal={signal} />);
    expect(screen.getByText("25.00%")).toBeInTheDocument(); // Position Size
  });

  test("does not display position size when recommended_size_fraction is 0", () => {
    const signal = {
      recommended_size_fraction: 0,
      recommended_action: "buy_yes",
    };
    render(<SignalCard signal={signal} />);
    // Position size section should not be rendered
    expect(screen.queryByText(/Position Size/)).not.toBeInTheDocument();
  });

  test("does not display position size when recommended_size_fraction is undefined", () => {
    const signal = {
      recommended_action: "buy_yes",
    };
    render(<SignalCard signal={signal} />);
    expect(screen.queryByText(/Position Size/)).not.toBeInTheDocument();
  });

  test("displays take profit and stop loss when available", () => {
    const signal = {
      target_take_profit_prob: 0.8,
      target_stop_loss_prob: 0.3,
    };
    render(<SignalCard signal={signal} />);
    // Text is split across spans and may appear in tooltips, so use getAllByText
    const takeProfitElements = screen.getAllByText((content, element) => {
      return element?.textContent?.includes("Take Profit:") && element?.textContent?.includes("80.00%") || false;
    });
    expect(takeProfitElements.length).toBeGreaterThan(0);
    expect(takeProfitElements[0]).toBeInTheDocument();
    const stopLossElements = screen.getAllByText((content, element) => {
      return element?.textContent?.includes("Stop Loss:") && element?.textContent?.includes("30.00%") || false;
    });
    expect(stopLossElements.length).toBeGreaterThan(0);
    expect(stopLossElements[0]).toBeInTheDocument();
  });

  test("displays only take profit when stop loss is missing", () => {
    const signal = {
      target_take_profit_prob: 0.8,
    };
    render(<SignalCard signal={signal} />);
    // Text may appear in tooltips, so use getAllByText
    const takeProfitElements = screen.getAllByText((content, element) => {
      return element?.textContent?.includes("Take Profit:") && element?.textContent?.includes("80.00%") || false;
    });
    expect(takeProfitElements.length).toBeGreaterThan(0);
    expect(takeProfitElements[0]).toBeInTheDocument();
    expect(screen.queryByText(/Stop Loss:/)).not.toBeInTheDocument();
  });

  test("displays only stop loss when take profit is missing", () => {
    const signal = {
      target_stop_loss_prob: 0.3,
    };
    render(<SignalCard signal={signal} />);
    // Text appears multiple times (in component and tooltips), so use getAllByText
    const stopLossElements = screen.getAllByText((content, element) => {
      return element?.textContent?.includes("Stop Loss:") && element?.textContent?.includes("30.00%") || false;
    });
    expect(stopLossElements.length).toBeGreaterThan(0);
    expect(stopLossElements[0]).toBeInTheDocument();
    expect(screen.queryByText(/Take Profit:/)).not.toBeInTheDocument();
  });

  test("displays rationale when available", () => {
    const signal = {
      rationale_short: "Short rationale",
    };
    render(<SignalCard signal={signal} />);
    expect(screen.getByText("Short rationale")).toBeInTheDocument();
  });

  test("uses rationale_long when rationale_short is missing", () => {
    const signal = {
      rationale_long: "Long rationale",
    };
    render(<SignalCard signal={signal} />);
    expect(screen.getByText("Long rationale")).toBeInTheDocument();
  });

  test("uses legacy rationale when new rationale fields are missing", () => {
    const signal = {
      rationale: "Legacy rationale",
    };
    render(<SignalCard signal={signal} />);
    expect(screen.getByText("Legacy rationale")).toBeInTheDocument();
  });

  test("applies correct color scheme for buy_yes", () => {
    const signal = {
      recommended_action: "buy_yes",
    };
    const { container } = render(<SignalCard signal={signal} />);
    const section = container.querySelector("section");
    expect(section).toHaveClass("bg-emerald-50/40");
    expect(section).toHaveClass("border-emerald-100/50");
  });

  test("applies correct color scheme for buy_no", () => {
    const signal = {
      recommended_action: "buy_no",
    };
    const { container } = render(<SignalCard signal={signal} />);
    const section = container.querySelector("section");
    expect(section).toHaveClass("bg-rose-50/40");
    expect(section).toHaveClass("border-rose-100/50");
  });

  test("applies correct color scheme for reduce_yes", () => {
    const signal = {
      recommended_action: "reduce_yes",
    };
    const { container } = render(<SignalCard signal={signal} />);
    const section = container.querySelector("section");
    expect(section).toHaveClass("bg-rose-50/40");
  });

  test("applies correct color scheme for reduce_no", () => {
    const signal = {
      recommended_action: "reduce_no",
    };
    const { container } = render(<SignalCard signal={signal} />);
    const section = container.querySelector("section");
    expect(section).toHaveClass("bg-amber-50/40");
  });

  test("applies correct color scheme for hold", () => {
    const signal = {
      recommended_action: "hold",
    };
    const { container } = render(<SignalCard signal={signal} />);
    const section = container.querySelector("section");
    expect(section).toHaveClass("bg-slate-50/40");
  });

  test("displays confidence score as percentage", () => {
    const signal = {
      confidence_score: 0.75,
      confidence_level: "HIGH",
    };
    render(<SignalCard signal={signal} />);
    expect(screen.getByText(/75%/)).toBeInTheDocument();
  });

  test("handles zero confidence score", () => {
    const signal = {
      confidence_score: 0,
      confidence_level: "LOW",
    };
    render(<SignalCard signal={signal} />);
    // "0%" appears multiple times, so use getAllByText
    const zeroPercentElements = screen.getAllByText(/0%/);
    expect(zeroPercentElements.length).toBeGreaterThan(0);
  });

  test("formats percentages with correct decimal places", () => {
    const signal = {
      market_prob: 0.123456,
      model_prob: 0.987654,
    };
    render(<SignalCard signal={signal} />);
    expect(screen.getByText("12.35%")).toBeInTheDocument(); // Rounded to 2 decimals
    expect(screen.getByText("98.77%")).toBeInTheDocument();
  });

  test("renders tooltips for metrics", () => {
    const signal = {
      market_prob: 0.5,
      model_prob: 0.6,
      edge_pct: 0.1,
      kelly_fraction_yes: 0.2,
    };
    render(<SignalCard signal={signal} />);
    // Tooltips are hidden by default, but should be in the DOM
    const tooltips = screen.getAllByText(/Market Probability|Model Probability|Edge|Kelly Fraction/);
    expect(tooltips.length).toBeGreaterThan(0);
  });

  test("handles expected_value_per_dollar in edge tooltip", () => {
    const signal = {
      edge_pct: 0.1,
      expected_value_per_dollar: 0.15,
    };
    render(<SignalCard signal={signal} />);
    // The tooltip should contain expected value information
    // This is tested indirectly through rendering
    expect(screen.getByText("10.00%")).toBeInTheDocument();
  });
});
