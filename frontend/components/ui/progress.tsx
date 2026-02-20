import { cn } from "@/lib/utils";

interface ProgressProps {
  value: number;
  className?: string;
}

export function Progress({ value, className }: ProgressProps) {
  const safeValue = Math.max(0, Math.min(100, value));
  return (
    <div className={cn("relative h-2.5 w-full overflow-hidden rounded-full border border-[var(--v2-border)] bg-[var(--v2-bg-canvas-deep)]", className)}>
      <div
        className="h-full bg-[linear-gradient(90deg,var(--v2-accent-soft)_0%,var(--v2-accent)_100%)] transition-all"
        style={{ width: `${safeValue}%` }}
      />
    </div>
  );
}
