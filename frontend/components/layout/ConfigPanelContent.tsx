"use client";

import React from "react";

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
}

interface NeuromorphicToggleProps {
  id: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}

function NeuromorphicToggle({ id, checked, onChange, disabled = false }: NeuromorphicToggleProps) {
  return (
    <label className="relative inline-flex items-center cursor-pointer flex-shrink-0">
      <input
        type="checkbox"
        id={id}
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        disabled={disabled}
        className="sr-only peer"
      />
      {/* Toggle track */}
      <div
        className="relative overflow-hidden"
        style={{
          width: "40px",
          height: "20px",
          borderRadius: "10px",
          boxShadow: "-4px -2px 4px 0px #ffffff, 4px 2px 6px 0px #d1d9e6, 2px 2px 2px 0px #d1d9e6 inset, -2px -2px 2px 0px #ffffff inset",
        }}
      >
        {/* Sliding indicator */}
        <div
          className="h-full"
          style={{
            width: "200%",
            background: checked ? "#86efac" : "#ecf0f3",
            borderRadius: "10px",
            transform: checked ? "translate3d(25%, 0, 0)" : "translate3d(-75%, 0, 0)",
            transition: "transform 0.4s cubic-bezier(0.85, 0.05, 0.18, 1.35), background 0.4s ease",
            boxShadow: "-4px -2px 4px 0px #ffffff, 4px 2px 6px 0px #d1d9e6",
          }}
        />
      </div>
    </label>
  );
}

