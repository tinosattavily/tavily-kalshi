import React from "react";
import { Link as LinkIcon } from "lucide-react";

type Props = {
  url: string;
  isSubmitting: boolean;
  isFocused: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  onFocusChange: (focused: boolean) => void;
};

export default function UrlInputBar({
  url,
  isSubmitting,
  isFocused,
  onChange,
  onSubmit,
  onKeyDown,
  onFocusChange,
}: Props) {
  return (
    <div
      id="url-input-bar"
      className="w-full h-9 rounded px-3.5 flex items-center gap-2.5 bg-input-bg shadow-neu-inset border border-line transition-shadow"
    >
      <span className="text-ink-mute"><LinkIcon size={13} /></span>
      <input
        id="url-input"
        type="url"
        value={url}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKeyDown}
        onFocus={() => onFocusChange(true)}
        onBlur={() => onFocusChange(false)}
        disabled={isSubmitting}
        placeholder="https://polymarket.com/event/… or https://kalshi.com/markets/…"
        aria-label="Market URL"
        className="flex-1 bg-transparent outline-none border-0 font-mono text-[12px] text-ink-soft placeholder:text-ink-mute disabled:opacity-50"
      />
      <button
        id="submit-url-button"
        type="button"
        onClick={onSubmit}
        disabled={isSubmitting || url.trim().length === 0}
        aria-label="Analyze"
        className="font-mono text-[10px] px-1.5 py-0.5 rounded text-accent disabled:opacity-50"
        style={{ background: "var(--accent-soft)", letterSpacing: 0.5 }}
      >
        ↵ RUN
      </button>
    </div>
  );
}


