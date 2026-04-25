/** @jest-environment node */
/* eslint-disable @typescript-eslint/no-explicit-any */
import { GET } from "../../../../app/api/run/[run_id]/route";
import { logger } from "../../../../lib/logger";

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

jest.mock("../../../../lib/logger", () => ({
  logger: {
    error: jest.fn(),
    warn: jest.fn(),
    info: jest.fn(),
    debug: jest.fn(),
  },
}));

// Mock fetch
global.fetch = jest.fn();

describe("GET /api/run/[run_id]", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    jest.clearAllMocks();
    process.env = { ...originalEnv };
    delete process.env.BACKEND_URL;
    Object.defineProperty(process.env, "NODE_ENV", {
      value: "development",
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  test("fetches run from backend successfully with sync params", async () => {
    const originalEnv = process.env.NODE_ENV;
    // Use Object.defineProperty to bypass TypeScript read-only check in tests
    Object.defineProperty(process.env, 'NODE_ENV', {
      value: 'development',
      writable: true,
      configurable: true,
    });
    
    const mockRequest = {} as any;
    const params = { run_id: "test-run-id" };

    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({ run_id: "test-run-id", status: "completed" }),
    };

    (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

    const response = await GET(mockRequest, { params });

    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/run/test-run-id",
      expect.objectContaining({
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        signal: expect.any(Object),
      })
    );

    const responseData = await response.json();
    expect(responseData).toEqual({ run_id: "test-run-id", status: "completed" });
    // Restore original NODE_ENV
    Object.defineProperty(process.env, 'NODE_ENV', {
      value: originalEnv,
      writable: true,
      configurable: true,
    });
  });

  test("fetches run from backend successfully with async params", async () => {
    const mockRequest = {} as any;
    const params = Promise.resolve({ run_id: "test-run-id" });

    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({ run_id: "test-run-id", status: "completed" }),
    };

    (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

    const consoleLogSpy = jest.spyOn(console, "log").mockImplementation();

    const response = await GET(mockRequest, { params });

    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/run/test-run-id",
      expect.objectContaining({
        signal: expect.any(Object),
      })
    );

    const responseData = await response.json();
    expect(responseData).toEqual({ run_id: "test-run-id", status: "completed" });

    consoleLogSpy.mockRestore();
  });

  test("uses BACKEND_URL from environment", async () => {
    process.env.BACKEND_URL = "https://api.example.com";

    const mockRequest = {} as any;
    const params = { run_id: "test-run-id" };

    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({ run_id: "test-run-id" }),
    };

    (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

    await GET(mockRequest, { params });

    expect(global.fetch).toHaveBeenCalledWith(
      "https://api.example.com/api/run/test-run-id",
      expect.any(Object)
    );
  });

  test("validates run_id and returns 400 for missing run_id", async () => {
    const mockRequest = {} as any;
    const params = { run_id: "" };

    const response = await GET(mockRequest, { params });

    expect(response.status).toBe(400);
    const responseData = await response.json();
    expect(responseData.error).toBe("Invalid run_id parameter");
    expect(responseData.received).toBe("");
    expect(logger.error).toHaveBeenCalledWith(
      "[Next.js API] Invalid run_id in route params:",
      "",
      "type:",
      "string"
    );
  });

  test("validates run_id and returns 400 for 'undefined' string", async () => {
    const mockRequest = {} as any;
    const params = { run_id: "undefined" };

    const response = await GET(mockRequest, { params });

    expect(response.status).toBe(400);
    const responseData = await response.json();
    expect(responseData.error).toBe("Invalid run_id parameter");
    expect(responseData.received).toBe("undefined");

  });

  test("validates run_id and returns 400 for 'null' string", async () => {
    const mockRequest = {} as any;
    const params = { run_id: "null" };

    const response = await GET(mockRequest, { params });

    expect(response.status).toBe(400);
    const responseData = await response.json();
    expect(responseData.error).toBe("Invalid run_id parameter");
    expect(responseData.received).toBe("null");

  });

  test("encodes run_id in URL", async () => {
    const mockRequest = {} as any;
    const params = { run_id: "test/run?id=123" };

    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({ run_id: "test/run?id=123" }),
    };

    (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

    await GET(mockRequest, { params });

    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/run/test%2Frun%3Fid%3D123",
      expect.objectContaining({
        signal: expect.any(Object),
      })
    );
  });

  test("handles backend error with JSON response", async () => {
    const mockRequest = {} as any;
    const params = { run_id: "test-run-id" };

    const mockResponse = {
      ok: false,
      status: 404,
      json: jest.fn().mockResolvedValue({ detail: "Run not found" }),
    };

    (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

    const response = await GET(mockRequest, { params });

    expect(response.status).toBe(404);
    const responseData = await response.json();
    expect(responseData.error).toBe("Backend error: 404");
    expect(responseData.detail).toBe("Run not found");
    expect(responseData.details).toEqual({ detail: "Run not found" });
  });

  test("handles backend error with text response", async () => {
    const mockRequest = {} as any;
    const params = { run_id: "test-run-id" };

    const mockResponse = {
      ok: false,
      status: 500,
      json: jest.fn().mockRejectedValue(new Error("Not JSON")),
      text: jest.fn().mockResolvedValue("Internal Server Error"),
    };

    (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

    const response = await GET(mockRequest, { params });

    expect(response.status).toBe(500);
    const responseData = await response.json();
    expect(responseData.error).toBe("Backend error: 500");
    expect(responseData.detail).toBe("Internal Server Error");
  });

  test("handles backend error with error field", async () => {
    const mockRequest = {} as any;
    const params = { run_id: "test-run-id" };

    const mockResponse = {
      ok: false,
      status: 400,
      json: jest.fn().mockResolvedValue({ error: "Validation error" }),
    };

    (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

    const response = await GET(mockRequest, { params });

    const responseData = await response.json();
    expect(responseData.detail).toBe("Validation error");
  });

  test("handles backend error with message field", async () => {
    const mockRequest = {} as any;
    const params = { run_id: "test-run-id" };

    const mockResponse = {
      ok: false,
      status: 400,
      json: jest.fn().mockResolvedValue({ message: "Error message" }),
    };

    (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

    const response = await GET(mockRequest, { params });

    const responseData = await response.json();
    expect(responseData.detail).toBe("Error message");
  });

  test("handles backend error with unknown error shape", async () => {
    const mockRequest = {} as any;
    const params = { run_id: "test-run-id" };

    const mockResponse = {
      ok: false,
      status: 500,
      json: jest.fn().mockResolvedValue({}),
    };

    (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

    const response = await GET(mockRequest, { params });

    const responseData = await response.json();
    expect(responseData.detail).toBe("Unknown error");
  });

  test("handles fetch error", async () => {
    const mockRequest = {} as any;
    const params = { run_id: "test-run-id" };

    (global.fetch as jest.Mock).mockRejectedValue(new Error("Network error"));

    const response = await GET(mockRequest, { params });

    expect(response.status).toBe(500);
    const responseData = await response.json();
    expect(responseData.error).toBe("Failed to connect to backend");
    expect(responseData.detail).toBe("Network error");
    expect(logger.error).toHaveBeenCalledWith(
      "Error proxying to backend:",
      expect.any(Error)
    );
  });

  test("handles non-Error exception", async () => {
    const mockRequest = {} as any;
    const params = { run_id: "test-run-id" };

    (global.fetch as jest.Mock).mockRejectedValue("String error");

    const response = await GET(mockRequest, { params });

    expect(response.status).toBe(500);
    const responseData = await response.json();
    expect(responseData.error).toBe("Failed to connect to backend");
    expect(responseData.detail).toBe("String error");
  });

  test("handles empty text response in error", async () => {
    const mockRequest = {} as any;
    const params = { run_id: "test-run-id" };

    const mockResponse = {
      ok: false,
      status: 404,
      json: jest.fn().mockRejectedValue(new Error("Not JSON")),
      text: jest.fn().mockResolvedValue(""),
    };

    (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

    const response = await GET(mockRequest, { params });

    expect(response.status).toBe(404);
    const responseData = await response.json();
    expect(responseData.error).toBe("Backend error: 404");
    expect(responseData.detail).toBe("Backend error: 404");
  });
});

