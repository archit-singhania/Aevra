"use client";

import { useEffect, useState } from "react";

/**
 * Full-bleed looping background video for the landing/auth hero. Sits
 * between the WebGL ambient field and the grain overlay so the existing
 * layers still provide texture on top of it.
 *
 * Renders nothing (falling back to the plain WebGL ambient background) when:
 *  - the viewer prefers reduced motion, or
 *  - the video fails to load/decode (e.g. an unsupported container/codec in
 *    the visitor's browser) — checked via the native `error` event rather
 *    than assumed, so a bad source degrades gracefully instead of leaving a
 *    broken/blank frame.
 */
export function HeroVideo() {
  const [enabled, setEnabled] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    setEnabled(!prefersReducedMotion);
  }, []);

  if (!enabled || failed) return null;

  return (
    <video
      className="hero-video"
      autoPlay
      muted
      loop
      playsInline
      preload="auto"
      aria-hidden="true"
      onError={() => setFailed(true)}
    >
      {/* Source is whatever loop lives in /public — currently a .MOV. Most
          Chromium/Firefox builds will only decode this if it's H.264/AAC;
          for guaranteed cross-browser playback, export an .mp4 (H.264) and
          .webm (VP9) alongside it and add them as additional <source> tags
          above this one, most-compatible first. */}
      <source src="/video_loop.MOV" />
    </video>
  );
}
