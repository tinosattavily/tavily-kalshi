import React from "react";

/**
 * Page-level decorative background. The active theme's --bg-image
 * (set in globals.css) renders on <body>; this component layers a
 * subtle hairline grid on top using --line for the stroke color so
 * it works in both Atelier and Obsidian themes.
 */
export default function GridBackground() {
  const stroke = "var(--line)";
  const svg = `<svg width="120" height="120" xmlns="http://www.w3.org/2000/svg"><path d="M120 0H0v120" fill="none" stroke="${stroke}" stroke-width="1"/></svg>`;
  const url = `url("data:image/svg+xml;utf8,${encodeURIComponent(svg)}")`;

  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 z-0"
      style={{
        backgroundImage: url,
        backgroundSize: "120px 120px",
      }}
    />
  );
}

