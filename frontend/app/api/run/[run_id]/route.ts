import { NextRequest, NextResponse } from "next/server";

import { getBackendUrl, proxyBackendRequest } from "../../../../lib/api";
import { logger } from "../../../../lib/logger";

type RouteParams = { params: Promise<{ run_id: string }> | { run_id: string } };

export async function GET(
  _request: NextRequest,
  { params }: RouteParams,
): Promise<NextResponse> {
  const resolvedParams = params instanceof Promise ? await params : params;
  const { run_id } = resolvedParams;

  if (!run_id || run_id === "undefined" || run_id === "null") {
    logger.error("[run/[run_id]] Invalid run_id:", run_id);
    return NextResponse.json(
      { error: "Invalid run_id parameter", received: run_id },
      { status: 400 },
    );
  }

  return proxyBackendRequest({
    url: `${getBackendUrl()}/api/run/${encodeURIComponent(run_id)}`,
    timeoutMs: 60000,
    timeoutMessage: "Backend request took too long. The analysis may still be running.",
    logContext: `run/${run_id}`,
  });
}
