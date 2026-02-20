import * as React from "react";

import { cn } from "@/lib/utils";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type, ...props }, ref) => (
    <input
      type={type}
      ref={ref}
      className={cn(
        "flex h-11 w-full rounded-[12px] border border-[var(--v2-border)] bg-[var(--v2-bg-surface)] px-3.5 py-2 text-sm text-[var(--v2-text-main)]",
        "placeholder:text-[var(--v2-text-subtle)] focus-visible:outline-none",
        "focus-visible:border-[var(--v2-accent)] focus-visible:ring-2 focus-visible:ring-[var(--v2-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--v2-bg-canvas)] disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    />
  )
);
Input.displayName = "Input";
