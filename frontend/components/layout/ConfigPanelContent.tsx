"use client";

import React, { useState } from "react";
import { Zap } from "lucide-react";

export interface AnalysisConfiguration {
  useTavilyPromptAgent: boolean;
  useNewsSummaryAgent: boolean;
  maxArticles: number;
  maxArticlesPerQuery: number;
  minConfidence: "low" | "medium" | "high";
  enableSentimentAnalysis: boolean;
}

interface ConfigPanelContentProps {
  config: AnalysisConfiguration;
  onChange: (config: AnalysisConfiguration) => void;
  isSubmitting?: boolean;
  onSubmit?: () => void;
}

interface NeuromorphicToggleProps {
  id: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}

function NeuromorphicToggle({ id, checked, onChange, disabled = false }: NeuromorphicToggleProps) {
  return (
    <button
      id={id}
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => !disabled && onChange(!checked)}
      disabled={disabled}
      className="relative rounded-full p-0.5 cursor-pointer transition-colors disabled:opacity-50"
      style={{
        width: 40,
        height: 22,
        background: checked ? "var(--accent)" : "var(--neu-track)",
        boxShadow: checked
          ? "inset 0 1px 2px var(--accent-shadow)"
          : "var(--neu-inset)",
      }}
    >
      <span
        className="block rounded-full"
        style={{
          width: 18,
          height: 18,
          background: "var(--neu-thumb)",
          boxShadow: "var(--neu-raised)",
          transform: `translateX(${checked ? 18 : 0}px)`,
          transition: "transform .2s",
        }}
      />
    </button>
  );
}

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="font-mono uppercase font-semibold text-ink-mute"
      style={{ padding: "12px 4px 8px", fontSize: 9, letterSpacing: 1.4 }}
    >
      {children}
    </div>
  );
}

function SegChip({
  options,
  value,
  onSelect,
}: {
  options: string[];
  value: string;
  onSelect: (v: string) => void;
}) {
  return (
    <div className="inline-flex gap-0.5 p-0.5 rounded bg-neu-track shadow-neu-inset border border-ring">
      {options.map((o) => {
        const on = o === value;
        return (
          <button
            key={o}
            type="button"
            onClick={() => onSelect(o)}
            className={
              "font-mono text-[10px] px-2 py-0.5 rounded " +
              (on
                ? "bg-glass-strong shadow-neu-raised text-ink"
                : "text-ink-mute hover:text-ink-soft")
            }
          >
            {o}
          </button>
        );
      })}
    </div>
  );
}

function ConfigRow({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-2.5 px-1 py-2 min-h-9">
      <div className="flex-1 min-w-0">
        <div className="text-[12px] text-ink font-medium">{label}</div>
        {hint && <div className="text-[10.5px] text-ink-mute mt-0.5">{hint}</div>}
      </div>
      {children}
    </div>
  );
}

