"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import type { RecentRun } from "../components/layout/HistoryCard";

interface UseRecentSessionsOptions {
  refreshTrigger?: number;
}

interface UseRecentSessionsReturn {
  runs: RecentRun[];
  isLoading: boolean;
  error: string | null;
  fetchRecentRuns: () => Promise<void>;
}

export function useRecentSessions({
  refreshTrigger = 0,
}: UseRecentSessionsOptions = {}): UseRecentSessionsReturn {
  const [runs, setRuns] = useState<RecentRun[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchRecentRuns = useCallback(async () => {
    // Cancel any pending requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new AbortController for this request
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    setIsLoading(true);
    setError(null);

    // Add timeout to prevent hanging requests (30 seconds)
    const timeoutId = globalThis.setTimeout(() => {
      if (!abortController.signal.aborted) {
        abortController.abort();
      }
    }, 30000);

    try {
      const response = await fetch("/api/runs/recent?limit=20", {
        signal: abortController.signal,
      });

      globalThis.clearTimeout(timeoutId);

      // Check if request was aborted before processing response
      if (abortController.signal.aborted) {
        return;
      }

      if (!response.ok) {
        // Try to parse error response
        let errorData: {
          detail?: string;
          error?: string;
          message?: string;
        } = {};
        try {
          const text = await response.text();
          if (text) {
            errorData = JSON.parse(text) as typeof errorData;
          }
        } catch {
          errorData = { error: response.statusText || `HTTP ${response.status}` };
        }

        if (abortController.signal.aborted) {
          return;
        }

        throw new Error(
          errorData.detail || errorData.error || `Failed to fetch recent runs (${response.status})`
        );
      }

      const data = await response.json();

      if (!abortController.signal.aborted) {
        setRuns(data.runs || []);
      }
    } catch (err) {
      globalThis.clearTimeout(timeoutId);

      if (
        abortController.signal.aborted ||
        (err instanceof Error &&
          (err.name === "AbortError" ||
            err.message === "terminated" ||
            err.message.includes("aborted"))) ||
        (err instanceof globalThis.DOMException && err.name === "AbortError")
      ) {
        return;
      }

      if (!abortController.signal.aborted) {
        let errorMessage = "Failed to load recent sessions";
        if (err instanceof Error) {
          if (err.message === "terminated" || err.message.includes("aborted")) {
            errorMessage = "Request was cancelled";
          } else {
            errorMessage = err.message;
          }
        }
        setError(errorMessage);
        console.error("Error fetching recent runs:", err);
      }
    } finally {
      if (!abortController.signal.aborted) {
        setIsLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    fetchRecentRuns();
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [refreshTrigger, fetchRecentRuns]);

  return {
    runs,
    isLoading,
    error,
    fetchRecentRuns,
  };
}
