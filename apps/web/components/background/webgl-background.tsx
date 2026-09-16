"use client";

import dynamic from "next/dynamic";

// Loaded client-only and code-split away from the main bundle — three.js is
// heavy and the background is purely decorative, so it should never block
// first paint or the initial JS chunk.
const WebglScene = dynamic(() => import("./webgl-scene").then((mod) => mod.WebglScene), {
  ssr: false,
});

export function WebglBackground() {
  return <WebglScene />;
}
