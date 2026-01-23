import React from "react";

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
      className="rounded-2xl px-4 py-2.5 flex items-center gap-3"
      style={{
        background: "rgba(236, 240, 243, 0.3)",
        boxShadow: isFocused
          ? "0px 0px 0px 0px #ffffff, 0px 0px 0px 0px #d1d9e6, 4px 4px 6px 0px #d1d9e6 inset, -4px -4px 6px 0px #ffffff inset"
          : "-8px -4px 8px 0px #ffffff, 8px 4px 12px 0px #d1d9e6, 2px 2px 3px 0px #d1d9e6 inset, -2px -2px 3px 0px #ffffff inset",
        transition: "box-shadow 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
      }}
    >
      {/* Link icon */}
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="16"
        height="16"
        viewBox="0 0 48 48"
        className={`flex-shrink-0 transition-colors duration-300 ${
          isFocused ? "text-[#394a56]" : "text-[#394a56]/60"
        }`}
      >
        <path
          fill="none"
          stroke="currentColor"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2.5"
          d="M12.852 32.708a8.297 8.297 0 0 1-7.236-4.355a9.012 9.012 0 0 1 .009-8.704a8.296 8.296 0 0 1 7.245-4.338m0-.001l9.001-.035m-9.457 17.46l8.639.09m14.095-17.651a8.297 8.297 0 0 1 7.236 4.355a9.012 9.012 0 0 1-.009 8.704a8.296 8.296 0 0 1-7.245 4.338m.09-17.369l-9 .036m8.91 17.333l-8.64-.09m-10.984-8.749h16.733v.182H15.506z"
        />
      </svg>

      {/* Divider */}
      <div className="h-4 w-px flex-shrink-0 bg-[#d1d9e6]" />

      {/* Input field */}
      <input
        id="url-input"
        type="text"
        placeholder="Enter Kalshi market URL..."
        value={url || ""}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKeyDown}
        className="flex-1 bg-transparent border-none outline-none text-[#394a56] placeholder:text-[#394a56]/50 text-sm font-medium"
        style={{ background: "transparent" }}
        onFocus={() => onFocusChange(true)}
        onBlur={() => onFocusChange(false)}
        disabled={isSubmitting}
      />

      {/* Submit button - neuromorphic style */}
      <button
        id="submit-url-button"
        type="button"
        onClick={onSubmit}
        disabled={!url.trim() || isSubmitting}
        className={`
          flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center
          transition-all duration-300
          disabled:opacity-40 disabled:cursor-not-allowed
          cursor-pointer
          ${isSubmitting ? "animate-pulse" : ""}
        `}
        style={{
          background: "#ecf0f3",
          boxShadow: !url.trim() || isSubmitting
            ? "2px 2px 4px 0px #d1d9e6 inset, -2px -2px 4px 0px #ffffff inset"
            : "-4px -2px 4px 0px #ffffff, 4px 2px 6px 0px #d1d9e6",
        }}
        onMouseDown={(e) => {
          if (url.trim() && !isSubmitting) {
            e.currentTarget.style.boxShadow = "2px 2px 4px 0px #d1d9e6 inset, -2px -2px 4px 0px #ffffff inset";
          }
        }}
        onMouseUp={(e) => {
          if (url.trim() && !isSubmitting) {
            e.currentTarget.style.boxShadow = "-4px -2px 4px 0px #ffffff, 4px 2px 6px 0px #d1d9e6";
          }
        }}
        onMouseLeave={(e) => {
          if (url.trim() && !isSubmitting) {
            e.currentTarget.style.boxShadow = "-4px -2px 4px 0px #ffffff, 4px 2px 6px 0px #d1d9e6";
          }
        }}
        aria-label="Submit URL"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          className={`transition-colors duration-300 ${
            url.trim() && !isSubmitting ? "text-[#394a56]" : "text-[#394a56]/40"
          }`}
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


