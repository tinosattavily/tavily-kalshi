/**
 * Shared API utilities for Next.js API routes.
 */

import { NextResponse } from "next/server";

/**
 * Get the backend URL from environment variables or default to Elastic Beanstalk.
 * Production uses Elastic Beanstalk, development uses localhost.
 */
export function getBackendUrl(): string {
  // Use BACKEND_URL environment variable if set (allows override)
  if (process.env.BACKEND_URL) {
    return process.env.BACKEND_URL;
  }
  
  // Production: Use Elastic Beanstalk backend
  // Development: Use localhost for local development
  const isDevelopment = process.env.NODE_ENV === "development";
  
  if (isDevelopment) {
    return "http://localhost:8000";
  }
  
  // Production default: Elastic Beanstalk backend
  return "https://tavily-backend-env.eba-jv6q9hd7.us-east-1.elasticbeanstalk.com";
}


/**
 * Handle fetch errors and return appropriate NextResponse.
 */
export function handleFetchError(error: unknown): NextResponse {
  const errorMessage = error instanceof Error ? error.message : String(error);
  return NextResponse.json(
    { 
      error: "Failed to connect to backend", 
      detail: errorMessage 
    },
    { status: 500 }
  );
}

/**
 * Parse error response from backend.
 * Attempts to extract error details from various response formats.
 */
export async function parseErrorResponse(response: Response): Promise<Record<string, unknown>> {
  try {
    return (await response.json()) as Record<string, unknown>;
  } catch {
    const errorText = await response.text();
    return { 
      detail: errorText || `Backend error: ${response.status}` 
    };
  }
}

