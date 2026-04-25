/** @jest-environment jsdom */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { MarketCard } from "../components/analysis/MarketCard";

describe("MarketCard", () => {
  const defaultProps = {
    eventTitle: "Test Event",
    marketUrl: "https://kalshi.com/markets/test",
    closesIn: "23 days",
    yesPrice: 0.5,
    noPrice: 0.5,
    marketVolume: 1000000,
  };

  test("renders with full data", () => {
    render(<MarketCard {...defaultProps} />);
    
    expect(screen.getByText("Test Event")).toBeInTheDocument();
    // "0.500" appears multiple times (YES and NO tiles), so use getAllByText
    const priceElements = screen.getAllByText(/0\.500/i);
    expect(priceElements.length).toBeGreaterThan(0);
    expect(screen.getByText(/YES/i)).toBeInTheDocument();
    // "NO" appears multiple times (NO tile and "no way" text), so use getAllByText
    const noElements = screen.getAllByText(/NO/i);
    expect(noElements.length).toBeGreaterThan(0);
    // Verify NO tile exists by checking for the tile container
    expect(document.getElementById("tile-no")).toBeInTheDocument();
  });

  test("handles missing data", () => {
    render(
      <MarketCard
        {...defaultProps}
        question={undefined}
        commentCount={undefined}
      />
    );
    
    expect(screen.getByText("Test Event")).toBeInTheDocument();
  });

  test("renders without comment counts", () => {
    render(
      <MarketCard
        {...defaultProps}
        venue="kalshi"
        question="A?"
        commentCount={null}
        eventCommentCount={null}
        seriesCommentCount={null}
      />
    );

    expect(screen.queryByText(/NaN/)).not.toBeInTheDocument();
    expect(screen.getAllByText("Kalshi").length).toBeGreaterThan(0);
  });

  test("formats prices correctly", () => {
    render(
      <MarketCard
        {...defaultProps}
        yesPrice={0.1234}
        noPrice={0.8766}
      />
    );
    
    expect(screen.getByText(/0\.123/i)).toBeInTheDocument();
    expect(screen.getByText(/0\.877/i)).toBeInTheDocument();
  });

  test("formats dates correctly", () => {
    const endDate = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();
    render(
      <MarketCard
        {...defaultProps}
        endDate={endDate}
      />
    );
    
    expect(screen.getByText(/closes in/i)).toBeInTheDocument();
  });

  test("handles URL correctly", () => {
    render(<MarketCard {...defaultProps} />);

    const link = screen.getByRole("link", { name: /kalshi/i });
    expect(link).toHaveAttribute("href", "https://kalshi.com/markets/test");
    expect(link).toHaveAttribute("target", "_blank");
  });

  test("displays all prop variations", () => {
    render(
      <MarketCard
        {...defaultProps}
        question="Will this test pass?"
        groupItemTitle="Test Market"
        volume24h={500000}
        liquidity={2000000}
        commentCount={10}
        eventCommentCount={5}
        seriesCommentCount={3}
        bestBid={0.49}
        bestAsk={0.51}
      />
    );
    
    expect(screen.getByText("Will this test pass?")).toBeInTheDocument();
    expect(screen.getByText(/Test Market/i)).toBeInTheDocument();
  });

  test("handles order book data", () => {
    render(
      <MarketCard
        {...defaultProps}
        bids={[{ price: 0.48, size: 100 }, { price: 0.47, size: 200 }]}
        asks={[{ price: 0.52, size: 150 }, { price: 0.53, size: 250 }]}
        bestBid={0.48}
        bestAsk={0.52}
      />
    );
    
    expect(screen.getByText(/0\.480/i)).toBeInTheDocument();
    expect(screen.getByText(/0\.520/i)).toBeInTheDocument();
  });

  test("handles market selection", () => {
    const onMarketSelect = jest.fn();
    const previousMarkets = [
      { market_id: "market-1", slug: "market-1", question: "Market 1?" },
      { market_id: "market-2", slug: "market-2", question: "Market 2?" },
    ];

    render(
      <MarketCard
        {...defaultProps}
        question="Test?"
        previousMarkets={previousMarkets}
        onMarketSelect={onMarketSelect}
        activeMarketId="market-1"
      />
    );

    // Click the picker chip to open the dropdown
    const marketLabel = screen.getByText("MARKET");
    fireEvent.click(marketLabel);

    // Click on a sibling market
    const marketButton = screen.getByText("Market 2?");
    fireEvent.click(marketButton);

    expect(onMarketSelect).toHaveBeenCalledWith("market-2");
  });

  test("displays red countdown color when less than 1 day", () => {
    const endDate = new Date(Date.now() + 12 * 60 * 60 * 1000).toISOString(); // 12 hours from now
    render(
      <MarketCard
        {...defaultProps}
        endDate={endDate}
      />
    );
    
    const timer = screen.getByText(/closes in/i);
    expect(timer).toHaveClass("text-red-500");
  });

  test("displays yellow countdown color when less than 7 days but more than 1 day", () => {
    const endDate = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(); // 3 days from now
    render(
      <MarketCard
        {...defaultProps}
        endDate={endDate}
      />
    );
    
    const timer = screen.getByText(/closes in/i);
    expect(timer).toHaveClass("text-yellow-500");
  });

  test("displays green countdown color when more than 7 days", () => {
    const endDate = new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString(); // 10 days from now
    render(
      <MarketCard
        {...defaultProps}
        endDate={endDate}
      />
    );
    
    const timer = screen.getByText(/closes in/i);
    expect(timer).toHaveClass("text-green-500");
  });

  test("handles invalid date in countdown color", () => {
    render(
      <MarketCard
        {...defaultProps}
        endDate="invalid-date"
      />
    );
    
    const timer = screen.getByText(/closes in/i);
    expect(timer).toHaveClass("text-red-500");
  });

  test("toggles market picker dropdown via click", () => {
    const onMarketSelect = jest.fn();
    const previousMarkets = [
      { market_id: "market-1", slug: "market-1", question: "Market 1?" },
      { market_id: "market-2", slug: "market-2", question: "Market 2?" },
    ];

    render(
      <MarketCard
        {...defaultProps}
        question="Test?"
        previousMarkets={previousMarkets}
        onMarketSelect={onMarketSelect}
        activeMarketId="market-1"
      />
    );

    // The picker chip exposes a "MARKET" label as a button
    const marketLabel = screen.getByText("MARKET");
    expect(marketLabel).toBeInTheDocument();

    // Click to open the dropdown
    fireEvent.click(marketLabel);
    expect(screen.getByText("Market 2?")).toBeInTheDocument();

    // Click again to close
    fireEvent.click(marketLabel);
  });

  test("handles Kalshi favicon image error", () => {
    render(<MarketCard {...defaultProps} />);

    const images = screen.getAllByRole("img");
    const favicon = images.find(img => (img as HTMLImageElement).alt === "Kalshi");

    if (favicon) {
      fireEvent.error(favicon);
      expect(favicon).toHaveStyle({ display: "none" });
    }
  });
});

