"use client";

import React, { useState } from "react";

export interface AnalysisConfiguration {
  // Agent toggles
  useTavilyPromptAgent: boolean; // If false, use fallback queries
  useNewsSummaryAgent: boolean; // If false, use fallback summary
  
  // Article limits
  maxArticles: number; // Maximum number of articles to include (5-30)
  maxArticlesPerQuery: number; // Max results per Tavily query (5-12)
  
  // Analysis settings
  minConfidence: "low" | "medium" | "high"; // Minimum confidence threshold
  enableSentimentAnalysis: boolean; // Enable/disable sentiment analysis
}

const DEFAULT_CONFIG: AnalysisConfiguration = {
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
  const [isExpanded, setIsExpanded] = useState(true);

  const updateConfig = <K extends keyof AnalysisConfiguration>(
    key: K,
    value: AnalysisConfiguration[K]
  ): void => {
    onChange({ ...config, [key]: value });
  };

  const resetToDefaults = (): void => {
    onChange(DEFAULT_CONFIG);
  };

  return (
    <div
      id="configuration-panel"
      className="h-full flex flex-col bg-white/90 border-0"
    >
      {/* Header */}
      <div className="bg-white/90 p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-neutral-900 flex items-center gap-2">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 256 256"
              className="text-neutral-900"
            >
              <path
                fill="currentColor"
                d="M128 80a48 48 0 1 0 48 48a48.05 48.05 0 0 0-48-48Zm0 80a32 32 0 1 1 32-32a32 32 0 0 1-32 32Zm88-29.84q.06-2.16 0-4.32l14.92-18.64a8 8 0 0 0 1.48-7.06a107.21 107.21 0 0 0-10.88-26.25a8 8 0 0 0-6-3.93l-23.72-2.64q-1.48-1.56-3-3L186 40.54a8 8 0 0 0-3.94-6a107.71 107.71 0 0 0-26.25-10.87a8 8 0 0 0-7.06 1.49L130.16 40h-4.32L107.2 25.11a8 8 0 0 0-7.06-1.48a107.6 107.6 0 0 0-26.25 10.88a8 8 0 0 0-3.93 6l-2.64 23.76q-1.56 1.49-3 3L40.54 70a8 8 0 0 0-6 3.94a107.71 107.71 0 0 0-10.87 26.25a8 8 0 0 0 1.49 7.06L40 125.84v4.32L25.11 148.8a8 8 0 0 0-1.48 7.06a107.21 107.21 0 0 0 10.88 26.25a8 8 0 0 0 6 3.93l23.72 2.64q1.49 1.56 3 3L70 215.46a8 8 0 0 0 3.94 6a107.71 107.71 0 0 0 26.25 10.87a8 8 0 0 0 7.06-1.49L125.84 216q2.16.06 4.32 0l18.64 14.92a8 8 0 0 0 7.06 1.48a107.21 107.21 0 0 0 26.25-10.88a8 8 0 0 0 3.93-6l2.64-23.72q1.56-1.48 3-3l23.78-2.8a8 8 0 0 0 6-3.94a107.71 107.71 0 0 0 10.87-26.25a8 8 0 0 0-1.49-7.06Zm-16.1-6.5a73.93 73.93 0 0 1 0 8.68a8 8 0 0 0 1.74 5.48l14.19 17.73a91.57 91.57 0 0 1-6.23 15l-22.6 2.56a8 8 0 0 0-5.1 2.64a74.11 74.11 0 0 1-6.14 6.14a8 8 0 0 0-2.64 5.1l-2.51 22.58a91.32 91.32 0 0 1-15 6.23l-17.74-14.19a8 8 0 0 0-5-1.75h-.48a73.93 73.93 0 0 1-8.68 0a8 8 0 0 0-5.48 1.74l-17.78 14.2a91.57 91.57 0 0 1-15-6.23L82.89 187a8 8 0 0 0-2.64-5.1a74.11 74.11 0 0 1-6.14-6.14a8 8 0 0 0-5.1-2.64l-22.58-2.52a91.32 91.32 0 0 1-6.23-15l14.19-17.74a8 8 0 0 0 1.74-5.48a73.93 73.93 0 0 1 0-8.68a8 8 0 0 0-1.74-5.48L40.2 100.45a91.57 91.57 0 0 1 6.23-15L69 82.89a8 8 0 0 0 5.1-2.64a74.11 74.11 0 0 1 6.14-6.14A8 8 0 0 0 82.89 69l2.51-22.57a91.32 91.32 0 0 1 15-6.23l17.74 14.19a8 8 0 0 0 5.48 1.74a73.93 73.93 0 0 1 8.68 0a8 8 0 0 0 5.48-1.74l17.77-14.19a91.57 91.57 0 0 1 15 6.23L173.11 69a8 8 0 0 0 2.64 5.1a74.11 74.11 0 0 1 6.14 6.14a8 8 0 0 0 5.1 2.64l22.58 2.51a91.32 91.32 0 0 1 6.23 15l-14.19 17.74a8 8 0 0 0-1.74 5.53Z"
              />
            </svg>
            Configurations
          </h2>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-neutral-600 hover:text-neutral-900 transition-colors"
              aria-label={isExpanded ? "Collapse" : "Expand"}
              disabled={isSubmitting}
            >
              <svg
                className={`w-5 h-5 transition-transform ${isExpanded ? "" : "-rotate-90"}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>
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

      {/* Configuration Content */}
      {isExpanded && (
        <div className="flex-1 overflow-y-auto p-4 space-y-6 border-0">
          {/* Agent Toggles Section */}
          <section>
            <h3 className="text-sm font-semibold text-neutral-700 mb-3">Agent Settings</h3>
            <div className="space-y-3">
              {/* Tavily Prompt Agent Toggle */}
              <div className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg border border-neutral-200 min-w-0 overflow-hidden gap-3">
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
                <label className="relative inline-flex items-center cursor-pointer flex-shrink-0">
                  <input
                    type="checkbox"
                    id="tavily-prompt-toggle"
                    checked={config.useTavilyPromptAgent}
                    onChange={(e) => updateConfig("useTavilyPromptAgent", e.target.checked)}
                    disabled={isSubmitting}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-neutral-300 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-neutral-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              {/* News Summary Agent Toggle */}
              <div className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg border border-neutral-200 min-w-0 overflow-hidden gap-3">
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
                <label className="relative inline-flex items-center cursor-pointer flex-shrink-0">
                  <input
                    type="checkbox"
                    id="news-summary-toggle"
                    checked={config.useNewsSummaryAgent}
                    onChange={(e) => updateConfig("useNewsSummaryAgent", e.target.checked)}
                    disabled={isSubmitting}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-neutral-300 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-neutral-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              {/* Sentiment Analysis Toggle */}
              <div className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg border border-neutral-200 min-w-0 overflow-hidden gap-3">
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
                <label className="relative inline-flex items-center cursor-pointer flex-shrink-0">
                  <input
                    type="checkbox"
                    id="sentiment-toggle"
                    checked={config.enableSentimentAnalysis}
                    onChange={(e) => updateConfig("enableSentimentAnalysis", e.target.checked)}
                    disabled={isSubmitting}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-neutral-300 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-neutral-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
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
                  className="block text-sm font-medium text-neutral-900 mb-2 break-words"
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
                  className="block text-sm font-medium text-neutral-900 mb-2 break-words"
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
                  onChange={(e) =>
                    updateConfig("maxArticlesPerQuery", parseInt(e.target.value, 10))
                  }
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
      )}

      {/* Footer with info */}
      {isExpanded && (
        <div className="border-t border-neutral-300 bg-white/90 p-3">
          <p className="text-xs text-neutral-500 text-center">
            Settings apply to the next analysis run
          </p>
        </div>
      )}
    </div>
  );
}

export { DEFAULT_CONFIG };