export default function ConfigPanelContent({
  config,
  onChange,
  isSubmitting = false,
}: ConfigPanelContentProps): React.JSX.Element {
  const updateConfig = <K extends keyof AnalysisConfiguration>(
    key: K,
    value: AnalysisConfiguration[K]
  ): void => {
    onChange({ ...config, [key]: value });
  };

  return (
    <div className="h-full flex flex-col bg-white/60 backdrop-blur-sm border-r border-b border-neutral-300">
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Agent Toggles Section */}
        <section>
          <h3 className="text-sm font-semibold text-neutral-700 mb-3">Agent Settings</h3>
          <div className="space-y-3">
            {/* Tavily Prompt Agent Toggle */}
            <div className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg border border-neutral-200 min-w-0 overflow-hidden gap-3">
              <div className="flex-1 min-w-0">
                <label
                  htmlFor="tavily-prompt-toggle"
                  className="text-sm font-medium text-[#394a56] cursor-pointer block break-words"
                >
                  Use Tavily Prompt Agent
                </label>
                <p className="text-xs text-neutral-500 mt-1 break-words overflow-hidden">
                  Generate optimized queries with AI. Disable to use fallback queries.
                </p>
              </div>
              <NeuromorphicToggle
                id="tavily-prompt-toggle"
                checked={config.useTavilyPromptAgent}
                onChange={(checked) => updateConfig("useTavilyPromptAgent", checked)}
                disabled={isSubmitting}
              />
            </div>

            {/* News Summary Agent Toggle */}
            <div className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg border border-neutral-200 min-w-0 overflow-hidden gap-3">
              <div className="flex-1 min-w-0">
                <label
                  htmlFor="news-summary-toggle"
                  className="text-sm font-medium text-[#394a56] cursor-pointer block break-words"
                >
                  Use News Summary Agent
                </label>
                <p className="text-xs text-neutral-500 mt-1 break-words overflow-hidden">
                  Generate AI-powered summaries. Disable to use fallback summaries.
                </p>
              </div>
              <NeuromorphicToggle
                id="news-summary-toggle"
                checked={config.useNewsSummaryAgent}
                onChange={(checked) => updateConfig("useNewsSummaryAgent", checked)}
                disabled={isSubmitting}
              />
            </div>

            {/* Sentiment Analysis Toggle */}
            <div className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg border border-neutral-200 min-w-0 overflow-hidden gap-3">
              <div className="flex-1 min-w-0">
                <label
                  htmlFor="sentiment-toggle"
                  className="text-sm font-medium text-[#394a56] cursor-pointer block break-words"
                >
                  Enable Sentiment Analysis
                </label>
                <p className="text-xs text-neutral-500 mt-1 break-words overflow-hidden">
                  Analyze article sentiment (bullish/bearish/neutral).
                </p>
              </div>
              <NeuromorphicToggle
                id="sentiment-toggle"
                checked={config.enableSentimentAnalysis}
                onChange={(checked) => updateConfig("enableSentimentAnalysis", checked)}
                disabled={isSubmitting}
              />
            </div>
          </div>
        </section>

        {/* Article Limits Section */}
        <section>
          <h3 className="text-sm font-semibold text-neutral-700 mb-3">Article Limits</h3>
          <div className="space-y-4">
            {/* Max Articles */}
            <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200 overflow-hidden min-w-0">
              <label
                htmlFor="max-articles"
                className="block text-sm font-medium text-[#394a56] mb-2 break-words"
              >
                Max Articles: {config.maxArticles}
              </label>
              <input
                type="range"
                id="max-articles"
                min="5"
                max="30"
                step="1"
                value={config.maxArticles}
                onChange={(e) => updateConfig("maxArticles", parseInt(e.target.value, 10))}
                disabled={isSubmitting}
                className="w-full h-2 bg-neutral-200 rounded-lg appearance-none cursor-pointer accent-blue-600 min-w-0"
              />
              <div className="flex justify-between text-xs text-neutral-500 mt-1">
                <span>5</span>
                <span>30</span>
              </div>
              <p className="text-xs text-neutral-500 mt-2 break-words overflow-hidden">
                Maximum number of articles to include in analysis.
              </p>
            </div>

            {/* Max Articles Per Query */}
            <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200 overflow-hidden min-w-0">
              <label
                htmlFor="max-articles-per-query"
                className="block text-sm font-medium text-[#394a56] mb-2 break-words"
              >
                Max Per Query: {config.maxArticlesPerQuery}
              </label>
              <input
                type="range"
                id="max-articles-per-query"
                min="5"
                max="12"
                step="1"
                value={config.maxArticlesPerQuery}
                onChange={(e) => updateConfig("maxArticlesPerQuery", parseInt(e.target.value, 10))}
                disabled={isSubmitting}
                className="w-full h-2 bg-neutral-200 rounded-lg appearance-none cursor-pointer accent-blue-600 min-w-0"
              />
              <div className="flex justify-between text-xs text-neutral-500 mt-1">
                <span>5</span>
                <span>12</span>
              </div>
              <p className="text-xs text-neutral-500 mt-2 break-words overflow-hidden">
                Maximum results per Tavily search query.
              </p>
            </div>
          </div>
        </section>

        {/* Analysis Settings Section */}
        <section>
          <h3 className="text-sm font-semibold text-neutral-700 mb-3">Analysis Settings</h3>
          <div className="space-y-3">
            {/* Min Confidence */}
            <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200 overflow-hidden min-w-0">
              <label
                htmlFor="min-confidence"
                className="block text-sm font-medium text-[#394a56] mb-2 break-words"
              >
                Minimum Confidence
              </label>
              <select
                id="min-confidence"
                value={config.minConfidence}
                onChange={(e) =>
                  updateConfig("minConfidence", e.target.value as "low" | "medium" | "high")
                }
                disabled={isSubmitting}
                className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent min-w-0"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
              <p className="text-xs text-neutral-500 mt-2 break-words overflow-hidden">
                Minimum confidence level for trading signals.
              </p>
            </div>
          </div>
        </section>
      </div>

      {/* Footer */}
      <div className="border-t border-neutral-300 bg-white/60 backdrop-blur-sm p-3">
        <p className="text-xs text-neutral-500 text-center">
          Settings apply to the next analysis run
        </p>
      </div>
    </div>
  );
}
