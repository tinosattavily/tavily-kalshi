import type { ReactNode } from "react";
import { Geist, Geist_Mono } from "next/font/google";

import "../app/globals.css";
import { Providers } from "../components/Providers";
import { getServerTheme } from "../lib/theme-cookie";

const geistSans = Geist({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-geist-sans",
});

const geistMono = Geist_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-geist-mono",
});

export const metadata = {
  title: "Prophily - Tavily Kalshi Signals",
  description: "Dashboard for multi-agent Kalshi market signals powered by Tavily.",
};

const themeBootstrap = `
(function(){
  try {
    var hasCookie = document.cookie.indexOf('prophily-theme=') !== -1;
    if (hasCookie) return;
    var dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.dataset.theme = dark ? 'obsidian' : 'atelier';
  } catch (_e) {}
})();
`;

export default async function RootLayout({ children }: { children: ReactNode }) {
  const stored = await getServerTheme();
  const initialTheme = stored ?? "atelier";

  return (
    <html lang="en" data-theme={initialTheme} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeBootstrap }} />
      </head>
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
