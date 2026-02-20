import React from "react";

export const Badge = ({ children, variant = "secondary", className = "" }: { children: React.ReactNode; variant?: string; className?: string }) => {
  const base = "inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em]";
  const variants: Record<string, string> = {
    primary: "border-[var(--v2-accent)] bg-[color-mix(in_srgb,var(--v2-accent)_20%,transparent)] text-[var(--v2-text-main)]",
    secondary: "border-[var(--v2-border)] bg-[color-mix(in_srgb,white_3%,transparent)] text-[var(--v2-text-main)]",
    destructive: "border-[var(--v2-danger)] bg-[color-mix(in_srgb,var(--v2-danger)_20%,transparent)] text-[var(--v2-danger-soft)]",
    outline: "border-[var(--v2-border-strong)] bg-transparent text-[var(--v2-text-muted)]",
  };
  const variantClass = variants[variant] || variants.secondary;
  return <span className={`${base} ${variantClass} ${className}`}>{children}</span>;
};
