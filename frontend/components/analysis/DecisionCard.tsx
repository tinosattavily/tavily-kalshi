import React from "react";

type Decision = {
  action?: string;
  side?: string;
  edge_pct?: number;
  toy_kelly_fraction?: number;
  notes?: string;
};

// Also accept signal for recommended_action and recommended_size_fraction
type Signal = {
  recommended_action?: string;
  recommended_size_fraction?: number;
  edge_pct?: number;
  confidence_level?: string;
};

export default function DecisionCard({ 
  decision, 
  signal 
}: { 
  decision?: Decision;
  signal?: Signal;
}) {
  // Use signal fields if available, fallback to decision
  const action = signal?.recommended_action 
    ? signal.recommended_action.replace(/_/g, " ").toUpperCase()
    : (decision?.action || "HOLD").replace(/_/g, " ").toUpperCase();
  const sizeFraction = signal?.recommended_size_fraction ?? decision?.toy_kelly_fraction;
  const edge = signal?.edge_pct ?? decision?.edge_pct;
  const confidence = signal?.confidence_level;
  const notes = decision?.notes;
  const side = decision?.side;
  
  if (!decision && !signal) return null;
  if (decision && Object.keys(decision).length === 0 && (!signal || Object.keys(signal).length === 0)) return null;
  if (!decision && signal && Object.keys(signal).length === 0) return null;
  
  return (
    <div
      id="decision-card"
      className="mb-4 rounded-2xl border border-white bg-white/20 shadow-[0_4px_30px_rgba(0,0,0,0.1)] backdrop-blur-[11.3px] p-4"
      style={{ WebkitBackdropFilter: "blur(11.3px)" }}
    >
      <h4 className="text-sm font-medium text-neutral-800 mb-2">Decision</h4>
      <div className="text-sm">
        <p className="font-semibold text-lg mb-2">
          {action}
          {edge !== undefined && (
            <span className="ml-2 text-base font-normal">
              (Edge: {(edge * 100).toFixed(2)}%)
            </span>
          )}
        </p>
        {sizeFraction !== undefined && sizeFraction > 0 && (
          <p className="text-neutral-700 mb-1">
            <span className="font-medium">Position Size:</span> {(sizeFraction * 100).toFixed(1)}% of capital
          </p>
        )}
        {side && (
          <p className="text-neutral-600 text-xs mb-1">
            <span className="font-medium">Side:</span> {side}
          </p>
        )}
        {confidence && (
          <p className="text-neutral-600 text-xs mb-1">
            <span className="font-medium">Confidence:</span> {confidence.toUpperCase()}
          </p>
        )}
        {notes && (
          <p className="text-neutral-700 italic mt-2 text-xs">{notes}</p>
        )}
      </div>
    </div>
  );
}


