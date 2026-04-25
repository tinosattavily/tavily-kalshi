/** @jest-environment jsdom */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { NewsCard } from "../components/analysis/NewsCard";

describe("NewsCard (legacy shim wrapping NewsTab + SummaryTab)", () => {
  const mockArticles = [
    {
      title: "Article 1",
      source: "Source 1",
      url: "https://example.com/1",
      publishedAt: "2025-11-15T10:00:00Z",
      sentiment: "bullish" as const,
    },
    {
      title: "Article 2",
      source: "Source 2",
      url: "https://example.com/2",
      publishedAt: "2025-11-15T11:00:00Z",
      sentiment: "bearish" as const,
    },
    {
      title: "Article 3",
      source: "Source 3",
      sentiment: "neutral" as const,
    },
  ];

  test("renders article list", () => {
    render(<NewsCard highlights={mockArticles} />);

    expect(screen.getByText("Article 1")).toBeInTheDocument();
    expect(screen.getByText("Article 2")).toBeInTheDocument();
    expect(screen.getByText("Article 3")).toBeInTheDocument();
  });

  test("displays summary text alongside news (no internal tab strip)", () => {
    render(<NewsCard highlights={mockArticles} newsSummary="Test summary" />);

    // The shim renders NewsTab + SummaryTab in sequence — no tab switch needed.
    expect(screen.getByText("Test summary")).toBeInTheDocument();
    expect(screen.getByText("Article 1")).toBeInTheDocument();
  });

  test("handles empty states", () => {
    render(<NewsCard highlights={[]} />);

    expect(screen.getByText(/no articles in this run/i)).toBeInTheDocument();
    expect(screen.getByText(/no summary available/i)).toBeInTheDocument();
  });

  test("displays sentiment chips for each article", () => {
    render(<NewsCard highlights={mockArticles} />);

    // Sentiment chips render the kind as text — but "bullish"/"bearish"/"neutral"
    // also appear in the SummaryTab breakdown rows ("Bullish"/"Bearish"/"Neutral").
    // We assert the chip variant (lowercase) appears at least once for each kind.
    expect(screen.getByText("bullish")).toBeInTheDocument();
    expect(screen.getByText("bearish")).toBeInTheDocument();
    expect(screen.getByText("neutral")).toBeInTheDocument();
  });

  test("handles article click", () => {
    const onItemClick = jest.fn();
    render(<NewsCard highlights={mockArticles} onItemClick={onItemClick} />);

    const article = screen.getByText("Article 1");
    fireEvent.click(article);

    expect(onItemClick).toHaveBeenCalledWith(mockArticles[0]);
  });

  test("displays summary with provided text", () => {
    render(<NewsCard highlights={mockArticles} newsSummary="Summary with query info" />);

    expect(screen.getByText(/summary with query info/i)).toBeInTheDocument();
  });

  test("renders both news and summary content simultaneously", () => {
    render(<NewsCard highlights={mockArticles} newsSummary="Test summary" />);

    // News content
    expect(screen.getByText("Article 1")).toBeInTheDocument();
    // Summary content
    expect(screen.getByText("Test summary")).toBeInTheDocument();
  });

  test("shows loading placeholder when loading and no articles", () => {
    const { container } = render(<NewsCard highlights={[]} isLoading={true} />);

    // The loading branch in NewsTab renders a pulsing skeleton block.
    expect(container.querySelector(".animate-pulse")).not.toBeNull();
  });

  test("source link click still fires onItemClick", () => {
    const onItemClick = jest.fn();
    const articleWithUrl = {
      title: "Article with URL",
      source: "Test Source",
      url: "https://example.com/article",
      sentiment: "bullish" as const,
    };

    render(<NewsCard highlights={[articleWithUrl]} onItemClick={onItemClick} />);

    const link = screen.getByRole("link", { name: /Test Source/i });
    fireEvent.click(link);

    expect(onItemClick).toHaveBeenCalledWith(articleWithUrl);
  });

  test("falls back to combinedSummary when newsSummary is absent", () => {
    render(<NewsCard highlights={mockArticles} combinedSummary="Combined summary text" />);

    expect(screen.getByText("Combined summary text")).toBeInTheDocument();
  });
});
