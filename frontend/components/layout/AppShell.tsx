"use client";

import React, { ReactNode } from "react";
import GridBackground from "./GridBackground";
import TopBar from "./TopBar";
import type { Signal } from "../../types/signal";

interface AppShellProps {
  /** URL input node — rendered centered in TopBar */
  urlInput: ReactNode;
  /** Signal pill — rendered top-right of TopBar; null hides the pill */
  signal?: Signal | null;
  /** Left column glass card (sessions list) */
  sessions: ReactNode;
  /** Center column main panel (snapshot + tabs + body) */
  main: ReactNode;
  /** Right column glass card (configuration) */
  config: ReactNode;
}

/**
 * Application shell layout — single top bar + 3-column body.
 *
 * Layout:
 * - Row 1: TopBar (60 px)
 * - Row 2: Sessions (260 px) | Main (1fr) | Config (320 px)
 */
export function AppShell({ urlInput, signal, sessions, main, config }: AppShellProps): React.JSX.Element {
  return (
    <section
      id="app-root"
      className="relative min-h-screen overflow-x-auto z-10 text-ink"
    >
      <GridBackground />

      <TopBar urlInput={urlInput} signal={signal} />

      <div
        className="grid gap-5"
        style={{
          gridTemplateColumns: "260px minmax(0, 1fr) 320px",
          padding: "20px 28px 28px",
          minWidth: 1280,
        }}
      >
        {/* Left — sessions */}
        <aside className="rounded-lg bg-glass shadow-soft border border-ring backdrop-blur-glass overflow-hidden">
          {sessions}
        </aside>

        {/* Center — main */}
        <section className="min-w-0 flex flex-col gap-4">{main}</section>

        {/* Right — config */}
        <aside className="rounded-lg bg-glass shadow-soft border border-ring backdrop-blur-glass overflow-hidden flex flex-col">
          {config}
        </aside>
      </div>
    </section>
  );
}
