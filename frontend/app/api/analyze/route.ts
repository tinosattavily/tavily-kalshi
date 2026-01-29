import { NextRequest } from "next/server";

import { getBackendUrl, handleFetchError, proxyBackendRequest } from "../../../lib/api";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    return proxyBackendRequest({
      url: `${getBackendUrl()}/api/analyze/start`,
      method: "POST",
      body,
      timeoutMs: 30000,
      timeoutMessage: "Backend request took too long.",
      logContext: "analyze",
    });
  } catch (error) {
    return handleFetchError(error);
  }
}
