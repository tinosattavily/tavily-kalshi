/**
 * Client-safe theme constants. The server-side cookie reader lives in
 * `theme-cookie.ts` and should not be imported from client components —
 * importing this file is safe in either environment.
 */

export type Theme = "atelier" | "obsidian";

export const THEME_COOKIE = "prophily-theme";
