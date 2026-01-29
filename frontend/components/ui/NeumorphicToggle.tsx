"use client";

import React from "react";

interface NeumorphicToggleProps {
  id: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}

export default function NeumorphicToggle({
  id,
  checked,
  onChange,
  disabled = false,
}: NeumorphicToggleProps): React.JSX.Element {
  return (
    <label
      htmlFor={id}
      className={`relative inline-flex items-center cursor-pointer ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
    >
      <input
        type="checkbox"
        id={id}
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        disabled={disabled}
        className="sr-only peer"
      />
      {/* Toggle track with neumorphic shadows */}
      <div
        className="
          relative isolate h-[22px] w-[44px] rounded-[11px] overflow-hidden bg-[#ecf0f3]
          shadow-[inset_3px_3px_3px_0px_#d1d9e6,inset_-3px_-3px_3px_0px_#ffffff,-4px_-2px_4px_0px_#ffffff,4px_2px_6px_0px_#d1d9e6]
        "
      >
        {/* Sliding indicator/knob */}
        <div
          className={`
            h-full w-[200%] rounded-[11px]
            shadow-[-4px_-2px_4px_0px_#ffffff,4px_2px_6px_0px_#d1d9e6]
            transition-all duration-[400ms] ease-[cubic-bezier(0.85,0.05,0.18,1.35)]
            ${checked ? "translate-x-[25%] bg-emerald-800" : "translate-x-[-75%] bg-[#ecf0f3]"}
          `}
        />
      </div>
    </label>
  );
}
