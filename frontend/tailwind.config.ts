import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "var(--ink)",
        "ink-soft": "var(--ink-soft)",
        "ink-mute": "var(--ink-mute)",
        line: "var(--line)",
        glass: "var(--glass)",
        "glass-strong": "var(--glass-strong)",
        "topbar-bg": "var(--topbar-bg)",
        "input-bg": "var(--input-bg)",
        "logo-bg": "var(--logo-bg)",
        ring: "var(--ring)",
        accent: "var(--accent)",
        "accent-soft": "var(--accent-soft)",
        "accent-on": "var(--accent-on)",
        yes: "var(--yes)",
        "yes-soft": "var(--yes-soft)",
        "yes-ink": "var(--yes-ink)",
        no: "var(--no)",
        "no-soft": "var(--no-soft)",
        "no-ink": "var(--no-ink)",
        "neu-track": "var(--neu-track)",
        "neu-thumb": "var(--neu-thumb)",
      },
      boxShadow: {
        "neu-raised": "var(--neu-raised)",
        "neu-inset": "var(--neu-inset)",
        soft: "var(--shadow)",
      },
      borderRadius: {
        DEFAULT: "var(--radius-sm)",
        lg: "var(--radius)",
      },
      fontFamily: {
        sans: ["var(--font-sans)"],
        mono: ["var(--font-mono)"],
      },
      backdropBlur: {
        glass: "var(--blur)",
      },
    },
  },
  plugins: [],
};

export default config;


