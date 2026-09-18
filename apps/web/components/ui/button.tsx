import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full font-medium transition-all outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus)] active:scale-[0.97] disabled:pointer-events-none disabled:opacity-50 disabled:active:scale-100",
  {
    variants: {
      variant: {
        primary:
          "bg-[var(--accent)] text-[var(--accent-ink)] shadow-[0_0_24px_rgba(201,164,92,.22)] hover:bg-[var(--accent-strong)]",
        secondary:
          "border border-[var(--line)] bg-[var(--surface-2)] text-[var(--text-strong)] hover:border-[var(--line-strong)] hover:bg-[var(--surface-3)]",
        ghost:
          "text-[var(--text-soft)] hover:bg-[var(--surface-2)] hover:text-[var(--text-strong)]",
      },
      size: {
        sm: "h-9 px-4 text-sm",
        md: "h-11 px-5 text-sm",
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
