"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

interface CommandContextValue {
  query: string;
  setQuery: (value: string) => void;
}

const CommandContext = React.createContext<CommandContextValue | null>(null);

function useCommand() {
  const ctx = React.useContext(CommandContext);
  if (!ctx) throw new Error("Command components must be used inside Command");
  return ctx;
}

export function Command({ className, children }: { className?: string; children: React.ReactNode }) {
  const [query, setQuery] = React.useState("");
  return (
    <CommandContext.Provider value={{ query, setQuery }}>
      <div className={cn("rounded-lg border bg-card", className)}>{children}</div>
    </CommandContext.Provider>
  );
}

export function CommandInput({ placeholder }: { placeholder?: string }) {
  const { setQuery } = useCommand();
  return (
    <input
      className="w-full border-b bg-transparent px-3 py-2 text-sm outline-none"
      placeholder={placeholder}
      onChange={(event) => setQuery(event.target.value)}
      aria-label={placeholder ?? "Buscar"}
    />
  );
}

export function CommandList({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn("max-h-64 overflow-auto p-1", className)}>{children}</div>;
}

export function CommandEmpty({ children }: { children: React.ReactNode }) {
  return <p className="px-2 py-6 text-center text-sm text-muted-foreground">{children}</p>;
}

export function CommandGroup({ heading, children }: { heading?: string; children: React.ReactNode }) {
  return (
    <div>
      {heading ? <p className="px-2 py-1 text-xs font-semibold uppercase text-muted-foreground">{heading}</p> : null}
      <div>{children}</div>
    </div>
  );
}

export function CommandItem({
  value,
  keywords = [],
  onSelect,
  children,
}: {
  value: string;
  keywords?: string[];
  onSelect?: (value: string) => void;
  children: React.ReactNode;
}) {
  const { query } = useCommand();
  const searchable = `${value} ${keywords.join(" ")}`.toLowerCase();
  if (query && !searchable.includes(query.toLowerCase())) return null;

  return (
    <button
      type="button"
      className="flex w-full items-center rounded-md px-2 py-1.5 text-sm text-left hover:bg-accent"
      onClick={() => onSelect?.(value)}
    >
      {children}
    </button>
  );
}
