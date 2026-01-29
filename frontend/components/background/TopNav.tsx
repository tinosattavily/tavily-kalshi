import React from "react";

import Image from "next/image";

import openaiLogo from "../../openai-trans.png";
import tavilyLogo from "../../tavily-trans.png";
import FlamingOrb from "../ui/FlamingOrb";

export default function TopNav(): React.JSX.Element {
  return (
    <div
      id="top-nav"
      className="flex items-center justify-between border-y border-x border-[#1e3a8a]/20 bg-white/40 backdrop-blur-sm px-12"
    >
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 flex items-center justify-center overflow-hidden">
          <FlamingOrb size={0.4} />
        </div>
        <span className="inline-flex items-center rounded-md py-3 text-2xl font-bold text-[#1e3a8a]">
          prophecy
        </span>
      </div>
      <span className="inline-flex items-center px-4 py-3 gap-6">
        <Image src={tavilyLogo} alt="Tavily logo" className="h-7 w-7 object-contain" />
        <Image src={openaiLogo} alt="OpenAI logo" className="h-7 w-7 object-contain" />
      </span>
    </div>
  );
}
