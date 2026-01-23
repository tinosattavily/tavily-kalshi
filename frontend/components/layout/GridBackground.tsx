import React from "react";

export default function GridAndNoise() {
  return (
    <>
      <div className="pointer-events-none absolute inset-0 -z-10 bg-grid opacity-40" />
      <div className="pointer-events-none absolute inset-0 -z-10 bg-noise opacity-20" />
    </>
  );
}


