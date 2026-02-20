"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

interface TooltipContextValue {
  open: boolean;
  setOpen: (open: boolean) => void;
}

const TooltipContext = React.createContext<TooltipContextValue | null>(null);

function useTooltip() {
  const ctx = React.useContext(TooltipContext);
  if (!ctx) throw new Error("Tooltip components must be used within Tooltip");
  return ctx;
}

export function Tooltip({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = React.useState(false);
  return <TooltipContext.Provider value={{ open, setOpen }}>{children}</TooltipContext.Provider>;
}

export function TooltipTrigger({ children, asChild }: { children: React.ReactNode; asChild?: boolean }) {
  const { setOpen } = useTooltip();

  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children as React.ReactElement<any>, {
      onMouseEnter: () => setOpen(true),
      onMouseLeave: () => setOpen(false),
      onFocus: () => setOpen(true),
      onBlur: () => setOpen(false),
    });
  }

  return <span>{children}</span>;
}

export function TooltipContent({ children, className }: { children: React.ReactNode; className?: string }) {
  const { open } = useTooltip();
  if (!open) return null;

  return (
    <div className={cn("absolute z-50 mt-1 rounded-md bg-foreground px-2 py-1 text-xs text-background", className)}>
      {children}
    </div>
  );
}
