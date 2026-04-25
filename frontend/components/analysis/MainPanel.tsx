"use client";

import { BarChart3, FileText, Newspaper } from "lucide-react";
import { useState, type ReactNode } from "react";

type Tab = "news" | "summary" | "thesis";

type Props = {
  newsCount?: number;
  newsTab: ReactNode;
  summaryTab: ReactNode;
  thesisTab: ReactNode;
};

export default function MainPanel({ newsCount, newsTab, summaryTab, thesisTab }: Props) {
  const [tab, setTab] = useState<Tab>("thesis");

  const items: Array<{ id: Tab; label: string; Icon: typeof Newspaper; count?: number; accent?: boolean }> = [
    { id: "news", label: "News", Icon: Newspaper, count: newsCount },
    { id: "summary", label: "Summary", Icon: FileText },
    { id: "thesis", label: "Thesis", Icon: BarChart3, accent: true },
  ];

  const body =
    tab === "news" ? newsTab : tab === "summary" ? summaryTab : thesisTab;

  return (
    <div className="flex flex-col gap-3.5 min-w-0">
      <div
        className="self-start inline-flex gap-1 p-1 rounded border border-ring bg-neu-track shadow-neu-inset"
      >
        {items.map(({ id, label, Icon, count, accent }) => {
          const on = tab === id;
          return (
            <button
              key={id}
              type="button"
              onClick={() => setTab(id)}
              className={
                "flex items-center gap-2 px-3.5 py-1.5 rounded font-sans text-[12.5px] font-medium transition-colors " +
                (on
                  ? `${accent ? "text-accent" : "text-ink"} bg-glass-strong shadow-neu-raised`
                  : "text-ink-mute")
              }
            >
              <Icon size={12} />
              {label}
              {typeof count === "number" && (
                <span
                  className={
                    "font-mono text-[10px] text-ink-mute px-1.5 py-px rounded " +
                    (on ? "bg-neu-track" : "")
                  }
                >
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>
      <div className="flex-1 overflow-auto min-h-0">{body}</div>
    </div>
  );
}
