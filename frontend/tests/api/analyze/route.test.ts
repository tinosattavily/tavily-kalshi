/** @jest-environment node */
/* eslint-disable @typescript-eslint/no-explicit-any */
import { POST } from "../../../app/api/analyze/route";

// Mock Next.js server
jest.mock("next/server", () => ({
  NextRequest: jest.fn(),
  NextResponse: {
    json: jest.fn((data, init) => ({
      json: async () => data,
      status: init?.status || 200,
      ok: (init?.status || 200) < 400,
    })),
  },
}));

// Mock fetch
global.fetch = jest.fn();

describe("POST /api/analyze", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    jest.clearAllMocks();
    process.env = { ...originalEnv };
    delete process.env.BACKEND_URL;
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  test("proxies request to backend successfully", async () => {
    const originalNodeEnv = process.env.NODE_ENV;
    Object.defineProperty(process.env, "NODE_ENV", {
      value: "development",
      writable: true,
      configurable: true,
    });

    const mockRequest = {
      json: jest.fn().mockResolvedValue({ url: "https://polymarket.com/event/123" }),
    };

    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({ run_id: "test-run-id" }),
    };

    (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

    const response = await POST(mockRequest as any);

    // The route now calls /api/analyze/start and includes signal
    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/analyze/start",
      expect.objectContaining({
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: "https://polymarket.com/event/123" }),
        signal: expect.any(AbortSignal),
      })
    );

    expect(mockRequest.json).toHaveBeenCalled();
    const responseData = await response.json();
    expect(responseData).toEqual({ run_id: "test-run-id" });

    Object.defineProperty(process.env, "NODE_ENV", {
      value: originalNodeEnv,
      writable: true,
      configurable: true,
    });
  });

  test("uses BACKEND_URL from environment", async () => {
    process.env.BACKEND_URL = "https://api.example.com";

    const mockRequest = {
      json: jest.fn().mockResolvedValue({ url: "https://polymarket.com/event/123" }),
    };

    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({ run_id: "test-run-id" }),
    };

    (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

    await POST(mockRequest as any);

    expect(global.fetch).toHaveBeenCalledWith(
      "https://api.example.com/api/analyze/start",
      expect.any(Object)
    );
  });

  test("handles backend error with JSON response", async () => {
    const mockRequest = {
      json: jest.fn().mockResolvedValue({ url: "https://polymarket.com/event/123" }),
    };

    const mockResponse = {
      ok: false,
      status: 400,
      json: jest.fn().mockResolvedValue({ detail: "Invalid URL" }),
    };

    (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

    const response = await POST(mockRequest as any);

    expect(response.status).toBe(400);
    const responseData = await response.json();
    expect(responseData.error).toBe("Backend error: 400");
    expect(responseData.detail).toBe("Invalid URL");
    expect(responseData.details).toEqual({ detail: "Invalid URL" });
  });

  test("handles backend error with text response", async () => {
    const mockRequest = {
      json: jest.fn().mockResolvedValue({ url: "https://polymarket.com/event/123" }),
    };

    const mockResponse = {
      ok: false,
      status: 500,
      json: jest.fn().mockRejectedValue(new Error("Not JSON")),
      text: jest.fn().mockResolvedValue("Internal Server Error"),
    };

    (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

    const response = await POST(mockRequest as any);

    expect(response.status).toBe(500);
    const responseData = await response.json();
    expect(responseData.error).toBe("Backend error: 500");
    expect(responseData.detail).toBe("Internal Server Error");
  });

  test("handles backend error with empty text response", async () => {
    const mockRequest = {
      json: jest.fn().mockResolvedValue({ url: "https://polymarket.com/event/123" }),
    };

    const mockResponse = {
      ok: false,
      status: 404,
      json: jest.fn().mockRejectedValue(new Error("Not JSON")),
      text: jest.fn().mockResolvedValue(""),
    };

    (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

    const response = await POST(mockRequest as any);

    expect(response.status).toBe(404);
    const responseData = await response.json();
    expect(responseData.error).toBe("Backend error: 404");
    expect(responseData.detail).toBe("Backend error: 404");
  });

  test("handles backend error with error field", async () => {
    const mockRequest = {
      json: jest.fn().mockResolvedValue({ url: "https://polymarket.com/event/123" }),
    };

    const mockResponse = {
      ok: false,
      status: 400,
      json: jest.fn().mockResolvedValue({ error: "Validation error" }),
    };

    (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

    const response = await POST(mockRequest as any);

    const responseData = await response.json();
    expect(responseData.detail).toBe("Validation error");
  });

  test("handles backend error with message field", async () => {
    const mockRequest = {
      json: jest.fn().mockResolvedValue({ url: "https://polymarket.com/event/123" }),
    };

    const mockResponse = {
      ok: false,
      status: 400,
      json: jest.fn().mockResolvedValue({ message: "Error message" }),
    };

    (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

    const response = await POST(mockRequest as any);

    const responseData = await response.json();
    expect(responseData.detail).toBe("Error message");
  });

  test("handles backend error with unknown error shape", async () => {
    const mockRequest = {
      json: jest.fn().mockResolvedValue({ url: "https://polymarket.com/event/123" }),
    };

    const mockResponse = {
      ok: false,
      status: 500,
      json: jest.fn().mockResolvedValue({}),
    };

    (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

    const response = await POST(mockRequest as any);

    const responseData = await response.json();
    expect(responseData.detail).toBe("Unknown error");
  });

  test("handles fetch error", async () => {
    const mockRequest = {
      json: jest.fn().mockResolvedValue({ url: "https://polymarket.com/event/123" }),
    };

    (global.fetch as jest.Mock).mockRejectedValue(new Error("Network error"));

    const response = await POST(mockRequest as any);

    expect(response.status).toBe(500);
    const responseData = await response.json();
    expect(responseData.error).toBe("Failed to connect to backend");
    expect(responseData.detail).toBe("Network error");
  });

  test("handles non-Error exception", async () => {
    const mockRequest = {
      json: jest.fn().mockResolvedValue({ url: "https://polymarket.com/event/123" }),
    };

    (global.fetch as jest.Mock).mockRejectedValue("String error");

    const response = await POST(mockRequest as any);

    expect(response.status).toBe(500);
    const responseData = await response.json();
    expect(responseData.error).toBe("Failed to connect to backend");
    expect(responseData.detail).toBe("String error");
  });

  test("handles request.json() error", async () => {
    const mockRequest = {
      json: jest.fn().mockRejectedValue(new Error("Invalid JSON")),
    };

    const response = await POST(mockRequest as any);

    expect(response.status).toBe(500);
    const responseData = await response.json();
    expect(responseData.error).toBe("Failed to connect to backend");
  });

  test("forwards request body correctly", async () => {
    const requestBody = {
      url: "https://polymarket.com/event/123",
      options: { include_news: true },
    };

    const mockRequest = {
      json: jest.fn().mockResolvedValue(requestBody),
    };

    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({ run_id: "test-run-id" }),
    };

    (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

    await POST(mockRequest as any);

    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        body: JSON.stringify(requestBody),
      })
    );
  });
});
