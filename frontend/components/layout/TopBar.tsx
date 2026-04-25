"use client";

import type { ReactNode } from "react";
import type { Signal } from "../../types/signal";
import SignalPill from "../analysis/SignalPill";
import ThemeToggle from "./ThemeToggle";

type Props = {
  urlInput: ReactNode;
  signal?: Signal | null;
};

export default function TopBar({ urlInput, signal }: Props) {
  return (
    <header
      className="flex items-center gap-5 px-7 border-b border-line bg-topbar-bg backdrop-blur-glass"
      style={{ height: 60 }}
    >
      {/* Logo */}
      <div className="flex items-center gap-2.5" style={{ width: 232 }}>
        <span
          className="grid place-items-center rounded-md bg-logo-bg shadow-neu-raised relative overflow-hidden"
          style={{ width: 30, height: 30 }}
        >
          <span
            className="rotate-45 rounded-sm"
            style={{ width: 14, height: 14, background: "var(--accent)" }}
          />
          <span
            className="absolute inset-0 rounded-md pointer-events-none"
            style={{ boxShadow: "inset 0 1px 0 var(--highlight)" }}
          />
        </span>
        <span className="text-lg font-semibold text-ink" style={{ letterSpacing: "-0.02em" }}>
          prophecy
          <span className="text-accent">.</span>
        </span>
      </div>

      {/* URL input centered */}
      <div className="flex-1 flex justify-center">
        <div className="w-full" style={{ maxWidth: 560 }}>
          {urlInput}
        </div>
      </div>

      {/* Signal pill (only when there's a signal) */}
      <SignalPill signal={signal ?? null} size="sm" />

      {/* Theme toggle */}
      <ThemeToggle />
    </header>
  );
}
