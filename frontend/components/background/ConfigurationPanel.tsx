"use client";

import React from "react";
import NeumorphicToggle from "../ui/NeumorphicToggle";
import NeumorphicSlider from "../ui/NeumorphicSlider";

export interface AnalysisConfiguration {
  useTavilyPromptAgent: boolean;
  useNewsSummaryAgent: boolean;
  maxArticles: number;
  maxArticlesPerQuery: number;
  minConfidence: "low" | "medium" | "high";
  enableSentimentAnalysis: boolean;
}

export const DEFAULT_CONFIG: AnalysisConfiguration = {
  useTavilyPromptAgent: true,
  useNewsSummaryAgent: true,
  maxArticles: 15,
  maxArticlesPerQuery: 8,
  minConfidence: "medium",
  enableSentimentAnalysis: true,
};

interface ConfigurationPanelProps {
  config: AnalysisConfiguration;
  onChange: (config: AnalysisConfiguration) => void;
  isSubmitting?: boolean;
}

export default function ConfigurationPanel({
  config,
  onChange,
  isSubmitting = false,
}: ConfigurationPanelProps): React.JSX.Element {
  function updateConfig<K extends keyof AnalysisConfiguration>(
    key: K,
    value: AnalysisConfiguration[K],
  ): void {
    onChange({ ...config, [key]: value });
  }

  function resetToDefaults(): void {
    onChange(DEFAULT_CONFIG);
  }

  return (
    <div
      id="configuration-panel"
      className="h-full flex flex-col bg-transparent border-0"
    >
      {/* Header - stays fixed */}
      <div className="flex-shrink-0 p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-neutral-900">
            Configurations
          </h2>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={resetToDefaults}
              className="text-xs text-neutral-500 hover:text-neutral-700 transition-colors"
              disabled={isSubmitting}
            >
              Reset
            </button>
          </div>
        </div>
      </div>

      {/* Configuration Content - scrollable */}
      <div className="flex-1 min-h-0 overflow-y-auto scrollbar-minimal p-4 space-y-6 border-0">
          {/* Agent Toggles Section */}
          <section>
            <h3 className="text-sm font-semibold text-neutral-700 mb-3">Agent Settings</h3>
            <div className="space-y-3">
              {/* Tavily Prompt Agent Toggle */}
              <div className="flex items-center justify-between p-3 bg-[#ecf0f3] rounded-lg min-w-0 overflow-hidden gap-3"
                style={{ boxShadow: '4px 4px 8px #d1d9e6, -4px -4px 8px #ffffff' }}
              >
                <div className="flex-1 min-w-0">
                  <label
                    htmlFor="tavily-prompt-toggle"
                    className="text-sm font-medium text-neutral-900 cursor-pointer block break-words"
                  >
                    Use Tavily Prompt Agent
                  </label>
                  <p className="text-xs text-neutral-500 mt-1 break-words overflow-hidden">
                    Generate optimized queries with AI. Disable to use fallback queries.
                  </p>
                </div>
                <NeumorphicToggle
                  id="tavily-prompt-toggle"
                  checked={config.useTavilyPromptAgent}
                  onChange={(checked) => updateConfig("useTavilyPromptAgent", checked)}
                  disabled={isSubmitting}
                />
              </div>

              {/* News Summary Agent Toggle */}
              <div className="flex items-center justify-between p-3 bg-[#ecf0f3] rounded-lg min-w-0 overflow-hidden gap-3"
                style={{ boxShadow: '4px 4px 8px #d1d9e6, -4px -4px 8px #ffffff' }}
              >
                <div className="flex-1 min-w-0">
                  <label
                    htmlFor="news-summary-toggle"
                    className="text-sm font-medium text-neutral-900 cursor-pointer block break-words"
                  >
                    Use News Summary Agent
                  </label>
                  <p className="text-xs text-neutral-500 mt-1 break-words overflow-hidden">
                    Generate AI-powered summaries. Disable to use fallback summaries.
                  </p>
                </div>
                <NeumorphicToggle
                  id="news-summary-toggle"
                  checked={config.useNewsSummaryAgent}
                  onChange={(checked) => updateConfig("useNewsSummaryAgent", checked)}
                  disabled={isSubmitting}
                />
              </div>

              {/* Sentiment Analysis Toggle */}
              <div className="flex items-center justify-between p-3 bg-[#ecf0f3] rounded-lg min-w-0 overflow-hidden gap-3"
                style={{ boxShadow: '4px 4px 8px #d1d9e6, -4px -4px 8px #ffffff' }}
              >
                <div className="flex-1 min-w-0">
                  <label
                    htmlFor="sentiment-toggle"
                    className="text-sm font-medium text-neutral-900 cursor-pointer block break-words"
                  >
                    Enable Sentiment Analysis
                  </label>
                  <p className="text-xs text-neutral-500 mt-1 break-words overflow-hidden">
                    Analyze article sentiment (bullish/bearish/neutral).
                  </p>
                </div>
                <NeumorphicToggle
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
              <div className="p-3 bg-[#ecf0f3] rounded-lg overflow-hidden min-w-0"
                style={{ boxShadow: '4px 4px 8px #d1d9e6, -4px -4px 8px #ffffff' }}
              >
                <label
                  htmlFor="max-articles"
                  className="block text-sm font-medium text-neutral-900 mb-3 break-words"
                >
                  Max Articles: {config.maxArticles}
                </label>
                <NeumorphicSlider
                  id="max-articles"
                  min={5}
                  max={30}
                  step={1}
                  value={config.maxArticles}
                  onChange={(value) => updateConfig("maxArticles", value)}
                  disabled={isSubmitting}
                />
                <div className="flex justify-between text-xs text-neutral-500 mt-2">
                  <span>5</span>
                  <span>30</span>
                </div>
                <p className="text-xs text-neutral-500 mt-2 break-words overflow-hidden">
                  Maximum number of articles to include in analysis.
                </p>
              </div>

              {/* Max Articles Per Query */}
              <div className="p-3 bg-[#ecf0f3] rounded-lg overflow-hidden min-w-0"
                style={{ boxShadow: '4px 4px 8px #d1d9e6, -4px -4px 8px #ffffff' }}
              >
                <label
                  htmlFor="max-articles-per-query"
                  className="block text-sm font-medium text-neutral-900 mb-3 break-words"
                >
                  Max Per Query: {config.maxArticlesPerQuery}
                </label>
                <NeumorphicSlider
                  id="max-articles-per-query"
                  min={5}
                  max={12}
                  step={1}
                  value={config.maxArticlesPerQuery}
                  onChange={(value) => updateConfig("maxArticlesPerQuery", value)}
                  disabled={isSubmitting}
                />
                <div className="flex justify-between text-xs text-neutral-500 mt-2">
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
              <div className="p-3 bg-[#ecf0f3] rounded-lg overflow-hidden min-w-0"
                style={{ boxShadow: '4px 4px 8px #d1d9e6, -4px -4px 8px #ffffff' }}
              >
                <label
                  htmlFor="min-confidence"
                  className="block text-sm font-medium text-neutral-900 mb-2 break-words"
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

      {/* Footer with info - stays fixed */}
      <div className="flex-shrink-0 border-t border-neutral-300 p-3">
        <p className="text-xs text-neutral-500 text-center">
          Settings apply to the next analysis run
        </p>
      </div>
    </div>
  );
}

