import React from "react";
import Image from "next/image";
import { Courier_Prime } from "next/font/google";

const courierPrime = Courier_Prime({
  subsets: ["latin"],
  weight: "700",
});

export default function TopNav() {
  return (
    <div id="top-nav" className="flex items-center justify-between border-y border-x border-neutral-300 bg-white/60 backdrop-blur-sm px-4">
      <div className="flex items-center">
        <span
          className={`${courierPrime.className} inline-flex items-center rounded-md px-4 py-3 text-2xl font-bold text-black`}
        >
          prophily
        </span>
      </div>
      <span className="inline-flex items-center px-4 py-3 gap-6">
        <Image src="/tavily-full-logo.svg" alt="Tavily logo" width={28} height={28} className="h-7 w-7 object-contain" />
      </span>
    </div>
  );
}


