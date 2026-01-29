import type { Metadata } from "next";
import type { ReactNode } from "react";

import { Inter } from "next/font/google";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Tavily Polymarket Signals",
  description: "Dashboard for multi-agent Polymarket signals.",
};

interface RootLayoutProps {
  children: ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps): React.JSX.Element {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
