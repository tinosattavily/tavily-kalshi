import { NextRequest, NextResponse } from "next/server";

import { getBackendUrl, handleFetchError, parseErrorResponse, buildErrorResponse } from "../../../../lib/api";
import { logger } from "../../../../lib/logger";

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json();
    const backendUrl = getBackendUrl();

    logger.debug(`[analyze/start] Proxying to ${backendUrl}/api/analyze/start`);

    const response = await fetch(`${backendUrl}/api/analyze/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await parseErrorResponse(response);
      return buildErrorResponse(response.status, errorData);
    }

    const data = await response.json();

    if (!data.run_id && !data.error) {
      logger.error("[analyze/start] Missing run_id in backend response:", data);
    }

    return NextResponse.json(data);
  } catch (error) {
    logger.error("[analyze/start] Error proxying to backend:", error);
    return handleFetchError(error);
  }
}
