import { NextRequest, NextResponse } from "next/server";

import { getBackendUrl, handleFetchError, parseErrorResponse } from "../../../../lib/api";
import { logger } from "../../../../lib/logger";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ run_id: string }> | { run_id: string } }
) {
  try {
    // Next.js 15+ uses async params, Next.js 14 uses sync params
    const resolvedParams = params instanceof Promise ? await params : params;
    const { run_id } = resolvedParams;
    
    // Validate run_id
    if (!run_id || run_id === 'undefined' || run_id === 'null') {
      logger.error("[Next.js API] Invalid run_id in route params:", run_id, "type:", typeof run_id);
      return NextResponse.json(
        { error: "Invalid run_id parameter", received: run_id },
        { status: 400 }
      );
    }

    // Add timeout to prevent hanging requests (60 seconds for run status checks)
    const controller = new AbortController();
    const timeoutId = globalThis.setTimeout(() => controller.abort(), 60000);
    
    try {
      const response = await fetch(
        `${getBackendUrl()}/api/run/${encodeURIComponent(run_id)}`,
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
      // Propagate backend error shape to the client, similar to /analyze/start
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
        logger.warn("Request to backend timed out or was aborted", run_id);
        return NextResponse.json(
          {
            error: "Request timeout",
            detail: "Backend request took too long. The analysis may still be running.",
          },
          { status: 504 }
        );
      }
      logger.error("Error proxying to backend:", error);
      return handleFetchError(error);
    }
  } catch (error) {
    logger.error("Error in run route:", error);
    return handleFetchError(error);
  }
}

