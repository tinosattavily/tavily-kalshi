"use client";

import React, { PropsWithChildren } from "react";

import Dashboard from "./Dashboard";


export default function Layout({ children }: PropsWithChildren) {
  // Render the main dashboard.
  return <Dashboard>{children}</Dashboard>;
}

