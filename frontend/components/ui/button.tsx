import * as React from "react";

import { cn } from "@/lib/utils";

type ButtonVariant = "default" | "outline" | "destructive" | "secondary" | "ghost";
type ButtonSize = "default" | "sm" | "lg" | "icon";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  asChild?: boolean;
}

const variants: Record<ButtonVariant, string> = {
  default:
    "border border-[var(--v2-accent)] bg-[linear-gradient(180deg,var(--v2-accent-soft)_0%,var(--v2-accent)_100%)] text-[color:var(--v2-bg-canvas-deep)] shadow-[0_8px_24px_color-mix(in_srgb,var(--v2-accent)_32%,transparent)] hover:brightness-105",
  outline:
    "border border-[var(--v2-border-strong)] bg-[var(--v2-bg-surface)] text-[var(--v2-text-main)] hover:border-[var(--v2-accent)] hover:bg-[var(--v2-bg-surface-muted)]",
  destructive:
    "border border-[var(--v2-danger)] bg-[color-mix(in_srgb,var(--v2-danger)_18%,transparent)] text-[var(--v2-danger-soft)] hover:bg-[color-mix(in_srgb,var(--v2-danger)_26%,transparent)]",
  secondary:
    "border border-[var(--v2-border)] bg-[var(--v2-bg-surface-muted)] text-[var(--v2-text-main)] hover:border-[var(--v2-border-strong)]",
  ghost: "text-[var(--v2-text-muted)] hover:bg-[color-mix(in_srgb,white_4%,transparent)] hover:text-[var(--v2-text-main)]",
};

const sizes: Record<ButtonSize, string> = {
  default: "h-10 px-4 py-2 rounded-[10px]",
  sm: "h-9 rounded-[9px] px-3",
  lg: "h-11 rounded-[12px] px-8",
  icon: "h-10 w-10 rounded-[10px]",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", asChild = false, children, ...props }, ref) => {
    const classes = cn(
      "inline-flex items-center justify-center whitespace-nowrap text-sm font-semibold tracking-[0.01em] transition-all duration-200",
      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--v2-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[color:var(--v2-bg-canvas)]",
      "disabled:pointer-events-none disabled:opacity-50",
      variants[variant],
      sizes[size],
      className
    );

    if (asChild && React.isValidElement(children)) {
      const child = children as React.ReactElement<{ className?: string }>;
      return React.cloneElement(child, {
        className: cn(classes, child.props.className),
      });
    }

    return (
      <button ref={ref} className={classes} {...props}>
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";
