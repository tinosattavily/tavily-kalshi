/** @jest-environment jsdom */
import React from "react";
import { render, screen } from "@testing-library/react";
import DecisionCard from "../components/analysis/DecisionCard";

describe("DecisionCard Component", () => {
  test("returns null when both decision and signal are missing", () => {
    const { container } = render(<DecisionCard />);
    expect(container.firstChild).toBeNull();
  });

  test("returns null when decision is empty object and signal is missing", () => {
    const { container } = render(<DecisionCard decision={{}} />);
    expect(container.firstChild).toBeNull();
  });

  test("returns null when signal is empty object and decision is missing", () => {
    const { container } = render(<DecisionCard signal={{}} />);
    expect(container.firstChild).toBeNull();
  });

  test("returns null when both decision and signal are empty objects", () => {
    const { container } = render(<DecisionCard decision={{}} signal={{}} />);
    expect(container.firstChild).toBeNull();
  });

  test("renders with decision object", () => {
    const decision = {
      action: "buy_yes",
      side: "yes",
      edge_pct: 0.1,
      toy_kelly_fraction: 0.2,
      notes: "Test notes",
    };
    render(<DecisionCard decision={decision} />);
    expect(screen.getByText("Decision")).toBeInTheDocument();
    const edgeElements = screen.getAllByText((content, element) => {
      return element?.textContent?.includes("BUY YES") && element?.textContent?.includes("Edge: 10.00%") || false;
    });
    expect(edgeElements.length).toBeGreaterThan(0);
    expect(edgeElements[0]).toBeInTheDocument();
    expect(screen.getByText((content, element) => {
      return element?.textContent === "Position Size: 20.0% of capital";
    })).toBeInTheDocument();
    expect(screen.getByText((content, element) => {
      return element?.textContent === "Side: yes";
    })).toBeInTheDocument();
    expect(screen.getByText("Test notes")).toBeInTheDocument();
  });

  test("renders with signal object", () => {
    const signal = {
      recommended_action: "buy_no",
      recommended_size_fraction: 0.15,
      edge_pct: 0.05,
      confidence_level: "HIGH",
    };
    render(<DecisionCard signal={signal} />);
    const edgeElements = screen.getAllByText((content, element) => {
      return element?.textContent?.includes("BUY NO") && element?.textContent?.includes("Edge: 5.00%") || false;
    });
    expect(edgeElements.length).toBeGreaterThan(0);
    expect(edgeElements[0]).toBeInTheDocument();
    expect(screen.getByText((content, element) => {
      return element?.textContent === "Position Size: 15.0% of capital";
    })).toBeInTheDocument();
    expect(screen.getByText((content, element) => {
      return element?.textContent === "Confidence: HIGH";
    })).toBeInTheDocument();
  });

  test("prefers signal over decision when both are provided", () => {
    const decision = {
      action: "hold",
      edge_pct: 0.1,
      toy_kelly_fraction: 0.2,
    };
    const signal = {
      recommended_action: "buy_yes",
      recommended_size_fraction: 0.25,
      edge_pct: 0.15,
      confidence_level: "MEDIUM",
    };
    render(<DecisionCard decision={decision} signal={signal} />);
    const edgeElements = screen.getAllByText((content, element) => {
      return element?.textContent?.includes("BUY YES") && element?.textContent?.includes("Edge: 15.00%") || false;
    });
    expect(edgeElements.length).toBeGreaterThan(0);
    expect(edgeElements[0]).toBeInTheDocument();
    expect(screen.getByText((content, element) => {
      return element?.textContent === "Position Size: 25.0% of capital";
    })).toBeInTheDocument();
    expect(screen.getByText((content, element) => {
      return element?.textContent === "Confidence: MEDIUM";
    })).toBeInTheDocument();
    // Should not show decision's action
    expect(screen.queryByText("HOLD")).not.toBeInTheDocument();
  });

  test("falls back to decision when signal fields are missing", () => {
    const decision = {
      action: "reduce_yes",
      edge_pct: 0.1,
      toy_kelly_fraction: 0.2,
      notes: "Decision notes",
    };
    const signal = {
      confidence_level: "LOW",
    };
    render(<DecisionCard decision={decision} signal={signal} />);
    const edgeElements = screen.getAllByText((content, element) => {
      return element?.textContent?.includes("REDUCE YES") && element?.textContent?.includes("Edge: 10.00%") || false;
    });
    expect(edgeElements.length).toBeGreaterThan(0);
    expect(edgeElements[0]).toBeInTheDocument();
    expect(screen.getByText((content, element) => {
      return element?.textContent === "Position Size: 20.0% of capital";
    })).toBeInTheDocument();
    expect(screen.getByText("Decision notes")).toBeInTheDocument();
    expect(screen.getByText((content, element) => {
      return element?.textContent === "Confidence: LOW";
    })).toBeInTheDocument();
  });

  test("defaults to HOLD when action is missing", () => {
    const decision = {
      edge_pct: 0.1,
    };
    render(<DecisionCard decision={decision} />);
    expect(screen.getByText("HOLD")).toBeInTheDocument();
  });

  test("formats action by replacing underscore with space and uppercasing", () => {
    const decision = {
      action: "buy_yes",
    };
    render(<DecisionCard decision={decision} />);
    expect(screen.getByText("BUY YES")).toBeInTheDocument();
  });

  test("formats signal recommended_action correctly", () => {
    const signal = {
      recommended_action: "reduce_no",
    };
    render(<DecisionCard signal={signal} />);
    expect(screen.getByText("REDUCE NO")).toBeInTheDocument();
  });

  test("displays edge percentage with 2 decimal places", () => {
    const decision = {
      action: "buy_yes",
      edge_pct: 0.123456,
    };
    render(<DecisionCard decision={decision} />);
    const edgeElements = screen.getAllByText((content, element) => {
      return element?.textContent?.includes("Edge: 12.35%") || false;
    });
    expect(edgeElements.length).toBeGreaterThan(0);
    expect(edgeElements[0]).toBeInTheDocument();
  });

  test("displays position size with 1 decimal place", () => {
    const decision = {
      action: "buy_yes",
      toy_kelly_fraction: 0.123456,
    };
    render(<DecisionCard decision={decision} />);
    expect(screen.getByText((content, element) => {
      return element?.textContent === "Position Size: 12.3% of capital";
    })).toBeInTheDocument();
  });

  test("does not display position size when 0", () => {
    const decision = {
      action: "buy_yes",
      toy_kelly_fraction: 0,
    };
    render(<DecisionCard decision={decision} />);
    expect(screen.queryByText(/Position Size:/)).not.toBeInTheDocument();
  });

  test("does not display position size when undefined", () => {
    const decision = {
      action: "buy_yes",
    };
    render(<DecisionCard decision={decision} />);
    expect(screen.queryByText(/Position Size:/)).not.toBeInTheDocument();
  });

  test("does not display edge when undefined", () => {
    const decision = {
      action: "buy_yes",
    };
    render(<DecisionCard decision={decision} />);
    expect(screen.queryByText(/Edge:/)).not.toBeInTheDocument();
  });

  test("does not display side when missing", () => {
    const decision = {
      action: "buy_yes",
    };
    render(<DecisionCard decision={decision} />);
    expect(screen.queryByText(/Side:/)).not.toBeInTheDocument();
  });

  test("displays side when available", () => {
    const decision = {
      action: "buy_yes",
      side: "yes",
    };
    render(<DecisionCard decision={decision} />);
    expect(screen.getByText((content, element) => {
      return element?.textContent === "Side: yes";
    })).toBeInTheDocument();
  });

  test("does not display confidence when missing", () => {
    const decision = {
      action: "buy_yes",
    };
    render(<DecisionCard decision={decision} />);
    expect(screen.queryByText(/Confidence:/)).not.toBeInTheDocument();
  });

  test("displays confidence from signal", () => {
    const signal = {
      recommended_action: "buy_yes",
      confidence_level: "HIGH",
    };
    render(<DecisionCard signal={signal} />);
    expect(screen.getByText((content, element) => {
      return element?.textContent === "Confidence: HIGH";
    })).toBeInTheDocument();
  });

  test("uppercases confidence level", () => {
    const signal = {
      recommended_action: "buy_yes",
      confidence_level: "medium",
    };
    render(<DecisionCard signal={signal} />);
    expect(screen.getByText((content, element) => {
      return element?.textContent === "Confidence: MEDIUM";
    })).toBeInTheDocument();
  });

  test("does not display notes when missing", () => {
    const decision = {
      action: "buy_yes",
    };
    render(<DecisionCard decision={decision} />);
    expect(screen.queryByText(/Test notes/)).not.toBeInTheDocument();
  });

  test("displays notes from decision", () => {
    const decision = {
      action: "buy_yes",
      notes: "Important notes here",
    };
    render(<DecisionCard decision={decision} />);
    expect(screen.getByText("Important notes here")).toBeInTheDocument();
  });

  test("uses signal recommended_size_fraction over decision toy_kelly_fraction", () => {
    const decision = {
      action: "buy_yes",
      toy_kelly_fraction: 0.1,
    };
    const signal = {
      recommended_size_fraction: 0.2,
    };
    render(<DecisionCard decision={decision} signal={signal} />);
    expect(screen.getByText((content, element) => {
      return element?.textContent === "Position Size: 20.0% of capital";
    })).toBeInTheDocument();
    expect(screen.queryByText((content, element) => {
      return element?.textContent === "Position Size: 10.0% of capital";
    })).not.toBeInTheDocument();
  });

  test("uses signal edge_pct over decision edge_pct", () => {
    const decision = {
      action: "buy_yes",
      edge_pct: 0.1,
    };
    const signal = {
      edge_pct: 0.2,
    };
    render(<DecisionCard decision={decision} signal={signal} />);
    const edgeElements = screen.getAllByText((content, element) => {
      return element?.textContent?.includes("Edge: 20.00%") || false;
    });
    expect(edgeElements.length).toBeGreaterThan(0);
    expect(edgeElements[0]).toBeInTheDocument();
    expect(screen.queryByText((content, element) => {
      return element?.textContent?.includes("Edge: 10.00%") || false;
    })).not.toBeInTheDocument();
  });

  test("handles negative edge", () => {
    const decision = {
      action: "buy_yes",
      edge_pct: -0.05,
    };
    render(<DecisionCard decision={decision} />);
    const edgeElements = screen.getAllByText((content, element) => {
      return element?.textContent?.includes("Edge: -5.00%") || false;
    });
    expect(edgeElements.length).toBeGreaterThan(0);
    expect(edgeElements[0]).toBeInTheDocument();
  });

  test("handles very small position size", () => {
    const decision = {
      action: "buy_yes",
      toy_kelly_fraction: 0.001,
    };
    render(<DecisionCard decision={decision} />);
    expect(screen.getByText((content, element) => {
      return element?.textContent === "Position Size: 0.1% of capital";
    })).toBeInTheDocument();
  });

  test("handles very large position size", () => {
    const decision = {
      action: "buy_yes",
      toy_kelly_fraction: 0.99,
    };
    render(<DecisionCard decision={decision} />);
    expect(screen.getByText((content, element) => {
      return element?.textContent === "Position Size: 99.0% of capital";
    })).toBeInTheDocument();
  });

  test("renders with minimal decision data", () => {
    const decision = {
      action: "hold",
    };
    render(<DecisionCard decision={decision} />);
    expect(screen.getByText("HOLD")).toBeInTheDocument();
    expect(screen.getByText("Decision")).toBeInTheDocument();
  });

  test("renders with minimal signal data", () => {
    const signal = {
      recommended_action: "hold",
    };
    render(<DecisionCard signal={signal} />);
    expect(screen.getByText("HOLD")).toBeInTheDocument();
  });
});
