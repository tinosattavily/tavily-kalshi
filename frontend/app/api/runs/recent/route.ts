import { NextRequest, NextResponse } from "next/server";

import { getBackendUrl, handleFetchError, parseErrorResponse } from "../../../../lib/api";
import { logger } from "../../../../lib/logger";

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = searchParams.get("limit") || "20";

    // Add timeout to prevent hanging requests (30 seconds)
    const controller = new AbortController();
    const timeoutId = globalThis.setTimeout(() => controller.abort(), 30000);
    
    try {
      const response = await fetch(
        `${getBackendUrl()}/api/runs/recent?limit=${encodeURIComponent(limit)}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
          signal: controller.signal,
        },
      );
      
      globalThis.clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await parseErrorResponse(response);
        return NextResponse.json(
          {
            error: `Backend error: ${response.status}`,
            detail:
              (errorData.detail as string) ||
              (errorData.error as string) ||
              (errorData.message as string) ||
              "Unknown error",
            details: errorData,
          },
          { status: response.status },
        );
      }

      const data = await response.json();
      return NextResponse.json(data);
    } catch (error) {
      globalThis.clearTimeout(timeoutId);
      // Handle abort/timeout errors gracefully
      if (error instanceof Error && (error.name === "AbortError" || error.message.includes("aborted"))) {
        logger.warn("Request to backend timed out or was aborted");
        return NextResponse.json(
          {
            error: "Request timeout",
            detail: "Backend request took too long.",
          },
          { status: 504 }
        );
      }
      logger.error("Error proxying to backend:", error);
      return handleFetchError(error);
    }
  } catch (error) {
    logger.error("Error in recent runs route:", error);
    return handleFetchError(error);
  }
}

