import type { ReactNode } from "react";
import { Inter } from "next/font/google";

import "../app/globals.css";
import { Providers } from "../components/Providers";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
});

export const metadata = {
  title: "Prophily - Tavily Kalshi Signals",
  description: "Dashboard for multi-agent Kalshi market signals powered by Tavily.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}


