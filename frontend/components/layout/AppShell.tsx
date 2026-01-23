"use client";

import React, { ReactNode } from "react";
import GridBackground from "./GridBackground";
import TopNav from "./TopNav";

interface AppShellProps {
  /** Content for the left sidebar (col 1) */
  sidebar: ReactNode;
  /** Main content area (col 2) */
  children: ReactNode;
  /** Content for the right panel (col 3) */
  rightPanel: ReactNode;
}

/**
 * Application shell layout with 3-column grid structure.
 *
 * Layout:
 * - Row 1: Navigation bar spanning middle column
 * - Row 2: Sidebar | Main Content | Right Panel
 */
export function AppShell({ sidebar, children, rightPanel }: AppShellProps): React.JSX.Element {
  return (
    <section id="app-root" className="relative min-h-screen overflow-hidden bg-white text-neutral-900">
      <GridBackground />

      <div
        id="app-grid"
        className="grid min-h-screen w-full grid-rows-[auto,1fr] grid-cols-[minmax(0,2fr)_minmax(0,8fr)_minmax(0,2fr)]"
      >
        {/* Row 1, Col 1 - Empty header cell */}
        <div className="border-y border-l border-neutral-300 bg-white/90">
          <div className="h-10" />
        </div>

        {/* Row 1, Col 2 - Navigation */}
        <TopNav />

        {/* Row 1, Col 3 - Empty header cell */}
        <div className="border-y border-r border-neutral-300 bg-white/90">
          <div className="h-10" />
        </div>

        {/* Row 2, Col 1 - Sidebar */}
        {sidebar}

        {/* Row 2, Col 2 - Main Content */}
        <div className="border-x border-neutral-300 bg-white/90 flex flex-col">
          {children}
        </div>

        {/* Row 2, Col 3 - Right Panel */}
        {rightPanel}
      </div>
    </section>
  );
}
