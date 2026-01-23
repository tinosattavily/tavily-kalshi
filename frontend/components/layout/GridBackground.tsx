import React from "react";

export default function GridAndNoise() {
  return (
    <>
      {/* Background image */}
      <div
        className="pointer-events-none fixed inset-0 z-0 bg-cover bg-center bg-no-repeat"
        style={{
          backgroundImage: "url('/tavily_landscapes_edited_11.webp')",
          opacity: 0.7,
        }}
      />
      <div className="pointer-events-none fixed inset-0 z-0 bg-grid opacity-40" />
      <div className="pointer-events-none fixed inset-0 z-0 bg-noise opacity-20" />
    </>
  );
}


