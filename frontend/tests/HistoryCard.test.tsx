/** @jest-environment jsdom */
import React from "react";
import { render, screen } from "@testing-library/react";
import HistoryCard from "../components/layout/HistoryCard";

describe("HistoryCard", () => {
  const baseRun = {
    _id: "run-1",
    market_snapshot: { yes_price: 0.4, no_price: 0.6 },
    status: { market: "done", news: "done", signal: "done", report: "done" },
  };

  test("event-style market: renders BOTH event title (small) and market question (bold)", () => {
    const run = {
      ...baseRun,
      event_context: { title: "Who will win the 2028 US presidential election?" },
      market_snapshot: { ...baseRun.market_snapshot, question: "J.D. Vance" },
    };
    render(<HistoryCard run={run} onClick={() => {}} />);

    // Event title rendered (small/muted)
    expect(
      screen.getByText("Who will win the 2028 US presidential election?")
    ).toBeInTheDocument();
    // Market question rendered (bold/primary)
    expect(screen.getByText("J.D. Vance")).toBeInTheDocument();
  });

  test("standalone market (event title === market question): renders ONLY one line", () => {
    const sameText = "US x Iran permanent peace deal by April 30, 2026?";
    const run = {
      ...baseRun,
      event_context: { title: sameText },
      market_snapshot: { ...baseRun.market_snapshot, question: sameText },
    };
    render(<HistoryCard run={run} onClick={() => {}} />);

    // Should appear exactly once, not duplicated
    const matches = screen.getAllByText(sameText);
    expect(matches).toHaveLength(1);
  });

  test("standalone with case/whitespace differences: also dedupes", () => {
    const run = {
      ...baseRun,
      event_context: { title: "  Will it rain tomorrow?  " },
      market_snapshot: { ...baseRun.market_snapshot, question: "Will it rain tomorrow?" },
    };
    render(<HistoryCard run={run} onClick={() => {}} />);
    const matches = screen.getAllByText(/Will it rain tomorrow/i);
    expect(matches).toHaveLength(1);
  });

  test("missing event title: renders single line with market question", () => {
    const run = {
      ...baseRun,
      market_snapshot: { ...baseRun.market_snapshot, question: "Standalone Q?" },
    };
    render(<HistoryCard run={run} onClick={() => {}} />);

    expect(screen.getByText("Standalone Q?")).toBeInTheDocument();
  });

  test("missing market question, has event title: event becomes the primary", () => {
    const run = {
      ...baseRun,
      event_context: { title: "Event-only question?" },
      market_snapshot: baseRun.market_snapshot,
    };
    render(<HistoryCard run={run} onClick={() => {}} />);

    expect(screen.getByText("Event-only question?")).toBeInTheDocument();
  });

  test("both missing: renders fallback 'Unknown Market'", () => {
    const run = { ...baseRun };
    render(<HistoryCard run={run} onClick={() => {}} />);
    expect(screen.getByText("Unknown Market")).toBeInTheDocument();
  });
});
