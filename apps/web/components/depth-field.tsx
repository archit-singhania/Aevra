"use client";

import { useEffect } from "react";

/**
 * Applies the depth system to the whole app from a single mount point.
 *
 * The alternative was adding pointer handlers to every card in
 * live-workspace.tsx. That would mean ~60 React components each holding a
 * listener, each calling getBoundingClientRect on every pointermove — a
 * forced synchronous layout per card per frame. This does it once: one
 * capture-phase listener on the document, a rect cached on enter rather
 * than re-measured on move, and all writes batched into a single rAF.
 *
 * Elements opt in by matching TILT_SELECTOR. Nothing in the markup needs
 * to change, which is why this converts every existing surface — including
 * pages and dialogs — rather than only the ones someone remembered to tag.
 */

// Surfaces that should tilt from this global listener. Two real class names
// exist in live-workspace.tsx but are deliberately absent:
//   .live-stats article — rendered by the existing DepthCard component,
//     which already runs its own pointer handler and owns the transform via
//     .depth-card. Adding this here would run two competing tilt systems on
//     the same four elements and double the per-move layout reads this
//     component exists to avoid.
//   .live-auth-card — renders as motion.form. Framer Motion writes its
//     resolved transform to the inline style attribute, which always wins
//     over a stylesheet rule for the same property. A tilt rule targeting it
//     would be silently inert.
// Dense list rows are excluded on purpose too: a row that tilts as the
// pointer crosses it on the way somewhere else reads as jitter, not depth.
const TILT_SELECTOR = [".live-panel", ".chart-card"].join(",");

// Skip the effect entirely below this width — small viewports are coarse
// pointers in practice, and the tilt has nothing to track.
const MIN_WIDTH = 900;

export function DepthField() {
  useEffect(() => {
    const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    const coarseQuery = window.matchMedia("(pointer: coarse)");

    let active: HTMLElement | null = null;
    let rect: DOMRect | null = null;
    let raf = 0;
    let pendingX = 0;
    let pendingY = 0;

    const enabled = () =>
      !motionQuery.matches && !coarseQuery.matches && window.innerWidth >= MIN_WIDTH;

    const clear = (el: HTMLElement | null) => {
      if (!el) return;
      el.style.removeProperty("--tilt-x");
      el.style.removeProperty("--tilt-y");
      el.style.removeProperty("--sheen-x");
      el.style.removeProperty("--sheen-y");
      el.removeAttribute("data-depth-active");
    };

    const flush = () => {
      raf = 0;
      const el = active;
      const r = rect;
      if (!el || !r) return;
      const nx = (pendingX - r.left) / r.width - 0.5;
      const ny = (pendingY - r.top) / r.height - 0.5;
      el.style.setProperty("--tilt-x", `${(-ny * 6).toFixed(3)}deg`);
      el.style.setProperty("--tilt-y", `${(nx * 8).toFixed(3)}deg`);
      el.style.setProperty("--sheen-x", `${(50 + nx * 90).toFixed(1)}%`);
      el.style.setProperty("--sheen-y", `${(50 + ny * 90).toFixed(1)}%`);
    };

    const onPointerMove = (event: PointerEvent) => {
      if (!enabled()) return;
      // Ignore anything that isn't a real hovering pointer — a finger
      // dragging the page would otherwise leave cards tilted behind it.
      if (event.pointerType === "touch") return;

      const target = (event.target as Element | null)?.closest?.(TILT_SELECTOR) as HTMLElement | null;

      if (target !== active) {
        clear(active);
        active = target;
        // Measured once, on entry. Re-measuring per move is the forced
        // layout this whole component exists to avoid.
        rect = target ? target.getBoundingClientRect() : null;
        if (target) target.setAttribute("data-depth-active", "");
      }
      if (!active) return;

      pendingX = event.clientX;
      pendingY = event.clientY;
      if (!raf) raf = window.requestAnimationFrame(flush);
    };

    const onPointerLeaveWindow = () => {
      clear(active);
      active = null;
      rect = null;
    };

    // A scroll moves the element under a stationary pointer, invalidating
    // the cached rect. Dropping the tilt is cheaper and less jarring than
    // re-measuring mid-scroll.
    //
    // Capture phase, not window: the app shell is height:100dvh with
    // `overflow: hidden` on body, so the page never scrolls — `.live-content`
    // does. Scroll events don't bubble from elements, so a window listener
    // would never fire and cards would stay tilted at stale positions.
    const onScroll = () => {
      if (active) onPointerLeaveWindow();
    };

    const onMotionChange = () => {
      if (!enabled()) onPointerLeaveWindow();
    };

    document.addEventListener("pointermove", onPointerMove, { passive: true });
    document.addEventListener("pointerleave", onPointerLeaveWindow);
    document.addEventListener("scroll", onScroll, { capture: true, passive: true });
    window.addEventListener("blur", onPointerLeaveWindow);
    motionQuery.addEventListener("change", onMotionChange);
    coarseQuery.addEventListener("change", onMotionChange);

    document.documentElement.setAttribute("data-depth-enabled", "");

    return () => {
      if (raf) window.cancelAnimationFrame(raf);
      clear(active);
      document.removeEventListener("pointermove", onPointerMove);
      document.removeEventListener("pointerleave", onPointerLeaveWindow);
      document.removeEventListener("scroll", onScroll, { capture: true });
      window.removeEventListener("blur", onPointerLeaveWindow);
      motionQuery.removeEventListener("change", onMotionChange);
      coarseQuery.removeEventListener("change", onMotionChange);
      document.documentElement.removeAttribute("data-depth-enabled");
    };
  }, []);

  return null;
}
