import * as React from "react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface GlossyCardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverLift?: boolean;
}

export function GlossyCard({ className, hoverLift = true, ...props }: GlossyCardProps) {
  return (
    <Card
      className={cn(
        "rounded-[var(--radius-lg)] border-[1.5px] border-[var(--v2-border)] bg-[linear-gradient(180deg,var(--v2-bg-surface-muted)_0%,var(--v2-bg-surface)_100%)] text-[var(--v2-text-main)] shadow-[0_18px_42px_color-mix(in_srgb,black_32%,transparent)] transition-all duration-200",
        hoverLift && "hover:-translate-y-0.5 hover:border-[var(--v2-border-strong)]",
        className
      )}
      {...props}
    />
  );
}
