"use client";

import { useCallback, useEffect, useState } from "react";
import { THEME_COOKIE, type Theme } from "../lib/theme-cookie";

const COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 365;
const USER_OVERRIDE_FLAG = "prophily-theme-explicit";

function readDatasetTheme(): Theme {
  if (typeof document === "undefined") return "atelier";
  const v = document.documentElement.dataset.theme;
  return v === "obsidian" ? "obsidian" : "atelier";
}

function writeCookie(theme: Theme) {
  document.cookie = `${THEME_COOKIE}=${theme}; Path=/; Max-Age=${COOKIE_MAX_AGE_SECONDS}; SameSite=Lax`;
}

function applyTheme(theme: Theme) {
  document.documentElement.dataset.theme = theme;
}

export function useTheme(): {
  theme: Theme;
  setTheme: (t: Theme) => void;
  toggle: () => void;
} {
  const [theme, setThemeState] = useState<Theme>(readDatasetTheme);

  const setTheme = useCallback((next: Theme) => {
    applyTheme(next);
    writeCookie(next);
    try {
      window.localStorage?.setItem(USER_OVERRIDE_FLAG, "1");
    } catch (_e) {
      // localStorage may be unavailable; cookie is still authoritative.
    }
    setThemeState(next);
  }, []);

  const toggle = useCallback(() => {
    setThemeState((prev) => {
      const next: Theme = prev === "atelier" ? "obsidian" : "atelier";
      applyTheme(next);
      writeCookie(next);
      try {
        window.localStorage?.setItem(USER_OVERRIDE_FLAG, "1");
      } catch (_e) {
        // localStorage may be unavailable; cookie is still authoritative.
      }
      return next;
    });
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (typeof window.matchMedia !== "function") return;

    const hasUserOverride = () => {
      try {
        return window.localStorage?.getItem(USER_OVERRIDE_FLAG) === "1";
      } catch (_e) {
        return false;
      }
    };

    if (hasUserOverride()) return;

    const mql = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = (e: MediaQueryListEvent) => {
      if (hasUserOverride()) return;
      const next: Theme = e.matches ? "obsidian" : "atelier";
      applyTheme(next);
      setThemeState(next);
    };
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  return { theme, setTheme, toggle };
}
