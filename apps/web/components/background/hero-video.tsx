"use client";

import { useEffect, useState } from "react";

/**
 * The landing hero uses the original `.MOV` artwork when the browser can
 * decode it, with the same layered CSS visual kept underneath as a graceful
 * fallback for browsers that do not support QuickTime containers.
 */
export function HeroVideo() {
  const [motionEnabled, setMotionEnabled] = useState(true);
  const [videoReady, setVideoReady] = useState(false);

  useEffect(() => {
    setMotionEnabled(!window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }, []);

  return (
    <div className={`hero-video-stage ${videoReady ? "has-video" : ""}`} aria-hidden="true">
      <div className={`hero-visual ${motionEnabled ? "is-animated" : ""}`}>
        <span className="hero-visual-orb hero-visual-orb-one" />
        <span className="hero-visual-orb hero-visual-orb-two" />
        <span className="hero-visual-orb hero-visual-orb-three" />
        <span className="hero-visual-grid" />
      </div>
      <video
        className="hero-video"
        autoPlay={motionEnabled}
        muted
        loop
        playsInline
        preload="auto"
        onCanPlay={() => setVideoReady(true)}
        onError={() => setVideoReady(false)}
      >
        {/* Leave the MIME type unspecified: Chromium can decode this MOV on
            some installations even though `video/quicktime` advertises no
            support, and the original landing page relied on that behavior. */}
        <source src="/video_loop.MOV" />
      </video>
    </div>
  );
}
