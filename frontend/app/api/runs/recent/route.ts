import { NextRequest } from "next/server";

import { getBackendUrl, proxyBackendRequest } from "../../../../lib/api";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const limit = searchParams.get("limit") || "20";

  return proxyBackendRequest({
    url: `${getBackendUrl()}/api/runs/recent?limit=${encodeURIComponent(limit)}`,
    timeoutMs: 30000,
    timeoutMessage: "Backend request took too long.",
    logContext: "runs/recent",
  });
}
