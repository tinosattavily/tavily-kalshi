import React from "react";

interface UrlInputBarProps {
  url: string;
  isSubmitting: boolean;
  isFocused: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  onFocusChange: (focused: boolean) => void;
}

const GPU_ACCELERATION_STYLES: React.CSSProperties = {
  willChange: "border-color, box-shadow",
  transform: "translateZ(0)",
  backfaceVisibility: "hidden",
  isolation: "isolate",
};

export default function UrlInputBar({
  url,
  isSubmitting,
  isFocused,
  onChange,
  onSubmit,
  onKeyDown,
  onFocusChange,
}: UrlInputBarProps): React.JSX.Element {
  const focusColor = isFocused ? "text-[#1e3a8a]" : "text-neutral-900";
  const borderColor = isFocused ? "border-[#1e3a8a]" : "border-[#1e3a8a]/20";
  const dividerColor = isFocused ? "bg-[#1e3a8a]" : "bg-[#1e3a8a]/20";

  return (
    <div
      id="url-input-bar"
      className={`rounded-full bg-white/10 backdrop-blur-md border ${borderColor} px-6 py-3 shadow-lg flex items-center gap-3 transition-colors duration-200`}
      style={GPU_ACCELERATION_STYLES}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="20"
        height="20"
        viewBox="0 0 48 48"
        className={`flex-shrink-0 transition-colors ${focusColor}`}
      >
        <path
          fill="none"
          stroke="currentColor"
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M12.852 32.708a8.297 8.297 0 0 1-7.236-4.355a9.012 9.012 0 0 1 .009-8.704a8.296 8.296 0 0 1 7.245-4.338m0-.001l9.001-.035m-9.457 17.46l8.639.09m14.095-17.651a8.297 8.297 0 0 1 7.236 4.355a9.012 9.012 0 0 1-.009 8.704a8.296 8.296 0 0 1-7.245 4.338m.09-17.369l-9 .036m8.91 17.333l-8.64-.09m-10.984-8.749h16.733v.182H15.506z"
        />
      </svg>
      <div className={`h-5 w-px flex-shrink-0 transition-colors ${dividerColor}`} />
      <input
        id="url-input"
        type="text"
        placeholder="Enter Polymarket URL"
        value={url}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKeyDown}
        onFocus={() => onFocusChange(true)}
        onBlur={() => onFocusChange(false)}
        disabled={isSubmitting}
        className="flex-1 bg-transparent border-none outline-none text-neutral-900 placeholder:text-neutral-500 pr-2"
      />
      <button
        id="submit-url-button"
        type="button"
        onClick={onSubmit}
        disabled={!url.trim() || isSubmitting}
        aria-label="Submit URL"
        className="flex-shrink-0 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer hover:opacity-80"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          className={`transition-colors ${focusColor}`}
        >
          <path
            fill="currentColor"
            d="M20 4v9a4 4 0 0 1-4 4H6.914l2.5 2.5L8 20.914L3.086 16L8 11.086L9.414 12.5l-2.5 2.5H16a2 2 0 0 0 2-2V4h2Z"
          />
        </svg>
      </button>
    </div>
  );
}
