"use client";

import * as React from "react";
import { ChevronDown } from "lucide-react";

import { cn } from "@/lib/utils";

interface SelectContextValue {
  value: string;
  setValue: (value: string) => void;
}

const SelectContext = React.createContext<SelectContextValue | null>(null);

function useSelectContext() {
  const ctx = React.useContext(SelectContext);
  if (!ctx) throw new Error("Select components must be used inside Select");
  return ctx;
}

export function Select({
  value,
  onValueChange,
  children,
}: {
  value: string;
  onValueChange: (value: string) => void;
  children: React.ReactNode;
}) {
  return <SelectContext.Provider value={{ value, setValue: onValueChange }}>{children}</SelectContext.Provider>;
}

export function SelectTrigger({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div
      className={cn(
        "relative min-w-[160px] rounded-[12px] border border-[var(--v2-border)] bg-[var(--v2-bg-surface)] px-3.5 py-2.5 text-sm text-[var(--v2-text-main)]",
        className
      )}
    >
      {children}
      <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--v2-text-muted)]" />
    </div>
  );
}

export function SelectValue({ placeholder }: { placeholder?: string }) {
  const { value } = useSelectContext();

  return <span className="block truncate pr-6 text-sm text-[var(--v2-text-main)]">{value || placeholder}</span>;
}

export function SelectContent({
  children,
  ariaLabel,
  className,
}: {
  children: React.ReactNode;
  ariaLabel?: string;
  className?: string;
}) {
  const { value, setValue } = useSelectContext();

  return (
    <select
      value={value}
      aria-label={ariaLabel}
      onChange={(event) => setValue(event.target.value)}
      className={cn("absolute inset-0 h-full w-full cursor-pointer opacity-0", className)}
    >
      {children}
    </select>
  );
}

export function SelectItem({ value, children }: { value: string; children: React.ReactNode }) {
  return <option value={value}>{children}</option>;
}
