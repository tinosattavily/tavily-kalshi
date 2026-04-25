/** @jest-environment jsdom */
import React from "react";
import { render, screen } from "@testing-library/react";
import ReportCard from "../components/analysis/ReportCard";
import type { Signal } from "../types/signal";

describe("ReportCard Component", () => {
  const mockEventContext = {
    title: "Test Event",
    url: "https://example.com/event",
  };

  const mockSignal: Signal = {
    market_prob: 0.45,
    model_prob: 0.62,
    edge_pct: 17,
    recommended_action: "BUY_YES",
    confidence_level: "high",
  };

  test("renders structured report with headline", () => {
    const report = {
      headline: "Test Headline",
      thesis: "Test thesis",
    };
    render(<ReportCard report={report} eventContext={mockEventContext} />);
    expect(screen.getByText("Test Headline")).toBeInTheDocument();
    expect(screen.getByText("Test thesis")).toBeInTheDocument();
  });

  test("renders structured report with bull_case and bear_case", () => {
    const report = {
      headline: "Test Headline",
      thesis: "Test thesis",
      bull_case: ["Bull point 1", "Bull point 2"],
      bear_case: ["Bear point 1", "Bear point 2"],
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText("BULL CASE")).toBeInTheDocument();
    expect(screen.getByText("BEAR CASE")).toBeInTheDocument();
    expect(screen.getByText("Bull point 1")).toBeInTheDocument();
    expect(screen.getByText("Bull point 2")).toBeInTheDocument();
    expect(screen.getByText("Bear point 1")).toBeInTheDocument();
    expect(screen.getByText("Bear point 2")).toBeInTheDocument();
  });

  test("renders structured report with key_risks", () => {
    const report = {
      headline: "Test Headline",
      key_risks: ["Risk 1", "Risk 2", "Risk 3"],
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText("KEY RISKS")).toBeInTheDocument();
    expect(screen.getByText("Risk 1")).toBeInTheDocument();
    expect(screen.getByText("Risk 2")).toBeInTheDocument();
    expect(screen.getByText("Risk 3")).toBeInTheDocument();
  });

  test("renders structured report with execution_notes", () => {
    const report = {
      headline: "Test Headline",
      execution_notes: ["Execution note one", "Execution note two"],
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText("EXECUTION NOTES")).toBeInTheDocument();
    expect(screen.getByText("Execution note one")).toBeInTheDocument();
    expect(screen.getByText("Execution note two")).toBeInTheDocument();
  });

  test("renders complete structured report", () => {
    const report = {
      headline: "Complete Report",
      thesis: "Main thesis statement",
      bull_case: ["Bull 1", "Bull 2"],
      bear_case: ["Bear 1"],
      key_risks: ["Risk 1"],
      execution_notes: ["Notes"],
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText("Complete Report")).toBeInTheDocument();
    expect(screen.getByText("Main thesis statement")).toBeInTheDocument();
    expect(screen.getByText("Bull 1")).toBeInTheDocument();
    expect(screen.getByText("Bear 1")).toBeInTheDocument();
    expect(screen.getByText("Risk 1")).toBeInTheDocument();
    expect(screen.getByText("Notes")).toBeInTheDocument();
  });

  test("renders string report in fallback panel", () => {
    const report = "Simple string report";
    render(<ReportCard report={report} />);
    expect(screen.getByText("Simple string report")).toBeInTheDocument();
  });

  test("renders fallback message for non-structured object", () => {
    // Arrays are not considered structured by the new component
    const report = ["unexpected", "array"] as unknown as Parameters<typeof ReportCard>[0]["report"];
    render(<ReportCard report={report} />);
    expect(screen.getByText("No structured report available.")).toBeInTheDocument();
  });

  test("renders EdgeBar when signal is provided", () => {
    const report = {
      headline: "With Signal",
    };
    render(<ReportCard report={report} signal={mockSignal} />);
    // EdgeBar emits the MARKET / MODEL labels with percentages
    expect(screen.getByText(/MARKET\s+45%/)).toBeInTheDocument();
    expect(screen.getByText(/MODEL\s+62%/)).toBeInTheDocument();
  });

  test("does not render EdgeBar when signal is null", () => {
    const report = {
      headline: "No Signal",
    };
    render(<ReportCard report={report} signal={null} />);
    expect(screen.queryByText(/MARKET\s+\d+%/)).not.toBeInTheDocument();
    expect(screen.queryByText(/MODEL\s+\d+%/)).not.toBeInTheDocument();
  });

  test("does not render EdgeBar when signal is undefined", () => {
    const report = {
      headline: "No Signal",
    };
    render(<ReportCard report={report} />);
    expect(screen.queryByText(/MARKET\s+\d+%/)).not.toBeInTheDocument();
  });

  test("renders signal hero with MODEL OUTPUT label", () => {
    const report = {
      headline: "Hero Headline",
    };
    render(<ReportCard report={report} signal={mockSignal} />);
    expect(screen.getByText("MODEL OUTPUT")).toBeInTheDocument();
    expect(screen.getByText("Hero Headline")).toBeInTheDocument();
  });

  test("renders fallback hero text when headline is missing but signal provided", () => {
    const report = {
      thesis: "Just thesis",
    };
    render(<ReportCard report={report} signal={mockSignal} />);
    expect(screen.getByText("Awaiting model output.")).toBeInTheDocument();
  });

  test("does not render headline content when missing", () => {
    const report = {
      thesis: "Test thesis",
    };
    render(<ReportCard report={report} />);
    expect(screen.queryByText(/Test Headline/)).not.toBeInTheDocument();
    expect(screen.getByText("Test thesis")).toBeInTheDocument();
  });

  test("does not render thesis section when missing", () => {
    const report = {
      headline: "Test Headline",
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText("Test Headline")).toBeInTheDocument();
    expect(screen.queryByText("THESIS")).not.toBeInTheDocument();
  });

  test("does not render bull_case when empty array", () => {
    const report = {
      headline: "Test Headline",
      bull_case: [],
    };
    render(<ReportCard report={report} />);
    expect(screen.queryByText("BULL CASE")).not.toBeInTheDocument();
  });

  test("does not render bear_case when empty array", () => {
    const report = {
      headline: "Test Headline",
      bear_case: [],
    };
    render(<ReportCard report={report} />);
    expect(screen.queryByText("BEAR CASE")).not.toBeInTheDocument();
  });

  test("does not render key_risks when empty array", () => {
    const report = {
      headline: "Test Headline",
      key_risks: [],
    };
    render(<ReportCard report={report} />);
    expect(screen.queryByText("KEY RISKS")).not.toBeInTheDocument();
  });

  test("does not render execution_notes when missing", () => {
    const report = {
      headline: "Test Headline",
    };
    render(<ReportCard report={report} />);
    expect(screen.queryByText("EXECUTION NOTES")).not.toBeInTheDocument();
  });

  test("does not render execution_notes when empty array", () => {
    const report = {
      headline: "Test Headline",
      execution_notes: [],
    };
    render(<ReportCard report={report} />);
    expect(screen.queryByText("EXECUTION NOTES")).not.toBeInTheDocument();
  });

  test("renders only bull_case when bear_case is missing", () => {
    const report = {
      headline: "Test Headline",
      bull_case: ["Bull 1"],
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText("BULL CASE")).toBeInTheDocument();
    expect(screen.queryByText("BEAR CASE")).not.toBeInTheDocument();
  });

  test("renders only bear_case when bull_case is missing", () => {
    const report = {
      headline: "Test Headline",
      bear_case: ["Bear 1"],
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText("BEAR CASE")).toBeInTheDocument();
    expect(screen.queryByText("BULL CASE")).not.toBeInTheDocument();
  });

  test("identifies structured report by headline", () => {
    const report = {
      headline: "Test",
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText("Test")).toBeInTheDocument();
  });

  test("identifies structured report by thesis", () => {
    const report = {
      thesis: "Test thesis",
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText("Test thesis")).toBeInTheDocument();
  });

  test("identifies structured report by bull_case", () => {
    const report = {
      bull_case: ["Bull 1"],
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText("BULL CASE")).toBeInTheDocument();
  });

  test("handles null event context", () => {
    const report = {
      headline: "Test Headline",
    };
    render(<ReportCard report={report} eventContext={null} />);
    expect(screen.getByText("Test Headline")).toBeInTheDocument();
  });

  test("handles undefined event context", () => {
    const report = {
      headline: "Test Headline",
    };
    render(<ReportCard report={report} eventContext={undefined} />);
    expect(screen.getByText("Test Headline")).toBeInTheDocument();
  });

  test("renders multiple bull case points", () => {
    const report = {
      headline: "Test",
      bull_case: ["Point 1", "Point 2", "Point 3", "Point 4"],
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText("Point 1")).toBeInTheDocument();
    expect(screen.getByText("Point 2")).toBeInTheDocument();
    expect(screen.getByText("Point 3")).toBeInTheDocument();
    expect(screen.getByText("Point 4")).toBeInTheDocument();
  });

  test("renders multiple bear case points", () => {
    const report = {
      headline: "Test",
      bear_case: ["BearPoint 1", "BearPoint 2", "BearPoint 3"],
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText("BearPoint 1")).toBeInTheDocument();
    expect(screen.getByText("BearPoint 2")).toBeInTheDocument();
    expect(screen.getByText("BearPoint 3")).toBeInTheDocument();
  });

  test("renders multiple key risks", () => {
    const report = {
      headline: "Test",
      key_risks: ["Risk 1", "Risk 2", "Risk 3", "Risk 4", "Risk 5"],
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText("Risk 1")).toBeInTheDocument();
    expect(screen.getByText("Risk 5")).toBeInTheDocument();
  });

  test("handles empty string report in fallback panel", () => {
    const report = "";
    const { container } = render(<ReportCard report={report} />);
    // Component renders the fallback panel; intent: empty-string content path runs without throwing
    expect(container.firstChild).toBeInTheDocument();
  });

  test("renders structured report sections in correct order", () => {
    const report = {
      headline: "TestHeadline",
      thesis: "TestThesis",
      bull_case: ["TestBull"],
      bear_case: ["TestBear"],
      key_risks: ["TestRisk"],
      execution_notes: ["TestNotes"],
    };
    const { container } = render(<ReportCard report={report} />);
    const textContent = container.textContent || "";
    const headlineIndex = textContent.indexOf("TestHeadline");
    const thesisIndex = textContent.indexOf("TestThesis");
    const bullIndex = textContent.indexOf("TestBull");
    const bearIndex = textContent.indexOf("TestBear");
    const riskIndex = textContent.indexOf("TestRisk");
    const notesIndex = textContent.indexOf("TestNotes");

    expect(headlineIndex).toBeGreaterThan(-1);
    expect(thesisIndex).toBeGreaterThan(-1);
    expect(bullIndex).toBeGreaterThan(-1);
    expect(bearIndex).toBeGreaterThan(-1);
    expect(riskIndex).toBeGreaterThan(-1);
    expect(notesIndex).toBeGreaterThan(-1);

    expect(headlineIndex).toBeLessThan(thesisIndex);
    expect(thesisIndex).toBeLessThan(bullIndex);
    expect(bullIndex).toBeLessThan(bearIndex);
    expect(bearIndex).toBeLessThan(riskIndex);
    expect(riskIndex).toBeLessThan(notesIndex);
  });

  test("identifies structured report by execution_notes only", () => {
    const report = {
      execution_notes: ["Execution notes only"],
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText("Execution notes only")).toBeInTheDocument();
    expect(screen.getByText("EXECUTION NOTES")).toBeInTheDocument();
  });
});
