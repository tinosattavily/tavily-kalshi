import React from "react";

export default function EmptyPrompt(): React.JSX.Element {
  return (
    <div className="min-h-[200px] rounded-lg border border-dashed border-neutral-200/80 flex items-center justify-center text-sm text-neutral-500">
      Enter a Polymarket URL above to generate analysis.
    </div>
  );
}
