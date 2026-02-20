"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

interface TabsContextValue {
  value: string;
  setValue: (value: string) => void;
}

const TabsContext = React.createContext<TabsContextValue | null>(null);

function useTabs() {
  const ctx = React.useContext(TabsContext);
  if (!ctx) throw new Error("Tabs components must be used inside Tabs");
  return ctx;
}

export function Tabs({
  defaultValue,
  value,
  onValueChange,
  className,
  children,
}: {
  defaultValue: string;
  value?: string;
  onValueChange?: (value: string) => void;
  className?: string;
  children: React.ReactNode;
}) {
  const [internal, setInternal] = React.useState(defaultValue);
  const current = value ?? internal;

  const setValue = (next: string) => {
    if (value === undefined) {
      setInternal(next);
    }
    onValueChange?.(next);
  };

  return (
    <TabsContext.Provider value={{ value: current, setValue }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  );
}

type TabsListProps = React.HTMLAttributes<HTMLDivElement> & { variant?: "default" | "line" };

export function TabsList({ className, variant = "default", ...props }: TabsListProps) {
  return (
    <div
      className={cn(
        variant === "line"
          ? "w-full bg-transparent p-0"
          : "inline-flex rounded-[12px] border border-[var(--v2-border)] bg-[var(--v2-bg-surface)] p-1",
        className
      )}
      {...props}
    />
  );
}

export function TabsTrigger({
  value,
  className,
  children,
  variant,
  ...props
}: {
  value: string;
  className?: string;
  children: React.ReactNode;
  variant?: "default" | "line";
} & Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "value" | "children" | "className">) {
  const { value: activeValue, setValue } = useTabs();
  const isActive = activeValue === value;

  return (
    <button
      type="button"
      onClick={() => setValue(value)}
      {...props}
      className={cn(
        "inline-flex items-center text-sm font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--v2-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--v2-bg-canvas)]",
        variant === "line"
          ? cn(
              "rounded-none border-none bg-transparent px-3 py-2",
              isActive
                ? "text-[var(--v2-accent-soft)] [text-shadow:0_0_10px_color-mix(in_srgb,var(--v2-accent)_45%,transparent)]"
                : "text-[var(--v2-text-muted)] hover:text-[var(--v2-text-main)]"
            )
          : cn(
              "rounded-[9px] px-3 py-1.5",
              isActive
                ? "border border-[var(--v2-accent)] bg-[color-mix(in_srgb,var(--v2-accent)_20%,transparent)] text-[var(--v2-text-main)]"
                : "border border-transparent text-[var(--v2-text-muted)] hover:border-[var(--v2-border-strong)] hover:text-[var(--v2-text-main)]"
            ),
        className
      )}
    >
      {children}
    </button>
  );
}

export function TabsContent({
  value,
  className,
  children,
}: {
  value: string;
  className?: string;
  children: React.ReactNode;
}) {
  const { value: activeValue } = useTabs();
  if (activeValue !== value) return null;
  return <div className={className}>{children}</div>;
}
