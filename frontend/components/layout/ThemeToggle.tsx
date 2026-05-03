"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "../../hooks/useTheme";

export default function ThemeToggle() {
  const { theme, toggle } = useTheme();

  // Avoid hydration mismatch: don't read theme until after client mount,
  // since the server has no way of knowing what the client's initial dataset
  // theme is when the html data-theme is bootstrapped from a cookie.
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const effectiveTheme = mounted ? theme : "atelier";
  const Icon = effectiveTheme === "atelier" ? Moon : Sun;
  const label =
    effectiveTheme === "atelier"
      ? "Switch to Obsidian theme"
      : "Switch to Atelier theme";

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={label}
      title={label}
      className="grid place-items-center w-8 h-8 rounded border border-ring bg-glass-strong text-ink-soft shadow-neu-raised hover:-translate-y-px transition-transform"
      suppressHydrationWarning
    >
      <Icon size={14} />
    </button>
  );
}
