import { cookies } from "next/headers";

export type Theme = "atelier" | "obsidian";
export const THEME_COOKIE = "prophily-theme";

/**
 * Read the theme cookie on the server. Returns null when unset or invalid
 * so the caller can decide on a default.
 */
export async function getServerTheme(): Promise<Theme | null> {
  const store = await cookies();
  const value = store.get(THEME_COOKIE)?.value;
  return value === "atelier" || value === "obsidian" ? value : null;
}
