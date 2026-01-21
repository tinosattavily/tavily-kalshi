import { NextRequest, NextResponse } from "next/server";

import { getBackendUrl, handleFetchError, parseErrorResponse } from "../../../../lib/api";
import { logger } from "../../../../lib/logger";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Add timeout to prevent hanging requests (10 seconds for starting analysis)
    const controller = new AbortController();
    const timeoutId = globalThis.setTimeout(() => controller.abort(), 10000);
    
    try {
      const response = await fetch(`${getBackendUrl()}/api/analyze/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      
      globalThis.clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await parseErrorResponse(response);
      return NextResponse.json(
        { 
          error: `Backend error: ${response.status}`, 
          detail: errorData.detail || errorData.error || errorData.message || "Unknown error",
          details: errorData 
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    
    // Validate response has run_id
    if (!data.run_id) {
      logger.error("[Next.js API] Missing run_id in backend response:", data);
    }
    
      return NextResponse.json(data);
    } catch (error) {
      globalThis.clearTimeout(timeoutId);
      // Handle abort/timeout errors gracefully
      if (error instanceof Error && (error.name === "AbortError" || error.message.includes("aborted"))) {
        logger.warn("Request to backend timed out or was aborted");
        return NextResponse.json(
          {
            error: "Request timeout",
            detail: "Backend request took too long to start analysis.",
          },
          { status: 504 }
        );
      }
      logger.error("Error proxying to backend:", error);
      return handleFetchError(error);
    }
  } catch (error) {
    logger.error("Error in analyze start route:", error);
    return handleFetchError(error);
  }
}

