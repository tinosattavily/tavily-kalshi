/** @jest-environment jsdom */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import ReportCard from "../components/analysis/ReportCard";

describe("ReportCard Component", () => {
  const mockEventContext = {
    title: "Test Event",
    image: "https://example.com/event.jpg",
  };

  test("renders structured report with headline", () => {
    const report = {
      headline: "Test Headline",
      thesis: "Test thesis",
    };
    render(<ReportCard report={report} eventContext={mockEventContext} />);
    expect(screen.getByText("Report & Thesis")).toBeInTheDocument();
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
    expect(screen.getByText("Bull Case")).toBeInTheDocument();
    expect(screen.getByText("Bear Case")).toBeInTheDocument();
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
    expect(screen.getByText("Key Risks")).toBeInTheDocument();
    expect(screen.getByText("Risk 1")).toBeInTheDocument();
    expect(screen.getByText("Risk 2")).toBeInTheDocument();
    expect(screen.getByText("Risk 3")).toBeInTheDocument();
  });

  test("renders structured report with execution_notes", () => {
    const report = {
      headline: "Test Headline",
      execution_notes: "Execution notes here",
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText("Execution Notes")).toBeInTheDocument();
    expect(screen.getByText("Execution notes here")).toBeInTheDocument();
  });

  test("renders complete structured report", () => {
    const report = {
      headline: "Complete Report",
      thesis: "Main thesis statement",
      bull_case: ["Bull 1", "Bull 2"],
      bear_case: ["Bear 1"],
      key_risks: ["Risk 1"],
      execution_notes: "Notes",
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText("Complete Report")).toBeInTheDocument();
    expect(screen.getByText("Main thesis statement")).toBeInTheDocument();
    expect(screen.getByText("Bull 1")).toBeInTheDocument();
    expect(screen.getByText("Bear 1")).toBeInTheDocument();
    expect(screen.getByText("Risk 1")).toBeInTheDocument();
    expect(screen.getByText("Notes")).toBeInTheDocument();
  });

  test("renders legacy markdown report", () => {
    const report = {
      markdown: "# Legacy Report\n\nThis is markdown content.",
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText(/# Legacy Report/)).toBeInTheDocument();
    expect(screen.getByText(/This is markdown content\./)).toBeInTheDocument();
  });

  test("renders string report", () => {
    const report = "Simple string report";
    render(<ReportCard report={report} />);
    expect(screen.getByText("Simple string report")).toBeInTheDocument();
  });

  test("renders JSON fallback for unknown object structure", () => {
    const report = {
      unknownField: "value",
      anotherField: 123,
    };
    render(<ReportCard report={report} />);
    const jsonContent = JSON.stringify(report, null, 2);
    expect(screen.getByText(new RegExp(jsonContent.split("\n")[0]))).toBeInTheDocument();
  });

  test("renders event context image when available", () => {
    const report = {
      headline: "Test Headline",
    };
    render(<ReportCard report={report} eventContext={mockEventContext} />);
    const image = screen.getByAltText("Test Event");
    expect(image).toBeInTheDocument();
    expect(image).toHaveAttribute("src", "https://example.com/event.jpg");
  });

  test("does not render event context image when missing", () => {
    const report = {
      headline: "Test Headline",
    };
    render(<ReportCard report={report} eventContext={{ title: "Test" }} />);
    expect(screen.queryByAltText("Event image")).not.toBeInTheDocument();
  });

  test("handles event image load error", () => {
    const report = {
      headline: "Test Headline",
    };
    render(<ReportCard report={report} eventContext={mockEventContext} />);
    const image = screen.getByAltText("Test Event");
    fireEvent.error(image);
    expect(image).toHaveStyle({ display: "none" });
  });

  test("does not render headline section when missing", () => {
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
    // Check for Thesis section heading (h4), not the word "Thesis" in "Report & Thesis" header
    // The "Report & Thesis" header is in a p tag, so we check for h4 heading specifically
    const thesisHeading = screen.queryByRole("heading", { name: "Thesis", level: 4 });
    expect(thesisHeading).not.toBeInTheDocument();
  });

  test("does not render bull_case when empty array", () => {
    const report = {
      headline: "Test Headline",
      bull_case: [],
    };
    render(<ReportCard report={report} />);
    expect(screen.queryByText("Bull Case")).not.toBeInTheDocument();
  });

  test("does not render bear_case when empty array", () => {
    const report = {
      headline: "Test Headline",
      bear_case: [],
    };
    render(<ReportCard report={report} />);
    expect(screen.queryByText("Bear Case")).not.toBeInTheDocument();
  });

  test("does not render key_risks when empty array", () => {
    const report = {
      headline: "Test Headline",
      key_risks: [],
    };
    render(<ReportCard report={report} />);
    expect(screen.queryByText("Key Risks")).not.toBeInTheDocument();
  });

  test("does not render execution_notes when missing", () => {
    const report = {
      headline: "Test Headline",
    };
    render(<ReportCard report={report} />);
    expect(screen.queryByText("Execution Notes")).not.toBeInTheDocument();
  });

  test("renders only bull_case when bear_case is missing", () => {
    const report = {
      headline: "Test Headline",
      bull_case: ["Bull 1"],
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText("Bull Case")).toBeInTheDocument();
    expect(screen.queryByText("Bear Case")).not.toBeInTheDocument();
  });

  test("renders only bear_case when bull_case is missing", () => {
    const report = {
      headline: "Test Headline",
      bear_case: ["Bear 1"],
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText("Bear Case")).toBeInTheDocument();
    expect(screen.queryByText("Bull Case")).not.toBeInTheDocument();
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
    expect(screen.getByText("Bull Case")).toBeInTheDocument();
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
      bear_case: ["Point 1", "Point 2", "Point 3"],
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText("Point 1")).toBeInTheDocument();
    expect(screen.getByText("Point 2")).toBeInTheDocument();
    expect(screen.getByText("Point 3")).toBeInTheDocument();
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

  test("handles report with only title (legacy field)", () => {
    const report = {
      title: "Legacy Title",
      markdown: "Legacy content",
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText("Legacy content")).toBeInTheDocument();
  });

  test("handles empty string report", () => {
    const report = "";
    render(<ReportCard report={report} />);
    // Empty string will match multiple elements, so we check that the component renders
    expect(screen.getByText("Report & Thesis")).toBeInTheDocument();
    // Check that the empty string is rendered in the content area
    const contentDiv = screen.getByText("Report & Thesis").closest("section")?.querySelector(".whitespace-pre-wrap");
    expect(contentDiv).toBeInTheDocument();
  });

  test("handles report with special characters in markdown", () => {
    const report = {
      markdown: "# Title\n\n*Bold* and _italic_ text\n\n- List item",
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText(/# Title/)).toBeInTheDocument();
  });

  test("handles report with newlines in string", () => {
    const report = "Line 1\nLine 2\nLine 3";
    render(<ReportCard report={report} />);
    expect(screen.getByText(/Line 1/)).toBeInTheDocument();
  });

  test("renders structured report sections in correct order", () => {
    const report = {
      headline: "TestHeadline",
      thesis: "TestThesis",
      bull_case: ["TestBull"],
      bear_case: ["TestBear"],
      key_risks: ["TestRisk"],
      execution_notes: "TestNotes",
    };
    const { container } = render(<ReportCard report={report} />);
    const textContent = container.textContent || "";
    // Use unique text to avoid matching "Test" in "Report & Thesis"
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
      execution_notes: "Execution notes only",
    };
    render(<ReportCard report={report} />);
    expect(screen.getByText("Execution notes only")).toBeInTheDocument();
    expect(screen.getByText("Execution Notes")).toBeInTheDocument();
  });

  test("handles event image load error", () => {
    const report = {
      headline: "Test Headline",
    };
    render(<ReportCard report={report} eventContext={mockEventContext} />);
    const image = screen.getByAltText("Test Event");
    fireEvent.error(image);
    expect(image).toHaveStyle({ display: "none" });
  });
});
