"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

interface LabelProps extends React.HTMLAttributes<HTMLElement> {
  asChild?: boolean;
}

export function Label({ asChild = false, className, ...props }: LabelProps) {
  const classes = cn(
    "mono-label inline-block text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--v2-text-subtle)]",
    className
  );

  if (asChild && React.isValidElement(props.children)) {
    const child = props.children as React.ReactElement<{ className?: string }>;
    return React.cloneElement(child, {
      ...props,
      className: cn(classes, child.props.className),
    });
  }

  return <span className={classes} {...props} />;
}
