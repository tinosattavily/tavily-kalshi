import type { ReactNode } from "react";
import { Geist, Geist_Mono } from "next/font/google";

import "../app/globals.css";
import { Providers } from "../components/Providers";

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

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" data-theme="atelier" suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
