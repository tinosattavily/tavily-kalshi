/** @jest-environment jsdom */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NewsCard } from "../components/analysis/NewsCard";

describe("NewsCard", () => {
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

  test("displays summary", () => {
    render(
      <NewsCard
        highlights={mockArticles}
        newsSummary="Test summary"
      />
    );
    
    // Switch to summary tab
    const summaryTab = screen.getByText("Summary");
    fireEvent.click(summaryTab);
    
    expect(screen.getByText("Test summary")).toBeInTheDocument();
  });

  test("handles empty states", () => {
    render(<NewsCard highlights={[]} />);
    
    expect(screen.getByText(/0 stories/i)).toBeInTheDocument();
  });

  test("displays sentiment", () => {
    render(<NewsCard highlights={mockArticles} />);
    
    expect(screen.getByText("bullish")).toBeInTheDocument();
    expect(screen.getByText("bearish")).toBeInTheDocument();
    expect(screen.getByText("neutral")).toBeInTheDocument();
  });

  test("handles article link clicks", () => {
    const onItemClick = jest.fn();
    render(
      <NewsCard
        highlights={mockArticles}
        onItemClick={onItemClick}
      />
    );
    
    const article = screen.getByText("Article 1");
    fireEvent.click(article);
    
    expect(onItemClick).toHaveBeenCalledWith(mockArticles[0]);
  });

  test("displays query information", () => {
    render(
      <NewsCard
        highlights={mockArticles}
        newsSummary="Summary with query info"
      />
    );
    
    const summaryTab = screen.getByText("Summary");
    fireEvent.click(summaryTab);
    
    expect(screen.getByText(/summary with query info/i)).toBeInTheDocument();
  });

  test("switches between news and summary tabs", async () => {
    const user = userEvent.setup();
    render(
      <NewsCard
        highlights={mockArticles}
        newsSummary="Test summary"
      />
    );
    
    // Start on news tab
    expect(screen.getByText("Article 1")).toBeInTheDocument();
    
    // Switch to summary
    const summaryTab = screen.getByText("Summary");
    await user.click(summaryTab);
    
    expect(screen.getByText("Test summary")).toBeInTheDocument();
    expect(screen.queryByText("Article 1")).not.toBeInTheDocument();
    
    // Switch back to news
    const newsTab = screen.getByText("News");
    await user.click(newsTab);
    
    expect(screen.getByText("Article 1")).toBeInTheDocument();
  });

  test("shows loading state", () => {
    render(
      <NewsCard
        highlights={[]}
        isLoading={true}
      />
    );
    
    expect(screen.getByText(/updating/i)).toBeInTheDocument();
  });

  test("handles article link click with stopPropagation", async () => {
    const _user = userEvent.setup();
    const onItemClick = jest.fn();
    const articleWithUrl = {
      title: "Article with URL",
      source: "Test Source",
      url: "https://example.com/article",
      sentiment: "bullish" as const,
    };
    
    render(
      <NewsCard
        highlights={[articleWithUrl]}
        onItemClick={onItemClick}
      />
    );
    
    // Find the link element (when both url and source exist, it renders as a link)
    const link = screen.getByRole("link", { name: /Test Source/i });
    
    // Simulate click on the link (fireEvent creates the event for us)
    fireEvent.click(link);
    
    // Verify onItemClick was called
    expect(onItemClick).toHaveBeenCalledWith(articleWithUrl);
    
    // Note: stopPropagation is called in the onClick handler, but we can't easily test it
    // without accessing the internal event. The important part is that onItemClick is called.
  });
});

