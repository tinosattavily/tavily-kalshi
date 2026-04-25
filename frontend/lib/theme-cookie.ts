import { cookies } from "next/headers";
import { THEME_COOKIE, type Theme } from "./theme";

export { THEME_COOKIE };
export type { Theme };

/**
 * Read the theme cookie on the server. Returns null when unset or invalid
 * so the caller can decide on a default. Server-only — do not import from
 * a client component (use `lib/theme` for shared constants instead).
 */
export async function getServerTheme(): Promise<Theme | null> {
  const store = await cookies();
  const value = store.get(THEME_COOKIE)?.value;
  return value === "atelier" || value === "obsidian" ? value : null;
}
