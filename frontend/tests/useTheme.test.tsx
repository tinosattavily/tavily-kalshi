import { act, renderHook } from "@testing-library/react";
import { useTheme } from "../hooks/useTheme";
import { THEME_COOKIE } from "../lib/theme-cookie";

function setHtmlTheme(value: string | null) {
  if (value === null) delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = value;
}

function clearCookie() {
  document.cookie = `${THEME_COOKIE}=; Max-Age=0; Path=/`;
}

beforeEach(() => {
  setHtmlTheme(null);
  clearCookie();
  try { window.localStorage?.clear(); } catch (_) { /* noop */ }
});

describe("useTheme", () => {
  it("returns the value of document.documentElement.dataset.theme on initial render", () => {
    setHtmlTheme("obsidian");
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe("obsidian");
  });

  it("defaults to 'atelier' when no data-theme is set", () => {
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe("atelier");
  });

  it("toggle() flips the data-theme attribute and writes a cookie", () => {
    setHtmlTheme("atelier");
    const { result } = renderHook(() => useTheme());

    act(() => result.current.toggle());

    expect(result.current.theme).toBe("obsidian");
    expect(document.documentElement.dataset.theme).toBe("obsidian");
    expect(document.cookie).toContain(`${THEME_COOKIE}=obsidian`);
  });

  it("setTheme writes the cookie and updates the attribute", () => {
    const { result } = renderHook(() => useTheme());
    act(() => result.current.setTheme("obsidian"));

    expect(document.documentElement.dataset.theme).toBe("obsidian");
    expect(document.cookie).toContain(`${THEME_COOKIE}=obsidian`);
  });

  it("after setTheme, system preference changes are ignored", () => {
    const originalMatchMedia = (window as Window & typeof globalThis).matchMedia;

    let mqlListener: ((e: MediaQueryListEvent) => void) | null = null;
    const matchMedia = jest.fn().mockImplementation((q: string) => ({
      matches: false,
      media: q,
      addEventListener: (_: string, cb: typeof mqlListener) => { mqlListener = cb; },
      removeEventListener: jest.fn(),
      addListener: jest.fn(),
      removeListener: jest.fn(),
      onchange: null,
      dispatchEvent: jest.fn(),
    }));
    Object.defineProperty(window, "matchMedia", { writable: true, configurable: true, value: matchMedia });

    try {
      const { result } = renderHook(() => useTheme());
      act(() => result.current.setTheme("atelier"));

      act(() => {
        if (mqlListener) mqlListener({ matches: true } as MediaQueryListEvent);
      });

      expect(result.current.theme).toBe("atelier");
    } finally {
      if (typeof originalMatchMedia === "undefined") {
        // jsdom default — restore the pre-test absence
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        delete (window as any).matchMedia;
      } else {
        Object.defineProperty(window, "matchMedia", { writable: true, configurable: true, value: originalMatchMedia });
      }
    }
  });
});
