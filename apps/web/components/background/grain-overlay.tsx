"use client";

/**
 * Static film-grain texture. Pure SVG (feTurbulence → feColorMatrix), no
 * animation loop and no JS after mount — cheap enough to leave mounted
 * permanently. Sits above the WebGL plasma field but below the sidebar and
 * content, so it textures the ambient background without ever touching
 * legibility of text panels.
 */
export function GrainOverlay() {
  return (
    <svg className="grain-overlay" aria-hidden="true" focusable="false">
      <filter id="grain-filter">
        <feTurbulence
          type="fractalNoise"
          baseFrequency="0.85"
          numOctaves="2"
          stitchTiles="stitch"
          result="noise"
        />
        <feColorMatrix
          in="noise"
          type="matrix"
          values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.06 0"
        />
      </filter>
      <rect width="100%" height="100%" filter="url(#grain-filter)" />
    </svg>
  );
}
