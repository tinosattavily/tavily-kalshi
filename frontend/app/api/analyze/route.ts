import { NextRequest, NextResponse } from "next/server";

import { getBackendUrl, handleFetchError, parseErrorResponse } from "../../../lib/api";
import { logger } from "../../../lib/logger";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const response = await fetch(`${getBackendUrl()}/api/analyze/start`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

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
    return NextResponse.json(data);
  } catch (error) {
    logger.error("Error proxying to backend:", error);
    return handleFetchError(error);
  }
}

