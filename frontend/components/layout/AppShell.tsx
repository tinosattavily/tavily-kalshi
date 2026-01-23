"use client";

import React, { ReactNode } from "react";
import GridBackground from "./GridBackground";
import TopNav from "./TopNav";

interface AppShellProps {
  /** Header for the left sidebar (row 2, col 1) */
  sidebarHeader: ReactNode;
  /** Content for the left sidebar cards (row 3, col 1) */
  sidebarContent: ReactNode;
  /** URL input bar (row 2, col 3) */
  urlInput: ReactNode;
  /** Header for the right config panel (row 2, col 5) */
  configHeader: ReactNode;
  /** Content for the right config panel (row 3, col 3) */
  configContent: ReactNode;
  /** Main content area - results (row 3, col 2) */
  children: ReactNode;
}

/**
 * Application shell layout with 3-row, 5-column grid structure.
 *
 * Layout (5 columns: 2fr | 2fr | 4fr | 2fr | 2fr):
 * - Row 1: Empty | Navigation (spans 3 cols) | Empty
 * - Row 2: Sidebar Header | spacer | URL Input | spacer | Config Header
 * - Row 3: Sidebar Cards | Main Content (spans 3 cols) | Config Settings
 */
export function AppShell({
  sidebarHeader,
  sidebarContent,
  urlInput,
  configHeader,
  configContent,
  children,
}: AppShellProps): React.JSX.Element {
  return (
    <section id="app-root" className="relative min-h-screen overflow-hidden text-neutral-900 z-10">
      <GridBackground />

      <div className="grid min-h-screen grid-cols-[2fr_2fr_4fr_2fr_2fr] grid-rows-[auto_auto_1fr]">
        {/* Row 1, Col 1 - Empty header cell */}
        <div className="border-y border-l border-neutral-300 bg-white/60 backdrop-blur-sm">
          <div className="h-10" />
        </div>

        {/* Row 1, Cols 2-4 - Navigation (spans 3 columns) */}
        <div className="col-span-3">
          <TopNav />
        </div>

        {/* Row 1, Col 5 - Empty header cell */}
        <div className="border-y border-r border-neutral-300 bg-white/60 backdrop-blur-sm">
          <div className="h-10" />
        </div>

        {/* Row 2, Col 1 - Sidebar Header */}
        {sidebarHeader}

        {/* Row 2, Col 2 - Left spacer */}
        <div className="border-b border-neutral-300 bg-white/60 backdrop-blur-sm" />

        {/* Row 2, Col 3 - URL Input */}
        <div className="border-x border-b border-neutral-300 bg-white/60 backdrop-blur-sm p-4">
          {urlInput}
        </div>

        {/* Row 2, Col 4 - Right spacer */}
        <div className="border-b border-neutral-300 bg-white/60 backdrop-blur-sm" />

        {/* Row 2, Col 5 - Config Header */}
        {configHeader}

        {/* Row 3, Col 1 - Sidebar Content */}
        {sidebarContent}

        {/* Row 3, Cols 2-4 - Main Content (spans 3 columns) */}
        <div className="col-span-3 border-x border-b border-neutral-300 bg-white/60 backdrop-blur-sm flex flex-col overflow-auto">
          {children}
        </div>

        {/* Row 3, Col 5 - Config Content */}
        {configContent}
      </div>
    </section>
  );
}
