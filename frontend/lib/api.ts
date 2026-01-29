import { NextResponse } from "next/server";

import { logger } from "./logger";

const DEFAULT_DEV_BACKEND = "http://localhost:8000";
const DEFAULT_PROD_BACKEND = "https://tavily-backend-env.eba-jv6q9hd7.us-east-1.elasticbeanstalk.com";

export function getBackendUrl(): string {
  if (process.env.BACKEND_URL) {
    return process.env.BACKEND_URL;
  }
  return process.env.NODE_ENV === "development" ? DEFAULT_DEV_BACKEND : DEFAULT_PROD_BACKEND;
}

export function handleFetchError(error: unknown): NextResponse {
  const errorMessage = error instanceof Error ? error.message : String(error);
  return NextResponse.json(
    { error: "Failed to connect to backend", detail: errorMessage },
    { status: 500 },
  );
}

export async function parseErrorResponse(response: Response): Promise<Record<string, unknown>> {
  try {
    return (await response.json()) as Record<string, unknown>;
  } catch {
    const errorText = await response.text();
    return { detail: errorText || `Backend error: ${response.status}` };
  }
}

export function buildErrorResponse(status: number, errorData: Record<string, unknown>): NextResponse {
  const detail =
    (errorData.detail as string) ||
    (errorData.error as string) ||
    (errorData.message as string) ||
    "Unknown error";

  return NextResponse.json(
    { error: `Backend error: ${status}`, detail, details: errorData },
    { status },
  );
}

function isAbortError(error: unknown): boolean {
  return error instanceof Error && (error.name === "AbortError" || error.message.includes("aborted"));
}

export function createTimeoutResponse(message: string): NextResponse {
  return NextResponse.json({ error: "Request timeout", detail: message }, { status: 504 });
}

interface ProxyRequestOptions {
  url: string;
  method?: "GET" | "POST";
  body?: unknown;
  timeoutMs: number;
  timeoutMessage: string;
  logContext?: string;
}

export async function proxyBackendRequest(options: ProxyRequestOptions): Promise<NextResponse> {
  const { url, method = "GET", body, timeoutMs, timeoutMessage, logContext = "proxy" } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const fetchOptions: RequestInit = {
      method,
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
    };

    if (body !== undefined) {
      fetchOptions.body = JSON.stringify(body);
    }

    const response = await fetch(url, fetchOptions);
    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await parseErrorResponse(response);
      return buildErrorResponse(response.status, errorData);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    clearTimeout(timeoutId);

    if (isAbortError(error)) {
      logger.warn(`[${logContext}] Request timed out`);
      return createTimeoutResponse(timeoutMessage);
    }

    logger.error(`[${logContext}] Error proxying to backend:`, error);
    return handleFetchError(error);
  }
}

