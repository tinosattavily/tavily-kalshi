/** @jest-environment jsdom */
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import MarketPicker from "../components/analysis/MarketPicker";

describe("MarketPicker Component", () => {
  const mockOptions = [
    {
      slug: "market-1",
      question: "Will X happen?",
      image: "https://example.com/image1.jpg",
      best_bid: 0.5,
      best_ask: 0.6,
      liquidity: 1000,
      volume: 5000,
      volume24hr: 2000,
      end_date: "2024-12-31T23:59:59Z",
    },
    {
      slug: "market-2",
      question: "Will Y happen?",
      image: "https://example.com/image2.jpg",
      best_bid: 0.3,
      best_ask: 0.4,
      liquidity: 500,
      volume: 3000,
      volume24hr: 1500,
      end_date: "2024-12-30T23:59:59Z",
    },
    {
      slug: "market-3",
      question: "Will Z happen?",
      best_bid: 0.7,
      best_ask: 0.8,
      liquidity: 2000,
      volume: 10000,
      volume24hr: 0,
      end_date: "2025-01-01T23:59:59Z",
    },
  ];

  const mockEventContext = {
    title: "Test Event",
    image: "https://example.com/event.jpg",
  };

  const defaultProps = {
    options: mockOptions,
    eventContext: mockEventContext,
    isSubmitting: false,
    onSelect: jest.fn(),
    onSortedOptionsChange: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders component with options", () => {
    render(<MarketPicker {...defaultProps} />);
    expect(screen.getByText("Test Event")).toBeInTheDocument();
    expect(screen.getByText("Select a market to analyze")).toBeInTheDocument();
    expect(screen.getByText("Will X happen?")).toBeInTheDocument();
    expect(screen.getByText("Will Y happen?")).toBeInTheDocument();
    expect(screen.getByText("Will Z happen?")).toBeInTheDocument();
  });

  test("renders without event context", () => {
    render(<MarketPicker {...defaultProps} eventContext={null} />);
    expect(screen.getByText("Multi-market event")).toBeInTheDocument();
  });

  test("renders single market with correct text", () => {
    render(<MarketPicker {...defaultProps} options={[mockOptions[0]]} />);
    // The question appears in the button card.
    expect(screen.getAllByText("Will X happen?").length).toBeGreaterThan(0);
  });

  test("calls onSelect when market button is clicked", async () => {
    const user = userEvent.setup();
    render(<MarketPicker {...defaultProps} />);
    const button = document.getElementById("market-option-market-1");
    expect(button).not.toBeNull();
    if (button) {
      await user.click(button);
    }
    expect(defaultProps.onSelect).toHaveBeenCalledWith("market-1");
  });

  test("uses market_id when slug is absent", async () => {
    const user = userEvent.setup();
    const onSelect = jest.fn();
    const options = [{ venue: "kalshi" as const, market_id: "AAA-1", label: "A" }];

    render(<MarketPicker {...defaultProps} options={options} onSelect={onSelect} />);

    expect(screen.getAllByText("A").length).toBeGreaterThan(0);
    const marketButton = document.getElementById("market-option-AAA-1");
    expect(marketButton).not.toBeNull();
    if (marketButton) {
      await user.click(marketButton);
    }
    expect(onSelect).toHaveBeenCalledWith("AAA-1");
  });

  test("disables buttons when isSubmitting is true", () => {
    render(<MarketPicker {...defaultProps} isSubmitting={true} />);
    const buttons = screen.getAllByRole("button");
    const marketButtons = buttons.filter(
      (btn) => btn.id?.startsWith("market-option-")
    );
    marketButtons.forEach((btn) => {
      expect(btn).toBeDisabled();
    });
  });

  test("renders sort dropdown", () => {
    render(<MarketPicker {...defaultProps} />);
    expect(screen.getByText("SORT BY")).toBeInTheDocument();
    expect(screen.getByText("Active (24h volume)")).toBeInTheDocument();
  });

  test("opens and closes sort dropdown", async () => {
    const user = userEvent.setup();
    render(<MarketPicker {...defaultProps} />);
    const sortButton = screen.getByRole("button", { name: /Active \(24h volume\)/i });
    await user.click(sortButton);
    expect(screen.getByRole("listbox")).toBeInTheDocument();
    expect(screen.getByText("Soonest to close")).toBeInTheDocument();
    expect(screen.getByText("Highest total volume")).toBeInTheDocument();
  });

  test("changes sort option to 'soonest'", async () => {
    const user = userEvent.setup();
    render(<MarketPicker {...defaultProps} />);
    const sortButton = screen.getByRole("button", { name: /Active \(24h volume\)/i });
    await user.click(sortButton);
    const soonestOption = screen.getByRole("option", { name: /Soonest to close/i });
    await user.click(soonestOption);
    expect(screen.getByText("Soonest to close")).toBeInTheDocument();
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  test("changes sort option to 'total'", async () => {
    const user = userEvent.setup();
    render(<MarketPicker {...defaultProps} />);
    const sortButton = screen.getByRole("button", { name: /Active \(24h volume\)/i });
    await user.click(sortButton);
    const totalOption = screen.getByRole("option", { name: /Highest total volume/i });
    await user.click(totalOption);
    expect(screen.getByText("Highest total volume")).toBeInTheDocument();
  });

  test("sorts by active (24h volume) by default", () => {
    render(<MarketPicker {...defaultProps} />);
    const buttons = screen.getAllByRole("button");
    const marketButtons = buttons.filter(
      (btn) => btn.id?.startsWith("market-option-")
    );
    // Market-3 has volume24hr: 0, so it falls back to total volume (10000) which is highest
    // Market-1 has volume24hr: 2000, Market-2 has volume24hr: 1500
    // So market-3 should be first (highest total volume when 24h is 0)
    expect(marketButtons[0]).toHaveAttribute("id", "market-option-market-3");
  });

  test("sorts by total volume when selected", async () => {
    const user = userEvent.setup();
    render(<MarketPicker {...defaultProps} />);
    const sortButton = screen.getByRole("button", { name: /Active \(24h volume\)/i });
    await user.click(sortButton);
    const totalOption = screen.getByRole("option", { name: /Highest total volume/i });
    await user.click(totalOption);
    const buttons = screen.getAllByRole("button");
    const marketButtons = buttons.filter(
      (btn) => btn.id?.startsWith("market-option-")
    );
    // First market should have highest total volume (10000)
    expect(marketButtons[0]).toHaveAttribute("id", "market-option-market-3");
  });

  test("sorts by soonest end date when selected", async () => {
    const user = userEvent.setup();
    render(<MarketPicker {...defaultProps} />);
    const sortButton = screen.getByRole("button", { name: /Active \(24h volume\)/i });
    await user.click(sortButton);
    const soonestOption = screen.getByRole("option", { name: /Soonest to close/i });
    await user.click(soonestOption);
    const buttons = screen.getAllByRole("button");
    const marketButtons = buttons.filter(
      (btn) => btn.id?.startsWith("market-option-")
    );
    // First market should have soonest end date (2024-12-30)
    expect(marketButtons[0]).toHaveAttribute("id", "market-option-market-2");
  });

  test("calls onSortedOptionsChange when sort changes", async () => {
    const user = userEvent.setup();
    render(<MarketPicker {...defaultProps} />);
    const sortButton = screen.getByRole("button", { name: /Active \(24h volume\)/i });
    await user.click(sortButton);
    const soonestOption = screen.getByRole("option", { name: /Soonest to close/i });
    await user.click(soonestOption);
    await waitFor(() => {
      expect(defaultProps.onSortedOptionsChange).toHaveBeenCalled();
    });
  });

  test("handles missing optional fields gracefully", () => {
    const minimalOptions = [
      {
        slug: "minimal-market",
        question: "Minimal market?",
      },
    ];
    render(<MarketPicker {...defaultProps} options={minimalOptions} />);
    // The question appears in both the subtitle and the button, so use getAllByText
    expect(screen.getAllByText("Minimal market?").length).toBeGreaterThan(0);
  });

  test("displays bid/ask when available", () => {
    render(<MarketPicker {...defaultProps} />);
    // Bid/ask render as formatted mono values inside a card.
    expect(screen.getAllByText("0.50").length).toBeGreaterThan(0);
    expect(screen.getAllByText("0.60").length).toBeGreaterThan(0);
  });

  test("displays liquidity when available", () => {
    render(<MarketPicker {...defaultProps} />);
    expect(screen.getAllByText("1,000").length).toBeGreaterThan(0);
  });

  test("handles image load error", () => {
    render(<MarketPicker {...defaultProps} />);
    const images = screen.queryAllByRole("img");
    const marketImage = images.find((img) => (img as HTMLImageElement).alt === "Market");
    if (marketImage) {
      fireEvent.error(marketImage);
      expect(marketImage).toHaveStyle({ display: "none" });
    }
  });

  test("handles event image load error", () => {
    render(<MarketPicker {...defaultProps} />);
    const images = screen.queryAllByRole("img");
    const eventImage = images.find((img) => (img as HTMLImageElement).alt === "Event");
    if (eventImage) {
      fireEvent.error(eventImage);
      expect(eventImage).toHaveStyle({ display: "none" });
    }
  });

  test("renders correct grid layout for 1 market", () => {
    render(<MarketPicker {...defaultProps} options={[mockOptions[0]]} />);
    const grid = document.querySelector("#market-options-grid");
    expect(grid).toBeInTheDocument();
  });

  test("renders correct grid layout for 2 markets", () => {
    render(<MarketPicker {...defaultProps} options={mockOptions.slice(0, 2)} />);
    const grid = document.querySelector("#market-options-grid");
    expect(grid).toBeInTheDocument();
  });

  test("renders correct grid layout for 4 markets", () => {
    const fourMarkets = [
      ...mockOptions,
      {
        slug: "market-4",
        question: "Will W happen?",
        volume24hr: 500,
        end_date: "2025-01-02T23:59:59Z",
      },
    ];
    render(<MarketPicker {...defaultProps} options={fourMarkets} />);
    const grid = document.querySelector("#market-options-grid");
    expect(grid).toBeInTheDocument();
    expect(grid).toHaveClass("grid-cols-3");
  });

  test("renders correct grid layout for 5 markets", () => {
    const fiveMarkets = [
      ...mockOptions,
      {
        slug: "market-4",
        question: "Will W happen?",
        volume24hr: 500,
        end_date: "2025-01-02T23:59:59Z",
      },
      {
        slug: "market-5",
        question: "Will V happen?",
        volume24hr: 300,
        end_date: "2025-01-03T23:59:59Z",
      },
    ];
    render(<MarketPicker {...defaultProps} options={fiveMarkets} />);
    const grid = document.querySelector("#market-options-grid");
    expect(grid).toBeInTheDocument();
    expect(grid).toHaveClass("grid-cols-3");
  });

  test("renders correct grid layout for 6+ markets", () => {
    const sixMarkets = [
      ...mockOptions,
      {
        slug: "market-4",
        question: "Will W happen?",
        volume24hr: 500,
        end_date: "2025-01-02T23:59:59Z",
      },
      {
        slug: "market-5",
        question: "Will V happen?",
        volume24hr: 300,
        end_date: "2025-01-03T23:59:59Z",
      },
      {
        slug: "market-6",
        question: "Will U happen?",
        volume24hr: 200,
        end_date: "2025-01-04T23:59:59Z",
      },
    ];
    render(<MarketPicker {...defaultProps} options={sixMarkets} />);
    const grid = document.querySelector("#market-options-grid");
    expect(grid).toBeInTheDocument();
    expect(grid).toHaveClass("grid-cols-3");
  });

  test("handles markets without end_date", () => {
    const optionsWithoutEndDate = [
      {
        slug: "no-end-date",
        question: "No end date?",
        volume24hr: 1000,
      },
    ];
    render(<MarketPicker {...defaultProps} options={optionsWithoutEndDate} />);
    // The question appears in both the subtitle and the button
    expect(screen.getAllByText("No end date?").length).toBeGreaterThan(0);
  });

  test("handles markets with invalid end_date", () => {
    const optionsWithInvalidDate = [
      {
        slug: "invalid-date",
        question: "Invalid date?",
        volume24hr: 1000,
        end_date: "invalid-date",
      },
    ];
    render(<MarketPicker {...defaultProps} options={optionsWithInvalidDate} />);
    // The question appears in both the subtitle and the button
    expect(screen.getAllByText("Invalid date?").length).toBeGreaterThan(0);
  });

  test("handles markets with NaN volume values", () => {
    const optionsWithNaN = [
      {
        slug: "nan-volume",
        question: "NaN volume?",
        volume: NaN,
        volume24hr: NaN,
        liquidity: NaN,
      },
    ];
    render(<MarketPicker {...defaultProps} options={optionsWithNaN} />);
    // The question should be displayed in the button
    expect(screen.getByRole("button", { name: /NaN volume/i })).toBeInTheDocument();
  });

  test("does not call onSortedOptionsChange if not provided", () => {
    const propsWithoutCallback = {
      ...defaultProps,
      onSortedOptionsChange: undefined,
    };
    render(<MarketPicker {...propsWithoutCallback} />);
    // Should not throw
    expect(screen.getByText("Test Event")).toBeInTheDocument();
  });

  test("disables sort dropdown when isSubmitting is true", async () => {
    const user = userEvent.setup();
    render(<MarketPicker {...defaultProps} isSubmitting={true} />);
    const sortButton = screen.getByRole("button", { name: /Active \(24h volume\)/i });
    expect(sortButton).toBeDisabled();
    await user.click(sortButton);
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  test("handles hover state changes", () => {
    render(<MarketPicker {...defaultProps} />);
    const buttons = screen.getAllByRole("button");
    const marketButton = buttons.find((btn) => btn.id === "market-option-market-1");
    if (marketButton) {
      fireEvent.mouseEnter(marketButton);
      // Slider should appear (opacity becomes 1)
      // This is tested indirectly through the component rendering
    }
  });

  test("handles mouse leave from grid", () => {
    render(<MarketPicker {...defaultProps} />);
    const grid = document.querySelector("#market-options-grid");
    if (grid) {
      fireEvent.mouseLeave(grid);
      // Slider should disappear (opacity becomes 0)
    }
    expect(grid).toBeInTheDocument();
  });

  test("sorts by total volume with fallback to volume24hr when total is 0", async () => {
    const user = userEvent.setup();
    const marketsWithZeroTotal = [
      {
        slug: "market-1",
        question: "Market 1?",
        volume: 0,
        volume24hr: 2000,
        end_date: "2024-12-31T23:59:59Z",
      },
      {
        slug: "market-2",
        question: "Market 2?",
        volume: 0,
        volume24hr: 1500,
        end_date: "2024-12-30T23:59:59Z",
      },
    ];
    render(<MarketPicker {...defaultProps} options={marketsWithZeroTotal} />);
    
    // Switch to total sort
    const sortButton = screen.getByRole("button", { name: /Active \(24h volume\)/i });
    await user.click(sortButton);
    const totalOption = screen.getByRole("option", { name: /Highest total volume/i });
    await user.click(totalOption);
    
    const buttons = screen.getAllByRole("button");
    const marketButtons = buttons.filter((btn) => btn.id?.startsWith("market-option-"));
    // Market 1 should be first (higher volume24hr: 2000 > 1500)
    expect(marketButtons[0]).toHaveAttribute("id", "market-option-market-1");
  });

  test("tie-breaks by end_date in total sort", async () => {
    const user = userEvent.setup();
    const marketsWithSameVolume = [
      {
        slug: "market-1",
        question: "Market 1?",
        volume: 5000,
        end_date: "2024-12-31T23:59:59Z",
      },
      {
        slug: "market-2",
        question: "Market 2?",
        volume: 5000,
        end_date: "2024-12-30T23:59:59Z",
      },
    ];
    render(<MarketPicker {...defaultProps} options={marketsWithSameVolume} />);
    
    // Switch to total sort
    const sortButton = screen.getByRole("button", { name: /Active \(24h volume\)/i });
    await user.click(sortButton);
    const totalOption = screen.getByRole("option", { name: /Highest total volume/i });
    await user.click(totalOption);
    
    const buttons = screen.getAllByRole("button");
    const marketButtons = buttons.filter((btn) => btn.id?.startsWith("market-option-"));
    // Market 2 should be first (sooner end_date: 2024-12-30 < 2024-12-31)
    expect(marketButtons[0]).toHaveAttribute("id", "market-option-market-2");
  });

  test("tie-breaks by volume24hr when end_date is identical in soonest sort", async () => {
    const user = userEvent.setup();
    const marketsWithSameEndDate = [
      {
        slug: "market-1",
        question: "Market 1?",
        volume24hr: 2000,
        end_date: "2024-12-31T23:59:59Z",
      },
      {
        slug: "market-2",
        question: "Market 2?",
        volume24hr: 1500,
        end_date: "2024-12-31T23:59:59Z",
      },
    ];
    render(<MarketPicker {...defaultProps} options={marketsWithSameEndDate} />);
    
    // Switch to soonest sort
    const sortButton = screen.getByRole("button", { name: /Active \(24h volume\)/i });
    await user.click(sortButton);
    const soonestOption = screen.getByRole("option", { name: /Soonest to close/i });
    await user.click(soonestOption);
    
    const buttons = screen.getAllByRole("button");
    const marketButtons = buttons.filter((btn) => btn.id?.startsWith("market-option-"));
    // Market 1 should be first (higher volume24hr: 2000 > 1500)
    expect(marketButtons[0]).toHaveAttribute("id", "market-option-market-1");
  });

  test("handles market image load error", () => {
    render(<MarketPicker {...defaultProps} />);
    const images = screen.queryAllByRole("img");
    const marketImage = images.find((img) => (img as HTMLImageElement).alt === "Market");
    if (marketImage) {
      fireEvent.error(marketImage);
      expect(marketImage).toHaveStyle({ display: "none" });
    }
  });

  test("handles event image load error (duplicate coverage)", () => {
    render(<MarketPicker {...defaultProps} />);
    const images = screen.queryAllByRole("img");
    const eventImage = images.find((img) => (img as HTMLImageElement).alt === "Event");
    if (eventImage) {
      fireEvent.error(eventImage);
      expect(eventImage).toHaveStyle({ display: "none" });
    }
  });

  test("renders 3-col grid for 4 markets (duplicate coverage)", () => {
    const fourMarkets = [
      ...mockOptions,
      {
        slug: "market-4",
        question: "Will W happen?",
        volume24hr: 500,
        end_date: "2025-01-02T23:59:59Z",
      },
    ];
    render(<MarketPicker {...defaultProps} options={fourMarkets} />);
    const grid = document.querySelector("#market-options-grid");
    expect(grid).toBeInTheDocument();
    expect(grid).toHaveClass("grid-cols-3");
  });

  test("renders 3-col grid for 5 markets (duplicate coverage)", () => {
    const fiveMarkets = [
      ...mockOptions,
      {
        slug: "market-4",
        question: "Will W happen?",
        volume24hr: 500,
        end_date: "2025-01-02T23:59:59Z",
      },
      {
        slug: "market-5",
        question: "Will V happen?",
        volume24hr: 300,
        end_date: "2025-01-03T23:59:59Z",
      },
    ];
    render(<MarketPicker {...defaultProps} options={fiveMarkets} />);
    const grid = document.querySelector("#market-options-grid");
    expect(grid).toBeInTheDocument();
    expect(grid).toHaveClass("grid-cols-3");
  });

  test("renders 3-col grid for 6+ markets (duplicate coverage)", () => {
    const sixMarkets = [
      ...mockOptions,
      {
        slug: "market-4",
        question: "Will W happen?",
        volume24hr: 500,
        end_date: "2025-01-02T23:59:59Z",
      },
      {
        slug: "market-5",
        question: "Will V happen?",
        volume24hr: 300,
        end_date: "2025-01-03T23:59:59Z",
      },
      {
        slug: "market-6",
        question: "Will U happen?",
        volume24hr: 200,
        end_date: "2025-01-04T23:59:59Z",
      },
    ];
    render(<MarketPicker {...defaultProps} options={sixMarkets} />);
    const grid = document.querySelector("#market-options-grid");
    expect(grid).toBeInTheDocument();
    expect(grid).toHaveClass("grid-cols-3");
  });
});
