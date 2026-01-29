import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      boxShadow: {
        'neumorph': '8px 8px 16px #d1d5db, -8px -8px 16px #ffffff',
        'neumorph-sm': '4px 4px 8px #d1d5db, -4px -4px 8px #ffffff',
        'neumorph-lg': '12px 12px 24px #d1d5db, -12px -12px 24px #ffffff',
        'neumorph-inset': 'inset 4px 4px 8px #d1d5db, inset -4px -4px 8px #ffffff',
      },
    },
  },
  plugins: [],
};

export default config;
