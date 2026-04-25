"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "../../hooks/useTheme";

export default function ThemeToggle() {
  const { theme, toggle } = useTheme();
  const Icon = theme === "atelier" ? Moon : Sun;
  const label = theme === "atelier" ? "Switch to Obsidian theme" : "Switch to Atelier theme";

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={label}
      title={label}
      className="grid place-items-center w-8 h-8 rounded border border-ring bg-glass-strong text-ink-soft shadow-neu-raised hover:-translate-y-px transition-transform"
    >
      <Icon size={14} />
    </button>
  );
}
