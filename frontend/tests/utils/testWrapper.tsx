import React, { ReactNode } from "react";
import { render } from "@testing-library/react";
import { ToastProvider } from "../../components/ui/Toast";

/**
 * Wraps components with necessary providers for testing
 */
export function TestWrapper({ children }: { children: ReactNode }) {
  return <ToastProvider>{children}</ToastProvider>;
}

/**
 * Custom render wrapper that includes all providers
 */
export function renderWithProviders(ui: React.ReactElement) {
  return render(ui, { wrapper: TestWrapper });
}
