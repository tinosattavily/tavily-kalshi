"use client";

import React, { useRef, useCallback, useEffect, useState } from "react";

interface NeumorphicSliderProps {
  id: string;
  min: number;
  max: number;
  step?: number;
  value: number;
  onChange: (value: number) => void;
  disabled?: boolean;
}

export default function NeumorphicSlider({
  id,
  min,
  max,
  step = 1,
  value,
  onChange,
  disabled = false,
}: NeumorphicSliderProps): React.JSX.Element {
  const trackRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Calculate the percentage for the fill effect
  const percentage = ((value - min) / (max - min)) * 100;

  const calculateValue = useCallback((clientX: number) => {
    if (!trackRef.current || disabled) return;
    const rect = trackRef.current.getBoundingClientRect();
    const clickX = clientX - rect.left;
    const newPercentage = Math.max(0, Math.min(100, (clickX / rect.width) * 100));
    const rawValue = min + (newPercentage / 100) * (max - min);
    const steppedValue = Math.round(rawValue / step) * step;
    const clampedValue = Math.max(min, Math.min(max, steppedValue));
    onChange(clampedValue);
  }, [disabled, min, max, step, onChange]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (disabled) return;
    e.preventDefault();
    setIsDragging(true);
    calculateValue(e.clientX);
  }, [disabled, calculateValue]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging) return;
    calculateValue(e.clientX);
  }, [isDragging, calculateValue]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  return (
    <div className={`relative w-full ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}>
      {/* Hidden input for accessibility */}
      <input
        type="range"
        id={id}
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value, 10))}
        disabled={disabled}
        className="sr-only"
      />
      
      {/* Custom neumorphic track */}
      <div
        ref={trackRef}
        className="relative w-full h-2 rounded select-none"
        style={{
          backgroundColor: '#e5e7eb',
          boxShadow: '-2px -2px 4px white, 2px 2px 4px rgb(153, 161, 175)',
        }}
        onMouseDown={handleMouseDown}
      >
        {/* Fill */}
        <div
          className="absolute top-0 left-0 h-full rounded bg-emerald-800 pointer-events-none"
          style={{
            width: `${percentage}%`,
          }}
        />
        
        {/* Thumb */}
        <div
          className={`absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full pointer-events-none ${isDragging ? 'shadow-lg scale-110' : 'hover:shadow-lg'}`}
          style={{
            left: `calc(${percentage}% - 8px)`,
            backgroundColor: '#e5e7eb',
            boxShadow: '-2px -2px 4px white, 2px 2px 4px rgb(153, 161, 175)',
            transition: isDragging ? 'none' : 'box-shadow 0.2s, transform 0.1s',
          }}
        />
      </div>
    </div>
  );
}
