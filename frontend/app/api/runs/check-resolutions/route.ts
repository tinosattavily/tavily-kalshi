import { getBackendUrl, proxyBackendRequest } from "../../../../lib/api";

export async function POST() {
  return proxyBackendRequest({
    url: `${getBackendUrl()}/api/runs/check-resolutions`,
    method: "POST",
    timeoutMs: 60000, // Allow more time for resolution checks
    timeoutMessage: "Resolution check took too long.",
    logContext: "runs/check-resolutions",
  });
}
