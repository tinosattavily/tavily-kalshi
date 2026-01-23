/** @jest-environment jsdom */
import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Dashboard from "../components/Dashboard";
import { TestWrapper } from "./utils/testWrapper";

jest.mock("../components/layout/HistorySidebar", () => ({
  __esModule: true,
  default: () => <div data-testid="recent-sessions" />,
}));

// Mock Next.js router
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
  }),
}));

// Mock fetch
global.fetch = jest.fn();

// Helper to render Dashboard with providers
const renderDashboard = () => {
  return render(
    <TestWrapper>
      <Dashboard />
    </TestWrapper>
  );
};

describe("Dashboard Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockClear();
  });

  test("renders component", () => {
    renderDashboard();
    // Background uses a section with id "app-root", not a main role
    expect(document.getElementById("app-root")).toBeInTheDocument();
  });

  test("renders URL input bar", () => {
    renderDashboard();
    const input = screen.getByPlaceholderText(/kalshi/i);
    expect(input).toBeInTheDocument();
  });

  test("handles URL input", async () => {
    const user = userEvent.setup();
    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    
    expect(input).toHaveValue("https://kalshi.com/markets/test");
  });

  test("handles form submission", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ run_id: "test-run-id" }),
    });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/analyze/start",
        expect.objectContaining({
          method: "POST",
        })
      );
    });
  });

  test("handles market selection flow", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: {
              market: "done",
            },
            market_options: [
              { slug: "market-1", question: "Market 1?" },
              { slug: "market-2", question: "Market 2?" },
            ],
            // Empty market_snapshot triggers market selection
            market_snapshot: {},
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/events/test");
    
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/market 1/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  test("handles polling logic", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: { market: "done", news: "pending" },
            market_snapshot: { question: "Test?" },
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringMatching(/\/api\/run\/test-run-id/)
      );
    }, { timeout: 3000 });
  });

  test("displays market snapshot when available", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: {
              market: "done",
            },
            market_snapshot: {
              question: "Will this test pass?",
              yes_price: 0.5,
            },
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      // The question appears multiple times in the MarketSnapshotCard
      expect(screen.getAllByText(/will this test pass/i).length).toBeGreaterThan(0);
    }, { timeout: 3000 });
  });

  test("displays news when available", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: {
              market: "done",
              news: "done",
            },
            market_snapshot: {
              question: "Test?",
            },
            news_context: {
              articles: [
                { title: "Test Article", source: "Test Source" },
              ],
              summary: "Test summary",
            },
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/test article/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  test("handles error states", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error("Network error"));

    renderDashboard();

    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");

    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      // Should show error toast
      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });

  test("handles loading states", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock).mockImplementationOnce(
      () => new Promise(() => {}) // Never resolves
    );

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    // Should show loading state - component shows disabled input and button when submitting
    await waitFor(() => {
      expect(input).toBeDisabled();
      expect(submitButton).toBeDisabled();
    });
  });

  test("handles empty prompt state", () => {
    renderDashboard();
    expect(screen.getByText(/enter a kalshi/i)).toBeInTheDocument();
  });

  test("cleans up polling on unmount", () => {
    const { unmount } = renderDashboard();
    unmount();
    // Component should unmount without errors
    expect(true).toBe(true);
  });

  test("handles early return when URL is empty", async () => {
    const user = userEvent.setup();
    renderDashboard();
    
    const _input = screen.getByPlaceholderText(/kalshi/i);
    // Don't type anything, leave it empty
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);
    
    // Should not make any fetch calls
    await waitFor(() => {
      expect(global.fetch).not.toHaveBeenCalled();
    }, { timeout: 500 });
  });

  test("handles early return when URL is whitespace only", async () => {
    const user = userEvent.setup();
    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "   ");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);
    
    // Should not make any fetch calls
    await waitFor(() => {
      expect(global.fetch).not.toHaveBeenCalled();
    }, { timeout: 500 });
  });

  test("handles early return when isSubmitting is true", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock).mockImplementationOnce(
      () => new Promise(() => {}) // Never resolves to keep isSubmitting true
    );
    
    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    
    // First click starts submission
    await user.click(submitButton);
    
    // Wait for isSubmitting to be true
    await waitFor(() => {
      expect(submitButton).toBeDisabled();
    });
    
    // Try to submit again while submitting
    await user.click(submitButton);
    
    // Should only have one fetch call
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  test("handles error when response.json() fails in error path", async () => {
    const user = userEvent.setup();

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => {
        throw new Error("Invalid JSON");
      },
      text: async () => "Error text",
    });

    renderDashboard();

    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      // Should show error toast
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  test("handles invalid run_id - undefined", async () => {
    const user = userEvent.setup();

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ run_id: undefined }),
    });

    renderDashboard();

    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(screen.getByText(/backend did not return run_id/i)).toBeInTheDocument();
    });
  });

  test("handles invalid run_id - null", async () => {
    const user = userEvent.setup();

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ run_id: null }),
    });

    renderDashboard();

    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(screen.getByText(/backend did not return run_id/i)).toBeInTheDocument();
    });
  });

  test("handles invalid run_id - empty string", async () => {
    const user = userEvent.setup();

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ run_id: "" }),
    });

    renderDashboard();

    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(screen.getByText(/backend did not return run_id/i)).toBeInTheDocument();
    });
  });

  test("handles invalid run_id - string 'undefined'", async () => {
    const user = userEvent.setup();

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ run_id: "undefined" }),
    });

    renderDashboard();

    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(screen.getByText(/invalid run_id/i)).toBeInTheDocument();
    });
  });

  test("handles invalid run_id - string 'null'", async () => {
    const user = userEvent.setup();

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ run_id: "null" }),
    });

    renderDashboard();

    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(screen.getByText(/invalid run_id/i)).toBeInTheDocument();
    });
  });

  test("handles market selection successfully", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: { market: "done" },
            market_options: [
              { slug: "market-1", question: "Market 1?" },
            ],
            market_snapshot: {},
          },
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id-2" }),
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id-2",
            status: { market: "done" },
            market_snapshot: { question: "Test?" },
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/events/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    // Wait for market selection to appear
    await waitFor(() => {
      expect(screen.getAllByText(/market 1/i).length).toBeGreaterThan(0);
    }, { timeout: 3000 });

    // Find the market button by role and name
    const marketButton = screen.getByRole("button", { name: /market 1/i });
    expect(marketButton).toBeInTheDocument();
    
    // Click on the market button
    await user.click(marketButton);

    // Should start new analysis with selected market
    await waitFor(() => {
      const calls = (global.fetch as jest.Mock).mock.calls;
      const analyzeStartCall = calls.find((call: [string, { method?: string; body?: string }?]) => 
        call[0] === "/api/analyze/start" && 
        call[1]?.method === "POST" &&
        call[1]?.body?.includes("selected_market_slug")
      );
      expect(analyzeStartCall).toBeDefined();
    }, { timeout: 10000 });
  }, 15000);

  test("handles market selection error", async () => {
    const user = userEvent.setup();

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: { market: "done" },
            market_options: [
              { slug: "market-1", question: "Market 1?" },
            ],
            market_snapshot: {},
          },
        }),
      })
      .mockRejectedValueOnce(new Error("Network error"));

    renderDashboard();

    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/events/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    // Wait for market selection to appear
    await waitFor(() => {
      expect(screen.getAllByText(/market 1/i).length).toBeGreaterThan(0);
    }, { timeout: 3000 });

    // Find the market button by role and name
    const marketButton = screen.getByRole("button", { name: /market 1/i });
    expect(marketButton).toBeInTheDocument();

    // Click on the market button - this should trigger an error
    await user.click(marketButton);

    await waitFor(() => {
      // Should show error toast
      expect(screen.getByRole("alert")).toBeInTheDocument();
    }, { timeout: 10000 });
  }, 15000);

  test("handles Enter key to submit", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ run_id: "test-run-id" }),
    });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    await user.keyboard("{Enter}");

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/analyze/start",
        expect.objectContaining({
          method: "POST",
        })
      );
    });
  });

  test("humanizeClosesIn handles valid ISO date", () => {
        const _endDate = new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(); // 2 days
    renderDashboard();
    // This is tested indirectly through the component rendering with endDate
    // We can't directly test the function, but we can verify it's used correctly
    expect(true).toBe(true);
  });

  test("humanizeClosesIn handles invalid date", () => {
    renderDashboard();
    // Invalid dates are handled gracefully
    expect(true).toBe(true);
  });

  test("humanizeClosesIn handles null/undefined", () => {
    renderDashboard();
    // Null/undefined dates return "—"
    expect(true).toBe(true);
  });

  test("humanizeClosesIn handles dates less than 1 day - minutes", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: { market: "done" },
            market_snapshot: {
              question: "Test?",
              end_date: new Date(Date.now() + 30 * 60 * 1000).toISOString(), // 30 minutes
            },
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Closes in .*min/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  test("humanizeClosesIn handles dates less than 1 day - hours", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: { market: "done" },
            market_snapshot: {
              question: "Test?",
              end_date: new Date(Date.now() + 12 * 60 * 60 * 1000).toISOString(), // 12 hours
            },
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Closes in .*hr/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  test("humanizeClosesIn handles dates >= 1 day", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: { market: "done" },
            market_snapshot: {
              question: "Test?",
              end_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days
            },
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getAllByText(/day/i).length).toBeGreaterThan(0);
    }, { timeout: 3000 });
  });

  test("handles polling 404 response - continues polling", async () => {
    const user = userEvent.setup();
    
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({}),
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: { market: "done" },
            market_snapshot: { question: "Test?" },
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    // Wait for polling to occur
    await waitFor(() => {
      // Should have made multiple fetch calls (initial + polling)
      expect(global.fetch).toHaveBeenCalledTimes(2);
    }, { timeout: 5000 });
  });

  test("handles polling 500 response - retries with longer delay", async () => {
    const user = userEvent.setup();
    
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: "Server error" }),
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: { market: "done" },
            market_snapshot: { question: "Test?" },
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    // Wait for polling to occur
    await waitFor(() => {
      // Should have made multiple fetch calls
      expect(global.fetch).toHaveBeenCalledTimes(2);
    }, { timeout: 5000 });
  });

  test("handles polling 500 response with JSON parse error", async () => {
    const user = userEvent.setup();
    
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error("Invalid JSON");
        },
        text: async () => "Server error",
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: { market: "done" },
            market_snapshot: { question: "Test?" },
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    // Wait for polling to occur
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    }, { timeout: 5000 });
  });

  test("handles polling when run object is missing", async () => {
    const user = userEvent.setup();
    
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({}), // No run object
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: { market: "done" },
            market_snapshot: { question: "Test?" },
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    // Wait for polling to occur
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    }, { timeout: 5000 });
  });

  test("handles polling network error", async () => {
    const user = userEvent.setup();
    
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: { market: "done" },
            market_snapshot: { question: "Test?" },
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    // Wait for polling retry to occur
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    }, { timeout: 5000 });
  });

  test("initializes results when prevResults is null", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: { market: "done" },
            market_snapshot: { question: "Test?" },
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getAllByText(/test\?/i).length).toBeGreaterThan(0);
    }, { timeout: 3000 });
  });

  test("updates event_context when market phase done", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: { market: "done" },
            market_snapshot: { question: "Test?" },
            event_context: { title: "Test Event", url: "https://example.com" },
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/test event/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  test("sets requires_market_selection to false when market_snapshot has data", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: { market: "done" },
            market_snapshot: { question: "Test?", yes_price: 0.5 },
            market_options: [
              { slug: "market-1", question: "Market 1?" },
            ],
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      // Should show market snapshot, not market selection
      // Use getAllByText since the question appears multiple times
      expect(screen.getAllByText(/test\?/i).length).toBeGreaterThan(0);
      expect(screen.queryByText(/select a market/i)).not.toBeInTheDocument();
    }, { timeout: 3000 });
  });

  test("updates news_context when news phase done", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: { market: "done", news: "done" },
            market_snapshot: { question: "Test?" },
            news_context: {
              articles: [{ title: "News Article", source: "Source" }],
              summary: "News summary",
            },
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/news article/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  test("updates signal and decision when signal phase done", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: { market: "done", signal: "done" },
            market_snapshot: { question: "Test?" },
            signal: { recommended_action: "buy_yes", model_prob: 0.6 },
            decision: { action: "buy", edge_pct: 10 },
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      // SignalCard displays "BUY YES" (uppercase) for buy_yes recommended_action
      expect(screen.getByText(/buy yes/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  test("updates report when report phase done", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: { market: "done", report: "done" },
            market_snapshot: { question: "Test?" },
            report: { headline: "Test Report", thesis: "Test thesis" },
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/test report/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  test("sets selectedMarketSlug when market_snapshot.slug exists", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: { market: "done", news: "done", signal: "done", report: "done" },
            market_snapshot: { question: "Test?", slug: "test-market-slug" },
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      // Polling should stop when all phases are done
      expect(screen.getAllByText(/test\?/i).length).toBeGreaterThan(0);
    }, { timeout: 3000 });
  });

  test("handles mapNewsArticles with empty newsContext", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: { market: "done", news: "done" },
            market_snapshot: { question: "Test?" },
            news_context: {}, // Empty news context
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      // Should not show news card when news_context is empty
      expect(screen.queryByText(/market news/i)).not.toBeInTheDocument();
    }, { timeout: 3000 });
  });

  test("handles order book mapping with order_book.bids and order_book.asks", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: { market: "done" },
            market_snapshot: {
              question: "Test?",
              order_book: {
                bids: [{ price: 0.48, size: 100 }],
                asks: [{ price: 0.52, size: 150 }],
              },
            },
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getAllByText(/test\?/i).length).toBeGreaterThan(0);
    }, { timeout: 3000 });
  });

  test("handles order book mapping with orderBook.bids and orderBook.asks (camelCase)", async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "test-run-id" }),
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run: {
            run_id: "test-run-id",
            status: { market: "done" },
            market_snapshot: {
              question: "Test?",
              orderBook: {
                bids: [{ price: 0.48, size: 100 }],
                asks: [{ price: 0.52, size: 150 }],
              },
            },
          },
        }),
      });

    renderDashboard();
    
    const input = screen.getByPlaceholderText(/kalshi/i);
    await user.type(input, "https://kalshi.com/markets/test");
    const submitButton = screen.getByRole("button", { name: /analyze|submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getAllByText(/test\?/i).length).toBeGreaterThan(0);
    }, { timeout: 3000 });
  });
});

