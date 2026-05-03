/** @jest-environment jsdom */
import React from "react";
import { render, screen } from "@testing-library/react";
import SignalPill from "../components/analysis/SignalPill";

describe("SignalPill", () => {
  test("edge_pct fraction (-0.015) renders as 'EDGE -1%' (the bug-fix path; JS rounds -1.5 -> -1)", () => {
    render(<SignalPill signal={{ recommended_action: "hold", edge_pct: -0.015 }} />);
    // Math.round(-0.015 * 100) = Math.round(-1.5) = -1 in JS (rounds toward 0 for negative halves)
    expect(screen.getByText(/-1%/)).toBeInTheDocument();
  });

  test("edge_pct positive fraction (0.05) renders as 'EDGE +5%'", () => {
    render(<SignalPill signal={{ recommended_action: "buy_yes", edge_pct: 0.05 }} />);
    expect(screen.getByText(/\+5%/)).toBeInTheDocument();
  });

  test("edge_pct negative larger fraction (-0.124) renders as 'EDGE -12%'", () => {
    render(<SignalPill signal={{ recommended_action: "hold", edge_pct: -0.124 }} />);
    expect(screen.getByText(/-12%/)).toBeInTheDocument();
  });

  test("edge_pct undefined: falls back to model_prob - market_prob (still works)", () => {
    render(
      <SignalPill
        signal={{
          recommended_action: "hold",
          model_prob: 0.36,
          market_prob: 0.375,
        }}
      />
    );
    // JS floating-point: (0.36 - 0.375) === -0.014999999999999958, * 100 === -1.5000000000000013
    // Math.round(-1.5000000000000013) === -2 (away from zero because magnitude > 1.5)
    expect(screen.getByText(/-2%/)).toBeInTheDocument();
  });

  test("no edge inputs: chip renders just the action without EDGE", () => {
    const { container } = render(
      <SignalPill signal={{ recommended_action: "hold" }} />
    );
    expect(container.textContent).not.toMatch(/EDGE/);
  });
});