export default function ConfigPanelContent({
  config,
  onChange,
  isSubmitting = false,
  onSubmit,
}: ConfigPanelContentProps): React.JSX.Element {
  const updateConfig = <K extends keyof AnalysisConfiguration>(
    key: K,
    value: AnalysisConfiguration[K]
  ): void => {
    onChange({ ...config, [key]: value });
  };

  // Decorative seg-chips not yet wired to AnalysisConfiguration; keep as local UI state.
  const [timeWindow, setTimeWindow] = useState<string>("7d");
  const [bias, setBias] = useState<string>("calib");

  return (
    <div className="flex flex-col h-full overflow-auto px-3 pb-2">
      {/* AGENTS */}
      <SectionHeader>Agents</SectionHeader>
      <ConfigRow
        label="Tavily prompt agent"
        hint="Generate optimized queries with AI."
      >
        <NeuromorphicToggle
          id="tavily-prompt-toggle"
          checked={config.useTavilyPromptAgent}
          onChange={(checked) => updateConfig("useTavilyPromptAgent", checked)}
          disabled={isSubmitting}
        />
      </ConfigRow>
      <ConfigRow
        label="News summarizer"
        hint="AI-powered article summaries."
      >
        <NeuromorphicToggle
          id="news-summary-toggle"
          checked={config.useNewsSummaryAgent}
          onChange={(checked) => updateConfig("useNewsSummaryAgent", checked)}
          disabled={isSubmitting}
        />
      </ConfigRow>
      <ConfigRow
        label="Sentiment analysis"
        hint="Bullish / bearish / neutral classification."
      >
        <NeuromorphicToggle
          id="sentiment-toggle"
          checked={config.enableSentimentAnalysis}
          onChange={(checked) => updateConfig("enableSentimentAnalysis", checked)}
          disabled={isSubmitting}
        />
      </ConfigRow>

      {/* RETRIEVAL */}
      <SectionHeader>Retrieval</SectionHeader>
      <div className="rounded p-3 bg-glass-strong border border-ring shadow-neu-inset mb-2">
        <div className="flex items-baseline mb-2">
          <span className="text-[12px] text-ink-soft">Max articles</span>
          <span className="flex-1" />
          <span className="font-mono text-[14px] font-semibold text-ink">
            {config.maxArticles}
          </span>
        </div>
        <input
          type="range"
          id="max-articles"
          min="5"
          max="30"
          step="1"
          value={config.maxArticles}
          onChange={(e) => updateConfig("maxArticles", parseInt(e.target.value, 10))}
          disabled={isSubmitting}
          className="w-full h-2 bg-neu-track rounded-lg appearance-none cursor-pointer accent-accent min-w-0"
        />
        <div className="flex justify-between mt-1.5 font-mono text-[9px] text-ink-mute">
          <span>5</span>
          <span>30</span>
        </div>
      </div>
      <div className="rounded p-3 bg-glass-strong border border-ring shadow-neu-inset mb-2">
        <div className="flex items-baseline mb-2">
          <span className="text-[12px] text-ink-soft">Max per query</span>
          <span className="flex-1" />
          <span className="font-mono text-[14px] font-semibold text-ink">
            {config.maxArticlesPerQuery}
          </span>
        </div>
        <input
          type="range"
          id="max-articles-per-query"
          min="5"
          max="12"
          step="1"
          value={config.maxArticlesPerQuery}
          onChange={(e) =>
            updateConfig("maxArticlesPerQuery", parseInt(e.target.value, 10))
          }
          disabled={isSubmitting}
          className="w-full h-2 bg-neu-track rounded-lg appearance-none cursor-pointer accent-accent min-w-0"
        />
        <div className="flex justify-between mt-1.5 font-mono text-[9px] text-ink-mute">
          <span>5</span>
          <span>12</span>
        </div>
      </div>
      <ConfigRow label="Time window" hint="Recency filter for retrieval.">
        <SegChip
          options={["24h", "7d", "30d"]}
          value={timeWindow}
          onSelect={setTimeWindow}
        />
      </ConfigRow>

      {/* MODEL */}
      <SectionHeader>Model</SectionHeader>
      <ConfigRow label="Bias" hint="Calibrated or contrarian stance.">
        <SegChip
          options={["calib", "contrarian"]}
          value={bias}
          onSelect={setBias}
        />
      </ConfigRow>
      <ConfigRow label="Confidence floor" hint="Minimum confidence for signals.">
        <SegChip
          options={["low", "medium", "high"]}
          value={config.minConfidence}
          onSelect={(v) =>
            updateConfig("minConfidence", v as "low" | "medium" | "high")
          }
        />
      </ConfigRow>

      {/* Re-run CTA */}
      {onSubmit && (
        <div className="px-0 pt-3 pb-3 border-t border-line mt-3">
          <button
            type="button"
            onClick={onSubmit}
            disabled={isSubmitting}
            className="w-full h-10 rounded inline-flex items-center justify-center gap-2 font-sans text-[13px] font-semibold disabled:opacity-50"
            style={{
              background: "var(--accent)",
              color: "var(--accent-on)",
              letterSpacing: "-0.01em",
              boxShadow: "var(--neu-raised)",
            }}
          >
            <Zap size={13} strokeWidth={2.5} />
            Re-run analysis
          </button>
        </div>
      )}
    </div>
  );
}
