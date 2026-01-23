"use client";

import { ReactNode } from "react";
import { ToastProvider } from "./ui/Toast";
import { ErrorBoundary } from "./ui/ErrorBoundary";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary>
      <ToastProvider>{children}</ToastProvider>
    </ErrorBoundary>
  );
}
