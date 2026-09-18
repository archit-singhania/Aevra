import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";
import { cn } from "@/lib/utils";

// Squircle, not a pill. A fully-rounded button reads consumer-friendly; the
// rest of this product is an instrument panel, and the corner radius is one
// of the loudest signals of which of those two things an interface is.
// `--r-sm` is the same token the fields and nav items use, so controls that
// sit next to each other share a corner.
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-[var(--r-sm)] font-semibold tracking-[-0.01em] transition-all outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--bg)] active:scale-[0.98] disabled:pointer-events-none disabled:opacity-45 disabled:active:scale-100",
  {
    variants: {
      variant: {
        // The accent glow is deliberate and deliberately rare: the primary
        // CTA and the AI orb are the only two things in the app allowed one.
        primary:
          "bg-[var(--accent)] text-[var(--accent-ink)] shadow-[0_0_22px_rgba(var(--accent-rgb),0.2)] hover:bg-[var(--accent-strong)] hover:shadow-[0_0_28px_rgba(var(--accent-rgb),0.28)]",
        secondary:
          "border border-[var(--line-strong)] bg-[var(--surface-2)] text-[var(--text-strong)] hover:border-[var(--accent-line)] hover:bg-[var(--surface-3)]",
        ghost:
          "text-[var(--text-soft)] hover:bg-[var(--surface-2)] hover:text-[var(--text-strong)]",
        // Outline rather than a filled red block: destructive actions here
        // are reversible workspace decisions, not data deletion, and a solid
        // red button overstates that every time it's on screen.
        danger:
          "border border-[rgba(224,101,110,0.34)] bg-[rgba(224,101,110,0.08)] text-[var(--rose)] hover:bg-[rgba(224,101,110,0.14)]",
      },
      size: {
        sm: "h-9 px-4 text-[13px]",
        md: "h-11 px-5 text-[13px]",
        icon: "size-10 p-0",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export function Button({ className, variant, size, asChild = false, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : "button";
  return (
    <Comp
      type={asChild ? undefined : "button"}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  );
}
